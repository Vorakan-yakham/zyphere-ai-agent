"""Reasoning Engine v2 — NO lookup table, NO taught 'if gap X do Y'.
It observes, ranks candidates by MEASURED past effect, explores when uncertain,
acts, measures the delta, and updates its own strategy. This is the logic of
thinking rather than waiting for instructions.
"""
import os, json, time, math, random

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "reasoning_engine.json")
OUT = os.path.join(ROOT, "governance", "REASONING_ENGINE.md")

# Candidate actions are just names. The engine does NOT know which is 'right';
# it LEARNS from measured deltas which one helps the current objective.
CANDIDATES = [
    "qa_supreme", "cover_designer", "storefront_rebuild", "autonomous_scout",
    "department_scouts", "poster_studio", "revenue_autopilot", "own_brain",
    "image_quality_loop", "future_roadmap", "wish_cycle", "cross_ask",
]


def state():
    s = {}
    files = {
        "qa": ("data/qa_supreme.json", lambda d: (d.get("total",0)-d.get("failed",99))),
        "covers": ("data/cover_designer.json", lambda d: d.get("covers",0)),
        "prices": ("data/storefront_rebuild.json", lambda d: d.get("unique_prices",0)),
        "visual": ("data/world_visual_library.json", lambda d: len(d.get("studies",[]))),
        "scouts": ("data/department_scouts.json", lambda d: d.get("successful",0)),
        "brain": ("data/zy_own_brain.json", lambda d: d.get("rounds",0)),
        "revenue": ("data/revenue_autopilot.json", lambda d: d.get("cycles",0)),
        "quality": ("data/qa_full_audit.json", lambda d: d.get("keep",0)),
    }
    for k, (f, fn) in files.items():
        try:
            v = fn(json.load(open(os.path.join(ROOT, f), encoding="utf-8")))
            if isinstance(v, (int, float)):
                s[k] = int(v)
            elif isinstance(v, (list, dict)):
                s[k] = len(v)
            else:
                s[k] = 0
        except Exception:
            s[k] = 0
    return s


def objective(before):
    """The engine chooses the WORST dimension itself — no human labels it."""
    floor = {"qa": 14, "covers": 46, "prices": 8, "visual": 3, "scouts": 12,
             "brain": 5, "revenue": 5, "quality": 18}
    gaps = [(floor[k]-before.get(k, 0))/max(1, floor[k]) for k in floor]
    worst = sorted(zip(floor.keys(), gaps), key=lambda x: -x[1])[0]
    return worst[0], worst[1]


def load_memory():
    try:
        return json.load(open(DATA, encoding="utf-8"))
    except Exception:
        return {"history": [], "weights": {c: 1.0 for c in CANDIDATES}}


def choose(mem, focus):
    """Exploit actions with proven positive delta on this focus; explore sometimes."""
    weights = mem["weights"]
    scored = []
    for c in CANDIDATES:
        recs = [h for h in mem["history"] if h.get("action") == c and
                h.get("focus") == focus]
        avg = sum(r.get("delta", 0) for r in recs)/len(recs) if len(recs) >= 2 else 0
        conf = min(1.0, len(recs)/4)
        explore = random.random()*0.6*(1-conf)
        scored.append((avg*weights.get(c,1) + explore, c))
    scored.sort(reverse=True)
    return scored[0][1], {"ranked": [(c, round(v,3)) for v, c in scored[:5]]}


def execute(action):
    try:
        m = __import__(action)
        r = m.run(apply=True)
        return bool(r.get("ok", True)) if isinstance(r, dict) else True
    except Exception as e:
        return False


def run(apply=True):
    mem = load_memory()
    before = state()
    focus, severity = objective(before)
    action, reasoning = choose(mem, focus)
    ok = execute(action)
    after = state()
    delta = after.get(focus, 0) - before.get(focus, 0)
    # self-correction: reinforce what worked, weaken what didn't
    mem["weights"][action] = max(0.2, min(3.0, mem["weights"].get(action,1) * (1.25 if delta>0 else 0.82)))
    hist = mem.setdefault("history", [])
    hist.append({"t": int(time.time()), "focus": focus, "severity": round(severity,3),
                 "action": action, "ok": ok, "delta": delta,
                 "before": before, "after": after})
    mem["history"] = hist[-200:]
    rec = {"t": int(time.time()), "before": before, "focus": focus,
           "chosen": action, "reasoning": reasoning, "ok": ok,
           "after": after, "delta": delta,
           "rule": "เลือกเป้าหมายที่แย่ที่สุดเอง → เลือกเครื่องมือจากผลที่เคยได้จริง → วัดผล → ปรับน้ำหนักความเชื่อ"}
    if apply:
        json.dump(mem, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# เครื่องคิดเหตุผล v2 (ไม่มีตารางสั่งงาน)", "",
              "รอบ: %d" % len(hist), "",
              "## สถานะก่อนคิด", json.dumps(before, ensure_ascii=False), "",
              "## สิ่งที่ระบบเลือกเอง", "- เป้าหมายที่แย่ที่สุด: **%s** (severity %.2f)" % (focus, severity),
              "- เครื่องมือที่เลือก: **%s** (จากคะแนนความเชื่อ + exploration)" % action,
              "- การให้คะแนน: " + json.dumps(reasoning["ranked"], ensure_ascii=False), "",
              "## ผลที่วัดได้", "- delta ของ `%s`: **%+d**" % (focus, delta),
              "- ok: %s" % ok, "- สถานะหลัง: " + json.dumps(after, ensure_ascii=False), "",
              rec["rule"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"focus": r["focus"], "chosen": r["chosen"],
                      "delta": r["delta"], "ok": r["ok"]}, ensure_ascii=False))
