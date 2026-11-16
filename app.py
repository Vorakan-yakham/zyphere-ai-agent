"""Zyphere COMPLETE21 server
- Serve the web UI
- TTS via edge-tts (/tts)
- Agent tools backend: web search, page fetch, persistent memory
- Autonomous learning: rotating curriculum -> persistent knowledge base,
  optional server-side LLM summaries (Groq/OpenRouter/Gemini), scheduler
- Watchlist + proactive briefing: track topics, prioritise them when learning,
  and report what changed since the user last checked in
- Backup / restore (+ optional Upstash-compatible remote KV so memory survives
  Render restarts): REMOTE_KV_URL, REMOTE_KV_TOKEN, BACKUP_TOKEN
- Video maker: royalty-free images + text overlay + Thai/English narration -> MP4
  Image sources (no key): Openverse, Wikimedia Commons
  Optional (set env vars): Pexels, Pixabay, Unsplash

Run:
  pip install -r requirements.txt
  python app.py
Then open http://localhost:8000
"""
import asyncio
import html
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid
import wave
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

import requests
from bs4 import BeautifulSoup

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    Image = None
    ImageDraw = None
    ImageFilter = None
    ImageFont = None
    ImageOps = None

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None

PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
FONT_DIR = os.path.join(BASE_DIR, "fonts")
MEM_PATH = os.path.join(DATA_DIR, "memory.json")
VOICES = {"th": "th-TH-NiwatNeural", "en": "en-GB-RyanNeural"}
MEM_LOCK = threading.Lock()
JOB_LOCK = threading.Lock()
JOBS = {}
UA = "Mozilla/5.0 (compatible; Zyphere/18; +https://github.com/Vorakan-yakham/zyphere-ai-agent)"
VIDEO_W, VIDEO_H = 1280, 720

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(FONT_DIR, exist_ok=True)

FFMPEG = None
if imageio_ffmpeg is not None:
    try:
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        FFMPEG = None
if not FFMPEG:
    FFMPEG = shutil.which("ffmpeg")


# ----------------------------------------------------------------------------
# optional remote persistence (Upstash Redis REST compatible)
# ----------------------------------------------------------------------------
# Render's free plan wipes the local disk on every restart. If you want memory
# to survive restarts without a paid disk, create a free Upstash Redis database
# and set:
#   REMOTE_KV_URL=https://xxxx.upstash.io
#   REMOTE_KV_TOKEN=...
# Every save is pushed to the remote store in the background and, at startup,
# the newest remote copy is restored when it exists.
REMOTE_KV_URL = os.environ.get("REMOTE_KV_URL", "").strip().rstrip("/")
REMOTE_KV_TOKEN = os.environ.get("REMOTE_KV_TOKEN", "").strip()
REMOTE_KEYS = {
    "memory": "zyphere:memory",
    "knowledge": "zyphere:knowledge",
    "learning": "zyphere:learning",
    "watch": "zyphere:watch",
}
REMOTE_STATE = {"last_push": 0, "last_pull": 0, "last_ok": 0, "last_error": ""}
REMOTE_LOCK = threading.RLock()
REMOTE_Q = {}
REMOTE_Q_LOCK = threading.Lock()
REMOTE_WORKER = {"thread": None}


def remote_enabled():
    return bool(REMOTE_KV_URL and REMOTE_KV_TOKEN)


def _remote_headers():
    return {
        "Authorization": "Bearer " + REMOTE_KV_TOKEN,
        "Content-Type": "application/json",
    }


def _remote_error(err):
    with REMOTE_LOCK:
        REMOTE_STATE["last_error"] = _clip(str(err), 300)


def _remote_ok(what):
    with REMOTE_LOCK:
        REMOTE_STATE["last_ok"] = int(time.time())
        REMOTE_STATE[what] = int(time.time())
        REMOTE_STATE["last_error"] = ""


def _remote_key(name):
    return REMOTE_KEYS.get(name) or name


def remote_push(name, data):
    if not remote_enabled():
        return False
    try:
        payload = json.dumps(data, ensure_ascii=False)
        r = requests.post(
            REMOTE_KV_URL + "/set/" + urllib.parse.quote(_remote_key(name), safe=""),
            headers=_remote_headers(),
            data=payload.encode("utf-8"),
            timeout=12,
        )
        if not r.ok:
            raise RuntimeError("HTTP %s" % r.status_code)
        _remote_ok("last_push")
        return True
    except Exception as e:
        _remote_error(e)
        return False


def remote_get_json(name):
    if not remote_enabled():
        return None
    try:
        r = requests.get(
            REMOTE_KV_URL + "/get/" + urllib.parse.quote(_remote_key(name), safe=""),
            headers=_remote_headers(),
            timeout=12,
        )
        if not r.ok:
            raise RuntimeError("HTTP %s" % r.status_code)
        j = r.json()
        val = j.get("result") if isinstance(j, dict) else j
        if val is None:
            return None
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                return None
        return val if isinstance(val, dict) else None
    except Exception as e:
        _remote_error(e)
        return None


def _remote_drain():
    while True:
        time.sleep(1.2)
        with REMOTE_Q_LOCK:
            if not REMOTE_Q:
                REMOTE_WORKER["thread"] = None
                return
            items = list(REMOTE_Q.items())
            REMOTE_Q.clear()
        for name, data in items:
            remote_push(name, data)


def _remote_schedule(name, data):
    if not remote_enabled():
        return
    with REMOTE_Q_LOCK:
        REMOTE_Q[name] = data
        t = REMOTE_WORKER.get("thread")
        if t and t.is_alive():
            return
        t = threading.Thread(target=_remote_drain, daemon=True)
        REMOTE_WORKER["thread"] = t
        t.start()


def remote_push_all():
    if not remote_enabled():
        return {"ok": False, "error": "remote storage is not configured"}
    sent = []
    for name in ("memory", "knowledge", "learning", "watch"):
        try:
            data = {
                "memory": load_mem,
                "knowledge": load_knowledge,
                "learning": load_learning,
                "watch": load_watch,
            }[name]()
        except Exception:
            continue
        if remote_push(name, data):
            sent.append(name)
    return {"ok": bool(sent), "pushed": sent, "remote": remote_public()}


def remote_pull_all():
    if not remote_enabled():
        return {"ok": False, "error": "remote storage is not configured"}
    restored = []
    skipped = []
    paths = {
        "memory": MEM_PATH,
        "knowledge": os.path.join(DATA_DIR, "knowledge.json"),
        "learning": os.path.join(DATA_DIR, "learning.json"),
        "watch": os.path.join(DATA_DIR, "watch.json"),
    }
    for name, path in paths.items():
        data = remote_get_json(name)
        if not isinstance(data, dict):
            skipped.append(name)
            continue
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            restored.append(name)
        except Exception as e:
            _remote_error(e)
            skipped.append(name)
    if restored:
        _remote_ok("last_pull")
    return {"ok": bool(restored), "restored": restored, "skipped": skipped, "remote": remote_public()}


def remote_public():
    with REMOTE_LOCK:
        state = dict(REMOTE_STATE)
    host = ""
    if REMOTE_KV_URL:
        host = urllib.parse.urlparse(REMOTE_KV_URL).netloc
    return {
        "enabled": remote_enabled(),
        "host": host,
        "keys": sorted(REMOTE_KEYS.values()),
        **state,
    }



# ----------------------------------------------------------------------------
# memory
# ----------------------------------------------------------------------------
def _default_mem():
    return {
        "profile": {},
        "facts": [],
        "preferences": [],
        "notes": [],
        "history_summary": "",
        "updated_at": 0,
    }


def load_mem():
    with MEM_LOCK:
        if not os.path.exists(MEM_PATH):
            return _default_mem()
        try:
            with open(MEM_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = _default_mem()
            base.update(data if isinstance(data, dict) else {})
            return base
        except Exception:
            return _default_mem()


def save_mem(data):
    with MEM_LOCK:
        data = data if isinstance(data, dict) else _default_mem()
        data["updated_at"] = int(time.time())
        with open(MEM_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _remote_schedule("memory", data)
        return data


def _clip(text, n):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text[:n]


def _dedupe_append(lst, item, key_fields, limit=120):
    if not isinstance(lst, list):
        lst = []
    if not isinstance(item, dict):
        return lst
    norm = {k: _clip(str(item.get(k, "")), 500) for k in key_fields}
    for i, x in enumerate(lst):
        if isinstance(x, dict) and all(_clip(str(x.get(k, "")), 500) == v for k, v in norm.items()):
            lst[i].update({k: v for k, v in item.items() if v not in (None, "")})
            return lst
    item = {k: v for k, v in item.items() if v not in (None, "")}
    item["ts"] = int(time.time())
    lst.append(item)
    if len(lst) > limit:
        lst = lst[-limit:]
    return lst


def memory_update(payload):
    mem = load_mem()
    p = payload or {}
    if isinstance(p.get("profile"), dict):
        mem["profile"] = mem.get("profile") or {}
        for k, v in p["profile"].items():
            if v is None:
                mem["profile"].pop(k, None)
            else:
                mem["profile"][k] = _clip(str(v), 400)
    if isinstance(p.get("remember"), dict):
        kind = (p["remember"].get("kind") or "fact").lower()
        item = {
            "text": _clip(str(p["remember"].get("text", "")), 500),
            "source": _clip(str(p["remember"].get("source", "conversation")), 120),
        }
        if not item["text"]:
            pass
        elif kind == "preference":
            mem["preferences"] = _dedupe_append(mem.get("preferences"), item, ["text"], 120)
        elif kind == "note":
            mem["notes"] = _dedupe_append(mem.get("notes"), item, ["text"], 200)
        else:
            mem["facts"] = _dedupe_append(mem.get("facts"), item, ["text"], 200)
    if isinstance(p.get("summary"), str) and p["summary"].strip():
        mem["history_summary"] = _clip(p["summary"], 4000)
    if p.get("clear") == "all":
        mem = _default_mem()
    return save_mem(mem)


# ----------------------------------------------------------------------------
# web search / fetch (Agent tools)
# ----------------------------------------------------------------------------
LANG_NAMES = {"th":"ไทย","en":"อังกฤษ","zh":"จีน","ja":"ญี่ปุ่น","ko":"เกาหลี","ar":"อาหรับ","ru":"รัสเซีย","hi":"ฮินดี","vi":"เวียดนาม"}

def detect_lang(text):
    t = str(text or "")
    ranges = [("th", 0x0E00, 0x0E7F), ("zh", 0x4E00, 0x9FFF), ("ja", 0x3040, 0x30FF), ("ko", 0xAC00, 0xD7AF), ("ar", 0x0600, 0x06FF), ("ru", 0x0400, 0x04FF), ("hi", 0x0900, 0x097F), ("el", 0x0370, 0x03FF)]
    scored = [(sum(1 for c in t if a <= ord(c) <= b), code) for code, a, b in ranges]
    n, code = max(scored)
    if n == 0:
        return "en" if re.search(r"[A-Za-z]", t) else "unknown"
    return code


def translate_text(text, target="th", source=""):
    text = _clip(str(text or ""), 900)
    if not text:
        raise RuntimeError("missing text")
    src = _clip(str(source or detect_lang(text)), 12)
    tgt = _clip(str(target or "th"), 12)
    try:
        r = requests.get("https://api.mymemory.translated.net/get", params={"q": text, "langpair": src + "|" + tgt}, timeout=15, headers={"User-Agent": UA})
        if r.ok:
            out = (r.json().get("responseData") or {}).get("translatedText") or ""
            if out and "MYMEMORY WARNING" not in out.upper():
                return {"ok": True, "text": out, "source": src, "target": tgt, "engine": "mymemory"}
    except Exception:
        pass
    try:
        raw = _server_llm_json("You are a precise translator. Translate the user text into the target language. Return JSON only: {\"text\":\"...\"}", "From " + src + " to " + tgt + ": " + text)
        j = _extract_json(raw or "")
        if isinstance(j, dict) and j.get("text"):
            return {"ok": True, "text": str(j["text"]), "source": src, "target": tgt, "engine": "llm"}
    except Exception:
        pass
    raise RuntimeError("แปลไม่ได้ในขณะนี้")


def polish_text(text, lang="th"):
    t = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not t.strip():
        raise RuntimeError("missing text")
    try:
        raw = _server_llm_json(
            "You are a Thai/English writing editor. Rewrite the text to be clear, natural and easy to understand. Fix awkward word order, add correct spacing between sentences, break into short paragraphs, use punctuation properly, keep the original meaning and facts, never invent content, and avoid emoji. Return JSON only: {\"text\":\"...\"}",
            "Language: " + str(lang or "th") + "\n\nTEXT:\n" + t[:6000],
        )
        j = _extract_json(raw or "")
        if isinstance(j, dict) and j.get("text"):
            return {"ok": True, "text": str(j["text"]), "engine": "llm"}
    except Exception:
        pass
    out = re.sub(r"[ \t]+", " ", t)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"([.!?。！？])(?=[A-Za-z])", r"\1 ", out)
    out = re.sub(r",(?=[A-Za-z])", ", ", out)
    out = re.sub(r"([.!?。！？])\s*(?=[ก-๙])", r"\1 ", out)
    out = "\n".join(x.strip() for x in out.split("\n"))
    return {"ok": True, "text": out.strip(), "engine": "heuristic"}


def search_web(query, max_results=5):
    q = _clip(query, 300)
    if not q:
        return {"ok": False, "error": "empty query", "results": []}
    headers = {"User-Agent": UA}
    results = []
    # 1) DuckDuckGo Instant Answer API
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": q, "format": "json", "no_redirect": 1, "no_html": 1, "skip_disambig": 0},
            headers=headers,
            timeout=12,
        )
        if r.ok:
            j = r.json()
            if j.get("AbstractText"):
                results.append({
                    "title": j.get("Heading") or q,
                    "url": j.get("AbstractURL") or "",
                    "snippet": _clip(j.get("AbstractText"), 500),
                    "source": j.get("AbstractSource") or "DuckDuckGo",
                })
            for t in (j.get("RelatedTopics") or []):
                if isinstance(t, dict) and t.get("Text"):
                    results.append({
                        "title": _clip(t.get("Text"), 80),
                        "url": t.get("FirstURL") or "",
                        "snippet": _clip(t.get("Text"), 400),
                        "source": "DuckDuckGo",
                    })
                elif isinstance(t, dict) and t.get("Topics"):
                    for tt in t.get("Topics", []):
                        if isinstance(tt, dict) and tt.get("Text"):
                            results.append({
                                "title": _clip(tt.get("Text"), 80),
                                "url": tt.get("FirstURL") or "",
                                "snippet": _clip(tt.get("Text"), 400),
                                "source": "DuckDuckGo",
                            })
                if len(results) >= max_results:
                    break
    except Exception:
        pass
    # 2) DuckDuckGo HTML results fallback
    if len(results) < max_results:
        try:
            r = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": q},
                headers=headers,
                timeout=12,
            )
            if r.ok:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.select(".result__a"):
                    href = a.get("href") or ""
                    if "uddg=" in href:
                        href = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
                    title = _clip(a.get_text(" ", strip=True), 160)
                    sn = a.find_parent(class_="result")
                    snippet = _clip(sn.select_one(".result__snippet").get_text(" ", strip=True) if sn and sn.select_one(".result__snippet") else "", 400)
                    if title or href:
                        results.append({"title": title, "url": href, "snippet": snippet, "source": "DuckDuckGo"})
                    if len(results) >= max_results:
                        break
        except Exception:
            pass
    # dedupe by url/title
    seen = set()
    uniq = []
    for it in results:
        k = (it.get("url") or "") or (it.get("title") or "")
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(it)
        if len(uniq) >= max_results:
            break
    return {"ok": True, "query": q, "results": uniq}


