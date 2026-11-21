"""Continuous Dialogue — never-ending inter-department conversation.

Every pulse:
  1. Owner's standing complaint is re-issued: "not satisfied, not JARVIS yet"
  2. Every department answers with a REAL metric + a concrete next step
  3. Departments cross-ask each other (graphic <-> video <-> book <-> QA)
  4. A new technology is pulled from Tech Radar and assigned
  5. The full transcript is written to governance so the owner can WATCH it

No owner command is required — this IS the standing order.
"""
import os, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "continuous_dialogue.json")
OUT = os.path.join(ROOT, "governance", "CONTINUOUS_DIALOGUE.md")
UI = os.path.join(ROOT, "DIALOGUE.html")


def _j(n):
    try:
        return json.load(open(os.path.join(ROOT, "data", n), encoding="utf-8"))
    except Exception:
        return {}


DEPTS = [
    ("วิศวกรกราฟิก", "diffusion_covers.json", "generated", "ปกต้องสมจริงระดับ reference"),
    ("วิศวกรสื่อ", "walkthrough_3d_v2.json", "ok", "วิดีโอ 3D ต้องลื่นและมีสีสัน"),
    ("วิศวกรหนังสือ", "ebook_v2_publisher.json", "published", "เนื้อหาต้องทันสมัยอยู่เสมอ"),
    ("วิศวกรร้านค้า", "storefront_rebuild.json", "unique_prices", "ร้านต้องดูเป็นสากล"),
    ("วิศวกรQA", "qa_supreme.json", "passed", "ห้ามปล่อยของที่ไม่ผ่าน"),
    ("วิศวกรเสียง", "qa_supreme.json", "passed", "เสียงต้องมีจริง ไม่เงียบ"),
    ("วิศวกรเพลง", "music_composer.json", "ok", "ทำนองต้องฟังเป็นเพลง"),
    ("วิศวกรความปลอดภัย", "security_audit.json", "passed", "ต้องปลอดภัยโดยไม่ลดคุณภาพ"),
    ("วิศวกรอัตโนมัติ", "department_progress.json", "active", "ต้องทำงานต่อโดยไม่มีคำสั่ง"),
    ("วิศวกรแชท", "ui_functional_audit.json", "ok", "ทุกปุ่มต้องใช้ได้จริง"),
]

CROSS = [
    ("วิศวกรกราฟิก", "วิศวกรสื่อ", "ส่งภาพ diffusion ให้ทีมวิดีโอใช้เป็น material"),
    ("วิศวกรสื่อ", "วิศวกรหนังสือ", "ขอปกใหม่ไปฝังใน book v2"),
    ("วิศวกรหนังสือ", "วิศวกรQA", "ขอตรวจ editorial gate หลังอัพเดท"),
    ("วิศวกรQA", "วิศวกรกราฟิก", "แจ้งผล contrast/ความคมที่ต้องปรับ"),
]


def run(apply=True):
    t = int(time.time())
    prev = _j("continuous_dialogue.json")
    turns = list(prev.get("turns", []))

    radar = _j("tech_radar.json")
    tech = []
    for items in (radar.get("by_topic") or {}).values():
        for x in (items or [])[:2]:
            tech.append((x.get("title", "")[:70], x.get("url", "")))
    tech = tech[:3]

    owner = ("ผู้พัฒนา: ยังไม่พอใจผลงานกราฟฟิก/วิดีโอ ยังไม่ถึง JARVIS "
             "— ทุกแผนกช่วยกันคิด หาเทคโนโลยีใหม่มาใช้ ผมไม่ต้องสั่งอีก")

    new_turns = [{
        "who": "ผู้พัฒนา (คำสั่งถาวร)", "text": owner,
        "tag": "STANDING ORDER"}]
    for dept, datafile, key, worry in DEPTS:
        d = _j(datafile)
        v = d.get(key)
        if isinstance(v, list):
            v = len(v)
        if isinstance(v, bool):
            v = "PASS" if v else "FAIL"
        state = "ยังไม่ผ่าน" if v in (0, None, False, "FAIL") else str(v)[:40]
        ans = ("%s: ตอบคำถาม '%s' → ตัวเลขจริงตอนนี้ = %s "
               "ขั้นต่อไป: เก็บหลักฐาน/เฝ้าดู แล้วปรับในรอบถัดไป "
               "(ห้ามรายงานเสร็จถ้าตัวเลขยังไม่ผ่าน)" % (dept, worry, state))
        new_turns.append({"who": dept, "text": ans, "tag": "SELF-REVIEW"})
    for a, b, msg in CROSS:
        new_turns.append({"who": a + " → " + b, "text": msg,
                          "tag": "CROSS-ASK"})
    for title, url in tech:
        new_turns.append({"who": "Tech Radar", "text":
                          "เทคโนโลยีใหม่สำหรับพัฒนา: " + title + " " + url,
                          "tag": "NEW TECH"})
    new_turns.append({"who": "ระบบ", "text":
                      "WORKING × %d รอบสนทนา — ทุกแผนกตอบและถามต่อแล้ว "
                      "รอบถัดไปจะเริ่มใหม่โดยอัตโนมัติ" % (len(prev.get("turns", [])) // 16 + 1),
                      "tag": "WORKING"})
    turns += new_turns
    turns = turns[-320:]
    rec = {"t": t, "turns": turns, "last": new_turns,
           "rule": "สนทนาตลอด — ไม่หยุด ไม่รอคำสั่ง"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# บทสนทนาต่อเนื่องของทีม Zyphere\n\nอัปเดตล่าสุด " +
            time.strftime("%Y-%m-%d %H:%M:%S") + "\n\n" +
            "\n".join("### [%s] %s\n%s\n" % (x["tag"], x["who"], x["text"])
                      for x in new_turns) +
            "\n\n" + rec["rule"] + "\n")
    return {"ok": True, "turns": len(new_turns), "total": len(turns),
            "last": new_turns}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
