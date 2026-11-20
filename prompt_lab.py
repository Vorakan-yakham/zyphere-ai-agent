"""Prompt Lab — visualise how role / objective / context / rules / review /
execution fit together, using REAL Zyphere artefacts (no invented metrics).
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))

SEGMENTS = ["prompt creator", "objective", "context", "rules", "review", "execution"]


def _read(name):
    try:
        return open(os.path.join(ROOT, name), encoding="utf-8").read()
    except Exception:
        return ""


def _gov(name):
    return _read(os.path.join("governance", name))


def snapshot():
    idx = _read("index.html")
    app = _read(os.path.join("app.py"))
    live = _read("live_context.py")
    design = _gov("SYSTEM_DESIGN.md")
    directive = _gov("JARVIS_DIRECTIVE.md")
    qa = _gov("QA_SUPREME.md")
    it = _gov("IT_INTEGRATION_REVIEW.md")

    # REAL section keyword counts from committed governance + prompt source
    keys = {
        "objective": ["เป้าหมาย", "objective", "target", "goal"],
        "context": ["บริบท", "context", "ข้อมูลสด", "2026"],
        "role": ["role", "แผนก", "owner", "admin"],
        "rules": ["กฎ", "rule", "ห้าม", "fail-closed", "security"],
        "review": ["QA", "ตรวจ", "review", "audit"],
        "execution": ["workflow", "pulse", "run", "dispatch"],
    }
    corpus = "\n".join([idx[:60000], app[:60000], live, design, directive, qa, it]).lower()
    sections = {}
    for k, words in keys.items():
        sections[k] = sum(len(re.findall(r"(?<!\w)" + re.escape(w.lower()) + r"(?!\w)", corpus))
                          for w in words)
    total = max(1, sum(sections.values()))

    # crawl log: real files actually read to build this view
    files = ["index.html", "app.py", "live_context.py",
             "governance/SYSTEM_DESIGN.md", "governance/JARVIS_DIRECTIVE.md",
             "governance/QA_SUPREME.md", "governance/IT_INTEGRATION_REVIEW.md"]
    crawl = []
    for f in files:
        txt = _read(f)
        crawl.append({"file": f, "lines": txt.count("\n") + 1,
                      "words": len(re.findall(r"\S+", txt))})

    # graph nodes from real artefacts
    nodes = [
        {"id": "prompt creator", "n": 1, "group": "core"},
        {"id": "objective", "n": sections["objective"], "group": "pink"},
        {"id": "context", "n": sections["context"], "group": "pink"},
        {"id": "rules", "n": sections["rules"], "group": "pink"},
        {"id": "role", "n": sections["role"], "group": "cyan"},
        {"id": "review", "n": sections["review"], "group": "cyan"},
        {"id": "execution", "n": sections["execution"], "group": "cyan"},
    ]
    links = [{"source": "prompt creator", "target": n["id"]} for n in nodes[1:]]

    # word heat: real keyword occurrences in 6 bands
    heat = []
    bands = ["objective", "context", "rules", "role", "review", "execution"]
    for b in bands:
        heat.append({"band": b, "v": sections[b]})

    # honest score: share of QA gates passed (not a decorative number)
    m = re.search(r"(\d+)/(\d+)", it)
    passed, totalq = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    score = round(passed / totalq * 100) if totalq else 0

    return {"ok": True, "t": int(time.time()), "segments": SEGMENTS,
            "nodes": nodes, "links": links, "sections": sections,
            "coverage": round(total / 1000, 1), "crawl": crawl,
            "heat": heat, "score": score,
            "code": live[:600],
            "note": "all counts from real committed files — no fabricated telemetry"}


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False)[:400])
