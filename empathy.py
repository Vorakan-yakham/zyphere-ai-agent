"""Zyphere Empathy from REAL memory - the honest answer to "ขาดประสบการณ์อารมณ์".

Zyphere cannot FEEL (no body, no lived emotion). Claiming otherwise would be
a false claim. What it CAN do is respond with understanding grounded in the
REAL things it remembers: preferences, feedback tone, family, voice state.

HONEST boundary is part of the output: never pretend to have feelings.
Free, local, uses existing modules.
"""
import re


class Empathy:
    def __init__(self):
        self.boundary = ("ผมไม่มีร่างกายและไม่ได้ 'รู้สึก' แบบมนุษย์ — แต่ผมจำสิ่งที่คุณบอกได้ "
                         "และจะตอบด้วยความเข้าใจตรงกับนั้นครับ")

    def read_signals(self, state=None):
        s = state or {}
        out = []
        if s.get("likes_short"):
            out.append("ชอบตอบสั้น กระชับ")
        if s.get("likes_voice"):
            out.append("ชอบฟังเสียงมากกว่าอ่าน")
        if s.get("no_emoji"):
            out.append("ไม่ชอบ emoji/สัญลักษณ์")
        if s.get("family"):
            out.append("มีครอบครัวที่จำได้ (%d คน)" % len(s["family"]))
        if s.get("last_feedback"):
            out.append("เพิ่งให้ feedback เรื่อง " + str(s["last_feedback"])[:40])
        if s.get("negative_feedback", 0) > 0:
            out.append("มี feedback เชิงปรับปรุง %d ครั้ง — ต้องระวังน้ำเสียง" % s["negative_feedback"])
        return out

    def respond_style(self, text="", state=None):
        """Return a tone directive + honest boundary, grounded in real memory."""
        t = str(text or "")
        signals = self.read_signals(state)
        distress = bool(re.search(r"(เหนื่อย|เครียด|เสียใจ|กังวล|ไม่สบาย|เจ็บ|ท้อ|ภูมิใจ|ดีใจ)", t, re.I))
        parts = []
        if distress:
            parts.append("ผู้ใช้กำลังสื่อสารอารมณ์ — ตอบด้วยความเข้าใจ ก่อนอธิบายเนื้อหา")
        if signals:
            parts.append("ปรับตามความชอบที่จำได้: " + ", ".join(signals))
        return {"ok": True, "distress": distress, "signals": signals,
                "directive": " · ".join(parts) if parts else "ตอบตามปกติ สุภาพ เป็นกันเอง",
                "boundary": self.boundary,
                "honest": "ใช้ความจำจริง ไม่ใช่การเสแสร้งว่ามีความรู้สึก"}

    def status(self):
        return {"ok": True, "module": "Empathy-from-Memory",
                "can_feel": False, "can_remember_preferences": True,
                "note": "เหนือกว่า AI ทั่วไปตรง 'จำความชอบคุณแล้วปรับน้ำเสียง' ไม่ใช่ตรง 'มีหัวใจ'"}
