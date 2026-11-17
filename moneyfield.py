"""Zyphere MoneyField - turn EVERY academic/professional field into a
concrete, deliverable, sellable digital product (owner's goal: earn income
from every field of work). Uses existing factory: work + media + packbuilder +
delivery + billing. No hardware, no OTP, no auto-posting (owner account needed),
no gambling/illegal. HONEST: produces products; selling still needs the owner.
"""
import os, json, time, threading


# field -> (deliverable name, what it contains, suggested price)
FIELD_PRODUCTS = {
    "สถาปัตยกรรม/ออกแบบ": ("แบบแปลน + visualization", "แปลนห้อง/บ้าน + ภาพ PF", 1500),
    "วิศวกรรม/หุ่นยนต์": ("สเปกชิ้นส่วนหุ่นยนต์", "รายการชิ้นส่วน + แปลน assembly", 1200),
    "การแพทย์/สุขภาพ": ("สรุปสุขภาพความรู้", "เอกสารอธิบายเรื่องสุขภาพแบบเข้าใจง่าย", 800),
    "กฎหมาย": ("สรุปกฎหมายเข้าใจง่าย", "เอกสารสรุปกฎหมาย+ข้อควรระวัง (ไม่ใช่คำปรึกษากฎหมาย)", 900),
    "ภาษา/การแปล": ("แปลเอกสาร", "แปล TH↔EN + ตรวจภาษา", 500),
    "การเงิน/บัญชี": ("template งบการเงิน", "ไฟล์ tabulate รายรับ-รายจ่าย + คำอธิบาย", 700),
    "การศึกษา/สอน": ("ชุดการสอน/หลักสูตร", "สไลด์เนื้อหา + แบบฝึกหัด + เฉลย", 999),
    "เนื้อหา/การเขียน": ("แพ็กคอนเทนต์", "บทความ 5 ชิ้น + คำโปรโมต", 600),
    "ศิลปะ/ดนตรี/สื่อ": ("แพ็กสื่อ", "MP3/MP4/เพลง/ซับ", 1200),
    "วิทยาศาสตร์ข้อมูล/AI": ("รายงานวิเคราะห์ข้อมูล", "สรุปข้อมูล + graph + ข้อเสนอแนะ", 1500),
    "ประวัติศาสตร์/มนุษยวิทยา": ("หนังสือเล่าเรื่องสั้น", "เรื่องเล่าอ้างอิงแหล่งจริง", 500),
    "จิตวิทยา": ("ชุดส่งเสริมสุขภาพจิต", "เนื้อหา + สื่อเสียงบรรยาย", 699),
    "เกษตร/สิ่งแวดล้อม": ("คู่มือเกษตร", "แนวทางปลูก/เลี้ยง + ตาราง", 700),
    "กราฟฟิก/UI": ("ชุดกราฟฟิก", "ภาพ + layout + คำอธิบาย", 999),
    "อาหาร/โภชนาการ": ("ตารางอาหาร/เมนู", "menu plan + สรุปโภชนาการ", 599),
    "กีฬา/สุขภาพ": ("แผนฝึกซ้อม", "ตารางฝึก + คำแนะนำ", 699),
    "IT/โค้ด": ("สคริปต์/โปรแกรม", "โค้ดพร้อมใช้ + ตัวอย่าง", 1500),
    "ธุรกิจ/การจัดการ": ("แผนธุรกิจ", "แผน + งบประมาณ + KPI", 1800),
    "นวัตกรรม/สิทธิบัตร": ("รายงานความเป็นไปได้", "วิเคราะห์ไอเดีย + สิทธิบัตรเบื้องต้น", 2000),
}

BLOCK = ("พนัน", "casino", "gambling", "บาคาร่า", "ผิดกฎหมาย")


class MoneyField:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.catalog = []
        self._load()

    def _load(self):
        try:
            self.catalog = json.load(open(self.path, encoding="utf-8")).get("catalog", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"catalog": self.catalog[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def generate(self, field="", zyphere_answer=""):
        """Create a sellable product spec for a field from real knowledge."""
        f = str(field or "").strip()
        if not f or any(b in f.lower() for b in BLOCK):
            return {"ok": False, "error": "invalid/forbidden field"}
        name, contains, price = FIELD_PRODUCTS.get(f, ("ของขายตามสั่ง", "ผลิตตามความรู้ที่ study ไว้", 999))
        rec = {"ok": True, "id": "mf_" + str(int(time.time() * 1000)),
               "field": f[:120], "product": name, "contains": contains,
               "price": price, "source": "Zyphere knowledge" if zyphere_answer else "master catalog",
               "zyphere_note": str(zyphere_answer or "")[:600],
               "delivery": "zip → /media/ → delivery record → PromptPay",
               "status": "spec_ready", "t": int(time.time())}
        with self.lock:
            self.catalog.append(rec)
        self.save()
        return rec

    def catalog_list(self):
        with self.lock:
            return list(reversed(self.catalog[-100:]))

    def fields(self):
        return {"ok": True, "fields": list(FIELD_PRODUCTS.keys()), "count": len(FIELD_PRODUCTS)}

    def stats(self):
        with self.lock:
            return {"specs": len(self.catalog), "potential_revenue": sum(p.get("price", 0) for p in self.catalog)}

    def snapshot(self):
        with self.lock:
            return {"catalog": self.catalog[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "catalog" in data:
                self.catalog = data.get("catalog", [])
                self.save()
                return True
        return False
