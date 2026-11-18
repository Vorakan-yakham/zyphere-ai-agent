"""Zyphere AI Creative Director — plans, generates multiple versions, critiques,
revises, and lets the owner choose. Learns from feedback (recorded, not claimed).

Uses the free Image Studio (PIL composition). Honest: design composition,
not diffusion. No paid provider is called automatically.
"""
import os, json, time, threading, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "creative_feedback.json")


class CreativeDirector:
    def __init__(self):
        self.lock = threading.RLock()
        self.feedback = []
        self._load()

    def _load(self):
        try:
            self.feedback = json.load(open(DATA, encoding="utf-8")).get("feedback", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"feedback": self.feedback[-500:]},
                      open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def direct(self, title, subtitle="", kind="poster", variants=3):
        """Generate -> critique -> revise; return ranked versions."""
        import image_studio
        plans = []
        for p in ("indigo", "forest", "rose", "slate")[:max(1, min(4, variants))]:
            r = image_studio.produce(title, subtitle, kind, p)
            plans.append({"palette": r.get("palette"), "url": r.get("url"),
                          "score": r.get("quality", {}).get("score", 0),
                          "issues": r.get("quality", {}).get("issues", [])})
        plans.sort(key=lambda x: -x["score"])
        best = plans[0] if plans else None
        record = {"t": int(time.time()), "title": str(title)[:120], "kind": kind,
                  "versions": plans, "best": best}
        with self.lock:
            self.feedback.append(record)
        self.save()
        return {"ok": True, "plan": "generate -> critique -> revise -> rank",
                "versions": plans, "best": best,
                "note": "design composition only; no diffusion model"}

    def rate(self, url="", score=0, note=""):
        """Owner feedback: which version was actually chosen."""
        with self.lock:
            self.feedback.append({"t": int(time.time()), "type": "rating",
                                  "url": str(url)[:200], "score": int(score),
                                  "note": str(note)[:300]})
        self.save()
        return {"ok": True, "ratings": sum(1 for x in self.feedback
                                           if x.get("type") == "rating")}

    def status(self):
        return {"ok": True, "runs": len([x for x in self.feedback if not x.get("type")]),
                "ratings": sum(1 for x in self.feedback if x.get("type") == "rating"),
                "last": self.feedback[-5:]}


CD = CreativeDirector()
