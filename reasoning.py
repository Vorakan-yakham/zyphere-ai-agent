"""Zyphere Reasoning Engine - 'ตีโจทย์ให้แตก': think, analyze, discriminate.

Turns a problem into structured thinking using the methods from the owner's
master directives (First Principles, MECE, fact/opinion/theory discrimination,
second-order thinking, evidence levels). Produces a reviewable reasoning map,
not just an answer.

Works offline (structured scaffold) + optionally uses ensemble LLM as the
'thinking teacher' via app.py. No gambling/illegal.
"""
import re

FRAMEWORKS = {
    "first_principles": "แยกความเชื่อเดิมออก → หาสิ่งที่รู้จริงเป็นข้อเท็จจริงพื้นฐาน → สร้างใหม่จากศูนย์",
    "mece": "แยกประเด็นให้ครบถ้วนและไม่ซ้ำกัน (Mutually Exclusive, Collectively Exhaustive)",
    "discriminate": "แยกแยะ: ข้อเท็จจริง / ความเห็น / สมมติฐาน / ทฤษฎี / การคาดการณ์ — ระบุระดับความเชื่อมั่น",
    "second_order": "คิดผลกระทบลูกโซ่: ถ้าทำสิ่งนี้ → เกิดอะไร → แล้วเกิดอะไรต่อ → ใครได้/เสีย",
    "causal": "หาเหตุ-ผล (ไม่ใช่แค่ความสัมพันธ์) — มีหลักฐานอะไรสนับสนุน ตรวจสอบตัวแปรอื่น",
    "counterfactual": "คิดแบบ 'ถ้าไม่ทำ/ทำ differently จะเป็นยังไง' → ทดสอบความจำเป็นของเหตุ",
    "inversion": "คิดตรงข้าม: อะไรจะทำให้แน่นอนว่าล้มเหลว → หลีกเลี่ยงสิ่งนั้นก่อน",
}

BLOCK = ("พนัน", "casino", "gambling", "บาคาร่า", "สล็อต", "ผิดกฎหมาย")


class ReasoningEngine:
    def __init__(self):
        self.methods = list(FRAMEWORKS)

    def solve(self, problem, approach="full"):
        """Break a problem open into a structured thinking map."""
        p = str(problem or "").strip()
        if not p:
            return {"ok": False, "error": "missing problem"}
        if any(b in p.lower() for b in BLOCK):
            return {"ok": False, "error": "งดเด็ดขาด: โจทย์ผิดกฎหมาย/เว็บพนัน"}

        parts = [x.strip() for x in re.split(r"[?？.!?\n,;]|\s+แล้ว\s+", p) if x.strip()]
        steps = []
        steps.append({"step": "แยกโจทย์ (MECE)",
                      "content": " | ".join(parts[:8]) if parts else p,
                      "why": FRAMEWORKS["mece"]})
        steps.append({"step": "รากเหตุ (First Principles)",
                      "content": "อะไรเป็นข้อเท็จจริงที่ยืนยันได้ในโจทย์นี้? อะไรเป็นความเชื่อที่ยังไม่พิสูจน์?",
                      "why": FRAMEWORKS["first_principles"]})
        steps.append({"step": "แยกแยะข้อเท็จจริง/สมมติฐาน",
                      "content": "ข้อเท็จจริง = พิสูจน์ได้ · ความเห็น = ความเชื่อส่วนบุคคล · สมมติฐาน = ยังไม่มีหลักฐาน · ทฤษฎี = มีหลักฐานสนับสนุน · การคาดการณ์ = อนาคต",
                      "why": FRAMEWORKS["discriminate"]})
        steps.append({"step": "เหตุ-ผล",
                      "content": "สาเหตุที่เป็นไปได้ → หลักฐาน → ผลลัพธ์ → ตรวจหาตัวแปรอื่นที่อธิบายผลเดียวกันได้",
                      "why": FRAMEWORKS["causal"]})
        steps.append({"step": "ผลลำดับที่ 2",
                      "content": "ถ้าแก้โจทย์นี้ → ใครได้/ใครเสีย → ผลข้างเคียงระยะยาวคืออะไร",
                      "why": FRAMEWORKS["second_order"]})
        steps.append({"step": "ทดสอบตรงข้าม (Inversion)",
                      "content": "อะไรจะทำให้โจทย์นี้ล้มเหลวแน่นอน? หลีกเลี่ยงสิ่งนั้นก่อน",
                      "why": FRAMEWORKS["inversion"]})
        steps.append({"step": "สมมติฐานตรงข้าม (Counterfactual)",
                      "content": "ถ้าไม่ทำตามทางที่คิดไว้ ผลจะต่างกันไหม? ถ้าไม่ต่าง → เหตุเดิมอาจไม่ใช่เหตุจริง",
                      "why": FRAMEWORKS["counterfactual"]})
        steps.append({"step": "สรุป + ความเชื่อมั่น",
                      "content": "ข้อสรุปควรระบุ: รู้อะไร confidently · ยังไม่รู้อะไร · ต้องหาหลักฐานเพิ่มตรงไหน",
                      "why": "มาตรฐานคุณภาพ: ห้ามอ้างว่ารู้ในสิ่งที่ไม่มีหลักฐาน"})
        return {"ok": True, "problem": p[:400], "approach": approach,
                "thinking_map": steps, "methods": self.methods,
                "reminder": "ตีโจทย์แตก = แยกส่วน → หาราก → แยกแยะ → ทดสอบตรงข้าม → สรุปอย่างมีหลักฐาน"}

    def think_prompt(self, problem):
        """Prompt for the ensemble LLM to fill the scaffold with real analysis."""
        return ("คุณเป็นนักคิดของ Zyphere จง 'ตีโจทย์ให้แตก' โจทย์ต่อไปนี้:\n%s\n\n"
                "ทำตามขั้นตอน: แยกโจทย์ (MECE) → หาข้อเท็จจริงราก → แยกแยะ ข้อเท็จจริง/ความเห็น/"
                "สมมติฐาน/ทฤษฎี/การคาดการณ์ → เหตุผล → ผลลำดับที่ 2 → ทดสอบตรงข้าม → "
                "สรุปพร้อมระดับความเชื่อมั่นและสิ่งที่ยังไม่รู้\n"
                "ห้ามแต่งหลักฐาน ห้ามใช้เนื้อหาผิดกฎหมาย/พนัน ตอบภาษาไทย กระชับแต่ลึก") % problem
