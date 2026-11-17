"""Zyphere Delivery - turn a paid order into a DELIVERED asset automatically.

Owner's core goal: knowledge -> real income. After payment confirmed, the
customer/owner receives a deliverable ( Pro entitlement, portfolio pack,
custom media work) with a tracked delivery record. No empty "thank you page".

HONEST: produces delivery records + download-ready assets from local tools;
actual bank transfer verification stays manual (PromptPay slip). No auto
external posting (needs owner account/OTP). No gambling/illegal.
"""
import os, json, time, threading

ASSETS = {
    "pro": {"name": "Zyphere Pro", "type": "entitlement", "desc": "ปลดล็อกโควต้า AI/วิดีโอ/เสียงพรีเมียม"},
    "lifetime": {"name": "Zyphere Lifetime", "type": "entitlement", "desc": "ฟีเจอร์ทั้งหมดตลอดชีวิต"},
    "portfolio": {"name": "พอร์ตผลงานรับจ้าง", "type": "pack", "desc": "4 ตัวอย่างงาน: เขียน/แปล/วิเคราะห์/โค้ด"},
    "media_pack": {"name": "แพ็กสื่อสร้างสรรค์", "type": "pack", "desc": "คลิป+เสียง+เพลง+ซับ ผลิตโดย Zyphere"},
    "custom_work": {"name": "งานตามสั่ง", "type": "custom", "desc": "ผลงานที่ Zyphere ผลิตให้ตามโจทย์"},
}


class Delivery:
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
                json.dump({"records": self.records[-2000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def deliver(self, order_id="", asset="pro", customer="", note=""):
        """Create a delivery record after payment; ready to download/claim."""
        a = str(asset or "pro")
        info = ASSETS.get(a, ASSETS["custom_work"])
        rec = {"ok": True, "id": "d_" + str(int(time.time() * 1000)),
               "order_id": str(order_id)[:80], "customer": str(customer or "")[:120],
               "asset": a, "name": info["name"], "type": info["type"], "desc": info["desc"],
               "status": "ready", "note": str(note or "")[:300], "t": int(time.time()),
               "download": ("/media/" + str(note)[:80]) if info["type"] == "pack" else None}
        with self.lock:
            self.records.append(rec)
        self.save()
        return rec

    def pending(self):
        with self.lock:
            return [r for r in self.records if r.get("status") == "ready"]

    def stats(self):
        with self.lock:
            return {"deliveries": len(self.records), "pending": len(self.pending()),
                    "revenue_ready": sum(1 for r in self.records if r.get("status") == "ready")}

    def snapshot(self):
        with self.lock:
            return {"records": self.records[-2000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "records" in data:
                self.records = data.get("records", [])
                self.save()
                return True
        return False
