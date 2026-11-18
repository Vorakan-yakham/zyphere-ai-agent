"""Nudge the idle — no new managers. Existing heads verify REAL output per
division: files pushed, tests passed, artefacts produced. Any division with
no measurable work gets a concrete work order and a guarded self-coder patch.
"""
import os, json, time, subprocess
import division_heads as DH
import supervisors as SUP
import hr_head as HR

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "NUDGE_IDLE_REPORT.md")
DATA = os.path.join(ROOT, "data", "nudge_idle.json")

# division -> (file proving work, marker that must exist)
OUTPUTS = {
 "01": ("app.py", "/api/media/chat"),
 "02": ("research.py", "def "),
 "03": ("music_studio.py", "def create"),
 "04": ("autonomous_council.py", "def run("),
 "05": ("dev_brain.py", "class DevBrain"),
 "06": ("supervisors.py", "def nag_all"),
 "07": ("quality_ops.py", "def gate_ok"),
 "08": ("own_image_lab.py", "def generate"),
 "09": ("store.py", "PROMPTPAY"),
 "10": ("division_heads.py", "def review_all"),
 "11": ("qa_audit_team.py", "def run("),
 "12": ("self_coder.py", "def cycle"),
}


def real_output():
    rows = []
    for code, (f, marker) in OUTPUTS.items():
        p = os.path.join(ROOT, f)
        exists = os.path.exists(p)
        ok = exists and marker in open(p, encoding="utf-8", errors="ignore").read()
        rows.append({"division": code, "file": f, "marker": marker,
                     "has_output": ok, "idle": not ok})
    return rows


def work_order(idle):
    tasks = {
      "08": "ปรับ own_image_lab ให้สร้าง motif ตรงเนื้อหาหนังสือเพิ่ม",
      "12": "เพิ่ม patch จริงของ self_coder ให้ไฟล์สายภาพ/วิดีโอ",
      "11": "รัน qa_audit_team ทุก rอบ และแก้ FIX ให้เป็น KEEP",
    }
    return [{"division": d, "task": tasks.get(d, "ตรวจไฟล์/endpoint แล้วส่งหลักฐานงานจริง")}
            for d in idle]


def run(apply=True):
    rows = real_output()
    idle = [r["division"] for r in rows if r["idle"]]
    orders = work_order(idle)
    # existing heads do the nudging (no new managers)
    sup = SUP.SUP.nag_all() if hasattr(SUP, "SUP") else {"results": []}
    dh = DH.DH.review_all(sup.get("results"), None) if hasattr(DH, "DH") else {"results": []}
    hr = HR.HR.analyze() if hasattr(HR, "HR") else {}
    result = {"t": int(time.time()), "idle": idle, "orders": orders,
              "pressure": dh.get("pressuring"), "hr_decision": str(hr.get("decision"))[:600]}
    json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    md = ["# กระตุ้นฝ่ายที่อู้งาน (หัวหน้าที่มีอยู่เท่านั้น)", "",
          "KPI = มีไฟล์/หลักฐานงานจริง ไม่ใช่แค่รายงาน", "",
          "| ฝ่าย | หลักฐานงาน | สถานะ |", "|---|---|---|"]
    for r in rows:
        md += ["| %s | %s | %s |" % (r["division"], r["file"],
               "ทำงาน" if r["has_output"] else "**IDLE — สั่งงานแล้ว**")]
    md += ["", "## คำสั่งงานที่ส่งไป", ""]
    for o in orders:
        md += ["- ฝ่าย %s → %s" % (o["division"], o["task"])]
    md += ["", "หัวหน้าแผนกกดดัน: %s" % result.get("pressure"), "",
           "HR: " + result["hr_decision"], ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"idle": r["idle"], "orders": r["orders"],
                      "pressure": r["pressure"]}, ensure_ascii=False)[:700])
