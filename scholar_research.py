"""Zyphere Scholar Research — every faculty STUDIES before producing.

For each of the 46 faculties, the assigned scholar:
  1. reads the real Wikipedia summary (source + citation)
  2. collects its real worldwide sub-disciplines from world_taxonomy.json
  3. records the core concepts from the faculty tree
  4. writes an auditable research note (SCHOLAR_RESEARCH.md + research/*.json)

Book production must consume these notes; chapters without a studied source
are blocked by QA. This is why the scholars exist.
"""
import os, json, time, requests, subprocess, base64
from faculty_expansion import TREE
from book_design_system import EN_TITLE
from book_team_v2 import fetch_json, put

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"


def research_one(faculty):
    title = EN_TITLE.get(faculty)
    src, summary = "", ""
    if title:
        try:
            r = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/" +
                             requests.utils.quote(title), timeout=15,
                             headers={"User-Agent": "ZyphereScholar/1.0 (educational)"})
            if r.ok:
                j = r.json()
                summary = str(j.get("extract", ""))[:700]
                src = j.get("content_urls", {}).get("desktop", {}).get("page", "")
        except Exception:
            pass
    world = fetch_json("world_taxonomy.json")
    info = next((r for r in world.get("rows", []) if r.get("faculty") == faculty), {})
    topics = [x for x in info.get("world_sub_disciplines", [])
              if x and "also regarded" not in x.lower() and "(outline)" not in x.lower()
              and not x.startswith("Main ")][:60]
    concepts = [c for subs in TREE[faculty].values() for c in subs]
    return {"faculty": faculty, "source_title": title or "", "source_url": src,
            "summary": summary, "world_topics": topics,
            "core_concepts": concepts, "studied_at": int(time.time()),
            "method": "Wikipedia summary + world taxonomy + faculty tree (auditable)"}


def main():
    notes = []
    for i, faculty in enumerate(TREE, 1):
        note = research_one(faculty)
        notes.append(note)
        put("research/%02d_%s.json" % (i, faculty.replace("/", "_")),
            json.dumps(note, ensure_ascii=False, indent=2).encode("utf-8"))
        if i % 10 == 0:
            print("studied", i, flush=True)
    md = ["# บันทึกการศึกษาของนักวิชาการ Zyphere", "",
          "นักวิชาการทุกคณะศึกษาก่อนผลิตหนังสือเสมอ", "",
          "คณะที่ศึกษา: %d · แหล่งที่มีการอ้างอิง: %d" %
          (len(notes), sum(1 for n in notes if n["source_url"])), "",
          "วิธีศึกษา: อ่านบทสรุปจาก Wikipedia (ระบุ URL) + รวบรวมสาขาวิชาจริงจากฐานข้อมูลโลก "
          "+ แนวคิดหลักจากต้นไม้คณะวิชา", ""]
    for n in notes:
        md += ["## " + n["faculty"], ""]
        if n["summary"]:
            md.append("**บทสรุปที่ศึกษา:** " + n["summary"])
            md.append("")
        md.append("**แหล่งที่มา:** " + (n["source_url"] or "ไม่มีบทสรุป — ใช้ฐานข้อมูลสาขาวิชา"))
        md.append("")
        md.append("**แนวคิดหลัก (%d):** %s" % (len(n["core_concepts"]),
                                             ", ".join(n["core_concepts"][:8])))
        md.append("")
        md.append("**สาขาวิชาที่รวบรวม (%d):** %s" %
                  (len(n["world_topics"]), ", ".join(n["world_topics"][:8])))
        md.append("")
    put("SCHOLAR_RESEARCH.md", "\n".join(md))
    put("scholar_research.json", json.dumps({"notes": notes, "t": int(time.time())},
                                            ensure_ascii=False, indent=2).encode("utf-8"))
    print("DONE studied", len(notes), "with source", sum(1 for n in notes if n["source_url"]))


if __name__ == "__main__":
    main()
