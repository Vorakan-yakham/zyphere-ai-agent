"""Security Audit — concrete code checks, run every pulse. Never stores values."""
import os, re, json, time
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "security_audit.json")
OUT = os.path.join(ROOT, "governance", "SECURITY_AUDIT.md")


def run(apply=True):
    app = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    checks = []
    def c(n, ok, ev=""):
        checks.append({"check": n, "ok": bool(ok), "evidence": str(ev)[:160]})
    c("no wildcard CORS", 'Access-Control-Allow-Origin", "*"' not in app)
    c("CORS allowlist", "_allowed_origin" in app and "ALLOWED_ORIGINS" in app)
    c("nosniff", "X-Content-Type-Options" in app)
    c("clickjacking guard", "X-Frame-Options" in app and "DENY" in app)
    c("referrer policy", "Referrer-Policy" in app and "no-referrer" in app)
    c("POST rate limit", "_rate_ok(self)" in app and "429" in app)
    c("admin gate", "forbidden — admin only" in app)
    c("payment fail-closed", 'res["file"] = None' in app)
    bad = [x for x in checks if not x["ok"]]
    rec = {"t": int(time.time()), "total": len(checks),
           "passed": len(checks) - len(bad), "checks": checks,
           "note": "secrets stay in Render env, never in repo"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# Security Audit — %d/%d PASS\n\n| ตรวจ | ผล |\n|---|---|\n" %
            (rec["passed"], rec["total"]) +
            "\n".join("| %s | %s |" % (x["check"], "PASS" if x["ok"] else "FAIL")
                      for x in checks) + "\n")
    return {"ok": not bad, "passed": rec["passed"], "total": rec["total"]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
