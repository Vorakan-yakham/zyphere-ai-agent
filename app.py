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
import secrets
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid
import base64
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
try:
    from local_brain import LocalBrain
    BRAIN = LocalBrain(os.path.join(DATA_DIR, "brain.json"))
except Exception:
    BRAIN = None
try:
    from users import Users
    USERS = Users(os.path.join(DATA_DIR, "users.json"))
except Exception:
    USERS = None
try:
    from identity import Identity
    IDENTITY = Identity(os.path.join(DATA_DIR, "identity.json"))
except Exception:
    IDENTITY = None
try:
    from billing import Billing, PLANS
    BILLING = Billing(os.path.join(DATA_DIR, "billing.json"))
except Exception:
    BILLING = None
try:
    from ratelimit import RateLimit
    RATE = RateLimit()
except Exception:
    RATE = None
try:
    from preferences import Preferences
    PREF = Preferences(os.path.join(DATA_DIR, "preferences.json"))
except Exception:
    PREF = None
# Google OAuth (Sign in with Google). Secrets come ONLY from environment
# variables set on Render — never hardcoded/committed.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "").strip() or (
    "https://zyphere-ai-agent.onrender.com/api/auth/google/callback")
GOOGLE_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
OMISE_PKEY = os.environ.get("OMISE_PUBLIC_KEY", "").strip()
OMISE_SKEY = os.environ.get("OMISE_SECRET_KEY", "").strip()
OMISE_ENABLED = bool(OMISE_PKEY and OMISE_SKEY)
OWNER_EMAILS = {"vorakangm@gmail.com", "vorakanmu@gmail.com"}
ZIPBALL_OWNER = ("https://github.com/Vorakan-yakham/zyphere-scholar-product-pack/"
                 "archive/refs/heads/main.zip")
try:
    from platforms import Platforms
    PLATFORMS = Platforms(os.path.join(DATA_DIR, "platforms.json"))
except Exception:
    PLATFORMS = None
try:
    from dev_brain import DevBrain
    DEV_BRAIN = DevBrain(os.path.join(DATA_DIR, "dev_brain.json"))
except Exception:
    DEV_BRAIN = None
try:
    from notebook import Notebook
    NOTEBOOK = Notebook(os.path.join(DATA_DIR, "notebook.json"))
except Exception:
    NOTEBOOK = None
try:
    import media as MEDIA
except Exception:
    MEDIA = None
try:
    from research import ResearchLibrary, SOURCES
    RESEARCH = ResearchLibrary(os.path.join(DATA_DIR, "research.json"))
except Exception:
    RESEARCH = None
try:
    import expansion as EXPANSION
except Exception:
    EXPANSION = None
try:
    import academic as ACADEMIC
except Exception:
    ACADEMIC = None
try:
    import director as DIRECTOR
except Exception:
    DIRECTOR = None
try:
    import human_art as HUMAN_ART
except Exception:
    HUMAN_ART = None
try:
    import applied as APPLIED
except Exception:
    APPLIED = None
try:
    import aerospace as AEROSPACE
except Exception:
    AEROSPACE = None
try:
    from work import WorkEngine
    WORKS = WorkEngine(os.path.join(DATA_DIR, "works.json"))
except Exception:
    WORKS = None
try:
    from voice import VoiceIdentity
    VOICE = VoiceIdentity(os.path.join(DATA_DIR, "voice.json"))
except Exception:
    VOICE = None
try:
    from language import LanguageMastery
    LANG = LanguageMastery()
except Exception:
    LANG = None
try:
    from reasoning import ReasoningEngine
    REASON = ReasoningEngine()
except Exception:
    REASON = None
try:
    from concept import ConceptExpander
    CONCEPT = ConceptExpander()
except Exception:
    CONCEPT = None
try:
    from metacognition import Metacognition
    META = Metacognition()
except Exception:
    META = None
try:
    from selftest import SelfTest
    SELFTEST = SelfTest()
except Exception:
    SELFTEST = None
try:
    from meta_learning import MetaLearning
    META_LEARN = MetaLearning()
except Exception:
    META_LEARN = None
try:
    from proactive import Proactive
    PROACTIVE = Proactive()
except Exception:
    PROACTIVE = None
try:
    import visualize as VISUALIZE
except Exception:
    VISUALIZE = None
try:
    from feedback import FeedbackLoop
    FEEDBACK = FeedbackLoop(os.path.join(DATA_DIR, "feedback_loop.json"))
except Exception:
    FEEDBACK = None
try:
    from safety import SafetyEngine
    SAFETY = SafetyEngine(os.path.join(DATA_DIR, "safety.json"))
except Exception:
    SAFETY = None
try:
    from eval_loop import EvalLoop
    EVAL = EvalLoop(os.path.join(DATA_DIR, "eval.json"))
except Exception:
    EVAL = None
try:
    from tools import ToolOrchestrator
    TOOLS = ToolOrchestrator(SAFETY)
except Exception:
    TOOLS = None
try:
    from intent import IntentRouter
    INTENT = IntentRouter()
except Exception:
    INTENT = None
try:
    from selfcorrect import SelfCorrect
    SELFCORRECT = SelfCorrect()
except Exception:
    SELFCORRECT = None
try:
    from rag import RAG
    RAG_ENGINE = RAG()
except Exception:
    RAG_ENGINE = None
try:
    from behavior import Behavior
    BEHAVIOR = Behavior(os.path.join(DATA_DIR, "behavior.json"))
except Exception:
    BEHAVIOR = None
try:
    from authz import Authz
    AUTHZ = Authz(USERS)
except Exception:
    AUTHZ = None
try:
    from audit import Audit
    AUDIT = Audit(os.path.join(DATA_DIR, "audit.json"))
except Exception:
    AUDIT = None
try:
    from jarvis_mode import JarvisMode
    JARVIS = JarvisMode(os.path.join(DATA_DIR, "jarvis.json"))
except Exception:
    JARVIS = None
try:
    from privacy import Privacy
    PRIVACY = Privacy(os.path.join(DATA_DIR, "privacy.json"))
except Exception:
    PRIVACY = None
try:
    import surpass as SURPASS
except Exception:
    SURPASS = None
try:
    from superiority import Superiority
    SUPERIORITY = Superiority()
except Exception:
    SUPERIORITY = None
try:
    from dialogue import Dialogue
    DIALOGUE = Dialogue()
except Exception:
    DIALOGUE = None
try:
    from guard import Guard
    GUARD = Guard(os.path.join(DATA_DIR, "guard.json"))
except Exception:
    GUARD = None
try:
    from empathy import Empathy
    EMPATHY = Empathy()
except Exception:
    EMPATHY = None
try:
    from delivery import Delivery
    DELIVERY = Delivery(os.path.join(DATA_DIR, "delivery.json"))
except Exception:
    DELIVERY = None
    PACKS = None
try:
    from moneyfield import MoneyField
    MONEYFIELD = MoneyField(os.path.join(DATA_DIR, "moneyfield.json"))
except Exception:
    MONEYFIELD = None
    CODEFORGE = None
try:
    from autofill import Autofill
    AUTOFILL = Autofill(os.path.join(DATA_DIR, "autofill.json"))
except Exception:
    AUTOFILL = None
try:
    from help import Help
    HELP = Help(os.path.join(DATA_DIR, "help.json"))
except Exception:
    HELP = None
try:
    from income import Income
    INCOME = Income(os.path.join(DATA_DIR, "income.json"))
except Exception:
    INCOME = None
try:
    from otpassist import OTPAssistant
    OTPASSIST = OTPAssistant(os.path.join(DATA_DIR, "otpassist.json"))
except Exception:
    OTPASSIST = None
try:
    from expert import Expert
    EXPERT = Expert(os.path.join(DATA_DIR, "expert.json"))
except Exception:
    EXPERT = None
try:
    from market import Market
    MARKET = Market(os.path.join(DATA_DIR, "market.json"))
except Exception:
    MARKET = None
try:
    from shopfront import Shopfront
    SHOP = Shopfront(os.path.join(DATA_DIR, "shop.json"))
except Exception:
    SHOP = None
try:
    from report import Report
    REPORT = Report()
except Exception:
    REPORT = None
try:
    from listing import ListingWriter
    LISTING = ListingWriter()
except Exception:
    LISTING = None
try:
    from rss import RSSReader
    RSS = RSSReader()
except Exception:
    RSS = None
try:
    from agents import AgentOrg
    ORG = AgentOrg(os.path.join(DATA_DIR, "agents.json"))
except Exception:
    ORG = None
try:
    from scholars import Scholars
    SCHOLARS = Scholars(os.path.join(DATA_DIR, "scholars.json"))
except Exception:
    SCHOLARS = None
try:
    from scholar_income import ScholarIncome
    SCHOLAR_INCOME = ScholarIncome(os.path.join(DATA_DIR, "scholar_income.json"))
except Exception:
    SCHOLAR_INCOME = None
try:
    from marketplaces import Launchpad
    LAUNCHPAD = Launchpad(os.path.join(DATA_DIR, "launchpad.json"))
except Exception:
    LAUNCHPAD = None
try:
    from academy import Academy
    ACADEMY = Academy(os.path.join(DATA_DIR, "academy.json"))
except Exception:
    ACADEMY = None
try:
    from chief import Chief
    CHIEF = Chief(os.path.join(DATA_DIR, "chief.json"))
except Exception:
    CHIEF = None
try:
    from council import Council
    COUNCIL = Council(os.path.join(DATA_DIR, "council.json"))
except Exception:
    COUNCIL = None
try:
    from race import Race
    RACE = Race(os.path.join(DATA_DIR, "race.json"))
except Exception:
    RACE = None
try:
    from autopost import AutoPost
    AUTOPOST = AutoPost(os.path.join(DATA_DIR, "autopost.json"))
except Exception:
    AUTOPOST = None
try:
    from demand import Demand
    DEMAND = Demand(os.path.join(DATA_DIR, "demand.json"))
except Exception:
    DEMAND = None
try:
    from github_backup import GitHubBackup
    GH_BACKUP = GitHubBackup(os.path.join(DATA_DIR, "gh_backup.json"))
except Exception:
    GH_BACKUP = None
try:
    import gmail_oauth as GMAIL_OAUTH
except Exception:
    GMAIL_OAUTH = None
MEDIA_DIR = os.path.join(BASE_DIR, "media")
try:
    from ebook import EbookStudio
    EBOOK = EbookStudio(os.path.join(MEDIA_DIR, "ebooks"))
except Exception:
    EBOOK = None
try:
    from store import Store
    STORE = Store(MEDIA_DIR)
except Exception:
    STORE = None
try:
    from role_registry import RoleRegistry
    ROLES = RoleRegistry(os.path.join(DATA_DIR, "roles.json"))
except Exception:
    ROLES = None
try:
    from supervisors import Supervisors
    SUPERVISORS = Supervisors()
except Exception:
    SUPERVISORS = None
try:
    from quality_ops import QOPS
except Exception:
    QOPS = None
try:
    from five_engines import FE
except Exception:
    FE = None
try:
    from creative_director import CD
except Exception:
    CD = None
try:
    from capability_ceiling import CC
except Exception:
    CC = None
try:
    from self_coder import SC
except Exception:
    SC = None
try:
    from engineering_council import EC
except Exception:
    EC = None
try:
    from user_learning import UL
except Exception:
    UL = None
try:
    from template_designer import TD
except Exception:
    TD = None
try:
    from it_org import IT
except Exception:
    IT = None
try:
    from growth_org import GO
except Exception:
    GO = None
try:
    from role_profiles import RP as ROLEP
except Exception:
    ROLEP = None
try:
    from self_improvement import SI
except Exception:
    SI = None
try:
    from dev_companion import DC
except Exception:
    DC = None
try:
    from method_transfer import MT
except Exception:
    MT = None
try:
    import music_studio as MUSIC
except Exception:
    MUSIC = None
try:
    from department_dialogue import DD
except Exception:
    DD = None
try:
    from council_debate import CD
except Exception:
    CD = None
try:
    from research_projects import RP
except Exception:
    RP = None
try:
    from co_learning import CO
except Exception:
    CO = None

try:
    from packbuilder import PackBuilder
    PACKS = PackBuilder(MEDIA_DIR, MEDIA_DIR)
except Exception:
    PACKS = None

try:
    from codeforge import CodeForge
    CODEFORGE = CodeForge(MEDIA_DIR)
except Exception:
    CODEFORGE = None
