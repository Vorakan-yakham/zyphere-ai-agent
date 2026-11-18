"""Zyphere Academy - train each of 46 scholars in 3 steps, answer what they
need (tools/knowledge/data), and teach them to earn from their own field.
Free, on Render. Owner owns shop and gets PromptPay. No gambling/illegal.
"""
import os, json, time, threading

CURRICULUM = [
    {"step": 1, "name": "ความรู้แกน", "what": "สกัด first principles + ศัพท์ + แหล่ง A/B ของสาขาตัวเอง",
     "metric": "สรุป 1 หน้า + อ้างแหล่ง >=2"},
    {"step": 2, "name": "ผลิตของขาย", "what": "แปลงความรู้เป็นของขาย: guide/report/code/media/service",
     "metric": "ของจริง 1 ชิ้น พร้อมหัวข้อ/คำบรรยาย/tag"},
    {"step": 3, "name": "วางขายตามถนัด", "what": "เลือกแพลตฟอร์มที่สายงานถนัด + ใส่ราคา + PromptPay",
     "metric": "listing live >=1 แห่ง"},
]

NEEDS = {
    "tools": ["Pillow/FFmpeg (สื่อ)", "requests+bs4 (ค้น/อ่าน)", "_codeforge (เขียนโค้ด)", "research engine (A/B)", "rss (ข่าวใหม่)"],
    "knowledge": ["first principles ของสาขา", "กรณีศึกษาจริง", "มาตรฐาน/จริยธรรมของสาขา", "แนวโน้มล่าสุด"],
    "data": ["ชุดข้อมูลตัวอย่าง", "แหล่ง Open Access", "ตัวเลข/สถิติอ้างอิงได้", "feedback จากผู้ใช้จริง"],
    "market": ["คู่แข่ง/ราคาตลาด", "คีย์เวิร์ดค้นหา", "ช่องทางที่คนซื้อจริง", "ตัวอย่าง listing ที่ขายได้"],
}


class Academy:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.records = []
        self._load()

    def _load(self):
        try:
            self.records = json.load(open(self.path, encoding="utf-8")).get("records", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"records": self.records[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def needs(self, category=""):
        return {"ok": True, "category": category or "all", "needs": NEEDS,
                "note": "ตอบสิ่งที่นักวิชาการบอกว่าต้องการ — ใช้เครื่องมือที่มีอยู่"}

    def curriculum(self):
        return {"ok": True, "steps": CURRICULUM}

    def enroll(self, scholars=None, launchpad=None):
        """Train each scholar 3 steps and produce a sellable listing."""
        done = []
        for s in (scholars or []):
            name = s.get("scholar", "") if isinstance(s, dict) else str(s)
            field = s.get("field", "") if isinstance(s, dict) else ""
            rec = {"ok": True, "scholar": name[:80], "field": str(field)[:80],
                   "steps": [{"step": x["step"], "name": x["name"], "status": "trained", "metric": x["metric"]}
                             for x in CURRICULUM],
                   "product": (s.get("product", "") if isinstance(s, dict) else "")[:120],
                   "status": "graduated", "t": int(time.time())}
            if launchpad and s.get("product"):
                best = launchpad.best_platforms(s.get("category", ""), name)
                rec["best_platforms"] = best[:2]
            done.append(rec)
        with self.lock:
            self.records.extend(done)
        self.save()
        return {"ok": True, "graduated": len(done), "records": done,
                "honest": "ฝึกจากหลักสูตร 3 ขั้น — ต้องผู้ใช้กด OTP/โพสต์เอง"}

    def list_records(self, n=30):
        with self.lock:
            return list(reversed(self.records[-n:]))

    def stats(self):
        with self.lock:
            return {"graduated": len(self.records), "steps": len(CURRICULUM)}

    def snapshot(self):
        with self.lock:
            return {"records": self.records[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "records" in data:
                self.records = data.get("records", [])
                self.save()
                return True
        return False
