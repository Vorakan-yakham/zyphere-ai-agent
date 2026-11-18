"""Discipline Lab — propose NEW academic disciplines by cross-pollinating
real harvested knowledge. Every proposal carries real source URLs, research
questions and a testable method. Nothing is invented as a 'fact'.
"""
import os, json, re, time, itertools

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "new_disciplines.json")
OUT = os.path.join(ROOT, "governance", "NEW_DISCIPLINES.md")


def sources_for(topic):
    p = os.path.join(ROOT, "data", "world_knowledge.json")
    try:
        db = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    out = []
    for t in db.get("topics", []):
        if topic.lower() in t.get("q", "").lower():
            out.extend([{"source": h["source"], "title": h.get("title"),
                         "url": h.get("url")} for h in t.get("hits", [])])
    return out[:4]


def existing_names():
    names = set()
    try:
        from faculty_expansion import TREE
        for f, subs in TREE.items():
            names.add(f.lower())
            for s in subs:
                names.add(s.lower())
                for t in subs[s]:
                    names.add(str(t).lower())
    except Exception:
        pass
    try:
        d = json.load(open(os.path.join(ROOT, "data", "new_disciplines.json"), encoding="utf-8"))
        for x in d.get("proposed", []):
            names.add(x.get("name", "").lower())
    except Exception:
        pass
    return names


def propose(pairs=None, apply=True):
    import knowledge_engine as KE
    fields = KE.all_disciplines()
    known = existing_names()
    if not pairs:
        pairs = list(itertools.islice(
            ((fields[i], fields[(i*7+3) % len(fields)])
             for i in range(len(fields)) if len(fields) > 10), 12))
    proposals = []
    for a, b in pairs:
        name = ("%s + %s" % (a, b)).title()
        if name.lower() in known:
            continue
        ev = sources_for(a) + sources_for(b)
        if not ev:
            continue  # no real evidence -> no proposal
        proposals.append({
            "name": name, "parents": [a, b], "evidence": ev,
            "questions": [
                "ความรู้จาก %s อธิบายปรากฏการณ์ใน %s ได้อย่างไร" % (a, b),
                "สามารถทดสอบสมมติฐานร่วมด้วยข้อมูลจริงได้ไหม",
                "ผลลัพธ์ที่วัดได้คืออะไร และวัดอย่างไร"],
            "method": "studies->compare->experiment->measure->publish",
            "t": int(time.time()),
            "status": "proposed (needs research)",
        })
        if len(proposals) >= 6:
            break
    result = {"t": int(time.time()), "proposed": proposals, "count": len(proposals),
              "note": "สาขาใหม่เกิดจากการเชื่อมแหล่งจริง — ยังไม่ claims ว่าเป็นศาสตร์ที่ยอมรับแล้ว"}
    if apply:
        json.dump(result, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# สาขาวิชาใหม่ที่ระบบเสนอ", "",
              "เกิดจากการเชื่อมความรู้ที่มีแหล่งอ้างอิงจริง — ต้องวิจัยและทดสอบต่อ", ""]
        for p in proposals:
            md += ["## " + p["name"], "- แม่สาขา: " + ", ".join(p["parents"]),
                   "- แหล่งจริง: " + ", ".join(str(e.get("url"))[:100] for e in p["evidence"]),
                   "- คำถามวิจัย: " + " | ".join(p["questions"]),
                   "- วิธี: " + p["method"], "- สถานะ: " + p["status"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = propose()
    print(json.dumps({"count": r["count"],
                      "samples": [p["name"] for p in r["proposed"][:3]]},
                     ensure_ascii=False))
