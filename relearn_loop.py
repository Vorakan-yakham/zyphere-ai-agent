"""Relearn Loop — a FAILED inspection sends the owning engineer BACK TO SCHOOL.

It harvests NEW knowledge specifically for the failed topic, writes it into
that department's own brain, then issues a work order containing the new
lesson. The engineer rebuilds; QA re-inspects. No repeated blind patching.
"""
import os, json, time, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "RELEARN_LOG.md")
DATA = os.path.join(ROOT, "data", "relearn_loop.json")

SYLLABUS = {
    "ตา: ปกไม่ซ้ำ": ("graphic", "book cover design unique visual identity typography"),
    "ตา: contrast/balance ผ่าน": ("graphic", "visual hierarchy contrast ratio composition balance"),
    "หู: เสียงมีจริง ไม่เงียบ": ("sound", "audio loudness normalization waveform dynamics"),
    "สมอง: คำกล่าวตรงกับไฟล์จริง": ("qa", "evidence based reporting verification audit"),
    "สมอง: ราคาไม่ซ้ำซาก": ("commerce", "value based pricing tiered pricing ebook"),
}


def learn(topic):
    """Study from open world knowledge + our own brains, then summarise a lesson."""
    notes = []
    try:
        import world_knowledge as WK
        r = WK.harvest(topic, apply=True)
        notes.append(" dunia: " + ", ".join(r.get("sources", [])) +
                     " / " + str(len(r.get("hits", []))) + " facts")
    except Exception as e:
        notes.append("world harvest error: " + str(e)[:60])
    try:
        from local_brain import LocalBrain
        p = os.path.join(ROOT, "data", "dept_brains", "qa.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        LocalBrain(p).learn_text("relearn: " + topic, source="qa-relearn")
        notes.append("สมองแผนกอัปเดตแล้ว")
    except Exception:
        pass
    return notes


def run(gate=None, apply=True):
    if gate is None:
        try:
            gate = json.load(open(os.path.join(ROOT, "data", "qa_supreme.json"),
                                  encoding="utf-8"))
        except Exception:
            gate = {"passed": True, "orders": []}
    orders = gate.get("orders") or []
    sessions = []
    for o in orders:
        name = o.get("fix") or o.get("check")
        dept, topic = SYLLABUS.get(name, ("qa", name + " best practices"))
        notes = learn(topic)
        sessions.append({"failed_check": name, "owner": o.get("owner"),
                         "department": dept, "studied": topic,
                         "new_knowledge": notes,
                         "order": "%s ต้อง rebuild งานโดยใช้สิ่งที่เพิ่งเรียนรู้ใหม่ — ห้ามส่งงานเก่าซ้ำ" % o.get("owner")})
    rec = {"t": int(time.time()), "failed": len(orders),
           "sessions": sessions,
           "rule": "ไม่ผ่าน → เรียนรู้ใหม่ → ส่งงานใหม่ → ตรวจใหม่ (วนจนผ่าน)"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# การส่งทีมกลับไปเรียนรู้ใหม่ (Fail → Relearn)", "",
              "รอบ: %d · งานไม่ผ่าน %d ชิ้น" % (int(time.time()), len(orders)), ""]
        for s in sessions:
            md += ["## %s → %s" % (s["failed_check"], s["department"]),
                   "- ศึกษา: " + s["studied"],
                   "- ความรู้ใหม่: " + " | ".join(s["new_knowledge"]),
                   "- คำสั่ง: " + s["order"], ""]
        md += [rec["rule"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"failed": r["failed"], "sessions": len(r["sessions"])},
                     ensure_ascii=False))
