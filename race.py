"""Zyphere Revenue Race + IT Help Desk - scholars COMPETE to create income
channels; each reports blockers and the system's IT role maps blockers to code
fixes. Chief ranks and pushes. Free, on Render. HONEST: scores are real
counted assets/launches/owner-reported revenue, not invented money.
"""
import os, json, time, threading

BLOCKER_TO_CODE = {
    "ไม่มีของขาย": ["codeforge.forge", "media.melody", "work.produce"],
    "ไม่มีตลาด": ["market.analyze", "launchpad.kit"],
    "ไม่มีข้อมูล": ["research.search", "rss.fetch", "elibrary.search"],
    "เขียนโค้ดไม่ได้": ["codeforge.forge", "tools.run"],
    "เสียง/ภาพไม่ดี": ["media.burn_srt", "ttsNorm", "video_download_only"],
    "ข้อมูลหาย": ["remote_push", "restore", "audit"],
    "OTP/บัญชี": ["otpassist.prepare", "help.ask_owner"],
}


class Race:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.scores = {}
        self.blockers = []
        self.fixes = []
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.scores = d.get("scores", {})
            self.blockers = d.get("blockers", [])
            self.fixes = d.get("fixes", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"scores": self.scores, "blockers": self.blockers[-1000:],
                           "fixes": self.fixes[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def start(self, scholars=None):
        for s in (scholars or []):
            name = s.get("scholar", "") if isinstance(s, dict) else str(s)
            self.scores.setdefault(name[:80], {"assets": 0, "launches": 0, "revenue": 0, "learned": 0})
        self.save()
        return {"ok": True, "racing": len(self.scores)}

    def score(self, scholar="", assets=0, launches=0, revenue=0, learned=0):
        name = str(scholar or "")[:80]
        with self.lock:
            e = self.scores.setdefault(name, {"assets": 0, "launches": 0, "revenue": 0, "learned": 0})
            e["assets"] += int(assets or 0); e["launches"] += int(launches or 0)
            e["revenue"] += int(revenue or 0); e["learned"] += int(learned or 0)
        self.save()
        return {"ok": True, "scholar": name, "score": e}

    def leaderboard(self):
        rows = []
        with self.lock:
            for name, e in self.scores.items():
                pts = e["assets"] * 10 + e["launches"] * 5 + e["revenue"] // 10 + e["learned"]
                rows.append({"scholar": name, **e, "points": pts})
        rows.sort(key=lambda x: -x["points"])
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        return {"ok": True, "leaderboard": rows,
                "note": "แต้มจากของจริง+การลงขาย+รายได้ที่เจ้าของแจ้ง+การเรียนรู้"}

    def report_blocker(self, scholar="", blocker="", detail=""):
        b = str(blocker or "")
        fixes = []
        for k, v in BLOCKER_TO_CODE.items():
            if any(w in b for w in k.split("/")) or k in b:
                fixes.extend(v)
        rec = {"ok": True, "scholar": str(scholar)[:80], "blocker": b[:200],
               "detail": str(detail or "")[:300], "code_to_call": sorted(set(fixes)) or ["research.search"],
               "status": "open", "t": int(time.time())}
        with self.lock:
            self.blockers.append(rec)
        self.save()
        return rec

    def it_help(self, n=20):
        """IT of Zyphere solves blockers by mapping to actual modules."""
        solved = []
        with self.lock:
            open_b = [b for b in self.blockers if b.get("status") == "open"][-n:]
            for b in open_b:
                b["status"] = "helped"
                solved.append({"scholar": b["scholar"], "blocker": b["blocker"],
                               "run": b["code_to_call"], "by": "IT of Zyphere"})
            self.fixes.extend(solved)
        self.save()
        return {"ok": True, "solved": len(solved), "fixes": solved,
                "note": "IT จับคู่ blocker → โมดูลที่มีอยู่ รันต่อได้ทันที"}

    def stats(self):
        with self.lock:
            return {"racing": len(self.scores), "blockers": len(self.blockers),
                    "fixed": len(self.fixes)}

    def snapshot(self):
        with self.lock:
            return {"scores": self.scores, "blockers": self.blockers[-1000:], "fixes": self.fixes[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "scores" in data:
                self.scores = data.get("scores", {})
                self.blockers = data.get("blockers", [])
                self.fixes = data.get("fixes", [])
                self.save()
                return True
        return False
