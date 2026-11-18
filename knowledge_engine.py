"""Knowledge Engine — continuously learn MANY topics from open world sources,
then push the new evidence into our own brain. Measures real coverage growth.
"""
import os, json, time, re, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "knowledge_engine.json")
OUT = os.path.join(ROOT, "governance", "KNOWLEDGE_ENGINE.md")

SEED_TOPICS = [
    "quantum computing", "renewable energy", "machine learning",
    "Thai history", "climate science", "human anatomy",
    "software engineering", "space exploration", "economics",
    "music theory", "graphic design", "video production",
    "prompt engineering", "data compression", "robotics",
]


def coverage():
    try:
        db = json.load(open(os.path.join(ROOT, "data", "world_knowledge.json"), encoding="utf-8"))
    except Exception:
        return {"topics": 0, "facts": 0, "sources": []}
    src = set()
    for t in db.get("topics", []):
        src.update(t.get("sources", []))
    return {"topics": len(db.get("topics", [])),
            "facts": sum(len(t.get("hits", [])) for t in db.get("topics", [])),
            "sources": sorted(src)}


def all_disciplines():
    """Every field: 46 faculties / 184 sub-branches / 4225 world disciplines."""
    out = []
    try:
        from faculty_expansion import TREE
        for faculty, subs in TREE.items():
            for sub, topics in subs.items():
                out.extend([str(t) for t in topics][:3])
    except Exception:
        pass
    if not out:
        p = os.path.join(ROOT, "world_taxonomy.json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            def walk(x):
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    for v in x.values(): walk(v)
                elif isinstance(x, list):
                    for v in x[:20]: walk(v)
            walk(d)
    return list(dict.fromkeys(out))


def run(topics=None, apply=True, batch=25):
    import world_knowledge as WK
    import own_brain
    before = coverage()
    allf = all_disciplines()
    known = set()
    try:
        db = json.load(open(os.path.join(ROOT, "data", "world_knowledge.json"), encoding="utf-8"))
        known = {t.get("q", "").lower() for t in db.get("topics", [])}
    except Exception:
        pass
    pending = [d for d in allf if d.lower() not in known]
    targets = topics or (pending[:batch] if pending else SEED_TOPICS[:batch])
    learned = []
    for q in targets:
        try:
            r = WK.harvest(q, apply=apply)
            learned.append({"topic": q, "sources": r.get("sources", []),
                            "facts": len(r.get("hits", []))})
        except Exception as e:
            learned.append({"topic": q, "error": str(e)[:80]})
    after = coverage()
    # push newly harvested knowledge into the growing self-brain
    brain = own_brain.build(apply=apply)
    growth = own_brain.grow(apply=apply) if apply else {"round": brain.get("rounds", 0)}
    result = {"t": int(time.time()), "before": before, "after": after,
              "learned": learned, "taxonomy_total": len(allf),
              "taxonomy_pending": len(pending),
              "brain_lessons": brain.get("count"),
              "growth_round": growth.get("round"),
              "growth_actions": growth.get("actions", [])}
    if apply:
        json.dump(result, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# เครื่องยนต์ความรู้ — เรียนรู้เพิ่มทุก รอบ", "",
              "ก่อน: %d หัวข้อ / %d ข้อเท็จจริง" % (before["topics"], before["facts"]),
              "หลัง: %d หัวข้อ / %d ข้อเท็จจริง" % (after["topics"], after["facts"]), "",
              "| หัวข้อที่เรียนรู้ใหม่ | แหล่ง | facts |", "|---|---|---|"]
        for x in learned:
            md += ["| %s | %s | %s |" % (x["topic"], ", ".join(x.get("sources", [])),
                   x.get("facts", x.get("error", "-")))]
        md += ["", "ความรู้ในสมอง Zyphere: %d รายการ · รอบเติบโตที่ %s" % (
            result["brain_lessons"], result["growth_round"]), ""]
        for a in result["growth_actions"]:
            md += ["- " + str(a.get("gap")) + " → " + str(a.get("result")), ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"before": r["before"], "after": r["after"],
                      "brain_lessons": r["brain_lessons"],
                      "growth_round": r["growth_round"]}, ensure_ascii=False)[:600])
