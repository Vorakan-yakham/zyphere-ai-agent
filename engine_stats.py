"""Publish AGGREGATE engine statistics to the product repo (no private text).

Render has no persistent disk, so Five Engines reads these counts from GitHub.
Only numbers and safe metadata are published — never personal memory content.
"""
import os, json, time, subprocess, base64, requests

ROOT = r"C:\Users\vornl\Documents\zyphere"
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"


def load(name):
    try:
        return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))
    except Exception:
        return {}


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def main():
    kn, rs, cl, og = (load(x) for x in
                      ("knowledge.json", "research.json", "co_learning.json", "orders.json"))
    docs = rs.get("documents", []) if isinstance(rs, dict) else []
    rel = {}
    for x in docs:
        if isinstance(x, dict):
            k = x.get("reliability", "?")
            rel[k] = rel.get(k, 0) + 1
    log = cl.get("log", []) if isinstance(cl, dict) else []
    stats = {
        "t": int(time.time()),
        "knowledge_items": len(kn.get("items", [])) if isinstance(kn, dict) else 0,
        "research_documents": len(docs), "by_reliability": rel,
        "learning_sessions": len(log),
        "learning_departments": len({r.get("dept") for r in log if r.get("dept")}),
        "doctor_lessons": sum(len(r.get("lessons", [])) for r in log
                              if r.get("level") == "doctor"),
        "cross_lessons": sum(len(r.get("lessons", [])) for r in log
                             if r.get("level") == "cross-disciplinary"),
        "shop_orders": len(og.get("orders", [])) if isinstance(og, dict) else 0,
        "note": "aggregate counts only — no private memory text",
    }
    h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
    url = BASE + "engine_stats.json"
    sha = None
    try:
        g = requests.get(url, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
    except Exception:
        pass
    p = {"message": "Engine aggregate stats " + str(int(time.time())),
         "content": base64.b64encode(json.dumps(stats, ensure_ascii=False).encode()).decode(),
         "branch": "main"}
    if sha:
        p["sha"] = sha
    r = requests.put(url, headers=h, json=p, timeout=30)
    print("published", r.status_code, stats)


if __name__ == "__main__":
    main()
