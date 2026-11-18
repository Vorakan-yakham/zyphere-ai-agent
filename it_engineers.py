"""Zyphere IT Engineers — one coding engineer per division.

The single self-coder was a bottleneck: it picked files at random. This adds
12 named engineers, each owning the code of one division. They propose in
parallel (dry) and the best guarded patches are applied in rotation, so code
improvement is broader and faster while every patch still passes the same
compile -> regression -> push -> revert gates.

HONEST: an engineer counts as successful only when self_coder reports a pushed
commit. Dry proposals are not counted as work done.
"""
import os, json, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "it_engineers.json")

# (division, owner role, file owned, what it must improve)
ENGINEERS = [
    ("01 Global Intelligence", "วิศวกรข้อมูล", "app.py", "route/status ให้ตรงข้อมูลจริง"),
    ("02 Scientific Discovery", "วิศวกรวิจัย", "research.py", " investigations ที่มีแหล่งจริง"),
    ("03 Simulation", "วิศวกรทดสอบ", "music_studio.py", "สร้างไฟล์จริงและตรวจได้"),
    ("04 Knowledge Systems", "วิศวกรความรู้", "autonomous_council.py", "สภาฯ/การแข่งขัน/ความจำ"),
    ("05 Learning", "วิศวกรการเรียนรู้", "dev_brain.py", "ดึงบทเรียนเก่ากลับมาใช้"),
    ("06 Engineering", "วิศวกรโครงสร้าง", "supervisors.py", "หัวหน้าฝ่ายกระตุ้นได้จริง"),
    ("07 Quality", "วิศวกรคุณภาพ", "quality_ops.py", "gate ไม่ผ่านห้ามปล่อยของ"),
    ("08 Product Design", "วิศวกรออกแบบ", "image_studio.py", "ภาพ/ปกที่ตรวจได้"),
    ("09 Market & Revenue", "วิศวกรรายได้", "store.py", "ลิงก์ไฟล์/ราคา/จ่ายตรงกัน"),
    ("10 Operations", "วิศวกรปฏิบัติการ", "division_heads.py", "หัวหน้าแผนกกดดันหัวหน้าฝ่าย"),
    ("11 Governance", "วิศวกรกำกับดูแล", "systems_analyst.py", "ตรวจจุดอ่อนเพิ่ม"),
    ("12 Autonomy", "วิศวกร self-coding", "self_coder.py", "เพิ่มความเร็ว/ความปลอดภัยของ patch"),
]


class ITEngineers:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(DATA), exist_ok=True)
                json.dump({"log": self.log[-300:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _one(self, eng, dry):
        div, role, filename, focus = eng
        try:
            from self_coder import SelfCoder
            r = SelfCoder().cycle(filename=filename, dry=dry)
            return {"division": div, "engineer": role, "file": filename,
                    "goal": focus, "ok": bool(r.get("ok")),
                    "pushed": bool(r.get("ok") and not r.get("dry")),
                    "reason": str(r.get("reason") or "")[:160]}
        except Exception as e:
            return {"division": div, "engineer": role, "file": filename,
                    "ok": False, "pushed": False, "reason": str(e)[:120]}

    def run_all(self, dry=True):
        """Dry: 12 engineers propose in parallel. Real: rotate 2 patches per
        round so git commits never collide."""
        n = len(self.log)
        order = ENGINEERS[n % len(ENGINEERS):] + ENGINEERS[:n % len(ENGINEERS)]
        if not dry:
            # Apply only engineers whose guarded proposal actually passed.
            recent = next((x for x in reversed(self.log) if x.get("dry")), None)
            good = [e for e in ENGINEERS if any(
                r.get("file") == e[2] and r.get("ok")
                for r in (recent or {}).get("results", []))]
            order = good or order
        picked = order if dry else order[:2]
        if dry:
            results = []
            with ThreadPoolExecutor(max_workers=4) as ex:
                futs = [ex.submit(self._one, e, True) for e in picked]
                for f in as_completed(futs):
                    results.append(f.result())
        else:
            results = [self._one(e, False) for e in picked]
        with self.lock:
            self.log.append({"t": int(time.time()), "dry": dry,
                             "results": results,
                             "pushed": sum(1 for r in results if r.get("pushed"))})
        self.save()
        return {"ok": True, "engineers": len(ENGINEERS), "ran": len(results),
                "pushed": sum(1 for r in results if r.get("pushed")),
                "results": results}

    def assignments(self):
        """Who is stationed at which division, what they must deliver, and
        whether they have actually pushed a patch for that file."""
        done = {}
        for rnd in self.log:
            for r in rnd.get("results", []):
                if r.get("pushed"):
                    done.setdefault(r.get("file"), []).append(r.get("reason", "")[:100])
        return {"ok": True, "stations": [
            {"division": d, "engineer": role, "file": f, "needs": goal,
             "pushed": len(done.get(f, [])), "latest": done.get(f, [])[-1:]}
            for d, role, f, goal in ENGINEERS]}

    def status(self):
        last = self.log[-1] if self.log else {}
        return {"ok": True, "engineers": len(ENGINEERS), "rounds": len(self.log),
                "total_pushed": sum(x.get("pushed", 0) for x in self.log),
                "last": last.get("results", [])}


ITE = ITEngineers()
