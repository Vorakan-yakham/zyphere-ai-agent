"""Zyphere Billing - subscription (Pro) + PromptPay orders, offline-friendly.
Payments verified by user-submitted slip ref (manual confirm), then entitlement auto-granted.
"""
import json, os, time, threading, secrets

PLANS = {
    "free": {"price": 0, "name": "ฟรี", "perks": ["แชทพื้นฐาน", "ความจำถาวร", "เรียนรู้เอง"]},
    "pro": {"price": 199, "name": "Pro รายเดือน", "perks": [
        "โควต้า AI ไม่จำกัด", "สร้างวิดีโอเพิ่ม", "เสียงพูดพรีเมียม",
        "วิเคราะห์เชิงลึก", "ผู้ช่วยส่วนตัวขั้นสูง"]},
    "lifetime": {"price": 1990, "name": "Lifetime", "perks": [
        "ฟีเจอร์ Pro ทั้งหมดตลอดชีวิต", "อัปเดตฟรี", "สนับสนุนการพัฒนาโดยตรง"]},
}

class Billing:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.orders = []
        self.subs = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.orders = d.get("orders", [])
            self.subs = d.get("subs", {})
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump({"orders": self.orders[-1000:], "subs": self.subs},
                              f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def create_order(self, email, plan, ref=""):
        if plan not in PLANS:
            return {"ok": False, "error": "invalid plan"}
        oid = "ZY-" + secrets.token_hex(4).upper()
        with self.lock:
            self.orders.append({"id": oid, "email": str(email or "guest"),
                                "plan": plan, "amount": PLANS[plan]["price"],
                                "ref": str(ref or "")[:120], "status": "pending",
                                "t": int(time.time())})
            self.save()
        return {"ok": True, "id": oid, "amount": PLANS[plan]["price"],
                "promptpay": "0941939686", "kbank": "007 8 468 262"}

    def confirm(self, oid):
        with self.lock:
            for o in self.orders:
                if o["id"] == oid:
                    if o["status"] == "paid":
                        return {"ok": True, "already": True}
                    o["status"] = "paid"
                    o["paid_at"] = int(time.time())
                    email, plan = o["email"], o["plan"]
                    months = 1 if plan == "pro" else (120 if plan == "lifetime" else 0)
                    if months and email in self.subs:
                        prev = self.subs[email]
                        prev["until"] = max(int(prev.get("until") or 0), int(time.time())) + months * 30 * 86400
                        prev["plan"] = plan
                    elif months:
                        self.subs[email] = {"plan": plan, "until": int(time.time()) + months * 30 * 86400}
                    self.save()
                    return {"ok": True, "email": email, "plan": plan,
                            "until": self.subs.get(email, {}).get("until")}
        return {"ok": False, "error": "order not found"}

    def status(self, email):
        s = self.subs.get(str(email or ""))
        if not s:
            return {"plan": "free", "active": False}
        active = int(s.get("until") or 0) > int(time.time())
        return {"plan": s.get("plan"), "active": active,
                "until": s.get("until")}

    def stats(self):
        return {"orders": len(self.orders),
                "paid": len([o for o in self.orders if o["status"] == "paid"]),
                "subscribers": len(self.subs),
                "revenue": sum(o["amount"] for o in self.orders if o["status"] == "paid")}
