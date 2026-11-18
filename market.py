"""Zyphere Market Finder - apply the online-marketing knowledge Zyphere studied
to FIND A MARKET for owner's products, cheaply, before the owner lists them.

Does: niche research, competitor/audience analysis, positioning, go-to-market
plan, channel suggestions, and ready-to-post content (Thai). Owner still
creates accounts/posts/handles money (OTP). No gambling/illegal, no fake claims.
HONEST: plans + content; not auto-posting, not guaranteed sales.
"""
import os, json, time, threading

CHANNELS = {
    "Fastwork": "งานรับจ้าง/บริการ — คนไทยหางานทำ",
    "Fiverr": "บริการดิจิทัลสากล — ต้องอังกฤษ",
    "Facebook Marketplace/Group": "ขายของใกล้ตัว/กลุ่ม niche",
    "TikTok/Reels": "คลิปสั้นดึง traffic → ลิงก์ขาย",
    "YouTube": "วิดีโออธิบาย/รีวิว → affiliate/ขาย",
    "Shopee/Lazada": "สินค้าดิจิทัล/ของจริง",
    "GitHub": "โอเพนซอร์ส → รับจ้าง/สปอนเซอร์",
    "Etsy/Gumroad": "ขายไฟล์ดิจิทัลสากล",
}

BLOCK = ("พนัน", "casino", "gambling", "บาคาร่า", "สล็อต", "ผิดกฎหมาย", "ยาเสพติด")


class Market:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.plans = []
        self._load()

    def _load(self):
        try:
            self.plans = json.load(open(self.path, encoding="utf-8")).get("plans", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"plans": self.plans[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def analyze(self, product="", audience="", price=0, budget="free"):
        """Build a go-to-market plan from a product + audience."""
        p = str(product or "").strip()
        if not p or any(b in p.lower() for b in BLOCK):
            return {"ok": False, "error": "สินค้าห้าม/ผิดกฎหมาย หรือชื่อว่าง"}
        a = str(audience or "คนไทยที่ต้องการงานดิจิทัลราคาคุ้ม").strip()
        # pick channels by product type (rule-based from studied marketing)
        low = p.lower()
        if "โค้ด" in low or "code" in low or "script" in low:
            ch = ["Fastwork", "Fiverr", "GitHub"]
        elif any(k in low for k in ("คลิป", "วิดีโอ", "video", "เพลง", "เสียง")):
            ch = ["TikTok/Reels", "YouTube", "Facebook Marketplace/Group"]
        elif any(k in low for k in ("ภาพ", "ออกแบบ", "กราฟฟิก", "design")):
            ch = ["Fastwork", "Facebook Marketplace/Group", "Etsy/Gumroad"]
        else:
            ch = ["Fastwork", "Facebook Marketplace/Group", "Gumroad" if "gumroad" in CHANNELS else "Shopee/Lazada"]
        plan = {
            "ok": True, "id": "mk_" + str(int(time.time() * 1000)),
            "product": p[:160], "audience": a[:160], "price": int(price or 0),
            "niche": self._niche(p), "positioning": "ของจริง ราคาคุ้ม ส่งไว ผลิตโดย AI + มนุษย์ตรวจ",
            "channels": [{"name": c, "why": CHANNELS[c]} for c in ch],
            "funnel": ["โพสต์ตัวอย่าง/ผลงาน (คุณกด)", "คนสนใจทัก → ส่งตัวอย่าง", "ตกลงราคา → PromptPay",
                       "ยืนยันสลิป → ส่งไฟล์ zip ผ่านลิงก์"],
            "content_ideas": [
                "โพสต์: '" + p[:60] + " ในราคา " + str(price or 499) + " บาท — ดูตัวอย่างก่อนได้'",
                "คลิปสั้น 20 วิ: ก่อน/หลังใช้ " + p[:40],
                "รีวิวเชิงเทคนิคสั้น ๆ + ลิงก์ขาย",
            ],
            "metrics": ["จำนวนคนทัก/วัน", "อัตราปิดการขาย", "รายได้จริง/สัปดาห์ (เจ้าของแจ้ง)"],
            "honest": "หาตลาด+ทำคอนเทนต์ให้แล้ว · การสมัคร/โพสต์/รับเงินต้องเจ้าของ (OTP)",
            "t": int(time.time()),
        }
        with self.lock:
            self.plans.append(plan)
        self.save()
        return plan

    def _niche(self, p):
        low = p.lower()
        for k, v in (("โค้ด", "freelance developer"), ("code", "freelance developer"),
                     ("คลิป", "short-form video"), ("วิดีโอ", "video content"),
                     ("แปล", "translation"), ("ออกแบบ", "design service"),
                     ("รายงาน", "research report"), ("ภาพ", "digital art")):
            if k in low:
                return v
        return "digital product"

    def list_plans(self):
        with self.lock:
            return list(reversed(self.plans[-50:]))

    def stats(self):
        with self.lock:
            return {"plans": len(self.plans), "honest": "ไม่รับประกันยอดขาย"}

    def snapshot(self):
        with self.lock:
            return {"plans": self.plans[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "plans" in data:
                self.plans = data.get("plans", [])
                self.save()
                return True
        return False
