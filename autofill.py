"""Zyphere Autofill / Self-Directed Action - 'เปิดตาให้เขา แล้วให้เขาคิดเอง'.

Inside Zyphere's OWN app the agent can observe state (via API) and take the
next sensible action itself: e.g. if no briefing today -> generate; if no
products -> forge one; if guard has alerts -> alert owner; if knowledge gap ->
learn. This is autonomous agency WITHIN our system.

HONEST LIMIT: cannot fill forms on EXTERNAL platforms (Fastwork/Facebook/
bank) — those need owner's account/OTP. Never claim otherwise. No gambling/
illegal. Owner can stop anytime.
"""
import os, json, time, threading


class Autofill:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.actions = []
        self._load()

    def _load(self):
        try:
            self.actions = json.load(open(self.path, encoding="utf-8")).get("actions", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"actions": self.actions[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def observe(self, state=None):
        """Zyphere 'opens its eyes' on its own app state."""
        s = state or {}
        seen = {
            "has_briefing": bool(s.get("briefings", 0)),
            "has_products": bool(s.get("products", 0)),
            "has_knowledge": bool(s.get("knowledge", 0)),
            "has_alerts": bool(s.get("alerts", 0)),
            "has_pending_orders": bool(s.get("pending_orders", 0)),
            "remote_ok": bool(s.get("remote", False)),
        }
        return {"ok": True, "seen": seen, "t": int(time.time())}

    def decide(self, state=None):
        """Think for itself: pick ONE next best action from observed state."""
        obs = self.observe(state)["seen"]
        plan = []
        if not obs["remote_ok"]:
            plan.append({"action": "alert_owner", "why": "Remote KV ปิด — เสี่ยงข้อมูลหาย", "priority": 1})
        if not obs["has_knowledge"]:
            plan.append({"action": "learn", "why": "ความรู้ยังน้อย — ควรเรียนเพิ่ม", "priority": 2})
        if not obs["has_briefing"]:
            plan.append({"action": "briefing", "why": "ยังไม่มีรายงานประจำวัน — ควรสรุปให้เจ้าของ", "priority": 3})
        if not obs["has_products"]:
            plan.append({"action": "forge_code", "why": "ยังไม่มีของขาย — ควรเขียนโค้ดผลิตสินค้า", "priority": 4})
        if obs["has_pending_orders"]:
            plan.append({"action": "deliver", "why": "มีออเดอร์รอส่งของ — ควรส่งมอบ", "priority": 0})
        if obs["has_alerts"]:
            plan.append({"action": "notify_owner", "why": "ยามพบเหตุการณ์ — ควรแจ้งเจ้าของ", "priority": 0})
        plan.sort(key=lambda x: x["priority"])
        return {"ok": True, "next": plan[0] if plan else {"action": "idle", "why": "ทุกอย่างปกติ เรียนรู้ต่อBackground"},
                "all": plan, "autonomous": True}

    def record_action(self, action, why, result="done"):
        rec = {"ok": True, "action": str(action)[:60], "why": str(why)[:200],
               "result": str(result)[:200], "t": int(time.time())}
        with self.lock:
            self.actions.append(rec)
        self.save()
        return rec

    def log(self, n=20):
        with self.lock:
            return {"ok": True, "actions": list(reversed(self.actions[-n:]))}

    def snapshot(self):
        with self.lock:
            return {"actions": self.actions[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "actions" in data:
                self.actions = data.get("actions", [])
                self.save()
                return True
        return False