def fetch_page(url, max_chars=15000):
    url = (url or "").strip()
    if not url:
        return {"ok": False, "error": "empty url"}
    try:
        headers = {"User-Agent": UA}
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        title = url
        text = ""
        if "text/html" in ctype or "<html" in r.text[:200].lower():
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "svg"]):
                tag.decompose()
            if soup.title and soup.title.string:
                title = _clip(soup.title.string, 200)
            node = soup.find("article") or soup.find("main") or soup.body or soup
            text = node.get_text("\n", strip=True)
        else:
            text = r.text
        text = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()
        return {"ok": True, "url": r.url, "title": title, "content": _clip(text, max_chars), "truncated": len(text) > max_chars}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300], "url": url}


# ----------------------------------------------------------------------------
# autonomous learning + persistent knowledge base
# ----------------------------------------------------------------------------
KNOW_PATH = os.path.join(DATA_DIR, "knowledge.json")
LEARN_PATH = os.path.join(DATA_DIR, "learning.json")
KNOW_LOCK = threading.RLock()
LEARN_LOCK = threading.RLock()
LEARN_JOB_LOCK = threading.RLock()
LEARN_JOBS = {}

# A broad, rotating curriculum: world knowledge + learning theories/methods.
DEV_STAGES = [
 ("เกิด-3ขวบ", ["คว่ำคลานเดินวิ่ง", "หยิบจับกินเองขับถ่าย", "จำหน้าคนใกล้ชิด", "ยิ้มหัวเราะร้องไห้สื่อสาร", "กลัวคนแปลกหน้าเล่นสมมติ"], ["เสียงภาษาและคำแรก", "ประโยคสั้นและชื่อตัวเอง", "ร้อนเย็นนุ่มแข็ง", "หวานเปรี้ยวสีเสียงกลิ่น"]),
 ("อนุบาล3-6", ["เข้าคิวแบ่งของขอโทษขอบคุณ", "ระบายสีตัดกระดาษปั้นดิน", "กระโดดปีนป่ายกล้ามเนื้อ", "นิทานเพลงวาดรูปเล่นบทบาท"], ["ก-ฮ และ A-Z", "นับ1-10 และ1-100", "เขียนตามรอย"]),
 ("ประถม1-6", ["หน้าที่พลเมืองศาสนาประเพณีมารยาท", "สุขอนามัยกีฬาดูแลร่างกาย", "วาดภาพร้องเพลงงานฝีมืองานบ้าน", "ใช้เมาส์คีย์บอร์ดพิมพ์ค้นหา"], ["อ่านเขียนสะกดแต่งประโยคย่อความ", "บวกลบคูณหารเศษส่วนทศนิยมเรขาคณิต", "พืชสัตว์ร่างกายดินน้ำอากาศแรงพลังงาน", "ประวัติศาสตร์ไทยภูมิศาสตร์แผนที่", "ภาษาอังกฤษคำศัพท์ประโยคพื้นฐาน"]),
 ("มัธยมต้น", ["เพศศึกษาการเงินเบื้องต้นป้องกันภัย", "ทำงานกลุ่มและรู้จักตัวเอง"], ["ฟิสิกส์เคมีชีววิทยาโลกอวกาศ", "พีชคณิตสมการกราฟสถิติความน่าจะเป็น", "ภาษาไทยวิเคราะห์อังกฤษไวยากรณ์", "เศรษฐศาสตร์กฎหมายประวัติศาสตร์โลก"]),
 ("มัธยมปลายเลือกสาย", ["ช่างยนต์ไฟฟ้าก่อสร้าง", "อาหารโรงแรมเสริมสวยการท่องเที่ยว", "เกษตรและเทคโนโลยีการผลิต", "กีฬาดนตรีศิลปะเฉพาะทาง"], ["ฟิสิกส์เคมีชีวะคณิตเข้มข้น", "บริหารบัญชีเศรษฐศาสตร์นิติศาสตร์", "ภาษาอังกฤษจีนญี่ปุ่นเกาหลีฝรั่งเศส", "ประวัติศาสตร์ภูมิศาสตร์รัฐศาสตร์"]),
 ("มหาวิทยาลัยเชี่ยวชาญ", ["การเงินภาษีการลงทุนการเจรจาการขาย", "การสื่อสารจัดการอารมณ์เลี้ยงลูก", "ซ่อมของเอาตัวรอดรู้เท่าทันสื่อใช้เทคโนโลยี"], ["AIหุ่นยนต์วิศวกรรมวิทยาศาสตร์ข้อมูล", "แพทย์เภสัชทันตสัตวแพทย์สาธารณสุข", "ปรัชญาจิตวิทยาสังคมวิทยารัฐศาสตร์", "การตลาดโลจิสติกส์บริหารทรัพยากร", "นิเทศศาสตร์ภาพยนตร์แอนิเมชันออกแบบ", "เกษตรประมงป่าไม้สิ่งแวดล้อมธรณี"]),
 ("วัยทำงานเรียนรู้ตลอดชีวิต", ["การเงินส่วนตัวและภาษี", "การเจรจาขายและสื่อสาร", "การจัดการอารมณ์เลี้ยงลูก", "ซ่อมของในบ้านเอาตัวรอด", "รู้เท่าทันสื่อและใช้เทคโนโลยี"], ["สายราชการรัฐวิสาหกิจ", "สายเอกชนวิศวกรโปรแกรมเมอร์การตลาด", "สายอาชีพอิสระช่างเกษตรกรค้าขาย", "สายธุรกิจส่วนตัวฟรีแลนซ์ครีเอเตอร์", "สายวิชาชีพเฉพาะทนายนักบินนักวิจัย"]),
]

DEV_INNER = [
 ["ความรักและการผูกพัน", "ความกลัวและความปลอดภัย", "สติสัมปชัญญะเริ่มต้น"],
 ["นิทานศีลธรรม", "การเห็นอกเห็นใจ", "คำอธิษฐานและพิธีกรรมง่าย"],
 ["ศาสนาและประเพณีไทย", "ความดีความจริงความงาม", "การขอโทษและการอภัย", "การแบ่งปันและกตัญญู"],
 ["ปรัชญาชีวิตเบื้องต้น", "จิตวิทยาอารมณ์และตัวตน", "ศาสนาเปรียบเทียบโลก", "จุดหมายและคุณค่าส่วนตัว"],
 ["จริยธรรมและศีลธรรม", "สมาธิและการฝึกสติ", "ความตายและการจากลา", "สัญลักษณ์ทางศาสนา"],
 ["ปรัชญาตะวันออกและตะวันตก", "จิตวิทยาเชิงบวกและความหมายชีวิต", "การเปลี่ยนแปลงและการปล่อยวาง", "การเยียวยาและความเมตตา"],
 ["การจัดการความเครียด", "การให้ความหมายกับงาน", "ความเงียบและการทบทวนตนเอง", "การใช้ชีวิตตามคุณค่า"],
]

DEV_LANG = [
 ["ภาษาคือเสียงและสัญลักษณ์", "ชื่อเรียกในหลายภาษา"],
 ["ก-ฮ และ A-Z", "ตัวเลขในหลายภาษา", "คำทักทายง่าย"],
 ["ภาษาอังกฤษคำศัพท์พื้นฐาน", "ภาษาจีนตัวอักษรและการออกเสียง", "ภาษาญี่ปุ่นฮิรางานะ", "ภาษาเกาหลีฮังกึล", "ภาษาไทยการสะกดคำ"],
 ["อังกฤษไวยากรณ์", "การแปลเบื้องต้น", "คำเหมือนแต่ต่างความหมาย"],
 ["ภาษาสเปนฝรั่งเศสเยอรมัน", "ภาษารัสเซียอักษรซีริลลิก", "ภาษาอาหรับ", "ภาษาฮินดีเทวนาครี", "ภาษาเวียดนาม"],
 ["ภาษาศาสตร์และไวยากรณ์โลก", "ศิลปะการแปลและตีความ", "ภาษากับวัฒนธรรม", "คำยืมและคำเทียม"],
 ["ภาษาสำหรับทำงานและเจรจา", "เรียนภาษาใหม่ด้วยตัวเอง", "เทคนิคจำคำศัพท์", "หลายภาษาในชีวิตประจำวัน"],
]

LANG_CRAFT = [
 ["การเว้นวรรคและจังหวะประโยค"],
 ["การใช้เครื่องหมายวรรคตอน", "การแบ่งย่อหน้า"],
 ["การเรียงลำดับความคิด", "ประโยคสั้นต่อเนื่อง", "การใช้สรรพนามให้ชัด"],
 ["โครงสร้างบทความหัวข้อนำเนื้อหาสรุป", "การเขียนให้กระชับ", "คำซ้ำและคำเกิน"],
 ["การเขียนบทสนทนาให้เป็นธรรมชาติ", "การเชื่อมประโยคด้วยคำเชื่อม", "น้ำเสียงสุภาพ"],
 ["การจัดรูปแบบ Markdown", "การเขียนเชิงวิเคราะห์และอธิบาย", "การอ่านแล้วเรียบเรียงใหม่"],
 ["การเขียนให้ผู้อ่านเข้าใจครั้งเดียว", "การตรวจแก้ไขข้อความของตนเอง", "การแปลแล้วปรับสำนวน"],
]

def dev_items():
    out=[]
    for si,(stage,life,world) in enumerate(DEV_STAGES):
        for t in life: out.append({"stage":stage,"kind":"life","topic":t})
        for t in (DEV_INNER[si] if si < len(DEV_INNER) else []): out.append({"stage":stage,"kind":"inner","topic":t})
        for t in (DEV_LANG[si] if si < len(DEV_LANG) else []): out.append({"stage":stage,"kind":"lang","topic":t})
        for t in (LANG_CRAFT[si] if si < len(LANG_CRAFT) else []): out.append({"stage":stage,"kind":"craft","topic":t})
        for t in world: out.append({"stage":stage,"kind":"world","topic":t})
    return out

CURRICULUM = [
    "กำเนิดจักรวาลและดาราศาสตร์",
    "ระบบสุริยะและอวกาศ",
    "วิวัฒนาการของสิ่งมีชีวิต",
    "พันธุกรรมและชีวเทคโนโลยี",
    "ระบบนิเวศและความหลากหลายทางชีวภาพ",
    "สภาพภูมิอากาศและสิ่งแวดล้อม",
    "ฟิสิกส์ในชีวิตประจำวัน",
    "เคมีรอบตัว",
    "คณิตศาสตร์และตรรกะ",
    "วิทยาศาสตร์ข้อมูลและสถิติ",
    "ประวัติศาสตร์โลก",
    "ประวัติศาสตร์ไทย",
    "ภูมิศาสตร์และวัฒนธรรมโลก",
    "เศรษฐศาสตร์และเงิน",
    "การเงินส่วนบุคคลและการลงทุน",
    "การเป็นผู้ประกอบการ",
    "เทคโนโลยีปัญญาประดิษฐ์",
    "ความมั่นคงปลอดภัยไซเบอร์",
    "โลกดิจิทัลและสังคมออนไลน์",
    "จริยธรรมของเอไอ",
    "สุขภาพกายและใจ",
    "โภชนาการและอาหาร",
    "การออกกำลังกายและสุขภาวะ",
    "การนอนหลับกับสมอง",
    "จิตวิทยามนุษย์",
    "พฤติกรรมศาสตร์และการเปลี่ยนนิสัย",
    "ภาษาและการสื่อสาร",
    "ภาษาอังกฤษเพื่อการทำงาน",
    "ศิลปะ ดนตรี และวรรณกรรม",
    "ปรัชญาและจริยธรรม",
    "การคิดเชิงวิพากษ์",
    "การแก้ปัญหาและความคิดสร้างสรรค์",
    "การจัดการเวลาและสมาธิ",
    "ทักษะการเรียนรู้ Active Recall",
    "ทักษะการเรียนรู้ Spaced Repetition",
    "ทักษะการเรียนรู้ Feynman Technique",
    "ทักษะการเรียนรู้ Deliberate Practice",
    "ทักษะการเรียนรู้ Metacognition",
    "ทฤษฎีการเรียนรู้ Constructivism",
    "ทฤษฎีการเรียนรู้ Behaviorism",
    "ทฤษฎีการเรียนรู้ Cognitivism",
    "ทฤษฎีการเรียนรู้ Social Learning",
    "ทฤษฎีการเรียนรู้ Bloom's Taxonomy",
    "การเรียนรู้แบบโครงงาน Project-Based Learning",
    "การเรียนรู้แบบสืบเสาะ Inquiry-Based Learning",
    "การเรียนรู้แบบ Mastery Learning",
    "การเรียนแบบ Interleaving",
    "การเรียนแบบ Elaboration และ Dual Coding",
    "พลังงานทดแทนและความยั่งยืน",
    "เมืองอัจฉริยะและการขนส่งอนาคต",
    "อาหารอนาคตและการเกษตรยั่งยืน",
    "การเดินทางและวัฒนธรรม",
    "มนุษยศาสตร์และเรื่องเล่า",
]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "has", "have", "had", "not", "but", "you", "your", "they", "their", "its",
    "into", "about", "which", "when", "where", "what", "who", "how", "why",
    "can", "could", "would", "should", "will", "may", "might", "also", "more",
    "most", "than", "then", "there", "these", "those", "such", "been", "being",
    "other", "one", "two", "many", "some", "all", "any", "each", "very",
    "ของ", "และ", "ที่", "ใน", "เป็น", "การ", "ความ", "ได้", "ให้", "กับ",
    "จาก", "โดย", "หรือ", "แต่", "ไม่", "นี้", "นั้น", "ซึ่ง", "มี", "จะ",
    "ต้อง", "อย่าง", "เพื่อ", "เมื่อ", "เพราะ", "ว่า", "อีก", "ก็", "จึง",
}


