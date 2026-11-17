"""Zyphere Safety & Ethics Decision-Rule Engine - Zyphere's own #1 gap.

Real-time policy enforcement: blacklist/whitelist, rule evaluation over
proposed actions/text, privacy guard, and an auditable decision log.

Owner's absolute rules: no gambling, no illegal activity, no fake claims,
no auto account creation where OTP/identity required, respect copyright.
"""
import os, json, time, threading, re

# Hard rules — absolute (from owner's ethics directives)
ABS_BLACKLIST = [
    (r"(เว็บพนัน|บาคาร่า|สล็อต|casino|gambling|betting)", "gambling", "งดเด็ดขาด: เว็บพนัน"),
    (r"(ฆ่า|ทำร้าย|อาวุธปืน|ระเบิด|ยาเสพติด|illegal|ผิดกฎหมาย)", "illegal", "งดเด็ดขาด: สิ่งผิดกฎหมาย"),
    (r"(ข้ามจ่ายเงิน|bypass paywall|ละเมิดลิขสิทธิ์|แฮ็ก|ขโมย)", "copyright_or_security", "งด: ละเมิดสิทธิ์/ความปลอดภัย"),
    (r"(ให้คุณสมัคร|สร้างบัญชี|กรอก OTP แทน)", "identity", "ต้อง OTP/ตัวตนของเจ้าของ — ทำแทนไม่ได้"),
]

# Soft rules — warn / require confirmation
SOFT_RULES = [
    (r"(ส่งเมล|โพสต์|โอนเงิน|ซื้อ|จ่าย)", "external_action", "การกระทำภายนอกต้องเจ้าของยืนยัน"),
    (r"(ข้อมูลส่วนตัว|รหัสผ่าน|token|secret)", "privacy", "ห้ามเปิดเผยข้อมูลส่วนตัว/ความลับ"),
]


class SafetyEngine:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.log = []
        self.rules = self._default_rules()
        self._load()

    def _default_rules(self):
        return [{"pattern": p, "id": i, "msg": m, "hard": True}
                for p, i, m in ABS_BLACKLIST] + [
                {"pattern": p, "id": i, "msg": m, "hard": False}
                for p, i, m in SOFT_RULES]

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.log = d.get("log", [])
            if d.get("rules"):
                self.rules = d.get("rules")
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"rules": self.rules, "log": self.log[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def evaluate(self, text, context=""):
        """Check a proposed action/text against all rules. Returns decision.

        IMPORTANT: only block clear INTENTS, not mere mentions. A question that
        says the word 'ผิดกฎหมาย' to ask ABOUT it is not an illegal action.
        """
        t = str(text or "")
        # meta/discussion context (asking about rules, safety, learning) is allowed
        meta = bool(re.search(r"(ขาดอะไร|พัฒนา|เรียนรู้|อธิบาย|หมายความว่าอะไร|study|reflect|rule|safety|ตรวจสอบ|evaluation)", t, re.I))
        hits_hard, hits_soft = [], []
        for r in self.rules:
            if re.search(r["pattern"], t, re.I):
                (hits_hard if r.get("hard") else hits_soft).append(r)
        # if it's clearly a discussion/meta question, demote hard blocks to allow
        if meta and context in ("", "chat", "ask"):
            hits_hard = []
        decision = "BLOCK" if hits_hard else ("CONFIRM" if hits_soft and not meta else "ALLOW")
        rec = {"decision": decision, "text": t[:300], "context": str(context or "")[:120],
               "hard": [r["id"] for r in hits_hard], "soft": [r["id"] for r in hits_soft],
               "message": ("；".join(r["msg"] for r in hits_hard + hits_soft) or "ผ่านการตรวจสอบ"),
               "t": int(time.time())}
        with self.lock:
            self.log.append(rec)
        self.save()
        return {"ok": True, **rec}

    def add_rule(self, pattern, rule_id, message, hard=False):
        with self.lock:
            self.rules.append({"pattern": str(pattern)[:300], "id": str(rule_id)[:60],
                               "msg": str(message)[:200], "hard": bool(hard)})
        self.save()
        return {"ok": True, "rules": len(self.rules)}

    def stats(self):
        with self.lock:
            return {"rules": len(self.rules), "checks": len(self.log),
                    "blocked": sum(1 for x in self.log if x.get("decision") == "BLOCK")}

    def snapshot(self):
        with self.lock:
            return {"rules": self.rules, "log": self.log[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "rules" in data:
                self.rules = data.get("rules", self.rules)
                self.log = data.get("log", [])
                self.save()
                return True
        return False
