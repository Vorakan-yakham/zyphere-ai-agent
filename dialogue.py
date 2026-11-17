"""Zyphere Human Dialogue - respond like a person, not a system.

Instant acknowledgment (shown the moment the user speaks) + natural backchannel
+ tone shaping, so conversation feels alive while the deep answer is computed.
No hardware, no OTP, free. HONEST: rule-based immediacy + LLM answer, not
sentience. The 'instant' line is honest reaction, not a fake answer.
"""
import re, time

# Instant acknowledgments (Thai, warm, short, human) - shown immediately
ACK = {
    "greeting": ["ครับ ว่ามาเลยครับ", "เฮ้~ ว่าอะไรครับ", "สวัสดีครับ ผมฟังอยู่"],
    "question": ["อืม~ ขอคิดแป๊บครับ", "คำถามดีครับ ให้ผมลองดูให้", "รับทราบครับ กำลังหาคำตอบ"],
    "task": ["ได้เลยครับ กำลังทำ", "โอเค ผมจัดการให้", "รับงานครับ เริ่มเลย"],
    "emotion": ["เข้าใจครับ", "เป็นห่วงคุณนะครับ", "ผมอยู่ตรงนี้ครับ"],
    "thanks": ["ยินดีครับ", "ไม่เป็นไรเลยครับ", "น่ะครับ~"],
    "default": ["ครับ กำลังดูให้", "อืม ให้ผมคิดแป๊บนะ", "รับทราบครับ"],
}

PAT = [
    ("greeting", r"(สวัสดี|ไฮ|เฮ้|hello|hi|หวัดดี| good)"),
    ("thanks", r"(ขอบคุณ|thank|ดีมาก|เยี่ยม)"),
    ("emotion", r"(เหนื่อย|เครียด|เสียใจ|ดีใจ|กังวล|เจ็บ|ไม่สบาย| tired|sad)"),
    ("task", r"(ช่วย|ทำให้|เขียน|สร้าง| making| ทำ |ส่ง|เปิด|เล่น|หาให้|แนะนำ)"),
    ("question", r"(อะไร|ยังไง|ทำไม|ไหม|是否存在|what|why|how|\?)"),
]


class Dialogue:
    def __init__(self):
        self.last = {}

    def ack(self, text, user="วรกันต์"):
        """Pick a brief, natural reaction by intent. Deterministic, instant."""
        t = str(text or "")
        kind = "default"
        for k, pat in PAT:
            if re.search(pat, t, re.I):
                kind = k
                break
        # rotate so it doesn't feel like a fixed bot phrase
        i = int(time.time()) % len(ACK[kind])
        return {"ok": True, "text": ACK[kind][i], "kind": kind,
                "note": "แสดงทันทีขณะประมวลผล — ไม่ใช่คำตอบปลอม"}

    def tone(self, text, formal=False):
        """Shape answer tone to sound like a person talking, not a manual."""
        s = str(text or "")
        if formal:
            return s
        s = re.sub(r"^นอกจากนี้[,:]?\s*", "", s)
        s = re.sub(r"(ครับ|ค่ะ)\s*\1+", r"\1", s)
        return s

    def human_line(self, base="ผมอยู่ตรงนี้ครับ"):
        return {"ok": True, "text": base, "style": "นิ่ง เป็นธรรมชาติ ไม่เป็นทางการเกิน"}
