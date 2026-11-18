"""Zyphere Daily Money Report - gather EVERYTHING the owner needs to act on:
products ready to sell, market/channels, OTP steps awaiting the owner, help
requests, revenue, and a copy-paste action list. Send it to the owner's email
(owner said: just fill what's needed and email me). If mail isn't configured,
return the report inline so the app can show it. No fake numbers.
"""
import time


class Report:
    def build(self, data=None):
        d = data or {}
        L = []
        L.append("ZYPHERE — รายงานหาเงิน / สิ่งที่ต้องทำ")
        L.append("=" * 46)
        L.append("เวลา: " + time.strftime("%Y-%m-%d %H:%M"))
        L.append("")
        L.append("1) สินค้าที่ Zyphere ผลิตไว้พร้อมขาย")
        for p in (d.get("products") or [])[:10]:
            L.append("   - %s | %s บาท | %s" % (p.get("title","?"), p.get("price","?"), p.get("url","")))
        if not d.get("products"):
            L.append("   (ยังไม่มี — พิมพ์สั่งให้ Zyphere ผลิตได้)")
        L.append("")
        L.append("2) ตลาด/ช่องทางที่แนะนำ")
        for c in (d.get("channels") or [])[:6]:
            L.append("   - " + str(c))
        L.append("")
        L.append("3) สิ่งที่ต้องให้เจ้าของกดเอง (OTP/ยืนยันตัวตน)")
        for t in (d.get("otp") or [])[:10]:
            L.append("   - [%s] %s → %s" % (t.get("platform","?"), t.get("status","?"), t.get("reminder","")))
        if not d.get("otp"):
            L.append("   (ไม่มีค้าง)")
        L.append("")
        L.append("4) คำขอความช่วยเหลือที่ค้าง")
        for h in (d.get("help") or [])[:10]:
            L.append("   - %s: %s" % (h.get("action","?"), h.get("message","")))
        L.append("")
        L.append("5) ยอด/สถิติ")
        L.append("   รายงานโดยเจ้าของ: %s บาท · สินค้า %s ชิ้น · ออเดอร์ %s"
                 % (d.get("revenue", 0), d.get("assets", 0), d.get("orders", 0)))
        L.append("")
        L.append("6) ลำดับที่ต้องทำตอนนี้")
        for i, a in enumerate((d.get("actions") or ["ผลิตสินค้า", "ดูตลาด", "กด OTP เอง", "รับเงิน PromptPay"])[:8], 1):
            L.append("   %d. %s" % (i, a))
        L.append("")
        L.append("หมายเหตุ: ระบบไม่รับ OTP/ไม่เข้าบัญชี — เจ้าของเป็นคนกดทุกขั้นตอนที่ต้องตัวตน")
        L.append("งดพนัน/สิ่งผิดกฎหมาย · ข้อมูลจากระบบจริงเท่านั้น")
        return "\n".join(L)

    def send(self, to="", data=None, subject=""):
        body = self.build(data)
        result = {"ok": True, "preview": body[:3000], "to": to}
        if to:
            try:
                from mailer import send_mail
                result["email"] = send_mail(to, subject or "Zyphere — รายงานหาเงินประจำวัน", body)
            except Exception as e:
                result["email"] = {"ok": False, "error": str(e)[:200]}
        return result
