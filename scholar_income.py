"""Zyphere Scholar-to-Income - each of 46 scholars studies its field in depth,
extracts a SELLABLE knowledge product from that field, and lists it in the shop.
Turns 'learning' straight into 'money' (owner gets PromptPay). No auto-posting,
no bank access, no gambling/illegal. HONEST: products are drafts to review.
"""
import os, json, time, threading

# field -> sellable product template (price, what's inside)
PRODUCTS = {
    "ฟิสิกส์ควอนตัม": (790, "สรุปควอนตัมเข้าใจง่าย + ภาพประกอบ", "report"),
    "ฟิสิกส์คลาสสิก": (690, "คู่มือกลศาสตร์/เทอร์โม พร้อมโจทย์", "guide"),
    "ดาราศาสตร์-จักรวาล": (690, "คู่มือดาราศาสตร์เบื้องต้น", "guide"),
    "คณิตศาสตร์บริสุทธิ์": (890, "ชุดโจทย์+เฉลยพีชคณิต/เรขาคณิต", "guide"),
    "คณิตศาสตร์ประยุกต์": (890, "template สถิติ/วิเคราะห์ข้อมูล", "report"),
    "ตรรกะและทฤษฎีข้อมูล": (990, "คู่มือตรรกะสำหรับนักคิด", "guide"),
    "พันธุกรรม-ชีวโมเลกุล": (990, "สรุปพันธุกรรม CRISPR เข้าใจง่าย", "report"),
    "เซลล์และเนื้อเยื่อ": (790, "คู่มือเซลล์วิทยา", "guide"),
    "ภูมิคุ้มกัน-โรค": (990, "สรุปภูมิคุ้มกัน+วัคซีน", "report"),
    "สมอง-ประสาทวิทยา": (990, "คู่มือสมองและความจำ", "guide"),
    "สรีระและเภสัช": (790, "คู่มือสรีระ+โภชนาการ", "guide"),
    "การแพทย์คลินิก": (1200, "สรุปแนวทางตรวจเบื้องต้น", "report"),
    "จิตวิทยา": (690, "คู่มือจิตวิทยาความจำ/อารมณ์", "guide"),
    "ปัญญาประดิษฐ์": (1500, "คู่มือ AI/ML สำหรับผู้เริ่ม", "guide"),
    "อัลกอริทึม-โครงสร้างข้อมูล": (1500, "ชุดอัลกอริทึม+โค้ดตัวอย่าง", "code"),
    "วิศวกรรมซอฟต์แวร์": (1500, "template โปรเจกต์+สถาปัตยกรรม", "code"),
    "ความมั่นคงไซเบอร์": (1500, "คู่มือความปลอดภัยพื้นฐาน", "guide"),
    "ฐานข้อมูล-ข้อมูลขนาดใหญ่": (1500, "template ออกแบบฐานข้อมูล", "code"),
    "คอมพิวเตอร์วิทัศน์-เสียง": (1500, "สคริปต์ cv/audio พร้อมใช้", "code"),
    "หุ่นยนต์-ระบบอัตโนมัติ": (1800, "แบบแปลนหุ่นยนต์+สเปก", "design"),
    "วิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์": (1500, "คู่มือวงจร+คำนวณ", "guide"),
    "วิศวกรรมเครื่องกล": (1500, "สรุปหลักการเครื่องกล", "guide"),
    "วิศวกรรมโยธา-โครงสร้าง": (1500, "ตัวอย่างคำนวณโครงสร้าง", "report"),
    "วิศวกรรมเคมี-วัสดุ": (1500, "สรุปวัสดุศาสตร์", "report"),
    "สถาปัตยกรรม-การออกแบบ": (1500, "แบบแปลน+BIM พื้นฐาน", "design"),
    "เศรษฐกิจมหภาค-การเงิน": (1200, "สรุปเศรษฐกิจเข้าใจง่าย", "report"),
    "การเงิน-การลงทุน": (1200, "template วิเคราะห์การลงทุน", "report"),
    "การบัญชี-ตรวจสอบ": (1200, "template งบการเงิน", "report"),
    "การตลาด-ธุรกิจ": (1500, "แพ็กกลยุทธ์การตลาด", "content"),
    "การจัดการ-ภาวะผู้นำ": (1200, "คู่มือบริหารทีม", "guide"),
    "กฎหมาย-สิทธิมนุษยชน": (990, "สรุปกฎหมายเบื้องต้น (ไม่ใช่คำปรึกษา)", "report"),
    "จริยธรรม-ปรัชญา": (890, "คู่มือจริยธรรม AI", "guide"),
    "ประวัติศาสตร์-อารยธรรม": (790, "เรื่องเล่าประวัติศาสตร์", "content"),
    "สังคมวิทยา-มานุษยวิทยา": (790, "สรุปวัฒนธรรม/สังคม", "report"),
    "รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ": (990, "สรุปรัฐศาสตร์", "report"),
    "ภาษาศาสตร์-การแปล": (690, "บริการแปล+คู่มือภาษา", "service"),
    "วรรณกรรม-การเขียน": (690, "ชุดเขียนเรื่อง/บทความ", "content"),
    "การสอน-การศึกษา": (999, "ชุดการสอน+แบบฝึกหัด", "guide"),
    "ดนตรี-เสียง": (990, "เพลง MP3 ลิขสิทธิ์ตัวเอง", "media"),
    "ภาพยนตร์-สื่อ-กราฟฟิก": (1290, "แพ็กสื่อวิดีโอ/ภาพ", "media"),
    "ภูมิอากาศ-สิ่งแวดล้อม": (990, "รายงานภูมิอากาศ", "report"),
    "เกษตร-อาหาร": (790, "คู่มือเกษตร/เมนู", "guide"),
    "น้ำ-ทรัพยากร": (790, "คู่มือจัดการน้ำ", "guide"),
    "พลังงาน-นิวเคลียร์": (1200, "สรุปพลังงานทางเลือก", "report"),
    "อวกาศ-การสำรวจ": (1200, "สรุปอวกาศ+คำนวณวงโคจร", "report"),
    "การเอาชีวิตรอด-ความปลอดภัย": (990, "คู่มือเอาชีวิตรอด", "guide"),
}
BLOCK = ("พนัน", "casino", "gambling", "ผิดกฎหมาย")


