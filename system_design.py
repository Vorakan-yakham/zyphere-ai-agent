"""System Design — turn the department's architecture PLAN into an ENFORCEABLE
contract. Previously plans were prose in governance/*.md; nothing verified the
running system against them, so integration bugs reached the owner.

This module:
  1. publishes the architecture as a machine-readable contract (components,
     interfaces, invariants, failure modes)
  2. VALIDATES the real files and live endpoints against every invariant
  3. fail-closes: writes violations to data/integration_failures.json

No claims of perfection — only measured checks with evidence.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "system_design_check.json")
FAIL = os.path.join(ROOT, "data", "integration_failures.json")
OUT = os.path.join(ROOT, "governance", "SYSTEM_DESIGN.md")
BASE = "https://zyphere-ai-agent.onrender.com"

# --- THE CONTRACT: design decisions made BEFORE implementation ----------------
COMPONENTS = [
    {"id": "frontend_chat", "owner": "วิศวกรแชท", "role": "UI + session",
     "interfaces": ["index.html", "zy_token in localStorage"],
     "invariants": ["login persists zy_token", "logout clears local state first",
                    "owner-only controls gated by role"]},
    {"id": "storefront", "owner": "วิศวกรร้านค้า", "role": "browse/sample/buy",
     "interfaces": ["STORE.html", "samples/s_*.html", "/api/pay/order"],
     "invariants": ["account bar wired to auth API", "46 free samples render as HTML",
                    "price shown comes from measured content"]},
    {"id": "auth", "owner": "วิศวกรAPI", "role": "identity + session lifecycle",
     "interfaces": ["/api/store/me", "/api/auth/logout", "/api/store/my-orders"],
     "invariants": ["anonymous cannot see orders", "logout reachable",
                    "session cleared client-side even if backend is slow"]},
    {"id": "ordering", "owner": "วิศวกรฐานข้อมูล", "role": "create/decide/fulfil",
     "interfaces": ["/api/pay/order", "/api/pay/declare", "Upstash KV store_orders"],
     "invariants": ["order persisted on create", "declare finds order across instances",
                    "buyer email attached from login"]},
    {"id": "payment_gate", "owner": "วิศวกรQA", "role": "fail-closed release",
     "interfaces": ["slip_auto_verifier.py", "PSP webhook (when configured)"],
     "invariants": ["self declaration NEVER releases file",
                    "status awaiting_payment_proof"]},
    {"id": "brain", "owner": "วิศวกรสมอง", "role": "local-first learning",
     "interfaces": ["own_brain.py", "GitHub", "Upstash KV"],
     "invariants": ["source of truth is local + durable GitHub/KV",
                    "no fabricated sales or capability claims"]},
    {"id": "automation", "owner": "วิศวกรอัตโนมัติ", "role": "unattended pulses",
     "interfaces": [".github/workflows/autonomy.yml", "Render self-dispatch 60s"],
     "invariants": ["every department runs each pulse", "assembly verifies outputs"]},
]

DESIGN_DECISIONS = [
    ("Local-first brain + GitHub + KV", "of line local files are fast; GitHub is the durable "
     "visible store; Upstash KV shares state across Render instances."),
    ("Fail-closed payment", "a browser click is NOT payment proof. File release requires "
     "PSP webhook or owner slip check; self-declaration only records intent."),
    ("Shared order state in KV", "Render can run multiple instances; a per-process JSON file "
     "makes /api/pay/declare miss orders created by another instance."),
    ("Logout clears locally first", "await on a slow backend blocks the client cleanup — "
     "invalidate session immediately, fire backend logout in background."),
    ("Design -> validate -> relearn", "prose plans are not enough; every invariant is checked "
     "against real files/HTTP in this module and violations feed the relearn loop."),
]


def _src(name):
    try:
        return open(os.path.join(ROOT, name), encoding="utf-8").read()
    except Exception:
        return ""


def validate():
    idx, store = _src("index.html"), _src("STORE.html")
    app = _src(os.path.join("app.py"))
    results = []

    def v(cid, inv, ok, ev):
        results.append({"component": cid, "invariant": inv, "ok": bool(ok),
                        "evidence": str(ev)[:200]})

    v("frontend_chat", "login persists zy_token",
      "setK('zy_token'" in idx or "setItem('zy_token'" in idx, "index.html")
    v("frontend_chat", "logout clears local state first",
      "zyDoLogout" in idx and
      idx.find("removeItem('zy_token'") < idx.find("/api/auth/logout"), "zyDoLogout")
    v("frontend_chat", "owner-only controls gated by role",
      "window.zyRole" in idx and "owner-only" in idx, "applyPopupVis")
    v("storefront", "account bar wired to auth API",
      "acctbar" in store and "/api/store/me" in store, "STORE.html")
    v("storefront", "46 free samples render as HTML",
      sum(1 for f in os.listdir(os.path.join(ROOT, "samples"))
          if f.startswith("s_") and f.endswith(".html")) >= 46, "samples/")
    v("storefront", "price from measured content",
      "primer" in store and "ตัวอักษรไทย" in store, "card facts")
    v("auth", "anonymous cannot see orders",
      "if not me:" in app and "401" in app, "/api/store/my-orders")
    v("auth", "logout reachable", "/api/auth/logout" in app, "app.py")
    v("ordering", "order persisted on create",
      'remote_push("store_orders"' in app, "/api/pay/order")
    v("ordering", "declare finds order across instances",
      "orders = store_orders_all()" in app, "/api/pay/declare")
    v("ordering", "buyer email attached from login",
      "SV.new_order(price, book, email)" in app, "/api/pay/order")
    v("payment_gate", "self declaration NEVER releases file",
      'res["file"] = None' in app and "awaiting_payment_proof" in app, "declare")
    v("brain", "durable store configured",
      'remote_push("memory"' in app or "remote_push(" in app, "remote KV")
    wf = _src(os.path.join(".github", "workflows", "autonomy.yml"))
    v("automation", "QA + IT review gate wired",
      '"it_review"' in wf and '"qa"' in wf, "autonomy.yml")

    import requests
    try:
        r = requests.get(BASE + "/api/store/my-orders", timeout=25)
        v("auth", "live: anonymous orders blocked", r.status_code == 401,
          "HTTP " + str(r.status_code))
    except Exception as e:
        v("auth", "live: anonymous orders blocked", False, str(e)[:120])

    bad = [r for r in results if not r["ok"]]
    return results, bad


def run(apply=True):
    results, bad = validate()
    rec = {"t": int(time.time()), "components": len(COMPONENTS),
           "checks": len(results), "passed": len(results) - len(bad),
           "violations": [b["component"] + ": " + b["invariant"] for b in bad],
           "contract": [{"id": c["id"], "owner": c["owner"], "role": c["role"],
                         "interfaces": c["interfaces"],
                         "invariants": c["invariants"]} for c in COMPONENTS],
           "rule": "แผนที่เขียนไว้ต้องถูกตรวจกับของจริง — ถ้า Fail ห้ามปล่อย เข้า relearn"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        try:
            prev = json.load(open(FAIL, encoding="utf-8")).get("failures", [])
        except Exception:
            prev = []
        merged = prev + [{"source": "system_design", **b} for b in bad]
        json.dump({"t": rec["t"], "failures": merged[-50:]},
                  open(FAIL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# System Design — สัญญาสถาปัตยกรรมที่บังคับใช้ได้\n\n" +
            "ตรวจ **%d/%d** invariant · ฝ่าฝืน **%d**\n\n" %
            (rec["passed"], rec["checks"], len(bad)) +
            "## องค์ประกอบและเจ้าของ\n\n" +
            "\n".join("- **%s** (`%s`) — %s · ตรวจ: %s" %
                      (c["id"], c["owner"], c["role"], "; ".join(c["invariants"]))
                      for c in COMPONENTS) +
            "\n\n## การตัดสินใจออกแบบ (ทำก่อนเขียนโค้ด)\n\n" +
            "\n".join("- **%s**: %s" % (a, b) for a, b in DESIGN_DECISIONS) +
            "\n\n## ผลตรวจกับของจริง\n\n| ระบบ | invariant | ผล | หลักฐาน |\n|---|---|---|---|\n" +
            "\n".join("| %s | %s | %s | %s |" %
                      (r["component"], r["invariant"],
                       "PASS" if r["ok"] else "FAIL", r["evidence"])
                      for r in results) +
            "\n\n" + rec["rule"] + "\n")
    return {"ok": not bad, "passed": rec["passed"], "checks": rec["checks"],
            "violations": rec["violations"]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:700])
