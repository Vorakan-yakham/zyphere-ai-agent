"""Zyphere Intent Router + Dynamic Contextual Memory - Zyphere's own round-2 gap.

1) Route user text to the right tool/data BEFORE calling the LLM (prefetch).
2) Session cache: keep last 3-5 turns, merge relevant context into the prompt
   automatically so the user never repeats themselves.

Success metrics (from Zyphere): route+context accuracy >=90%, re-ask rate <=5%,
latency < 1.0-1.5s. This module is the deterministic part that makes those
possible; measured via eval_loop + feedback signals.
"""
import time, threading, re

INTENT_PATTERNS = [
    ("search", r"(ค้น|หา|search|ข่าว|ล่าสุด|หาเวลา|ที่ไหน)", "search_web"),
    ("fetch", r"(อ่าน|เปิด|fetch|ดูหน้า|เว็บไซต์|link นี้)", "fetch_page"),
    ("research", r"(วิจัย|งานวิจัย|ห้องสมุด|paper|เอกสารวิชาการ|research)", "research"),
    ("reason", r"(ทำไม|วิเคราะห์|ตีโจทย์|แก้ปัญหา|เพราะอะไร|ยังไง|strateg)", "reason"),
    ("concept", r"(คืออะไร|ความหมาย|ตีความ|หมายถึง|term|คำว่า)", "concept"),
    ("media", r"(คลิป|วิดีโอ|เพลง|เสียง|ภาพ|make.*video|แต่งเพลง)", "media"),
    ("work", r"(เขียน|สร้าง|ออกแบบ|ทำรายงาน|โค้ด|make|build)", "work"),
    ("memory", r"(จำได้ไหม|เคยบอก|ชื่ออะไร|ครอบครัว|เมื่อกี้)", "memory"),
    ("status", r"(สถานะ|พร้อมไหม|remote|ระบบทำงาน|check)", "status"),
]


class IntentRouter:
    def __init__(self):
        self.lock = threading.RLock()
        self.sessions = {}  # sid -> {"turns":[...], "last":ts}
        self.route_log = []

    def route(self, text):
        t = str(text or "")
        for name, pat, tool in INTENT_PATTERNS:
            if re.search(pat, t, re.I):
                return {"ok": True, "intent": name, "tool": tool,
                        "confidence": 0.9 if name in ("memory", "status") else 0.8}
        return {"ok": True, "intent": "chat", "tool": None, "confidence": 0.7}

    # ---- dynamic contextual memory ----
    def remember(self, sid, role, content, turns=5):
        with self.lock:
            s = self.sessions.setdefault(str(sid), {"turns": [], "last": 0})
            s["turns"].append({"role": role, "text": str(content or "")[:800], "t": int(time.time())})
            s["turns"] = s["turns"][-turns:]
            s["last"] = int(time.time())
        return len(s["turns"])

    def context(self, sid, current_text="", max_turns=5):
        """Return recent turns + tokens useful for grounding the current query."""
        with self.lock:
            s = self.sessions.get(str(sid)) or {"turns": []}
            recent = list(s["turns"][-max_turns:])
        qtok = set(w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", current_text.lower()))
        scored = []
        for tn in recent:
            overlap = len(qtok & set(w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", tn["text"].lower())))
            scored.append((overlap, tn))
        scored.sort(key=lambda x: -x[0])
        relevant = [tn for _, tn in scored[:3]]
        return {"ok": True, "turns": recent, "relevant": relevant,
                "note": "ผสาน context อัตโนมัติ — ไม่ต้องขยายความซ้ำ"}

    def build_system(self, base_sys, sid, current_text):
        """Merge relevant memory into the system prompt (dynamic memory)."""
        ctx = self.context(sid, current_text)
        if not ctx["relevant"]:
            return base_sys
        lines = ["[บริบทจากการสนทนาก่อนหน้า — ใช้เพื่อตอบให้ตรงโดยไม่ถามซ้ำ]"]
        for tn in ctx["relevant"]:
            lines.append("- " + tn["role"] + ": " + tn["text"][:300])
        extra = "\n".join(lines)[:1800]
        return (base_sys + "\n" + extra)[:8000]

    def stats(self):
        with self.lock:
            return {"routes": len(self.route_log), "sessions": len(self.sessions),
                    "turns": sum(len(s.get("turns", [])) for s in self.sessions.values())}

    def snapshot(self):
        with self.lock:
            return {"sessions": self.sessions, "route_log": self.route_log[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "sessions" in data:
                self.sessions = data.get("sessions", {})
                self.route_log = data.get("route_log", [])
                return True
        return False
