"""Next Development — reads the roadmap the system wrote ITSELF, picks the
top goal, executes the correct engine, measures, then asks all departments and
writes the next plan. No owner instruction in the loop.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "next_development.json")
OUT = os.path.join(ROOT, "governance", "NEXT_DEVELOPMENT.md")

# The engine already published its own top goals: compete / sales / book / design / film.
# We map a goal to an EXECUTABLE engine (this is execution, not being told what to want).
EXEC = {
    "compete": "improvement_league",
    "sales": "outreach_engine",
    "book": "ebook_design_team",
    "design": "own_image_lab",
    "film": "film_editor",
    "qa": "qa_supreme",
    "growth": "autonomous_mind",
    "offline": "own_brain",
}


def current_goal():
    try:
        md = open(os.path.join(ROOT, "governance", "FUTURE_ROADMAP.md"),
                  encoding="utf-8").read()
        m = re.search(r"### 1\. (\w+)", md)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "compete"


def measure():
    out = {}
    for f, k in [("data/qa_supreme.json", "failed"),
                 ("data/revenue_autopilot.json", "cycles"),
                 ("data/improvement_league.json", "rounds"),
                 ("data/outreach.json", "published"),
                 ("data/cover_designer.json", "covers")]:
        try:
            d = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
            v = d.get(k)
            out[k] = len(v) if isinstance(v, list) else (str(v)[:60] if isinstance(v, dict) else v)
        except Exception:
            out[k] = 0
    return out


def run(apply=True):
    before = measure()
    goal = current_goal()
    engine = EXEC.get(goal, "own_brain")
    result = {"ok": False, "error": "not run"}
    try:
        m = __import__(engine)
        r = m.run(apply=apply)
        result = {"ok": bool(r.get("ok", True)) if isinstance(r, dict) else True,
                  "summary": {k: r.get(k) for k in
                              ("published", "covers", "cycle", "round", "failed", "passed")
                              if isinstance(r, dict) and k in r}}
    except Exception as e:
        result = {"ok": False, "error": str(e)[:140]}
    # ask every department after the work, then write the next plan
    try:
        import wish_cycle, future_roadmap
        w = wish_cycle.run(apply=apply)
        p = future_roadmap.run(apply=apply)
        after_questions = len(w.get("next_wishes", []))
        next_plan = [t["id"] for t in p.get("next_five", [])]
    except Exception:
        after_questions, next_plan = 0, []
    after = measure()
    rec = {"t": int(time.time()), "goal_from_own_roadmap": goal,
           "engine_chosen": engine, "result": result,
           "before": before, "after": after,
           "asked_departments": after_questions, "next_plan": next_plan,
           "rule": "ระบบอ่านแผนที่ตัวเองเขียน → ลงมือ → ถามทุกฝ่าย → เขียนแผนใหม่ วนไม่หยุด"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# การพัฒนาต่อโดยไม่ต้องมีคำสั่ง\n\n" +
            "- เป้าหมายจากแผนที่ระบบเขียนเอง: **%s**\n" % goal +
            "- เครื่องมือที่เลือก: `%s`\n" % engine +
            "- ผล: " + json.dumps(result, ensure_ascii=False) + "\n" +
            "- ถามทุกฝ่ายแล้ว: %d คำถาม\n" % after_questions +
            "- แผนรอบหน้า: " + ", ".join(next_plan) + "\n\n" +
            "- " + rec["rule"] + "\n")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"goal": r["goal_from_own_roadmap"],
                      "engine": r["engine_chosen"], "result": r["result"],
                      "next": r["next_plan"]}, ensure_ascii=False)[:700])
