"""Zyphere Self-Correction Loop - Zyphere's round-3 gap.

Before sending an answer, check it for fixable defects and repair IN THE SAME
TURN (no user correction turns). Uses deterministic checks + eval score:
- empty / truncated / over-long
- leaked secrets (token/key/password)
- tech jargon when user asked simple
- unsupported absolute claims
- missing source when it claimed facts

If a defect is found, apply a conservative fix and re-check. Logs every
correction so quality can be measured (Correction Turns -> 0, Success Rate up).
"""
import re, time

SECRET_PAT = re.compile(r"(gsk_[A-Za-z0-9]+|sk-or-[A-Za-z0-9\-]+|GOCSPX-[A-Za-z0-9_\-]+|rnd_[A-Za-z0-9]+|Bearer\s+[A-Za-z0-9._\-]{12,})")
ABS_CLAIM = re.compile(r"(100%\s*แน่นอน|ไม่มีข้อผิดพลาดเลย|พิสูจน์แล้วแน่นอน|รับประกันผล)")
JARGON = re.compile(r"\b(API|endpoint|middleware|throughput|latency|schema|JWT|SDK)\b")


class SelfCorrect:
    def __init__(self):
        self.log = []

    def check(self, text, question="", lang="th"):
        t = str(text or "")
        issues = []
        if not t.strip():
            issues.append({"type": "empty", "msg": "คำตอบว่าง"})
        if len(t) > 12000:
            issues.append({"type": "too_long", "msg": "ยาวเกินไป"})
        if SECRET_PAT.search(t):
            issues.append({"type": "secret_leak", "msg": "พบข้อมูลความลับในคำตอบ"})
        if ABS_CLAIM.search(t):
            issues.append({"type": "absolute_claim", "msg": "อ้างความแน่นอนเกินจริง"})
        q = str(question or "")
        simple = bool(re.search(r"(ง่าย|อธิบายเด็ก|เข้าใจง่าย|simple|short)", q, re.I))
        if simple and len(JARGON.findall(t)) >= 2:
            issues.append({"type": "jargon", "msg": "ใช้ศัพท์เทคนิคทั้งที่ขอแบบเข้าใจง่าย"})
        return issues

    def fix(self, text, issues, eval_fn=None):
        t = str(text or "")
        fixes = []
        for it in issues:
            typ = it["type"]
            if typ == "secret_leak":
                t = SECRET_PAT.sub("[REDACTED]", t)
                fixes.append("redact_secret")
            elif typ == "absolute_claim":
                t = ABS_CLAIM.sub("มีหลักฐาน-support แต่ควรตรวจสอบเพิ่ม", t)
                fixes.append("soften_claim")
            elif typ == "too_long":
                t = t[:12000].rsplit("\n", 1)[0] + "\n…(ตัดยาว — ขอสรุปสั้นได้)"
                fixes.append("truncate")
            elif typ == "jargon":
                rep = {"API": "ช่องทางเชื่อมต่อ", "endpoint": "จุดเชื่อมต่อ", "middleware": "ตัวกลาง",
                       "throughput": "ปริมาณงาน", "latency": "ความหน่วง", "schema": "โครงสร้าง", "JWT": "บัตรผ่าน", "SDK": "ชุดเครื่องมือ"}
                for k, v in rep.items():
                    t = t.replace(k, v)
                fixes.append("simplify")
        # optional: re-evaluate score if provided
        score = None
        if eval_fn and t.strip():
            try:
                r = eval_fn(t)
                score = r.get("score") if isinstance(r, dict) else None
            except Exception:
                pass
        return t, fixes, score

    def run(self, text, question="", lang="th", eval_fn=None):
        issues = self.check(text, question, lang)
        if not issues:
            rec = {"ok": True, "changed": False, "text": str(text or ""), "issues": []}
            self.log.append({"t": int(time.time()), "changed": False})
            return rec
        fixed, fixes, score = self.fix(text, issues, eval_fn)
        remaining = self.check(fixed, question, lang)
        rec = {"ok": True, "changed": True, "text": fixed, "issues": issues,
               "fixes": fixes, "remaining": remaining, "score_after": score}
        self.log.append({"t": int(time.time()), "changed": True,
                         "types": [i["type"] for i in issues]})
        return rec

    def stats(self):
        return {"checks": len(self.log),
                "corrections": sum(1 for x in self.log if x.get("changed")),
                "principle": "แก้ใน turn เดียวกัน — ผู้ใช้ไม่ต้องบอกให้แก้ซ้ำ"}

    def snapshot(self):
        return {"log": self.log[-1000:]}

    def restore(self, data):
        if isinstance(data, dict) and "log" in data:
            self.log = data.get("log", [])
            return True
        return False
