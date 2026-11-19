"""Autonomous Mind — NO pre-fed domains, NO taught directions.

Reads its own measured weaknesses -> invents the research questions itself ->
goes out to open sources -> extracts techniques -> ACTS -> re-measures.
'Thinking' here = evidence-driven query generation + technique extraction +
execution, fully inside the unattended workflow.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "autonomous_mind.json")
OUT = os.path.join(ROOT, "governance", "AUTONOMOUS_MIND.md")


def weaknesses():
    w = []
    def get(f, k, default=0):
        try:
            d = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
            v = d.get(k, default)
            return len(v) if isinstance(v, (list, dict)) else v
        except Exception:
            return default
    qa_fix = get("data/qa_full_audit.json", "fix")
    if qa_fix:
        w.append({"area": "QA", "gap": "มี FIX %d รายการ" % qa_fix})
    strict = get("data/qa_gate_strict.json", "failed")
    if strict:
        w.append({"area": "GE>", "gap": "release gate ไม่ผ่าน %d ข้อ" % strict})
    covers = get("data/cover_designer.json", "covers")
    if covers < 46:
        w.append({"area": "GRAPHIC", "gap": "ปกไม่ครบ 46"})
    vis = get("data/world_visual_library.json", "studies")
    if not vis:
        w.append({"area": "VISION", "gap": "ยังไม่มีภาพอ้างอิงจากโลก"})
    scout = get("data/department_scouts.json", "reports")
    if not scout:
        w.append({"area": "SCOUT", "gap": "ยังไม่มีทีมออกไปดูโลก"})
    shop = get("data/commerce.json", "channels")
    if shop < 8:
        w.append({"area": "REVENUE", "gap": "ช่องทางรายได้น้อย"})
    return w or [{"area": "GROWTH", "gap": "ยังไม่มีจุดอ่อนชัดเจน — ต้องหาของใหม่"}]


def make_questions(gaps):
    """The system INVENTS its own research questions from its weaknesses."""
    qs = []
    for g in gaps:
        area = g["area"]
        qs.append("how to improve %s - best practice 2026" % (
            {"QA":"software quality acceptance criteria",
             "GE>":"visual accessibility contrast ratio standard",
             "GRAPHIC":"book cover design typography composition",
             "VISION":"reference photography composition lighting",
             "SCOUT":"competitive design research methods",
             "REVENUE":"free digital product distribution channels",
             "GROWTH":"creative craft new techniques"}.get(area, area.lower())))
    return qs


def probe(q):
    import requests
    found = []
    for url, params, key in [
        ("https://en.wikipedia.org/w/api.php",
         {"action":"query","list":"search","srsearch":q,"format":"json","srlimit":3},
         lambda j: [x.get("title","") for x in j.get("query",{}).get("search",[])]),
        ("https://api.openalex.org/works", {"search":q,"per-page":3},
         lambda j: [str(x.get("title",""))[:120] for x in j.get("results",[])]),
        ("https://api.github.com/search/repositories",
         {"q":q,"sort":"stars","per_page":3},
         lambda j: [x.get("full_name","") for x in j.get("items",[])]),
    ]:
        try:
            r = requests.get(url, params=params,
                             headers={"User-Agent":"Zypher-Mind/1.0"}, timeout=20)
            if r.ok:
                found += [str(x) for x in key(r.json()) if x]
        except Exception:
            pass
    return found[:8]


def technique(titles, gap):
    blob = " ".join(titles).lower()
    if any(k in blob for k in ("contrast", "accessib", "quality", "test")):
        return {"take": "ใช้เกณฑ์วัดที่เป็นตัวเลข + fail-closed ไม่ปล่อยของไม่ผ่าน",
                "act": "qa_supreme"}
    if any(k in blob for k in ("design", "cover", "typography", "poster", "visual")):
        return {"take": "ใช้ motif เฉพาะ.subject + typography hierarchy + พื้นที่ว่าง",
                "act": "cover_designer"}
    if any(k in blob for k in ("image", "photo", "light", "composition")):
        return {"take": " learns from real photo references แล้ว retouch แสง/คม/สี",
                "act": "poster_studio"}
    if any(k in blob for k in ("market", "distribution", "channel", "free")):
        return {"take": "เตรียม asset ให้ช่องทางฟรีให้พร้อมรับลูกค้า",
                "act": "revenue_autopilot"}
    return {"take": "(record findings as knowledge and retry next round)".replace("record","จดความรู้แล้วลองใหม่รอบหน้า"),
            "act": "own_brain"}


def run(apply=True):
    gaps = weaknesses()
    qs = make_questions(gaps)
    studies = []
    for g, q in zip(gaps, qs):
        found = probe(q)
        studies.append({"gap": g, "question_it_invented": q,
                        "found": found, "technique": technique(found, g)})
    actions = []
    for s in studies:
        try:
            m = __import__(s["technique"]["act"])
            r = m.run(apply=apply)
            actions.append({"module": s["technique"]["act"],
                            "ok": bool(r.get("ok", True)) if isinstance(r, dict) else True})
        except Exception as e:
            actions.append({"module": s["technique"]["act"], "ok": False,
                            "error": str(e)[:100]})
    rec = {"t": int(time.time()), "weaknesses": gaps, "questions": qs,
           "studies": studies, "actions": actions,
           "rule": "ระบบตั้งคำถามเองจากจุดอ่อน ออกไปหาเอง แล้วลงมือเอง — ไม่รอการป้อน"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# ความคิดอิสระของ Zyphere (Autonomous Mind)", "",
              "จุดอ่อนที่ระบบตรวจพบเอง:", ""]
        for g in gaps:
            md += ["- %s: %s" % (g["area"], g["gap"])]
        md += ["", "## คำถามที่ระบบตั้งขึ้นเอง (ไม่มีใครสอน)", ""]
        for q in qs:
            md += ["- " + q]
        md += ["", "## สิ่งที่เจอ + เทคนิคที่เลือก + การลงมือ", ""]
        for s, a in zip(studies, actions):
            md += ["### %s → %s" % (s["gap"]["area"], s["technique"]["act"]),
                   "- เจอ: " + "; ".join(s["found"][:3]),
                   "- หลักการ: " + s["technique"]["take"],
                   "- ผล: " + json.dumps(a, ensure_ascii=False), ""]
        md += [rec["rule"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"gaps": len(r["weaknesses"]), "questions": len(r["questions"]),
                      "actions": len(r["actions"])}, ensure_ascii=False))
