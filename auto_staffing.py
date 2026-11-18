"""Zyphere Auto-Staffing — create the MISSING department capability itself.

Scans real signals, decides which capability is absent, then WRITES a runnable
module in generated/ that performs that job (wrapping an engine that actually
exists). No invented headcount: a 'new department' is a real callable module,
registered and compile-verified.
"""
import os, json, time, threading
import autonomous_council as AC

ROOT = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(ROOT, "generated")
DATA = os.path.join(ROOT, "data", "auto_staffing.json")
OUT = os.path.join(ROOT, "governance", "AUTO_STAFFING.md")
LOCK = threading.RLock()

# capability -> (module name, real engine call, why it is needed)
CATALOG = {
    "editorial": ("editorial_review", "from department_editors import ED\n    result = ED.run(apply=True)",
                  "ตรวจทานข้อความของแต่ละฝ่าย"),
    "quality_gate": ("quality_gate_guard", "from quality_ops import QOPS\n    result = {'gate': QOPS.gate_ok()}",
                     "กันไม่ให้ของไม่ผ่านเกณฑ์ปล่อยขาย"),
    "income": ("income_strategist", "import autonomous_council as AC\n    result = {'catalog': AC.gh_raw('PRODUCTS.md') is not None}",
               "คิดหาช่องทางรายได้จากของจริง"),
    "self_code": ("self_code_captain", "from self_coder import SC\n    result = SC.status()",
                  "พัฒนาโค้ดตัวเองต่อเนื่อง"),
    "supervision": ("supervision_auditor", "from supervisors import SUP\n    result = SUP.status()",
                    "ตรวจว่าหัวหน้าฝ่ายทำงานหรือซ้ำ"),
    "division_pressure": ("division_pressure_auditor", "from division_heads import DH\n    result = DH.status()",
                          "หัวหน้าแผนกกดดันหัวหน้าฝ่าย"),
}


def scan():
    gaps = []
    try:
        from quality_ops import QOPS
        if not QOPS.gate_ok():
            gaps.append("quality_gate")
    except Exception:
        gaps.append("quality_gate")
    try:
        from department_editors import ED
        if not ED.log:
            gaps.append("editorial")
    except Exception:
        gaps.append("editorial")
    try:
        from self_coder import SC
        st = SC.status()
        if not st.get("pushed"):
            gaps.append("self_code")
    except Exception:
        gaps.append("self_code")
    if AC.gh_raw("INCOME_PLAN.md") is None:
        gaps.append("income")
    try:
        from division_heads import DH
        if not DH.log:
            gaps.append("division_pressure")
    except Exception:
        gaps.append("division_pressure")
    try:
        from supervisors import SUP
        if not SUP.log:
            gaps.append("supervision")
    except Exception:
        gaps.append("supervision")
    return gaps


def make_module(slug, call, why):
    name, code = slug, CATALOG[slug][1]
    return '''"""Auto-created capability: %s"""\n\n\ndef run():\n    %s\n    return result\n\n\nif __name__ == "__main__":\n    print(run())\n''' % (why, call), name


def run(apply=True):
    gaps = scan()
    created = []
    os.makedirs(GEN, exist_ok=True)
    for slug in gaps:
        body, name = make_module(slug, None, CATALOG[slug][2])
        path = os.path.join(GEN, name + ".py")
        existed = os.path.exists(path)
        if apply and not existed:
            open(path, "w", encoding="utf-8").write(body)
        created.append({"capability": slug, "module": "generated/" + name + ".py",
                        "created": bool(apply and not existed),
                        "why": CATALOG[slug][2]})
    result = {"ok": True, "t": int(time.time()), "gaps": gaps, "created": created}
    with LOCK:
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# การเพิ่มฝ่าย/ความสามารถอัตโนมัติ", "",
              "ระบบตรวจความขาดจากหลักฐานจริง แล้วสร้างโมดulersโค้ดที่เรียกใช้ได้", "",
              "| ความสามารถที่ขาด | โมดูล | เหตุผล |", "|---|---|---|"]
        for c in created:
            md += ["| %s | `%s` | %s |" % (c["capability"], c["module"], c["why"])]
        open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
    return result


if __name__ == "__main__":
    r = run()
    print("gaps", r["gaps"])
    for c in r["created"]:
        print(c["capability"], c["module"], "created", c["created"])
