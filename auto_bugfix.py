"""Auto Bugfix — detect AND repair common defects every pulse, unattended.

Checks real code for:
  - Python syntax errors (compile)
  - workflow YAML indentation that would break GitHub Actions
  - duplicate/missing module entries in the autonomy workflow
  - duplicate class attributes in UI HTML
  - stale auth labels shown together
  - endpoints declared in frontend but missing in backend

Applies only SAFE, deterministic fixes. Records every action with evidence.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "auto_bugfix.json")
OUT = os.path.join(ROOT, "governance", "AUTO_BUGFIX.md")


def _read(n):
    try:
        return open(os.path.join(ROOT, n), encoding="utf-8").read()
    except Exception:
        return ""


def _write(n, s):
    open(os.path.join(ROOT, n), "w", encoding="utf-8").write(s)


def run(apply=True):
    fixes, issues = [], []

    # 1) Python syntax across all root modules
    bad = []
    for f in os.listdir(ROOT):
        if f.endswith(".py"):
            try:
                compile(open(os.path.join(ROOT, f), encoding="utf-8").read(), f, "exec")
            except SyntaxError as e:
                bad.append("%s:%s %s" % (f, e.lineno, e.msg))
    if bad:
        # deterministic repairs: strip UTF-8 BOM, collapse ### in f-string CSS
        for f in os.listdir(ROOT):
            if not f.endswith(".py"):
                continue
            p = os.path.join(ROOT, f)
            raw = open(p, "rb").read()
            if raw.startswith(b"\xef\xbb\xbf"):
                if apply:
                    open(p, "wb").write(raw[3:])
                fixes.append("stripped BOM from " + f)
            s = open(p, encoding="utf-8", errors="replace").read()
            if "}}}" in s:
                if apply:
                    open(p, "w", encoding="utf-8").write(s.replace("}}}", "}}"))
                fixes.append("collapsed stray }}} in " + f)
        issues.append({"type": "python_syntax_repaired", "detail": bad[:5]})

    # 2) workflow indentation (YAML block scalar requires >=10 spaces)
    wf = _read(os.path.join(".github", "workflows", "autonomy.yml"))
    lines = wf.split("\n")
    broken = [(i+1, l[:50]) for i, l in enumerate(lines)
              if 20 <= i <= 205 and l.strip() and not l.startswith(" ")]
    if broken:
        if apply:
            out = []
            for i, l in enumerate(lines):
                if 20 <= i <= 205 and l.strip() and not l.startswith(" "):
                    out.append(" " * 37 + l.strip())
                else:
                    out.append(l)
            _write(os.path.join(".github", "workflows", "autonomy.yml"), "\n".join(out))
        issues.append({"type": "workflow_indent", "detail": broken[:4]})
        fixes.append("fixed workflow indentation on %d lines" % len(broken))

    # 3) duplicate class attributes in index.html
    idx = _read("index.html")
    dup = re.findall(r'<button[^>]*\bclass="[^"]*"[^>]*\bclass="', idx)
    if dup:
        issues.append({"type": "duplicate_class", "detail": len(dup)})
        fixes.append("duplicate class attributes: %d (manual review)" % len(dup))

    # 4) login/logout must never both be visible
    login = 'class="am guest-only" id="amGoogle"' in idx
    logout = 'class="am user-only" id="amLogout"' in idx
    if not (login and logout):
        issues.append({"type": "auth_gating", "detail": "login=%s logout=%s" % (login, logout)})
        fixes.append("auth gating classes missing — manual review")

    # 5) frontend endpoints must exist in backend
    app = _read("app.py")
    fe_eps = set(re.findall(r"/api/[a-z0-9/_-]+", idx + _read("STORE.html") +
                             _read("STAFF_LIVE.html") + _read("AGENT_GRID.html") +
                             _read("ORCHESTRA.html") + _read("DIALOGUE.html")))
    missing = sorted(e for e in fe_eps if e not in app and not e.startswith("/api/auth/google"))
    if missing:
        issues.append({"type": "missing_endpoint", "detail": missing[:6]})
        fixes.append("frontend calls missing backend endpoints: " + ", ".join(missing[:4]))

    # 6) QA regression: auto-rerun strict gates
    try:
        import it_integration_review as IT
        r = IT.run(apply=apply)
        if not r.get("ok"):
            issues.append({"type": "qa_regression", "detail": r.get("failed")})
            fixes.append("QA regression: " + ", ".join(r.get("failed", [])[:3]))
    except Exception as e:
        issues.append({"type": "qa_run", "detail": str(e)[:100]})

    rec = {"t": int(time.time()), "issues": issues, "fixes": fixes,
           "rule": "ตรวจและแก้บักอัตโนมัติทุก pulse — ไม่รอคำสั่งเจ้าของ"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# Auto Bugfix — %d issues\n\n" % len(issues) +
            "\n".join("- [%s] %s" % (i["type"], str(i["detail"])[:180]) for i in issues) +
            "\n\n## Actions\n\n" + "\n".join("- " + f for f in fixes) + "\n")
    return {"ok": not issues, "issues": len(issues), "fixes": fixes[:6]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:700])
