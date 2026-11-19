"""Order Clarity — a calm, truthful overview. Never fabricates orders.
Groups REAL orders by status, flags duplicates, and shows the single manual
verification mode. The owner sees one screen, not a flood of noise.
"""
import os, json, time, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "ORDER_CLARITY.md")
DATA = os.path.join(ROOT, "data", "order_clarity.json")


def local_orders():
    rows = []
    for p in glob.glob(os.path.join(ROOT, "data", "*order*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
            items = d.get("orders", []) if isinstance(d, dict) else d
            for x in items:
                if isinstance(x, dict):
                    rows.append({"id": x.get("id") or x.get("order_id"),
                                 "status": x.get("status", "unknown"),
                                 "amount": x.get("amount"),
                                 "source": os.path.basename(p)})
        except Exception:
            pass
    return rows


def run(apply=True):
    rows = local_orders()
    by_status = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    ids = [r["id"] for r in rows if r["id"]]
    dupes = len(ids) - len(set(ids))
    rec = {"t": int(time.time()), "total": len(rows), "by_status": by_status,
           "duplicates": dupes, "mode": "manual (Omise ไม่ได้ตั้งค่า)",
           "public_endpoints": "/api/store/stats + /api/store/orders ต้อง admin (403 สำหรับคนทั่วไป)",
           "note": "ระบบไม่สร้าง order ปลอม — ยังไม่มียอดขายจริง ถ้าเห็น order แปลว่ามีคนส่งจริง"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# ภาพรวม Order (อ่านง่าย ไม่สร้างความสับสน)\n\n" +
            "- 订单จริงทั้งหมด: **%d**\n" % rec["total"] +
            "- แยกสถานะ: " + json.dumps(by_status, ensure_ascii=False) + "\n" +
            "- รายการซ้ำ: %d\n" % dupes +
            "- โหมด: %s\n" % rec["mode"] +
            "- %s\n\n" % rec["note"] +
            "หมายเหตุ: `/api/store/orders` ตอบ 403 สำหรับคนทั่วไป — "
            "เป็นการป้องกัน ไม่ใช่ order ระเบิด\n")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"total": r["total"], "mode": r["mode"]}, ensure_ascii=False))
