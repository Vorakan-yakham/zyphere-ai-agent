"""Zyphere HR Head — allocates the right worker to the right division.

The organisation now has supervisors, division heads, IT engineers, editors
and auto-created capability modules. Without HR they overlap or sit idle.
This head reads the real roster, finds gaps/duplicates and assigns work by
actual file ownership. Missing capability is created through auto_staffing.
"""
import os, json, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "hr_head.json")

# (division, must-have capability, owner source)
ROSTER = [
    ("01 Global Intelligence", "data_route", "app.py"),
    ("02 Scientific Discovery", "research", "research.py"),
    ("03 Simulation", "media", "music_studio.py"),
    ("04 Knowledge Systems", "council", "autonomous_council.py"),
    ("05 Learning", "learning", "dev_brain.py"),
    ("06 Engineering", "supervision", "supervisors.py"),
    ("07 Quality", "quality_gate", "quality_ops.py"),
    ("08 Product Design", "editorial", "image_studio.py"),
    ("09 Market & Revenue", "income", "store.py"),
    ("10 Operations", "division_pressure", "division_heads.py"),
    ("11 Governance", "editorial", "systems_analyst.py"),
    ("12 Autonomy", "self_code", "self_coder.py"),
]


# Real, measurable work for a division that currently has no active output.
# No busywork: every task targets a file/artifact that can be verified.
WORK_BANK = {
    "01": ("ปรับ status/route ให้ตรงโค้ดจริง", "app.py"),
    "02": ("ค้นหาแหล่งอ้างอิงใหม่เพิ่มจาก SCHOLAR_RESEARCH.md", "SCHOLAR_RESEARCH.md"),
    "03": ("สร้างไฟล์สื่อจริงและตรวจว่าเปิดได้", "music_studio.py"),
    "04": ("ตรวจว่าสภาฯ ใช้ความจำรอบก่อนจริง", "autonomous_council.py"),
    "05": ("ตรวจว่า dev_brain ดึงบทเรียนเก่ากลับมาได้", "dev_brain.py"),
    "06": ("ให้หัวหน้าฝ่ายส่งหลักฐานใหม่ ไม่ใช่ action ซ้ำ", "supervisors.py"),
    "07": ("ปิดจุดอ่อนที่ QA ยังต่ำกว่าเป้า", "quality_ops.py"),
    "08": ("แก้ nav/theme ของหน้าร้านให้ตรงกัน", "ZY_TEMPLATE_V2.html"),
    "09": ("ตรวจราคา/ลิงก์/คำอธิบายให้ตรงของจริง", "PRODUCTS.md"),
    "10": ("ให้หัวหน้าแผนกกดดันหัวหน้าฝ่ายให้ตรงเวลา", "division_heads.py"),
    "11": ("ตรวจข้อความทุกฝ่ายกับ LanguageMastery", "EDITORIAL_REVIEW.md"),
    "12": ("เพิ่ม patch ที่ push จริงของ self_coder", "self_coder.py"),
}


