"""Zyphere Thai Language Mastery - reading, writing, narration, spacing,
word order, stress. Knowledge + a real APPLIEDCorrector that fixes text before
Zyphere reads/narrates it, so speech doesn't sound 'เพี้ยน'.

HONEST: rule-based correction for common cases + knowledge. Not a full
linguistic engine; complex literary prose still needs review.
"""
import re

# 5 Thai tones — wrong tone/pitch changes meaning (critical for TTS)
TONES = {
    "กลาง": "เสียงกลาง ระดับปกติ (เช่น มา)",
    "ต่ำ": "เสียงต่ำ ค่อยๆ ลดลง (เช่น ม่า)",
    "ตก": "เสียงตกจากสูงลงต่ำ (เช่น ม้า)",
    "สูง": "เสียงสูง (เช่น หมา)",
    "ขึ้น": "เสียงขึ้นจากต่ำไปสูง (เช่น หม้า)",
}

# Commonly misspelled / confusable Thai words (correct, wrong forms)
CONFUSABLES = {
    "แล้ว": ["เเล้ว"], "เพราะ": ["พร้อม", "พราะ"], "ก็": ["ก้อ"],
    "ว่า": ["วา"], "ซึ่ง": ["ซึง"], "หรือ": ["หรือ"], "แต่": ["เเต่"],
    "การ": ["กาาร"], "ความ": ["ควาาม"], "ที่": ["ทึ่"],
    "ต้อง": ["ต่อง"], "จะ": ["จ่ะ"],
}

# Thai has no spaces between words; we insert pauses at phrase boundaries
# (commas/periods) rather than between every word — this is what sounds natural.
PAUSE_MARKS = {"จุด": "。.", "จุลภาค": ",", "อัศเจรีย์": "!?！？", "colons": ":؛"}


class LanguageMastery:
    def __init__(self):
        self.learned = []

    def learn(self):
        facts = [
            "ภาษาไทยไม่เว้นวรรคระหว่างคำ แต่เว้นที่ขั้นตอนประโยค (จุลภาค/จุด) เพื่อจังหวะการอ่าน",
            "ใส่เครื่องหมายวรรคตอนผิดตำแหน่ง → การออกเสียง/เน้นความหมายเพี้ยนทันที",
            "ภาษาไทยมี 5 ระดับเสียง ความสูงผิดทำให้ความหมายเปลี่ยน (มา/ม่า/ม้า/หมา/หม้า)",
            "ลำดับคำไทย: ประธาน + กริยา + กรรม — เปลี่ยนลำดับอาจฟังแปลกแต่ยังเข้าใจได้",
            "คำที่เน้น (stress) ควรอยู่ที่คำสำคัญ ไม่เน้นทุกคำ และไม่เน้นคำต่อเนื่องกันเกิน 2 คำ",
            "การอ่านยาว ๆ ต้องหยุดสั้นที่ขั้นตอน ไม่หยุดกลางคำ (ไม่งั้นขาด ๆ หาย ๆ)",
            "คำที่เขียนผิดบ่อย: แล้ว/เพราะ/ก็/ซึ่ง/แต่ — ต้องตรวจก่อนอ่านออกเสียง",
            "การบรรยายที่น่าฟัง: ประโยคสั้นสลับยาว เน้นตัวเลข/ชื่อสำคัญ เสียงนุ่มลงท้ายประโยค",
        ]
        self.learned = list(dict.fromkeys(self.learned + facts))
        return {"ok": True, "learned": len(self.learned)}

    def correct(self, text):
        """Apply common Thai writing/spacing corrections before narration."""
        s = str(text or "")
        changes = []
        for correct, wrongs in CONFUSABLES.items():
            for w in wrongs:
                if w and w in s:
                    s = s.replace(w, correct)
                    changes.append("%s → %s" % (w, correct))
        # normalize spaces: collapse runs, ensure space after commas/periods
        s = re.sub(r"[ \t]+", " ", s).strip()
        s = re.sub(r"\s*([,;:])\s*", r"\1 ", s)
        s = re.sub(r"\.\s*", ". ", s)
        # remove spaces inside Thai word runs (Thai doesn't space between words)
        s = re.sub(r"(?<=[\u0E00-\u0E7F])\s+(?=[\u0E00-\u0E7F])", "", s)
        return {"ok": True, "text": s.strip(), "changes": changes}

    def narration_plan(self, text, emphasis=3):
        """Plan stress: mark important tokens (numbers, quoted, capitalized)
        so the voice emphasizes them — avoids flat/เพี้ยน reading."""
        s, _ = self.correct(text), None
        s = s["text"] if isinstance(s, dict) else str(text)
        toks = re.findall(r"[0-9]+(?:[.,][0-9]+)?|[A-Za-z][A-Za-z0-9\-]+|[\u0E00-\u0E7F]+", s)
        marked = []
        for t in toks:
            imp = bool(re.search(r"[0-9]|^[A-Z]", t)) or len(t) > 8
            if imp and len(marked) < emphasis:
                marked.append(t)
        return {"ok": True, "plan": "อ่านปกติ → เน้นเล็กน้อยที่: " + ", ".join(marked) if marked else "อ่านน้ำเสียงสม่ำเสมอ",
                "emphasis_tokens": marked, "tip": "หยุดสั้นที่ , . ! ? — ไม่หยุดกลางคำ"}

    def knowledge(self):
        return {"tones": TONES, "confusables": {k: v for k, v in CONFUSABLES.items() if v},
                "pause_marks": PAUSE_MARKS, "learned": self.learned}
