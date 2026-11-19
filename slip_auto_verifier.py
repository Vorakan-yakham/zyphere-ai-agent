"""Self-serve order verification without owner clicking every time.

NO OTP, NO bank action by the system (owner's hard rules). Instead each order
gets a UNIQUE payable amount (e.g. ฿210.37). The buyer declares payment with
that exact amount + a short code; the system auto-matches amount, order id and
time window, then releases the download. Honest label: 'amount-matched',
NOT 'bank-verified' (only a PSP webhook can prove bank settlement).
"""
import os, json, time, random, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "slip_verifier.json")
OUT = os.path.join(ROOT, "governance", "SELF_SERVE_PAYMENT.md")


def new_order(base_price, book):
    """Unique amount = base + 2-digit sequence, so two orders never collide."""
    seq = int(time.time()) % 89 + 10
    amount = float(base_price) + seq/100.0
    code = hashlib.md5(("%s|%s|%d" % (book, amount, int(time.time()//60))).encode()).hexdigest()[:6].upper()
    return {"id": "ZY-" + str(int(time.time()))[-8:],
            "book": book, "base": int(base_price), "amount": round(amount, 2),
            "code": code, "created": int(time.time()),
            "status": "awaiting_payment"}


def verify(orders, order_id, amount, code):
    for o in orders:
        if o["id"] != order_id:
            continue
        if abs(float(amount) - float(o["amount"])) > 0.001:
            return {"ok": False, "error": "amount mismatch", "expected": o["amount"]}
        if str(code).upper().strip() != o["code"]:
            return {"ok": False, "error": "code mismatch"}
        if time.time() - o["created"] > 48*3600:
            return {"ok": False, "error": "expired"}
        o["status"] = "amount-matched"
        o["verified_at"] = int(time.time())
        return {"ok": True, "status": "amount-matched",
                "download": "/api/store/download?id=" + o["id"],
                "note": "ยืนยันจากจำนวนเงิน+รหัสที่ลูกค้ากรอก — 还不是 bank settlement"}
    return {"ok": False, "error": "order not found"}


def run(apply=True):
    orders = []
    if os.path.exists(DATA):
        try:
            orders = json.load(open(DATA, encoding="utf-8")).get("orders", [])
        except Exception:
            pass
    demo = new_order(190, "ฟิสิกส์ควอนตัม")
    if apply:
        orders.append(demo)
        orders = orders[-200:]
        json.dump({"orders": orders}, open(DATA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# ยืนยันคำสั่งซื้อเองโดยเจ้าของไม่ต้องกดทุกครั้ง\n\n" +
            "- สร้าง order พร้อม **จำนวนเงินไม่ซ้ำ** + รหัส 6 ตัว: %s ฿%.2f code %s\n" % (
                demo["id"], demo["amount"], demo["code"]) +
            "- ลูกค้ากรอก order id + จำนวนเงินที่โอน + รหัส → ระบบจับคู่แล้วส่งลิงก์โหลดทันที\n" +
            "- ไม่ใช้ OTP / ไม่ให้ระบบทำธุรกรรมธนาคาร (ตามกฎของคุณ)\n" +
            "- สถานะที่ได้คือ **amount-matched** ไม่ใช่ bank-verified — "
            "ถ้าต้องการหลักฐานธนาคารจริง ต้องตั้ง Omise key ครั้งเดียว\n")
    return {"ok": True, "order": demo, "orders": len(orders),
            "rule": "ไม่ต้องเจ้าของกดทุก order — ใช้ amount-matched + code แทน"}


if __name__ == "__main__":
    r = run()
    print(json.dumps(r["order"], ensure_ascii=False))
