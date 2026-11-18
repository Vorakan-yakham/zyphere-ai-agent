"""Zyphere Marketplace Launchpad - free places to sell online, with a prepared
signup kit + platform-specific listing templates for every product.

Owner must click OTP/identity themselves (account is theirs). System prepares:
what to fill, what to upload, title/description/tags/price per platform, and
creates OTP-assist tasks so owner only types the code. No auto account creation,
no illegal/gambling, no bank access. HONEST: preparation only, owner publishes.
"""
import os, json, time, threading

PLATFORMS = {
    "Fastwork": {"url": "https://fastwork.co", "type": "service", "fee": "commission",
                 "fields": ["อีเมล", "เบอร์", "ชื่อ", "OTP"], "title_max": 80,
                 "tip": "เน้นบริการ/งานรับจ้าง ถ่ายผลงานให้ชัด"},
    "Fiverr": {"url": "https://www.fiverr.com", "type": "service", "fee": "commission",
               "fields": ["email", "password", "OTP"], "title_max": 80,
               "tip": "English title, gig thumbnail, packages Basic/Standard/Premium"},
    "Facebook Marketplace": {"url": "https://www.facebook.com/marketplace", "type": "goods", "fee": "free",
               "fields": ["Facebook account", "OTP"], "title_max": 100,
               "tip": "โพสต์ในกลุ่ม niche + รูปจริง + ราคาชัด"},
    "Shopee": {"url": "https://shopee.co.th", "type": "goods", "fee": "commission",
               "fields": ["เบอร์", "OTP", "ชื่อร้าน"], "title_max": 120,
               "tip": "ใส่ keyword ค้นหาในหัวข้อ"},
    "Lazada": {"url": "https://www.lazada.co.th", "type": "goods", "fee": "commission",
               "fields": ["เบอร์", "OTP", "ชื่อร้าน"], "title_max": 100,
               "tip": "ใช้หมวดหมู่ให้ตรง"},
    "Gumroad": {"url": "https://gumroad.com", "type": "digital", "fee": "commission",
                "fields": ["email", "password", "OTP"], "title_max": 80,
                "tip": "ขายไฟล์ดิจิทัล ใส่ preview + license"},
    "Etsy": {"url": "https://www.etsy.com", "type": "digital", "fee": "listing + commission",
             "fields": ["email", "password", "OTP", "payment"], "title_max": 140,
             "tip": "digital download, tags 13 ช่อง"},
    "YouTube": {"url": "https://www.youtube.com", "type": "content", "fee": "free",
                "fields": ["Google account", "OTP"], "title_max": 100,
                "tip": "วิดีโออธิบาย + link ขายในคำอธิบาย"},
    "TikTok Shop": {"url": "https://shop.tiktok.com", "type": "goods", "fee": "commission",
                    "fields": ["เบอร์", "OTP"], "title_max": 80,
                    "tip": "คลิปสั้น + link ใน bio"},
    "GitHub": {"url": "https://github.com", "type": "code", "fee": "free",
               "fields": ["email", "password", "OTP"], "title_max": 100,
               "tip": "repo สาธารณะ + README + รับจ้างผ่าน Issue/Sponsor"},
}

BLOCK = ("พนัน", "casino", "gambling", "ผิดกฎหมาย")


class Launchpad:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.kits = []
        self._load()

    def _load(self):
        try:
            self.kits = json.load(open(self.path, encoding="utf-8")).get("kits", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"kits": self.kits[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def platforms(self):
        return {"ok": True, "platforms": [{"name": k, **v} for k, v in PLATFORMS.items()],
                "note": "ฟรี/ค่าคอมฯ ตามแพลตฟอร์ม — ต้อง OTP เจ้าของกดเอง"}

    def kit(self, product="", price=0, platform=None, category="digital", otp=None):
        """Prepare a full launch kit: signup fields + listing + otp task."""
        p = str(product or "").strip()
        if not p or any(b in p.lower() for b in BLOCK):
            return {"ok": False, "error": "invalid product"}
        names = [platform] if platform and platform in PLATFORMS else list(PLATFORMS.keys())
        kits = []
        for nm in names:
            cfg = PLATFORMS[nm]
            title = (p + " — ผลงานจริงจาก Zyphere")[:cfg["title_max"]]
            desc = (p + "\n\nผลิตโดย Zyphere · ตรวจคุณภาพก่อนส่ง\n" +
                    "ราคา %d บาท · ชำระ PromptPay 0941939686 · ส่งไฟล์หลังยืนยัน\n" % int(price or 0) +
                    "แท็ก: #Zyphere #AI #ดิจิทัล\n" + cfg["tip"])
            otp_task = None
            if otp:
                try:
                    otp_task = otp.prepare(nm, "วรกันต์", "vorayakham@gmail.com", "เบอร์ของคุณ")
                except Exception:
                    pass
            kits.append({"platform": nm, "url": cfg["url"], "type": cfg["type"],
                         "signup_fields": cfg["fields"], "listing": {"title": title, "description": desc[:1000]},
                         "otp_task": (otp_task or {}).get("id"), "status": "ready_for_owner"})
        rec = {"ok": True, "id": "lp_" + str(int(time.time() * 1000)),
               "product": p[:160], "price": int(price or 0), "kits": kits,
               "honest": "เตรียมครบแล้ว — เจ้าของสมัคร(OTP)และกดโพสต์เอง", "t": int(time.time())}
        with self.lock:
            self.kits.append(rec)
        self.save()
        return rec

    def list_kits(self, n=20):
        with self.lock:
            return list(reversed(self.kits[-n:]))

    def best_platforms(self, category="", scholar=""):
        """Match a scholar's field to the platforms they're best at."""
        c = str(category or "").lower()
        s = str(scholar or "").lower()
        if any(k in c + s for k in ("code", "software", "algorithm", "database", "cyber", "machine", "ai", "program")):
            return ["GitHub", "Fiverr", "Gumroad"]
        if any(k in c + s for k in ("design", "art", "music", "film", "visual", "architecture")):
            return ["Etsy", "Fiverr", "Facebook Marketplace"]
        if any(k in c + s for k in ("guide", "education", "language", "literature", "history")):
            return ["Gumroad", "Etsy", "Fastwork"]
        if any(k in c + s for k in ("report", "finance", "economic", "law", "medical", "science")):
            return ["Fiverr", "Fastwork", "Gumroad"]
        return ["Fastwork", "Facebook Marketplace", "Gumroad"]

    def scholar_launch(self, products=None, otp=None, limit=60):
        """Each scholar launches their own product on platforms they excel at."""
        made = []
        for p in (products or [])[:limit]:
            best = self.best_platforms(p.get("category", ""), p.get("scholar", ""))
            for nm in best[:2]:
                k = self.kit(p.get("product", ""), p.get("price", 0), nm,
                             p.get("category", "digital"), otp)
                if k.get("ok"):
                    made.append(k)
        return {"ok": True, "launches": len(made), "kits": made,
                "note": "each scholar -> their best platforms; owner still clicks OTP + posts"}

    def stats(self):
        with self.lock:
            return {"kits": len(self.kits), "platforms": len(PLATFORMS)}

    def snapshot(self):
        with self.lock:
            return {"kits": self.kits[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "kits" in data:
                self.kits = data.get("kits", [])
                self.save()
                return True
        return False
