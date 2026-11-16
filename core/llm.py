"""Local LLM backend (Ollama). Same interface as the former cloud wrapper: LLM(api_key, model).

No cloud API and no API key: every token is generated on this machine.
Messages may use provider-neutral content blocks (text / image / document); they are converted here.
"""
import base64
import functools
import io
import json
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Dict, Generator, List, Optional

RECOMMENDED = {
    "qwen2.5:3b-instruct": "Qwen2.5 3B — เร็วสุด (RAM 4GB+)",
    "qwen2.5:7b-instruct": "Qwen2.5 7B — สมดุล (RAM 8GB+)",
    "qwen2.5:14b-instruct": "Qwen2.5 14B — ลึกขึ้น (RAM 16GB+)",
    "qwen2.5:32b-instruct": "Qwen2.5 32B — ลึกสุด (VRAM 24GB+)",
}
MODELS = RECOMMENDED  # kept for backwards compatibility
DEFAULT_MODEL = "qwen2.5:7b-instruct"
VISION_HINTS = ("vl", "llava", "vision", "minicpm-v", "moondream", "gemma3")


class LLMError(Exception):
    """Raised with a user-presentable (Thai) message."""


def _host() -> str:
    h = os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
    return (h if h.startswith("http") else "http://" + h).rstrip("/")


_cache: Dict[str, object] = {"t": 0.0, "models": None}


def installed_models(force: bool = False) -> List[str]:
    """Models installed in Ollama (cached 5 s). Empty list if Ollama is down or has none."""
    now = time.time()
    if force or _cache["models"] is None or now - float(_cache["t"]) > 5:
        try:
            with urllib.request.urlopen(_host() + "/api/tags", timeout=1.5) as r:
                names = [m["name"] for m in json.load(r).get("models", [])]
        except Exception:
            names = None
        _cache.update(t=now, models=names)
    return list(_cache["models"] or [])


def ollama_up() -> bool:
    installed_models()
    return _cache["models"] is not None


def default_model() -> str:
    env = os.environ.get("ZYPHERE_MODEL")
    if env:
        return env
    have = [m for m in installed_models() if "embed" not in m.lower()]
    if DEFAULT_MODEL in have or not have:
        return DEFAULT_MODEL
    return next((m for m in have if not _is_vision(m)), have[0])


def model_choices() -> Dict[str, str]:
    """Installed models first, then recommended ones that still need `ollama pull`."""
    out = {m: f"{m} — ติดตั้งแล้ว" for m in installed_models() if "embed" not in m.lower()}
    for k, label in RECOMMENDED.items():
        out.setdefault(k, f"{label} · ยังไม่ติดตั้ง")
    return out


def get_api_key(secrets=None) -> Optional[str]:
    """No key needed. Returns a truthy marker when Ollama is running AND has at least one model."""
    return "local" if installed_models() else None


def _is_vision(name: str) -> bool:
    return any(k in name.lower() for k in VISION_HINTS)


def _vision_model(selected: str) -> str:
    env = os.environ.get("ZYPHERE_VISION_MODEL")
    if env:
        return env
    if _is_vision(selected):
        return selected
    for m in installed_models():
        if _is_vision(m):
            return m
    raise LLMError("ข้อความนี้มีรูปภาพ แต่ยังไม่มีโมเดลที่มองภาพได้ — รัน `ollama pull qwen2.5vl:7b` แล้วลองใหม่")


@functools.lru_cache(maxsize=8)
def _pdf_text(b64: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(base64.b64decode(b64)))
        text = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    except ImportError:
        return "[PDF: ยังไม่ได้ติดตั้ง pypdf จึงอ่านไม่ได้]"
    except Exception:
        return "[PDF: อ่านไม่ได้]"
    return f"[PDF text]\n{text}\n[End PDF]" if text else "[PDF: ไม่มีข้อความ (อาจเป็นภาพสแกน)]"


class LLM:
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.model = model
        self.num_ctx = int(os.environ.get("ZYPHERE_NUM_CTX", "8192"))
        self.last_usage = (0, 0)

    # ---------- conversion ----------
    def _clip(self, text: str) -> str:
        if len(text) <= self.num_ctx:
            return text
        return text[: self.num_ctx] + f"\n[... ตัดทอน: ยาวเกินหน้าต่างบริบท {self.num_ctx} — เพิ่ม ZYPHERE_NUM_CTX ได้ถ้า RAM พอ ...]"

    def _convert(self, system: str, messages: List[dict]):
        out = [{"role": "system", "content": system}] if system else []
        has_images = False
        for m in messages:
            c = m["content"]
            if isinstance(c, str):
                out.append({"role": m["role"], "content": self._clip(c)})
                continue
            texts, images = [], []
            for b in c:
                t = b.get("type")
                if t == "text":
                    texts.append(self._clip(b.get("text", "")))
                elif t == "image":
                    images.append(b["source"]["data"])
                elif t == "document":
                    texts.append(self._clip(_pdf_text(b["source"]["data"])))
            msg = {"role": m["role"], "content": "\n\n".join(x for x in texts if x)}
            if images:
                msg["images"] = images
                has_images = True
            out.append(msg)
        return out, has_images

    # ---------- transport ----------
    def _payload(self, system, messages, max_tokens, stream, temperature):
        msgs, has_images = self._convert(system, messages)
        model = _vision_model(self.model) if has_images else self.model
        return {"model": model, "messages": msgs, "stream": stream, "keep_alive": "30m",
                "options": {"num_predict": max_tokens, "num_ctx": self.num_ctx, "temperature": temperature}}

    def _open(self, payload: dict):
        req = urllib.request.Request(_host() + "/api/chat", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            return urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise LLMError(f"ไม่พบโมเดล {payload['model']} ในเครื่อง — รัน `ollama pull {payload['model']}`") from e
            try:
                detail = json.loads(e.read().decode()).get("error", "")
            except Exception:
                detail = ""
            raise LLMError(f"Ollama ตอบกลับผิดพลาด (HTTP {e.code}) {detail}"[:300]) from e
        except (urllib.error.URLError, ConnectionError, socket.timeout) as e:
            raise LLMError("เชื่อมต่อ Ollama ไม่ได้ — เปิดโปรแกรม Ollama (`ollama serve`) แล้วลองใหม่") from e

    # ---------- API ----------
    def stream(self, system: str, messages: List[dict], max_tokens: int = 4096,
               temperature: float = 0.6) -> Generator[str, None, None]:
        resp = self._open(self._payload(system, messages, max_tokens, True, temperature))
        try:
            with resp:
                for line in resp:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    if d.get("error"):
                        raise LLMError(str(d["error"])[:300])
                    chunk = d.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if d.get("done"):
                        self.last_usage = (d.get("prompt_eval_count", 0) or 0, d.get("eval_count", 0) or 0)
                        break
        except (OSError, socket.timeout) as e:
            raise LLMError("การเชื่อมต่อกับ Ollama ขาดระหว่างตอบ (โมเดลอาจหน่วยความจำไม่พอ)") from e

    def complete(self, system: str, messages: List[dict], max_tokens: int = 1024,
                 temperature: float = 0.3) -> str:
        try:
            with self._open(self._payload(system, messages, max_tokens, False, temperature)) as r:
                d = json.load(r)
        except (OSError, socket.timeout) as e:
            raise LLMError("การเชื่อมต่อกับ Ollama ขาดระหว่างตอบ") from e
        if d.get("error"):
            raise LLMError(str(d["error"])[:300])
        self.last_usage = (d.get("prompt_eval_count", 0) or 0, d.get("eval_count", 0) or 0)
        return d.get("message", {}).get("content", "")
