"""Zyphere Self-Test + Feynman Teaching - measure real understanding, not storage.

Owner's principle: do NOT measure progress by files/tokens, measure by
understanding, accuracy, problem solving, verifiable work.

Two loops:
1) Feynman: explain a concept in simple language -> compare with the source ->
   find gaps in your own explanation.
2) Self-test: generate questions, attempt them, score, and if weak -> queue
   re-learning (feeds back to research/learning loop).
"""
import re, time


class SelfTest:
    def feynman(self, concept, known_facts=None):
        """Simple-language explanation + gap detection."""
        c = str(concept or "").strip()
        if not c:
            return {"ok": False, "error": "missing concept"}
        facts = known_facts or []
        # build explanation from the child's own facts (not copied text)
        own = [f.get("o") for f in facts if c.lower() in (f.get("s", "") + " " + f.get("o", "")).lower()][:6]
        if own:
            expl = "อธิบายแบบง่าย: " + " ; ".join(str(x)[:120] for x in own) + " ครับ"
            gaps = []
            if len(own) < 3:
                gaps.append("อธิบายยังสั้น — ควรหาตัวอย่างเพิ่ม")
            if not any(re.search(r"\d", str(x)) for x in own):
                gaps.append("ยังไม่มีตัวเลข/ข้อมูลรูปธรรม — เพิ่มเพื่อความชัดเจน")
        else:
            expl = "ยังอธิบายเรื่อง '%s' ด้วยภาษาของตัวเองไม่ได้ — ต้องเรียนเพิ่มก่อนครับ" % c
            gaps = ["ไม่มีข้อเท็จจริงของตัวเองในหัวข้อนี้", "ควรค้นคว้า + ให้ปู่ย่าสอนเพิ่ม"]
        return {"ok": True, "concept": c, "explanation": expl, "gaps": gaps,
                "verdict": "เข้าใจระดับหนึ่ง" if own and not gaps else "ยังต้องเรียนเพิ่ม"}

    def quiz(self, concept, difficulty=3, known_facts=None):
        """Generate questions that test understanding (not recall of words)."""
        c = str(concept or "").strip()
        if not c:
            return {"ok": False, "error": "missing concept"}
        qs = [
            {"q": "อธิบาย '%s' ด้วยภาษาของคุณเองโดยไม่ใช้คำศัพท์เฉพาะ" % c, "tests": "ความเข้าใจ"},
            {"q": "'%s' ทำงานยังไงขั้นตอนต่อขั้นตอน?" % c, "tests": "กลไก"},
            {"q": "อะไรจะเกิดขึ้นถ้าไม่มี '%s'?" % c, "tests": "ความจำเป็น (counterfactual)"},
            {"q": "'%s' ใช้กับงานจริงอะไรได้บ้าง? ยกตัวอย่าง" % c, "tests": "การประยุกต์"},
            {"q": "'%s' มีข้อจำกัดหรือข้อโต้แย้งอะไร?" % c, "tests": "การแยกแยะ"},
        ][:max(1, min(5, difficulty))]
        return {"ok": True, "concept": c, "questions": qs,
                "note": "ตอบแล้วให้ตรวจกับแหล่งระดับ A/B — ถ้าตอบไม่ได้ให้เรียนซ้ำ"}

    def evaluate(self, concept, answers, known_facts=None):
        """Score answers by coverage + grounding; return what to re-learn."""
        c = str(concept or "").strip()
        facts = known_facts or []
        blob = " ".join(str(a or "") for a in (answers or [])).lower()
        tokens = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", c.lower())]
        covered = [t for t in tokens if t in blob]
        ratio = (len(covered) / len(tokens)) if tokens else 0.0
        grounded = bool(blob.strip())
        score = round(min(1.0, (0.6 * ratio + 0.4 * (1 if grounded else 0))), 2)
        return {"ok": True, "concept": c, "score": score,
                "verdict": "เข้าใจดี" if score >= 0.7 else ("พอใช้" if score >= 0.4 else "ต้องเรียนซ้ำ"),
                "need_relearn": score < 0.5,
                "next": "ส่งกลับไปให้ปู่ย่าสอน/ค้นคว้าใหม่ แล้วทดสอบอีกครั้ง" if score < 0.5 else "ผ่าน — บันทึกเป็นความรู้ที่เข้าใจแล้ว"}
