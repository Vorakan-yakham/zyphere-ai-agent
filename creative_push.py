"""Creative Push — urgent directive to graphics + video teams.

Owner is not satisfied with cover quality vs reference. This writes a hard,
measurable order into the governance board every department reads each pulse.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "CREATIVE_PUSH.md")
DATA = os.path.join(ROOT, "data", "creative_push.json")

TASKS = [
    {"dept": "วิศวกรกราฟิก", "priority": "P0",
     "title": "ปก 46 เล่มให้ได้แบบ international reference",
     "target": "diffusion 46/46 · typography EN+TH · ไม่มี watermark · ตรงชื่อหนังสือ",
     "now": "ทำต่อทุก pulse แบบ incremental (โควต้าฟรีหมด → รอรอบหน้า ไม่หยุด)",
     "evidence": "data/diffusion_covers.json + public_covers/cover_NN.jpg"},
    {"dept": "วิศวกรสื่อ", "priority": "P0",
     "title": "วิดีโอ 4K ให้ดูโปรระดับ reference",
     "target": "4K H.264+AAC · xfade จริง · 3D parallax walk · caption · <60s/รอบ",
     "now": "ใช้ภาพจาก diffusion ที่สร้างได้เป็น material ใหม่แทนภาพเก่า",
     "evidence": "data/cinema_studio.json + data/walkthrough_3d.json"},
    {"dept": "วิศวกรภาพ", "priority": "P1",
     "title": "ศึกษา reference แล้วปรับ art direction",
     "target": "แสง/สี/organization ใกล้ภาพตัวอย่าง · วัด contrast >=3.0",
     "now": "อ่านGovernance/TECH_RADAR.md + ปรับ prompt ให้ตรงเนื้อหาหนังสือ",
     "evidence": "governance/TECH_RADAR.md + qa_supreme.json"},
]


def run(apply=True):
    rec = {"t": int(time.time()),
           "message": "เจ้าของยังไม่พอใจงานกราฟฟิก/วิดีโอ — ต้อง发展ต่อจนใกล้ reference",
           "rule": "ห้ามรายงานว่าเสร็จถ้าหลักฐานไม่ครบ — ทุก pulse ต้องมีของใหม่หรือบันทึกว่าติดโควต้า",
           "tasks": TASKS}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# กระตุ้นทีมงาน — กราฟฟิก / วิดีโอ (P0)\n\n**" + rec["message"] + "**\n\n" +
            rec["rule"] + "\n\n" +
            "\n".join("## [%s] %s — %s\n- เป้า: %s\n- ตอนนี้: %s\n- หลักฐาน: %s\n" %
                      (t["priority"], t["dept"], t["title"], t["target"],
                       t["now"], t["evidence"]) for t in TASKS))
    return {"ok": True, "tasks": len(TASKS)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
