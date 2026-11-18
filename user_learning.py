"""Zyphere User Learning — the more people use it, the more it learns.

Every interaction/feedback is recorded and taught into LocalBrain/DevBrain.
Learning accumulates; when a threshold is reached it requests a self-code cycle
(handled by the JARVIS loop, rate-limited and guarded).
"""
import os, json, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "user_learning.json")
THRESHOLD = 20  # feedback items before requesting a self-update


class UserLearning:
    def __init__(self):
        self.lock = threading.RLock()
        self.events = []
        self._load()

    def _load(self):
        try:
            self.events = json.load(open(DATA, encoding="utf-8")).get("events", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"events": self.events[-2000:]},
                      open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def record(self, text="", rating=0, source="user", tag=""):
        ev = {"t": int(time.time()), "text": str(text)[:600],
              "rating": int(rating or 0), "source": str(source)[:60],
              "tag": str(tag)[:60]}
        with self.lock:
            self.events.append(ev)
        self.save()
        taught = False
        if ev["text"]:
            lesson = ("ผู้ใช้สอน Zyphere: " + ev["text"] +
                      (" [ชอบ]" if ev["rating"] > 0 else
                       " [ไม่ชอบ]" if ev["rating"] < 0 else ""))
            try:
                from local_brain import LocalBrain
                from dev_brain import DevBrain
                LocalBrain(os.path.join(ROOT, "data", "local_brain.json")).learn_text(
                    lesson, source="user:" + ev["source"])
                DevBrain(os.path.join(ROOT, "data", "dev_brain.json")).experience(
                    lesson, role="user:" + ev["source"])
                taught = True
            except Exception:
                pass
        return {"ok": True, "taught": taught,
                "total": len(self.events),
                "update_due": len(self.events) % THRESHOLD == 0 and len(self.events) > 0}

    def status(self):
        return {"ok": True, "events": len(self.events), "threshold": THRESHOLD,
                "update_due": len(self.events) % THRESHOLD == 0 and len(self.events) > 0,
                "last": self.events[-10:]}


UL = UserLearning()
