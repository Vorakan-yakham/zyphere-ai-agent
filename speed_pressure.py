"""Speed Pressure — permanent notice to every department.

Owner's directive: the slower the team works, the more tasks are added.
This is written into the governance board that all departments read every pulse.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "SPEED_PRESSURE.md")
DATA = os.path.join(ROOT, "data", "speed_pressure.json")

NEW_QUESTS = [
    {"id": "q3d", "title": "3D realtime walkthrough → วิดีโอ",
     "detail": "จากงานก่อนหน้า ให้ทำ flow เดินได้แบบ realtime แล้วอัดเป็นวิดีโอ",
     "module": "walkthrough_3d", "owner": "วิศวกรสื่อ + วิศวกรภาพ"},
    {"id": "qper", "title": "ลดเวลา visual production ให้ <60s/รอบ",
     "detail": "ปัจจุบัน 33.6s — ต้องรักษาและลดต่อ", "module": "visual_production",
     "owner": "วิศวกรอัตโนมัติ"},
]


def run(apply=True):
    rec = {"t": int(time.time()),
           "message": "ยิ่งทำงานช้า ยิ่งได้โจทย์เพิ่ม — ระบบจะเติมงานให้ทุกแผนกที่เกินเวลา",
           "rule": "ถ้า pulse ใดใช้เวลา >60 วิ หรือมีเป้าไม่ผ่าน → เพิ่มโจทย์ใหม่เข้า board ทันที",
           "quests": NEW_QUESTS}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# ประกาศถึงพนักงานทุกแผนก (จากเจ้าของ)\n\n**" + rec["message"] + "**\n\n" +
            rec["rule"] + "\n\n## โจทย์ที่เพิ่มรอบนี้\n\n" +
            "\n".join("- **%s** — %s · ผู้รับผิดชอบ: %s (โมดูล `%s`)" %
                      (q["title"], q["detail"], q["owner"], q["module"]) for q in NEW_QUESTS) + "\n")
    return {"ok": True, "quests": len(NEW_QUESTS)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