class ScholarIncome:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.products = []
        self._load()

    def _load(self):
        try:
            self.products = json.load(open(self.path, encoding="utf-8")).get("products", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"products": self.products[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def study_all(self, researcher=None):
        """Every scholar studies deep and turns learning into a sellable draft."""
        made = []
        for field, (price, desc, cat) in PRODUCTS.items():
            if any(b in field.lower() for b in BLOCK):
                continue
            finding = ""
            if researcher:
                try:
                    r = researcher(field, desc)
                    finding = (str(r.get("result") or "")[:300] if isinstance(r, dict) else str(r)[:300])
                except Exception:
                    finding = ""
            rec = {"ok": True, "id": "si_" + str(int(time.time() * 1000)) + "_" + str(len(made)),
                   "scholar": field, "product": desc, "category": cat, "price": price,
                   "finding": finding, "status": "ready_to_list", "t": int(time.time()),
                   "honest": "ร่างจากการเรียนรู้ — ตรวจคุณภาพก่อนขายจริง"}
            made.append(rec)
        with self.lock:
            self.products.extend(made)
        self.save()
        return {"ok": True, "studied": len(made), "products": made,
                "potential_revenue": sum(p["price"] for p in made)}

    def list_catalog(self):
        with self.lock:
            return list(reversed(self.products[-100:]))

    def stats(self):
        with self.lock:
            return {"products": len(self.products),
                    "potential": sum(p.get("price", 0) for p in self.products)}

    def snapshot(self):
        with self.lock:
            return {"products": self.products[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "products" in data:
                self.products = data.get("products", [])
                self.save()
                return True
        return False
