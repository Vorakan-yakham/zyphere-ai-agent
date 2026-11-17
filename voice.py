"""Zyphere Voice Identity - learn what makes Thai speech sound natural/pleasant,
then tune Zyphere's own voice accordingly.

Principles (from phonetics / TTS practice), used as the knowledge base:
- Thai is a tonal language (5 tones) -> wrong pitch/prosody changes meaning.
- Pleasant male Thai anchor voice: lower pitch, warm, steady, moderate pace.
- Too-fast rate blurs tones; too-slow sounds robotic.
- Natural rhythm = pauses at phrase boundaries, not flat monotone.
- Consistency of voice across a reply matters more than perfect solo notes.

Zyphere's own voice config is stored here (persisted via remote KV) so the
child can "own" its voice, not just borrow a default.
"""
import os, json, threading, time

KNOWLEDGE = {
    "เสียงไทยเพราะเพราะอะไร": [
        "ภาษาไทยมี 5 ระดับเสียง (กลาง/ต่ำ/ตก/สูง/ขึ้น) — ถ้าความสูงผิด ความหมายเปลี่ยน",
        "เสียงผู้ชายที่ฟังเพราะ มักอยู่ในช่วงความถี่ต่ำถึงกลาง (ประมาณ 100–150 Hz) นุ่ม ไม่แห้ง",
        "ความเร็วพอดี (ไม่เร็วเกินไป) ทำให้ผู้ฟังแยกพยางค์และ 지원ศัพท์ได้ชัด",
        "จังหวะ natural มีการหยุดสั้น ๆ ตามขั้นตอนประโยค ไม่ใช่เสียงราบเรียบตลอด",
        "น้ำเสียงอบอุ่น นิ่ง มั่นใจ แบบนักข่าว/ผู้บรรยาย ฟังแล้วเชื่อถือได้",
        "การเน้นคำสำคัญ (stress) พอเหมาะ ทำให้ฟังมีชีวิต ไม่เรียบ ',' แต่ไม่ทับศัพท์",
    ],
    "ปัจจัยที่ทำให้เสียงแข็ง/ไม่ natur": [
        "พูดเร็วเกินไป → สนุก/เสียงกัดกัน",
        "pitch สูงเกินไปสำหรับเสียงชาย → แหลม ไม่นุ่ม",
        "ไม่หยุดเลย → อึดอัด ไม่เหมือนมนุษย์",
        "ตัดคำกลางคำ → ขาด ๆ หาย ๆ (แก้ด้วยการตัดตามประโยค)",
    ],
}

# tuned default: Niwat (male news anchor), lower pitch, calm rate
DEFAULT = {
    "voice_th": "th-TH-NiwatNeural",
    "voice_en": "en-GB-RyanNeural",
    "rate": 0.96,        # natural calm pace
    "pitch_ratio": -6,   # lower, warm male
    "style": "นักข่าวชาย นุ่ม นิ่ง เชื่อมั่น",
    "engine": "edge-tts",
    "updated": 0,
}


class VoiceIdentity:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.cfg = dict(DEFAULT)
        self.learned = []
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.cfg.update(d.get("cfg", {}))
            self.learned = d.get("learned", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"cfg": self.cfg, "learned": self.learned},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def learn(self):
        """Learn the voice knowledge -> child can recite it."""
        with self.lock:
            for k, items in KNOWLEDGE.items():
                for it in items:
                    if it not in self.learned:
                        self.learned.append(it)
            self.save()
        return {"ok": True, "learned": len(self.learned)}

    def tune(self, **kwargs):
        """Adjust own voice. Safe ranges only."""
        with self.lock:
            if "rate" in kwargs:
                self.cfg["rate"] = max(0.8, min(1.2, float(kwargs["rate"])))
            if "pitch_ratio" in kwargs:
                self.cfg["pitch_ratio"] = max(-12, min(6, int(kwargs["pitch_ratio"])))
            if "voice_th" in kwargs:
                self.cfg["voice_th"] = str(kwargs["voice_th"])[:60]
            if "style" in kwargs:
                self.cfg["style"] = str(kwargs["style"])[:120]
            self.cfg["updated"] = int(time.time())
            self.save()
            return dict(self.cfg)

    def profile(self):
        with self.lock:
            return {"cfg": dict(self.cfg), "knowledge": KNOWLEDGE, "learned": len(self.learned)}

    def snapshot(self):
        with self.lock:
            return {"cfg": self.cfg, "learned": self.learned}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "cfg" in data:
                self.cfg.update(data.get("cfg", {}))
                self.learned = data.get("learned", [])
                self.save()
                return True
        return False