def _default_knowledge():
    return {"items": [], "updated_at": 0}


def _default_learning():
    return {
        "enabled": True,
        "interval_hours": 6,
        "cursor": 0,
        "last_run": 0,
        "last_topic": "",
        "last_status": "",
        "updated_at": 0,
        "frontier": [],
        "expanded": 0,
        "dev_cursor": 0,
        "stage": "",
        "kind": "",
        "track": "",
    }


def load_knowledge():
    with KNOW_LOCK:
        if not os.path.exists(KNOW_PATH):
            return _default_knowledge()
        try:
            with open(KNOW_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = _default_knowledge()
            if isinstance(data, dict):
                base.update(data)
            if not isinstance(base.get("items"), list):
                base["items"] = []
            return base
        except Exception:
            return _default_knowledge()


def _save_knowledge(data):
    with KNOW_LOCK:
        data = data if isinstance(data, dict) else _default_knowledge()
        data["updated_at"] = int(time.time())
        with open(KNOW_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _remote_schedule("knowledge", data)
        return data


def _norm_topic(topic):
    return re.sub(r"\s+", " ", str(topic or "")).strip().casefold()


def add_knowledge(entry):
    entry = dict(entry or {})
    entry["topic"] = _clip(entry.get("topic") or "", 160)
    if not entry["topic"]:
        raise RuntimeError("knowledge entry needs a topic")
    now = int(time.time())
    with KNOW_LOCK:
        data = load_knowledge()
        items = data.get("items") or []
        norm = _norm_topic(entry["topic"])
        for i, old in enumerate(items):
            if _norm_topic(old.get("topic")) == norm:
                entry["id"] = old.get("id") or entry.get("id")
                entry["first_seen"] = old.get("first_seen") or old.get("created_at") or now
                entry["version"] = int(old.get("version") or 1) + 1
                items.pop(i)
                break
        entry.setdefault("id", uuid.uuid4().hex[:12])
        entry.setdefault("first_seen", now)
        entry.setdefault("version", 1)
        entry["created_at"] = int(entry.get("created_at") or now)
        entry["updated_at"] = now
        items.insert(0, entry)
        data["items"] = items[:500]
        _save_knowledge(data)
    return entry


def delete_knowledge(entry_id):
    with KNOW_LOCK:
        data = load_knowledge()
        items = [x for x in (data.get("items") or []) if str(x.get("id")) != str(entry_id)]
        removed = len(data.get("items") or []) - len(items)
        data["items"] = items
        _save_knowledge(data)
    return removed


def clear_knowledge():
    with KNOW_LOCK:
        data = _default_knowledge()
        _save_knowledge(data)
    return True


def knowledge_count():
    return len(load_knowledge().get("items") or [])


def _knowledge_tokens(text):
    return [t for t in re.findall(r"[A-Za-z0-9\u0E00-\u0E7F]{2,}", (text or "").lower()) if len(t) >= 2]


def search_knowledge(query="", limit=20):
    limit = max(1, min(int(limit or 20), 50))
    data = load_knowledge()
    items = list(data.get("items") or [])
    q = (query or "").strip()
    if not q:
        return {"query": "", "total": len(items), "items": [dict(it, related=related_topics(it, items, limit=3)) for it in items[:limit]]}
    low = q.lower()
    tokens = _knowledge_tokens(q)
    scored = []
    for it in items:
        blob = " ".join([
            str(it.get("topic") or ""),
            str(it.get("title") or ""),
            str(it.get("summary") or ""),
            " ".join(str(x) for x in (it.get("points") or [])),
            " ".join(str(x) for x in (it.get("tags") or [])),
        ]).lower()
        score = 0
        if low in str(it.get("topic") or "").lower():
            score += 12
        if low in blob:
            score += 6
        for t in tokens:
            score += blob.count(t)
        if score > 0:
            scored.append((score, int(it.get("created_at") or 0), it))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return {"query": q, "total": len(items), "items": [dict(x[2], related=related_topics(x[2], items, limit=3)) for x in scored[:limit]]}


def load_learning():
    with LEARN_LOCK:
        if not os.path.exists(LEARN_PATH):
            return _default_learning()
        try:
            with open(LEARN_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = _default_learning()
            if isinstance(data, dict):
                base.update(data)
            try:
                base["interval_hours"] = max(1.0, min(168.0, float(base.get("interval_hours") or 6)))
            except Exception:
                base["interval_hours"] = 6
            base["enabled"] = bool(base.get("enabled", True))
            base["cursor"] = max(0, int(base.get("cursor") or 0))
            return base
        except Exception:
            return _default_learning()


def save_learning(data):
    with LEARN_LOCK:
        data = data if isinstance(data, dict) else _default_learning()
        data["updated_at"] = int(time.time())
        with open(LEARN_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _remote_schedule("learning", data)
        return data


def learning_update(payload):
    payload = payload or {}
    cfg = load_learning()
    if "enabled" in payload:
        cfg["enabled"] = bool(payload.get("enabled"))
    if "interval_hours" in payload:
        try:
            cfg["interval_hours"] = max(1.0, min(168.0, float(payload.get("interval_hours") or 6)))
        except Exception:
            pass
    if payload.get("reset_cursor"):
        cfg["cursor"] = 0
    if payload.get("reset_schedule"):
        cfg["last_run"] = 0
        cfg["last_status"] = ""
    return save_learning(cfg)


def learning_public_config():
    cfg = load_learning()
    return {
        "enabled": bool(cfg.get("enabled")),
        "interval_hours": cfg.get("interval_hours") or 6,
        "cursor": cfg.get("cursor") or 0,
        "last_run": cfg.get("last_run") or 0,
        "last_topic": cfg.get("last_topic") or "",
        "last_status": cfg.get("last_status") or "",
        "knowledge_count": knowledge_count(),
        "curriculum_count": len(CURRICULUM),
        "frontier_count": len([x for x in (cfg.get("frontier") or []) if isinstance(x, dict) and x.get("status") != "done"]),
        "expanded": int(cfg.get("expanded") or 0),
        "stage": cfg.get("stage") or "",
        "kind": cfg.get("kind") or "",
        "track": cfg.get("track") or "",
        "dev_total": len(dev_items()),
        "topics": CURRICULUM,
        "server_llm": bool(
            os.environ.get("GROQ_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        ),
    }


# ----------------------------------------------------------------------------
# watchlist + proactive briefing + backup/restore
# ----------------------------------------------------------------------------
WATCH_PATH = os.path.join(DATA_DIR, "watch.json")
WATCH_LOCK = threading.RLock()


def _default_watch():
    return {"topics": [], "updated_at": 0}


def load_watch():
    with WATCH_LOCK:
        if not os.path.exists(WATCH_PATH):
            return _default_watch()
        try:
            with open(WATCH_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = _default_watch()
            if isinstance(data, dict):
                base.update(data)
            raw = base.get("topics")
            if not isinstance(raw, list):
                raw = []
            seen = set()
            topics = []
            for it in raw:
                if not isinstance(it, dict):
                    continue
                topic = _clip(it.get("topic") or "", 160)
                if not topic:
                    continue
                norm = _norm_topic(topic)
                if norm in seen:
                    continue
                seen.add(norm)
                topics.append({
                    "topic": topic,
                    "notes": _clip(it.get("notes") or "", 300),
                    "added_at": int(it.get("added_at") or 0),
                    "last_checked": int(it.get("last_checked") or 0),
                    "last_learned": int(it.get("last_learned") or 0),
                    "last_version": int(it.get("last_version") or 0),
                    "checks": int(it.get("checks") or 0),
                    "last_error": _clip(it.get("last_error") or "", 200),
                })
            base["topics"] = topics[:100]
            return base
        except Exception:
            return _default_watch()


def save_watch(data):
    with WATCH_LOCK:
        data = data if isinstance(data, dict) else _default_watch()
        if not isinstance(data.get("topics"), list):
            data["topics"] = []
        data["updated_at"] = int(time.time())
        with open(WATCH_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _remote_schedule("watch", data)
        return data


def watch_add(topic, notes="", refresh=False):
    topic = _clip(topic, 160)
    if not topic:
        raise RuntimeError("ต้องระบุหัวข้อที่ต้องการติดตาม")
    now = int(time.time())
    with WATCH_LOCK:
        data = load_watch()
        norm = _norm_topic(topic)
        found = None
        for it in data.get("topics") or []:
            if _norm_topic(it.get("topic")) == norm:
                found = it
                break
        if found:
            found["topic"] = topic
            if notes:
                found["notes"] = _clip(notes, 300)
            if refresh:
                found["last_checked"] = 0
                found["last_error"] = ""
        else:
            found = {
                "topic": topic,
                "notes": _clip(notes, 300),
                "added_at": now,
                "last_checked": 0,
                "last_learned": 0,
                "last_version": 0,
                "checks": 0,
                "last_error": "",
            }
            data.setdefault("topics", []).append(found)
        save_watch(data)
    return found


def watch_remove(topic):
    norm = _norm_topic(topic)
    with WATCH_LOCK:
        data = load_watch()
        before = len(data.get("topics") or [])
        data["topics"] = [x for x in (data.get("topics") or []) if _norm_topic(x.get("topic")) != norm]
        removed = before - len(data["topics"])
        save_watch(data)
    return removed


def watch_clear():
    with WATCH_LOCK:
        save_watch(_default_watch())
    return True


def watch_mark(topic, entry=None, error=""):
    """Remember that a watched topic was checked. Called by the learning worker."""
    norm = _norm_topic(topic)
    now = int(time.time())
    with WATCH_LOCK:
        data = load_watch()
        hit = False
        for it in data.get("topics") or []:
            if _norm_topic(it.get("topic")) == norm:
                it["last_checked"] = now
                it["checks"] = int(it.get("checks") or 0) + 1
                it["last_error"] = _clip(error or "", 200)
                if entry:
                    it["last_learned"] = now
                    it["last_version"] = int(entry.get("version") or 1)
                hit = True
                break
        if hit:
            save_watch(data)
    return hit


def watch_due_topics(limit=1):
    cfg = load_learning()
    try:
        interval = max(1.0, float(cfg.get("interval_hours") or 6)) * 3600
    except Exception:
        interval = 6 * 3600
    now = time.time()
    due = [
        it for it in (load_watch().get("topics") or [])
        if now - float(it.get("last_checked") or 0) >= interval
    ]
    due.sort(key=lambda x: (int(x.get("last_checked") or 0), int(x.get("added_at") or 0)))
    limit = max(1, min(int(limit or 1), 10))
    return due[:limit]


def watch_public():
    kb = {}
    for it in (load_knowledge().get("items") or []):
        kb[_norm_topic(it.get("topic"))] = it
    cfg = load_learning()
    try:
        interval = max(1.0, float(cfg.get("interval_hours") or 6)) * 3600
    except Exception:
        interval = 6 * 3600
    now = time.time()
    out = []
    for it in (load_watch().get("topics") or []):
        entry = kb.get(_norm_topic(it.get("topic")))
        version = int((entry or {}).get("version") or 0)
        out.append({
            **it,
            "knowledge_id": (entry or {}).get("id") or "",
            "title": (entry or {}).get("title") or it.get("topic") or "",
            "version": version,
            "summary": _clip((entry or {}).get("summary") or "", 360),
            "updated": bool(entry and version > int(it.get("last_version") or 0)),
            "due": now - float(it.get("last_checked") or 0) >= interval,
        })
    return out


def build_briefing(since=0, limit=12):
    now = int(time.time())
    try:
        since = max(0, int(since or 0))
    except Exception:
        since = 0
    limit = max(1, min(int(limit or 12), 50))
    items = []
    for it in (load_knowledge().get("items") or []):
        changed = max(int(it.get("updated_at") or 0), int(it.get("created_at") or 0))
        if changed > since:
            items.append(it)
    items.sort(key=lambda x: max(int(x.get("updated_at") or 0), int(x.get("created_at") or 0)), reverse=True)
    all_items = items
    lite = [{
        "id": it.get("id"),
        "topic": it.get("topic") or "",
        "title": it.get("title") or it.get("topic") or "",
        "summary": _clip(it.get("summary") or "", 600),
        "points": [str(x) for x in (it.get("points") or [])][:5],
        "tags": [str(x) for x in (it.get("tags") or [])][:6],
        "lang": it.get("lang") or "",
        "version": int(it.get("version") or 1),
        "created_at": int(it.get("created_at") or 0),
        "updated_at": int(it.get("updated_at") or it.get("created_at") or 0),
        "related": related_topics(it, all_items, limit=3),
    } for it in items[:limit]]
    watched = watch_public()
    cfg = learning_public_config()
    history = (load_learn_history().get("items") or [])[:5]
    suggestions = []
    overdue = [x for x in watched if x.get("due")][:3]
    if overdue:
        suggestions.append("ถึงกำหนดอัปเดตหัวข้อที่ติดตามแล้ว: " + " · ".join(str(x.get("topic")) for x in overdue))
    failed = [x for x in watched if str(x.get("last_error") or "").strip()][:2]
    if failed:
        suggestions.append("บางหัวข้อเรียนรู้ไม่สำเร็จ ลองกดอัปเดตอีกครั้ง: " + " · ".join(str(x.get("topic")) for x in failed))
    if not watched:
        suggestions.append("ลองติดตามหัวข้อที่สนใจ (เช่น AI ล่าสุด, เศรษฐกิจไทย) ไซเฟอร์จะอัปเดตให้ก่อนหัวข้ออื่น")
    if not lite:
        suggestions.append("ยังไม่มีความรู้ใหม่ในช่วงนี้ กด \"สุ่มหัวข้อถัดไป\" เพื่อสะสมความรู้เพิ่ม")
    return {
        "ok": True,
        "now": now,
        "since": since,
        "new_count": len(items),
        "items": lite,
        "watched": watched,
        "watch_count": len(watched),
        "watched_updated": [x for x in watched if x.get("updated")],
        "history": history,
        "suggestions": suggestions[:4],
        "learning": {
            "enabled": cfg.get("enabled"),
            "interval_hours": cfg.get("interval_hours"),
            "last_run": cfg.get("last_run"),
            "last_topic": cfg.get("last_topic"),
            "last_status": cfg.get("last_status"),
            "knowledge_count": cfg.get("knowledge_count"),
            "server_llm": cfg.get("server_llm"),
        },
    }


def backup_bundle():
    mem = load_mem()
    knowledge = load_knowledge()
    learning = load_learning()
    watch = load_watch()
    return {
        "app": "zyphere",
        "version": 21,
        "created_at": int(time.time()),
        "counts": {
            "memory": len((mem.get("facts") or [])) + len((mem.get("preferences") or [])) + len((mem.get("notes") or [])),
            "knowledge": len(knowledge.get("items") or []),
            "watch": len(watch.get("topics") or []),
        },
        "memory": mem,
        "knowledge": knowledge,
        "learning": learning,
        "watch": watch,
    }


def restore_bundle(body):
    body = body or {}
    if isinstance(body.get("backup"), dict):
        body = body["backup"]
    if not isinstance(body, dict) or not any(k in body for k in ("memory", "knowledge", "learning", "watch")):
        raise RuntimeError("ไฟล์สำรองไม่ถูกต้อง")
    counts = {}
    if isinstance(body.get("memory"), dict):
        save_mem(body["memory"])
        counts["memory"] = len((body["memory"].get("facts") or [])) + len((body["memory"].get("preferences") or [])) + len((body["memory"].get("notes") or []))
    if isinstance(body.get("knowledge"), dict) and isinstance(body["knowledge"].get("items"), list):
        data = body["knowledge"]
        data["items"] = data["items"][:2000]
        _save_knowledge(data)
        counts["knowledge"] = len(data["items"])
    if isinstance(body.get("learning"), dict):
        save_learning(body["learning"])
        counts["learning"] = 1
    if isinstance(body.get("watch"), dict) and isinstance(body["watch"].get("topics"), list):
        data = body["watch"]
        data["topics"] = data["topics"][:100]
        save_watch(data)
        counts["watch"] = len(data["topics"])
    return {"ok": True, "restored": counts, "counts": backup_bundle()["counts"]}


def storage_public():
    def exists(path):
        try:
            return os.path.exists(path) and os.path.getsize(path)
        except Exception:
            return False
    return {
        "ok": True,
        "remote": remote_public(),
        "local": {
            "memory": bool(exists(MEM_PATH)),
            "knowledge": bool(exists(KNOW_PATH)),
            "learning": bool(exists(LEARN_PATH)),
            "watch": bool(exists(WATCH_PATH)),
        },
        "counts": {
            "knowledge": knowledge_count(),
            "watch": len(load_watch().get("topics") or []),
        },
        "backup_token_required": bool(os.environ.get("BACKUP_TOKEN", "").strip()),
    }


def admin_token_ok(supplied):
    expected = os.environ.get("BACKUP_TOKEN", "").strip()
    if not expected:
        return True
    return str(supplied or "") == expected


# ----------------------------------------------------------------------------
# learning history + automatic local snapshots
# ----------------------------------------------------------------------------
HISTORY_PATH = os.path.join(DATA_DIR, "learn_history.json")
HISTORY_LOCK = threading.RLock()
SNAP_DIR = os.path.join(DATA_DIR, "snapshots")
SNAP_LOCK = threading.Lock()


def load_learn_history():
    with HISTORY_LOCK:
        if not os.path.exists(HISTORY_PATH):
            return {"items": [], "updated_at": 0}
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"items": [], "updated_at": 0}
            if not isinstance(data.get("items"), list):
                data["items"] = []
            return data
        except Exception:
            return {"items": [], "updated_at": 0}


def add_learn_history(record):
    record = dict(record or {})
    record["ts"] = int(record.get("ts") or time.time())
    record["learned"] = [str(x) for x in (record.get("learned") or [])][:3]
    record["errors"] = (record.get("errors") or [])[:3]
    with HISTORY_LOCK:
        data = load_learn_history()
        data["items"] = ([record] + (data.get("items") or []))[:100]
        data["updated_at"] = int(time.time())
        try:
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return record


def make_snapshot(reason="manual", keep=12):
    try:
        os.makedirs(SNAP_DIR, exist_ok=True)
        bundle = backup_bundle()
        name = time.strftime("%Y%m%d-%H%M%S") + "-" + (re.sub(r"[^A-Za-z0-9_-]+", "-", str(reason or "snap"))[:32] or "snap") + "-" + uuid.uuid4().hex[:4] + ".json"
        path = os.path.join(SNAP_DIR, name)
        with SNAP_LOCK:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=2)
            try:
                files = [os.path.join(SNAP_DIR, x) for x in os.listdir(SNAP_DIR) if x.endswith(".json")]
                files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                for old in files[max(1, int(keep or 12)):]:
                    try:
                        os.remove(old)
                    except Exception:
                        pass
            except Exception:
                pass
        return {"ok": True, "name": name, "bytes": os.path.getsize(path), "counts": bundle.get("counts") or {}}
    except Exception as e:
        return {"ok": False, "error": _clip(str(e), 300)}


def list_snapshots():
    try:
        if not os.path.isdir(SNAP_DIR):
            return []
        out = []
        for name in os.listdir(SNAP_DIR):
            if not name.endswith(".json"):
                continue
            path = os.path.join(SNAP_DIR, name)
            try:
                st = os.stat(path)
                out.append({"name": name, "bytes": st.st_size, "created_at": int(st.st_mtime)})
            except Exception:
                continue
        out.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
        return out[:30]
    except Exception:
        return []


def restore_snapshot(name):
    safe = os.path.basename(str(name or ""))
    if not safe.endswith(".json"):
        raise RuntimeError("ชื่อ snapshot ไม่ถูกต้อง")
    path = os.path.join(SNAP_DIR, safe)
    if not os.path.exists(path):
        raise RuntimeError("ไม่พบ snapshot นี้")
    with open(path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    return restore_bundle(bundle)


def related_topics(item, items=None, limit=3):
    item = item or {}
    items = items if isinstance(items, list) else (load_knowledge().get("items") or [])
    tags = set(str(x).casefold() for x in (item.get("tags") or []) if str(x).strip())
    topic = _norm_topic(item.get("topic"))
    tokens = set(_knowledge_tokens((item.get("topic") or "") + " " + (item.get("summary") or ""))) - STOPWORDS
    scored = []
    for other in items:
        if str(other.get("id")) == str(item.get("id")):
            continue
        if _norm_topic(other.get("topic")) == topic:
            continue
        otags = set(str(x).casefold() for x in (other.get("tags") or []) if str(x).strip())
        otokens = set(_knowledge_tokens((other.get("topic") or "") + " " + (other.get("summary") or ""))) - STOPWORDS
        score = 4 * len(tags & otags) + len(tokens & otokens)
        if score > 0:
            scored.append((score, other))
    scored.sort(key=lambda x: (-x[0], -int(x[1].get("updated_at") or x[1].get("created_at") or 0)))
    return [{
        "id": x[1].get("id"),
        "topic": x[1].get("topic") or "",
        "title": x[1].get("title") or x[1].get("topic") or "",
    } for x in scored[:max(1, min(int(limit or 3), 6))]]


def frontier_add(candidates, parent="", depth=0):
    cfg = load_learning()
    fr = cfg.get("frontier") if isinstance(cfg.get("frontier"), list) else []
    known = set()
    for it in (load_knowledge().get("items") or []):
        known.add(_norm_topic(it.get("topic")))
    for w in (load_watch().get("topics") or []):
        known.add(_norm_topic(w.get("topic")))
    seen = set(known)
    for x in fr:
        seen.add(_norm_topic(x.get("topic")) if isinstance(x, dict) else _norm_topic(x))
    added = []
    for c in (candidates or []):
        t = _clip(str(c or ""), 120)
        if not t or _norm_topic(t) in seen or "\ufffd" in t or t.count("?") >= 3:
            continue
        seen.add(_norm_topic(t))
        fr.append({"topic": t, "parent": _clip(str(parent or ""), 120), "depth": max(0, min(int(depth or 0), 8)), "added_at": int(time.time()), "status": "queued"})
        added.append(t)
        if len(added) >= 4:
            break
    cfg["frontier"] = fr[-200:]
    save_learning(cfg)
    return added


def frontier_pick(count=1):
    cfg = load_learning()
    fr = cfg.get("frontier") if isinstance(cfg.get("frontier"), list) else []
    picked = []
    for x in list(fr):
        if len(picked) >= count:
            break
        if not isinstance(x, dict) or x.get("status") == "done":
            continue
        t = str(x.get("topic") or "").strip()
        if not t:
            continue
        x["status"] = "taken"
        x["taken_at"] = int(time.time())
        picked.append(t)
    cfg["frontier"] = fr
    save_learning(cfg)
    return picked


def expand_from_entry(entry):
    entry = entry or {}
    topic = str(entry.get("topic") or "")
    if not topic or "\ufffd" in topic or topic.count("?") >= 3:
        return []
    depth = max(0, min(int(entry.get("depth") or 0) + 1, 8))
    blob = " ".join([str(entry.get("summary") or "")] + [str(x) for x in (entry.get("points") or [])] + [str(x) for x in (entry.get("tags") or [])])
    cands = []
    try:
        raw = _server_llm_json(
            "You are a curious self-learning assistant. From ONE learned topic, propose the next small sub-questions to study, from tiny to broader: who discovered or invented it, what its name or symbol means, how many types or symbols exist, simple examples, then one broader related topic. Return JSON only: {\"topics\":[\"...\",\"...\"]}. Use short searchable phrases of 2-6 words.",
            "Learned topic: " + topic + "\nNotes: " + blob[:2500],
        )
        j = _extract_json(raw or "")
        if isinstance(j, dict):
            cands = [str(x) for x in (j.get("topics") or []) if str(x).strip()]
    except Exception:
        pass
    if not cands:
        cands = ["Who discovered " + topic, "Meaning of the symbol of " + topic, "How many types of " + topic, "History of " + topic]
        proper = re.findall(r"\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,}){0,2}\b", blob)
        proper = [x for x in proper if x.casefold() not in {"the", "this", "that", "and", "for", "from", "with", "some", "many", "they", "their", "these", "those", "also", "such", "more", "most", "other", "into", "about", "over", "under", "between", "during", "while", "where", "which", "what", "when", "who", "how", "why", "all", "one", "two", "there", "here", "used", "using", "known", "called", "named", "first", "last", "some", "can", "has", "have", "its", "are", "was", "were"}]
        if proper:
            cands.append("Who was " + proper[0])
        cands += [str(x) for x in (entry.get("tags") or []) if len(str(x)) > 3]
    out = []
    for c in cands:
        c = c.strip(" .,:;()[]\"'")
        if len(c) < 3 or len(c) > 90 or c.casefold() == topic.casefold():
            continue
        out.append(c)
        if len(out) >= 5:
            break
    added = frontier_add(out, topic, depth)
    try:
        cfg = load_learning()
        cfg["expanded"] = int(cfg.get("expanded") or 0) + len(added)
        save_learning(cfg)
    except Exception:
        pass
    return added


def _learn_job_update(job_id, **kw):
    with LEARN_JOB_LOCK:
        job = LEARN_JOBS.get(job_id)
        if job:
            job.update(kw)


def _learn_job_prune():
    now = time.time()
    with LEARN_JOB_LOCK:
        for k, v in list(LEARN_JOBS.items()):
            if now - float(v.get("created_at") or 0) > 14400:
                LEARN_JOBS.pop(k, None)


def learn_busy():
    with LEARN_JOB_LOCK:
        return any(v.get("status") in ("queued", "running") for v in LEARN_JOBS.values())


def learn_job_get(job_id):
    with LEARN_JOB_LOCK:
        job = LEARN_JOBS.get(job_id)
        return dict(job) if job else None


def learn_jobs_list():
    with LEARN_JOB_LOCK:
        return sorted([dict(v) for v in LEARN_JOBS.values()], key=lambda x: x.get("created_at", 0), reverse=True)[:20]


TRACKS = {
    "วิทย์-เทคโนโลยี": ("วิทย์", "ฟิสิกส์", "เคมี", "ชีวะ", "คณิต", "AI", "วิศว", "โปรแกรม", "หุ่นยนต์", "ข้อมูล"),
    "สุขภาพ": ("แพทย์", "สุขภาพ", "ชีวะ", "เภสัช", "โภชนา", "กีฬา", "จิตวิทยา"),
    "ธุรกิจ-การเงิน": ("ธุรกิจ", "การเงิน", "บัญชี", "ตลาด", "เศรษฐ", "บริหาร", "ภาษี", "ลงทุน"),
    "ภาษา-ศิลปะ": ("ภาษา", "อังกฤษ", "จีน", "ญี่ปุ่น", "ศิลปะ", "ดนตรี", "วรรณ", "ภาพยนตร์", "นิเทศ"),
    "สังคม-กฎหมาย": ("ประวัติ", "สังคม", "รัฐ", "กฎหมาย", "นิติ", "การเมือง", "ศาสนา", "วัฒนธรรม"),
    "เกษตร-สิ่งแวดล้อม": ("เกษตร", "สิ่งแวดล้อม", "ป่าไม้", "ประมง", "ธรณี", "ภูมิอากาศ", "นิเวศ"),
}


def infer_track():
    blob = " ".join([str(x.get("topic") or "") + " " + " ".join(str(t) for t in (x.get("tags") or [])) for x in (load_knowledge().get("items") or [])])
    blob += " " + " ".join(str(w.get("topic") or "") for w in (load_watch().get("topics") or []))
    best, score = "ทั่วไป", 0
    low = blob.casefold()
    for name, kws in TRACKS.items():
        s = sum(low.count(str(k).casefold()) for k in kws)
        if s > score:
            best, score = name, s
    return best


def dev_pick(count=1):
    cfg = load_learning()
    items = dev_items()
    n = len(items)
    cur = int(cfg.get("dev_cursor") or 0) % n
    if cur >= sum(len(s[1]) + len(s[2]) for s in DEV_STAGES[:4]) and not cfg.get("track"):
        cfg["track"] = infer_track()
    picked = [items[(cur + i) % n]["topic"] for i in range(max(1, min(count or 1, 3)))]
    cfg["dev_cursor"] = (cur + len(picked)) % n
    cfg["stage"] = items[cur]["stage"]
    cfg["kind"] = items[cur]["kind"]
    save_learning(cfg)
    return picked


def _pick_curriculum(count):
    count = max(1, min(int(count or 1), 3))
    if int(load_learning().get("dev_cursor") or 0) < 31:
        picked = dev_pick(count)
        if picked:
            return picked
    picked = frontier_pick(count)
    if picked:
        return picked
    picked = dev_pick(count)
    if picked:
        return picked
    cfg = load_learning()
    n = len(CURRICULUM)
    cur = int(cfg.get("cursor") or 0) % n
    picked = [CURRICULUM[(cur + i) % n] for i in range(count)]
    cfg["cursor"] = (cur + count) % n
    save_learning(cfg)
    return picked


def _extract_json(text):
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _server_llm_json(system, user):
    """Optional: use a server-side API key (env) for higher-quality summaries."""
    timeout = 25
    groq = os.environ.get("GROQ_API_KEY", "").strip()
    if groq:
        groq_models = [os.environ.get("LEARN_LLM_MODEL", "").strip() or "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        for model in [m for m in groq_models if m]:
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": "Bearer " + groq, "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                        "temperature": 0.2,
                        "max_tokens": 1000,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=timeout,
                )
                if r.ok:
                    return (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
            except Exception:
                pass
    orkey = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if orkey:
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer " + orkey,
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/Vorakan-yakham/zyphere-ai-agent",
                    "X-Title": "Zyphere",
                },
                json={
                    "model": os.environ.get("LEARN_LLM_MODEL", "").strip() or "deepseek/deepseek-chat-v3.1:free",
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "temperature": 0.2,
                    "max_tokens": 1000,
                },
                timeout=timeout,
            )
            if r.ok:
                return (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
        except Exception:
            pass
    gkey = os.environ.get("GEMINI_API_KEY", "").strip()
    if gkey:
        try:
            model = os.environ.get("LEARN_LLM_MODEL", "").strip() or "gemini-flash-lite-latest"
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent",
                params={"key": gkey},
                json={
                    "contents": [{"role": "user", "parts": [{"text": system + "\n\n" + user}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000, "responseMimeType": "application/json"},
                },
                timeout=timeout,
            )
            if r.ok:
                parts = (((r.json().get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
                return "".join(str(p.get("text") or "") for p in parts)
        except Exception:
            pass
    return ""


def _wiki_summary(topic, lang):
    api = "https://%s.wikipedia.org/w/api.php" % ("th" if lang == "th" else "en")
    # Try the topic itself plus its meaningful parts. This keeps compound Thai
    # topics ("การนอนหลับกับสมอง") from resolving to an unrelated article.
    variants = [topic]
    for part in re.split(r"\s*(?:กับ|และ|หรือ|ของ|ใน|ต่อ|สำหรับ|เกี่ยวกับ|and|or|of|in|for|about)\s*", topic, flags=re.I):
        part = part.strip()
        if len(part) >= 3 and part.casefold() not in [v.casefold() for v in variants]:
            variants.append(part)
    candidates = []
    try:
        for q in variants[:4]:
            r = requests.get(
                api,
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": q,
                    "gsrlimit": 3,
                    "prop": "extracts|info",
                    "inprop": "url",
                    "exintro": 1,
                    "explaintext": 1,
                    "exsectionformat": "plain",
                    "redirects": 1,
                    "format": "json",
                },
                headers={"User-Agent": UA},
                timeout=12,
            )
            if not r.ok:
                continue
            r.encoding = "utf-8"
            pages = (r.json().get("query") or {}).get("pages") or {}
            for p in pages.values():
                text = (p.get("extract") or "").strip()
                if len(text) < 120:
                    continue
                title = p.get("title") or q
                candidates.append({
                    "title": title,
                    "url": p.get("fullurl") or ("https://%s.wikipedia.org/wiki/%s" % (lang, urllib.parse.quote(str(title).replace(" ", "_")))),
                    "text": text,
                    "primary": q == topic,
                })
    except Exception:
        return None
    if not candidates:
        return None

    def norm(s):
        return re.sub(r"\s+", "", str(s or "")).casefold()

    topic_n = norm(topic)
    is_ascii_topic = bool(re.search(r"[A-Za-z]", topic)) and " " in topic.strip()

    def title_set(c):
        return set(re.findall(r"[a-z0-9\u0E00-\u0E7F]", norm(c["title"])))

    topic_chars = set(re.findall(r"[a-z0-9\u0E00-\u0E7F]", topic_n))

    def char_coverage(c):
        ts = title_set(c)
        return len(ts & topic_chars) / max(1, len(ts))

    def word_coverage(c):
        stop = {"in", "of", "and", "the", "a", "an", "for", "about", "on", "to", "with", "or"}
        tt = set(re.findall(r"[a-z0-9]+", str(c["title"]).lower())) - stop
        tq = set(re.findall(r"[a-z0-9]+", topic.lower())) - stop
        return len(tt & tq) / max(1, len(tq))

    # English/Western topics: rank by how many topic words the title contains.
    if is_ascii_topic:
        pool = [c for c in candidates if c.get("primary")] or candidates
        best = max(pool, key=lambda c: (word_coverage(c), len(c["text"])))
    else:
        # Prefer candidates whose title is literally part of the topic (longest wins).
        contains = [
            c for c in candidates
            if norm(c["title"]) and norm(c["title"]) in topic_n
            and len(norm(c["title"])) >= len(topic_n) * 0.5
        ]
        if contains:
            best = max(contains, key=lambda c: (len(norm(c["title"])), len(c["text"])))
        else:
            pool = [c for c in candidates if c.get("primary")] or candidates
            best = max(pool, key=lambda c: len(c["text"]))
            # Avoid answering a positive topic with a "not/insomnia/disease" article.
            if "ไม่" not in topic and any(x in best["title"] for x in ("ไม่",)):
                alts = [c for c in candidates if "ไม่" not in c["title"] and char_coverage(c) >= 0.7]
                if alts:
                    best = max(alts, key=lambda c: (char_coverage(c), len(c["text"])))
    best["source"] = "Wikipedia"
    best["license"] = "CC BY-SA 4.0"
    best["lang"] = lang
    return best


def _keywords(text, n=8):
    toks = re.findall(r"[a-z][a-z0-9'\-]{2,}|[\u0E00-\u0E7F]{3,}", (text or "").lower())
    junk = ("ซึ่ง", "และ", "หรือ", "แปลว่า", "อังกฤษ", "กรีก", "เพราะ", "ดังนั้น", "กล่าว", "เช่น")
    freq = {}
    for t in toks:
        t = t.strip()
        if len(t) < 3 or t in STOPWORDS:
            continue
        if any(j in t for j in junk):
            continue
        freq[t] = freq.get(t, 0) + 1
    return [t for t, _ in sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))[:n]]


def _clean_text(text):
    text = re.sub(r"https?://\S+", " ", text or "")
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\{\d+\}", "", text)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _clip_at(text, n):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= n:
        return text
    cut = text[:n]
    idx = max(cut.rfind(" "), cut.rfind("."), cut.rfind("。"), cut.rfind("ฯ"), cut.rfind(";"))
    if idx > int(n * 0.55):
        cut = cut[:idx]
    return cut.rstrip(" ,;:") + "…"


def _paragraphs(text):
    text = _clean_text(text)
    out = []
    for block in re.split(r"\n+", text):
        b = re.sub(r"\s+", " ", block).strip()
        if len(b) < 60:
            continue
        if re.match(r"^(==+|<|file:|thumb|image:|see also|references|external links|อ่านเพิ่มเติม|อ้างอิง|แหล่งข้อมูล)", b, re.I):
            continue
        out.append(b)
        if len(out) >= 12:
            break
    if not out:
        flat = re.sub(r"\s+", " ", text).strip()
        if flat:
            out = [flat]
    return out


def _sentences(text):
    out = []
    for para in _paragraphs(text):
        for s in re.split(r"(?<=[.!?])\s+", para):
            s = s.strip()
            if len(s) >= 50:
                out.append(s)
    return out


# Domains/paths that are almost never useful for factual study notes.
_LOW_QUALITY_HOSTS = (
    "pinterest.", "facebook.", "instagram.", "tiktok.", "twitter.", "x.com",
    "youtube.", "quora.", "reddit.", "amazon.", "ebay.", "shopee.", "lazada.",
    "alibaba.", "aliexpress.", "tripadvisor.", "booking.com", "agoda.",
    "pantip.", "blogspot.", "wordpress.com", "medium.com", "substack.com",
)
_AD_HINTS = (
    "buy now", "add to cart", "sign up", "free trial", "subscribe", "discount",
    "coupon", "limited offer", "shop now", "order now", "click here", "affiliate",
    "sponsored", "advertisement", "ซื้อเลย", "สมัคร", "โปรโมชั่น", "ราคาพิเศษ",
    "ลดราคา", "สั่งซื้อ", "คลิก", "โฆษณา", "ดาวน์โหลดแอป",
)


def _low_quality_url(url):
    low = (url or "").lower()
    return any(h in low for h in _LOW_QUALITY_HOSTS)


def _web_quality_ok(content):
    """Reject pages that are mostly navigation, ads or marketing copy."""
    text = _clean_text(content or "")
    if len(text) < 400:
        return False
    low = text.lower()
    ad_hits = sum(low.count(h) for h in _AD_HINTS)
    # A genuine article mentions ads rarely; a shop/landing page mentions them a lot.
    if ad_hits > max(3, len(text) // 1200):
        return False
    letters = sum(1 for c in text if c.isalpha() or "\u0E00" <= c <= "\u0E7F")
    if letters < len(text) * 0.5:
        return False
    return True


def _para_ok(p):
    """Reject paragraphs that clearly start mid-sentence or are junk."""
    p = (p or "").strip()
    if len(p) < 60:
        return False
    first = p[0]
    if first.isdigit() and not re.match(r"^\d{4}\s*(ปี|พ\.ศ\.|ค\.ศ\.)", p):
        return False
    if re.match(r"^[a-z]", p):
        return False
    if re.match(r"^(และ|แต่|หรือ|ซึ่ง|โดย|ที่|ก็|จึง|อีก|รวมทั้ง|นอกจาก|เมื่อ|เพราะ|ว่า|ทั้งนี้|อย่างไรก็ตาม)", p):
        return False
    return True


def _collect_paras(texts):
    out = []
    for t in texts:
        for p in _paragraphs(t):
            if not _para_ok(p):
                continue
            if any(p[:50] == q[:50] for q in out):
                continue
            out.append(p)
    return out


def _extractive_notes(topic, primary_texts, extra_texts, lang):
    primary = _collect_paras(primary_texts)
    extra = _collect_paras(extra_texts or [])
    paras = primary + [p for p in extra if not any(p[:50] == q[:50] for q in primary)]

    lead = (primary or paras)[:3]
    summary = " ".join(_clip_at(p, 520) for p in lead[:2]).strip()
    # Only borrow from the open web when the trusted source is genuinely thin.
    if len(summary) < 450 and extra:
        summary += " " + _clip_at(extra[0], 420)
    if len(summary) < 350 and len(paras) > len(lead):
        summary += " " + _clip_at(paras[len(lead)], 360)
    summary = _clip(summary.strip(), 1400)

    points = []
    for p in (primary + extra)[:6]:
        s = _clip_at(p, 230)
        if s and not any(s[:40] == x[:40] for x in points):
            points.append(s)
        if len(points) >= 5:
            break

    tags = []
    for t in re.split(r"\s+|,|และ|กับ|\|", topic):
        t = _clip(t.strip(), 32)
        if len(t) >= 3 and t not in tags:
            tags.append(t)
    for t in _keywords(" ".join(paras[:4]), 10):
        if 3 <= len(t) <= 30 and t not in tags:
            tags.append(t)
        if len(tags) >= 6:
            break
    return {
        "title": _clip(topic, 140),
        "summary": summary or _clip(" ".join(paras), 1000),
        "points": points,
        "tags": tags[:6],
    }


def _summarize_with_llm(topic, texts, lang):
    joined = "\n\n--- SOURCE ---\n\n".join(texts)[:9000]
    system = (
        "You are the learning module of Zyphere, a personal AI assistant. "
        "Write concise, accurate study notes using ONLY facts present in the sources. "
        "Return ONLY valid JSON with this shape: "
        '{"title":"...","summary":"3-5 sentences","points":["..."],"tags":["..."]}. '
        "Write in Thai when the topic is Thai, otherwise write in English. "
        "Do not invent facts, numbers, quotes, or sources."
    )
    user = "Topic: " + topic + "\nLanguage: " + ("Thai" if lang == "th" else "English") + "\n\nSources:\n" + joined
    raw = _server_llm_json(system, user)
    if not raw:
        return None
    data = _extract_json(raw)
    if not isinstance(data, dict):
        return None
    summary = _clip(str(data.get("summary") or ""), 1400)
    if len(summary) < 40:
        return None
    points = [_clip(str(x), 240) for x in (data.get("points") or []) if str(x).strip()][:5]
    tags = [_clip(str(x), 32) for x in (data.get("tags") or []) if str(x).strip()][:6]
    title = _clip(str(data.get("title") or topic), 140) or topic
    return {"title": title, "summary": summary, "points": points, "tags": tags}


def learn_one(topic):
    topic = _clip(topic, 160)
    if not topic:
        raise RuntimeError("ต้องระบุหัวข้อที่ต้องการเรียนรู้")
    lang = _detect_lang(topic)
    sources = []
    texts = []
    wiki_texts = []
    web_texts = []

    def add_source(title, url, source, license_name=""):
        url = (url or "").strip()
        if not url or any(x.get("url") == url for x in sources):
            return
        sources.append({
            "title": _clip(title or url, 180),
            "url": url,
            "source": _clip(source or "", 60),
            "license": _clip(license_name or "", 80),
        })

    wiki = _wiki_summary(topic, lang)
    if wiki:
        add_source(wiki.get("title"), wiki.get("url"), "Wikipedia", wiki.get("license"))
        texts.append(wiki.get("text") or "")
        wiki_texts.append(wiki.get("text") or "")

    # English Wikipedia fallback for Thai labels that contain English terms
    if lang == "th" and (not wiki or len(wiki.get("text") or "") < 800):
        enq = " ".join(re.findall(r"[A-Za-z][A-Za-z0-9'\-]{2,}", topic))
        if enq:
            w2 = _wiki_summary(enq, "en")
            if w2 and (not wiki or w2.get("title") != wiki.get("title")):
                add_source(w2.get("title"), w2.get("url"), "Wikipedia (EN)", w2.get("license"))
                texts.append(w2.get("text") or "")
                wiki_texts.append(w2.get("text") or "")

    # Wikipedia is the cleanest source. If we already have a solid article,
    # skip the open web entirely: generic search results are full of ads,
    # marketing copy and navigation text that ruin extractive summaries.
    wiki_chars = sum(len(t or "") for t in wiki_texts)
    if wiki_chars < 900:
        try:
            res = search_web(topic, 6)
            for r in (res.get("results") or []):
                url = (r.get("url") or "").strip()
                if not url.startswith("http") or "wikipedia.org" in url:
                    continue
                if _low_quality_url(url):
                    continue
                page = fetch_page(url, 4500)
                if page.get("ok") and page.get("content") and _web_quality_ok(page["content"]):
                    add_source(page.get("title") or r.get("title") or url, page.get("url") or url, "เว็บ", "")
                    texts.append(page.get("content") or "")
                    web_texts.append(page.get("content") or "")
                if len(web_texts) >= 2:
                    break
        except Exception:
            pass

    if not texts:
        raise RuntimeError("ไม่พบข้อมูลเพียงพอสำหรับหัวข้อนี้ ลองใช้คำค้นที่เฉพาะเจาะจงขึ้น")

    llm_notes = _summarize_with_llm(topic, texts, lang)
    method = "llm" if llm_notes else "extractive"
    notes = llm_notes or _extractive_notes(topic, wiki_texts, web_texts, lang)
    summary = notes.get("summary") or ""
    entry_lang = "th" if re.search(r"[\u0E00-\u0E7F]", summary) else "en"
    entry = {
        "id": uuid.uuid4().hex[:12],
        "topic": topic,
        "title": notes.get("title") or topic,
        "summary": _clip(summary, 1400),
        "points": notes.get("points") or [],
        "tags": notes.get("tags") or [],
        "lang": entry_lang,
        "sources": sources,
        "method": method,
        "pages": len(texts),
        "chars": sum(len(x or "") for x in texts),
        "created_at": int(time.time()),
    }
    return add_knowledge(entry)


def _learn_worker(job_id, topics, reason):
    learned = []
    errors = []
    total = max(1, len(topics))
    _learn_job_update(job_id, status="running", progress=4, stage="กำลังเริ่มเรียนรู้")
    for i, topic in enumerate(topics):
        _learn_job_update(
            job_id,
            progress=max(4, int((i / total) * 85)),
            stage="กำลังค้นและสรุป: " + topic,
        )
        try:
            entry = learn_one(topic)
            watch_mark(topic, entry)
            try:
                added = expand_from_entry(entry)
                if added:
                    _learn_job_update(job_id, stage="ขยายความรู้: " + ", ".join(added[:2]))
            except Exception:
                pass
            learned.append({
                "id": entry.get("id"),
                "topic": entry.get("topic"),
                "title": entry.get("title"),
                "summary": _clip(entry.get("summary"), 400),
            })
        except Exception as e:
            watch_mark(topic, None, error=str(e))
            errors.append({"topic": topic, "error": _clip(str(e), 300)})
        _learn_job_update(
            job_id,
            progress=max(10, int(((i + 1) / total) * 90)),
            learned=learned,
            errors=errors,
        )
    now = int(time.time())
    try:
        cfg = load_learning()
        cfg["last_run"] = now
        cfg["last_topic"] = topics[-1] if topics else ""
        cfg["last_status"] = "ok" if learned else "error"
        save_learning(cfg)
    except Exception:
        pass
    if learned:
        _learn_job_update(job_id, status="done", progress=100, stage="เรียนรู้เสร็จแล้ว", learned=learned, errors=errors, finished_at=now)
    else:
        msg = errors[0]["error"] if errors else "ไม่พบข้อมูล"
        _learn_job_update(job_id, status="error", progress=0, stage="", error=msg, learned=learned, errors=errors, finished_at=now)
    try:
        add_learn_history({
            "reason": reason,
            "topics": list(topics or []),
            "learned": [x.get("topic") or x.get("title") or "" for x in learned],
            "errors": [x.get("topic") or "" for x in errors],
            "status": "ok" if learned else "error",
            "ts": now,
        })
    except Exception:
        pass


def create_learn_job(topics=None, count=1, rotate=False, reason="manual"):
    _learn_job_prune()
    if learn_busy():
        return None
    if rotate:
        topics = _pick_curriculum(count)
    topics = [_clip(t, 160) for t in (topics or []) if _clip(t, 160)][:3]
    if not topics:
        return None
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "stage": "อยู่ในคิว",
        "topics": topics,
        "reason": reason,
        "learned": [],
        "errors": [],
        "error": "",
        "created_at": time.time(),
    }
    with LEARN_JOB_LOCK:
        LEARN_JOBS[job_id] = job
    threading.Thread(target=_learn_worker, args=(job_id, topics, reason), daemon=True).start()
    return job


def learn_tick():
    cfg = load_learning()
    if time.time() - float(cfg.get("last_run") or 0) < 300:
        return {"ok": True, "skipped": "cooldown"}
    if learn_busy():
        return {"ok": True, "skipped": "busy"}
    due = watch_due_topics(1)
    if due:
        job = create_learn_job([due[0]["topic"]], reason="watch")
        source = "watch"
    else:
        job = create_learn_job(rotate=True, count=1, reason="cron")
        source = "curriculum"
    if not job:
        return {"ok": True, "skipped": "unavailable"}
    return {"ok": True, "id": job["id"], "status": job["status"], "topic": job["topics"][0], "source": source}


def learn_scheduler():
    while True:
        try:
            cfg = load_learning()
            if cfg.get("enabled") and not learn_busy():
                due_watch = watch_due_topics(1)
                if due_watch:
                    create_learn_job([due_watch[0]["topic"]], reason="watch")
                else:
                    interval = float(cfg.get("interval_hours") or 0)
                    if interval > 0 and time.time() - float(cfg.get("last_run") or 0) >= interval * 3600:
                        create_learn_job(rotate=True, count=1, reason="auto")
        except Exception:
            pass
        time.sleep(60)


# ----------------------------------------------------------------------------
# royalty-free image search (multiple free sources)
# ----------------------------------------------------------------------------
def _strip_html(s):
    return BeautifulSoup(str(s or ""), "html.parser").get_text(" ", strip=True)


def _image_item(title, url, page, creator, license_name, source, width=0, height=0):
    return {
        "title": _clip(title, 160),
        "url": (url or "").strip(),
        "page": (page or "").strip(),
        "creator": _clip(creator, 120),
        "license": _clip(license_name, 60),
        "source": _clip(source, 40),
        "width": int(width or 0),
        "height": int(height or 0),
    }


def search_openverse(query, n=6):
    out = []
    r = requests.get(
        "https://api.openverse.org/v1/images/",
        params={
            "q": query,
            "page_size": max(1, min(n, 20)),
            "license": "cc0,pdm,by",
            "license_type": "commercial,modification",
            "mature": "false",
        },
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=15,
    )
    if not r.ok:
        return out
    for it in (r.json().get("results") or []):
        lic = (it.get("license") or "").lower()
        if lic not in ("cc0", "pdm", "by"):
            continue
        url = it.get("url") or it.get("thumbnail") or ""
        if not url:
            continue
        out.append(_image_item(
            it.get("title") or query,
            url,
            it.get("foreign_landing_url") or "",
            it.get("creator") or "",
            {"by": "CC BY", "cc0": "CC0", "pdm": "Public Domain"}.get(lic, lic.upper()),
            it.get("source") or "Openverse",
            it.get("width") or 0,
            it.get("height") or 0,
        ))
    return out


def search_wikimedia(query, n=6):
    out = []
    r = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": "filetype:bitmap " + query,
            "gsrnamespace": 6,
            "gsrlimit": max(1, min(n, 20)),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": 1600,
            "format": "json",
        },
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=15,
    )
    if not r.ok:
        return out
    pages = (r.json().get("query") or {}).get("pages") or {}
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata") or {}
        lic = _strip_html(em.get("LicenseShortName", {}).get("value") or "")
        if re.search(r"\b(NC|ND|SA)\b", lic, re.I):
            continue
        url = ii.get("thumburl") or ii.get("url") or ""
        if not url:
            continue
        out.append(_image_item(
            p.get("title", "").replace("File:", "") or query,
            url,
            ii.get("descriptionurl") or "",
            _strip_html(em.get("Artist", {}).get("value") or ""),
            lic or "Wikimedia Commons",
            "Wikimedia Commons",
        ))
    return out


def search_pexels(query, n=6):
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key:
        return []
    r = requests.get(
        "https://api.pexels.com/v1/search",
        params={"query": query, "per_page": max(1, min(n, 20)), "orientation": "landscape"},
        headers={"Authorization": key, "User-Agent": UA},
        timeout=15,
    )
    if not r.ok:
        return []
    out = []
    for it in (r.json().get("photos") or []):
        src = it.get("src") or {}
        out.append(_image_item(
            it.get("alt") or query,
            src.get("large2x") or src.get("original") or src.get("large") or "",
            it.get("url") or "",
            it.get("photographer") or "",
            "Pexels License",
            "Pexels",
            it.get("width") or 0,
            it.get("height") or 0,
        ))
    return out


def search_pixabay(query, n=6):
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not key:
        return []
    r = requests.get(
        "https://pixabay.com/api/",
        params={"key": key, "q": query, "image_type": "photo", "orientation": "horizontal", "per_page": max(3, min(n, 20)), "safesearch": "true"},
        headers={"User-Agent": UA},
        timeout=15,
    )
    if not r.ok:
        return []
    out = []
    for it in (r.json().get("hits") or []):
        out.append(_image_item(
            it.get("tags") or query,
            it.get("largeImageURL") or it.get("webformatURL") or "",
            it.get("pageURL") or "",
            it.get("user") or "",
            "Pixabay Content License",
            "Pixabay",
            it.get("imageWidth") or 0,
            it.get("imageHeight") or 0,
        ))
    return out


def search_unsplash(query, n=6):
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    if not key:
        return []
    r = requests.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": max(1, min(n, 20)), "orientation": "landscape"},
        headers={"Authorization": "Client-ID " + key, "User-Agent": UA},
        timeout=15,
    )
    if not r.ok:
        return []
    out = []
    for it in (r.json().get("results") or []):
        urls = it.get("urls") or {}
        user = it.get("user") or {}
        out.append(_image_item(
            it.get("alt_description") or it.get("description") or query,
            urls.get("regular") or urls.get("full") or "",
            (it.get("links") or {}).get("html") or "",
            user.get("name") or "",
            "Unsplash License",
            "Unsplash",
            it.get("width") or 0,
            it.get("height") or 0,
        ))
    return out


def search_images(query, n=8):
    """Search several free image sources and merge the results.
    Prefer high-quality keyed providers, then Openverse, and use Wikimedia
    Commons only as a fallback (its search results can be less relevant).
    """
    q = _clip(query, 160)
    if not q:
        return []
    out = []
    for fn in (search_pexels, search_unsplash, search_pixabay):
        try:
            out.extend(fn(q, n))
        except Exception:
            pass
        if len(out) >= n:
            break
    if len(out) < n:
        try:
            out.extend(search_openverse(q, n))
        except Exception:
            pass
    if len(out) < max(3, n // 2):
        try:
            out.extend(search_wikimedia(q, n))
        except Exception:
            pass
    seen = set()
    uniq = []
    for it in out:
        url = it.get("url") or ""
        key = url.split("?")[0]
        if not url or key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    rank = {"Pexels": 0, "Unsplash": 0, "Pixabay": 0, "Openverse": 1, "Wikimedia Commons": 2}
    uniq.sort(key=lambda x: (0 if (x.get("width", 0) >= x.get("height", 0) and x.get("width", 0) > 0) else 1, rank.get(x.get("source"), 3)))
    return uniq[:n]


def _download_image(url, path):
    if not re.match(r"^https?://", url or "", re.I):
        raise RuntimeError("bad image url")
    r = requests.get(url, headers={"User-Agent": UA, "Accept": "image/*"}, timeout=25, stream=True)
    r.raise_for_status()
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "image" not in ctype and not re.search(r"\.(jpe?g|png|webp|gif|bmp)(\?|$)", url, re.I):
        raise RuntimeError("not an image")
    total = 0
    with open(path, "wb") as f:
        for chunk in r.iter_content(65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > 20 * 1024 * 1024:
                raise RuntimeError("image too large")
            f.write(chunk)
    with Image.open(path) as im:
        im.verify()


# ----------------------------------------------------------------------------
# video rendering
# ----------------------------------------------------------------------------
def _font(size, bold=False):
    if ImageFont is None:
        return None
    name = "NotoSansThai-Bold.ttf" if bold else "NotoSansThai-Regular.ttf"
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def _wrap(draw, text, font, maxw):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        return []
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        try:
            width = draw.textlength(test, font=font)
        except Exception:
            width = len(test) * 12
        if width <= maxw:
            cur = test
            continue
        if cur:
            lines.append(cur)
        # a single very long token (common in Thai, which has no spaces)
        try:
            tw = draw.textlength(w, font=font)
        except Exception:
            tw = len(w) * 12
        if tw > maxw:
            part = ""
            for ch in w:
                try:
                    pw = draw.textlength(part + ch, font=font)
                except Exception:
                    pw = len(part + ch) * 12
                if pw <= maxw:
                    part += ch
                else:
                    if part:
                        lines.append(part)
                    part = ch
            cur = part
        else:
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _gradient_bg(w=VIDEO_W, h=VIDEO_H):
    top = (17, 24, 48)
    bot = (74, 32, 110)
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    try:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.ellipse([int(w * 0.55), -int(h * 0.35), int(w * 1.3), int(h * 0.75)], fill=(236, 72, 153, 60))
        od.ellipse([-int(w * 0.2), int(h * 0.45), int(w * 0.65), int(h * 1.35)], fill=(59, 130, 246, 80))
        ov = ov.filter(ImageFilter.GaussianBlur(70))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    except Exception:
        pass
    return im


def _base_image(img_path, style="clean"):
    if img_path and Image is not None:
        try:
            with Image.open(img_path) as src:
                im = ImageOps.exif_transpose(src).convert("RGB")
                return ImageOps.fit(im, (VIDEO_W, VIDEO_H), method=Image.LANCZOS)
        except Exception:
            pass
    return _gradient_bg()


def _overlay(im, strength=1.0):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w, h = im.size
    for y in range(h):
        a = int(min(235, (8 + 205 * (y / max(1, h - 1)) ** 1.6) * strength))
        d.line([(0, y), (w, y)], fill=(4, 8, 18, a))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def _scene_image(img_path, title, body, idx, total, style="clean"):
    im = _base_image(img_path, style)
    if style == "dark":
        im = _overlay(im, 1.18)
    elif style == "warm":
        warm = Image.new("RGBA", im.size, (255, 140, 60, 26))
        im = Image.alpha_composite(im.convert("RGBA"), warm).convert("RGB")
        im = _overlay(im, 0.94)
    else:
        im = _overlay(im, 1.0)
    d = ImageDraw.Draw(im)
    w, h = im.size
    accent = (61, 224, 255) if style == "dark" else (139, 92, 246)
    d.rectangle([0, 0, w, 6], fill=accent)

    f_small = _font(22)
    f_title = _font(56, True)
    f_body = _font(32)
    d.text((68, 34), "ZYPHERE", font=f_small, fill=(235, 240, 250))
    d.text((w - 68, 34), f"{idx}/{total}", font=f_small, fill=(235, 240, 250), anchor="ra")

    margin = 68
    maxw = w - margin * 2
    body_lines = _wrap(d, body, f_body, maxw)[:4]
    title_lines = _wrap(d, title, f_title, maxw)[:2]
    line_h_body = 44
    line_h_title = 68
    body_h = len(body_lines) * line_h_body
    title_h = len(title_lines) * line_h_title
    block_h = title_h + body_h + 44
    box_top = h - 64 - block_h

    try:
        box = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([margin - 28, box_top - 26, w - margin + 28, h - 36], radius=26, fill=(0, 0, 0, 118))
        im = Image.alpha_composite(im.convert("RGBA"), box).convert("RGB")
        d = ImageDraw.Draw(im)
    except Exception:
        pass

    y = box_top
    for line in title_lines:
        d.text((margin, y), line, font=f_title, fill=(255, 255, 255))
        y += line_h_title
    y += 4
    for line in body_lines:
        d.text((margin, y), line, font=f_body, fill=(232, 238, 250))
        y += line_h_body
    return im


def _title_image(title, subtitle, style="clean"):
    im = _gradient_bg()
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rectangle([0, 0, w, 6], fill=(61, 224, 255) if style == "dark" else (139, 92, 246))
    f_small = _font(26)
    f_title = _font(66, True)
    f_sub = _font(30)
    d.text((68, 40), "ZYPHERE", font=f_small, fill=(220, 235, 255))
    lines = _wrap(d, title, f_title, w - 180)[:4]
    y = h // 2 - (len(lines) * 78) // 2 - 30
    for line in lines:
        d.text((90, y), line, font=f_title, fill=(255, 255, 255))
        y += 78
    if subtitle:
        for line in _wrap(d, subtitle, f_sub, w - 200)[:2]:
            d.text((92, y + 12), line, font=f_sub, fill=(190, 225, 245))
            y += 42
    return im


def _credits_image(lines, lang="th"):
    im = _gradient_bg()
    d = ImageDraw.Draw(im)
    w, h = im.size
    f_small = _font(20)
    f_title = _font(44, True)
    f_line = _font(21)
    d.text((60, 34), "ZYPHERE", font=f_small, fill=(220, 235, 255))
    d.text((60, 70), "เครดิตภาพ / Image credits", font=f_title, fill=(255, 255, 255))
    y = 150
    shown = 0
    for line in lines:
        for part in _wrap(d, line, f_line, w - 120)[:2]:
            d.text((60, y), part, font=f_line, fill=(220, 230, 245))
            y += 29
            shown += 1
            if shown >= 15:
                break
        if shown >= 15:
            d.text((60, y + 6), "...", font=f_line, fill=(220, 230, 245))
            break
    return im


def _tts_save(text, lang, path, rate=1.0):
    if edge_tts is None or not text:
        return False
    voice = VOICES.get(lang, VOICES["th"])
    pct = int(max(-40, min(60, (float(rate) - 1.0) * 100)))

    async def _run():
        com = edge_tts.Communicate(text, voice, rate=f"{pct:+d}%", pitch="-2Hz")
        await com.save(path)

    try:
        asyncio.run(_run())
        return os.path.exists(path) and os.path.getsize(path) > 1200
    except Exception:
        return False


def _silence_wav(path, seconds, rate=24000):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * max(0.5, seconds)))


def _duration(path):
    if MP3 is not None:
        try:
            return float(MP3(path).info.length)
        except Exception:
            pass
    return 0.0


def _run_ffmpeg(args, timeout=900):
    if not FFMPEG:
        raise RuntimeError("ffmpeg not available (pip install imageio-ffmpeg)")
    p = subprocess.run([FFMPEG] + args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout)
    if p.returncode != 0:
        msg = (p.stderr or b"").decode("utf-8", "ignore")[-800:]
        raise RuntimeError("ffmpeg failed: " + msg)


def _render_segment(img_path, audio_path, out_path, dur):
    dur = max(1.0, float(dur))
    args = [
        "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-r", "24", "-crf", "26", "-pix_fmt", "yuv420p", "-vf", "format=yuv420p", "-color_range", "tv",
        "-c:a", "aac", "-b:a", "128k", "-af", f"apad=whole_dur={dur:.2f}",
        "-t", f"{dur:.2f}", "-shortest",
        out_path,
    ]
    _run_ffmpeg(args, timeout=600)


def _concat_segments(paths, out_path):
    list_path = out_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for p in paths:
            f.write("file '" + p.replace("\\", "/").replace("'", "'\\''") + "'\n")
    try:
        _run_ffmpeg(["-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", "-movflags", "+faststart", out_path], timeout=600)
    finally:
        try:
            os.remove(list_path)
        except Exception:
            pass


def _detect_lang(text):
    return "th" if re.search(r"[\u0E00-\u0E7F]", text or "") else "en"


def _norm_scenes(script, topic, lang, seconds):
    scenes = []
    if isinstance(script, dict):
        topic = _clip(script.get("title") or topic, 160) or topic
        script = script.get("scenes")
    if isinstance(script, list):
        for sc in script[:10]:
            if not isinstance(sc, dict):
                continue
            title = _clip(sc.get("title") or sc.get("heading") or "", 140)
            text = _clip(sc.get("text") or sc.get("narration") or sc.get("content") or title, 500)
            query = _clip(sc.get("query") or sc.get("keywords") or title or topic, 140)
            if text or title:
                scenes.append({"title": title or topic, "text": text or title or topic, "query": query or topic})
    if not scenes:
        if lang == "th":
            scenes = [
                {"title": "เริ่มต้น", "text": f"วันนี้เราจะมาทำความรู้จักกับ {topic} ให้เข้าใจง่าย ๆ", "query": topic},
                {"title": "จุดสำคัญ", "text": f"สิ่งที่น่าสนใจเกี่ยวกับ {topic} มีหลายแง่มุมที่ควรรู้", "query": topic},
                {"title": "นำไปใช้", "text": f"เมื่อเข้าใจ {topic} แล้ว เราสามารถนำไปใช้ในชีวิตประจำวันได้ดีขึ้น", "query": topic},
                {"title": "สรุป", "text": f"สรุปสั้น ๆ ว่า {topic} เป็นเรื่องที่มีประโยชน์และน่าติดตาม", "query": topic},
            ]
        else:
            scenes = [
                {"title": "Introduction", "text": f"Today we will take a simple look at {topic}.", "query": topic},
                {"title": "Key points", "text": f"There are several interesting aspects of {topic} worth knowing.", "query": topic},
                {"title": "Practical use", "text": f"Understanding {topic} helps us use it better in daily life.", "query": topic},
                {"title": "Summary", "text": f"In short, {topic} is useful and worth learning about.", "query": topic},
            ]
    max_scenes = max(2, min(10, round(max(10, seconds) / 7)))
    return scenes[:max_scenes]


def _job_update(job_id, **kw):
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job:
            job.update(kw)


def _prune_jobs():
    now = time.time()
    with JOB_LOCK:
        for k, v in list(JOBS.items()):
            if now - float(v.get("created_at") or 0) > 7200:
                JOBS.pop(k, None)


def _video_worker(job_id, payload):
    tmp = os.path.join(DATA_DIR, "tmp_" + job_id)
    os.makedirs(tmp, exist_ok=True)
    try:
        if Image is None:
            raise RuntimeError("Pillow not installed (pip install -r requirements.txt)")
        if not FFMPEG:
            raise RuntimeError("ffmpeg not available (pip install imageio-ffmpeg)")
        topic = _clip(payload.get("topic") or "Zyphere", 160)
        lang = payload.get("lang") if payload.get("lang") in ("th", "en") else _detect_lang(topic)
        style = payload.get("style") if payload.get("style") in ("clean", "dark", "warm") else "clean"
        seconds = max(10, min(90, int(payload.get("seconds") or 30)))
        rate = max(0.8, min(1.5, float(payload.get("rate") or 1.0)))
        scenes = _norm_scenes(payload.get("script"), topic, lang, seconds)
        title = _clip((payload.get("script") or {}).get("title") if isinstance(payload.get("script"), dict) else topic, 160) or topic

        _job_update(job_id, status="running", progress=3, stage="เตรียมโครงเรื่อง", title=title)
        segments = []
        credits = []
        used = set()
        cache = {}
        add_intro = seconds >= 20
        intro_dur = 0.0

        # opening title
        if add_intro:
            intro_png = os.path.join(tmp, "intro.png")
            _title_image(title, "วิดีโอโดย Zyphere" if lang == "th" else "A video by Zyphere", style).save(intro_png, "JPEG", quality=90)
            intro_audio = os.path.join(tmp, "intro.mp3")
            intro_dur = 2.8
            if _tts_save(title, lang, intro_audio, rate):
                intro_dur = max(2.4, min(7.0, _duration(intro_audio) + 0.8))
            else:
                _silence_wav(intro_audio, intro_dur)
            intro_seg = os.path.join(tmp, "seg_intro.mp4")
            _render_segment(intro_png, intro_audio, intro_seg, intro_dur)
            segments.append(intro_seg)

        # prepare every scene first (images + narration) so we can fit the target length
        scene_items = []
        for i, sc in enumerate(scenes):
            base_prog = 6 + int((i / max(1, len(scenes))) * 58)
            _job_update(job_id, progress=base_prog, stage=f"กำลังเตรียมภาพและเสียง ฉาก {i + 1}/{len(scenes)}")
            q = sc.get("query") or sc.get("title") or topic
            if q not in cache:
                try:
                    cache[q] = search_images(q, 8)
                except Exception:
                    cache[q] = []
            pick = None
            for it in cache.get(q, []):
                if it.get("url") and it["url"] not in used:
                    pick = it
                    used.add(it["url"])
                    break
            if pick is None and cache.get(q):
                pick = cache[q][0]

            img_path = None
            if pick:
                img_path = os.path.join(tmp, f"img_{i}.jpg")
                try:
                    _download_image(pick["url"], img_path)
                except Exception:
                    img_path = None
                    pick = None
            if pick:
                credits.append({
                    "title": pick.get("title") or q,
                    "creator": pick.get("creator") or "",
                    "license": pick.get("license") or "",
                    "source": pick.get("source") or "",
                    "page": pick.get("page") or "",
                })

            scene_png = os.path.join(tmp, f"scene_{i}.jpg")
            _scene_image(img_path, sc.get("title") or topic, sc.get("text") or topic, i + 1, len(scenes), style).save(scene_png, "JPEG", quality=90)

            audio_path = os.path.join(tmp, f"scene_{i}.mp3")
            audio_dur = 4.0
            if _tts_save(sc.get("text") or sc.get("title") or topic, lang, audio_path, rate):
                audio_dur = max(1.5, _duration(audio_path))
            else:
                _silence_wav(audio_path, audio_dur)
            scene_items.append({"png": scene_png, "audio": audio_path, "audio_dur": audio_dur})

        # credits scene (prepared before rendering so its length counts toward the target)
        _job_update(job_id, progress=66, stage="กำลังสร้างเครดิตภาพ")
        credit_lines = []
        for c in credits:
            parts = [c.get("title") or "Image"]
            if c.get("creator"):
                parts.append(c["creator"])
            if c.get("license"):
                parts.append(c["license"])
            if c.get("source"):
                parts.append(c["source"])
            credit_lines.append(" — ".join(parts))
        if not credit_lines:
            credit_lines = ["ภาพพื้นหลังสร้างโดย Zyphere" if lang == "th" else "Backgrounds generated by Zyphere"]
        credit_png = os.path.join(tmp, "credits.jpg")
        _credits_image(credit_lines, lang).save(credit_png, "JPEG", quality=90)
        credit_audio = os.path.join(tmp, "credits.mp3")
        credit_text = "ภาพประกอบจากแหล่งภาพฟรี" if lang == "th" else "Images from free stock sources"
        credit_dur = 3.5
        if _tts_save(credit_text, lang, credit_audio, rate):
            credit_dur = max(2.8, min(6.0, _duration(credit_audio) + 0.8))
        else:
            _silence_wav(credit_audio, credit_dur)

        # fit scene lengths to the requested video length (narrated scenes never get cut)
        fixed = intro_dur + credit_dur
        scene_budget = max(2.5 * len(scene_items), seconds - fixed)
        per_scene = scene_budget / max(1, len(scene_items))
        for i, item in enumerate(scene_items):
            _job_update(job_id, progress=68 + int((i / max(1, len(scene_items))) * 20), stage=f"กำลังเรนเดอร์ฉาก {i + 1}/{len(scene_items)}")
            dur = max(item["audio_dur"] + 0.45, per_scene)
            dur = max(2.5, min(20.0, dur))
            seg = os.path.join(tmp, f"seg_{i}.mp4")
            _render_segment(item["png"], item["audio"], seg, dur)
            segments.append(seg)

        credit_seg = os.path.join(tmp, "seg_credits.mp4")
        _render_segment(credit_png, credit_audio, credit_seg, credit_dur)
        segments.append(credit_seg)

        _job_update(job_id, progress=94, stage="กำลังประกอบวิดีโอ")
        out_name = "video_" + job_id + ".mp4"
        out_path = os.path.join(MEDIA_DIR, out_name)
        _concat_segments(segments, out_path)
        if not os.path.exists(out_path) or os.path.getsize(out_path) < 5000:
            raise RuntimeError("video output is empty")
        _job_update(job_id, status="done", progress=100, stage="เสร็จแล้ว", url="/media/" + out_name, credits=credits, file=out_name)
    except Exception as e:
        _job_update(job_id, status="error", progress=0, stage="", error=_clip(str(e), 500))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def create_video_job(payload):
    _prune_jobs()
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "stage": "อยู่ในคิว",
        "url": "",
        "credits": [],
        "error": "",
        "created_at": time.time(),
        "title": _clip(payload.get("topic") or "Zyphere", 160),
    }
    with JOB_LOCK:
        JOBS[job_id] = job
    threading.Thread(target=_video_worker, args=(job_id, payload), daemon=True).start()
    return job


def get_job(job_id):
    with JOB_LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job else None


def list_jobs():
    with JOB_LOCK:
        return sorted([dict(v) for v in JOBS.values()], key=lambda x: x.get("created_at", 0), reverse=True)[:30]


# ----------------------------------------------------------------------------
# TTS
# ----------------------------------------------------------------------------
async def synth_tts(text, voice, rate):
    com = edge_tts.Communicate(text, voice, rate=rate, pitch="-8Hz")
    out = b""
    async for c in com.stream():
        if c["type"] == "audio":
            out += c["data"]
    return out


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, code, obj, extra_headers=None):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path.startswith("/data/"):
            self.send_error(403, "Forbidden")
            return
        if u.path == "/tts":
            q = urllib.parse.parse_qs(u.query)
            try:
                if edge_tts is None:
                    raise RuntimeError("edge-tts not installed (pip install -r requirements.txt)")
                text = q.get("text", [""])[0][:1500]
                voice = VOICES.get(q.get("lang", ["th"])[0], VOICES["th"])
                pct = int(q.get("rate", ["0"])[0])
                data = asyncio.run(synth_tts(text, voice, f"{pct:+d}%"))
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                msg = str(e).encode("ascii", "ignore").decode()[:200] or "TTS failed"
                self.send_error(500, "TTS failed", msg)
            return
        if u.path == "/api/memory":
            self._send_json(200, {"ok": True, "memory": load_mem()})
            return
        if u.path == "/api/search":
            q = urllib.parse.parse_qs(u.query)
            query = q.get("q", [""])[0]
            n = int(q.get("n", ["5"])[0] or 5)
            self._send_json(200, search_web(query, max(1, min(n, 8))))
            return
        if u.path == "/api/fetch":
            qq = urllib.parse.parse_qs(u.query)
            f_url = qq.get("url", [""])[0]
            try:
                f_chars = int(qq.get("chars", ["15000"])[0])
            except Exception:
                f_chars = 15000
            self._send_json(200, fetch_page(f_url, max(1000, min(f_chars, 60000))))
            return
        if u.path == "/api/images":
            q = urllib.parse.parse_qs(u.query)
            query = q.get("q", [""])[0]
            n = int(q.get("n", ["8"])[0] or 8)
            self._send_json(200, {"ok": True, "query": query, "results": search_images(query, max(1, min(n, 20)))})
            return
        if u.path == "/api/knowledge":
            q = urllib.parse.parse_qs(u.query)
            query = q.get("q", [""])[0]
            limit = int(q.get("limit", ["20"])[0] or 20)
            self._send_json(200, {"ok": True, **search_knowledge(query, limit)})
            return
        if u.path == "/api/watch":
            topics = watch_public()
            cfg = load_learning()
            self._send_json(200, {
                "ok": True,
                "count": len(topics),
                "topics": topics,
                "due": len(watch_due_topics(10)),
                "interval_hours": cfg.get("interval_hours") or 6,
            })
            return
        if u.path == "/api/briefing":
            q = urllib.parse.parse_qs(u.query)
            try:
                since = int(q.get("since", ["0"])[0] or 0)
            except Exception:
                since = 0
            try:
                limit = int(q.get("limit", ["12"])[0] or 12)
            except Exception:
                limit = 12
            self._send_json(200, build_briefing(since, limit))
            return
        if u.path == "/api/backup":
            q = urllib.parse.parse_qs(u.query)
            if not admin_token_ok(q.get("token", [""])[0]):
                self._send_json(403, {"ok": False, "error": "invalid backup token"})
                return
            name = "zyphere-backup-" + time.strftime("%Y%m%d-%H%M%S") + ".json"
            self._send_json(200, backup_bundle(), {
                "Content-Disposition": 'attachment; filename="%s"' % name,
            })
            return
        if u.path == "/api/storage":
            self._send_json(200, storage_public())
            return
        if u.path == "/api/learn/config":
            self._send_json(200, {"ok": True, "config": learning_public_config()})
            return
        if u.path == "/api/learn/history":
            q = urllib.parse.parse_qs(u.query)
            try:
                limit = int(q.get("limit", ["20"])[0] or 20)
            except Exception:
                limit = 20
            data = load_learn_history()
            items = (data.get("items") or [])[:max(1, min(limit, 100))]
            self._send_json(200, {"ok": True, "count": len(data.get("items") or []), "items": items})
            return
        if u.path == "/api/snapshots":
            snaps = list_snapshots()
            self._send_json(200, {"ok": True, "count": len(snaps), "snapshots": snaps, "dir": "data/snapshots"})
            return
        if u.path == "/api/learn/status":
            q = urllib.parse.parse_qs(u.query)
            job_id = q.get("id", [""])[0]
            if job_id:
                job = learn_job_get(job_id)
                if not job:
                    self._send_json(404, {"ok": False, "error": "job not found"})
                else:
                    self._send_json(200, {"ok": True, **job})
            else:
                self._send_json(200, {"ok": True, "jobs": learn_jobs_list(), "busy": learn_busy()})
            return
        if u.path == "/api/learn/tick":
            q = urllib.parse.parse_qs(u.query)
            expected = os.environ.get("LEARN_TOKEN", "").strip()
            if expected and q.get("token", [""])[0] != expected:
                self._send_json(403, {"ok": False, "error": "invalid token"})
                return
            self._send_json(200, learn_tick())
            return
        if u.path == "/api/video/status":
            q = urllib.parse.parse_qs(u.query)
            job = get_job(q.get("id", [""])[0])
            if not job:
                self._send_json(404, {"ok": False, "error": "job not found"})
            else:
                self._send_json(200, {"ok": True, **job})
            return
        if u.path == "/api/video/list":
            self._send_json(200, {"ok": True, "jobs": list_jobs()})
            return
        if u.path == "/api/lang/detect":
            q = urllib.parse.parse_qs(u.query)
            txt = q.get("text", [""])[0]
            code = detect_lang(txt)
            self._send_json(200, {"ok": True, "code": code, "name": LANG_NAMES.get(code, code)})
            return
        if u.path == "/api/health":
            self._send_json(200, {
                "ok": True,
                "name": "zyphere",
                "version": 21,
                "features": ["search", "fetch", "memory", "tts", "images", "video", "learn", "knowledge", "watch", "briefing", "backup", "restore", "remote_kv"],
                "image_sources": ["openverse", "wikimedia", "pexels", "pixabay", "unsplash"],
                "video": bool(Image and FFMPEG),
                "knowledge_count": knowledge_count(),
                "watch_count": len(load_watch().get("topics") or []),
                "storage": {
                    "remote": remote_enabled(),
                    "backup_token": bool(os.environ.get("BACKUP_TOKEN", "").strip()),
                },
                "learning": {
                    "topics": len(CURRICULUM),
                    "server_llm": bool(
                        os.environ.get("GROQ_API_KEY")
                        or os.environ.get("OPENROUTER_API_KEY")
                        or os.environ.get("GEMINI_API_KEY")
                    ),
                },
            })
            return
        return super().do_GET()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except Exception:
            length = 0
        if length > (8_000_000 if u.path == "/api/restore" else 300_000):
            self._send_json(413, {"ok": False, "error": "payload too large"})
            return
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        if u.path == "/api/text/polish":
            try:
                result = polish_text(body.get("text") or "", body.get("lang") or "th")
                self._send_json(200, result)
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 300)})
            return
        if u.path == "/api/translate":
            try:
                result = translate_text(body.get("text") or "", body.get("target") or "th", body.get("source") or "")
                self._send_json(200, result)
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 300)})
            return
        if u.path == "/api/memory":
            mem = memory_update(body)
            self._send_json(200, {"ok": True, "memory": mem})
            return
        if u.path == "/api/search":
            self._send_json(200, search_web(body.get("q", ""), int(body.get("n", 5) or 5)))
            return
        if u.path == "/api/fetch":
            try:
                f_chars = int(body.get("chars", 15000) or 15000)
            except Exception:
                f_chars = 15000
            self._send_json(200, fetch_page(body.get("url", ""), max(1000, min(f_chars, 60000))))
            return
        if u.path == "/api/knowledge":
            if body.get("clear"):
                make_snapshot("before-clear")
                clear_knowledge()
                self._send_json(200, {"ok": True, "cleared": True, "total": 0})
                return
            if body.get("delete"):
                make_snapshot("before-delete")
                removed = delete_knowledge(body.get("delete"))
                self._send_json(200, {"ok": True, "removed": removed, "total": knowledge_count()})
                return
            self._send_json(400, {"ok": False, "error": "nothing to do"})
            return
        if u.path == "/api/watch":
            if body.get("clear"):
                watch_clear()
                self._send_json(200, {"ok": True, "cleared": True, "topics": watch_public()})
                return
            if body.get("remove"):
                removed = watch_remove(body.get("remove"))
                self._send_json(200, {"ok": True, "removed": removed, "topics": watch_public()})
                return
            topic = _clip(body.get("topic") or body.get("q") or "", 160)
            if not topic:
                self._send_json(400, {"ok": False, "error": "missing topic"})
                return
            try:
                entry = watch_add(topic, body.get("notes") or "", refresh=bool(body.get("refresh")))
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 300)})
                return
            job = None
            if body.get("learn"):
                job = create_learn_job([topic], reason="watch")
            self._send_json(200, {
                "ok": True,
                "watch": entry,
                "topics": watch_public(),
                "job": ({"id": job["id"], "status": job["status"]} if job else None),
                "busy": learn_busy(),
            })
            return
        if u.path == "/api/restore":
            if not admin_token_ok(body.get("token") or ""):
                self._send_json(403, {"ok": False, "error": "invalid backup token"})
                return
            if not body.get("confirm"):
                self._send_json(400, {"ok": False, "error": "ต้องยืนยันการกู้คืน (confirm: true)"})
                return
            try:
                make_snapshot("before-restore")
                result = restore_bundle(body)
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 400)})
                return
            self._send_json(200, result)
            return
        if u.path == "/api/snapshots":
            snap = make_snapshot(body.get("reason") or "manual")
            if not snap.get("ok"):
                self._send_json(500, {"ok": False, "error": snap.get("error") or "snapshot failed"})
                return
            self._send_json(200, {"ok": True, "snapshot": snap, "snapshots": list_snapshots()})
            return
        if u.path == "/api/snapshots/restore":
            if not admin_token_ok(body.get("token") or ""):
                self._send_json(403, {"ok": False, "error": "invalid backup token"})
                return
            if not body.get("confirm"):
                self._send_json(400, {"ok": False, "error": "ต้องยืนยันการกู้คืน (confirm: true)"})
                return
            try:
                make_snapshot("before-snapshot-restore")
                result = restore_snapshot(body.get("name") or "")
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 400)})
                return
            self._send_json(200, result)
            return
        if u.path in ("/api/storage/sync", "/api/storage/pull"):
            if not admin_token_ok(body.get("token") or ""):
                self._send_json(403, {"ok": False, "error": "invalid backup token"})
                return
            if u.path == "/api/storage/sync":
                result = remote_push_all()
            else:
                make_snapshot("before-pull")
                result = remote_pull_all()
            self._send_json(200, result)
            return
        if u.path == "/api/learn/config":
            cfg = learning_update(body)
            self._send_json(200, {"ok": True, "config": learning_public_config(), "saved": cfg})
            return
        if u.path == "/api/learn":
            topic = _clip(body.get("topic") or "", 160)
            topics = body.get("topics") if isinstance(body.get("topics"), list) else []
            rotate = bool(body.get("rotate"))
            count = int(body.get("count") or 1)
            if rotate:
                job = create_learn_job(rotate=True, count=max(1, min(count, 3)), reason="manual")
            else:
                wanted = [topic] if topic else []
                wanted.extend([_clip(str(x), 160) for x in topics])
                wanted = [x for x in wanted if x]
                if not wanted:
                    self._send_json(400, {"ok": False, "error": "missing topic"})
                    return
                job = create_learn_job(wanted, reason="manual")
            if not job:
                self._send_json(409, {"ok": False, "error": "มีงานเรียนรู้กำลังทำงานอยู่ หรือไม่มีหัวข้อ"})
                return
            self._send_json(200, {"ok": True, "id": job["id"], "status": job["status"], "topics": job["topics"]})
            return
        if u.path == "/api/learn/once":
            topic = _clip(body.get("topic") or body.get("q") or "", 160)
            if not topic:
                self._send_json(400, {"ok": False, "error": "missing topic"})
                return
            try:
                entry = learn_one(topic)
                watch_mark(topic, entry)
                try:
                    expand_from_entry(entry)
                except Exception:
                    pass
                cfg = load_learning()
                cfg["last_run"] = int(time.time())
                cfg["last_topic"] = topic
                cfg["last_status"] = "ok"
                save_learning(cfg)
                add_learn_history({"reason": "once", "topics": [topic], "learned": [topic], "errors": [], "status": "ok"})
                self._send_json(200, {"ok": True, "entry": entry, "total": knowledge_count()})
            except Exception as e:
                add_learn_history({"reason": "once", "topics": [topic], "learned": [], "errors": [topic], "status": "error"})
                self._send_json(500, {"ok": False, "error": _clip(str(e), 500)})
            return
        if u.path == "/api/video":
            if Image is None or not FFMPEG:
                self._send_json(500, {"ok": False, "error": "video engine not available; run pip install -r requirements.txt"})
                return
            topic = _clip(body.get("topic") or "", 160)
            if not topic and not body.get("script"):
                self._send_json(400, {"ok": False, "error": "missing topic"})
                return
            job = create_video_job(body)
            self._send_json(200, {"ok": True, "id": job["id"], "status": job["status"]})
            return
        self._send_json(404, {"ok": False, "error": "not found"})


class Server(ThreadingHTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    if remote_enabled():
        try:
            boot = remote_pull_all()
            print("Remote storage:", boot.get("restored") or "nothing to restore")
        except Exception as e:
            print("Remote storage unavailable:", str(e)[:120])
    threading.Thread(target=learn_scheduler, daemon=True).start()
    with Server(("", PORT), Handler) as s:
        print(f"Zyphere COMPLETE21: http://localhost:{PORT}")
        print("Autonomous learning: every %.0f h (configurable in the Knowledge panel)" % (load_learning().get("interval_hours") or 6))
        print("Watchlist:", len(load_watch().get("topics") or []), "topic(s); remote KV:", "on" if remote_enabled() else "off")
        if Image is None or not FFMPEG:
            print("WARNING: video engine missing. Run: pip install -r requirements.txt")
        elif not os.environ.get("PORT"):
            try:
                import webbrowser
                webbrowser.open(f"http://localhost:{PORT}")
            except Exception:
                pass
        s.serve_forever()
