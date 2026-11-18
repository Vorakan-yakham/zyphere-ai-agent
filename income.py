"""Zyphere Income Channels - manage ALL online money channels Zyphere can feed:
selling media (image/audio/video), code products, content packs, affiliate
content, services, digital downloads. Owner's goal: earn from every channel.

HONEST: Zyphere PRODUCES the assets + tracks the channel. It does NOT auto-post,
auto-create accounts, or touch bank accounts (owner account/OTP). Affiliate
links are supplied by the owner; Zyphere makes promo content for them.
No gambling/illegal. No false income claims.

Tracks REAL metrics only: channel, asset produced, price, status, earned (owner-reported).
"""
import os, json, time, threading

CHANNELS = {
    "ภาพดิจิทัล": {"asset": "ภาพ/กราฟฟิก", "via": "ขายไฟล์ / พอร์ต / สต็อก", "auto": "ผลิตได้"},
    "เสียง/TTS": {"asset": "MP3/เสียงบรรยาย", "via": "ขายเสียง/ podcast/ ออดิโอบุ๊ค", "auto": "ผลิตได้"},
    "วิดีโอ": {"asset": "MP4/คลิป/ซับ", "via": "ขายคลิป/ยูทูป/สปอนเซอร์", "auto": "ผลิตได้"},
    "เพลง": {"asset": "MP3 ลิขสิทธิ์ตัวเอง", "via": "ขายเพลง/แบ็คกราวด์", "auto": "ผลิตได้"},
    "โค้ด/โปรแกรม": {"asset": "สคริปต์/เว็บแอป", "via": "ขายโค้ด/Freelance", "auto": "ผลิตได้"},
    "เนื้อหา/บทความ": {"asset": "บทความ/แปล/สรุป", "via": "ขายคอนเทนต์/บล็อก", "auto": "ผลิตได้"},
    "รายงาน/วิเคราะห์": {"asset": "รายงาน/ข้อมูลเชิงลึก", "via": "ขายรายงาน/ที่ปรึกษา", "auto": "ผลิตได้"},
    "หลักสูตร/การสอน": {"asset": "สไลด์/แบบฝึกหัด", "via": "ขายคอร์ส/สอน", "auto": "ผลิตได้"},
    "affiliate": {"asset": "เนื้อหาส่งเสริม", "via": "ลิงก์ affiliate ที่เจ้าของใส่", "auto": "ผลิตเนื้อหาได้ / ลิงก์ต้องเจ้าของ"},
    "ดิจิทัลดาวน์โหลด": {"asset": "zip/แพ็ก", "via": "ขายไฟล์ดาวน์โหลด", "auto": "ผลิต+ส่งได้"},
}


class Income:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.entries = []
        self.campaigns = []
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.entries = d.get("entries", [])
            self.campaigns = d.get("campaigns", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"entries": self.entries[-2000:], "campaigns": self.campaigns[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def channels(self):
        return {"ok": True, "channels": [{"name": k, **v} for k, v in CHANNELS.items()],
                "note": "ผลิตของได้จริง · การโพสต์/รับเงินต้องเจ้าของ"}

    def produce(self, channel="", title="", asset_url="", price=0, note=""):
        """Record a produced, sellable asset in a channel."""
        c = str(channel or "").strip()
        if c and c not in CHANNELS:
            return {"ok": False, "error": "unknown channel"}
        rec = {"ok": True, "id": "in_" + str(int(time.time() * 1000)),
               "channel": c or "ทั่วไป", "title": str(title or "")[:160],
               "asset_url": str(asset_url or "")[:300], "price": int(price or 0),
               "status": "ready_to_sell", "note": str(note or "")[:300], "t": int(time.time()),
               "honest": "ผลิตของแล้ว · การลงขาย/รับเงินต้องเจ้าของ"}
        with self.lock:
            self.entries.append(rec)
        self.save()
        return rec

    def affiliate(self, link="", note="", platform=""):
        """Owner supplies the affiliate link; Zyphere only makes promo content."""
        lk = str(link or "").strip()
        if not lk.startswith("http"):
            return {"ok": False, "error": "ต้องใส่ลิงก์ affiliate ที่เจ้าของได้มาจากแพลตฟอร์ม"}
        rec = {"ok": True, "id": "af_" + str(int(time.time() * 1000)),
               "link": lk[:500], "platform": str(platform or "")[:80],
               "note": str(note or "")[:300], "status": "promo_ready",
               "content": "Zyphere สามารถเขียนคำโปรโมต/ทำภาพ/คลิปสำหรับลิงก์นี้ได้",
               "honest": "ไม่สมัคร affiliate แทน · ไม่กดโพสต์ · เจ้าของเป็นคนลง", "t": int(time.time())}
        with self.lock:
            self.campaigns.append(rec)
        self.save()
        return rec

    def earned(self, channel="", amount=0, note=""):
        """Owner reports actual earnings (system never invents revenue)."""
        rec = {"ok": True, "t": int(time.time()), "channel": str(channel or "")[:80],
               "amount": int(amount or 0), "note": str(note or "")[:200],
               "source": "owner_reported", "honest": "รายได้จากเจ้าของแจ้ง — ระบบไม่แต่งยอด"}
        with self.lock:
            self.entries.append(rec)
        self.save()
        return rec

    def stats(self):
        with self.lock:
            assets = [e for e in self.entries if e.get("status") == "ready_to_sell"]
            earned = [e for e in self.entries if e.get("source") == "owner_reported"]
            return {"assets_ready": len(assets), "campaigns": len(self.campaigns),
                    "earned_reported": sum(e.get("amount", 0) for e in earned),
                    "honest": "ยอดมาจากเจ้าของแจ้งเท่านั้น"}

    def list(self, n=30):
        with self.lock:
            return list(reversed(self.entries[-n:]))

    def snapshot(self):
        with self.lock:
            return {"entries": self.entries[-2000:], "campaigns": self.campaigns[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "entries" in data:
                self.entries = data.get("entries", [])
                self.campaigns = data.get("campaigns", [])
                self.save()
                return True
        return False
