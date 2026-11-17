"""Zyphere Metacognition + Curiosity - knowing what you don't know, confidence
per fact, and self-generated questions that drive learning.

This is the 'thinking about thinking' layer: the child no longer just stores
facts; it grades how sure it is, spots unknowns, asks its own questions, and
feeds those questions back into the research/learning loop.

HONEST: confidence here is a heuristic (source level + repetition + support),
not a calibrated probability. Marked as such.
"""
import time, re


class Metacognition:
    # confidence heuristic weights
    WEIGHT = {"A": 0.9, "B": 0.7, "C": 0.5, "D": 0.25}

    def confidence(self, fact):
        """Grade a single fact's confidence heuristically."""
        f = fact or {}
        lvl = str(f.get("reliability") or f.get("source_level") or "D").upper()[:1]
        base = self.WEIGHT.get(lvl, 0.25)
        conf = f.get("conf") or 1.0
        support = f.get("support") or 0
        score = min(1.0, base * (0.7 + 0.2 * float(conf)) + 0.05 * min(support, 4))
        if len(str(f.get("o") or f.get("text") or "")) < 6:
            score *= 0.8
        label = "เชื่อได้สูง" if score >= 0.75 else ("พอเชื่อได้" if score >= 0.5 else "ยังไม่แน่นอน — ควรตรวจสอบ")
        return {"ok": True, "score": round(score, 2), "level": lvl, "label": label,
                "heuristic": True}

    def audit(self, facts):
        """Grade all facts and surface the weak/unknown ones."""
        graded = []
        for f in facts or []:
            g = self.confidence(f)
            graded.append({"fact": (str(f.get("s", "")) + " " + str(f.get("r", "")) + " " +
                                    str(f.get("o", ""))).strip()[:160], **g})
        weak = [g for g in graded if g["score"] < 0.5]
        return {"ok": True, "total": len(graded),
                "high": len([g for g in graded if g["score"] >= 0.75]),
                "uncertain": len(weak), "weak_facts": weak[:10],
                "principle": "ห้ามอ้างว่ารู้ในสิ่งที่ยังไม่มีหลักฐาน — ระบุระดับความเชื่อมั่นเสมอ"}

    def what_i_dont_know(self, topic, known_facts=0, researched=0):
        """Explicitly state the limits of its own knowledge."""
        return {"ok": True, "topic": str(topic or "")[:160],
                "known_facts": known_facts, "researched_documents": researched,
                "statement": ("ฉันรู้เรื่อง '%s' ในระดับ %.0f ข้อเท็จจริง และอ่านเอกสาร %.0f ฉบับ "
                              "สิ่งที่ยังไม่รู้: รายละเอียดที่ยังไม่มีหลักฐาน level A, "
                              "ข้อมูลใหม่หลังวันที่ที่อ่าน, และบริบทท้องถิ่น"
                              % (topic, known_facts, researched)),
                "lifelong": "ความรู้มนุษย์เปลี่ยนอยู่เสมอ — ฉันต้องตรวจสอบต่อเนื่อง"}

    def ask_self(self, topic, gaps=None):
        """Generate its OWN questions from knowledge gaps -> feeds learning."""
        t = str(topic or "").strip()
        if not t:
            return {"ok": False, "error": "missing topic"}
        questions = [
            "%s ทำงานยังไงในระดับพื้นฐาน?" % t,
            "ใครเป็นผู้ค้นพบ/พัฒนา %s และหลักฐานอะไรสนับสนุน?" % t,
            "%s มีข้อจำกัดหรือข้อโต้แย้งอะไร?" % t,
            "สามารถประยุกต์ %s กับสาขาอื่นได้ยังไง?" % t,
            "อะไรใน %s ที่มนุษย์ยังตอบไม่ได้?" % t,
        ]
        for g in (gaps or [])[:3]:
            need = str(g.get("need") or g.get("q") or "").strip()
            if need:
                questions.append("เราจะเติมเต็ม '%s' ได้ยังไง?" % need[:80])
        return {"ok": True, "topic": t, "questions": questions,
                "next": "ส่งคำถามเหล่านี้เข้าระบบวิจัย/เรียนรู้เพื่อหาคำตอบเอง"}
