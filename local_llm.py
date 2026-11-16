"""สมอง AI ที่รันบนเครื่องคุณเอง (Ollama) - ไม่ใช้ API คลาวด์ของค่ายใดเลย."""
import base64
import json
import os
import urllib.error
import urllib.request


class LLMError(Exception):
    pass


class LocalLLM:
    def __init__(self, model="qwen2.5:7b-instruct", host=None, timeout=300):
        self.model = model
        host = host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
        self.host = (host if host.startswith("http") else "http://" + host).rstrip("/")
        self.timeout = timeout

    def _open(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.host + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.URLError as e:
            raise LLMError(f"ติดต่อ Ollama ที่ {self.host} ไม่ได้ ({e}). รัน `ollama serve` และ "
                           f"`ollama pull {self.model}` แล้วหรือยัง?")

    def models(self):
        with self._open("/api/tags") as r:
            return [m["name"] for m in json.load(r).get("models", [])]

    def stream(self, messages, system="", max_tokens=2048, temperature=0.7, images=None):
        """messages = [{"role": "user"|"assistant", "content": str}, ...]; images = [bytes] (ต้องใช้โมเดลที่มองภาพได้)"""
        msgs = ([{"role": "system", "content": system}] if system else []) + [dict(m) for m in messages]
        if images and msgs:
            msgs[-1]["images"] = [base64.b64encode(b).decode() for b in images]
        payload = {"model": self.model, "messages": msgs, "stream": True,
                   "options": {"num_predict": max_tokens, "temperature": temperature}}
        with self._open("/api/chat", payload) as r:
            for line in r:
                if not line.strip():
                    continue
                d = json.loads(line)
                if "error" in d:
                    raise LLMError(d["error"])
                chunk = d.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
                if d.get("done"):
                    break

    def complete(self, messages, **kw):
        return "".join(self.stream(messages, **kw))
