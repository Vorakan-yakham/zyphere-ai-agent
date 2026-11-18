"""Zyphere Help Requests - 'ถ้าทำไม่ได้ ให้มาถาม แล้วแก้ไปด้วยกัน'.

When Zyphere hits a hard blocker (OTP, owner account, bank, money, hardware,
external platform), it does NOT fake success and does NOT bypass rules. It
creates a clear help request for the owner, and when solved, records the
solution so it learns and doesn't ask the same thing again.

Ethics: never ask for OTP/password/secrets to be given to AI — the request
tells the OWNER to do it themselves. No gambling/illegal. Free, local.
"""
import os, json, time, threading


class Help:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.requests = []
        self.solutions = []
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.requests = d.get("requests", [])
            self.solutions = d.get("solutions", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"requests": self.requests[-1000:], "solutions": self.solutions[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def ask(self, action="", blocker="", need="", context=""):
        """Create a help request when stuck. Honest about the blocker."""
        known = self._known(blocker)
        rec = {"ok": True, "id": "h_" + str(int(time.time() * 1000)),
               "action": str(action)[:160], "blocker": str(blocker)[:200],
               "need": str(need)[:300], "context": str(context)[:300],
               "status": "open" if not known else "has_known_solution",
               "known_solution": known, "t": int(time.time()),
               "message": ("ผมทำ '%s' ไม่ได้เพราะ '%s' — รบกวนเจ้าของช่วยดำเนินการส่วนที่ต้องใช้ตัวตน/OTP ด้วยตัวคุณครับ"
                           % (str(action)[:80], str(blocker)[:80]))}
        with self.lock:
            self.requests.append(rec)
        self.save()
        return rec

    def _known(self, blocker):
        b = str(blocker or "").lower()
        for s in self.solutions:
            if s.get("blocker", "").lower() in b and s.get("blocker"):
                return s.get("solution", "")
        return ""

    def resolve(self, rid="", solution="", blocker=""):
        """Owner solved it -> record so Zyphere learns the workaround."""
        with self.lock:
            for r in self.requests:
                if r["id"] == rid or (not rid and r["status"] == "open"):
                    r["status"] = "resolved"
                    r["resolved_at"] = int(time.time())
                    break
            self.solutions.append({"blocker": str(blocker or "")[:200],
                                   "solution": str(solution or "")[:500], "t": int(time.time())})
        self.save()
        return {"ok": True, "resolved": True, "learned": True}

    def pending(self, n=20):
        with self.lock:
            return [r for r in reversed(self.requests) if r.get("status") in ("open", "has_known_solution")][:n]

    def stats(self):
        with self.lock:
            return {"requests": len(self.requests), "open": len(self.pending()),
                    "solutions_learned": len(self.solutions)}

    def snapshot(self):
        with self.lock:
            return {"requests": self.requests[-1000:], "solutions": self.solutions[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "requests" in data:
                self.requests = data.get("requests", [])
                self.solutions = data.get("solutions", [])
                self.save()
                return True
        return False