class HRHead:
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
                json.dump({"log": self.log[-150:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _has(self, capability):
        p = os.path.join(ROOT, "generated", capability + ".py")
        return os.path.exists(p)

    def audit(self):
        rows = []
        for div, cap, src in ROSTER:
            exists = self._has(cap) or os.path.exists(os.path.join(ROOT, src))
            rows.append({"division": div, "capability": cap, "owner_file": src,
                         "staffed": exists,
                         "assignment": div + " → " + cap + " (" + src + ")"})
        return rows

    def create_work_orders(self, apply=True):
        """Idle divisions get REAL work from the bank, not headcount cuts."""
        stale = []
        try:
            from supervisors import SUP
            for x in (SUP.status().get("last") or []):
                if not x.get("ok"):
                    stale.append(x.get("dept"))
        except Exception:
            pass
        orders = []
        for div, cap, src in ROSTER:
            code = div[:2]
            task, target = WORK_BANK.get(code, ("ตรวจและพัฒนางานของฝ่าย", src))
            idle = any(k and (k in div or div.split()[1][:4] in k) for k in stale) or \
                not os.path.exists(os.path.join(ROOT, src))
            orders.append({"division": div, "task": task if idle else "รักษางานที่ทำอยู่",
                           "target": target, "idle": idle})
        if apply:
            md = ["# คำสั่งงานจากหัวหน้าฝ่ายบุคคล", "",
                  "ฝ่ายที่ยังไม่มีงานได้รับงานจริงที่ตรวจได้ — ไม่มีการยุบฝ่าย", ""]
            for o in orders:
                md += ["- **%s** → %s (`%s`)%s" % (
                    o["division"], o["task"], o["target"],
                    " [งานใหม่]" if o["idle"] else "")]
            p = os.path.join(ROOT, "governance", "HR_WORK_ORDERS.md")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write("\n".join(md) + "\n")
        return orders

    def assign(self, apply=True):
        created = []
        gaps = []
        for div, cap, src in ROSTER:
            if not self._has(cap) and not os.path.exists(os.path.join(ROOT, src)):
                gaps.append(cap)
        if gaps and apply:
            try:
                import auto_staffing
                auto_staffing.run(apply=True)
            except Exception:
                pass
        orders = self.create_work_orders(apply)
        rows = self.audit()
        result = {"ok": True, "t": int(time.time()), "head": "หัวหน้าฝ่ายบุคคล",
                  "staffed": sum(1 for r in rows if r["staffed"]),
                  "total": len(rows), "gaps": gaps,
                  "assignments": [r["assignment"] for r in rows],
                  "work_orders": [o for o in orders if o["idle"]],
                  "created": created}
        with self.lock:
            self.log.append(result)
        self.save()
        return result

    def signals(self):
        """Real workload evidence, not opinions."""
        s = {}
        try:
            from it_engineers import ITE
            s["engineer_pushes"] = ITE.status().get("total_pushed", 0)
        except Exception:
            s["engineer_pushes"] = 0
        try:
            from department_editors import ED
            last = ED.status().get("last") or []
            s["editor_issues"] = sum(len(x.get("issues", [])) for x in last)
        except Exception:
            s["editor_issues"] = 0
        try:
            from supervisors import SUP
            st = SUP.status()
            s["supervisor_rounds"] = st.get("rounds", 0)
            s["stale_heads"] = sum(1 for x in (st.get("last") or []) if not x.get("ok"))
        except Exception:
            s["supervisor_rounds"] = s["stale_heads"] = 0
        try:
            from self_coder import SC
            s["self_pushes"] = SC.status().get("pushed", 0)
        except Exception:
            s["self_pushes"] = 0
        s["staffed"] = sum(1 for r in self.audit() if r["staffed"])
        s["total"] = len(ROSTER)
        return s

    def analyze(self):
        """Decide what to ADD or CUT using real workload signals + ensemble."""
        ev = self.signals()
        roster = "\n".join("%s: %s (%s)" % r for r in ROSTER)
        prompt = (
            "คุณเป็นหัวหน้าฝ่ายบุคคล วิเคราะห์จากหลักฐานจริงด้านล่าง "
            "แล้วเสนอ 'งานจริงที่แต่ละฝ่ายควรทำต่อ' เพื่อให้ทุกฝ่ายมีผลงาน "
            "ห้ามแนะนำลด/ยุบฝ่าย และห้ามสร้างงานที่วัดผลไม่ได้ "
            "ตอบเป็นรายการสั้น ๆ รูปแบบ 'ฝ่าย — งานที่ต้องทำ — หลักฐานที่บอกว่ายังขาด' "
            "อ้างอิงสัญญาณด้านล่างเท่านั้น\n\n"
            "สัญญาณภาระงานจริง: " + json.dumps(ev, ensure_ascii=False) +
            "\nบทบาทที่มีอยู่:\n" + roster +
            "\nคำสั่งงานที่ระบบจัดให้แล้ว: " + json.dumps(
                self.create_work_orders(False), ensure_ascii=False)[:1800])
        try:
            import brain_ensemble as BE
            r = BE.ensemble([{"role": "user", "content": prompt}], want_synthesis=True)
            view = r.get("text") or r.get("error") or ""
            sources = r.get("sources", [])
        except Exception as e:
            view, sources = str(e)[:120], []
        result = {"ok": True, "t": int(time.time()), "evidence": ev,
                  "decision": view, "sources": sources}
        with self.lock:
            self.log.append(result)
        self.save()
        return result

    def status(self):
        last = self.log[-1] if self.log else {}
        return {"ok": True, "rounds": len(self.log), "last": last}


HR = HRHead()
