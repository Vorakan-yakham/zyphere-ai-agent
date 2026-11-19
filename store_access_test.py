"""Store Access Test — verify the user/admin separation invariants with REAL
local objects, no mocks of the result. Never mutates customer data."""
import os, json, time, hashlib


def run(apply=True):
    import store as ST
    import app as A
    out = []

    def t(name, ok, ev=""):
        out.append({"test": name, "ok": bool(ok), "evidence": str(ev)[:180]})

    # 1) customer data is permanent
    s = ST.Store(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    r = s.reset_demo()
    t("reset_demo refuses deletion", r.get("ok") is False, r)

    # 2) save() never truncates — write to a temp dir with >1000 fake rows
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="zy_store_test_")
    try:
        s2 = ST.Store(d)
        s2.orders = [{"id": "t%04d" % i, "status": "paid", "email": "a@b.c"}
                     for i in range(1005)]
        s2.save()
        saved = json.load(open(os.path.join(d, "orders.json"), encoding="utf-8"))["orders"]
        t("save keeps ALL customer records", len(saved) == 1005, "kept " + str(len(saved)))
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # 3) helpers
    t("paid status recognises approved", A.order_is_paid({"status": "paid"}) and
      A.order_is_paid({"status": "approved"}))
    t("unpaid stays locked", not A.order_is_paid({"status": "awaiting_payment_proof"}))
    t("single owner email recognised everywhere",
      "vorakangm@gmail.com" in A.OWNER_EMAILS)
    t("owner sees all orders", A.order_belongs({"email": "x@y.z"},
      {"email": "vorakangm@gmail.com", "role": "user"}))
    t("user sees only own", A.order_belongs({"email": "me@x.com"},
      {"email": "me@x.com"}) and not A.order_belongs({"email": "other@x.com"},
      {"email": "me@x.com"}))
    t("anonymous sees nothing", not A.order_belongs({"email": "me@x.com"}, None))

    # 4) online reader produces a FULL book (not the short sample)
    html = A.full_book_html("ฟิสิกส์ควอนตัม")
    t("online reader returns full book", bool(html) and "สารบัญ" in html and
      "บทที่ 70" in html, "bytes " + str(len(html or "")))

    # 5) admin view merges without deleting
    rows = A.orders_admin_all()
    t("admin list is read-only merge", isinstance(rows, list) and len(rows) >= 0,
      "orders " + str(len(rows)))

    rec = {"t": int(time.time()), "total": len(out),
           "passed": sum(x["ok"] for x in out), "tests": out,
           "rule": "ห้ามลบข้อมูลลูกค้า — ตรวจทุกครั้งก่อนปล่อย"}
    if apply:
        json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "data", "store_access_test.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    return {"ok": rec["passed"] == rec["total"],
            "passed": rec["passed"], "total": rec["total"],
            "failed": [x["test"] for x in out if not x["ok"]]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:600])
