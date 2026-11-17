"""Zyphere Proactive Engine - anticipate needs before the user asks (JARVIS trait #6).

Reduces cognitive load by suggesting the next useful action from context:
time, recent topics, knowledge gaps, pending works, family, revenue events.

HONEST: suggestions are heuristic from local state — no mind reading, no
external account access. Owner must approve actions needing OTP/account.
"""
import time, datetime


class Proactive:
    def __init__(self):
        self.history = []

    def _hour(self):
        return datetime.datetime.now().hour

    def suggest(self, ctx=None):
        """ctx may contain: recent_topics, gaps, pending_works, family, reminders."""
        ctx = ctx or {}
        h = self._hour()
        out = []

        # time-based (JARVIS-style ambient awareness)
        if 6 <= h < 11:
            out.append({"type": "briefing", "text": "เช้านี้ — สรุปสิ่งใหม่ที่ Zyphere เรียนรู้เมื่อคืนให้ฟังไหมครับ?",
                        "action": "/api/briefing"})
        elif 11 <= h < 14:
            out.append({"type": "health", "text": "กลางวัน — เช็กสถานะระบบ/ความจำถาวรให้ไหมครับ?",
                        "action": "/api/storage"})
        elif 17 <= h < 21:
            out.append({"type": "work", "text": "เย็นนี้ — มีผลงานที่ทำค้างอยู่ ส่งเป็นไฟล์ให้ดาวน์โหลดไหมครับ?",
                        "action": "/api/work/list"})
        else:
            out.append({"type": "rest", "text": "ดึกแล้ว — Zyphere จะเรียนรู้ต่อเอง ขอให้พักครับ",
                        "action": ""})

        for t in (ctx.get("recent_topics") or [])[:2]:
            out.append({"type": "continue", "text": "ต่อเรื่อง '" + str(t)[:60] + "' ไหมครับ?",
                        "action": ""})
        for g in (ctx.get("gaps") or [])[:2]:
            need = str(g.get("need") or g.get("q") or "")[:80]
            if need:
                out.append({"type": "gap", "text": "ยังมีคำถามค้าง: " + need + " — ให้หาคำตอบให้ไหมครับ?",
                            "action": "/api/research/search"})
        for w in (ctx.get("pending_works") or [])[:1]:
            out.append({"type": "work_ready", "text": "ผลงาน '" + str(w.get("topic", ""))[:50] + "' พร้อมแล้ว",
                        "action": "/api/work/list"})

        self.history = out[:6]
        return {"ok": True, "hour": h, "suggestions": self.history,
                "principle": "คาดการณ์จากบริบทจริงในระบบ — ไม่เดา ไม่แอบเข้าบัญชี"}
