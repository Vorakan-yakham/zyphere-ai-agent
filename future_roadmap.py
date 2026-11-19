"""Future Roadmap — written into code so planning NEVER stops.

After every completed round: read measured evidence, name the weak points,
set the next FIVE development targets with concrete work orders, then hand
them to the next pulse. The plan rewrites itself every round; nothing is
'finished' while any target is still weak.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "future_roadmap.json")
OUT = os.path.join(ROOT, "governance", "FUTURE_ROADMAP.md")

TARGETS = [
    {"id": "sales", "weak": "ยังไม่มีออเดอร์จริง", "plan": "เตรียม 6 ช่องทาง + landing + CTA ให้พร้อมรับลูกค้า", "module": "revenue_autopilot"},
    {"id": "book", "weak": "ปก/ข้อความเก่ายังไม่ถูกปรับปรุงหมด", "plan": " rebuild งานเก่าที่เกิน 6 ชม. ทุกเล่ม", "module": "ebook_design_team"},
    {"id": "design", "weak": "ภาพยังไม่มีรายละเอียดระดับสูง", "plan": "เพิ่ม advanced_filters + motif ตามเนื้อหาทุกรอบ", "module": "own_image_lab"},
    {"id": "film", "weak": "วิดีโอยังเป็นภาพนิ่งเคลื่อนไหว", "plan": "เพิ่มฉาก/ตัวละครที่มีความต่อเนื่อง", "module": "film_editor"},
    {"id": "sound", "weak": "เสียงร้องยังเป็น synthetic", "plan": "พัฒนา formant/note ให้ฟังเป็นทำนองมากขึ้น", "module": "music_composer"},
    {"id": "qa", "weak": "QA อาจมี FIX ได้ทุกคืน", "plan": "แก้ FIX เป็น KEEP ด้วยหลักฐานก่อนปล่อยของ", "module": "qa_audit_team"},
    {"id": "offline", "weak": "พึ่ง API ภายนอกได้น้อยลง", "plan": "เพิ่มความรู้ในสมองในเครื่องทุก.rอบ", "module": "own_brain"},
    {"id": "compete", "weak": "คู่แข่งใหญ่กว่า", "plan": "ลีกวิศวกรแข่งกันทุก pulse วัดคะแนนจริง", "module": "improvement_league"},
]


def evidence():
    out = {}
    for f, k in [("data/qa_full_audit.json", "fix"),
                 ("data/commerce.json", "channels"),
                 ("data/revenue_autopilot.json", "cycles"),
                 ("data/improvement_league.json", "rounds"),
                 ("data/zy_own_brain.json", "lessons")]:
        try:
            d = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
            v = d.get(k)
            out[k] = len(v) if isinstance(v, list) else v
        except Exception:
            pass
    return out


def run(apply=True):
    ev = evidence()
    hist = []
    if os.path.exists(DATA):
        try:
            hist = json.load(open(DATA, encoding="utf-8")).get("plans", [])
        except Exception:
            pass
    # Five targets for the NEXT five rounds, rotating by cycle so all improve.
    start = len(hist) % len(TARGETS)
    next5 = [TARGETS[(start+i) % len(TARGETS)] for i in range(5)]
    rec = {"t": int(time.time()), "cycle": len(hist)+1,
           "evidence": ev, "next_five": next5,
           "rule": "หลังทุกงานเสร็จ ต้องตั้งคำถามแล้ววางแผน 5 รอบข้างหน้าใหม่ — ห้ามหยุด",
           "note": "แผนปรับตัวเองทุกคืนตามหลักฐาน ไม่ใช่แผนตายตัว"}
    hist.append(rec); hist = hist[-100:]
    if apply:
        json.dump({"plans": hist}, open(DATA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        md = ["# แผนพัฒนาต่อ (เขียนใหม่ทุกครั้งที่งานเสร็จ — ห้ามหยุด)", "",
              "รอบที่ %d · %s" % (rec["cycle"], time.strftime("%Y-%m-%d %H:%M")), "",
              "หลักฐานล่าสุด: " + json.dumps(ev, ensure_ascii=False), "",
              "## 5 เป้าหมายถัดไป (ตามลำดับปฏิบัติ)", ""]
        for i, t in enumerate(next5, 1):
            md += ["### %d. %s — %s" % (i, t["id"], t["weak"]),
                   "- ทำ: " + t["plan"], "- โมดูล: " + t["module"], ""]
        md += [rec["rule"], "", "รอบหน้าจะอ่านผลแล้วเขียนแผนใหม่อีกครั้ง — วนไม่หยุด", ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"cycle": r["cycle"],
                      "next": [t["id"] for t in r["next_five"]]}, ensure_ascii=False))
