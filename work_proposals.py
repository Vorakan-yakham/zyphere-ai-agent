"""Work Proposals — each division discovers and PROPOSES what it could do.

No execution, no auto-publishing. The system inspects the real modules/functions
each division owns and proposes concrete work backed by that evidence, so the
owner can see capability without being asked to order it first.
"""
import os, json, importlib, inspect, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "work_proposals.json")
OUT = os.path.join(ROOT, "governance", "WORK_PROPOSALS.md")
LOCK = threading.RLock()

# division -> (owner file, module to inspect, what to look for)
LINES = [
    ("01 Global Intelligence", "app.py", None, "route/status, health, วัดผล live"),
    ("02 Scientific Discovery", "research.py", "research", "ค้นคว้า/สมมติฐาน/แหล่งอ้างอิง"),
    ("03 Simulation", "music_studio.py", "music_studio", "สร้างไฟล์สื่อจริง"),
    ("04 Knowledge Systems", "autonomous_council.py", "autonomous_council", "สภาฯ แข่งขัน ความจำ"),
    ("05 Learning", "dev_brain.py", "dev_brain", "เรียนรู้/ดึงบทเรียนเก่า"),
    ("06 Engineering", "supervisors.py", "supervisors", "กระตุ้นหัวหน้าฝ่าย"),
    ("07 Quality", "quality_ops.py", "quality_ops", "PDCA/gate คุณภาพ"),
    ("08 Product Design", "image_studio.py", "image_studio", "ภาพ/ปก/หน้าร้าน"),
    ("09 Market & Revenue", "store.py", "store", "ร้านค้า/ราคา/ชำระ"),
    ("10 Operations", "division_heads.py", "division_heads", "หัวหน้าแผนกกดดันหัวหน้าฝ่าย"),
    ("11 Governance", "systems_analyst.py", "systems_analyst", "ตรวจระบบ/จุดอ่อน"),
    ("12 Autonomy", "self_coder.py", "self_coder", "เขียนและปรับโค้ดตัวเอง"),
]


def inspect_module(name):
    try:
        m = importlib.import_module(name)
        funcs = [n for n, o in vars(m).items() if (inspect.isfunction(o) or inspect.isclass(o))
                 and not n.startswith("_") and getattr(o, "__module__", None) == name]
        return funcs[:8]
    except Exception as e:
        return ["import failed: " + str(e)[:60]]


def _engineer_map():
    """IT engineers were already stationed — reuse them, never propose duplicates."""
    try:
        from it_engineers import ENGINEERS
        return {e[0].split()[0]: {"engineer": e[1], "file": e[2], "goal": e[3]}
                for e in ENGINEERS}
    except Exception:
        return {}


def run(apply=True):
    proposals = []
    staffed = _engineer_map()
    for div, src, mod, focus in LINES:
        exists = os.path.exists(os.path.join(ROOT, src))
        funcs = inspect_module(mod) if mod else []
        man = staffed.get(div.split()[0], {})
        proposals.append({
            "division": div, "owner_file": src, "file_exists": exists,
            "engineer": man.get("engineer", "ยังไม่มีวิศวกรประจำ"),
            "assigned_file": man.get("file", src),
            "available": funcs,
            "can_do": focus,
            "proposal": ("วิศวกร%s ประจำ%s อยู่แล้ว (%s) — งานที่เสนอต่อ: %s" % (
                man.get("engineer", "—"), div, man.get("file", src), focus)),
            "status": "เสนอเพื่อพิจารณา — ยังไม่ได้ดำเนินการ",
        })
    result = {"ok": True, "t": int(time.time()), "proposals": proposals}
    with LOCK:
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if apply:
            md = ["# งานที่แต่ละสายงานเสนอว่าทำได้", "",
                  "ระบบตรวจโมดulersจริงแล้วเสนอ — **ยังไม่ได้สั่งให้ทำ**", ""]
            for p in proposals:
                md += ["## " + p["division"], "",
                       "- ไฟล์ที่ครอบครอง: `%s` (%s)" % (
                           p["owner_file"], "มีจริง" if p["file_exists"] else "ไม่มี"),
                       "- ความสามารถที่มี: " + (", ".join(p["available"]) or "—"),
                       "- งานที่เสนอ: " + p["can_do"], "",
                       "- สถานะ: " + p["status"], ""]
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = run()
    for p in r["proposals"]:
        print(p["division"], "->", p["can_do"], "|", p["status"])
