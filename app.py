"""Zyphere COMPLETE17 local server
- Serve the web UI
- TTS via edge-tts (/tts)
- Agent tools backend: web search, page fetch, persistent memory

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
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests
from bs4 import BeautifulSoup

try:
    import edge_tts
except ImportError:
    edge_tts = None

PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEM_PATH = os.path.join(DATA_DIR, "memory.json")
VOICES = {"th": "th-TH-NiwatNeural", "en": "en-GB-RyanNeural"}
MEM_LOCK = threading.Lock()

os.makedirs(DATA_DIR, exist_ok=True)


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


def search_web(query, max_results=5):
    q = _clip(query, 300)
    if not q:
        return {"ok": False, "error": "empty query", "results": []}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Zyphere/17; +http://localhost)"}
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


def fetch_page(url, max_chars=6000):
    url = (url or "").strip()
    if not url:
        return {"ok": False, "error": "empty url"}
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Zyphere/17; +http://localhost)"}
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


async def synth_tts(text, voice, rate):
    com = edge_tts.Communicate(text, voice, rate=rate, pitch="-8Hz")
    out = b""
    async for c in com.stream():
        if c["type"] == "audio":
            out += c["data"]
    return out


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
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
            q = urllib.parse.parse_qs(u.query)
            url = q.get("url", [""])[0]
            self._send_json(200, fetch_page(url))
            return
        if u.path == "/api/health":
            self._send_json(200, {"ok": True, "name": "zyphere", "version": 17})
            return
        return super().do_GET()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except Exception:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            body = {}
        if u.path == "/api/memory":
            mem = memory_update(body)
            self._send_json(200, {"ok": True, "memory": mem})
            return
        if u.path == "/api/search":
            self._send_json(200, search_web(body.get("q", ""), int(body.get("n", 5) or 5)))
            return
        if u.path == "/api/fetch":
            self._send_json(200, fetch_page(body.get("url", "")))
            return
        self._send_json(404, {"ok": False, "error": "not found"})


class Server(ThreadingHTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    with Server(("", PORT), Handler) as s:
        print(f"Zyphere COMPLETE17: http://localhost:{PORT}")
        try:
            import webbrowser
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass
        s.serve_forever()