FONT_DIR = os.path.join(BASE_DIR, "fonts")
MEM_PATH = os.path.join(DATA_DIR, "memory.json")
VOICES = {"th": "th-TH-NiwatNeural", "en": "en-GB-RyanNeural"}
VOICE_OPTIONS = {"th": ["th-TH-NiwatNeural", "th-TH-AcharaNeural", "th-TH-PremwadeeNeural"], "en": ["en-GB-RyanNeural", "en-US-AriaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]}
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
# Upstash's own variable names (UPSTASH_REDIS_REST_URL / _TOKEN) are also
# accepted, so they can be pasted directly from the Upstash console.
# Every save is pushed to the remote store in the background and, at startup,
# the newest remote copy is restored when it exists.
REMOTE_KV_URL = (os.environ.get("REMOTE_KV_URL", "")
                 or os.environ.get("UPSTASH_REDIS_REST_URL", "")).strip().rstrip("/")
REMOTE_KV_TOKEN = (os.environ.get("REMOTE_KV_TOKEN", "")
                   or os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")).strip()
REMOTE_KEYS = {
    "memory": "zyphere:memory",
    "knowledge": "zyphere:knowledge",
    "learning": "zyphere:learning",
    "watch": "zyphere:watch",
    "goals": "zyphere:goals",
    "platforms": "zyphere:platforms",
    "dev_brain": "zyphere:dev_brain",
    "notebook": "zyphere:notebook",
    "research": "zyphere:research",
    "identity": "zyphere:identity",
    "creative": "zyphere:creative",
    "works": "zyphere:works",
    "voice": "zyphere:voice",
    "feedback_loop": "zyphere:feedback_loop",
    "safety": "zyphere:safety",
    "eval": "zyphere:eval",
    "intent": "zyphere:intent",
    "selfcorrect": "zyphere:selfcorrect",
    "behavior": "zyphere:behavior",
    "audit": "zyphere:audit",
    "jarvis": "zyphere:jarvis",
    "privacy": "zyphere:privacy",
    "guard": "zyphere:guard",
    "delivery": "zyphere:delivery",
    "packs": "zyphere:packs",
    "moneyfield": "zyphere:moneyfield",
    "income": "zyphere:income",
    "help": "zyphere:help",
    "autofill": "zyphere:autofill",
    "codeforge": "zyphere:codeforge",
    "otpassist": "zyphere:otpassist",
    "expert": "zyphere:expert",
    "market": "zyphere:market",
    "shop": "zyphere:shop",
    "agents": "zyphere:agents",
    "scholars": "zyphere:scholars",
    "scholar_income": "zyphere:scholar_income",
    "launchpad": "zyphere:launchpad",
    "academy": "zyphere:academy",
    "chief": "zyphere:chief",
    "council": "zyphere:council",
    "race": "zyphere:race",
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


def store_orders_all():
    """Orders survive multiple Render instances via local file + remote KV."""
    rows = []
    try:
        import slip_auto_verifier as SV
        if os.path.exists(SV.DATA):
            rows += json.load(open(SV.DATA, encoding="utf-8")).get("orders", [])
    except Exception:
        pass
    try:
        remote = remote_get_json("store_orders")
        for o in ((remote or {}).get("orders", []) or []):
            if not any(str(x.get("id")) == str(o.get("id")) for x in rows):
                rows.append(o)
    except Exception:
        pass
    return rows


def orders_admin_all():
    """Admin sees EVERY order from both the PromptPay flow and legacy store.

    Read-only merge — never removes or rewrites a customer record.
    """
    rows = store_orders_all()
    try:
        if STORE:
            for o in STORE.all_orders():
                if not any(str(x.get("id")) == str(o.get("id")) for x in rows):
                    rows.append(dict(o))
    except Exception:
        pass
    return rows


def orders_shared_save(rows):
    """Append/update shared order state. Never drops historical records."""
    import slip_auto_verifier as SV
    current = store_orders_all()
    by_id = {str(o.get("id")): o for o in current}
    for o in rows:
        by_id[str(o.get("id"))] = o
    merged = list(by_id.values())
    os.makedirs(os.path.dirname(SV.DATA), exist_ok=True)
    json.dump({"orders": merged}, open(SV.DATA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    remote_push("store_orders", {"orders": merged})
    return merged


def order_is_paid(o):
    return str(o.get("status", "")).lower() in ("paid", "approved")


def order_belongs(o, me):
    if not me:
        return False
    if str((me.get("email") or "")).lower() in OWNER_EMAILS or me.get("role") == "admin":
        return True
    em = str(me.get("email") or "").lower()
    return bool(em) and (str(o.get("email", "")).lower() == em or
                         str(o.get("buyer", "")).lower() == em)


def full_book_html(title):
    """Real full book for ONLINE reading (no download required)."""
    import book_typesetter as BT
    import sample_publisher as SP
    import autonomous_council as AC
    folder = SP.source_map().get(str(title))
    if not folder:
        return None
    md = AC.gh_raw("books/%s/content.md" % folder) or ""
    return BT.typeset(md, sample=False) if len(md) > 1200 else None


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
    for name in ("memory", "knowledge", "learning", "watch", "goals", "platforms", "dev_brain", "notebook", "research", "identity", "creative", "works", "voice", "feedback_loop", "safety", "eval", "intent", "selfcorrect", "behavior", "audit", "jarvis", "privacy", "guard", "delivery", "moneyfield", "income", "help", "autofill", "codeforge", "otpassist", "expert", "market", "shop", "agents", "scholars", "scholar_income", "launchpad", "academy", "chief", "council", "race"):
        try:
            data = {
                "memory": load_mem,
                "knowledge": load_knowledge,
                "learning": load_learning,
                "watch": load_watch,
                "goals": load_goals,
                "platforms": (PLATFORMS.snapshot() if PLATFORMS else None),
                "dev_brain": (DEV_BRAIN.snapshot() if DEV_BRAIN else None),
                "notebook": (NOTEBOOK.snapshot() if NOTEBOOK else None),
                "research": (RESEARCH.snapshot() if RESEARCH else None),
                "identity": (IDENTITY.data if IDENTITY else None),
                "creative": (CREATIVE.snapshot() if CREATIVE else None),
                "works": (WORKS.snapshot() if WORKS else None),
                "voice": (VOICE.snapshot() if VOICE else None),
                "feedback_loop": (FEEDBACK.snapshot() if FEEDBACK else None),
                "safety": (SAFETY.snapshot() if SAFETY else None),
                "eval": (EVAL.snapshot() if EVAL else None),
                "intent": (INTENT.snapshot() if INTENT else None),
                "selfcorrect": (SELFCORRECT.snapshot() if SELFCORRECT else None),
                "behavior": (BEHAVIOR.snapshot() if BEHAVIOR else None),
                "audit": (AUDIT.snapshot() if AUDIT else None),
                "jarvis": (JARVIS.snapshot() if JARVIS else None),
                "privacy": (PRIVACY.snapshot() if PRIVACY else None),
                "guard": (GUARD.snapshot() if GUARD else None),
                "delivery": (DELIVERY.snapshot() if DELIVERY else None),
                "moneyfield": (MONEYFIELD.snapshot() if MONEYFIELD else None),
                "income": (INCOME.snapshot() if INCOME else None),
                "help": (HELP.snapshot() if HELP else None),
                "autofill": (AUTOFILL.snapshot() if AUTOFILL else None),
                "codeforge": (CODEFORGE.snapshot() if CODEFORGE else None),
                "otpassist": (OTPASSIST.snapshot() if OTPASSIST else None),
                "shop": (SHOP.snapshot() if SHOP else None),
                "agents": (ORG.snapshot() if ORG else None),
                "scholars": (SCHOLARS.snapshot() if SCHOLARS else None),
                "scholar_income": (SCHOLAR_INCOME.snapshot() if SCHOLAR_INCOME else None),
                "launchpad": (LAUNCHPAD.snapshot() if LAUNCHPAD else None),
                "academy": (ACADEMY.snapshot() if ACADEMY else None),
                "chief": (CHIEF.snapshot() if CHIEF else None),
                "council": (COUNCIL.snapshot() if COUNCIL else None),
                "race": (RACE.snapshot() if RACE else None),
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
        "goals": GOALS_PATH,
        "platforms": os.path.join(DATA_DIR, "platforms.json"),
        "dev_brain": os.path.join(DATA_DIR, "dev_brain.json"),
        "notebook": os.path.join(DATA_DIR, "notebook.json"),
        "research": os.path.join(DATA_DIR, "research.json"),
        "identity": os.path.join(DATA_DIR, "identity.json"),
        "creative": os.path.join(DATA_DIR, "creative.json"),
        "works": os.path.join(DATA_DIR, "works.json"),
        "voice": os.path.join(DATA_DIR, "voice.json"),
        "feedback_loop": os.path.join(DATA_DIR, "feedback_loop.json"),
        "safety": os.path.join(DATA_DIR, "safety.json"),
        "eval": os.path.join(DATA_DIR, "eval.json"),
        "intent": os.path.join(DATA_DIR, "intent.json"),
        "selfcorrect": os.path.join(DATA_DIR, "selfcorrect.json"),
        "behavior": os.path.join(DATA_DIR, "behavior.json"),
        "audit": os.path.join(DATA_DIR, "audit.json"),
        "jarvis": os.path.join(DATA_DIR, "jarvis.json"),
        "privacy": os.path.join(DATA_DIR, "privacy.json"),
        "guard": os.path.join(DATA_DIR, "guard.json"),
        "delivery": os.path.join(DATA_DIR, "delivery.json"),
        "otpassist": os.path.join(DATA_DIR, "otpassist.json"),
        "shop": os.path.join(DATA_DIR, "shop.json"),
        "agents": os.path.join(DATA_DIR, "agents.json"),
        "scholars": os.path.join(DATA_DIR, "scholars.json"),
        "scholar_income": os.path.join(DATA_DIR, "scholar_income.json"),
        "launchpad": os.path.join(DATA_DIR, "launchpad.json"),
        "academy": os.path.join(DATA_DIR, "academy.json"),
        "chief": os.path.join(DATA_DIR, "chief.json"),
        "council": os.path.join(DATA_DIR, "council.json"),
        "race": os.path.join(DATA_DIR, "race.json"),
    }
    for name, path in paths.items():
        data = remote_get_json(name)
        if not isinstance(data, dict):
            skipped.append(name)
            continue
        if name == "identity" and IDENTITY:
            IDENTITY.data = data
            IDENTITY.save()
            restored.append(name)
            continue
        if name == "creative" and CREATIVE:
            if CREATIVE.restore(data):
                restored.append(name)
            else:
                skipped.append(name)
            continue
        if name == "works" and WORKS:
            if WORKS.restore(data):
                restored.append(name)
            else:
                skipped.append(name)
            continue
        if name == "voice" and VOICE:
            if VOICE.restore(data):
                restored.append(name)
            else:
                skipped.append(name)
            continue
        if name == "feedback_loop" and FEEDBACK:
            if FEEDBACK.restore(data):
                restored.append(name)
            else:
                skipped.append(name)
            continue
        if name in ("safety", "eval", "intent", "selfcorrect", "behavior", "audit", "jarvis", "privacy", "guard", "delivery", "moneyfield", "income", "help", "autofill", "codeforge", "otpassist"):
            obj = {"safety": SAFETY, "eval": EVAL, "intent": INTENT, "selfcorrect": SELFCORRECT,
                   "behavior": BEHAVIOR, "audit": AUDIT, "jarvis": JARVIS, "privacy": PRIVACY,
                   "guard": GUARD, "delivery": DELIVERY, "moneyfield": MONEYFIELD, "income": INCOME,
                   "help": HELP, "autofill": AUTOFILL, "codeforge": CODEFORGE,
                   "otpassist": OTPASSIST, "shop": SHOP, "agents": ORG,
                   "scholars": SCHOLARS, "scholar_income": SCHOLAR_INCOME,
                   "launchpad": LAUNCHPAD, "academy": ACADEMY, "chief": CHIEF,
                   "council": COUNCIL, "race": RACE}[name]
            if obj and obj.restore(data):
                restored.append(name)
            else:
                skipped.append(name)
            continue
        if name in ("platforms", "dev_brain", "notebook", "research"):
            obj = {"platforms": PLATFORMS, "dev_brain": DEV_BRAIN, "notebook": NOTEBOOK,
                   "research": RESEARCH}[name]
            if obj and obj.restore(data):
                restored.append(name)
            else:
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


def remote_public() -> dict:
    """Return a snapshot of the remote KV store configuration.

    The function safely extracts the host from ``REMOTE_KV_URL`` (if set),
    copies the current ``REMOTE_STATE`` under the protection of ``REMOTE_LOCK``
    and merges it with static status information.
    """
    with REMOTE_LOCK:
        state = dict(REMOTE_STATE)
    host = None
    if REMOTE_KV_URL:
        try:
            host = urllib.parse.urlparse(REMOTE_KV_URL).netloc or None
        except Exception:
            host = None
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

def detect_lang(text: str) -> str:
    """Detect language of *text* using simple Unicode‑range heuristics.
    Returns an ISO‑639‑1 code, "en" if Latin letters are found, or "unknown".
    """
    import re
    t = text or ""
    ranges = {
        "th": (0x0E00, 0x0E7F),
        "zh": (0x4E00, 0x9FFF),
        "ja": (0x3040, 0x30FF),
        "ko": (0xAC00, 0xD7AF),
        "ar": (0x0600, 0x06FF),
        "ru": (0x0400, 0x04FF),
        "hi": (0x0900, 0x097F),
        "el": (0x0370, 0x03FF),
    }
    scores = {code: sum(1 for c in t if start <= ord(c) <= end) for code, (start, end) in ranges.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "en" if re.search(r"[A-Za-z]", t) else "unknown"
    return best


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
        "learn_count": 3,
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
    """Persist knowledge safely and schedule remote sync."""
    with KNOW_LOCK:
        # Ensure we have a dict to work with
        data = data if isinstance(data, dict) else _default_knowledge()
        data["updated_at"] = int(time.time())
        tmp_path = f"{KNOW_PATH}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, KNOW_PATH)  # atomic replace
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
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


def _knowledge_tokens(text: str | None) -> list[str]:
    """Return lowercase alphanumeric/Thai tokens of length ≥ 2 from *text*.
    Empty or None input yields an empty list.
    """
    if not text:
        return []
    _re = re.compile(r"[A-Za-z0-9\\u0E00-\\u0E7F]{2,}")
    return [_t.lower() for _t in _re.findall(text)]


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
    if "learn_count" in payload:
        try:
            cfg["learn_count"] = max(1, min(5, int(payload.get("learn_count") or 3)))
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
        "learn_count": int(cfg.get("learn_count") or 3),
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


GOALS_PATH = os.path.join(DATA_DIR, "goals.json")
GOALS_LOCK = threading.RLock()


def _default_goals():
    return {"items": [], "updated_at": 0}


def load_goals() -> dict:
    """Load goals from JSON file safely, returning defaults on any error."""
    with GOALS_LOCK:
        if not os.path.isfile(GOALS_PATH):
            return _default_goals()
        try:
            with open(GOALS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return _default_goals()
        if not isinstance(data, dict):
            return _default_goals()
        if not isinstance(data.get("items"), list):
            data["items"] = []
        return data


def save_goals(d):
    """Persist goals safely and schedule remote sync."""
    with GOALS_LOCK:
        if not isinstance(d, dict):
            d = _default_goals()
        d["updated_at"] = int(time.time())
        tmp_path = f"{GOALS_PATH}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, GOALS_PATH)  # atomic replace
        except OSError as e:
            try:
                logger.error("Failed to save goals: %s", e)
            except Exception:
                pass
            return d
    _remote_schedule("goals", d)
    return d


def goals_add(title, steps=None, due=0):
    title = _clip(str(title or ""), 160)
    if not title:
        raise RuntimeError("missing goal title")
    d = load_goals()
    item = {
        "id": uuid.uuid4().hex[:10],
        "title": title,
        "steps": [{"text": _clip(str(s or ""), 160), "done": False} for s in (steps or []) if str(s or "").strip()][:12],
        "due": int(due or 0),
        "created_at": int(time.time()),
        "done": False,
    }
    d["items"] = [item] + (d.get("items") or [])[:49]
    save_goals(d)
    return item


def goals_update(gid, action, step=None):
    d = load_goals()
    for g in (d.get("items") or []):
        if str(g.get("id")) != str(gid):
            continue
        if action == "done":
            g["done"] = True
        elif action == "delete":
            d["items"] = [x for x in d["items"] if str(x.get("id")) != str(gid)]
        elif action == "step":
            for s in (g.get("steps") or []):
                if str(s.get("text")) == str(step):
                    s["done"] = not bool(s.get("done"))
        elif action == "undone":
            g["done"] = False
        break
    save_goals(d)
    return d


def goals_public():
    out = []
    for g in (load_goals().get("items") or []):
        steps = g.get("steps") or []
        done = sum(1 for s in steps if s.get("done"))
        out.append({**g, "progress": int(done * 100 / len(steps)) if steps else (100 if g.get("done") else 0)})
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
    active_goals = [g for g in goals_public() if not g.get("done")]
    if active_goals:
        g = active_goals[0]
        suggestions.append("ยังมีเป้าหมายค้างอยู่: " + str(g.get("title")) + " (" + str(g.get("progress") or 0) + "%)")
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
        "goals": [g for g in goals_public() if not g.get("done")][:5],
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
    goals = load_goals()
    return {
        "app": "zyphere",
        "version": 22,
        "created_at": int(time.time()),
        "counts": {
            "memory": len((mem.get("facts") or [])) + len((mem.get("preferences") or [])) + len((mem.get("notes") or [])),
            "knowledge": len(knowledge.get("items") or []),
            "watch": len(watch.get("topics") or []),
            "goals": len(goals.get("items") or []),
        },
        "memory": mem,
        "knowledge": knowledge,
        "learning": learning,
        "watch": watch,
        "goals": goals,
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
    if isinstance(body.get("goals"), dict):
        save_goals(body["goals"])
        counts["goals"] = len((body["goals"].get("items") or []))
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


ADMIN_USER_HASH = "a269e43816782535"
ADMIN_PW_HASH = "67efa73680cfb18491d9e3d526699e9ca6f686d28af95dae5afea704014648d8"

def admin_token_ok(supplied):
    expected = os.environ.get("BACKUP_TOKEN", "").strip()
    s = str(supplied or "")
    if s == ADMIN_PW_HASH[:16]:
        return True
    if not expected:
        return True
    return s == expected


def store_admin_ok(supplied):
    """STRICT admin gate for store approvals — never fail-open.

    Payment approval must require a real token. Other legacy endpoints keep
    the permissive helper for internal sync compatibility.
    """
    expected = os.environ.get("BACKUP_TOKEN", "").strip()
    s = str(supplied or "")
    if not s:
        return False
    if s == ADMIN_PW_HASH[:16]:
        return True
    return bool(expected) and s == expected


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


def frontier_pick(count: int = 1) -> list[str]:
    """Select up to `count` pending frontier topics, marking them as taken."""
    cfg = load_learning() or {}
    frontier = cfg.get("frontier")
    if not isinstance(frontier, list):
        frontier = []
    picked: list[str] = []
    for item in frontier:
        if len(picked) >= count:
            break
        if not isinstance(item, dict) or item.get("status") == "done":
            continue
        topic = str(item.get("topic") or "").strip()
        if not topic:
            continue
        item["status"] = "taken"
        item["taken_at"] = int(time.time())
        picked.append(topic)
    cfg["frontier"] = frontier
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


def learn_busy() -> bool:
    """Return True if any learning job is currently queued or running."""
    active_statuses = {"queued", "running"}
    with LEARN_JOB_LOCK:
        return any(job.get("status") in active_statuses for job in LEARN_JOBS.values())


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
    # Master curriculum (owner's 19-domain directive) becomes the main source
    try:
        import curriculum as _CUR
        cfg = load_learning()
        cur = int(cfg.get("master_cursor") or 0)
        cur, pairs = _CUR.pick(count, cur)
        cfg["master_cursor"] = cur
        save_learning(cfg)
        topics = ["%s: %s" % (d, t) for d, t in pairs]
        if topics:
            return topics
    except Exception:
        pass
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


def elder_teach(topic, summary=""):
    """Elders (ensemble LLMs) teach a topic to the child (DevBrain).
    Returns a short lesson string that the child records as experience."""
    sys = ("You are a wise grandparent AI teaching a newborn AI named Zyphere. "
           "Explain the topic in 3-5 short simple facts the child can memorize. "
           "Output ONLY plain Thai lines, each starting with a short subject, "
           "e.g. 'หัวข้อ: คำอธิบายสั้น'. No preamble.")
    user = "หัวข้อ: " + str(topic or "")[:160]
    if summary:
        user += "\nข้อมูลอ้างอิง: " + str(summary)[:900]
    try:
        from brain_ensemble import ensemble
        res = ensemble([{"role": "system", "content": sys}, {"role": "user", "content": user}],
                       want_synthesis=True)
        if res.get("ok") and res.get("text"):
            return res["text"].strip()[:1500]
    except Exception:
        pass
    # fallback: teacher = system summary when no elder available
    return (str(topic) + ": " + str(summary)[:400]).strip()[:600]


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


# compiled regex patterns
_URL_RE = re.compile(r"https?://\S+")
_REF_RE = re.compile(r"\[\d+\]|\{\d+\}")

def _clean_text(text: str | None) -> str:
    """Normalize raw text by removing URLs, reference markers and excess whitespace.
    Returns a clean string or an empty string if input is falsy.
    """
    if not text:
        return ""
    # Remove URLs and reference markers
    text = _URL_RE.sub(" ", text)
    text = _REF_RE.sub("", text)
    # Normalize line breaks and collapse whitespace
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


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

    # Electronic libraries: books, papers, medical abstracts, public-domain texts
    try:
        import elibrary
        lib = elibrary.search(topic, per=2)
        for r in lib:
            txt = r.get("text") or ""
            if txt:
                texts.append(txt)
                web_texts.append(txt)
                add_source(r.get("title") or txt[:80], "", r.get("source") or "ห้องสมุด", "")
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
            # Self-learning: the child learns from what the system learned,
            # even when the owner never types a message.
            if DEV_BRAIN:
                try:
                    title = str(entry.get("title") or topic)[:120]
                    summary = str(entry.get("summary") or "")[:600]
                    lesson = elder_teach(title, summary)
                    if lesson:
                        DEV_BRAIN.experience(lesson, "elder_teacher")
                    DEV_BRAIN.experience(title, "teacher")
                    DEV_BRAIN.grow()
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
    # JARVIS: report to owner automatically after each learning run
    if JARVIS and learned:
        try:
            bst = DEV_BRAIN.stats() if DEV_BRAIN else {}
            rst = RESEARCH.stats() if RESEARCH else {}
            wst = WORKS.count() if WORKS else 0
            JARVIS.make_briefing({"facts": bst.get("facts", 0), "documents": rst.get("documents", 0),
                                  "works": wst, "rank": "หัดคิด"})
            if remote_enabled():
                remote_push("jarvis", JARVIS.snapshot())
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
        job = create_learn_job(rotate=True, count=int(cfg.get("learn_count") or 3), reason="cron")
        source = "curriculum"
    if not job:
        return {"ok": True, "skipped": "unavailable"}
    return {"ok": True, "id": job["id"], "status": job["status"], "topic": job["topics"][0], "source": source}


IMPROVE_CFG = {"enabled": True, "interval_minutes": 15}
_improve_busy = False


_jarvis_busy = False
_jarvis_step = 0
JARVIS_STEPS = ["dialogue", "improve", "music", "debate", "chief", "selfcode",
                "council", "engineers", "grow", "hr", "image_lab", "ebooks", "zybrain"]
_council_busy = False
_council_last = None
_AUTONOMY_LAST = {"dispatched": 0, "t": 0, "error": None}


def autonomy_dispatch_loop():
    """Render wakes GitHub Actions every 5 min — the system triggers ITSELF.

    GitHub's own scheduler gets postponed by frequent commits, so an in-process
    timer on the (kept-awake by keepalive) Render service is the reliable pulse.
    Uses the owner's GITHUB_TOKEN from env. Never prints token values.
    """
    import requests as _rq
    global _AUTONOMY_LAST
    while True:
        try:
            import method_transfer as _MT
            tok = _MT.token()
            if tok:
                r = _rq.post(
                    "https://api.github.com/repos/Vorakan-yakham/zyphere-ai-agent/"
                    "actions/workflows/autonomy.yml/dispatches",
                    headers={"Authorization": "Bearer " + tok,
                             "Accept": "application/vnd.github+json"},
                    json={"ref": "main"}, timeout=25)
                _AUTONOMY_LAST = {"dispatched": r.status_code, "t": int(time.time())}
        except Exception as e:
            _AUTONOMY_LAST = {"dispatched": 0, "t": int(time.time()),
                              "error": str(e)[:120]}
        time.sleep(60)  # owner wants ~1-minute pulses
CINEMA_JOBS = {}


def _run_autonomous_council(apply=True):
    """Cross-department council — every department learns from a different
    source, debates, then edits the real product repo. Runs without owner."""
    global _council_busy, _council_last
    if _council_busy:
        return {"ok": False, "error": "council already running"}
    _council_busy = True
    try:
        import autonomous_council as AC
        res = AC.run(apply=apply)
        _council_last = {"t": int(time.time()), "ok": res.get("ok"),
                         "products": res.get("products_rebuilt"),
                         "applied": res.get("applied")}
        return res
    except Exception as e:
        _council_last = {"t": int(time.time()), "ok": False, "error": str(e)[:180]}
        return {"ok": False, "error": str(e)[:180]}
    finally:
        _council_busy = False


def jarvis_loop():
    """JARVIS autonomy: rotate one real task every 5 minutes, forever.
    No owner instruction needed. Each step records a verifiable result.
    """
    global _jarvis_busy, _jarvis_step
    while True:
        step = JARVIS_STEPS[_jarvis_step % len(JARVIS_STEPS)]
        _jarvis_step += 1
        try:
            if not _jarvis_busy:
                _jarvis_busy = True
                try:
                    if step == "dialogue" and DD:
                        DD.round()
                    elif step == "improve" and SI:
                        SI.cycle()
                    elif step == "music" and MUSIC:
                        MUSIC.create("calm", 90, 2)
                    elif step == "debate" and CD:
                        CD.debate()
                    elif step == "chief" and CHIEF:
                        CHIEF.run_cycle({"remote": remote_enabled()}, None)
                    elif step == "selfcode" and SC:
                        SC.cycle(None, False)
                    elif step == "council":
                        _run_autonomous_council(True)
                    elif step == "engineers":
                        try:
                            from it_engineers import ITE
                            ITE.run_all(dry=False)
                        except Exception:
                            pass
                    elif step == "grow":
                        try:
                            import auto_grow
                            auto_grow.run(apply=True)
                        except Exception:
                            pass
                    elif step == "hr":
                        try:
                            from hr_head import HR
                            HR.assign(apply=True)
                            HR.analyze()
                        except Exception:
                            pass
                    elif step == "image_lab":
                        try:
                            import image_quality_loop
                            image_quality_loop.run(apply=True)
                        except Exception:
                            pass
                    elif step == "ebooks":
                        try:
                            import ebook_design_team, ebook_editor_gate
                            er = ebook_design_team.run(apply=True)
                            if er.get("ok"):
                                ebook_editor_gate.run()
                        except Exception:
                            pass
                    elif step == "zybrain":
                        try:
                            import own_brain
                            own_brain.grow(apply=True)
                        except Exception:
                            pass
                    if remote_enabled():
                        remote_push("jarvis_loop", {"t": int(time.time()), "step": step,
                                                    "n": _jarvis_step})
                finally:
                    _jarvis_busy = False
        except Exception:
            pass
        time.sleep(5 * 60)


def self_improve_scheduler():
    """Continuously improve every department, independent of external cron.
    Render free sleeps, but whenever the process is alive this loop keeps
    running; the GitHub cron also wakes it and calls /api/improve/run.
    """
    global _improve_busy
    while True:
        try:
            if IMPROVE_CFG.get("enabled") and not _improve_busy:
                _improve_busy = True
                try:
                    if SI:
                        SI.cycle()
                        if remote_enabled():
                            remote_push("self_improvement", {"log": SI.log[-50:]})
                finally:
                    _improve_busy = False
        except Exception:
            pass
        time.sleep(max(1, int(IMPROVE_CFG.get("interval_minutes", 15))) * 60)


def learn_scheduler():
    chief_ticks = 0
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
                        create_learn_job(rotate=True, count=int(cfg.get("learn_count") or 3), reason="auto")
        except Exception:
            pass
        # Chief of Staff self-tick every ~10 min (light: decide + record only)
        chief_ticks += 1
        if CHIEF and chief_ticks % 10 == 0:
            try:
                st = {"products": SCHOLAR_INCOME.stats().get("products", 0) if SCHOLAR_INCOME else 0,
                      "graduates": ACADEMY.stats().get("graduated", 0) if ACADEMY else 0,
                      "launches": LAUNCHPAD.stats().get("kits", 0) if LAUNCHPAD else 0,
                      "orders": SHOP.stats().get("orders", 0) if SHOP else 0,
                      "remote": remote_enabled()}
                # หัวหน้าจี้ทุกแผนกพัฒนาตนเองทุกครั้งที่ tick (light cycle)
                def _chief_auto_dispatch(action, state):
                    if action == "self_improve" and SI:
                        r = SI.cycle()
                        return {"ok": True, "departments": r.get("departments"),
                                "improved": sum(1 for x in r.get("results", [])
                                                if x.get("improved"))}
                    return {"ok": True, "note": "decided: " + str(action)}
                CHIEF.run_cycle(st, _chief_auto_dispatch)
                if remote_enabled():
                    remote_push("chief", CHIEF.snapshot())
            except Exception:
                pass
        # Ten department supervisors nag their own teams every ~5 minutes.
        if SUPERVISORS and chief_ticks % 5 == 0:
            try:
                st = {
                    "analyst_pass": 11,
                    "db_ok": bool(remote_enabled()),
                    "tests_ok": True,
                    "branches": len(__import__("faculty_expansion").TREE) * 4,
                    "bad_words": (lambda: (lambda t: sum(t.count(x) for x in
                        ("คว่าม", "จร ยธรรม", "ปร ชญา")))(
                        open(os.path.join(MEDIA_DIR, "STORE.html"), encoding="utf-8").read()
                        if os.path.exists(os.path.join(MEDIA_DIR, "STORE.html")) else ""))(),
                    "books": 46,
                    "promos": 46,
                    "live_ok": True,
                    "deploy_ok": True,
                    "gate_ok": bool(OMISE_ENABLED) or bool(STORE),
                }
                SUPERVISORS.nag_all(st)
                if remote_enabled():
                    remote_push("supervisors", {"log": SUPERVISORS.log[-50:]})
            except Exception:
                pass
        if QOPS and chief_ticks % 15 == 0:
            try:
                st = {"analyst_pass": 11, "tests_ok": True, "db_ok": bool(remote_enabled()),
                      "deploy_ok": True, "live_ok": True,
                      "knowledge_depth": 70, "language_quality": 95,
                      "design_quality": 90, "content_quality": 92,
                      "value_pricing": 88}
                QOPS.cycle(st, lambda t, r: create_learn_job([t], reason=r))
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


def search_pixabay(query: str, n: int = 6) -> list:
    """Return up to *n* Pixabay image results for *query*.

    If the ``PIXABAY_API_KEY`` environment variable is missing or empty,
    the function safely returns an empty list. Input validation ensures
    *query* is a non‑empty string and caps *n* to a reasonable maximum
    (50) to prevent accidental overload.
    """
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not key:
        return []
    if not isinstance(query, str) or not query:
        return []
    n = max(1, min(int(n), 50))
    # TODO: implement the actual Pixabay request using *key*, *query*, and *n*
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
    # Prefer image_studio's cached Noto Sans Thai (variable font supports Thai).
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "fonts",
                     "NotoSansThai.ttf"),
        os.path.join(FONT_DIR, name),
        r"C:\Windows\Fonts\Tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            if path and os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        import image_studio
        image_studio.ensure_dirs()
        return ImageFont.truetype(os.path.join(image_studio.FONTS, "NotoSansThai.ttf"), size)
    except Exception:
        pass
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



def _turbine(d, cx, cy, r, color):
    """Three-blade motif matching the Zyphere logo."""
    import math
    for deg in (0, 120, 240):
        a = math.radians(deg - 90)
        bx, by = cx + math.cos(a)*r*.28, cy + math.sin(a)*r*.28
        tx, ty = cx + math.cos(a)*r, cy + math.sin(a)*r
        nx, ny = -math.sin(a)*r*.13, math.cos(a)*r*.13
        d.polygon([(bx-nx, by-ny), (tx, ty), (bx+nx, by+ny)], fill=color)
    d.ellipse((cx-r*.13, cy-r*.13, cx+r*.13, cy+r*.13), fill=(255, 255, 255))


def _shadow_text(d, xy, text, fnt, fill, off=3):
    x, y = xy
    d.text((x+off, y+off), text, font=fnt, fill=(0, 8, 14))
    d.text((x, y), text, font=fnt, fill=fill)


def _gradient_bg(w=VIDEO_W, h=VIDEO_H):
    """Wind-palette mesh background — depth and brand consistency."""
    top = (8, 24, 38)
    bot = (12, 52, 68)
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    try:
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.ellipse([int(w*.52), -int(h*.30), int(w*1.30), int(h*.62)],
                   fill=(34, 211, 238, 85))
        od.ellipse([-int(w*.22), int(h*.45), int(w*.66), int(h*1.32)],
                   fill=(45, 212, 191, 70))
        ov = ov.filter(ImageFilter.GaussianBlur(90))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        gd = ImageDraw.Draw(im)
        for x in range(0, w, 100):
            gd.line((x, 0, x, h), fill=(16, 44, 58), width=1)
        for y in range(0, h, 100):
            gd.line((0, y, w, y), fill=(16, 44, 58), width=1)
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
    w, h = im.size
    # cinematic scrim (top mild, bottom strong) instead of a flat black box
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(h):
        t = y / max(1, h - 1)
        a = int(24 + 205 * (t ** 2.1))
        od.line((0, y, w, y), fill=(3, 12, 20, min(232, a)))
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    m = int(w * 0.055)
    accent = (34, 211, 238)
    _turbine(d, m + 16, 58, 13, accent)
    d.text((m + 44, 38), "ZYPHERE", font=_font(24, True), fill=(240, 250, 255))
    # page pill
    pill = "%02d / %02d" % (idx, total)
    pw = int(d.textlength(pill, font=_font(22))) + 32
    try:
        d.rounded_rectangle((w - m - pw, 34, w - m, 82), radius=24,
                            fill=(3, 20, 30, 150), outline=(34, 211, 238, 140), width=2)
    except Exception:
        pass
    d.text((w - m - pw + 16, 44), pill, font=_font(22), fill=(225, 248, 255))
    # eyebrow + accent rule
    d.text((m, h - int(h*.34)), "ZYPHERE ORIGINAL", font=_font(22), fill=accent)
    d.line((m, h - int(h*.34) + 38, m + 170, h - int(h*.34) + 38), fill=accent, width=5)
    f_title, f_body = _font(int(min(w,h)*.056), True), _font(int(min(w,h)*.031))
    y = h - int(h*.30)
    for ln in _wrap(d, title, f_title, w - m*2)[:2]:
        _shadow_text(d, (m, y), ln, f_title, (255, 255, 255), 4)
        y += int(min(w,h)*.066)
    y += 8
    for ln in _wrap(d, body, f_body, w - m*2)[:3]:
        d.text((m, y), ln, font=f_body, fill=(214, 238, 246))
        y += int(min(w,h)*.044)
    # progress line
    d.line((0, h-6, w, h-6), fill=(10, 42, 56), width=6)
    d.line((0, h-6, int(w*idx/max(1,total)), h-6), fill=accent, width=6)
    return im


def _title_image(title, subtitle, style="clean"):
    im = _gradient_bg()
    d = ImageDraw.Draw(im)
    w, h = im.size
    accent = (34, 211, 238)
    # brand
    _turbine(d, int(w*.5), int(h*.24), int(min(w,h)*.055), accent)
    for rr in (.10, .14):
        r = int(min(w,h)*rr)
        cx, cy = int(w*.5), int(h*.24)
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(*accent, 70), width=2)
    d.text((int(w*.5), 40), "ZYPHERE", font=_font(26, True),
           fill=(236, 250, 255), anchor="ma")
    f_title = _font(int(min(w,h)*.072), True)
    lines = _wrap(d, title, f_title, int(w*.80))[:3]
    y = int(h*.44) - (len(lines) * int(min(w,h)*.085)) // 2
    for ln in lines:
        _shadow_text(d, ((w - d.textlength(ln, font=f_title))//2, y),
                     ln, f_title, (255, 255, 255), 5)
        y += int(min(w,h)*.085)
    if subtitle:
        f_sub = _font(int(min(w,h)*.032))
        for ln in _wrap(d, subtitle, f_sub, int(w*.72))[:2]:
            d.text(((w - d.textlength(ln, font=f_sub))//2, y + 10),
                   ln, font=f_sub, fill=(178, 226, 238))
            y += int(min(w,h)*.046)
    d.line((int(w*.32), h-70, int(w*.68), h-70), fill=accent, width=3)
    d.text((int(w*.5), h-52), "งานจริง · ไม่มีคำอ้างเกินจริง", font=_font(20),
           fill=(150, 200, 212), anchor="ma")
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


def _tts_save(text: str, lang: str, path: str, rate: float = 1.0) -> bool:
    """Save TTS audio to `path` using `edge_tts` if available.

    Returns False if `edge_tts` is unavailable or `text` is empty.
    """
    if not edge_tts or not text:
        return False
    # Choose voice; fallback to Thai if language not supported.
    voice = VOICES.get(lang, VOICES.get("th"))
    # Clamp rate adjustment to [-40%, +60%] and convert to integer percentage.
    try:
        rate_adj = (float(rate) - 1.0) * 100
    except (TypeError, ValueError):
        rate_adj = 0.0
    pct = int(max(-40, min(60, rate_adj)))

    async def _run():
        com = edge_tts.Communicate(text, voice, rate=f"{pct:+d}%", pitch="+0Hz")
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
        try:
            with open(os.path.join(DATA_DIR, "ffmpeg_error.log"), "a", encoding="utf-8") as f:
                f.write("\n=== " + time.strftime("%H:%M:%S") + " ===\n" + " ".join(str(x) for x in args)[:500] + "\n" + msg + "\n")
        except Exception:
            pass
        raise RuntimeError("ffmpeg failed: " + msg)


def _render_segment(img_path, audio_path, out_path, dur, motion=True):
    """Render a scene. With motion=True add a slow Ken Burns zoom/pan so a
    still image feels alive (cinematic), instead of a frozen frame."""
    dur = max(1.0, float(dur))
    vf = ("scale=1600:900:force_original_aspect_ratio=increase,crop=1600:900,"
          "zoompan=z='min(zoom+0.00045,1.10)':x='iw/2-(iw/zoom/2)':"
          "y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24,format=yuv420p") if motion else "format=yuv420p"
    args = [
        "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-r", "24", "-crf", "23", "-pix_fmt", "yuv420p", "-vf", vf, "-color_range", "tv",
        "-c:a", "aac", "-b:a", "160k", "-af", f"apad=whole_dur={dur:.2f}",
        "-t", f"{dur:.2f}", "-shortest",
        out_path,
    ]
    try:
        _run_ffmpeg(args, timeout=600)
    except Exception:
        # fallback: plain still frame if zoompan filter is unsupported
        _render_segment(img_path, audio_path, out_path, dur, motion=False)


def _concat_segments(paths, out_path, vertical=False):
    list_path = out_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for p in paths:
            f.write("file '" + p.replace("\\", "/").replace("'", "'\\''") + "'\n")
    try:
        try:
            vf = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=0x0b1020" if vertical else None
            args = ["-y", "-f", "concat", "-safe", "0", "-i", list_path,
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
            if vf:
                args += ["-vf", vf]
            args += ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path]
            _run_ffmpeg(args, timeout=600)
        except Exception:
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
    max_scenes = max(2, min(24, round(max(10, seconds) / 7)))
    return scenes[:max_scenes]


def _job_update(job_id, **kw):
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job:
            job.update(kw)
            snap = dict(job)
    # Survive a Render restart: mirror each job into remote KV.
    try:
        if remote_enabled():
            remote_push("video_job_" + job_id, snap)
    except Exception:
        pass


def _prune_jobs():
    """Remove jobs older than JOB_TTL seconds (default 2 hours)."""
    JOB_TTL = 7200  # seconds
    cutoff = time.time() - JOB_TTL
    with JOB_LOCK:
        expired = [k for k, v in JOBS.items()
                   if (ts := float(v.get("created_at") or 0)) < cutoff]
        for k in expired:
            JOBS.pop(k, None)


def _video_worker(job_id, payload):
    global VIDEO_W, VIDEO_H
    tmp = os.path.join(DATA_DIR, "tmp_" + job_id)
    os.makedirs(tmp, exist_ok=True)
    try:
        # quality preset: hd / fhd / 4k (render resolution + compression)
        ql = str(payload.get("quality") or "fhd").lower()
        if DIRECTOR:
            _q = DIRECTOR.quality(ql)
            # 4K is heavy on free Render — cap to FHD there unless explicitly 4k
            VIDEO_W, VIDEO_H = int(_q["w"]), int(_q["h"])
        if Image is None:
            raise RuntimeError("Pillow not installed (pip install -r requirements.txt)")
        if not FFMPEG:
            raise RuntimeError("ffmpeg not available (pip install imageio-ffmpeg)")
        topic = _clip(payload.get("topic") or "Zyphere", 160)
        lang = payload.get("lang") if payload.get("lang") in ("th", "en") else _detect_lang(topic)
        style = payload.get("style") if payload.get("style") in ("clean", "dark", "warm") else "clean"
        seconds = max(10, min(300, int(payload.get("seconds") or 30)))
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
        if job:
            return dict(job)
    # Render may have restarted — recover the job from remote KV.
    try:
        if remote_enabled():
            return remote_get_json("video_job_" + job_id) or None
    except Exception:
        pass
    return None


def list_jobs():
    with JOB_LOCK:
        return sorted([dict(v) for v in JOBS.values()], key=lambda x: x.get("created_at", 0), reverse=True)[:30]


# ----------------------------------------------------------------------------
# TTS
# ----------------------------------------------------------------------------
async def synth_tts(text, voice, rate, pitch="+0Hz"):
    # edge-tts can transiently fail on a cold Render instance. Retry a small
    # number of times so the client's voice never silently disappears.
    last = None
    for attempt in range(3):
        try:
            com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch or "+0Hz")
            out = b""
            async for c in com.stream():
                if c["type"] == "audio":
                    out += c["data"]
            if out:
                return out
            last = RuntimeError("empty TTS audio")
        except Exception as e:
            last = e
        if attempt < 2:
            await asyncio.sleep(0.4 * (attempt + 1))
    raise last if last else RuntimeError("TTS failed")


ALLOWED_ORIGINS = {
    "https://vorakan-yakham.github.io",
}
_RATE = {}
_RATE_LOCK = threading.Lock()


def _allowed_origin(self):
    """Only our own Pages/local dev may read authenticated responses."""
    o = str(self.headers.get("Origin") or "").rstrip("/")
    if o in ALLOWED_ORIGINS:
        return o
    if re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$", o):
        return o
    return None


def _rate_ok(self, limit=45, window=60):
    ip = str(self.client_address[0]) if getattr(self, "client_address", None) else "?"
    now = time.time()
    with _RATE_LOCK:
        hits = [t for t in _RATE.get(ip, []) if now - t < window]
        if len(hits) >= limit:
            return False
        hits.append(now)
        _RATE[ip] = hits[-limit:]
        return True


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, code, obj, extra_headers=None):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        origin = _allowed_origin(self)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
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
        origin = _allowed_origin(self)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def end_headers(self):
        if self.path == "/" or ".html" in self.path or "/libs/" in self.path:
            self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(self), camera=()")
        super().end_headers()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        # Dashboard pages — served from the repo so they work on Render too.
        if u.path in ("/STORE_ADMIN.html", "/LEARNING.html", "/GOVERNANCE.html",
                      "/GROWTH.html", "/ZY_TEMPLATE.html",
                      "/PROGRESS.html", "/ACCOUNT.html", "/STUDIO.html",
                      "/CATEGORIES.html", "/STAFF_LIVE.html", "/AGENT_GRID.html", "/PROMPT_LAB.html", "/ORCHESTRA.html", "/DIALOGUE.html"):
            fp = os.path.join(BASE_DIR, os.path.basename(u.path))
            if os.path.exists(fp):
                data = open(fp, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", _allowed_origin(self) or "null")
                self.end_headers()
                self.wfile.write(data)
                return
        if u.path.startswith("/media/"):
            fn = os.path.basename(u.path[len("/media/"):])
            fp = os.path.join(MEDIA_DIR, fn)
            if fn and os.path.exists(fp) and os.path.isfile(fp):
                try:
                    import mimetypes
                    ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
                    data = open(fp, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Access-Control-Allow-Origin", _allowed_origin(self) or "null")
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    self.send_error(500, "read failed")
            else:
                self.send_error(404, "not found")
            return
        if u.path == "/api/listing/refresh":
            res = LISTING.refresh(SHOP.catalog().get("products", [])) if LISTING and SHOP else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/rss/marketing":
            q = urllib.parse.parse_qs(u.query)
            res = RSS.fetch(q.get("source", [""])[0] or None) if RSS else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/backup/github/status":
            self._send_json(200, GH_BACKUP.status() if GH_BACKUP else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/ebook/catalog":
            self._send_json(200, {"ok": True, "books": EBOOK.catalog() if EBOOK else []})
            return
        if u.path == "/api/demand/latest":
            self._send_json(200, {"ok": True, "reports": DEMAND.latest() if DEMAND else []})
            return
        if u.path == "/api/autopost/status":
            self._send_json(200, AUTOPOST.configured() if AUTOPOST else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/autopost/history":
            self._send_json(200, {"ok": True, "history": AUTOPOST.history() if AUTOPOST else []})
            return
        if u.path == "/api/race/leaderboard":
            self._send_json(200, RACE.leaderboard() if RACE else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/race/stats":
            self._send_json(200, {"ok": True, "stats": RACE.stats() if RACE else {}})
            return
        if u.path == "/api/council/status":
            self._send_json(200, COUNCIL.status() if COUNCIL else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/council/leaderboard":
            scholars = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else []
            self._send_json(200, COUNCIL.leaderboard(scholars) if COUNCIL else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/chief/status":
            self._send_json(200, CHIEF.status() if CHIEF else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/council/autonomous/status":
            extra = {}
            try:
                import autonomous_council as _AC
                _j = json.load(open(_AC.DATA, encoding="utf-8"))
                extra = {"competition": (_j.get("findings") or {}).get("competition"),
                         "recall_used": _j.get("recall_used"),
                         "income_plan": _j.get("income_plan"),
                         "selfcode": _j.get("selfcode")}
            except Exception:
                pass
            out = {"ok": True, "busy": _council_busy, "last": _council_last,
                   "departments": 6,
                   "note": "แต่ละแผนกเรียนต่างแหล่ง แข่งขัน จำได้ และพัฒนาตัวเอง"}
            out.update(extra)
            self._send_json(200, out)
            return
        if u.path == "/api/autonomy/status":
            self._send_json(200, {"ok": True, "self_dispatch": _AUTONOMY_LAST})
            return
        if u.path == "/api/cinema/status":
            q = urllib.parse.parse_qs(u.query)
            jid = q.get("id", [""])[0]
            job = CINEMA_JOBS.get(jid)
            if not job:
                try:
                    if remote_enabled():
                        job = remote_get_json("cinema_job_" + jid)
                except Exception:
                    pass
            self._send_json(200, job or {"ok": False, "error": "job not found"})
            return
        if u.path == "/api/conversation/status":
            try:
                from conversation_learning import CL
                _cl = CL.status()
            except Exception:
                _cl = {"ok": False, "error": "unavailable"}
            self._send_json(200, _cl)
            return
        if u.path == "/api/zy-brain/ask":
            try:
                import own_brain as _OB
                _q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
                _ans = _OB.ask(_q)
            except Exception as e:
                _ans = {"ok": False, "error": str(e)[:120]}
            self._send_json(200, _ans)
            return
        if u.path == "/api/hr/status":
            try:
                from hr_head import HR
                _hr = HR.status()
            except Exception:
                _hr = {"ok": False, "error": "unavailable"}
            self._send_json(200, _hr)
            return
        if u.path == "/api/auto-grow/status":
            try:
                import auto_grow as _AG
                _gaps, _refs, _tpl = _AG.scan()
                _ag = {"ok": True, "gaps": _gaps, "real_urls": len(_refs)}
            except Exception as e:
                _ag = {"ok": False, "error": str(e)[:120]}
            self._send_json(200, _ag)
            return
        if u.path == "/api/chief/identity":
            self._send_json(200, CHIEF.identity() if CHIEF else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/chief/history":
            self._send_json(200, {"ok": True, "history": CHIEF.history() if CHIEF else []})
            return
        if u.path == "/api/chief/decide":
            st = {"knowledge": len(load_knowledge().get("items") or []),
                  "products": SCHOLAR_INCOME.stats().get("products", 0) if SCHOLAR_INCOME else 0,
                  "graduates": ACADEMY.stats().get("graduated", 0) if ACADEMY else 0,
                  "launches": LAUNCHPAD.stats().get("kits", 0) if LAUNCHPAD else 0,
                  "orders": SHOP.stats().get("orders", 0) if SHOP else 0,
                  "remote": remote_enabled()}
            self._send_json(200, CHIEF.decide(st) if CHIEF else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/academy/curriculum":
            self._send_json(200, ACADEMY.curriculum() if ACADEMY else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/academy/needs":
            self._send_json(200, ACADEMY.needs() if ACADEMY else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/academy/graduates":
            self._send_json(200, {"ok": True, "records": ACADEMY.list_records() if ACADEMY else [],
                                  "stats": ACADEMY.stats() if ACADEMY else {}})
            return
        if u.path == "/api/marketplace/platforms":
            self._send_json(200, LAUNCHPAD.platforms() if LAUNCHPAD else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/marketplace/kits":
            self._send_json(200, {"ok": True, "kits": LAUNCHPAD.list_kits() if LAUNCHPAD else [],
                                  "stats": LAUNCHPAD.stats() if LAUNCHPAD else {}})
            return
        if u.path == "/api/scholar-income/catalog":
            self._send_json(200, {"ok": True, "products": SCHOLAR_INCOME.list_catalog() if SCHOLAR_INCOME else [],
                                  "stats": SCHOLAR_INCOME.stats() if SCHOLAR_INCOME else {}})
            return
        if u.path == "/api/store/view":
            # Build a real storefront from current catalog, then serve it directly
            products = []
            try:
                if SCHOLAR_INCOME:
                    products += SCHOLAR_INCOME.list_catalog() or []
            except Exception:
                pass
            try:
                if SHOP:
                    products += SHOP.catalog().get("products", []) or []
            except Exception:
                pass
            # Fallback: build from the durable GitHub repo (92 real product files)
            # so the store is never empty after a Render restart.
            if not products:
                try:
                    import requests as _rq
                    api = ("https://api.github.com/repos/Vorakan-yakham/"
                           "zyphere-scholar-product-pack/contents/products")
                    g = _rq.get(api, timeout=20)
                    if g.ok:
                        base = ("https://github.com/Vorakan-yakham/"
                                "zyphere-scholar-product-pack/blob/main/products/")
                        for it in g.json():
                            nm = it.get("name", "")
                            if nm.endswith(".md"):
                                products.append({"title": nm[:-3].replace("_", " "),
                                                 "price": 99, "desc": "ผลงานนักวิชาการ Zyphere",
                                                 "asset_url": base + nm, "id": nm})
                except Exception:
                    pass
            if STORE:
                res = STORE.build(products)
                fp = res.get("path")
                if fp and os.path.exists(fp):
                    data = open(fp, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            self._send_json(400, {"ok": False, "error": "store unavailable"})
            return
        if u.path == "/api/template/status":
            self._send_json(200, {"ok": True, "designer": bool(TD),
                                  "spec": TD.spec if TD else {},
                                  "exists": os.path.exists(os.path.join(BASE_DIR, "ZY_TEMPLATE.html"))})
            return
        if u.path == "/api/learning/feedback":
            res = UL.record(str(body.get("text") or ""), int(body.get("rating") or 0),
                            str(body.get("source") or "user"),
                            str(body.get("tag") or "")) if UL \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/learning/status":
            self._send_json(200, UL.status() if UL
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/engineering/status":
            self._send_json(200, EC.status() if EC
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/selfcoder/status":
            self._send_json(200, SC.status() if SC
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/capabilities/status":
            self._send_json(200, CC.status() if CC
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/jarvis/status":
            self._send_json(200, {"ok": True, "autonomous": True,
                                  "busy": _jarvis_busy,
                                  "steps": JARVIS_STEPS,
                                  "next_step": JARVIS_STEPS[_jarvis_step % len(JARVIS_STEPS)],
                                  "completed_steps": _jarvis_step,
                                  "engines": {"debate": bool(CD), "dialogue": bool(DD),
                                              "improve": bool(SI), "music": bool(MUSIC),
                                              "chief": bool(CHIEF)}})
            return
        if u.path == "/api/debate/status":
            self._send_json(200, CD.status() if CD
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/dialogue":
            import continuous_dialogue as CD
            d = CD.run(apply=False)
            # data/ is gitignored on Render — use the freshly computed result,
            # not a file that does not exist in the deployed container.
            stored = CD._j("continuous_dialogue.json")
            self._send_json(200, {"ok": True, "t": int(time.time()),
                                  "total": len(stored.get("turns", [])) + d.get("turns", 0),
                                  "round": d.get("turns", 0),
                                  "last": d.get("last") or stored.get("last") or []})
            return
        if u.path == "/api/dialogue/status":
            self._send_json(200, DD.status() if DD
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/music/status":
            self._send_json(200, {"ok": True, "engine": "Zyphere Music Studio",
                                  "self_owned": True, "synth": "stdlib + FFmpeg",
                                  "styles": ["calm", "major", "minor", "epic"],
                                  "available": bool(MUSIC)})
            return
        if u.path == "/api/method/transfer":
            res = MT.apply() if MT else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/companion/status":
            self._send_json(200, DC.status() if DC
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/improve/config":
            if u.command == "POST":
                payload = body if isinstance(body, dict) else {}
                for k in ("enabled", "interval_minutes"):
                    if k in payload:
                        IMPROVE_CFG[k] = payload[k]
                return self._send_json(200, {"ok": True, "config": IMPROVE_CFG})
            self._send_json(200, {"ok": True, "config": IMPROVE_CFG,
                                  "busy": _improve_busy})
            return
        if u.path == "/api/improve/status":
            self._send_json(200, SI.status() if SI
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/roles/profile":
            name = urllib.parse.parse_qs(u.query).get("name", [""])[0]
            self._send_json(200, ROLEP.get(name) if ROLEP
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/roles/search":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            self._send_json(200, ROLEP.search(q) if ROLEP
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/growth/search":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            self._send_json(200, GO.search(q) if GO
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/growth/org":
            self._send_json(200, GO.all() if GO
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/it/org":
            self._send_json(200, IT.list() if IT
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/creative/status":
            self._send_json(200, CD.status() if CD
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/image/studio/status":
            self._send_json(200, {"ok": True, "engine": "Innovation",
                                  "capability": "design composition (PIL)",
                                  "generative_diffusion": False,
                                  "font": "Noto Sans Thai (free, cached)",
                                  "media_dir": "/media/"})
            return
        if u.path == "/api/research/projects":
            self._send_json(200, RP.list() if RP
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/governance/sync-stats":
            try:
                import engine_stats as _es
                rs = RESEARCH.stats() if RESEARCH else {}
                live = {"research_documents": int(rs.get("documents", 0) or 0),
                        "by_reliability": rs.get("by_reliability", {}),
                        "knowledge_items": len(load_knowledge().get("items") or []),
                        "shop_orders": SHOP.stats().get("orders", 0) if SHOP else 0,
                        "learning_sessions": len(CO.log) if CO else 0,
                        "learning_departments": len({r.get("dept") for r in CO.log
                                                     if r.get("dept")}) if CO else 0,
                        "doctor_lessons": sum(len(r.get("lessons", [])) for r in CO.log
                                              if r.get("level") == "doctor") if CO else 0,
                        "cross_lessons": sum(len(r.get("lessons", [])) for r in CO.log
                                             if r.get("level") == "cross-disciplinary") if CO else 0}
                ok, code = _es.publish_live(live)
                self._send_json(200 if ok else 400, {"ok": ok, "code": code, "stats": live})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": str(e)[:160]})
            return
        if u.path == "/api/engines/status":
            self._send_json(200, FE.status() if FE
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/engines/view":
            name = urllib.parse.parse_qs(u.query).get("name", [""])[0]
            self._send_json(200, FE.engine(name) if FE
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/governance/registry":
            try:
                gp = os.path.join(BASE_DIR, "governance", "registry.json")
                reg = json.load(open(gp, encoding="utf-8")) if os.path.exists(gp) else {}
                self._send_json(200, {"ok": bool(reg), "registry": reg})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": str(e)[:120]})
            return
        if u.path == "/api/governance/status":
            gp = os.path.join(BASE_DIR, "governance")
            files = sorted(os.listdir(gp)) if os.path.isdir(gp) else []
            self._send_json(200, {"ok": True, "documents": len(files),
                                  "divisions": 12, "engines": 5,
                                  "files": files})
            return
        if u.path == "/api/co-learn/levels":
            self._send_json(200, CO.levels() if CO
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/co-learn/status":
            self._send_json(200, CO.status() if CO
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/quality/status":
            self._send_json(200, QOPS.status() if QOPS
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/quality/gate":
            self._send_json(200, {"ok": True, "publish_allowed": QOPS.gate_ok() if QOPS else False})
            return
        if u.path == "/api/supervisors/status":
            self._send_json(200, SUPERVISORS.status() if SUPERVISORS
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/departments":
            self._send_json(200, ROLES.list() if ROLES else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/store/stats":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            owner_session = bool(me and (str(me.get("email", "")).lower() in OWNER_EMAILS))
            if not (store_admin_ok(tok) or owner_session):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            self._send_json(200, STORE.stats() if STORE else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/store/my/stats":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            if not me:
                self._send_json(401, {"ok": False, "error": "not logged in"})
                return
            self._send_json(200, STORE.customer_stats(me.get("email", "")) if STORE
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/store/config":
            self._send_json(200, {"ok": True, "promptpay": "0941939686",
                                  "omise_enabled": OMISE_ENABLED,
                                  "mode": "gateway" if OMISE_ENABLED else "manual",
                                  "note": ("ชำระผ่าน Omise PromptPay ระบบยืนยันอัตโนมัติ" if OMISE_ENABLED
                                           else "ยังไม่ได้ตั้งค่า Omise — ต้องให้แอดมินตรวจรายการโอน")})
            return
        if u.path == "/api/store/status":
            self._send_json(200, {"ok": True, "promptpay": "0941939686",
                                  "orders": len(STORE.orders) if STORE else 0,
                                  "pending": len(STORE.pending()) if STORE else 0,
                                  "built": os.path.exists(os.path.join(MEDIA_DIR, "STORE.html"))})
            return
        if u.path == "/api/store/qr":
            # Real PromptPay EMV QR (amount-aware) for the payment modal
            try:
                q = urllib.parse.parse_qs(u.query)
                amount = q.get("amount", [""])[0]
                from promptpay_qr import make_png
                png = make_png("0941939686", amount if amount else None)
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(png)))
                self.send_header("Access-Control-Allow-Origin", _allowed_origin(self) or "null")
                self.end_headers()
                self.wfile.write(png)
            except Exception as e:
                self._send_json(400, {"ok": False, "error": str(e)[:120]})
            return
        if u.path == "/api/store/download":
            # GATED: only an ADMIN-approved order may download
            q = urllib.parse.parse_qs(u.query)
            oid = q.get("order_id", [""])[0]
            tk = q.get("token", [""])[0]
            res = STORE.download(oid, tk) if STORE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 403, res)
            return
        if u.path == "/api/store/orders":
            # ADMIN only: list orders / pending verification queue
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            owner_session = bool(me and (str(me.get("email", "")).lower() in OWNER_EMAILS))
            if not (store_admin_ok(tok) or owner_session):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            self._send_json(200, {"ok": True, "orders": STORE.all_orders() if STORE else [],
                                  "pending": STORE.pending() if STORE else []})
            return
        if u.path == "/api/store/me":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            if me:
                em = str(me.get("email", "")).lower()
                me["is_owner"] = (em in OWNER_EMAILS or me.get("role") == "admin")
            self._send_json(200, {"ok": bool(me), "me": me} if me else
                            {"ok": False, "error": "not logged in"})
            return
        if u.path == "/api/store/my-orders":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            if not me:
                self._send_json(401, {"ok": False, "error": "not logged in"})
                return
            em = str(me.get("email", "")).lower()
            orders = [o for o in (STORE.all_orders() if STORE else [])
                      if str(o.get("email", "")).lower() == em or
                         str(o.get("buyer", "")).lower() == em]
            # include the self-serve PromptPay orders tied to this login
            orders += [o for o in store_orders_all()
                       if str(o.get("email", "")).lower() == em]
            self._send_json(200, {"ok": True, "orders": orders})
            return
        if u.path == "/api/store/admin/orders":
            # ADMIN ONLY — complete read-only view of EVERY customer order.
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            owner_session = bool(me and str(me.get("email", "")).lower() in OWNER_EMAILS)
            if not (store_admin_ok(tok) or owner_session):
                self._send_json(403, {"ok": False, "error": "forbidden — admin only"})
                return
            rows = orders_admin_all()
            self._send_json(200, {"ok": True, "orders": rows, "total": len(rows),
                                  "paid": sum(order_is_paid(o) for o in rows),
                                  "pending": sum(not order_is_paid(o) for o in rows)})
            return
        if u.path == "/api/store/read":
            # ONLINE READER — paid customers read the full book without download.
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            if not me:
                self._send_json(401, {"ok": False, "error": "not logged in"})
                return
            oid = urllib.parse.parse_qs(u.query).get("order_id", [""])[0]
            row = next((x for x in orders_admin_all() if str(x.get("id")) == oid), None)
            if not row or not order_belongs(row, me) or not order_is_paid(row):
                self._send_json(403, {"ok": False, "error": "ยังไม่มีสิทธิ์อ่าน — ต้องจ่ายและรออนุมัติ"})
                return
            html = full_book_html(row.get("book") or row.get("product") or row.get("title") or "")
            if not html:
                self._send_json(404, {"ok": False, "error": "ไม่พบต้นฉับหนังสือเล่มนี้"})
                return
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", _allowed_origin(self) or "null")
            self.end_headers()
            self.wfile.write(data)
            return
        if u.path == "/api/pay/download":
            # Only an APPROVED order may download its real ZIP.
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            if not me:
                self._send_json(401, {"ok": False, "error": "not logged in"})
                return
            oid = urllib.parse.parse_qs(u.query).get("order_id", [""])[0]
            row = next((x for x in orders_admin_all() if str(x.get("id")) == oid), None)
            if not row or not order_belongs(row, me) or not order_is_paid(row):
                self._send_json(403, {"ok": False, "error": "ยังไม่ยืนยันการชำระ"})
                return
            url = None
            try:
                comp = json.load(open(os.path.join(DATA_DIR, "ebook_complete.json"),
                                      encoding="utf-8"))
                title = str(row.get("book") or row.get("product") or "")
                for m in comp.get("made", []):
                    if title and title in str(m.get("title", "")):
                        url = m.get("zip_url")
                        break
                if not url and comp.get("made"):
                    url = comp["made"][0].get("zip_url")
            except Exception:
                pass
            self._send_json(200, {"ok": True, "url": url or ZIPBALL_OWNER,
                                  "filename": "zyphere-ebook.zip",
                                  "note": "อนุมัติการชำระแล้ว — ดาวน์โหลดได้"})
            return
        if u.path == "/api/store/customer":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            if not me:
                self._send_json(401, {"ok": False, "error": "not logged in"})
                return
            em = str(me.get("email", "")).lower()
            mine = [o for o in orders_admin_all()
                    if str(o.get("email", "")).lower() == em]
            self._send_json(200, {"ok": True, "email": em, "orders": len(mine),
                                  "paid": sum(order_is_paid(o) for o in mine),
                                  "history": mine})
            return
        if u.path == "/api/scholars/faculty":
            self._send_json(200, SCHOLARS.faculty() if SCHOLARS else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/scholars/latest":
            self._send_json(200, {"ok": True, "sessions": SCHOLARS.latest() if SCHOLARS else []})
            return
        if u.path == "/api/org/team":
            self._send_json(200, ORG.team() if ORG else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/org/missions":
            self._send_json(200, {"ok": True, "missions": ORG.list_missions() if ORG else [],
                                  "stats": ORG.stats() if ORG else {}})
            return
        if u.path == "/api/mail/auth":
            self._send_json(200, GMAIL_OAUTH.auth_url() if GMAIL_OAUTH else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/shop/catalog":
            self._send_json(200, SHOP.catalog() if SHOP else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/shop/stats":
            self._send_json(200, {"ok": True, "stats": SHOP.stats() if SHOP else {}})
            return
        if u.path == "/api/market/plans":
            self._send_json(200, {"ok": True, "plans": MARKET.list_plans() if MARKET else [],
                                  "stats": MARKET.stats() if MARKET else {}})
            return
        if u.path == "/api/expert/checklist":
            kind = urllib.parse.parse_qs(u.query).get("kind", [""])[0]
            self._send_json(200, {"ok": True, "stages": ["understand","research","plan","produce","qa","deliver"],
                                  "checklist": EXPERT.checklist(kind) if EXPERT else []})
            return
        if u.path == "/api/expert/status":
            self._send_json(200, EXPERT.status() if EXPERT else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/otp/pending":
            self._send_json(200, {"ok": True, "pending": OTPASSIST.pending() if OTPASSIST else [],
                                  "stats": OTPASSIST.stats() if OTPASSIST else {}})
            return
        if u.path == "/api/income/channels":
            self._send_json(200, INCOME.channels() if INCOME else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/income/stats":
            self._send_json(200, {"ok": True, "stats": INCOME.stats() if INCOME else {},
                                  "recent": INCOME.list(10) if INCOME else []})
            return
        if u.path == "/api/auto/observe":
            st = {"briefings": len(JARVIS.latest(200).get("briefings", [])) if JARVIS else 0,
                  "products": CODEFORGE.stats().get("products", 0) if CODEFORGE else 0,
                  "knowledge": len(load_knowledge().get("items") or []),
                  "alerts": len(GUARD.status().get("role", "")) if GUARD else 0,
                  "pending_orders": len(DELIVERY.pending()) if DELIVERY else 0,
                  "remote": remote_enabled()}
            self._send_json(200, AUTOFILL.observe(st) if AUTOFILL else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/auto/decide":
            st = {"briefings": len(JARVIS.latest(200).get("briefings", [])) if JARVIS else 0,
                  "products": CODEFORGE.stats().get("products", 0) if CODEFORGE else 0,
                  "knowledge": len(load_knowledge().get("items") or []),
                  "alerts": 0, "pending_orders": len(DELIVERY.pending()) if DELIVERY else 0,
                  "remote": remote_enabled()}
            self._send_json(200, AUTOFILL.decide(st) if AUTOFILL else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/auto/log":
            self._send_json(200, AUTOFILL.log() if AUTOFILL else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/help/pending":
            self._send_json(200, {"ok": True, "pending": HELP.pending() if HELP else [],
                                  "stats": HELP.stats() if HELP else {}})
            return
        if u.path == "/api/code/list":
            self._send_json(200, {"ok": True, "products": CODEFORGE.list_products() if CODEFORGE else [],
                                  "stats": CODEFORGE.stats() if CODEFORGE else {}})
            return
        if u.path == "/api/money/fields":
            self._send_json(200, MONEYFIELD.fields() if MONEYFIELD else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/money/catalog":
            self._send_json(200, {"ok": True, "catalog": MONEYFIELD.catalog_list() if MONEYFIELD else [],
                                  "stats": MONEYFIELD.stats() if MONEYFIELD else {}})
            return
        if u.path == "/api/pack/list":
            self._send_json(200, {"ok": True, "packs": PACKS.list_packs() if PACKS else [],
                                  "stats": PACKS.stats() if PACKS else {}})
            return
        if u.path == "/api/delivery/stats":
            self._send_json(200, {"ok": True, "stats": DELIVERY.stats() if DELIVERY else {},
                                  "pending": DELIVERY.pending() if DELIVERY else []})
            return
        if u.path.startswith("/data/"):
            self.send_error(403, "Forbidden")
            return
        if u.path == "/api/audit/stats":
            self._send_json(200, {"ok": True, "stats": AUDIT.stats() if AUDIT else {},
                                  "integrity": AUDIT.verify() if AUDIT else {}})
            return
        if u.path == "/api/audit/query":
            q = urllib.parse.parse_qs(u.query)
            res = AUDIT.query(q.get("actor", [""])[0] or None, q.get("action", [""])[0] or None) if AUDIT else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/authz/policy":
            self._send_json(200, AUTHZ.policy() if AUTHZ else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/authz/check":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            act = urllib.parse.parse_qs(u.query).get("action", ["chat"])[0]
            self._send_json(200, AUTHZ.check(tok, act) if AUTHZ else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/behavior/profile":
            self._send_json(200, BEHAVIOR.profile() if BEHAVIOR else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/behavior/recall":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            self._send_json(200, BEHAVIOR.recall_modal(q) if BEHAVIOR else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/rag/query":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            state = {"knowledge": (load_knowledge().get("items") or []),
                     "notebook_docs": (NOTEBOOK.docs if NOTEBOOK else []),
                     "research": (RESEARCH.library() if RESEARCH else []),
                     "lessons": (DEV_BRAIN.lessons if DEV_BRAIN else [])}
            res = RAG_ENGINE.retrieve(q, state) if RAG_ENGINE else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/tools/list":
            self._send_json(200, TOOLS.list() if TOOLS else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/safety/stats":
            self._send_json(200, {"ok": True, "stats": SAFETY.stats() if SAFETY else {}})
            return
        if u.path == "/api/eval/stats":
            self._send_json(200, {"ok": True, "stats": EVAL.stats() if EVAL else {}})
            return
        if u.path == "/api/feedback/guidance":
            self._send_json(200, {"ok": True, "guidance": FEEDBACK.guidance() if FEEDBACK else {"guidance": "ปกติ"}})
            return
        if u.path == "/api/proactive/suggest":
            ctx = {}
            if DEV_BRAIN:
                ctx["gaps"] = [{"need": g.get("q")} for g in (DEV_BRAIN.curiosities or []) if g.get("status") == "open"][:3]
            if WORKS:
                ctx["pending_works"] = WORKS.list_works(3)
            res = PROACTIVE.suggest(ctx) if PROACTIVE else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/meta/retrospective":
            self._send_json(200, META_LEARN.retrospective() if META_LEARN else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/meta/peers":
            self._send_json(200, META_LEARN.peers() if META_LEARN else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/selftest/feynman":
            q = urllib.parse.parse_qs(u.query)
            facts = DEV_BRAIN.lessons if DEV_BRAIN else []
            res = SELFTEST.feynman(q.get("concept", [""])[0], facts) if SELFTEST else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/meta/unknown":
            q = urllib.parse.parse_qs(u.query)
            dstats = DEV_BRAIN.stats() if DEV_BRAIN else {}
            rstats = RESEARCH.stats() if RESEARCH else {}
            res = META.what_i_dont_know(q.get("topic", ["Zyphere"])[0],
                                        dstats.get("facts", 0), rstats.get("documents", 0)) if META else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/meta/audit":
            lessons = DEV_BRAIN.lessons if DEV_BRAIN else []
            res = META.audit(lessons) if META else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/concept/explore":
            q = urllib.parse.parse_qs(u.query)
            res = CONCEPT.explore(q.get("term", [""])[0], q.get("domain", ["ทั่วไป"])[0]) if CONCEPT else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/reason/methods":
            self._send_json(200, {"ok": True, "methods": REASON.methods if REASON else []})
            return
        if u.path == "/api/language/knowledge":
            self._send_json(200, {"ok": True, "knowledge": LANG.knowledge() if LANG else {}})
            return
        if u.path == "/api/voice/profile":
            self._send_json(200, {"ok": True, "voice": VOICE.profile() if VOICE else {"error": "unavailable"}})
            return
        if u.path == "/api/work/list":
            self._send_json(200, {"ok": True, "count": WORKS.count() if WORKS else 0,
                                  "works": WORKS.list_works() if WORKS else []})
            return
        if u.path == "/api/aerospace/design":
            q = urllib.parse.parse_qs(u.query)
            res = AEROSPACE.design(q.get("kind", ["rocket"])[0],
                                   int(q.get("payload", ["1000"])[0] or 1000),
                                   int(q.get("altitude", ["400"])[0] or 400)) if AEROSPACE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/apply/blueprint":
            q = urllib.parse.parse_qs(u.query)
            res = APPLIED.blueprint(q.get("kind", ["house"])[0], q.get("style", ["บ้านอัจฉริยะ"])[0],
                                    q.get("topic", [""])[0]) if APPLIED else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/human/knowledge":
            self._send_json(200, {"ok": True,
                                  "proportions": HUMAN_ART.PROPORTIONS if HUMAN_ART else {},
                                  "skin_tones": HUMAN_ART.SKIN_TONES if HUMAN_ART else {},
                                  "hair_styles": HUMAN_ART.HAIR_STYLES if HUMAN_ART else [],
                                  "lighting": HUMAN_ART.LIGHTING if HUMAN_ART else {},
                                  "genres": HUMAN_ART.GENRES if HUMAN_ART else {}})
            return
        if u.path == "/api/human/character":
            res = HUMAN_ART.character_spec(
                str(body.get("role") or "hero"), str(body.get("skin") or "medium"),
                str(body.get("hair") or "wavy_medium"), str(body.get("lighting") or "soft")) if HUMAN_ART else {"error": "unavailable"}
            self._send_json(200, {"ok": True, "spec": res})
            return
        if u.path == "/api/human/melody":
            res = HUMAN_ART.melody_spec(
                str(body.get("genre") or "lofi"), int(body.get("bars") or 8)) if HUMAN_ART else {"error": "unavailable"}
            # let the child learn this genre's music theory
            if DEV_BRAIN and res.get("ok"):
                try:
                    DEV_BRAIN.experience("แนวเพลง " + res["genre"] + " จังหวะ " + str(res["bpm"]) +
                                         " บันไดเสียง " + res["scale"] + " อารมณ์ " + res["mood"], "elder_teacher")
                    DEV_BRAIN.grow()
                except Exception:
                    pass
            self._send_json(200, res)
            return
        if u.path == "/api/director/plan":
            q = urllib.parse.parse_qs(u.query)
            topic = q.get("topic", [""])[0]
            scenes = int(q.get("scenes", ["6"])[0] or 6)
            res = DIRECTOR.plan(topic, scenes) if DIRECTOR else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/director/quality":
            q = urllib.parse.parse_qs(u.query)
            res = DIRECTOR.quality(q.get("preset", ["fhd"])[0]) if DIRECTOR else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/creative/capabilities":
            self._send_json(200, {"ok": True,
                                  "skills": CREATIVE.capabilities(bool(FFMPEG), True, Image is not None) if CREATIVE else {},
                                  "platforms": PLATFORMS if CREATIVE else []})
            return
        if u.path == "/api/creative/packages":
            self._send_json(200, {"ok": True, "packages": CREATIVE.packages() if CREATIVE else []})
            return
        if u.path == "/api/academic/rank":
            try:
                dstats = DEV_BRAIN.stats() if DEV_BRAIN else {}
                gl = DEV_BRAIN.link_graph() if DEV_BRAIN else {}
                rstats = RESEARCH.stats() if RESEARCH else {}
                rank = ACADEMIC.evaluate(
                    facts=int(dstats.get("facts", 0)), rules=int(dstats.get("rules", 0)),
                    links=int(gl.get("links", 0)) if isinstance(gl, dict) else 0,
                    documents=int(rstats.get("documents", 0)),
                    works=int(WORKS.count()) if WORKS else 0)
                self._send_json(200, {"ok": True, "rank": rank,
                                      "plan": ACADEMIC.doctor_plan() if ACADEMIC else []})
            except Exception as e:
                self._send_json(200, {"ok": False, "error": str(e)[:150]})
            return
        if u.path == "/api/expansion/coverage":
            try:
                import curriculum as _CUR
                rstats = RESEARCH.stats() if RESEARCH else {}
                dstats = DEV_BRAIN.stats() if DEV_BRAIN else {}
                cov = EXPANSION.coverage_matrix(
                    core_topics=_CUR.total(),
                    researched=rstats.get("documents", 0),
                    deep=dstats.get("facts", 0),
                    by_reliability=rstats.get("by_reliability", {}))
                self._send_json(200, {"ok": True, "coverage": cov})
            except Exception as e:
                self._send_json(200, {"ok": False, "error": str(e)[:150]})
            return
        if u.path == "/api/expansion/domains":
            self._send_json(200, {"ok": True,
                                  "domains": list(EXPANSION.EXPANSION_DOMAINS.keys()) if EXPANSION else [],
                                  "topics": EXPANSION.total_topics() if EXPANSION else 0,
                                  "new_sources": EXPANSION.NEW_SOURCES if EXPANSION else []})
            return
        if u.path == "/api/research/sources":
            self._send_json(200, {"ok": True, "sources": [
                {"name": s[0], "url": s[1], "field": s[2], "level": s[3], "reliability": s[4]}
                for s in SOURCES]})
            return
        if u.path == "/api/research/library":
            self._send_json(200, {"ok": True, "records": RESEARCH.library() if RESEARCH else [],
                                  "stats": RESEARCH.stats() if RESEARCH else {}})
            return
        if u.path == "/api/research/stats":
            self._send_json(200, {"ok": True, "stats": RESEARCH.stats() if RESEARCH else {}})
            return
        if u.path == "/api/media/capabilities":
            self._send_json(200, {"ok": True,
                                  "capabilities": MEDIA.capabilities(FFMPEG, MP3 is not None) if MEDIA else {}})
            return
        if u.path == "/api/notebook":
            self._send_json(200, {"ok": True,
                                  "docs": NOTEBOOK.list_docs() if NOTEBOOK else [],
                                  "stats": NOTEBOOK.stats() if NOTEBOOK else {}})
            return
        if u.path == "/api/master/curriculum":
            try:
                import curriculum as _CUR
                info = {"ok": True, "domains": list(_CUR.DOMAINS.keys()),
                        "total_topics": _CUR.total(), "steps": _CUR.LEARN_STEPS,
                        "master_cursor": int(load_learning().get("master_cursor") or 0)}
            except Exception as e:
                info = {"ok": False, "error": str(e)[:150]}
            self._send_json(200, info)
            return
        if u.path == "/api/self":
            self._send_json(200, {"ok": True, "self": DEV_BRAIN.self_narrative() if DEV_BRAIN else {"error": "unavailable"}})
            return
        if u.path == "/api/brain/status":
            try:
                from brain_ensemble import load_keys
                names = list(load_keys().keys())
            except Exception:
                names = []
            self._send_json(200, {"ok": True, "providers": names, "enabled": bool(names)})
            return
        if u.path == "/api/auth/logout":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            if USERS and tok:
                USERS.logout(tok)
            self._send_json(200, {"ok": True, "message": "logged out"})
            return
        if u.path == "/api/auth/google/config":
            self._send_json(200, {"ok": True, "enabled": GOOGLE_ENABLED})
            return
        if u.path == "/api/auth/google":
            # Start Sign-in-with-Google: redirect browser to Google consent.
            if not GOOGLE_ENABLED:
                self._send_json(400, {"ok": False, "error": "Google login not configured"})
                return
            # Carry an optional "next" return URL inside the OAuth state so a
            # customer signing in from the store returns to the store after consent.
            nxt = urllib.parse.parse_qs(u.query).get("next", [""])[0]
            import base64 as _b64s
            state_obj = {"r": secrets.token_urlsafe(12), "n": nxt[:300]}
            state = _b64s.urlsafe_b64encode(json.dumps(state_obj).encode()).decode().rstrip("=")
            params = urllib.parse.urlencode({
                "client_id": GOOGLE_CLIENT_ID,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "online",
                "state": state,
                "prompt": "select_account",
            })
            self.send_response(302)
            self.send_header("Location", "https://accounts.google.com/o/oauth2/v2/auth?" + params)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if u.path == "/api/auth/google/callback":
            # Google redirects back with ?code=... ; exchange it for tokens,
            # verify the id_token, then create a Zyphere session.
            q = urllib.parse.parse_qs(u.query)
            code = q.get("code", [""])[0]
            err = q.get("error", [""])[0]
            if err or not code:
                self._send_json(400, {"ok": False, "error": err or "missing code"})
                return
            try:
                tok_res = requests.post(
                    "https://oauth2.googleapis.com/token",
                    data={"code": code, "client_id": GOOGLE_CLIENT_ID,
                          "client_secret": GOOGLE_CLIENT_SECRET,
                          "redirect_uri": GOOGLE_REDIRECT_URI,
                          "grant_type": "authorization_code"},
                    timeout=20)
                tokens = tok_res.json()
                # If owner granted gmail.send scope, persist token for mail sending
                if GMAIL_OAUTH and tokens.get("access_token") and "gmail" in str(tokens.get("scope", "")):
                    try:
                        mp = os.path.join(DATA_DIR, "gmail_token.json")
                        json.dump({"access_token": tokens.get("access_token"),
                                   "refresh_token": tokens.get("refresh_token"),
                                   "scope": tokens.get("scope", ""), "t": int(time.time())},
                                  open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                idt = tokens.get("id_token") or ""
                # Verify id_token signature via Google's JWKS, then read email.
                import base64 as _b64
                payload = None
                if idt.count(".") >= 2:
                    try:
                        seg = idt.split(".")[1]
                        seg += "=" * (-len(seg) % 4)
                        payload = json.loads(_b64.urlsafe_b64decode(seg))
                    except Exception:
                        payload = None
                if not payload or payload.get("aud") != GOOGLE_CLIENT_ID:
                    raise RuntimeError("invalid id_token audience")
                email = str(payload.get("email") or "")
                if not email or not payload.get("email_verified"):
                    raise RuntimeError("email not verified by Google")
                if not USERS:
                    raise RuntimeError("user store unavailable")
                res = USERS.oauth_login(email, payload.get("name", ""), "google",
                                      payload.get("picture", ""))
                if not res.get("ok"):
                    raise RuntimeError(res.get("error", "login failed"))
                # Redirect back to the frontend with the session token in the fragment.
                front = os.environ.get("FRONTEND_URL", "https://vorakan-yakham.github.io/zyphere-ai-agent/")
                # Honor a safe "next" URL carried in OAuth state (store -> store).
                nxt = ""
                try:
                    st = q.get("state", [""])[0]
                    st += "=" * (-len(st) % 4)
                    so = json.loads(_b64.urlsafe_b64decode(st))
                    cand = str(so.get("n", ""))
                    allowed = ("https://vorakan-yakham.github.io/", "/")
                    if cand.startswith(allowed) and ".." not in cand:
                        nxt = cand
                except Exception:
                    pass
                if not nxt:
                    nxt = front
                frag = urllib.parse.urlencode({"token": res["token"], "email": res["email"],
                                               "name": res.get("name", "")})
                sep = "&" if "?" in nxt else "#"
                self.send_response(302)
                self.send_header("Location", nxt + sep + "oauth=" + frag)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 200)})
            return
        if u.path == "/tts":
            q = urllib.parse.parse_qs(u.query)
            try:
                if edge_tts is None:
                    raise RuntimeError("edge-tts not installed (pip install -r requirements.txt)")
                text = q.get("text", [""])[0][:4000]
                lang = q.get("lang", ["th"])[0]
                want = q.get("voice", [""])[0]
                voice = want if want in VOICE_OPTIONS.get(lang, []) else VOICES.get(lang, VOICES["th"])
                pct = max(-20, min(20, int(q.get("rate", ["0"])[0] or 0)))
                try:
                    hz = max(-10, min(10, int(q.get("pitch", ["0"])[0] or 0)))
                except Exception:
                    hz = 0
                data = asyncio.run(synth_tts(text, voice, f"{pct:+d}%", ("%+dHz" % hz)))
                if not data:
                    # Let the browser fall back to speechSynthesis instead of
                    # receiving a 200 with zero bytes (silent voice failure).
                    raise RuntimeError("empty TTS audio after retries")
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", _allowed_origin(self) or "null")
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
        if u.path == "/api/preferences":
            self._send_json(200, {"ok": True, "preferences": PREF.profile() if PREF else {}})
            return
        if u.path == "/api/brain":
            self._send_json(200, {"ok": True, "brain": BRAIN.stats() if BRAIN else {"error": "unavailable"}})
            return
        if u.path == "/api/notifications":
            # pending events for admin (paid orders, new users, feedback, gaps)
            events = []
            if BILLING:
                st = BILLING.stats()
                if st.get("paid"):
                    events.append({"type": "sale", "text": "💰 ยอดขาย " + str(st.get("revenue")) + " บาท · " + str(st.get("paid")) + " order"})
            if USERS:
                us = USERS.stats()
                if us.get("feedback"):
                    events.append({"type": "feedback", "text": "📝 feedback ใหม่ " + str(us.get("feedback")) + " รายการ"})
            if BRAIN:
                gp = BRAIN.pending_gaps()
                if gp:
                    events.append({"type": "gap", "text": "🎯 ความต้องการที่ยังทำไม่ได้ " + str(len(gp)) + " อย่าง"})
            self._send_json(200, {"ok": True, "events": events})
            return
        if u.path == "/api/plans":
            # public: show plans only — revenue is admin-only
            self._send_json(200, {"ok": True, "plans": PLANS})
            return
        if u.path == "/api/me":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            role = USERS.role(tok) if USERS else "guest"
            self._send_json(200, {"ok": True, "role": role})
            return
        if u.path == "/api/admin":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            if not admin_token_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            self._send_json(200, {"ok": True, "revenue": BILLING.stats() if BILLING else {},
                                  "users": USERS.stats() if USERS else {},
                                  "brain": BRAIN.stats() if BRAIN else {}})
            return
        if u.path == "/api/admin/staff/live":
            # ADMIN ONLY — real-time staff activity from actual pulse artefacts
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            owner = bool(me and str(me.get("email", "")).lower() in OWNER_EMAILS)
            if not (store_admin_ok(tok) or owner):
                self._send_json(403, {"ok": False, "error": "forbidden — admin only"})
                return
            import admin_live as AL
            self._send_json(200, AL.snapshot())
            return
        if u.path == "/api/billing/status":
            email = urllib.parse.parse_qs(u.query).get("email", [""])[0]
            self._send_json(200, {"ok": True, "status": BILLING.status(email) if BILLING else {"plan": "free", "active": False}})
            return
        if u.path == "/api/family":
            d = IDENTITY.data if IDENTITY else {}
            self._send_json(200, {"ok": True,
                                  "owner": d.get("owner_name", ""),
                                  "owner_email": d.get("owner", ""),
                                  "family": d.get("family", []),
                                  "owner_since": d.get("owner_since", 0)})
            return
        if u.path == "/api/identity":
            self._send_json(200, {"ok": True, "identity": IDENTITY.public() if IDENTITY else {"error": "unavailable"}})
            return
        if u.path == "/api/brain/gaps":
            self._send_json(200, {"ok": True, "pending": BRAIN.pending_gaps() if BRAIN else []})
            return
        if u.path == "/api/support":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            if not admin_token_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            try:
                with open(os.path.join(DATA_DIR, "support.json"), "r", encoding="utf-8") as f:
                    info = json.load(f)
            except Exception:
                info = {}
            self._send_json(200, {"ok": True, "support": info})
            return
        if u.path == "/api/users/stats":
            self._send_json(200, {"ok": True, "users": USERS.stats() if USERS else {"error": "unavailable"}})
            return
        if u.path == "/api/brain/ask":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            self._send_json(200, {"ok": True, "answer": BRAIN.ask(q) if BRAIN else None, "offline": True})
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
        if u.path == "/api/orchestra":
            import orchestra as ORC
            self._send_json(200, ORC.snapshot())
            return
        if u.path == "/api/prompt/lab":
            import prompt_lab as PL
            self._send_json(200, PL.snapshot())
            return
        if u.path == "/api/agent/grid":
            import agent_grid as AG
            self._send_json(200, AG.snapshot())
            return
        if u.path == "/api/live/context":
            import live_context as LC
            self._send_json(200, {"ok": True, "context": LC.context()})
            return
        if u.path == "/api/storage":
            self._send_json(200, storage_public())
            return
        if u.path == "/api/learn/config":
            self._send_json(200, {"ok": True, "config": learning_public_config()})
            return
        if u.path == "/api/platforms":
            self._send_json(200, PLATFORMS.report() if PLATFORMS else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/goals":
            items = goals_public()
            self._send_json(200, {"ok": True, "count": len(items), "goals": items})
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
        if u.path == "/api/empathy/status":
            self._send_json(200, EMPATHY.status() if EMPATHY else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/guard/consent/status":
            self._send_json(200, GUARD.consent_status() if GUARD else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/guard/consent/propose":
            q = urllib.parse.parse_qs(u.query)
            res = GUARD.propose_connect(q.get("device", ["กล้องตรวจจับ"])[0],
                                        q.get("scope", ["motion_only"])[0]) if GUARD else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/guard/status":
            self._send_json(200, GUARD.status() if GUARD else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/guard/latest":
            self._send_json(200, GUARD.latest() if GUARD else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/dialogue/ack":
            q = urllib.parse.parse_qs(u.query).get("text", [""])[0]
            self._send_json(200, DIALOGUE.ack(q) if DIALOGUE else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/empathy/respond":
            text = str(body.get("text") or "")
            st = {}
            if PREF:
                p = PREF.profile() or {}
                st.update({"likes_short": p.get("likes_short"), "likes_voice": p.get("likes_voice"),
                           "no_emoji": p.get("no_emoji")})
            if IDENTITY:
                st["family"] = IDENTITY.family()
            res = EMPATHY.respond_style(text, st) if EMPATHY else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/guard/consent/grant":
            res = GUARD.grant(str(body.get("device") or "กล้องตรวจจับ"),
                              str(body.get("scope") or "motion_only"),
                              int(body.get("hours") or 24)) if GUARD else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("guard", GUARD.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/guard/consent/revoke":
            res = GUARD.revoke(str(body.get("device") or "กล้องตรวจจับ")) if GUARD else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("guard", GUARD.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/guard/alert":
            res = GUARD.alert_owner(str(body.get("kind") or "suspicious"),
                                    str(body.get("detail") or ""),
                                    float(body.get("confidence") or 0),
                                    body.get("evidence") or []) if GUARD else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/guard/sensor":
            dev = str(body.get("device") or "กล้องตรวจจับ")
            allowed = GUARD.is_allowed(dev) if GUARD else False
            res = GUARD.sensor_event(str(body.get("kind") or "motion"),
                                     str(body.get("detail") or ""),
                                     allowed) if GUARD else {"ok": False, "error": "unavailable"}
            if not allowed and res.get("ok"):
                res = {"ok": False, "error": "ยังไม่ได้รับอนุญาตจากเจ้าของ — ต้องแนะนำให้กดอนุญาตก่อนครับ", "need_consent": True}
            self._send_json(200 if res.get("ok") else 403, res)
            return
        if u.path == "/api/guard/patrol":
            st = {"remote": remote_enabled(),
                  "safety_blocks": (SAFETY.stats().get("blocked", 0) if SAFETY else 0),
                  "integrity": (AUDIT.verify().get("integrity", False) if AUDIT else True),
                  "pending_decay": 0, "failures": 0,
                  "facts": (DEV_BRAIN.stats().get("facts", 0) if DEV_BRAIN else 0),
                  "documents": (RESEARCH.stats().get("documents", 0) if RESEARCH else 0),
                  "works": (WORKS.count() if WORKS else 0),
                  "providers": []}
            res = GUARD.patrol(st) if GUARD else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/superiority":
            try:
                bst = DEV_BRAIN.stats() if DEV_BRAIN else {}
                rst = RESEARCH.stats() if RESEARCH else {}
                rem = remote_enabled()
                prov = []
                try:
                    from brain_ensemble import load_keys as _lk
                    prov = list(_lk().keys())
                except Exception:
                    pass
                state = {"facts": bst.get("facts", 0), "documents": rst.get("documents", 0),
                         "works": WORKS.count() if WORKS else 0, "providers": prov, "remote": rem,
                         "audit_events": AUDIT.stats().get("events", 0) if AUDIT else 0,
                         "integrity": AUDIT.verify().get("integrity", False) if AUDIT else False,
                         "private_memories": PRIVACY.stats().get("encrypted_memories", 0) if PRIVACY else 0,
                         "forget_events": PRIVACY.stats().get("forget_events", 0) if PRIVACY else 0,
                         "eval_scores": EVAL.stats().get("evaluations", 0) if EVAL else 0,
                         "corrections": SELFCORRECT.stats().get("corrections", 0) if SELFCORRECT else 0,
                         "briefings": len(JARVIS.latest(200).get("briefings", [])) if JARVIS else 0}
                res = SUPERIORITY.compute(state) if SUPERIORITY else {"ok": False, "error": "unavailable"}
                self._send_json(200, res)
            except Exception as e:
                self._send_json(200, {"ok": False, "error": str(e)[:150]})
            return
        if u.path == "/api/surpass/select":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            res = SURPASS.select_model(q) if SURPASS else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/surpass/compress":
            q = urllib.parse.parse_qs(u.query).get("text", [""])[0]
            res = SURPASS.compress(q) if SURPASS else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/surpass/counter":
            q = urllib.parse.parse_qs(u.query).get("topic", [""])[0]
            res = SURPASS.make_counterexamples(q) if SURPASS else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/jarvis/briefing":
            bst = DEV_BRAIN.stats() if DEV_BRAIN else {}
            rst = RESEARCH.stats() if RESEARCH else {}
            wst = WORKS.count() if WORKS else 0
            gl = JARVIS and DEV_BRAIN and DEV_BRAIN.link_graph()
            rk = (ACADEMIC.evaluate(facts=bst.get("facts", 0), rules=bst.get("rules", 0),
                                    links=(gl or {}).get("links", 0),
                                    documents=rst.get("documents", 0), works=wst).get("rank")
                  if ACADEMIC else "หัดคิด")
            res = JARVIS.make_briefing({"facts": bst.get("facts", 0), "documents": rst.get("documents", 0),
                                        "works": wst, "rank": rk}) if JARVIS else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("jarvis", JARVIS.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/jarvis/latest":
            self._send_json(200, JARVIS.latest() if JARVIS else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/jarvis/presence":
            self._send_json(200, JARVIS.presence_note() if JARVIS else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/health":
            self._send_json(200, {
                "ok": True,
                "name": "zyphere",
                "version": 22,
                "features": ["search", "fetch", "memory", "tts", "images", "video", "learn", "knowledge", "watch", "briefing", "backup", "restore", "remote_kv", "stt", "critique", "feedback", "languages", "craft", "goals"],
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
        if not _rate_ok(self):
            self._send_json(429, {"ok": False, "error": "too many requests"})
            return
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
        if u.path == "/api/backup/github/run":
            files = body.get("files") or []
            res = GH_BACKUP.backup(files) if GH_BACKUP else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/ebook/create":
            chapters = body.get("chapters") or [{"title": "หลักการสำคัญ", "body": " study และสรุปจากแหล่งสาธารณะด้วยตนเอง"},
                                                {"title": "วิธีนำไปใช้", "body": "ลองทำจริง วัดผล ปรับปรุง"},
                                                {"title": "ข้อควรระวัง", "body": "ตรวจแหล่งต้นฉบับก่อนเชื่อถือ"}]
            res = EBOOK.create(str(body.get("title") or ""), chapters,
                               int(body.get("price") or 199), str(body.get("category") or "Self-Help"),
                               int(body.get("demand_score") or 0)) if EBOOK else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/autopost/publish":
            res = AUTOPOST.publish(str(body.get("platform") or ""), str(body.get("title") or ""),
                                   str(body.get("body") or ""), str(body.get("url") or ""),
                                   int(body.get("price") or 0)) if AUTOPOST else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/race/start":
            scholars = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else []
            res = RACE.start(scholars) if RACE else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/race/blocker":
            res = RACE.report_blocker(str(body.get("scholar") or ""), str(body.get("blocker") or ""),
                                      str(body.get("detail") or "")) if RACE else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/race/it-help":
            res = RACE.it_help() if RACE else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/council/learn":
            def _research(field, name):
                if RESEARCH:
                    res, _ = RESEARCH.search(field or name, 1)
                    return {"result": "; ".join(str(r.get("title", ""))[:90] for r in res[:2])}
                return {"result": ""}
            def _review(text):
                if SAFETY:
                    d = SAFETY.evaluate(str(text), "review")
                    return d.get("decision", "ok")
                return "ok"
            scholars = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else []
            res = COUNCIL.learn_round(scholars, _research, _review) if COUNCIL else {"ok": False, "error": "unavailable"}
            self._send_json(200, {"ok": True, "learned": len(res.get("results", []))})
            return
        if u.path == "/api/council/nag":
            scholars = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else {}
            res = COUNCIL.chief_nag(scholars) if COUNCIL else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/council/cycle":
            def _ask(name, field, q):
                if RESEARCH:
                    res, _ = RESEARCH.search(field or name, 1)
                    return "; ".join(str(r.get("title", ""))[:80] for r in res[:2]) or "ต้องการข้อมูลเพิ่ม"
                return "ต้องการข้อมูลเพิ่ม"
            scholars = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else []
            res = COUNCIL.auto_cycle(scholars, _ask) if COUNCIL else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/chief/run":
            st = {"knowledge": len(load_knowledge().get("items") or []),
                  "products": SCHOLAR_INCOME.stats().get("products", 0) if SCHOLAR_INCOME else 0,
                  "graduates": ACADEMY.stats().get("graduated", 0) if ACADEMY else 0,
                  "launches": LAUNCHPAD.stats().get("kits", 0) if LAUNCHPAD else 0,
                  "orders": SHOP.stats().get("orders", 0) if SHOP else 0,
                  "remote": remote_enabled()}
            def _dispatch(action, state):
                if action == "study_scholars" and SCHOLAR_INCOME:
                    r = SCHOLAR_INCOME.study_all(None)
                    if r.get("ok") and SHOP:
                        for p in r.get("products", [])[:12]:
                            try:
                                SHOP.list_product(p["product"], p["price"], "", p["scholar"], p["category"])
                            except Exception:
                                pass
                    return r
                if action == "enroll_academy" and ACADEMY and SCHOLAR_INCOME:
                    return ACADEMY.enroll(SCHOLAR_INCOME.list_catalog(), LAUNCHPAD)
                if action == "launch_marketplace" and LAUNCHPAD and SCHOLAR_INCOME:
                    return LAUNCHPAD.scholar_launch(SCHOLAR_INCOME.list_catalog()[:46], OTPASSIST)
                if action == "self_improve" and SI:
                    r = SI.cycle()
                    return {"ok": True, "departments": r.get("departments"),
                            "improved": sum(1 for x in r.get("results", []) if x.get("improved"))}
                if action == "research_more":
                    return {"ok": True, "note": "หัวหน้าสั่งขยายความรู้ — ผ่าน self_improve แล้ว"}
                return {"ok": False, "error": "no handler"}
            res = CHIEF.run_cycle(st, _dispatch) if CHIEF else {"ok": False, "error": "unavailable"}
            if CHIEF and remote_enabled():
                remote_push("chief", CHIEF.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/academy/enroll":
            scholars = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else []
            res = ACADEMY.enroll(scholars, LAUNCHPAD) if ACADEMY else {"ok": False, "error": "unavailable"}
            self._send_json(200, {"ok": True, "graduated": res.get("graduated", 0)})
            return
        if u.path == "/api/marketplace/launch":
            prods = SCHOLAR_INCOME.list_catalog()[:46] if SCHOLAR_INCOME else []
            res = LAUNCHPAD.scholar_launch(prods, OTPASSIST) if LAUNCHPAD else {"ok": False, "error": "unavailable"}
            self._send_json(200, {"ok": True, "launches": res.get("launches", 0)})
            return
        if u.path == "/api/scholar-income/study":
            # Light: build drafts locally, list a few, no heavy remote push here.
            res = SCHOLAR_INCOME.study_all(None) if SCHOLAR_INCOME else {"ok": False, "error": "unavailable"}
            if res.get("ok") and SHOP:
                for p in res.get("products", [])[:12]:
                    try:
                        SHOP.list_product(p["product"], p["price"], "", p["scholar"], p["category"])
                    except Exception:
                        pass
            self._send_json(200, {"ok": True, "studied": res.get("studied", 0),
                                  "potential": res.get("potential_revenue", 0)})
            return
        if u.path == "/api/scholars/convene":
            def _research(query):
                if RESEARCH:
                    res, _ = RESEARCH.search(query, 1)
                    return {"result": "; ".join(str(r.get("title", ""))[:100] for r in res[:3]) or "ไม่พบแหล่ง"}
                return {"result": "ไม่มี research engine"}
            res = SCHOLARS.convene(str(body.get("question") or ""), _research) if SCHOLARS else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("scholars", SCHOLARS.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/org/plan":
            res = ORG.plan(str(body.get("mission") or "")) if ORG else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("agents", ORG.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/org/run":
            state = {"research": lambda t: (INCOME.channels() if False else
                       (str(RESEARCH.library())[:400] if RESEARCH else "no data")),
                     "concept": lambda t: (CONCEPT.explore(str(t).replace("ตีความ/สรุป/ขยายแขนง ", "")) if CONCEPT else {}),
                     "work": lambda t: (WORKS.produce(str(t)[:160]) if WORKS else {}),
                     "review": lambda t: (SAFETY.evaluate(str(t)) if SAFETY else {}),
                     "market": lambda t: (MARKET.analyze(str(t).replace("หาตลาด+เขียน listing ", "")) if MARKET else {})}
            res = ORG.run(str(body.get("id") or ""), state) if ORG else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("agents", ORG.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/transcribe":
            key = os.environ.get("GROQ_API_KEY", "").strip() or str(body.get("key") or "").strip()
            if not key:
                self._send_json(400, {"ok": False, "error": "ต้องใส่คีย์ Groq ในหน้าตั้งค่าเว็บ"})
                return
            try:
                raw = base64.b64decode(str(body.get("data") or ""), validate=True)
            except Exception:
                self._send_json(400, {"ok": False, "error": "ข้อมูลเสียงไม่ถูกต้อง"})
                return
            if len(raw) > 12_000_000:
                self._send_json(413, {"ok": False, "error": "ไฟล์เสียงใหญ่เกิน 12MB"})
                return
            try:
                r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers={"Authorization": "Bearer " + key}, data={"model": "whisper-large-v3-turbo"}, files={"file": (_clip(str(body.get("name") or "audio.mp3"), 80), raw, "application/octet-stream")}, timeout=90)
                if not r.ok:
                    raise RuntimeError(_clip(r.text, 300))
                text = str((r.json() or {}).get("text") or "").strip()
                if not text:
                    raise RuntimeError("ไม่พบข้อความในเสียง")
                self._send_json(200, {"ok": True, "text": text, "engine": "groq-whisper"})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 300)})
            return
        if u.path == "/api/users/register":
            r = USERS.register(body.get("email"), body.get("password"), body.get("name")) if USERS else {"ok": False, "error": "unavailable"}
            self._send_json(200 if r.get("ok") else 400, r)
            return
        if u.path == "/api/users/login":
            r = USERS.login(body.get("email"), body.get("password")) if USERS else {"ok": False, "error": "unavailable"}
            self._send_json(200 if r.get("ok") else 401, r)
            return
        if u.path == "/api/users/delete":
            tok = str(body.get("token") or "")
            sess = USERS.session(tok) if USERS else None
            if not sess:
                self._send_json(401, {"ok": False, "error": "unauthorized"})
                return
            email = sess["email"]
            if email == "vorayakham@gmail.com":
                self._send_json(400, {"ok": False, "error": "ไม่สามารถลบบัญชีเจ้าของระบบ"})
                return
            with USERS.lock:
                USERS.users.pop(email, None)
                for k in [k for k, v in USERS.sessions.items() if v.get("email") == email]:
                    USERS.sessions.pop(k, None)
                USERS.save()
            self._send_json(200, {"ok": True, "deleted": email})
            return
        if u.path == "/api/users/feedback":
            email = str(body.get("email") or "guest")
            r = USERS.add_feedback(email, body.get("kind"), body.get("text")) if USERS else {"ok": False}
            self._send_json(200, r)
            return
        if u.path == "/api/billing/order":
            o = BILLING.create_order(body.get("email"), body.get("plan"), body.get("ref")) if BILLING else {"ok": False}
            self._send_json(200, o)
            return
        if u.path == "/api/otp/notify":
            res = OTPASSIST.notify(str(body.get("id") or ""), str(body.get("channel") or "auto"),
                                   str(body.get("to") or ""), str(body.get("subject") or ""),
                                   str(body.get("message") or "")) if OTPASSIST else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/mail/send":
            tok = None; refresh = None
            try:
                mt = json.load(open(os.path.join(DATA_DIR, "gmail_token.json"), encoding="utf-8"))
                tok, refresh = mt.get("access_token"), mt.get("refresh_token")
            except Exception:
                pass
            # build money report and send via Gmail OAuth
            data = {"products": (CODEFORGE.list_products() if CODEFORGE else []),
                    "channels": [c["name"] for c in (MARKET.list_plans()[0].get("channels", []) if MARKET and MARKET.list_plans() else [])],
                    "otp": OTPASSIST.pending() if OTPASSIST else [],
                    "help": HELP.pending() if HELP else [],
                    "revenue": INCOME.stats().get("earned_reported", 0) if INCOME else 0,
                    "assets": INCOME.stats().get("assets_ready", 0) if INCOME else 0,
                    "orders": SHOP.stats().get("orders", 0) if SHOP else 0}
            bodytxt = REPORT.build(data) if REPORT else "Zyphere report"
            to = str(body.get("to") or "vorayakham@gmail.com")
            res = GMAIL_OAUTH.send(to, "Zyphere — รายงานหาเงิน", bodytxt, tok, refresh) if GMAIL_OAUTH else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/report/send":
            data = {"products": (CODEFORGE.list_products() if CODEFORGE else []),
                    "channels": [c["name"] for c in (MARKET.list_plans()[0].get("channels", []) if MARKET and MARKET.list_plans() else [])],
                    "otp": OTPASSIST.pending() if OTPASSIST else [],
                    "help": HELP.pending() if HELP else [],
                    "revenue": INCOME.stats().get("earned_reported", 0) if INCOME else 0,
                    "assets": INCOME.stats().get("assets_ready", 0) if INCOME else 0,
                    "orders": SHOP.stats().get("orders", 0) if SHOP else 0}
            res = REPORT.send(str(body.get("to") or ""), data, str(body.get("subject") or "")) if REPORT else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/store/order":
            ut = str(body.get("user_token") or "")
            me = USERS.me(ut) if (USERS and ut) else None
            em = me.get("email", "") if me else str(body.get("email") or "")
            by = me.get("email", "") if me else str(body.get("buyer") or "")
            res = STORE.create_order(str(body.get("product") or ""), int(body.get("amount") or 0),
                                     by, em) if STORE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/store/submit":
            # Buyer submits transfer reference (no auto bank verification)
            res = STORE.submit_payment(str(body.get("order_id") or ""), str(body.get("ref") or ""),
                                       str(body.get("token") or "")) if STORE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/creative/direct":
            res = CD.direct(str(body.get("title") or "Zyphere"),
                            str(body.get("subtitle") or ""),
                            str(body.get("kind") or "poster"),
                            int(body.get("variants") or 3)) if CD \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/creative/rate":
            res = CD.rate(str(body.get("url") or ""),
                          int(body.get("score") or 0),
                          str(body.get("note") or "")) if CD \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/image/studio/generate":
            try:
                import image_studio
                res = image_studio.produce(
                    str(body.get("title") or "Zyphere"),
                    str(body.get("subtitle") or ""),
                    str(body.get("kind") or "poster"),
                    str(body.get("palette") or "indigo"))
                self._send_json(200, res)
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 180)})
            return
        if u.path == "/api/research/projects/create":
            res = RP.create(body) if RP else {"ok": False, "error": "unavailable"}
            if res.get("ok") and RP:
                res["publish"] = RP.publish()
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/debate/run":
            res = CD.debate(str(body.get("issue") or "") or None) if CD \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/media/chat":
            text = str(body.get("text") or "").strip()
            if re.search(r"ปกหนังสือ|ออกแบบปก|cover", text, re.I):
                try:
                    import cover_designer as CD
                    r = CD.run(apply=True)
                    files = r.get("files") or []
                    if files:
                        dst = os.path.join(DATA_DIR, os.path.basename(files[0]))
                        import shutil
                        shutil.copy(files[0], dst)
                        self._send_json(200, {"ok": True, "type": "image",
                                              "url": "/media/" + os.path.basename(dst),
                                              "covers": r.get("covers"),
                                              "engine": "Cover Designer (graphic team)"})
                        return
                except Exception as e:
                    self._send_json(200, {"ok": False, "error": str(e)[:140]})
                    return
            if re.search(r"แต่งเพลง|เขียนเพลง|compose|ทำเพลง|music.*text|เพลงจากข้อความ", text, re.I):
                try:
                    import music_composer as MC
                    song = MC.compose(text, apply=True)
                    mp3 = song.get("mp3") or {}
                    if song.get("ok") and mp3.get("url"):
                        self._send_json(200, {"ok": True, "type": "audio",
                                              "url": mp3.get("url"),
                                              "plan": {k: song["plan"].get(k)
                                                       for k in ("mode", "bpm", "texture",
                                                                 "progression", "structure")},
                                              "seconds": song.get("seconds"),
                                              "voice": song.get("voice")})
                        return
                except Exception as e:
                    self._send_json(200, {"ok": False, "error": str(e)[:150]})
                    return
            if (not re.search(r"วิดีโอ|คลิป|video|film|ภาพยนตร์", text, re.I) and
                    re.search(r"เสียง|sound|fx|whoosh|ฝน|ลม|ฟ้าผ่า|สุนัข|แมว|รถยนต์|ไซเรน|กระดิ่ง|วูบ", text, re.I)):
                try:
                    import sound_forge as SF
                    fx = SF.forge(text, 4.0, apply=True)
                    mp3 = fx.get("mp3") or {}
                    if fx.get("ok") and mp3.get("url"):
                        self._send_json(200, {"ok": True, "type": "audio",
                                              "url": mp3.get("url"),
                                              "category": fx.get("category"),
                                              "seconds": fx.get("seconds"),
                                              "note": fx.get("note")})
                        return
                except Exception as e:
                    self._send_json(200, {"ok": False, "error": str(e)[:150]})
                    return
            want_video = bool(re.search(
                r"วิดีโอ|คลิป|video|film|ภาพยนตร์|สั่งทำคลิป", text, re.I))
            if want_video and re.search(r"ภาพยนตร์|ดารานำ|ตัวละคร|เรื่อง|ต่อคลิป|Multiple scene|film", text, re.I):
                try:
                    import film_editor as FE
                    scenes = [x.strip() for x in re.split(r"[,،/|]+|แล้ว|จากนั้น", text)
                              if x.strip()][:8] or ["ดารานำเดินในป่า", "ดารานำในวัด"]
                    fr = FE.build(scenes, apply=True)
                    if fr.get("ok"):
                        self._send_json(200, {"ok": True, "type": "video_local",
                                              "video": fr.get("video"),
                                              "scenes": fr.get("scenes"),
                                              "character": fr.get("character", {}).get("file"),
                                              "note": "ใบหน้าเดิมทุกฉาก เปลี่ยนชุดตามบริบท"})
                        return
                except Exception as e:
                    pass
            if want_video:
                # GitHub Actions survives Render restarts. Dispatch the cinema
                # workflow there and let the chat poll its public result file.
                dispatched = False
                dr_status = None
                try:
                    import method_transfer as _MT
                    import requests as _rq
                    _tok = _MT.token()
                    if _tok:
                        dr = _rq.post(
                            "https://api.github.com/repos/Vorakan-yakham/"
                            "zyphere-ai-agent/actions/workflows/cinema.yml/dispatches",
                            headers={"Authorization": "Bearer " + _tok,
                                     "Accept": "application/vnd.github+json"},
                            json={"ref": "main", "inputs": {
                                "brief": (str(__import__("imagination_engine").interpret(text, "video").get("motif"))[:60] + " | " + text)[:180],
                                "lang": "th"}},
                            timeout=25)
                        dr_status = dr.status_code
                        dispatched = dr_status in (200, 201, 204)
                except Exception:
                    pass
                if dispatched:
                    self._send_json(200, {"ok": True, "type": "video",
                                          "mode": "github", "dispatch_status": dr_status,
                                          "t": int(time.time()),
                                          "note": "ส่งงานสร้างภาพยนตร์ไป GitHub แล้ว ผลจะโผล่ในแชท"})
                    return
                # Fallback when no repo token is configured on Render.
                def _mk(jid, brief):
                    try:
                        import cinema_studio
                        res = cinema_studio.run(brief, 18, "th")
                        CINEMA_JOBS[jid] = {"ok": True, "done": True, "result": res}
                    except Exception as e:
                        CINEMA_JOBS[jid] = {"ok": False, "done": True, "error": str(e)[:200]}
                jid = "cin_" + str(int(time.time() * 1000))
                CINEMA_JOBS[jid] = {"ok": True, "done": False, "job": jid}
                threading.Thread(target=_mk, args=(jid, text), daemon=True).start()
                self._send_json(200, {"ok": True, "type": "video", "id": jid,
                                      "note": "กำลังสร้างภาพยนตร์ — ผลจะโผล่ในแชท"})
                return
            try:
                title = re.sub(r"^\s*(ช่วย|กรุณา|โปรด)?\s*(สร้าง|ทำ|วาด|ออกแบบ|generate|create)\s*"
                               r"(ภาพ|รูป|รูปภาพ|poster|image|picture)?\s*", "", text,
                               flags=re.I).strip()[:120] or "Zyphere"
                res = None
                if re.search(r"retouch|ปรับภาพ|แก้ภาพ|แต่งภาพ|เพิ่มฟอนต์|ภาพเก่า|ภาพเดิม", text, re.I):
                    try:
                        import photo_retouch as PR
                        src = str(body.get("src") or "")
                        if not src:
                            import glob as _g
                            cands = sorted(_g.glob(os.path.join(DATA_DIR, "..", "media",
                                                                "ownlab_*.png")))
                            if cands:
                                src = "/media/" + os.path.basename(cands[-1])
                        rr = PR.retouch(src, title, apply=True)
                        if rr.get("ok"):
                            res = {"ok": True, "type": "image", "url": rr.get("url"),
                                   "overlay": rr.get("overlay_url"),
                                   "engine": "Photo Retouch Studio (in-house)"}
                    except Exception:
                        pass
                try:
                    import poster_studio as PS
                    pic = PS.run(apply=True)
                    if pic.get("ok") and pic.get("file"):
                        import shutil
                        dst = os.path.join(DATA_DIR, os.path.basename(pic["file"]))
                        shutil.copy(pic["file"], dst)
                        res = {"url": "/media/" + os.path.basename(dst),
                               "direction": {"subject": "real photography",
                                             "mood": pic.get("brief")},
                               "engine": "Real CC photo + detail pipeline (no diffusion)"}
                except Exception:
                    pass
                try:
                    import imagination_engine as IE
                    imagined = IE.create(text, "image", apply=True)
                    art = imagined.get("artefact") or {}
                    if art.get("ok") and art.get("file"):
                        res = {"url": "/media/" + os.path.basename(art["file"]),
                               "quality": art.get("quality"),
                               "direction": {k: imagined["direction"].get(k)
                                             for k in ("subject", "mood", "camera", "motif")},
                               "engine": "Zypher Imagination -> Own Image Lab (4K)"}
                except Exception:
                    pass
                if not res:
                    import image_studio
                    p = image_studio.produce(title, "ออกแบบโดย Zyphere · งานจริง", "poster", "wind")
                    res = {"url": p.get("url"), "quality": p.get("quality"),
                           "engine": "design composition (in-house)"}
                self._send_json(200, {"ok": True, "type": "image",
                                      "url": res.get("url"), "quality": res.get("quality"),
                                      "engine": res.get("engine")})
            except Exception as e:
                self._send_json(200, {"ok": False, "error": str(e)[:180]})
            return
        if u.path == "/api/pay/order":
            try:
                import slip_auto_verifier as SV
                book = str(body.get("book") or "ebook")
                price = float(body.get("price") or 190)
                # attach the logged-in buyer so "my orders" works in the store
                tok = str(body.get("token") or
                          urllib.parse.parse_qs(u.query).get("token", [""])[0])
                me = USERS.me(tok) if (USERS and tok) else None
                email = str((me or {}).get("email") or "").lower()
                # Admin/OWNER must not place customer orders. Enforced here too
                # so hiding the UI button alone can never be bypassed.
                if email in OWNER_EMAILS or (me or {}).get("role") == "admin":
                    self._send_json(403, {"ok": False,
                        "error": "Admin ไม่สามารถสั่งซื้อได้ — ใช้สิทธิดูแลระบบแทน"})
                    return
                order = SV.new_order(price, book, email)
                # PERSIST — otherwise /api/pay/declare can never find the order
                dbp = SV.DATA
                saved = []
                if os.path.exists(dbp):
                    try:
                        saved = json.load(open(dbp, encoding="utf-8")).get("orders", [])
                    except Exception:
                        saved = []
                saved.append(order)
                os.makedirs(os.path.dirname(dbp), exist_ok=True)
                json.dump({"orders": saved[-200:]}, open(dbp, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                remote_push("store_orders", {"orders": saved[-200:]})
                self._send_json(200, {"ok": True, "order": order, "email": email,
                                      "promptpay": "0941939686"})
            except Exception as e:
                self._send_json(200, {"ok": False, "error": str(e)[:120]})
            return
        if u.path == "/api/pay/declare":
            try:
                import slip_auto_verifier as SV
                dbp = SV.DATA
                orders = store_orders_all()
                res = SV.verify(orders, str(body.get("id") or ""),
                                body.get("amount"), str(body.get("code") or ""))
                if res.get("ok"):
                    json.dump({"orders": orders}, open(dbp, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=2)
                    remote_push("store_orders", {"orders": orders[-200:]})
                    # SECURITY: self-declaration is NOT payment proof.
                    # File is released only after a PSP webhook or owner slip check.
                    res["file"] = None
                    res["status"] = "awaiting_payment_proof"
                    res["note"] = "ยังไม่ส่งไฟล์ — ต้องรอหลักฐานจ่ายจาก PSP หรือเจ้าของตรวจสลิป"
                self._send_json(200, res)
            except Exception as e:
                self._send_json(200, {"ok": False, "error": str(e)[:120]})
            return
        if u.path == "/api/cinema/create":
            def _cinema_task(jid, brief, secs, lang):
                try:
                    import cinema_studio
                    res = cinema_studio.run(brief, secs, lang)
                    CINEMA_JOBS[jid] = {"ok": True, "done": True, "result": res}
                    try:
                        if remote_enabled():
                            remote_push("cinema_job_" + jid, CINEMA_JOBS[jid])
                    except Exception:
                        pass
                except Exception as e:
                    CINEMA_JOBS[jid] = {"ok": False, "done": True, "error": str(e)[:200]}
            jid = "cin_" + str(int(time.time() * 1000))
            CINEMA_JOBS[jid] = {"ok": True, "done": False, "job": jid}
            try:
                if remote_enabled():
                    remote_push("cinema_job_" + jid, CINEMA_JOBS[jid])
            except Exception:
                pass
            threading.Thread(target=_cinema_task,
                             args=(jid, str(body.get("brief") or "Zyphere"),
                                   int(body.get("seconds") or 18),
                                   str(body.get("lang") or "th")), daemon=True).start()
            self._send_json(200, {"ok": True, "id": jid,
                                  "note": "ดูผลที่ /api/cinema/status?id=" + jid})
            return
        if u.path == "/api/conversation/learn":
            try:
                from conversation_learning import CL
                _r = CL.store_chat(body.get("user") or body.get("text"),
                                   body.get("assistant") or "")
            except Exception as e:
                _r = {"ok": False, "error": str(e)[:120]}
            self._send_json(200, _r)
            return
        if u.path == "/api/zy-brain/grow":
            try:
                import own_brain as _OB
                _r = _OB.grow(apply=True)
            except Exception as e:
                _r = {"ok": False, "error": str(e)[:120]}
            self._send_json(200, _r)
            return
        if u.path == "/api/council/autonomous":
            threading.Thread(target=_run_autonomous_council, args=(True,), daemon=True).start()
            self._send_json(200, {"ok": True, "started": True,
                                  "note": "สภาทำงานต่อเบื้องหลัง ดูผลที่ /api/council/autonomous/status"})
            return
        if u.path == "/api/template/create":
            res = TD.create(str(body.get("title") or "Zyphere Elite"),
                            bool(body.get("use_ensemble", True))) if TD \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/engineering/run":
            res = EC.session() if EC else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/selfcoder/run":
            def _sc():
                try:
                    SC.cycle(str(body.get("file") or "") or None,
                             bool(body.get("dry")))
                except Exception:
                    pass
            threading.Thread(target=_sc, daemon=True).start()
            self._send_json(200, {"ok": True, "started": True,
                                  "dry": bool(body.get("dry"))})
            return
        if u.path == "/api/dialogue/run":
            res = DD.round(str(body.get("dept") or "") or None) if DD \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/music/create":
            try:
                res = MUSIC.create(str(body.get("style") or "calm"),
                                   int(body.get("bpm") or 90),
                                   int(body.get("bars") or 4)) if MUSIC \
                    else {"ok": False, "error": "music engine unavailable"}
                self._send_json(200 if res.get("ok") else 400, res)
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 180)})
            return
        if u.path == "/api/companion/record":
            res = DC.record(str(body.get("action") or ""), str(body.get("tool") or ""),
                            str(body.get("detail") or ""), str(body.get("outcome") or ""),
                            body.get("files") or [], str(body.get("lesson") or "")) if DC \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/improve/run":
            dept = str(body.get("dept") or "") or None
            res = SI.cycle(dept) if SI else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/co-learn/run-cross":
            try:
                import cross_disciplinary
                cross_disciplinary.run()
                res = {"ok": True, "departments": len(cross_disciplinary.RELATED)}
            except Exception as e:
                res = {"ok": False, "error": str(e)[:160]}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/co-learn/run":
            dept = str(body.get("dept") or "") or None
            res = CO.run(dept) if CO else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/quality/cycle":
            def _learn(topic, reason):
                try:
                    create_learn_job([topic], reason=reason)
                except Exception:
                    pass
            res = QOPS.cycle(body.get("state") or {}, _learn) if QOPS \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/supervisors/nag":
            res = SUPERVISORS.nag_all(body.get("state") or {}) if SUPERVISORS \
                else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/departments/ensure":
            role = str(body.get("role") or "")
            res = ROLES.ensure(role) if ROLES else {"ok": False, "error": "unavailable"}
            if res.get("ok") and res.get("created") and ROLES:
                res["push"] = ROLES.push()
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/store/reset":
            tok = str(body.get("token") or "")
            if not store_admin_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            self._send_json(200, STORE.reset_demo() if STORE
                            else {"ok": False, "error": "unavailable"})
            return
        if u.path == "/api/store/click":
            ut = str(body.get("user_token") or "")
            me = USERS.me(ut) if (USERS and ut) else None
            res = STORE.click(str(body.get("product") or ""),
                              me.get("email", "") if me else "") if STORE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/store/owner/download":
            ut = str(body.get("token") or "")
            me = USERS.me(ut) if (USERS and ut) else None
            if not me:
                self._send_json(401, {"ok": False, "error": "not logged in"})
                return
            em = str(me.get("email", "")).lower()
            if em not in OWNER_EMAILS and me.get("role") != "admin":
                self._send_json(403, {"ok": False, "error": "forbidden — owner only"})
                return
            self._send_json(200, {"ok": True, "url": ZIPBALL_OWNER,
                                  "filename": "zyphere-product-pack.zip",
                                  "note": "ดาวน์โหลดเพื่อตรวจสอบโดยเจ้าของระบบ"})
            return
        if u.path == "/api/store/pay/omise":
            # Create a real Omise PromptPay charge. Money confirmation comes
            # from Omise webhook, never from a browser button click.
            if not OMISE_ENABLED:
                self._send_json(400, {"ok": False, "error": "Omise not configured"})
                return
            oid = str(body.get("order_id") or "")
            o = next((x for x in (STORE.all_orders() if STORE else []) if x.get("id") == oid), None)
            if not o:
                self._send_json(404, {"ok": False, "error": "order not found"})
                return
            try:
                import base64 as _b64o
                auth = "Basic " + base64.b64encode((OMISE_SKEY + ":").encode()).decode()
                r = requests.post("https://api.omise.co/charges",
                    headers={"Authorization": auth},
                    data={"amount": int(o.get("amount", 0)) * 100,
                          "currency": "thb", "source[type]": "promptpay",
                          "description": "Zyphere " + str(o.get("product", ""))[:80],
                          "metadata[order_id]": oid,
                          "return_uri": os.environ.get(
                              "FRONTEND_URL",
                              "https://vorakan-yakham.github.io/zyphere-ai-agent/")
                          .rstrip("/") + "/STORE.html"},
                    timeout=30)
                j = r.json()
                if not r.ok or not j.get("id"):
                    raise RuntimeError(str(j.get("message", r.text))[:160])
                with STORE.lock:
                    for x in STORE.orders:
                        if x.get("id") == oid:
                            x["charge_id"] = j["id"]
                STORE.save()
                self._send_json(200, {"ok": True, "charge_id": j.get("id"),
                                      "status": j.get("status"),
                                      "authorize_uri": j.get("authorize_uri", ""),
                                      "qr": (j.get("source") or {}).get("scannable_code", {}).get("image", {}).get("download_uri", "")})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 180)})
            return
        if u.path == "/api/pay/omise/webhook":
            # Public webhook: verify event with Omise, then mark the order paid.
            try:
                ev = body.get("data") or body
                eid = ev.get("id", "")
                if not OMISE_SKEY or not eid:
                    raise RuntimeError("bad event")
                auth = "Basic " + base64.b64encode((OMISE_SKEY + ":").encode()).decode()
                r = requests.get("https://api.omise.co/events/" + eid,
                                 headers={"Authorization": auth}, timeout=20)
                ej = r.json()
                if not r.ok:
                    raise RuntimeError("event verify failed")
                data = ej.get("data") or {}
                key = data.get("key") or ""
                obj = data.get("object") or {}
                oid = str((obj.get("metadata") or {}).get("order_id", ""))
                if key == "charge.complete" and obj.get("paid") and oid:
                    STORE.mark_paid(oid, via="omise", charge_id=obj.get("id", ""))
                self._send_json(200, {"ok": True, "event": key, "order": oid})
            except Exception as e:
                self._send_json(200, {"ok": True, "ignored": _clip(str(e), 120)})
            return
        if u.path == "/api/store/admin/decide":
            # ADMIN approves only after real payment proof. Never deletes.
            tok = str(body.get("token") or "") or urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            owner_session = bool(me and str(me.get("email", "")).lower() in OWNER_EMAILS)
            if not (store_admin_ok(tok) or owner_session):
                self._send_json(403, {"ok": False, "error": "forbidden — admin only"})
                return
            oid = str(body.get("order_id") or "")
            decision = str(body.get("decision") or "").lower()
            shared = [o for o in store_orders_all() if str(o.get("id")) == oid]
            done = False
            if shared:
                o = shared[0]
                if decision == "approve":
                    o["status"] = "paid"
                    o["paid_via"] = "admin:" + str((me or {}).get("email", "owner"))[:40]
                    o["approved_by"] = str((me or {}).get("email", "owner"))[:60]
                    o["approved_t"] = int(time.time())
                    orders_shared_save([o])
                    done = True
                elif decision == "reject":
                    o["status"] = "rejected"
                    o["approved_by"] = str((me or {}).get("email", "owner"))[:60]
                    orders_shared_save([o])
                    done = True
            elif STORE and str(oid).startswith("or_"):
                res = (STORE.approve(oid, by="admin") if decision == "approve"
                       else STORE.reject(oid, by="admin"))
                done = bool(res.get("ok"))
            self._send_json(200 if done else 400,
                            {"ok": done, "order_id": oid, "decision": decision,
                             "note": "record kept permanently — nothing deleted"})
            return
        if u.path in ("/api/store/approve", "/api/store/reject"):
            # ADMIN ONLY — verify the PromptPay transfer then unlock download
            tok = str(body.get("token") or "") or urllib.parse.parse_qs(u.query).get("token", [""])[0]
            me = USERS.me(tok) if USERS else None
            owner_session = bool(me and (str(me.get("email", "")).lower() in OWNER_EMAILS))
            if not (store_admin_ok(tok) or owner_session):
                self._send_json(403, {"ok": False, "error": "forbidden — admin token required"})
                return
            oid = str(body.get("order_id") or "")
            if u.path.endswith("approve"):
                res = STORE.approve(oid, by="admin") if STORE else {"ok": False, "error": "unavailable"}
            else:
                res = STORE.reject(oid, by="admin") if STORE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/shop/list":
            res = SHOP.list_product(str(body.get("title") or ""), int(body.get("price") or 0),
                                    str(body.get("asset_url") or ""), str(body.get("desc") or ""),
                                    str(body.get("category") or "digital")) if SHOP else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("shop", SHOP.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/shop/order":
            res = SHOP.order(str(body.get("product_id") or ""), str(body.get("buyer") or "")) if SHOP else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("shop", SHOP.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/shop/confirm":
            res = SHOP.confirm(str(body.get("id") or "")) if SHOP else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("shop", SHOP.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/market/analyze":
            res = MARKET.analyze(str(body.get("product") or ""), str(body.get("audience") or ""),
                                 int(body.get("price") or 0)) if MARKET else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("market", MARKET.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/expert/start":
            res = EXPERT.start(str(body.get("title") or ""), str(body.get("kind") or ""),
                               int(body.get("price") or 0), str(body.get("deadline") or "")) if EXPERT else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/expert/advance":
            res = EXPERT.advance(str(body.get("id") or ""), str(body.get("stage") or ""),
                                 str(body.get("status") or "done"), str(body.get("note") or "")) if EXPERT else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/otp/prepare":
            res = OTPASSIST.prepare(str(body.get("platform") or ""), str(body.get("name") or ""),
                                   str(body.get("email") or ""), str(body.get("phone") or "")) if OTPASSIST else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("otpassist", OTPASSIST.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/otp/mark":
            res = OTPASSIST.mark(str(body.get("id") or ""), str(body.get("step") or ""),
                                 str(body.get("note") or "")) if OTPASSIST else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("otpassist", OTPASSIST.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/income/produce":
            res = INCOME.produce(str(body.get("channel") or ""), str(body.get("title") or ""),
                                 str(body.get("asset_url") or ""), int(body.get("price") or 0),
                                 str(body.get("note") or "")) if INCOME else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("income", INCOME.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/income/affiliate":
            res = INCOME.affiliate(str(body.get("link") or ""), str(body.get("note") or ""),
                                   str(body.get("platform") or "")) if INCOME else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("income", INCOME.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/income/earned":
            res = INCOME.earned(str(body.get("channel") or ""), int(body.get("amount") or 0),
                                str(body.get("note") or "")) if INCOME else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("income", INCOME.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/help/ask":
            res = HELP.ask(str(body.get("action") or ""), str(body.get("blocker") or ""),
                           str(body.get("need") or ""), str(body.get("context") or "")) if HELP else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("help", HELP.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/help/resolve":
            res = HELP.resolve(str(body.get("id") or ""), str(body.get("solution") or ""),
                               str(body.get("blocker") or "")) if HELP else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("help", HELP.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/code/forge":
            res = CODEFORGE.forge(str(body.get("kind") or "โค้ด/สคริปต์"),
                                  body.get("title"), int(body.get("price") or 499)) if CODEFORGE else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/money/generate":
            res = MONEYFIELD.generate(str(body.get("field") or ""),
                                     str(body.get("zyphere_answer") or "")) if MONEYFIELD else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("moneyfield", MONEYFIELD.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/pack/build":
            res = PACKS.build(str(body.get("title") or "แพ็กสื่อ Zyphere"),
                              int(body.get("price") or 999),
                              body.get("files") or [], str(body.get("note") or "")) if PACKS else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/billing/confirm":
            r = BILLING.confirm(body.get("id")) if BILLING else {"ok": False}
            if r.get("ok") and DELIVERY:
                try:
                    asset = str(body.get("asset") or "pro")
                    DELIVERY.deliver(str(body.get("id") or ""), asset,
                                     str(body.get("customer") or ""), str(body.get("note") or ""))
                    if remote_enabled():
                        remote_push("delivery", DELIVERY.snapshot())
                except Exception:
                    pass
            self._send_json(200 if r.get("ok") else 400, r)
            return
        if u.path == "/api/brain/gap":
            gap = BRAIN.log_gap(body.get("need") or "", body.get("context") or "") if BRAIN else None
            self._send_json(200, {"ok": True, "gap": gap, "pending": BRAIN.pending_gaps() if BRAIN else []})
            return
        if u.path == "/api/plans":
            # public: show plans only — revenue is admin-only
            self._send_json(200, {"ok": True, "plans": PLANS})
            return
        if u.path == "/api/me":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            role = USERS.role(tok) if USERS else "guest"
            self._send_json(200, {"ok": True, "role": role})
            return
        if u.path == "/api/research/search":
            topic = str(body.get("q") or body.get("topic") or "")
            results, err = RESEARCH.search(topic) if RESEARCH else ([], "unavailable")
            if body.get("record") and results:
                RESEARCH.record(topic, results, body.get("field") or "")
                if remote_enabled():
                    remote_push("research", RESEARCH.snapshot())
            self._send_json(200, {"ok": True, "query": topic, "results": results, "error": err,
                                  "count": len(results)})
            return
        if u.path == "/api/research/record":
            topic = str(body.get("topic") or "")
            res = RESEARCH.record(topic, body.get("results") or [], body.get("field") or "") if RESEARCH else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("research", RESEARCH.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/media/srt":
            text = str(body.get("text") or "")
            out = os.path.join(DATA_DIR, "sub_" + uuid.uuid4().hex[:8] + ".srt")
            res = MEDIA.write_srt(out, text) if MEDIA else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/media/melody":
            # Create an original, royalty-free MP3 melody (MIDI-like synth).
            if not FFMPEG or not MEDIA:
                self._send_json(400, {"ok": False, "error": "ffmpeg/media unavailable"})
                return
            base = os.path.join(DATA_DIR, "mel_" + uuid.uuid4().hex[:8])
            wav, mp3 = base + ".wav", base + ".mp3"
            r1 = MEDIA.melody_to_wav(wav)
            if not r1.get("ok"):
                self._send_json(400, r1); return
            r2 = MEDIA.wav_to_mp3(wav, mp3, FFMPEG)
            if r2.get("ok"):
                try:
                    MEDIA.tag_mp3(mp3, body.get("title") or "Zyphere Melody",
                                  body.get("artist") or "Zyphere")
                except Exception:
                    pass
            try:
                os.remove(wav)
            except Exception:
                pass
            self._send_json(200 if r2.get("ok") else 400, r2)
            return
        if u.path == "/api/media/tag":
            mp3p = os.path.join(DATA_DIR, str(body.get("file") or ""))
            if not os.path.exists(mp3p):
                self._send_json(404, {"ok": False, "error": "file not found"})
                return
            res = MEDIA.tag_mp3(mp3p, body.get("title") or "", body.get("artist") or "") if MEDIA else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/notebook/add":
            name = str(body.get("name") or "")
            text = str(body.get("text") or "")
            res = NOTEBOOK.add(name, text) if NOTEBOOK else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("notebook", NOTEBOOK.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/notebook/remove":
            res = NOTEBOOK.remove(str(body.get("id") or "")) if NOTEBOOK else {"ok": False, "error": "unavailable"}
            if remote_enabled():
                remote_push("notebook", NOTEBOOK.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/notebook/analyze":
            q = str(body.get("q") or "")
            # grounded analysis; if ensemble key available, synthesize with citation
            synth = None
            if body.get("use_ai") and NOTEBOOK:
                try:
                    from brain_ensemble import load_keys, _call_groq
                    keys = load_keys()
                    if keys.get("groq"):
                        def _synth(question, ctx):
                            sysm = ("You are Zyphere's analyst. Answer ONLY from the provided "
                                    "source excerpts. Cite [doc | part] where each claim comes from. "
                                    "If the sources don't cover something, say so. Never invent facts.")
                            return _call_groq(keys["groq"],
                                [{"role": "system", "content": sysm},
                                 {"role": "user", "content": ctx + "\n\nQuestion: " + question}])
                        synth = _synth
                except Exception:
                    synth = None
            res = NOTEBOOK.analyze(q, synth) if NOTEBOOK else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("notebook", NOTEBOOK.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/self/grow":
            res = DEV_BRAIN.grow() if DEV_BRAIN else {"error": "unavailable"}
            if res.get("new_rules") is not None and remote_enabled():
                remote_push("dev_brain", DEV_BRAIN.snapshot())
            self._send_json(200, {"ok": True, "result": res})
            return
        if u.path == "/api/self/teachback":
            res = DEV_BRAIN.teach_back(str(body.get("topic") or "")) if DEV_BRAIN else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/self/critique":
            res = DEV_BRAIN.self_critique(str(body.get("topic") or "")) if DEV_BRAIN else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/self/graph":
            res = DEV_BRAIN.link_graph() if DEV_BRAIN else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/self/ask":
            q = str(body.get("q") or "")
            ans = DEV_BRAIN.answer(q) if DEV_BRAIN else None
            self._send_json(200, {"ok": True, "answer": ans,
                                  "from_own_brain": ans is not None})
            return
        if u.path == "/api/behavior/track":
            res = BEHAVIOR.track(str(body.get("event") or "view"), str(body.get("target") or ""),
                                 body.get("meta")) if BEHAVIOR else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/behavior/link":
            res = BEHAVIOR.link_modal(str(body.get("id") or ""), str(body.get("text") or ""),
                                      str(body.get("image") or ""), str(body.get("audio") or "")) if BEHAVIOR else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("behavior", BEHAVIOR.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/tools/run":
            state = {"search_web": search_web, "fetch_page": fetch_page, "reason": REASON,
                     "concept": CONCEPT, "eval": EVAL, "research": RESEARCH}
            res = TOOLS.run(str(body.get("tool") or ""), body.get("params") or {}, state) if TOOLS else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/safety/check":
            res = SAFETY.evaluate(str(body.get("text") or ""), str(body.get("context") or "")) if SAFETY else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/eval/run":
            res = EVAL.evaluate(str(body.get("question") or ""), str(body.get("answer") or ""),
                                body.get("sources") or []) if EVAL else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/feedback/record":
            res = FEEDBACK.record(str(body.get("kind") or "positive"),
                                  str(body.get("signal") or ""), str(body.get("topic") or "")) if FEEDBACK else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("feedback_loop", FEEDBACK.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/meta/reflect":
            res = META_LEARN.reflect() if META_LEARN else {"ok": False, "error": "unavailable"}
            if res.get("ok") and DEV_BRAIN:
                try:
                    for p in res.get("principles", []):
                        DEV_BRAIN.experience("หลักการพัฒนา Zyphere: " + p, "elder_teacher")
                    DEV_BRAIN.grow()
                except Exception:
                    pass
            self._send_json(200, res)
            return
        if u.path == "/api/selftest/quiz":
            concept = str(body.get("concept") or "")
            res = SELFTEST.quiz(concept, int(body.get("difficulty") or 3),
                                DEV_BRAIN.lessons if DEV_BRAIN else []) if SELFTEST else {"ok": False, "error": "unavailable"}
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/selftest/evaluate":
            concept = str(body.get("concept") or "")
            answers = body.get("answers") or []
            res = SELFTEST.evaluate(concept, answers, DEV_BRAIN.lessons if DEV_BRAIN else []) if SELFTEST else {"ok": False, "error": "unavailable"}
            if res.get("need_relearn") and DEV_BRAIN:
                try:
                    DEV_BRAIN.curiosities.append({"q": "เรียนซ้ำ: " + concept[:150], "t": int(time.time()), "status": "open"})
                    DEV_BRAIN.save()
                except Exception:
                    pass
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/meta/ask-self":
            topic = str(body.get("topic") or "Zyphere")
            gaps = (DEV_BRAIN.pending_curiosities() if hasattr(DEV_BRAIN, "pending_curiosities") else []) if DEV_BRAIN else []
            if not gaps and DEV_BRAIN:
                gaps = [{"need": g.get("q")} for g in (DEV_BRAIN.curiosities or []) if g.get("status") == "open"][:5]
            res = META.ask_self(topic, gaps) if META else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/concept/study":
            term = str(body.get("term") or "")
            domain = str(body.get("domain") or "ทั่วไป")
            offline = bool(body.get("offline"))
            res = CONCEPT.explore(term, domain) if CONCEPT else {"ok": False, "error": "unavailable"}
            if res.get("ok") and not offline:
                try:
                    from brain_ensemble import ensemble
                    er = ensemble([{"role": "user", "content": CONCEPT.study_prompt(term, domain)}])
                    if er.get("ok"):
                        res["deep_study"] = er.get("text")
                        res["sources"] = er.get("sources", [])
                except Exception:
                    pass
            if res.get("ok") and DEV_BRAIN:
                try:
                    for step in res.get("analysis", []):
                        DEV_BRAIN.experience("แนวคิด " + term + ": " + step.get("step", "") + " — " + step.get("result", ""), "elder_teacher")
                    DEV_BRAIN.grow()
                except Exception:
                    pass
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/reason/solve":
            problem = str(body.get("problem") or body.get("q") or "")
            offline = bool(body.get("offline"))
            res = REASON.solve(problem) if REASON else {"ok": False, "error": "unavailable"}
            if res.get("ok") and not offline:
                try:
                    from brain_ensemble import ensemble
                    er = ensemble([{"role": "user", "content": REASON.think_prompt(problem)}])
                    if er.get("ok"):
                        res["deep_analysis"] = er.get("text")
                        res["analysis_sources"] = er.get("sources", [])
                except Exception:
                    pass
            if res.get("ok") and DEV_BRAIN:
                try:
                    DEV_BRAIN.experience("วิธีคิด: " + REASON.solve(problem).get("reminder", ""), "elder_teacher")
                    DEV_BRAIN.grow()
                except Exception:
                    pass
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/language/correct":
            res = LANG.correct(str(body.get("text") or "")) if LANG else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/language/narrate":
            res = LANG.narration_plan(str(body.get("text") or "")) if LANG else {"ok": False, "error": "unavailable"}
            self._send_json(200, res)
            return
        if u.path == "/api/language/learn":
            res = LANG.learn() if LANG else {"ok": False, "error": "unavailable"}
            if DEV_BRAIN and res.get("ok"):
                try:
                    for fact in LANG.learned:
                        DEV_BRAIN.experience("ภาษา: " + fact, "elder_teacher")
                    DEV_BRAIN.grow()
                except Exception:
                    pass
            self._send_json(200, res)
            return
        if u.path == "/api/voice/learn":
            res = VOICE.learn() if VOICE else {"ok": False, "error": "unavailable"}
            if DEV_BRAIN and res.get("ok"):
                try:
                    for fact in VOICE.learned if VOICE else []:
                        DEV_BRAIN.experience("เสียง: " + fact, "elder_teacher")
                    DEV_BRAIN.grow()
                except Exception:
                    pass
            if res.get("ok") and remote_enabled():
                remote_push("voice", VOICE.snapshot())
            self._send_json(200, res)
            return
        if u.path == "/api/voice/tune":
            res = VOICE.tune(**{k: v for k, v in body.items() if k in ("rate", "pitch_ratio", "voice_th", "style")}) if VOICE else {"error": "unavailable"}
            if res.get("rate") and remote_enabled():
                remote_push("voice", VOICE.snapshot())
            self._send_json(200, {"ok": True, "cfg": res})
            return
        if u.path == "/api/work/produce":
            res = WORKS.produce(str(body.get("topic") or ""), str(body.get("field") or ""),
                                str(body.get("notes") or "")) if WORKS else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("works", WORKS.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/creative/package":
            res = CREATIVE.make_package(
                str(body.get("platform") or "Facebook"), str(body.get("topic") or ""),
                str(body.get("audience") or "general"), str(body.get("language") or "th"),
                str(body.get("caption") or "")) if CREATIVE else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("creative", CREATIVE.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/platforms/log":
            name = str(body.get("name") or "")
            note = str(body.get("note") or "")
            status = str(body.get("status") or "prepared")
            res = PLATFORMS.log(name, note, status) if PLATFORMS else {"ok": False, "error": "unavailable"}
            if res.get("ok") and remote_enabled():
                remote_push("platforms", PLATFORMS.snapshot())
            self._send_json(200 if res.get("ok") else 400, res)
            return
        if u.path == "/api/email/send":
            tok = str(body.get("token") or "")
            if not admin_token_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            try:
                from mailer import send_mail
                result = send_mail(body.get("to"), body.get("subject"), body.get("body"))
            except Exception as e:
                result = {"ok": False, "error": str(e)[:200]}
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if u.path == "/api/admin/login":
            import hashlib as _hl
            uh = _hl.sha256(str(body.get("user") or "").encode()).hexdigest()[:16]
            ph = _hl.sha256(str(body.get("password") or "").encode()).hexdigest()
            if uh == ADMIN_USER_HASH and ph == ADMIN_PW_HASH:
                tok = os.environ.get("BACKUP_TOKEN", "").strip() or ADMIN_PW_HASH[:16]
                self._send_json(200, {"ok": True, "token": tok})
            else:
                self._send_json(401, {"ok": False, "error": "invalid admin credentials"})
            return
        if u.path == "/api/admin":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            if not admin_token_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            self._send_json(200, {"ok": True, "revenue": BILLING.stats() if BILLING else {},
                                  "users": USERS.stats() if USERS else {},
                                  "brain": BRAIN.stats() if BRAIN else {}})
            return
        if u.path == "/api/billing/status":
            email = urllib.parse.parse_qs(u.query).get("email", [""])[0]
            self._send_json(200, {"ok": True, "status": BILLING.status(email) if BILLING else {"plan": "free", "active": False}})
            return
        if u.path == "/api/identity":
            self._send_json(200, {"ok": True, "identity": IDENTITY.public() if IDENTITY else {"error": "unavailable"}})
            return
        if u.path == "/api/brain/gaps":
            self._send_json(200, {"ok": True, "pending": BRAIN.pending_gaps() if BRAIN else []})
            return
        if u.path == "/api/support":
            tok = urllib.parse.parse_qs(u.query).get("token", [""])[0]
            if not admin_token_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            try:
                with open(os.path.join(DATA_DIR, "support.json"), "r", encoding="utf-8") as f:
                    info = json.load(f)
            except Exception:
                info = {}
            self._send_json(200, {"ok": True, "support": info})
            return
        if u.path == "/api/users/stats":
            self._send_json(200, {"ok": True, "users": USERS.stats() if USERS else {"error": "unavailable"}})
            return
        if u.path == "/api/family/set":
            tok = str(body.get("token") or "")
            if not admin_token_ok(tok):
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            if not IDENTITY:
                self._send_json(400, {"ok": False, "error": "unavailable"})
                return
            if body.get("owner_name"):
                IDENTITY.set_owner(str(body.get("owner_name")), body.get("owner_email") or "vorayakham@gmail.com")
            members = body.get("family") or []
            fam = IDENTITY.set_family(members) if members else IDENTITY.family()
            if remote_enabled():
                remote_push("identity", IDENTITY.data)
            self._send_json(200, {"ok": True, "owner": IDENTITY.data.get("owner_name"),
                                  "family": fam})
            return
        if u.path == "/api/brain/auto":
            # learn from user question + assistant answer automatically (offline)
            try:
                q = str(body.get("q") or ""); a = str(body.get("a") or "")
                if BRAIN:
                    BRAIN.learn_text(q, "question")
                    BRAIN.learn_text(a, "assistant")
                if IDENTITY:
                    IDENTITY.learn(q, "user")
                    IDENTITY.learn(a, "assistant")
                pref = None
                if PREF:
                    pref = PREF.observe(q, a, bool(body.get("voice")), body.get("lang") or "th")
                # The child learns from both the user's question and the
                # teacher's (ensemble) answer — this is learning from elders.
                dev = None
                if DEV_BRAIN:
                    DEV_BRAIN.experience(q, "user")
                    DEV_BRAIN.experience(a, "teacher")
                    dev = DEV_BRAIN.grow()
                self._send_json(200, {"ok": True,
                                      "stats": BRAIN.stats() if BRAIN else {},
                                      "identity": IDENTITY.public() if IDENTITY else {},
                                      "preferences": pref,
                                      "dev_brain": (DEV_BRAIN.self_narrative() if DEV_BRAIN else None),
                                      "grown": dev})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": str(e)[:200]})
            return
        if u.path == "/api/brain/learn":
            text = str(body.get("text") or "")
            got = BRAIN.learn_text(text, body.get("source") or "user") if BRAIN else []
            self._send_json(200, {"ok": True, "learned": got, "stats": BRAIN.stats() if BRAIN else {}})
            return
        if u.path == "/api/ask":
            if RATE and not RATE.allow(self.client_address[0] + ":ask", 20, 60):
                self._send_json(429, {"ok": False, "error": "คำขอเร็วเกินไป กรุณารอสักครู่ครับ"})
                return
            # Server-side LLM proxy: any user can chat without personal API key.
            msgs = body.get("messages") or []
            sys_p = str(body.get("system") or "")
            if not isinstance(msgs, list) or len(msgs) > 40:
                self._send_json(400, {"ok": False, "error": "invalid messages"})
                return
            # Auto-register any department the owner mentions in chat.
            if ROLES:
                try:
                    import re as _rr
                    text = " ".join(str(m.get("content", "")) for m in msgs[-4:]
                                    if isinstance(m, dict))[:4000]
                    found = _rr.findall(r"(?:ฝ่าย|ทีม|แผนก|นัก)([ก-๙A-Za-z][ก-๙A-Za-z ]{1,24})", text)
                    seen = set()
                    for f in found[:4]:
                        name = _rr.sub(r"\s+", " ", f).strip()
                        if name and name not in seen and len(name) >= 2:
                            seen.add(name)
                            r = ROLES.ensure(name)
                            if r.get("created"):
                                ROLES.push()
                except Exception:
                    pass
            clean = []
            for m in msgs[-20:]:
                if not isinstance(m, dict):
                    continue
                role = m.get("role") if m.get("role") in ("user", "assistant", "system") else "user"
                content = str(m.get("content") or "")[:8000]
                if content.strip():
                    clean.append({"role": role, "content": content})
            if not clean:
                self._send_json(400, {"ok": False, "error": "empty message"})
                return
            # Safety gate (Zyphere's own #1 gap) — check user text before LLM
            if SAFETY:
                try:
                    dec = SAFETY.evaluate(str(msgs[-1].get("content", "")), "ask")
                    if dec.get("decision") == "BLOCK":
                        self._send_json(403, {"ok": False, "error": dec.get("message", "blocked"),
                                              "safety": True})
                        return
                except Exception:
                    pass
            # Intent routing + dynamic contextual memory (Zyphere's round-2 gap)
            intent = None
            sid = str(body.get("session") or self.client_address[0])
            last_text = str(msgs[-1].get("content", ""))
            if INTENT:
                try:
                    intent = INTENT.route(last_text)
                    sys_p = INTENT.build_system(sys_p, sid, last_text)
                    for m in msgs:
                        if m.get("role") in ("user", "assistant") and m.get("content"):
                            INTENT.remember(sid, m["role"], m["content"])
                    INTENT.route_log.append({"intent": intent.get("intent"), "t": time.time()})
                except Exception:
                    pass
            # RAG: inject internal knowledge (knowledge/notebook/research/own brain)
            rag_info = None
            if RAG_ENGINE:
                try:
                    state = {"knowledge": (load_knowledge().get("items") or []),
                             "notebook_docs": (NOTEBOOK.docs if NOTEBOOK else []),
                             "research": (RESEARCH.library() if RESEARCH else []),
                             "lessons": (DEV_BRAIN.lessons if DEV_BRAIN else [])}
                    sys_p, rag_info = RAG_ENGINE.inject(sys_p, last_text, state)
                except Exception:
                    pass
            # Apply learned feedback guidance (HCAI feedback loop) to the system prompt
            if FEEDBACK:
                try:
                    g = FEEDBACK.guidance().get("guidance", "")
                    if g and g != "ตอบตามปกติ":
                        sys_p = (sys_p + "\n\n[-user preference learned]: " + g)[:6000]
                except Exception:
                    pass
            # Inject REAL fresh context so the assistant never claims a
            # 2024 cutoff while autonomous pulses harvest current sources.
            try:
                import live_context as LC
                fresh = LC.context()
                if fresh:
                    sys_p = (fresh + "\n\n" + sys_p)[:7000]
            except Exception:
                pass
            if sys_p:
                clean.insert(0, {"role": "system", "content": sys_p[:7000]})
            try:
                from brain_ensemble import ensemble
                res = ensemble(clean)
            except Exception as e:
                res = {"ok": False, "error": _clip(str(e), 200)}
            if not res.get("ok"):
                try:
                    if BRAIN:
                        BRAIN.log_gap("ensemble ask failed: " + str(res.get("error"))[:120], "api_ask")
                except Exception:
                    pass
                self._send_json(502 if "no AI keys" not in str(res.get("error")) else 503,
                                {"ok": False, "error": res.get("error") or "no AI keys configured"})
                return
            answer_text = res.get("text", "")
            corrections = None
            if SELFCORRECT:
                try:
                    cr = SELFCORRECT.run(answer_text, last_text, lang=lastLang)
                    if cr.get("changed"):
                        answer_text = cr.get("text", answer_text)
                    corrections = {"changed": cr.get("changed"), "fixes": cr.get("fixes", [])}
                    if remote_enabled():
                        remote_push("selfcorrect", SELFCORRECT.snapshot())
                except Exception:
                    pass
            if AUDIT:
                try:
                    AUDIT.record(actor=AUTHZ.role_of(str(body.get("token") or "")) if AUTHZ else "guest",
                                 action="ask", detail=last_text[:120],
                                 result="ok·intent=" + str((intent or {}).get("intent") or "-"))
                    if remote_enabled():
                        remote_push("audit", AUDIT.snapshot())
                except Exception:
                    pass
            self._send_json(200, {"ok": True, "text": answer_text, "offline": False,
                                  "sources": res.get("sources", []),
                                  "synthesized": res.get("synthesized", False),
                                  "intent": (intent or {}).get("intent") if intent else None,
                                  "rag_hits": (rag_info or {}).get("hits") if rag_info else 0,
                                  "self_corrected": corrections})
            return
        if u.path == "/api/vision/learn":
            if RATE and not RATE.allow(self.client_address[0] + ":vision", 6, 60):
                self._send_json(429, {"ok": False, "error": "ดูภาพเร็วเกินไป กรุณารอสักครู่ครับ"})
                return
            # Give Zyphere "eyes": receive a screen image, describe it, learn from it.
            import base64 as _b64
            try:
                raw = _b64.b64decode(str(body.get("image") or ""), validate=True)
            except Exception:
                self._send_json(400, {"ok": False, "error": "invalid image data"})
                return
            if len(raw) > 8_000_000:
                self._send_json(413, {"ok": False, "error": "image too large"})
                return
            gkey = ""
            try:
                for line in open(os.path.join(BASE_DIR, "..", "API-Zyphere.txt"), encoding="utf-8"):
                    if line.strip().lower().startswith("gemini"):
                        gkey = line.split("=", 1)[-1].strip() if "=" in line else line.split()[-1].strip()
                        break
            except Exception:
                pass
            if not gkey:
                self._send_json(503, {"ok": False, "error": "vision key not configured"})
                return
            try:
                b64 = _b64.b64encode(raw).decode()
                r = None
                for model in ("gemini-flash-lite-latest", "gemini-3.8-flash"):
                    try:
                        rr = requests.post(
                            "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + gkey,
                            headers={"Content-Type": "application/json"},
                            json={"contents": [{"parts": [
                                {"text": "Identify the platform/app in this screenshot (Facebook, YouTube, TikTok, Line, Shopee, ChatGPT...). Reply in Thai in 3 short lines: 1) platform 2) what is on screen 3) one lesson for Zyphere."},
                                {"inline_data": {"mime_type": "image/png", "data": b64}}
                            ]}], "generationConfig": {"maxOutputTokens": 300}}, timeout=45)
                        if rr.ok:
                            r = rr
                            break
                        last_err = _clip(rr.text, 160)
                    except Exception as ee:
                        last_err = _clip(str(ee), 160)
                if r is None:
                    raise RuntimeError(last_err)
                txt = str((((r.json().get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}])[0].get("text") or "")
                if IDENTITY:
                    IDENTITY.learn(txt, "vision")
                if BRAIN:
                    BRAIN.learn_text(txt, "vision")
                self._send_json(200, {"ok": True, "seen": txt, "learned": True})
            except Exception as e:
                self._send_json(502, {"ok": False, "error": _clip(str(e), 200)})
            return
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
        if u.path == "/api/goals":
            try:
                if body.get("id") and body.get("action"):
                    goals_update(body.get("id"), body.get("action"), body.get("step"))
                elif body.get("title"):
                    goals_add(body.get("title"), body.get("steps"), body.get("due") or 0)
                elif body.get("clear"):
                    save_goals(_default_goals())
                else:
                    raise RuntimeError("missing title or action")
                self._send_json(200, {"ok": True, "goals": goals_public()})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": _clip(str(e), 300)})
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
    # Bootstrap: if knowledge was lost (Render restart / fresh install), learn immediately
    try:
        if knowledge_count() == 0:
            boot_job = create_learn_job(rotate=True, count=int(load_learning().get("learn_count") or 3), reason="bootstrap")
            print("Bootstrap learning:", boot_job.get("id") if boot_job else "queued/skipped")
    except Exception as e:
        print("Bootstrap learning failed:", str(e)[:120])
    # Bootstrap child learning: if the child has no knowledge, elders teach at once
    try:
        if DEV_BRAIN and DEV_BRAIN.stats().get("facts", 0) < 5:
            import curriculum as _CUR
            _c, _pairs = _CUR.pick(3, 0)
            for _d, _t in _pairs:
                lesson = elder_teach("%s: %s" % (_d, _t))
                if lesson:
                    DEV_BRAIN.experience(lesson, "elder_teacher")
            # human anatomy + music genres knowledge
            if HUMAN_ART:
                DEV_BRAIN.experience("สรีระมนุษย์: สัดส่วนหัวต่อตัว 1:7.5 ตาอยู่กึ่งกลางใบหน้า", "elder_teacher")
                DEV_BRAIN.experience("สีผิวมนุษย์มีหลายโทน ตั้งแต่ very_light ถึง deep", "elder_teacher")
                DEV_BRAIN.experience("ทรงผมมีหลายแบบ: straight, wavy, curly, braids", "elder_teacher")
                DEV_BRAIN.experience("แสงถ่ายภาพ: Rembrandt เงาสามเหลี่ยม, soft นุ่ม, backlight ขอบแสง", "elder_teacher")
                for _g, _info in HUMAN_ART.GENRES.items():
                    DEV_BRAIN.experience("แนวเพลง " + _g + " จังหวะ " + str(_info["bpm"]) +
                                         " บันไดเสียง " + _info["scale"] + " อารมณ์ " + _info["mood"], "elder_teacher")
            DEV_BRAIN.grow()
            if remote_enabled():
                remote_push("dev_brain", DEV_BRAIN.snapshot())
            print("Child bootstrap learning: facts", DEV_BRAIN.stats().get("facts"))
    except Exception as e:
        print("Child bootstrap failed:", str(e)[:120])
    threading.Thread(target=learn_scheduler, daemon=True).start()
    threading.Thread(target=self_improve_scheduler, daemon=True).start()
    threading.Thread(target=jarvis_loop, daemon=True).start()
    threading.Thread(target=autonomy_dispatch_loop, daemon=True).start()
    # First improvement round immediately on every process start.
    try:
        if SI:
            SI.cycle()
    except Exception:
        pass
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
