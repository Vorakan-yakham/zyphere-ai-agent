"""Zyphere Division Heads — the layer ABOVE the ten department supervisors.

A supervisor nudges its own department. A division head audits the supervisors
themselves: are they producing NEW work, or repeating the same nudge? If a
supervisor is stale, the division head escalates and hands a concrete target
back down. This makes the organisation pressurise itself without an owner.

HONEST: escalation is a recorded decision based on measured results, not a
claim that work was done.
"""
import os, json, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "division_heads.json")

DIVISIONS = [
    ("01", "Global Intelligence Center", "ข้อมูล/ความรู้ต้องมีแหล่งจริง"),
    ("02", "Scientific Discovery Center", "ต้องมีการค้นคว้าใหม่ทุก رอบ"),
    ("03", "Advanced Simulation Center", "ต้องทดสอบสมมติฐานจริง"),
    ("04", "Knowledge Systems Division", "46 คณะ/184 สาขาต้องมีเนื้อหา"),
    ("05", "Learning & Development Division", "บทเรียนต้องถูกนำไปใช้ ไม่ใช่เขียนทิ้ง"),
    ("06", "Engineering Division", "ต้องมี patch ที่ push จริง"),
    ("07", "Quality Assurance Division", "gate ต้องผ่านก่อนขาย"),
    ("08", "Product Design Division", "หน้าร้าน/ปกต้องสวยและใช้ได้"),
    ("09", "Market & Revenue Division", "ราคา/โปรโม/ลิงก์ต้องตรงของจริง"),
    ("10", "Operations Division", "workflow/cron ต้องไม่ fail"),
    ("11", "Governance & Ethics Division", "ห้าม claim ปลอม/secret รั่ว"),
    ("12", "Autonomy Division", "ต้องพัฒนาตัวเองต่อเนื่องโดยไม่รอสั่ง"),
]

QUESTIONS = [
    "หัวหน้าฝ่ายคนไหนส่งงานซ้ำรอบนี้?",
    "ผลงานใหม่ที่วัดได้ของแผนกคืออะไร?",
    "มี obstacle อะไรที่ต้องยกระดับตอนนี้?",
    "รอบหน้าต้องดีกว่ารอบนี้ตรงไหน (ตัวเลข)?",
]


class DivisionHead:
    def __init__(self, code, name, kpi):
        self.code, self.name, self.kpi = code, name, kpi

    def review(self, results, selfcode, round_no):
        stale = [r for r in (results or []) if r.get("repeated") or not r.get("ok")]
        pushed = bool((selfcode or {}).get("ok") and not (selfcode or {}).get("dry"))
        ok = not stale and pushed
        q = QUESTIONS[round_no % len(QUESTIONS)]
        if stale:
            action = "เร่งหัวหน้าฝ่าย: " + ", ".join(x["dept"] for x in stale[:3]) + " — ต้องส่งหลักฐานใหม่"
        elif not pushed:
            action = "เร่ง self-coder: ยังไม่มี patch ที่ push จริงรอบนี้"
        else:
            action = "รักษาความเร็ว ตั้งเป้าสูงกว่ารอบก่อน"
        return {"code": self.code, "division": self.name, "kpi": self.kpi,
                "ok": ok, "question": q, "action": action,
                "stale_heads": [x.get("dept") for x in stale],
                "selfcode_pushed": pushed, "t": int(time.time())}


class DivisionHeads:
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

    def review_all(self, supervisor_results=None, selfcode=None):
        rnd = len(self.log)
        heads = [DivisionHead(*d).review(supervisor_results, selfcode, rnd) for d in DIVISIONS]
        with self.lock:
            self.log.append({"t": int(time.time()), "round": rnd, "results": heads})
        self.save()
        return {"ok": True, "count": len(heads), "round": rnd,
                "pressuring": sum(1 for h in heads if not h["ok"]),
                "results": heads}

    def status(self):
        last = self.log[-1] if self.log else {}
        return {"ok": True, "count": len(DIVISIONS), "rounds": len(self.log),
                "last": last.get("results", [])}


DH = DivisionHeads()
