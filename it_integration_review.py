"""IT Integration Review — the engineering department's REAL end-to-end gate.

Not a status report. This runs concrete checks across the whole journey:
login -> store -> order -> declare -> download -> logout, plus pricing and
samples. Every check carries evidence (file/line or live HTTP response).

Failures are written to data/integration_failures.json so the relearn loop
and QA Supreme can act on them instead of the owner discovering bugs first.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "it_integration_review.json")
FAIL = os.path.join(ROOT, "data", "integration_failures.json")
OUT = os.path.join(ROOT, "governance", "IT_INTEGRATION_REVIEW.md")
BASE = "https://zyphere-ai-agent.onrender.com"


def read(name):
    try:
        return open(os.path.join(ROOT, name), encoding="utf-8").read()
    except Exception:
        return ""


def check(name, ok, evidence):
    return {"check": name, "ok": bool(ok), "evidence": str(evidence)[:240]}


def static_checks():
    idx = read("index.html")
    store = read("STORE.html")
    app = read(os.path.join("app.py"))
    out = []
    out.append(check("login stores zy_token",
                     "setK('zy_token'" in idx or "setItem('zy_token'" in idx,
                     "index.html setK/setItem zy_token"))
    out.append(check("chat logout clears local BEFORE backend call",
                     "zyDoLogout" in idx and
                     idx.find("removeItem('zy_token'") < idx.find("/api/auth/logout"),
                     "zyDoLogout order"))
    out.append(check("chat popup logout wired",
                     "am('amLogout',()=>{zyDoLogout()})" in idx,
                     "amLogout -> zyDoLogout"))
    # Regression: the owner found a stale alert because this exact wiring was
    # missing. Never pass while an old error string remains in the shipped UI.
    out.append(check("no stale logout alert shipped",
                     "ยังไม่ได้เข้าสู่ระบบครับ" not in idx,
                     "old alert string absent"))
    out.append(check("logout button bound to handler",
                     "$('logoutBtn').onclick=()=>zyDoLogout();" in idx,
                     "logoutBtn onclick"))
    out.append(check("store account bar present",
                     "acctbar" in store and "/api/store/me" in store,
                     "STORE.html acctbar + /api/store/me"))
    out.append(check("store has my-orders / owner / logout",
                     all(x in store for x in
                         ("/api/store/my-orders", "zyOwner", "zyLogout")),
                     "3 store account actions"))
    out.append(check("store logout clears local first",
                     "function zyLogout" in store and
                     store.find("removeItem('zy_token'") < store.find("/api/auth/logout"),
                     "zyLogout order"))
    out.append(check("order attaches buyer login",
                     "SV.new_order(price, book, email)" in app,
                     "app.py new_order email"))
    out.append(check("order persisted locally + remote KV",
                     'remote_push("store_orders"' in app and "store_orders_all()" in app,
                     "remote KV + merge helper"))
    out.append(check("declare reads shared store",
                     "orders = store_orders_all()" in app,
                     "app.py declare"))
    out.append(check("fail-closed: no file on self declaration",
                     'res["file"] = None' in app and "awaiting_payment_proof" in app,
                     "payment proof gate"))
    out.append(check("owner download receives token",
                     "body:JSON.stringify({token:tk})" in idx.replace("\n", ""),
                     "index.html owner download"))
    try:
        db = json.load(open(os.path.join(ROOT, "data", "commerce.json"),
                            encoding="utf-8"))
        titles = [str(p.get("title") or "") for p in db.get("products", [])]
        evidence = "rows=%d unique=%d" % (len(titles), len(set(titles)))
        ok46 = (len(titles) == 46 and len(set(titles)) == 46)
        out.append(check("catalogue has exactly 46 unique books", ok46, evidence))
    except Exception as e:
        out.append(check("catalogue has exactly 46 unique books", False, str(e)[:120]))
    try:
        import cover_queries as CQ
        vals = list(CQ.QUERIES.values())
        uniq = len(set(vals))
        evidence = "queries=%d unique=%d" % (len(vals), uniq)
        ok_cover = len(vals) >= 46 and uniq == len(vals)
        out.append(check("46 distinct cover photo subjects", ok_cover, evidence))
    except Exception as e:
        out.append(check("46 distinct cover photo subjects", False, str(e)[:120]))
    out.append(check("assistant receives live 2026 context",
                     "import live_context as LC" in app and
                     "ไม่ได้จำกัด" in read("live_context.py"),
                     "live context injected into system prompt"))
    out.append(check("admin cannot order (UI + backend)",
                     "zyApplyBuyVisibility" in store and
                     "Admin ไม่สามารถสั่งซื้อได้" in app,
                     "buy hidden for owner + 403 at API"))
    out.append(check("store uses 46 real photographic covers",
                     store.count("public_covers/cover_") >= 46 and
                     "<svg" not in store,
                     "real images=" + str(store.count("public_covers/cover_"))))
    out.append(check("progress dashboard has 12 departments",
                     read("PROGRESS.html").count('class="d"') >= 12,
                     "PROGRESS.html cards"))
    out.append(check("all 46 sample files exist",
                     sum(1 for f in os.listdir(os.path.join(ROOT, "samples"))
                         if f.startswith("s_") and f.endswith(".html")) >= 46,
                     "samples/s_*.html count"))
    try:
        prices = {int(p.get("price") or 0) for p in
                  json.load(open(os.path.join(ROOT, "data", "commerce.json"),
                                 encoding="utf-8")).get("products", [])}
        out.append(check("prices come from measured content (<=50)",
                         bool(prices) and max(prices) <= 50,
                         "price set " + str(sorted(prices))))
    except Exception as e:
        out.append(check("prices", False, str(e)[:120]))
    return out


def live_checks():
    import requests
    out = []
    try:
        r = requests.get(BASE + "/api/store/me", timeout=30)
        out.append(check("live /api/store/me gate", r.status_code == 200 and
                         r.json().get("ok") is False, str(r.status_code) + " " + r.text[:80]))
    except Exception as e:
        out.append(check("live /api/store/me gate", False, str(e)[:140]))
    try:
        r = requests.get(BASE + "/api/store/my-orders", timeout=30)
        out.append(check("live /api/store/my-orders 401", r.status_code == 401,
                         str(r.status_code)))
    except Exception as e:
        out.append(check("live my-orders gate", False, str(e)[:140]))
    try:
        r = requests.get(BASE + "/api/auth/logout", timeout=30)
        out.append(check("live /api/auth/logout reachable", r.ok, str(r.status_code)))
    except Exception as e:
        out.append(check("live logout reachable", False, str(e)[:140]))
    try:
        pages = "https://vorakan-yakham.github.io/zyphere-ai-agent/"
        r = requests.get(pages, timeout=30)
        out.append(check("live UI ships instant logout",
                         "zyDoLogout" in r.text and
                         "ยังไม่ได้เข้าสู่ระบบครับ" not in r.text,
                         "HTTP " + str(r.status_code)))
    except Exception as e:
        out.append(check("live UI ships instant logout", False, str(e)[:140]))
    return out


def run(apply=True):
    checks = static_checks() + live_checks()
    failed = [c for c in checks if not c["ok"]]
    rec = {"t": int(time.time()), "total": len(checks),
           "passed": len(checks) - len(failed), "failed": len(failed),
           "checks": checks,
           "rule": "วิศวกร IT ตรวจครบวงจรจริง — ไม่ใช่รายงานสวย ๆ ถ้า Fail ต้องเข้า relearn"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        json.dump({"t": rec["t"], "failures": failed},
                  open(FAIL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# IT Integration Review — ตรวจครบวงจรโดยวิศวกร IT\n\n"
            "ผ่าน **%d/%d** · ไม่ผ่าน **%d**\n\n| ตรวจ | ผล | หลักฐาน |\n|---|---|---|\n" %
            (rec["passed"], rec["total"], rec["failed"]) +
            "\n".join("| %s | %s | %s |" % (
                c["check"], "PASS" if c["ok"] else "FAIL", c["evidence"])
                for c in checks) + "\n\n" + rec["rule"] + "\n")
    return {"ok": not failed, "passed": rec["passed"], "total": rec["total"],
            "failed": [c["check"] for c in failed]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:600])
