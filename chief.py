"""Zyphere Chief of Staff - THE missing head: thinks for itself, self-triggers,
and directs the 46 scholars + 6 agents + all modules WITHOUT waiting for orders.

Call it: "หัวหน้า" / "ผู้คุมงาน" / "Chief of Staff" / "COO" of Zyphere.

Loop: observe -> decide -> dispatch -> verify -> report. Runs on Render via
the keepalive cron (GitHub Actions every 10 min already hits /api/learn/tick).
Owner can check /api/chief/status anytime, or just let it run.

HONEST: autonomous WITHIN Zyphere's own system. Cannot create accounts/OTP/
touch bank (owner only). No gambling/illegal. Reports real numbers only.
"""
import os, json, time, threading

NAME = "หัวหน้าคุมงาน Zyphere (Chief of Staff)"


class Chief:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.cycles = []
        self.last_tick = 0
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.cycles = d.get("cycles", [])
            self.last_tick = d.get("last_tick", 0)
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"cycles": self.cycles[-500:], "last_tick": self.last_tick},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def identity(self):
        return {"ok": True, "name": NAME, "role": "คิดเอง สั่งงานเอง ตรวจเอง รายงานเจ้าของ",
                "triggers": ["cron ทุก 10 นาที (/api/learn/tick)", "เจ้าของพิมพ์ /api/chief/run",
                             "เหตุการณ์ในระบบ (ของใหม่/ออเดอร์/ภัย)"],
                "commands": ["observe", "decide", "dispatch", "verify", "report"]}

    def observe(self, state=None):
        s = state or {}
        seen = {
            "knowledge": s.get("knowledge", 0),
            "products": s.get("products", 0),
            "graduates": s.get("graduates", 0),
            "launches": s.get("launches", 0),
            "orders": s.get("orders", 0),
            "alerts": s.get("alerts", 0),
            "remote": bool(s.get("remote", False)),
        }
        gaps = []
        if not seen["remote"]:
            gaps.append("remote KV ปิด")
        if seen["products"] < 46:
            gaps.append("ผลิตของไม่ครบ 46")
        if seen["graduates"] < 46:
            gaps.append("นักวิชาการยังฝึกไม่ครบ")
        if seen["launches"] < 46:
            gaps.append("ยังลงแพลตฟอร์มไม่ครบ")
        return {"ok": True, "seen": seen, "gaps": gaps}

    def decide(self, state=None):
        obs = self.observe(state)
        actions = []
        for g in obs["gaps"]:
            if "remote" in g:
                actions.append({"do": "alert_owner", "why": g, "priority": 0})
            elif "ผลิต" in g:
                actions.append({"do": "study_scholars", "why": g, "priority": 1})
            elif "ฝึก" in g:
                actions.append({"do": "enroll_academy", "why": g, "priority": 2})
            elif "ลงแพลตฟอร์ม" in g:
                actions.append({"do": "launch_marketplace", "why": g, "priority": 3})
        if not actions:
            actions = [{"do": "research_more", "why": "ทุกอย่างครบ — ขยายความรู้/หาตลาดเพิ่ม", "priority": 4}]
        actions.sort(key=lambda x: x["priority"])
        return {"ok": True, "next": actions[0], "plan": actions, "gaps": obs["gaps"]}

    def run_cycle(self, state=None, dispatch=None):
        """observe -> decide -> dispatch -> verify -> record. Self-triggered."""
        dec = self.decide(state)
        result = None
        if dispatch and dec.get("next"):
            try:
                result = dispatch(dec["next"]["do"], state)
            except Exception as e:
                result = {"ok": False, "error": str(e)[:150]}
        rec = {"ok": True, "ts": int(time.time()), "cycle": len(self.cycles) + 1,
               "decision": dec.get("next"), "gaps": dec.get("gaps", []),
               "result": (str(result)[:300] if result else "dispatched by caller"),
               "by": NAME}
        with self.lock:
            self.cycles.append(rec)
            self.last_tick = int(time.time())
        self.save()
        return rec

    def status(self):
        with self.lock:
            return {"ok": True, "name": NAME, "cycles": len(self.cycles),
                    "last_tick": self.last_tick,
                    "autonomous": True,
                    "latest": self.cycles[-1] if self.cycles else None,
                    "note": "ไม่ต้องรอคำสั่ง — cron กระตุ้นเองทุก 10 นาที"}

    def history(self, n=10):
        with self.lock:
            return list(reversed(self.cycles[-n:]))

    def snapshot(self):
        with self.lock:
            return {"cycles": self.cycles[-500:], "last_tick": self.last_tick}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "cycles" in data:
                self.cycles = data.get("cycles", [])
                self.last_tick = data.get("last_tick", 0)
                self.save()
                return True
        return False
