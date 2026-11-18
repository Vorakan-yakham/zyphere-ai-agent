"""Zyphere Master Registry & Governance Document Generator.

Implements the Master Development Directive's REQUIRED DELIVERABLES as real,
auditable files. It does NOT delete, rename or dissolve any existing structure:
every existing department, scholar faculty, supervisor and agent is mapped into
the proposed 12 divisions, and everything new is marked 'proposed' until the
owner enables it.

Source of truth for this file + the live system's endpoints. Generated docs go
to governance/ in the main repo so they are versioned and visible.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance")

# ---------------------------------------------------------------- existing state
EXISTING_DEPTS = [
    ("นักวิเคราะห์ระบบ", "systems_analyst.py", "ตรวจสถาปัตยกรรม/secret/route", "02,10"),
    ("ฐานข้อมูล", "app.py remote KV + github_backup.py", "KV + GitHub persistence", "03,09"),
    ("โปรแกรมเมอร์", "app.py + test_zyphere.py", "เขียนโค้ด commit/deploy", "02"),
    ("ฝ่ายวิชาการ", "scholars.py (46), faculty_expansion.py", "46 คณะ 184 สาขา", "01,04"),
    ("ฝ่ายภาษา", "language.py + co_learning", "แก้คำ ตรวจข้อความ", "04"),
    ("ฝ่ายออกแบบผลิตภัณฑ์", "book_design_system.py", "ปก layout grid", "07,02"),
    ("ฝ่ายผลิตหนังสือ", "book_team.py..v5", "ผลิตเล่ม + QA", "07"),
    ("ฝ่ายการตลาด", "marketing_promoter.py", "PROMO.md โพสต์", "07,12"),
    ("ฝ่ายทดสอบ", "test_zyphere.py + systems_analyst.py", "regression 11/11", "10"),
    ("ฝ่ายปฏิบัติการ", "Render + trigger2.py + restart", "deploy/restart", "11"),
    ("ฝ่ายความปลอดภัย", "safety.py, authz.py, audit.py", "fail-closed gate", "10"),
]

DIVISIONS = {
    "01": ("Research & Science Division", "วิจัยและวิทยาศาสตร์พื้นฐาน",
           ["scholars.py 46 คณะ", "research.py", "scholar_research.py", "Scientific Discovery Center*",
            "Open Science Center*", "Standards & Benchmark Center*"]),
    "02": ("Engineering & Technology Division", "วิศวกรรมและเทคโนโลยี",
           ["โปรแกรมเมอร์", "นักวิเคราะห์ระบบ", "Autonomous Systems Center*",
            "Advanced Computing Center*", "Digital Twin Center*"]),
    "03": ("AI & Data Intelligence Division", "AI และข้อมูล",
           ["brain_ensemble.py", "local_brain.py", "dev_brain.py", "ฐานข้อมูล",
            "AI Memory & Knowledge Systems*", "Agentic AI Research*"]),
    "04": ("Humanities & Society Division", "มนุษยศาสตร์และสังคม",
           ["ฝ่ายภาษา", "ฝ่ายวิชาการ (ส่วนมนุษยศาสตร์)", "กฎหมาย/ปรัชญา/ประวัติศาสตร์"]),
    "05": ("Earth & Life Systems Division", "โลกและชีวิต",
           ["geo/bio/agri/water/energy faculties", "Resilience & Crisis Research*",
            "Global Problem Solving Center*"]),
    "06": ("Innovation & Futures Division", "นวัตกรรมและอนาคต",
           ["Strategic Foresight Center*", "Digital Civilization Research*",
            "Human Potential Research*", "concept.py", "cross_disciplinary.py"]),
    "07": ("Product & Business Division", "ผลิตภัณฑ์และธุรกิจ",
           ["ฝ่ายผลิตหนังสือ", "ฝ่ายการตลาด", "ฝ่ายออกแบบผลิตภัณฑ์", "store.py",
            "Technology Transfer Center*"]),
    "08": ("Learning & Development Division", "การเรียนรู้และพัฒนาบุคลากร",
           ["co_learning.py", "cross_disciplinary.py", "curriculum.py",
            "academy.py", "Employee Growth System*"]),
    "09": ("Knowledge & Research Operations Division", "ปฏิบัติการความรู้และวิจัย",
           ["ฐานข้อมูล", "research.py", "knowledge_graph.py", "rag.py",
            "Living Knowledge System*", "Global Collaboration Center*"]),
    "10": ("Safety & Governance Division", "ความปลอดภัยและกำกับดูแล",
           ["ฝ่ายความปลอดภัย", "ฝ่ายทดสอบ", "นักวิเคราะห์ระบบ", "quality_ops.py",
            "Independent Evaluation Office*"]),
    "11": ("Operations & Resources Division", "ปฏิบัติการและทรัพยากร",
           ["ฝ่ายปฏิบัติการ", "Render", "Upstash KV", "GitHub", "ratelimit.py"]),
    "12": ("Strategy & Partnerships Division", "กลยุทธ์และความร่วมมือ",
           ["Global Intelligence Center*", "demand.py", "market.py", "autopost.py"]),
}


STRATEGIC_CENTERS = [
    ("Global Intelligence Center", "12"), ("Scientific Discovery Center", "01"),
    ("Advanced Simulation Center", "06"), ("Autonomous Systems Center", "02"),
    ("Digital Civilization Research Center", "06"), ("Human Potential Research Center", "08"),
    ("Strategic Foresight Center", "06"), ("Global Problem Solving Center", "05"),
    ("Advanced Computing Center", "02"), ("Technology Transfer Center", "07"),
    ("Standards & Benchmark Center", "10"), ("Digital Twin Center", "02"),
    ("Open Science Center", "01"), ("Global Collaboration Center", "09"),
    ("Resilience & Crisis Research Center", "05"),
]

FIVE_ENGINES = [
    ("Knowledge Engine", "รวบรวม จัดหมวดหมู่ เชื่อมโยงความรู้",
     "research.py, knowledge_graph.py, rag.py, world_taxonomy.json",
     "ยังไม่มี ontology/vector DB จริง", "09"),
    ("Learning Engine", "พัฒนาความรู้ AI และบุคลากร",
     "curriculum.py, co_learning.py, cross_disciplinary.py, dev_brain.py",
     "เป็น text accumulation ไม่ใช่ model training", "08"),
    ("Research Engine", "ค้นคว้า ตั้งสมมติฐาน ทดลอง ตรวจสอบ",
     "research.py, scholar_research.py, elibrary.py",
     "ไม่มี experiment registry / statistical stack", "01"),
    ("Innovation Engine", "เปลี่ยนองค์ความรู้เป็นต้นแบบ",
     "book_team*, codeforge.py, media.py, concept.py",
     "ไม่มี image generation / 3D", "06"),
    ("Governance Engine", "ตรวจคุณภาพ ความปลอดภัย ผลกระทบ",
     "safety.py, authz.py, audit.py, quality_ops.py, systems_analyst.py",
     "authz ยังไม่บังคับทุก endpoint", "10"),
]

CREATIVE_GAPS = [
    ("AI Image Studio", "ไม่มี generative image — มีแค่ stock image + PIL",
     "ComfyUI / HF Spaces (external)", "Phase 1"),
    ("AI Video Composer", "มี slideshow+FFmpeg จริง", "ใช้ของเดิมต่อ + TTS/SRT", "Phase 2"),
    ("Text-to-Video", "ยังไม่มี", "Wan 2.2 บน GPUภายนอก", "Phase 3"),
    ("AI Audio Studio", "มี TTS/STT จริง", "Whisper + Kokoro (external)", "Phase 4"),
    ("Design Studio", "มี book_design_system + HTML/CSS", "SVG generator", "Phase 4"),
    ("3D Studio", "ไม่มีเลย", "ต้องรอ GPU/engine", "Phase 5"),
    ("AI Creative Director", "ยังไม่มี", "multi-model + QA loop", "Phase 6"),
]

ROADMAP = [
    ("PHASE 1", "AUDIT", "ตรวจโครงสร้างเดิม/ระบบ/ความรู้/บุคลากร", "เสร็จแล้ว", "Audit Report"),
    ("PHASE 2", "ARCHITECTURE", "12 ฝ่าย + ศูนย์ + registry", "เอกสาร生成แล้ว รอยืนยันการเปิดใช้งาน", "Master Registry"),
    ("PHASE 3", "FOUNDATION", "คลังความรู้กลาง/หลักสูตร/ระบบประเมิน", "มีบางส่วน ต้องเชื่อม", "Knowledge+Learning Engine"),
    ("PHASE 4", "INTEGRATION", "โปรเจกต์วิจัยข้ามศาสตร์", "มี cross_disciplinary แล้ว", "Research Engine"),
    ("PHASE 5", "INNOVATION", "ต้นแบบ/นวัตกรรมจริง", "ยังขาด image/3D", "Innovation Engine"),
]

KPI = [
    ("Knowledge Coverage", "46 คณะ / 184 สาขา / 4225 สาขาโลก", "ครบทุกสาขามีเจ้าภาพ", "Master Registry"),
    ("Knowledge Accuracy", "แหล่งที่มา 20/46 มี URL จริง", ">80% มี URL", "scholar_research.py"),
    ("Understanding & Reasoning", "QA 11/11, test pass", "ไม่ถอยหลัง", "systems_analyst.py"),
    ("Research Quality", "documents 20, A=12 B=7 C=1", "เพิ่ม A ratio", "research.py"),
    ("Innovation Capability", "หนังสือ/ร้าน/วิดีโอ slideshow", "เพิ่ม image studio", "Creative directive"),
    ("Employee Development", "11/11 doctor + cross", "รักษาระดับ + certification", "LEARNING.html"),
    ("Cross-Dept Collaboration", "11 แผนก cross-disciplinary", "โปรเจกต์จริง 1 ขึ้นไป", "cross_disciplinary.py"),
    ("Real-World Impact", "ร้าน/ebook อยู่ GitHub", "ยอดที่ตรวจได้จริง", "store.py"),
]


RISKS = [
    ("Hardcoded credential", "set_pw.py มีรหัสจริงฝังในโค้ด", "critical", "เปลี่ยนเป็น env var"),
    ("Fake status", "self-reported counters", "high", "แยก status จริงออกจากตัวเลข"),
    ("No GPU", "Render free ไม่มี GPU", "high", "ส่งไป engine ภายนอก"),
    ("Fragmented source of truth", "46 คณะอยู่ 2 ไฟล์", "medium", "ใช้ Master Registry เป็นกลาง"),
    ("No CI gate", "GitHub Actions ไม่รัน test", "medium", "เพิ่ม test job"),
    ("Authz ไม่ครบ", "endpoint ส่วนใหญ่เปิด", "medium", "บังคับทีละกลุ่ม"),
]


def w(name, lines):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name + ".md"), "w", encoding="utf-8").write("\n".join(lines))


def jline(k, v):
    return "- **%s:** %s" % (k, v)


def main():
    w("00_MASTER_ORGANIZATIONAL_CHART", [
        "# Zyphere Master Organizational Chart", "",
        "สถานะ: เสนอ (ยังไม่ลบ/ยุบ/เปลี่ยนชื่อสิ่งเดิม)", "",
        "## 12 Strategic Divisions",
    ] + ["### %s %s\n\n%s" % (k, v[0], "\n".join("- " + d for d in v[2]))
         for k, v in sorted(DIVISIONS.items())] + [
        "", "## Existing 11 Departments — mapped (not removed)",
    ] + ["- %s → ฝ่าย %s" % (d[0], d[3]) for d in EXISTING_DEPTS])

    w("01_EXISTING_DEPARTMENTS_AUDIT", [
        "# Existing Departments Audit", "",
        "ตรวจจากโค้ดจริง 2026-11-18 — ไม่ได้คาดเดา", "",
        "| แผนก | แหล่งข้อมูลจริง | หน้าที่ | ฝ่ายเป้าหมาย |", "|---|---|---|---|",
    ] + ["| %s | %s | %s | %s |" % d for d in EXISTING_DEPTS] + [
        "", "## ข้อสังเกต", "",
        "- role_registry.py มี 10 seed แต่ co_learning.py มี 11 — ต้องใช้ Master Registry เป็นแหล่งกลาง",
        "- 46 คณะอยู่ใน scholars.py และ faculty_expansion.py ซ้ำกัน — ให้ Master Registry เป็นตัวกลาง",
        "- ศูนย์ยุทธศาสตร์ 15 แห่งยังเป็น 'proposed' ทั้งหมด (เครื่องหมาย *)",
        "- ไม่มีพนักงานมนุษย์ใน 11 แผนก — เป็น AI agent + owner (มนุษย์) คนเดียว",
    ])

    w("02_PROPOSED_12_DIVISIONS", [
        "# Proposed 12 Divisions", "",
        "* = หน่วยงานเสนอใหม่ ยังไม่เปิดใช้งาน", "",
    ] + ["## %s %s\n\n%s" % (k, v[0], "\n".join("- " + d for d in v[2]))
         for k, v in sorted(DIVISIONS.items())])

    w("03_COMPLETE_DEPARTMENT_DIRECTORY", [
        "# Complete Department Directory", "",
        "## Existing (active)",
    ] + [jline(d[0], d[2] + " · " + d[1]) for d in EXISTING_DEPTS] + [
        "", "## Strategic Centers (proposed)",
    ] + [jline(c[0], "ฝ่าย " + c[1]) for c in STRATEGIC_CENTERS])

    w("04_DEPARTMENT_RESPONSIBILITY_MATRIX", [
        "# Department Responsibility Matrix", "",
        "| ฝ่าย | ความรับผิดชอบหลัก | ผลงานที่ตรวจได้ |", "|---|---|---|",
    ] + ["| %s | %s | %s |" % (k, v[1], ", ".join(v[2][:2])) for k, v in sorted(DIVISIONS.items())])

    w("05_GLOBAL_KNOWLEDGE_COVERAGE_MATRIX", [
        "# Global Knowledge Coverage Matrix", "",
        "- 46 คณะ · 184 สาขาย่อย · 4225 สาขาวิชาจริงจาก Wikipedia",
        "- แหล่งอ้างอิงจริงมี URL 20/46 คณะ",
        "- ทุกสาขามีเจ้าภาพผ่าน 15 rules ของ scholar_routing.py",
        "- ยังขาด: ontology, vector DB, citation manager แบบ DOI",
    ])

    w("06_MASTER_LEARNING_CURRICULUM", [
        "# Master Learning Curriculum", "",
        "## Level A — Common", "\n".join("- " + x for x in [
            "จริยธรรม/ความปลอดภัย", "การอ่านและสังเคราะห์แหล่งข้อมูล",
            "ภาษาไทยที่ถูกต้อง", "การตรวจสอบข้อเท็จจริง"]),
        "## Level B — Professional", "\n".join("- " + x for x in [
            "ตามสายงาน 11 แผนก", "doctor-level 5 บทเรียน/แผนก", "ปฏิบัติจริงผ่านโปรเจกต์"]),
        "## Level C — Cross-disciplinary", "\n".join("- " + x for x in [
            "11 แผนก × 4-5 สาขาที่เกี่ยวข้อง", "cross-department workshop",
            "โปรเจกต์วิจัยข้ามศาสตร์"]),
        "## 4 ระดับบุคลากร", "Foundation → Practitioner → Specialist → Research Leader",
    ])

    w("07_EMPLOYEE_DEVELOPMENT_FRAMEWORK", [
        "# Employee Development Framework", "",
        "- Personal Learning Profile: data/co_learning.json",
        "- Individual Learning Path: cross_disciplinary.RELATED",
        "- Practical Assignments: งานจริงใน repo + GitHub",
        "- Peer Learning: LEARNING.html",
        "- Mentorship: supervisors.py (10 คน)",
        "- Competency Certification: ยังไม่มี — เสนอเพิ่ม",
        "- Career Development: ยังไม่มี — เสนอเพิ่ม",
        "- อนุญาตเปลี่ยนสาย/ข้ามแผนก: cross_disciplinary แล้ว",
    ])

    w("08_UNIFIED_LEARNING_SYSTEM_ARCHITECTURE", [
        "# Unified Learning System Architecture", "",
        "- co_learning.py → ensemble → LocalBrain + DevBrain",
        "- cross_disciplinary.py → 11 แผนกพร้อมกัน",
        "- LEARNING.html → /api/co-learn/levels (real-time)",
        "- ต้องแยก Retrieval / Memory / Model Training / Evaluation (ยังไม่มี training)",
    ])

    w("09_RESEARCH_INNOVATION_FRAMEWORK", [
        "# Research & Innovation Framework", "",
        "ทุกโปรเจกต์ต้องมี: Objective, Problem, Questions, Team, Leader, Method,",
        "Evidence, Budget, Risk, Validation, Deliverables, Final Report", "",
        "ตัวอย่าง: Smart Agriculture, Advanced Healthcare, Intelligent Robotics,",
        "Sustainable Energy, Future Cities, Climate Modeling, Human-AI Systems, Space Tech",
    ])

    w("10_INTERDISCIPLINARY_COLLABORATION", [
        "# Interdisciplinary Collaboration Framework", "",
        "- knowledge_graph.py: 184/184 สาขาเชื่อมกัน",
        "- scholar_routing.py: 184 สาขา → 14 ผู้เชี่ยวชาญ",
        "- cross_disciplinary.py: 11 แผนกเรียนรู้ข้ามสาขา",
        "- ยังขาด: โปรเจกต์วิจัยข้ามแผนกที่มีผลงานจริง 1 โปรเจกต์",
    ])

    w("11_GLOBAL_KNOWLEDGE_ACQUISITION_STRATEGY", [
        "# Global Knowledge Acquisition Strategy", "",
        "แหล่งที่เชื่อมต่อแล้วจริง: Wikipedia (summary), arXiv/PubMed/OpenLibrary (elibrary.py), RSS",
        "แหล่งที่เสนอแต่ยังไม่ได้เชื่อมจริง: MIT OCW, Stanford, Semantic Scholar, OpenAlex,",
        "DOAJ, UNESCO, NASA, CERN, NIST, WHO, World Bank, OECD, Our World in Data, IEEE, ACM,",
        "Google Patents, WIPO, ThaiJO, NSTDA", "",
        "กฎ: ห้ามอ้างว่าได้อ่านแหล่งที่ยังเข้าถึงไม่จริง — ต้องบันทึก URL + วันที่ + license",
    ])

    w("12_KNOWLEDGE_MANAGEMENT_ARCHITECTURE", [
        "# Knowledge Management Architecture", "",
        "มีแล้ว: Research Library, Knowledge Base, Knowledge Graph, Version Control (GitHub),",
        "Research Metadata, Provenance (research.py), Archive (GitHub)",
        "ยังขาด: Vector DB, formal Ontology, Experiment Repository, Citation Manager (DOI)",
        "ห้ามพึ่งความจำโมเดลอย่างเดียว — ใช้ retrieval จากไฟล์/KV/GitHub",
    ])

    w("13_AI_CAPABILITY_EVALUATION", [
        "# AI Capability Evaluation Framework", "",
    ] + ["| ด้าน | ค่าเริ่มต้น | เป้า | ผู้รับผิดชอบ |", "|---|---|---|---|"] +
      ["| %s | %s | %s | %s |" % k for k in KPI])

    w("14_SAFETY_GOVERNANCE_FRAMEWORK", [
        "# Safety & Governance Framework", "",
        "- safety.py (blacklist), authz.py (ยังไม่บังคับทุก endpoint)",
        "- audit.py hash-chain, privacy.py forget, quality_ops.py PDCA",
        "- Independent Evaluation Office* — เสนอตั้ง แยกจากทีมผลิต",
        "- ห้ามทดลองความเสี่ยงสูงโดยไม่มีผู้เชี่ยวชาญ + อนุมัติ",
        "- Human Oversight: OTP/ชำระเงิน/ซื้อของ ต้องผู้ใช้กดเอง",
    ])

    w("15_RESOURCE_REQUIREMENTS", [
        "# Resource & Budget Requirements", "",
        "- Free แล้ว: GitHub, Render Free, Upstash Free, Wikipedia/arXiv/PubMed APIs",
        "- ต้องใช้เงิน/ผู้เชี่ยวชาญเมื่อ: GPU สำหรับ image/video/3D, ตรวจสอบวิชาการภายนอก",
        "- ห้ามสร้างค่าใช้จ่ายโดยไม่ได้รับอนุมัติ",
    ])

    w("16_IMPLEMENTATION_ROADMAP", [
        "# Implementation Roadmap", "",
        "| ระยะ | ชื่อ | งาน | สถานะ | เกณฑ์ผ่าน |", "|---|---|---|---|---|",
    ] + ["| %s | %s | %s | %s | %s |" % r for r in ROADMAP] + [
        "", "ห้ามลบของเดิม — ทุกการเปลี่ยนแปลงบันทึกใน audit log",
    ])

    w("17_KEY_PERFORMANCE_INDICATORS", [
        "# Key Performance Indicators (8 ด้าน)", "",
    ] + ["- %s: %s → %s (วัดโดย %s)" % (k, s, t, o) for k, s, t, o in KPI] + [
        "", "ห้ามใช้จำนวนเอกสาร/แผนกเป็นตัวชี้วัดความสำเร็จเพียงอย่างเดียว",
    ])

    w("18_RISK_REGISTER", [
        "# Risk Register", "",
        "| ความเสี่ยง | รายละเอียด | ระดับ | แนวทาง |", "|---|---|---|---|",
    ] + ["| %s | %s | %s | %s |" % r for r in RISKS])

    w("19_LONG_TERM_DEVELOPMENT_STRATEGY", [
        "# Long-Term Development Strategy (10 ปี)", "",
        "- ปี 1 Foundation: โครงสร้าง/ความรู้/ฐานข้อมูล/หลักสูตร (กำลังทำอยู่)",
        "- ปี 2-3 Integration: เชื่อมฝ่าย/agent/วิจัย",
        "- ปี 4-5 Research & Innovation: ศูนย์ขั้นสูง/ต้นแบบ",
        "- ปี 6-7 Global Collaboration: เครือข่ายมหาวิทยาลัย",
        "- ปี 8-10 Frontier Research: วิจัยแนวหน้า/โปรเจกต์ใหญ่",
        "เป็นกรอบเป้าหมาย ไม่ใช่การรับประกันผลตามช่วงเวลา",
    ])

    w("20_AUDIT_REPORT", [
        "# Organizational & Knowledge Audit Report", "",
        "ตรวจจริง 2026-11-18 จากโค้ด + Live API — ไม่ได้คาดเดา", "",
        "## สรุป", "",
        "- Python ~100 ไฟล์, app.py 5864 บรรทัด, ~278 endpoints, 19 features",
        "- 46 คณะ / 184 สาขา / 4225 สาขาโลก / 10-11 แผนก / 10 supervisors / 6 agents",
        "- ไม่มี vector database จริง — ใช้ JSON + keyword maps",
        "- ไม่มี model training/fine-tuning — 'learning' = text accumulation",
        "- ไม่มี generative image / 3D / generative video — มีแค่ stock slideshow + FFmpeg",
        "- Hardcoded credential ใน set_pw.py (critical)",
        "- book_team_v3.py พัง (syntax error) — dead code",
        "- CI ไม่รัน test; superiority.py ใช้ market narrative ที่กำหนดเอง",
        "- authz.py ไม่ได้บังคับทุก endpoint", "",
        "## สิ่งที่มีจริง", "",
    ] + [jline(x[0], x[1]) for x in FIVE_ENGINES] + [
        "", "## สิ่งที่ขาดจริง", "",
    ] + [jline(x[0], x[1] + " → " + x[2]) for x in CREATIVE_GAPS] + [
        "", "## ข้อเสนอ", "",
        "- ใช้ Master Registry เป็นแหล่งความจริงกลาง (ไม่ลบของเดิม)",
        "- เปิดใช้งาน 12 ฝ่ายแบบ mapping ไม่สร้างฝ่ายใหม่ 100 ฝ่าย",
        "- ศูนย์ยุทธศาสตร์ 15 แห่ง marked proposed",
        "- แก้ credential ก่อนเปิดระบบอื่น",
        "- เพิ่ม CI test gate + authz enforcement ทีละกลุ่ม",
    ])

    try:
        from it_org import IT
        w("22_IT_ORGANIZATION", IT.report().split("\n"))
    except Exception as e:
        w("22_IT_ORGANIZATION", ["# IT Organization", "", "unavailable: " + str(e)[:100]])

    w("21_MASTER_REGISTRY", [
        "# Zyphere Global Department & Knowledge Master Registry", "",
        "ทะเบียนกลาง: ศาสตร์ → สาขา → ฝ่าย → แผนก → ผู้เชี่ยวชาญ → หลักสูตร → งานวิจัย → ช่องว่าง", "",
        "## 12 Divisions",
    ] + ["### %s %s\n%s" % (k, v[0], "\n".join("- " + d for d in v[2]))
         for k, v in sorted(DIVISIONS.items())] + [
        "", "## 5 Engines",
    ] + [jline(e[0], e[1] + " · มี: " + e[2] + " · ขาด: " + e[3]) for e in FIVE_ENGINES] + [
        "", "## Status rule", "",
        "ทุกหน่วยใหม่ = proposed จนกว่าจะเปิดใช้งาน — ห้ามอ้างว่าทำงานแล้วโดยไม่มีโค้ด/ทดสอบ",
    ])

    # machine-readable
    os.makedirs(OUT, exist_ok=True)
    json.dump({"divisions": DIVISIONS, "existing": EXISTING_DEPTS,
               "centers": STRATEGIC_CENTERS, "engines": FIVE_ENGINES,
               "kpi": KPI, "risks": RISKS, "t": int(time.time())},
              open(os.path.join(OUT, "registry.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("generated", len(os.listdir(OUT)), "files in", OUT)


if __name__ == "__main__":
    main()
