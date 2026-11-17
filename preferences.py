"""Zyphere Preferences - learns user style silently from behavior."""
import json, os, threading, time
from collections import Counter

class Preferences:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.d = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.d = json.load(f)
        except Exception:
            self.d = {"short_reply": 0, "voice": 0, "no_emoji": 0,
                      "thai": 0, "english": 0, "samples": 0, "updated": 0}

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.d, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def observe(self, user_text="", answer="", voice=False, lang="th"):
        t = str(user_text or "")
        a = str(answer or "")
        with self.lock:
            self.d["samples"] = self.d.get("samples", 0) + 1
            if len(a) < 300:
                self.d["short_reply"] = self.d.get("short_reply", 0) + 1
            if any(x in t + a for x in ("สั้น", "กระชับ", "short", "ไม่ต้องยาว")):
                self.d["short_reply"] = self.d.get("short_reply", 0) + 2
            if any(x in t + a for x in ("อีโมจิ", "emoji", "ไม่เอาสัญลักษณ์")):
                self.d["no_emoji"] = self.d.get("no_emoji", 0) + 2
            if voice:
                self.d["voice"] = self.d.get("voice", 0) + 1
            if lang == "th":
                self.d["thai"] = self.d.get("thai", 0) + 1
            else:
                self.d["english"] = self.d.get("english", 0) + 1
            self.d["updated"] = int(time.time())
            self.save()
        return self.profile()

    def profile(self):
        n = max(1, self.d.get("samples", 0))
        return {
            "likes_short": self.d.get("short_reply", 0) >= n * 0.4,
            "likes_voice": self.d.get("voice", 0) >= n * 0.3,
            "no_emoji": self.d.get("no_emoji", 0) >= n * 0.2,
            "language": "th" if self.d.get("thai", 0) >= self.d.get("english", 0) else "en",
            "samples": self.d.get("samples", 0),
        }
