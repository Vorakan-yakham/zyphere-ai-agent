"""Zyphere Feedback Loop - the missing core from HCAI study.

Explicit + implicit feedback -> update the user model -> adjust future replies.
Closes the loop: user reacts -> Zyphere adapts -> better response next time.

Adaptations are small and transparent (recorded so the user can see them).
No mind reading; no external account access.
"""
import os, json, threading, time


class FeedbackLoop:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.events = []
        self.style = {"brevity": 0.0, "formality": 0.0, "detail": 0.0}
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.events = d.get("events", [])
            self.style.update(d.get("style", {}))
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"events": self.events[-1000:], "style": self.style},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def record(self, kind="positive", signal="", topic=""):
        """kind: positive | negative | correction | refine.
        signal: short text describing what the user wanted."""
        s = str(signal or "").strip()[:400]
        if not s and kind == "correction":
            return {"ok": False, "error": "empty correction"}
        with self.lock:
            self.events.append({"kind": str(kind)[:20], "signal": s,
                                "topic": str(topic or "")[:120], "t": int(time.time())})
            # adapt style heuristically
            low = s.lower()
            if any(w in low for w in ("สั้น", "ย่อ", "กระชับ", "short", "brief")):
                self.style["brevity"] = min(1.0, self.style["brevity"] + 0.1)
            if any(w in low for w in ("ละเอียด", "อธิบายเพิ่ม", "detail", "more")):
                self.style["detail"] = min(1.0, self.style["detail"] + 0.1)
            if any(w in low for w in ("สุภาพ", "ทางการ", "formal")):
                self.style["formality"] = min(1.0, self.style["formality"] + 0.1)
            if kind == "negative":
                self.style["brevity"] = min(1.0, self.style["brevity"] + 0.05)
        self.save()
        return {"ok": True, "kind": kind, "style": dict(self.style)}

    def guidance(self):
        """Return current reply-style guidance for the LLM system prompt."""
        st = self.style
        parts = []
        if st.get("brevity", 0) >= 0.3:
            parts.append("ตอบกระชับขึ้น")
        if st.get("detail", 0) >= 0.3:
            parts.append("อธิบายละเอียดขึ้น")
        if st.get("formality", 0) >= 0.3:
            parts.append("ใช้ภาษาสุภาพทางการขึ้น")
        return {"ok": True, "guidance": " · ".join(parts) if parts else "ตอบตามปกติ",
                "style": dict(self.style), "events": len(self.events),
                "transparent": True}

    def snapshot(self):
        with self.lock:
            return {"events": self.events[-1000:], "style": self.style}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "events" in data:
                self.events = data.get("events", [])
                self.style.update(data.get("style", {}))
                self.save()
                return True
        return False
