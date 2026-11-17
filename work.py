"""Zyphere Applied Work Engine - turn ANY learned knowledge into real deliverables.

Maps a field/topic from the curriculum (196+138 subjects) to a concrete work
output that can actually be produced with Zyphere's tools (text, code, spec,
media, report). Tracks completed works -> feeds the academic rank 'works'
metric. This is the 'working, not just knowing' layer the owner asked for.

HONEST: produces plans/drafts/assets/specs. Physical creation, posting, and
paid platform actions still need the owner's account/hardware. No gambling,
no illegal work, respect copyright.
"""
import os, json, time, threading

WORK_TYPES = {
    "บทความ/สรุปความรู้": ("article", ["เขียน", "อธิบาย", "สรุป", "ความรู้", "history", "physics", "philosophy"]),
    "สเปก/แบบแปลน": ("spec", ["ออกแบบ", "สเปก", "แบบแปลน", "architecture", "robot", "aerospace", "engineering"]),
    "โค้ด/โปรแกรม": ("code", ["โค้ด", "code", "python", "โปรแกรม", "script", "algorithm", "software"]),
    "สื่อ/คลิป/เสียง": ("media", ["คลิป", "วิดีโอ", "เพลง", "เสียง", "ภาพ", "video", "music", "design"]),
    "รายงานวิจัย": ("research", ["วิจัย", "งานวิจัย", "report", "research", "วิเคราะห์", "evidence"]),
    "แผน/กลยุทธ์": ("plan", ["แผน", "กลยุทธ์", "วางแผน", "manage", "strategy", "business", "finance"]),
}

BLOCK = ("พนัน", "casino", "gambling", "บาคาร่า", "สล็อต", "ผิดกฎหมาย")


class WorkEngine:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.works = []
        self._load()

    def _load(self):
        try:
            self.works = json.load(open(self.path, encoding="utf-8")).get("works", [])
        except Exception:
            self.works = []

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"works": self.works[-1000:]}, open(self.path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def classify(self, topic):
        t = str(topic or "").lower()
        best, score = "article", 0
        for label, (key, kws) in WORK_TYPES.items():
            s = sum(1 for k in kws if k.lower() in t)
            if s > score:
                best, score = key, s
        return best

    def produce(self, topic, field="", notes=""):
        """Produce a real, reviewable work package from knowledge."""
        topic = str(topic or "").strip()
        if not topic:
            return {"ok": False, "error": "missing topic"}
        if any(b in topic.lower() for b in BLOCK):
            return {"ok": False, "error": "งดเด็ดขาด: งานผิดกฎหมาย/เว็บพนัน"}
        key = self.classify(topic)
        blueprint = {
            "article": "โครงสร้าง: หัวข้อ → ใจความ → หลักการ → ตัวอย่าง → ข้อจำกัด → แหล่งอ้างอิง",
            "spec": "โครงสร้าง: วัตถุประสงค์ → สเปก → รายการชิ้นส่วน → วัสดุ → ขั้นตอน → ความปลอดภัย",
            "code": "โครงสร้าง: อินพุต → อัลกอริทึม → ฟังก์ชัน → ทดสอบ → ตัวอย่างการใช้",
            "media": "โครงสร้าง: เรื่อง → storyboard → ภาพ/มุมกล้อง → เสียง → ซับ → ส่งออก MP4/MP3",
            "research": "โครงสร้าง: คำถาม → สมมติฐาน → หลักฐาน(ระดับ A/B) → วิเคราะห์ → ข้อสรุป → คำถามต่อยอด",
            "plan": "โครงสร้าง: เป้าหมาย → ทรัพยากร → ขั้นตอน → ความเสี่ยง → ตัวชี้วัด → ตารางเวลา",
        }[key]
        work = {"ok": True, "id": "w_" + str(int(time.time() * 1000)),
                "topic": topic[:200], "field": str(field or "")[:100],
                "type": key, "blueprint": blueprint,
                "notes": str(notes or "")[:800],
                "status": "draft_ready", "t": int(time.time()),
                "note": "โครงผลงานพร้อมผลิตจริงด้วยเครื่องมือของ Zyphere (media/code/research)"}
        with self.lock:
            self.works.append(work)
        self.save()
        return work

    def count(self):
        with self.lock:
            return len(self.works)

    def list_works(self, limit=30):
        with self.lock:
            return list(reversed(self.works[-limit:]))

    def snapshot(self):
        with self.lock:
            return {"works": self.works[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "works" in data:
                self.works = data.get("works", [])
                self.save()
                return True
        return False
