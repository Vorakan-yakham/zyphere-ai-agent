"""UI Functional Audit — proactively find dead buttons, empty pages and stale
hardcoded identities BEFORE the owner has to report them.

Checks are static but concrete (handler presence, page existence, visible text
volume, dynamic loading, no stale owner name). Results feed integration_failures.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "ui_functional_audit.json")
FAIL = os.path.join(ROOT, "data", "integration_failures.json")
OUT = os.path.join(ROOT, "governance", "UI_FUNCTIONAL_AUDIT.md")


def read(name):
    try:
        return open(os.path.join(ROOT, name), encoding="utf-8").read()
    except Exception:
        return ""


def run(apply=True):
    idx = read("index.html")
    checks = []

    def c(name, ok, ev=""):
        checks.append({"check": name, "ok": bool(ok), "evidence": str(ev)[:180]})

    # 1) every declared button has SOME handler
    ids = re.findall(r'<button[^>]*id="([A-Za-z0-9_]+)"', idx)
    dead = []
    for i in ids:
        patterns = [
            r"\$\('" + i + r"'\)\.onclick",
            r"getElementById\('" + i + r"'\)\.onclick",
            r"getElementById\('" + i + r"'\)\.addEventListener",
            r"am\('" + i + r"'",
            r"'" + i + r"'\s*,\s*\(",
        ]
        # Some handlers are attached through a variable
        # (const b = getElementById(id); b.addEventListener(...)) or inside a
        # helper. A JS reference beyond the HTML declaration counts as wired.
        refs = idx.count("'" + i + "'") + idx.count('"' + i + '"')
        if not any(re.search(p, idx) for p in patterns) and refs < 2:
            dead.append(i)
    c("all %d buttons have handlers" % len(ids), not dead, "dead=" + str(dead[:8]))

    # 2) no stale hardcoded identity
    c("no hardcoded owner name", "vorakan_yakham" not in idx, "clean")
    c("identity loader exists", "zyApplyIdentity" in idx and 'id="acctName"' in idx)

    # 3) the 5 thin chat-shortcut buttons must open REAL destinations
    real = {
        "amProfile": "ACCOUNT.html", "amMusic": "STUDIO.html",
        "amIncome": "GROWTH.html", "amBrief": "PROGRESS.html",
    }
    for bid, page in real.items():
        m = re.search(r"am\('" + bid + r"',\s*\(\)=>\{window\.open\('" +
                      re.escape(page) + r"'", idx)
        c(bid + " opens real page", bool(m), page)
    c("amVideo opens video modal",
      bool(re.search(r"am\('amVideo',\s*\(\)=>\{if\(typeof openVideo", idx)))

    # 4) every referenced page exists and is not a near-empty shell
    targets = set(re.findall(r"(?:window\.open\('|href=\")([A-Za-z0-9_\-]+\.html)", idx))
    targets |= {"STORE.html", "PROGRESS.html", "ACCOUNT.html", "STUDIO.html",
                "GROWTH.html", "GOVERNANCE.html", "CATEGORIES.html"}
    thin, missing = [], []
    for f in sorted(targets):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            missing.append(f)
            continue
        t = read(f)
        txt = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", t)
        txt = re.sub(r"<[^>]+>", " ", txt)
        words = len(re.findall(r"\S+", txt))
        if words < 10 and "fetch(" not in t:
            thin.append(f + "(" + str(words) + ")")
    c("all referenced pages exist", not missing, "missing=" + str(missing))
    c("no empty static pages", not thin, "thin=" + str(thin))

    bad = [x for x in checks if not x["ok"]]
    rec = {"t": int(time.time()), "total": len(checks),
           "passed": len(checks) - len(bad), "failed": len(bad),
           "checks": checks,
           "rule": "ตรวจเชิงรุก — ปุ่มตาย/หน้าโล่ง/ชื่อค้าง ต้องเจอก่อนเจ้าของ"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        try:
            prev = json.load(open(FAIL, encoding="utf-8")).get("failures", [])
        except Exception:
            prev = []
        json.dump({"t": rec["t"],
                   "failures": prev + [{"source": "ui_audit", **x} for x in bad][-50:]},
                  open(FAIL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# UI Functional Audit\n\nผ่าน **%d/%d**\n\n| ตรวจ | ผล | หลักฐาน |\n|---|---|---|\n" %
            (rec["passed"], rec["total"]) +
            "\n".join("| %s | %s | %s |" %
                      (x["check"], "PASS" if x["ok"] else "FAIL", x["evidence"])
                      for x in checks) + "\n")
    return {"ok": not bad, "passed": rec["passed"], "total": rec["total"],
            "failed": [x["check"] for x in bad]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:600])
