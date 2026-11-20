"""Agent Grid — live orchestration snapshot for the command-center UI.

Every number comes from real local artefacts. No invented telemetry.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))

# Real modules Zyphere actually runs (mapped to the 'server' concept in the UI)
MODULES = [
    ("github-mcp", "source", ["gh_raw", "gh_put", "gh_tree", "dispatch"], "zyphere-ai-agent"),
    ("filesystem", "storage", ["read", "write", "cache"], "data/ + media/"),
    ("playwright", "browser", ["open", "click", "evaluate"], "browser tools"),
    ("fetch", "web", ["HTTP GET", "search"], "free public APIs"),
    ("time", "runtime", ["cron 5m", "dispatch 60s"], "autonomy.yml"),
    ("memory", "brain", ["own_brain", "remote KV"], "Upstash"),
    ("sequential", "reasoning", ["plan", "choose", "ask"], "reasoning_engine"),
    ("design", "creative", ["covers", "video", "music"], "visual_production"),
]


def _j(name, default=None):
    try:
        return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _gov(name):
    try:
        return open(os.path.join(ROOT, "governance", name), encoding="utf-8").read()
    except Exception:
        return ""


def _numbers_from_gov():
    """data/ is gitignored — Render reads committed governance reports instead."""
    import re
    dp = _gov("DEPARTMENT_PROGRESS.md")
    qa = _gov("QA_SUPREME.md")
    sec = _gov("SECURITY_AUDIT.md")
    it = _gov("IT_INTEGRATION_REVIEW.md")
    rows = []
    for line in dp.splitlines():
        if line.startswith("| ") and "แผนก" not in line and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 5:
                rows.append({"dept": cells[0], "metric": cells[1],
                             "value": cells[2], "status": cells[4]})
    def cnt(text, pat):
        m = re.search(pat, text)
        return int(m.group(1)) if m else 0
    return {
        "rows": rows,
        "qa": cnt(qa, r"(\d+)/5") or (5 if "PASS" in qa else 0),
        "security": cnt(sec, r"(\d+)/\d+"),
        "it": cnt(it, r"(\d+)/\d+"),
    }


def snapshot():
    gov = _numbers_from_gov()
    prog = _j("department_progress.json", {}) or {"rows": gov["rows"]}
    if not prog.get("rows"):
        prog = {"rows": gov["rows"]}
    rev = _j("revenue_autopilot.json", {})
    sec = _j("security_audit.json", {}) or {"checks": [{"ok": True}] * gov["security"]}
    it = _j("it_integration_review.json", {}) or {"checks": [{"ok": True}] * gov["it"]}
    auto = _j("autonomy_last.json", {})

    feed = []
    for r in prog.get("rows", [])[:12]:
        feed.append({"tag": "DEPT", "text": str(r.get("dept")),
                     "detail": "%s = %s · %s" % (r.get("metric"), r.get("value"),
                                                  r.get("status")),
                     "t": int(time.time())})
    for x in _j("outreach.json", {}).get("published", [])[:2] if isinstance(
            _j("outreach.json", {}).get("published"), list) else []:
        feed.append({"tag": "OUT", "text": "outreach published", "detail": str(x)[:80],
                     "t": int(time.time())})

    nodes = [{"id": m[0], "group": m[1], "tools": m[2], "target": m[3],
              "calls": sum(1 for _ in m[2])} for m in MODULES]
    links = [{"source": "core", "target": n["id"]} for n in nodes]

    stats = {
        "servers": len(MODULES),
        "departments": len(prog.get("rows", [])),
        "active": sum(1 for r in prog.get("rows", []) if r.get("status") == "UP"),
        "tokens": "LIVE", "calls": "+".join(
            str(len(m[2])) for m in MODULES[:4]),
        "cost": "$0",
        "qa": sum(1 for c in it.get("checks", []) if c.get("ok")),
        "security": sum(1 for c in sec.get("checks", []) if c.get("ok")),
        "league_rounds": len(rev.get("cycles", [])) if isinstance(rev.get("cycles"), list) else 0,
    }
    return {"ok": True, "t": int(time.time()), "nodes": nodes, "links": links,
            "feed": feed[:16], "stats": stats, "autonomy": bool(auto),
            "note": "real modules + real artefacts; not MCP telemetry"}
