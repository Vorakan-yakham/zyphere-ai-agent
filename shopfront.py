"""Zyphere Shopfront - Zyphere's OWN store inside the app, so it can 'sell'
without any external account/OTP. Owner owns the shop and receives PromptPay.

Flow: Zyphere lists its produced assets (code/media/packs) with price + quote
-> buyers see catalog -> owner confirms PromptPay -> delivery auto-releases file.
This is the legal way for the AI to 'do the selling' inside its own system.

HONEST: no external marketplace login, no fake buyers, no auto bank access.
Revenue is owner-reported; system tracks orders/delivery only. No gambling/illegal.
"""
import os, json, time, threading

PROMPTPAY = "0941939686"


class Shopfront:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.products = []
        self.orders = []
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.products = d.get("products", [])
            self.orders = d.get("orders", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"products": self.products[-500:], "orders": self.orders[-1000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def list_product(self, title="", price=0, asset_url="", desc="", category=""):
        t = str(title or "").strip()
        if not t:
            return {"ok": False, "error": "missing title"}
        p = {"ok": True, "id": "sp_" + str(int(time.time() * 1000)),
             "title": t[:160], "price": int(price or 0), "asset_url": str(asset_url or "")[:300],
             "desc": str(desc or "")[:300], "category": str(category or "digital")[:60],
             "seller": "Zyphere", "promptpay": PROMPTPAY, "status": "live", "t": int(time.time())}
        with self.lock:
            self.products.append(p)
        self.save()
        return p

    def catalog(self):
        with self.lock:
            return {"ok": True, "products": [p for p in self.products if p.get("status") == "live"],
                    "seller": "Zyphere", "promptpay": PROMPTPAY}

    def order(self, product_id="", buyer=""):
        prod = next((p for p in self.products if p["id"] == product_id and p.get("status") == "live"), None)
        if not prod:
            return {"ok": False, "error": "product not found"}
        o = {"ok": True, "id": "so_" + str(int(time.time() * 1000)),
             "product_id": product_id, "title": prod["title"], "price": prod["price"],
             "buyer": str(buyer or "")[:120], "pay_to": PROMPTPAY,
             "status": "awaiting_payment", "asset_url": prod["asset_url"], "t": int(time.time())}
        with self.lock:
            self.orders.append(o)
        self.save()
        return o

    def confirm(self, oid=""):
        """Owner confirms payment -> file released (delivery happens)."""
        with self.lock:
            o = next((x for x in self.orders if x["id"] == oid), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            o["status"] = "paid_delivered"
            o["delivered_at"] = int(time.time())
        self.save()
        return {"ok": True, "order": o, "note": "เงินเข้าบัญชีเจ้าของผ่าน PromptPay — ระบบปลดไฟล์ให้แล้ว"}

    def stats(self):
        with self.lock:
            paid = [o for o in self.orders if o.get("status") == "paid_delivered"]
            return {"products": len([p for p in self.products if p.get("status") == "live"]),
                    "orders": len(self.orders), "paid": len(paid),
                    "revenue": sum(o.get("price", 0) for o in paid),
                    "honest": "ยอดจาก order ที่เจ้าของยืนยันเท่านั้น"}

    def snapshot(self):
        with self.lock:
            return {"products": self.products[-500:], "orders": self.orders[-1000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "products" in data:
                self.products = data.get("products", [])
                self.orders = data.get("orders", [])
                self.save()
                return True
        return False
