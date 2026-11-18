"""Zyphere Expert Mode - work like a professional online expert, not a chatbot.

A repeatable, verifiable workflow for every paid task (writing/translation/
analysis/design/code/media): understand -> research -> plan -> produce -> QA ->
deliver. Each stage is recorded so quality is auditable, not claimed.

Uses existing modules (research/rag/selftest/eval/safety/selfcorrect/delivery).
HONEST: produces expert-grade drafts + QA; owner reviews/approves final output.
No auto-posting/bank/OTP. No gambling/illegal.
"""
import os, json, time, threading

STAGES = ["understand", "research", "plan", "produce", "qa", "deliver"]


class Expert:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.projects = []
        self._load()

    def _load(self):
        try:
            self.projects = json.load(open(self.path, encoding="utf-8")).get("projects", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"projects": self.projects[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def checklist(self, kind=""):
        k = str(kind or "").lower()
        base = [
            "เข้าใจโจทย์: ใคร/อะไร/รูปแบบ/ภาษา/กำหนดส่ง",
            "ค้นหลักฐานระดับ A/B อย่างน้อย 2 แหล่ง + บันทึก URL",
            "วางแผน: โครงเรื่อง + สิ่งที่ต้องมี + เกณฑ์วัด",
            "ผลิตผลงานจริงด้วยเครื่องมือของ Zyphere",
            "QA: ตรวจข้อเท็จจริง/ภาษา/ความครบ/ความปลอดภัย + self-correct",
            "ส่งมอบ: หีบแพ็ก + ใบเสนอราคา + สถานะพร้อมดาวน์โหลด",
        ]
        extra = {
            "code": ["รันโค้ดทดสอบจริงก่อนส่ง", "ตรวจ dependency/คำอธิบาย README"],
            "แปล": ["เทียบคำศัพท์เฉพาะทาง", "อ่านย้อนกลับเพื่อความลื่นไหล"],
            "วิเคราะห์": ["แยกข้อเท็จจริง/สมมติฐาน", "ระบุระดับความเชื่อมั่น"],
            "สื่อ": ["ตรวจเสียงไม่ขาด/ภาพชัด/ซับตรง", "ดูใบอนุญาตภาพ"],
        }
        for key, items in extra.items():
            if key in k:
                base += items
        return base

    def start(self, title="", kind="", price=0, deadline=""):
        rec = {"ok": True, "id": "ex_" + str(int(time.time() * 1000)),
               "title": str(title or "")[:160], "kind": str(kind or "")[:80],
               "price": int(price or 0), "deadline": str(deadline or "")[:80],
               "stages": {s: "pending" for s in STAGES},
               "checklist": self.checklist(kind), "t": int(time.time()),
               "honest": "งานต้องให้เจ้าของตรวจอนุมัติก่อนส่งจริง"}
        with self.lock:
            self.projects.append(rec)
        self.save()
        return rec

    def advance(self, pid="", stage="", status="done", note=""):
        st = str(stage or "")
        if st not in STAGES:
            return {"ok": False, "error": "invalid stage"}
        with self.lock:
            for p in self.projects:
                if p["id"] == pid or (not pid and p["stages"].get("understand") == "pending"):
                    p["stages"][st] = status
                    p.setdefault("notes", {})[st] = str(note or "")[:300]
                    break
        self.save()
        return {"ok": True, "stage": st, "status": status}

    def status(self, pid=""):
        with self.lock:
            p = next((x for x in reversed(self.projects) if x["id"] == pid or not pid), None)
        if not p:
            return {"ok": False, "error": "no project"}
        done = sum(1 for v in p["stages"].values() if v == "done")
        return {"ok": True, "project": p, "progress": round(done / len(STAGES), 2),
                "ready": done == len(STAGES)}

    def list_projects(self):
        with self.lock:
            return list(reversed(self.projects[-50:]))

    def snapshot(self):
        with self.lock:
            return {"projects": self.projects[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "projects" in data:
                self.projects = data.get("projects", [])
                self.save()
                return True
        return False
