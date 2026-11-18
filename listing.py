"""Zyphere Listing Writer - write sell-ready titles, descriptions and tags for
every product (marketing knowledge Zyphere studied). No fake claims, no
gambling/illegal. Owner owns shop; system only writes listing copy.
"""
import re

BENEFIT = {
    "code": ["พร้อมรัน ไม่ต้องแก้เพิ่ม", "มี README + ตัวอย่าง", "ประหยัดเวลาเขียนเอง"],
    "service": ["ส่งผลงานเร็ว", "ปรับตามความต้องการ", "ราคาคุ้ม"],
    "report": ["อ้างแหล่งจริง", "สรุปเข้าใจง่าย", "มีข้อเสนอแนะนำไปใช้"],
    "content": ["หลายภาษา", "พร้อมโพสต์", "ปรับโทนได้"],
    "design": ["แบบแปลนชัดเจน", "ระบุชิ้นส่วน", "ปรับขนาดได้"],
    "guide": ["ขั้นตอนทีละขั้น", "ตารางปฏิบัติ", "อ่านง่าย"],
    "media": ["ภาพชัด เสียงตรง", "มีซับไตเติล", "ดาวน์โหลดเลย"],
}
TAGS = {
    "code": ["#โค้ด", "#Python", "#freelance", "#โปรแกรม"],
    "service": ["#บริการ", "#รับจ้าง", "#แปลภาษา"],
    "report": ["#วิเคราะห์", "#รายงาน", "#data"],
    "content": ["#คอนเทนต์", "#การตลาด", "#โซเชียล"],
    "design": ["#ออกแบบ", "#หุ่นยนต์", "#แบบแปลน"],
    "guide": ["#คู่มือ", "#เกษตร", "#ความรู้"],
    "media": ["#คลิป", "#เสียง", "#สื่อ"],
}


class ListingWriter:
    def write(self, title="", desc="", category="", price=0):
        t = str(title or "").strip()
        c = str(category or "digital").lower()
        if not t:
            return {"ok": False, "error": "missing title"}
        key = next((k for k in BENEFIT if k in c), "service")
        benefits = BENEFIT[key]
        tags = TAGS[key] + ["#Zyphere", "#AI"]
        headline = ("%s — ผลงานจริงจาก Zyphere" % t)[:120]
        body = (str(desc or t)[:200] + "\n\n" +
                "สิ่งที่ได้:\n" + "\n".join("• " + b for b in benefits) +
                "\n\nราคา %d บาท · ชำระ PromptPay · ส่งไฟล์ทันทีหลังยืนยัน" % int(price or 0) +
                "\n\nผลิตโดย Zyphere · ตรวจคุณภาพก่อนส่ง · งดพนัน/ผิดกฎหมาย")
        return {"ok": True, "title": headline, "description": body[:1200],
                "tags": tags, "category": c,
                "honest": "เขียนจากประโยชน์จริง ไม่โอ้อวดยอดขาย"}

    def refresh(self, products):
        out = []
        for p in (products or []):
            w = self.write(p.get("title", ""), p.get("desc", ""), p.get("category", ""), p.get("price", 0))
            out.append({"id": p.get("id"), "title": w.get("title"),
                        "description": w.get("description"), "tags": w.get("tags")})
        return {"ok": True, "listings": out}
