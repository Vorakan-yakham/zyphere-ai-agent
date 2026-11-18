"""Zyphere IT Organization — large-scale software project roles.

Maps the owner's required IT roles into the EXISTING 12 divisions as teams,
not new divisions. Each role has: mission, parent division, existing modules
that already do the work, and honest gaps. Nothing is deleted or duplicated.
"""
import os, json, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "it_org.json")

# group -> [(role, mission, division, current_modules, gap)]
GROUPS = {
    "1. Management & Governance": [
        ("Project Manager / Scrum Master", "ควบคุมภาพรวม งบ เวลา ติดตามและแก้อุปสรรค",
         "11", ["chief.py", "app.py /api/chief/run"], "ยังไม่มี timeline จริง/งบประมาณ"),
        ("Product Owner", "กำหนดวิสัยทัศน์ผลิตภัณฑ์ จัดลำดับ Backlog",
         "12/07", ["demand.py", "market.py", "master_registry.py"], "ยังไม่มี backlog ที่ผู้ใช้จัดลำดับได้"),
    ],
    "2. Business & Analysis": [
        ("Business Analyst", "ถอดความต้องการผู้ใช้เป็นข้อกำหนดทางเทคนิค",
         "07/01", ["help.py", "intent.py", "concept.py"], "ยังไม่มี workshop กับผู้ใช้จริง"),
        ("System Analyst", "ออกแบบสถาปัตยกรรม Data Flow โครงสร้างฐานข้อมูล",
         "02/10", ["systems_analyst.py", "governance/registry.json"],
         "มี static check แล้ว ต้องเพิ่ม design review ก่อนพัฒนา"),
    ],
    "3. Design Team": [
        ("UX Designer", "ออกแบบ user journey / wireframe",
         "07", ["index.html", "book_design_system.py"], "ยังไม่มี wireframe artifact แยก"),
        ("UI Designer", "ออกแบบสี ฟอนต์ ไอคอน Design System",
         "07", ["book_design_system.py", "image_studio.py"], "Design System ยังไม่รวม Web UI"),
    ],
    "4. Development Team": [
        ("System Architect / Tech Lead", "เลือก stack คุมมาตรฐานโค้ด",
         "02", ["systems_analyst.py", "app.py"], "มีแล้วบางส่วน"),
        ("Backend Developer", "เซิร์ฟเวอร์ API ฐานข้อมูล หลังบ้าน",
         "02", ["app.py", "store.py", "five_engines.py"], "ยังมี endpoint ที่ authz ไม่บังคับ"),
        ("Frontend Developer", "เว็บ/หน้าผู้ใช้",
         "07", ["index.html", "STORE.html", "GOVERNANCE.html"], "หน้าเดิมบางปุ่มยังเป็น fallback"),
        ("Mobile App Developer", "แอปมือถือ iOS/Android",
         "02", [], "ยังไม่มี — ต้องตัดสินใจว่าจำเป็นหรือไม่"),
        ("Database Administrator", "ออกแบบ ปรับแต่ง ดูแลความปลอดภัยข้อมูล",
         "09/03", ["app.py remote KV", "github_backup.py"], "ไม่มี relational DB/migration"),
    ],
    "5. QA & Operations": [
        ("QA / Tester", "เขียน test case ทดสอบ manual/automatic",
         "10", ["test_zyphere.py", "systems_analyst.py"], "CI เพิ่งเพิ่ม test gate"),
        ("DevOps Engineer", "Deploy CI/CD cloud monitoring security",
         "11", ["trigger2.py", "restart_svc.py", ".github/workflows/deploy.yml"],
         "ยังไม่มี structured logging/metrics"),
    ],
    "6. Support & Documentation": [
        ("Technical Writer", "คู่มือผู้ใช้ + เอกสารเทคนิค",
         "09", ["governance/*.md", "README.md"], "มีเอกสารแต่ยังไม่มี user guide รวม"),
        ("IT Support / Customer Support", "รับเรื่องเมื่อใช้งานจริง ส่งต่อทีมพัฒนา",
         "11/12", ["help.py", "support.json"], "ยังไม่มี ticket workflow"),
    ],
}


class ITOrg:
    def __init__(self):
        self.lock = threading.RLock()
        self.roles = []
        for group, items in GROUPS.items():
            for role, mission, div, mods, gap in items:
                self.roles.append({"group": group, "role": role, "mission": mission,
                                   "division": div, "current_modules": mods, "gap": gap,
                                   "proposed": not mods})

    def list(self):
        return {"ok": True, "groups": len(GROUPS), "roles": len(self.roles),
                "implemented": sum(1 for r in self.roles if not r["proposed"]),
                "proposed": sum(1 for r in self.roles if r["proposed"]),
                "details": self.roles}

    def report(self):
        md = ["# Zyphere IT Organization (Large-Scale Software Project)", "",
              "Map บทบาทไอทีที่จำเป็นเข้ากับ 12 ฝ่ายเดิม — ไม่สร้างฝ่ายใหม่ซ้ำ", ""]
        for g in GROUPS:
            md += ["## " + g, "", "| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |", "|---|---|---|---|"]
            for r in self.roles:
                if r["group"] == g:
                    md.append("| %s | %s | %s | %s |" %
                              (r["role"], r["division"],
                               ", ".join(r["current_modules"]) or "ยังไม่มี",
                               r["gap"]))
            md.append("")
        return "\n".join(md)


IT = ITOrg()
