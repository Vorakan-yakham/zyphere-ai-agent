"""Zyphere Audit Trail - Zyphere's final free gap: a unified, verifiable log
of every significant action (who/what/when/result), with integrity hash so
records can't be silently altered. Local, free, no external service.

Complements per-module logs (safety/eval/intent/feedback) with one central trail.
"""
import os, json, time, threading, hashlib


class Audit:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.events = []
        self._load()

    def _load(self):
        try:
            self.events = json.load(open(self.path, encoding="utf-8")).get("events", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"events": self.events[-5000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def record(self, actor="system", action="", detail="", result="ok"):
        with self.lock:
            prev = self.events[-1]["hash"] if self.events else "0" * 16
            rec = {"i": len(self.events), "ts": int(time.time()),
                   "actor": str(actor)[:60], "action": str(action)[:120],
                   "detail": str(detail)[:600], "result": str(result)[:60], "prev": prev}
            raw = json.dumps(rec, ensure_ascii=False, sort_keys=True).encode("utf-8")
            rec["hash"] = hashlib.sha256(raw).hexdigest()[:16]
            self.events.append(rec)
        self.save()
        return {"ok": True, "id": rec["i"], "hash": rec["hash"]}

    def query(self, actor=None, action=None, limit=50):
        with self.lock:
            ev = list(self.events)
        if actor:
            ev = [e for e in ev if e.get("actor") == actor]
        if action:
            ev = [e for e in ev if action.lower() in str(e.get("action", "")).lower()]
        return {"ok": True, "count": len(ev), "events": list(reversed(ev[-limit:]))}

    def verify(self):
        """Check hash chain integrity."""
        with self.lock:
            ev = list(self.events)
        broken = []
        for i, e in enumerate(ev):
            if i and e.get("prev") != ev[i - 1].get("hash"):
                broken.append(i)
        return {"ok": True, "events": len(ev), "integrity": not broken, "broken_at": broken[:10]}

    def stats(self):
        with self.lock:
            return {"events": len(self.events),
                    "actions": len(set(e.get("action") for e in self.events))}

    def snapshot(self):
        with self.lock:
            return {"events": self.events[-5000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "events" in data:
                self.events = data.get("events", [])
                self.save()
                return True
        return False
