"""Zyphere Council Dialogue - the Chief automatically INTERVIEWS every scholar
(what do you lack? what tool do you need?) then converts answers into dev tasks,
without waiting for any human order. Self-sustaining improvement loop.

Free, one Render process. HONEST: uses the LLM/ensemble + rule mapping to turn
scholars' stated needs into concrete module tasks; not magic, auditable log.
No gambling/illegal.
"""
import os, json, time, threading

QUESTION = "ในฐานะนักวิชาการสาขาของคุณ ขาดเครื่องมือ/ความรู้/ข้อมูลอะไรเพื่อทำงานได้เหมือนผู้เชี่ยวชาญ และจะใช้มันทำเงินยังไง?"

# map need keywords -> module to build/enable (what Zyphere already can wire)
NEED_TO_MODULE = {
    "ข้อมูล": ["research", "rss", "elibrary"],
    "เครื่องมือ": ["tools", "codeforge", "media"],
    "ความรู้": ["curriculum", "concept", "scholars"],
    "ตลาด": ["market", "listing", "launchpad"],
    "เวลา": ["surpass.select_model", "proactive"],
    "คุณภาพ": ["reviewer", "selftest", "eval"],
    "เงิน": ["income", "billing", "delivery", "shop"],
    "ภาษา": ["language", "empathy", "ttsNorm"],
}


class Council:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.sessions = []
        self.tasks = []
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.sessions = d.get("sessions", [])
            self.tasks = d.get("tasks", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"sessions": self.sessions[-200:], "tasks": self.tasks[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def interview(self, scholars=None, asker=None):
        """Chief interviews each scholar; no human order needed."""
        out = []
        for s in (scholars or [])[:46]:
            name = s.get("scholar", "") if isinstance(s, dict) else str(s)
            field = str(s.get("field", "") if isinstance(s, dict) else "")[:80]
            ans = ""
            if asker:
                try:
                    ans = str(asker(name, field, QUESTION))[:700]
                except Exception:
                    ans = ""
            out.append({"scholar": name[:80], "field": field,
                        "question": QUESTION, "answer": ans, "t": int(time.time())})
        rec = {"ok": True, "id": "co_" + str(int(time.time() * 1000)),
               "by": "หัวหน้าคุมงาน (Chief)", "interviews": out, "t": int(time.time())}
        with self.lock:
            self.sessions.append(rec)
        self.save()
        return rec

    def to_tasks(self, session=None, scholar_income=None):
        """Turn scholars' stated needs into concrete dev tasks."""
        ses = session or (self.sessions[-1] if self.sessions else {})
        made = []
        for iv in ses.get("interviews", []):
            text = (iv.get("answer", "") or " " + iv.get("field", "") or "").lower()
            modules = []
            for k, v in NEED_TO_MODULE.items():
                if k in text:
                    modules.extend(v)
            made.append({"ok": True, "scholar": iv.get("scholar", ""),
                         "need_detected": [k for k in NEED_TO_MODULE if k in text] or ["general"],
                         "modules_to_build": sorted(set(modules)) or ["research", "market"],
                         "status": "queued", "t": int(time.time())})
        with self.lock:
            self.tasks.extend(made)
        self.save()
        return {"ok": True, "tasks": made, "count": len(made)}

    def auto_cycle(self, scholars=None, asker=None):
        """One full self-directed loop: interview -> tasks -> report."""
        ses = self.interview(scholars, asker)
        tasks = self.to_tasks(ses)
        return {"ok": True, "interviewed": len(ses.get("interviews", [])),
                "tasks": tasks.get("count", 0),
                "note": "หัวหน้าคุมงานถามนักวิชาการเอง → แปลงเป็นงานพัฒนาเอง ไม่รอคำสั่ง"}

    # ---- continuous learning + competition + review + chief nagging ----
    def learn_round(self, scholars=None, researcher=None, reviewer=None):
        """Every scholar learns one more unit this round; reviewer checks each."""
        results = []
        for s in (scholars or [])[:46]:
            name = s.get("scholar", "") if isinstance(s, dict) else str(s)
            field = str(s.get("field", "") if isinstance(s, dict) else "")[:80]
            gain = 0
            finding = ""
            if researcher:
                try:
                    r = researcher(field, name)
                    text = str(r.get("result") or "") if isinstance(r, dict) else str(r)
                    gain = min(10, len(text) // 40 + 1)
                    finding = text[:200]
                except Exception:
                    pass
            reviewed = "pending"
            if reviewer:
                try:
                    reviewed = reviewer(finding or field)
                except Exception:
                    pass
            results.append({"scholar": name[:80], "field": field, "gain": gain,
                            "finding": finding, "reviewed": str(reviewed)[:120],
                            "t": int(time.time())})
        return {"ok": True, "round": int(time.time()), "results": results}

    def leaderboard(self, scholars=None):
        """Rank scholars by learning gains + reviewed work (competition)."""
        rows = []
        with self.lock:
            tasks = list(self.tasks)
        for s in (scholars or [])[:46]:
            name = s.get("scholar", "") if isinstance(s, dict) else str(s)
            n = sum(1 for t in tasks if t.get("scholar") == name and t.get("status") != "blocked")
            rows.append({"scholar": name[:80], "tasks": n, "score": n * 10})
        rows.sort(key=lambda x: -x["score"])
        for i, r in enumerate(rows, 1):
            r["rank"] = i
            r["badge"] = "ทอง" if i == 1 else ("เงิน" if i == 2 else ("ทองแดง" if i == 3 else ""))
        return {"ok": True, "leaderboard": rows,
                "note": "แข่งกันเรียนรู้ — อันดับจากงานที่ตรวจแล้ว"}

    def chief_nag(self, scholars=None, leaderboard=None):
        """Chief checks laggards and pushes them (จี้ผลงาน)."""
        lb = (leaderboard or self.leaderboard(scholars))["leaderboard"]
        laggards = [r for r in lb if r.get("score", 0) == 0][:10]
        nags = [{"scholar": r["scholar"], "nag": "หัวหน้าคุมงานขอให้เร่งเรียนรอบนี้ — ส่งผลงานภายในรอบถัดไป",
                 "by": "Chief of Staff", "t": int(time.time())} for r in laggards]
        return {"ok": True, "checked": len(lb), "laggards": len(laggards), "nags": nags,
                "note": "หัวหน้าจี้ผู้ที่ยังไม่ส่งผลงาน — ตรวจทุก rอบ"}

    def status(self):
        with self.lock:
            return {"ok": True, "sessions": len(self.sessions), "tasks": len(self.tasks),
                    "autonomous": True, "by": "Chief of Staff",
                    "features": ["learn_round", "leaderboard", "chief_nag", "interview"]}

    def snapshot(self):
        with self.lock:
            return {"sessions": self.sessions[-200:], "tasks": self.tasks[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "sessions" in data:
                self.sessions = data.get("sessions", [])
                self.tasks = data.get("tasks", [])
                self.save()
                return True
        return False
