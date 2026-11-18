"""Zyphere Professional Role Profiles — 23 IT/growth roles in detail.

Each profile: mission, duties, skills, tools, KPIs (measurable), deliverables,
collaborators and source. Built from the owner's brief + Wikipedia
(Growth hacking, Scrum) + cross-brain research in ROLE_PROFILES_RESEARCH.md.
HONEST: roles are AI agents in one process, not hired humans.
"""
import os, re, json, threading

ROOT = os.path.dirname(os.path.abspath(__file__))

SRC_SCRUM = "https://en.wikipedia.org/wiki/Scrum_(software_development)"
SRC_GROWTH = "https://en.wikipedia.org/wiki/Growth_hacking"
SRC_SCRUM_OFFICIAL = "https://scrumguides.org/scrum-guide.html"
SRC_SEO_GOOGLE = "https://developers.google.com/search/docs/beginner/seo-starter-guide"
SRC_UX = "https://en.wikipedia.org/wiki/User_experience_design"
SRC_DEVOPS = "https://en.wikipedia.org/wiki/DevOps"
SRC_MULTI = "governance/ROLE_PROFILES_RESEARCH.md (Groq + Gemini วิเคราะห์ข้ามสาขา)"

SOURCE_MAP = {
    "Project Manager / Scrum Master": [SRC_SCRUM_OFFICIAL, SRC_SCRUM, SRC_MULTI],
    "Product Owner": [SRC_SCRUM_OFFICIAL, SRC_SCRUM, SRC_MULTI],
    "Business Analyst": [SRC_MULTI, "https://en.wikipedia.org/wiki/Business_analysis"],
    "System Analyst": [SRC_MULTI, "https://en.wikipedia.org/wiki/Systems_analysis"],
    "UX Designer": [SRC_UX, SRC_MULTI],
    "UI Designer": ["https://en.wikipedia.org/wiki/User_interface_design", SRC_MULTI],
    "System Architect / Tech Lead": [SRC_MULTI, "https://en.wikipedia.org/wiki/Software_architecture"],
    "Backend Developer": [SRC_MULTI, "https://en.wikipedia.org/wiki/Server-side_scripting"],
    "Frontend Developer": [SRC_MULTI, "https://en.wikipedia.org/wiki/Front-end_web_development"],
    "Mobile App Developer": [SRC_MULTI, "https://en.wikipedia.org/wiki/Mobile_development"],
    "Database Administrator": [SRC_MULTI, "https://en.wikipedia.org/wiki/Database_administration"],
    "QA / Tester": [SRC_MULTI, "https://en.wikipedia.org/wiki/Software_testing"],
    "DevOps Engineer": [SRC_DEVOPS, SRC_MULTI],
    "Technical Writer": [SRC_MULTI, "https://en.wikipedia.org/wiki/Technical_writing"],
    "IT Support / Customer Support": [SRC_MULTI, "https://en.wikipedia.org/wiki/Technical_support"],
    "Growth Manager / Growth Hacker": [SRC_GROWTH, SRC_MULTI],
    "Data Analyst": [SRC_GROWTH, SRC_MULTI, "https://en.wikipedia.org/wiki/Data_analysis"],
    "Paid Ads Specialist (Media Buyer)": [SRC_GROWTH, SRC_MULTI],
    "SEO & ASO Specialist": [SRC_SEO_GOOGLE, SRC_MULTI],
    "Content Creator / Copywriter": [SRC_SEO_GOOGLE, SRC_MULTI],
    "Graphic Designer & Video Editor": [SRC_MULTI, "https://en.wikipedia.org/wiki/Graphic_design"],
    "CRM Specialist": [SRC_MULTI, "https://en.wikipedia.org/wiki/Customer_relationship_management"],
    "Community & Partnership Manager": [SRC_MULTI, SRC_GROWTH],
}

P = {}

def add(name, group, mission, duties, skills, tools, kpis, deliverables, collab, source=""):
    P[name] = {"role": name, "group": group, "mission": mission,
               "duties": duties, "skills": skills, "tools": tools,
               "kpis": kpis, "deliverables": deliverables, "collaborators": collab,
               "source": source,
               "sources": SOURCE_MAP.get(name, [source] if source else [])}

# --- 1 Management & Governance ---
add("Project Manager / Scrum Master", "Management & Governance",
    "บริหาร Sprint ให้ส่งมอบตรงเวลาและลดอุปสรรคข้ามทีม",
    ["กำหนด Sprint goal และวางแผน Sprint planning", "จัด Daily scrum ไม่เกิน 15 นาที",
     "ติดตาม burndown และ Velocity", "จัด Sprint review/retrospective และเก็บ lessons"],
    ["Agile/Scrum", "Facilitation", "Risk management", "Communication", "Data tracking"],
    ["chief.py", "systems_analyst.py", "governance/registry.json", "QUALITY_REPORT.md"],
    ["Sprint ตรงเวลา ≥90%", "Velocity เสถียร 3 sprint ติด", "Blocker แก้ภายใน 24 ชม.", "DoD ผ่าน 100%"],
    ["Sprint backlog", "Burndown chart", "Retrospective report"],
    ["Product Owner", "QA/Tester"], SRC_SCRUM)
add("Product Owner", "Management & Governance",
    "เป็นเสียงผู้ใช้ จัดลำดับ Backlog ให้ทีมทำสิ่งมีค่าที่สุดก่อน",
    ["เก็บความต้องการจากผู้ใช้/ข้อมูลจริง", "เขียน user story และ acceptance criteria",
     "จัดลำดับ product backlog ตามมูลค่า", "ตัดสินใจ go/no-go ของ feature"],
    ["Product vision", "Backlog refinement", "Prioritization", "Stakeholder communication", "Analytics"],
    ["demand.py", "market.py", "master_registry.py", "/api/growth/search"],
    ["Backlog มี AC ครบ 100%", "Feature ที่ปล่อยมีข้อมูลรองรับ", "Time-to-decision < 2 วัน", "ผู้ใช้ให้feedback ≥1 รอบ"],
    ["Product backlog", "PRD", "Release decision log"],
    ["Project Manager", "Business Analyst"], SRC_SCRUM)

# --- 2 Business & Analysis ---
add("Business Analyst", "Business & Analysis",
    "ถอดความต้องการทางธุรกิจเป็นข้อกำหนดที่ทีมพัฒนาเข้าใจตรงกัน",
    ["สัมภาษณ์ผู้ใช้/เจ้าของระบบ", "แยก functional และ non-functional requirement",
     "เขียน user story/use case", "ตรวจความขัดแย้งของข้อกำหนด"],
    ["Requirement elicitation", "Process modeling", "Documentation", "Interview", "Critical thinking"],
    ["help.py", "intent.py", "concept.py", "governance/*.md"],
    ["Requirement มีแหล่งที่มา 100%", "ไม่มีข้อกำหนดขัดแย้ง", "ทีมพัฒนาเข้าใจ ≥90% (ทดสอบด้วยคำถาม)", "เปลี่ยนแปลงมีบันทึก"],
    ["BRD", "User stories", "Requirement traceability"],
    ["System Analyst", "Product Owner"])
add("System Analyst", "Business & Analysis",
    "ออกแบบสถาปัตยกรรม和 data flow แปลงความต้องการเป็นโครงสร้างระบบ",
    ["วิเคราะห์โครงสร้างเดิมก่อนเปลี่ยน", "ออกแบบ data flow และ schema",
     "กำหนด design gate ก่อนพัฒนา", "ตรวจหา duplication จุดอ่อน"],
    ["Systems analysis", "Architecture", "Data modeling", "Static analysis", "Design review"],
    ["systems_analyst.py", "SYSTEM_DESIGN_REVIEW.md", "governance/registry.json", "five_engines.py"],
    ["Design review ก่อน develop 100%", " Analyst ≥16/16", "ไม่มี path ตายตัว", "ไม่มีซ้ำ source of truth"],
    ["SYSTEM_ANALYSIS.md", "SYSTEM_DESIGN_REVIEW.md", "Data flow map"],
    ["Tech Lead", "QA/Tester"])

# --- 3 Design ---
add("UX Designer", "Design Team",
    "ออกแบบ user journey ให้ผู้ใช้ทำสำเร็จในขั้นตอน最少",
    ["วิเคราะห์พฤติกรรมผู้ใช้และจุดออกกลางทาง", "วาง wireframe/user journey",
     "ทดสอบความเข้าใจกับผู้ใช้จริง", "ปรับลดขั้นตอนที่ไม่จำเป็น"],
    ["User research", "Journey mapping", "Wireframing", "Usability testing", "Empathy"],
    ["index.html", "STORE.html", "GROWTH.html", "LEARNING.html"],
    ["อ่านแล้วรู้ว่ากดอะไร ≥90%", "ลดขั้นตอนซื้อเหลือ ≤3", "มีผู้ใช้ทดสอบจริง ≥1 คน", "ไม่มีปุ่มที่ไม่มี backend"],
    ["User journey", "Wireframe", "Usability finding"],
    ["UI Designer", "Frontend Developer"])
add("UI Designer", "Design Team",
    "กำหนด Design System สี/ฟอนต์/ไอคอนให้สม่ำเสมอและเป็นแบรนด์",
    ["สร้าง design token (สี ฟอนต์ ระยะ)", "ออกแบบไอคอน mono + โลโก้มีสีติดชื่อ",
     "ตรวจ contrast และ alignment", "ทำ responsive"],
    ["Typography", "Color theory", "Grid", "Visual hierarchy", "Design system"],
    ["book_design_system.py", "image_studio.py", "creative_director.py", "index.html"],
    ["Design token ใช้ตรงกัน 100%", "Contrast ผ่าน squint test", "หน้าเว็บเปิดได้ทุกขนาด", "ไม่มี gradient ฉูดฉาดเกิน"],
    ["Design System", "Cover/poster", "UI spec"],
    ["UX Designer", "Graphic Designer & Video Editor"])

# --- 4 Development ---
add("System Architect / Tech Lead", "Development Team",
    "เลือก stack คุมมาตรฐานโค้ด และกันไม่ให้ระบบแตกเมื่อขยาย",
    ["กำหนดโครงสร้างโมดูลและสัญญา API", "review import order/persistence",
     "ตั้ง gate ก่อน commit", "ดูแล technical debt"],
    ["Architecture", "Python", "HTTP server", "Git", "Code review"],
    ["app.py", "systems_analyst.py", "master_registry.py", "requirements.txt"],
    ["py_compile ผ่าน 100%", "regression ผ่าน", "ไม่มี secret ในโค้ด", "deploy สำเร็จ"],
    ["Architecture diagram", "Coding standard", "Tech debt list"],
    ["Backend Developer", "DevOps Engineer"])
add("Backend Developer", "Development Team",
    "สร้าง API และระบบหลังบ้านที่เชื่อถือได้",
    ["เขียน endpoint แบบ targeted edit", "แยก business logic ออกจาก handler",
     "ป้องกัน fail-open", "ทดสอบก่อน deploy"],
    ["Python", "http.server", "JSON persistence", "Auth", "Testing"],
    ["app.py", "store.py", "five_engines.py", "test_zyphere.py"],
    ["endpoint ตอบ 200", "admin fail-closed", "มี test ครบ", "ไม่ทำลายของเดิม"],
    ["API endpoint", "Module", "Test case"],
    ["Frontend Developer", "Database Administrator"])
add("Frontend Developer", "Development Team",
    "สร้างหน้าที่ใช้งานได้จริงและเชื่อม backend ทุกปุ่ม",
    ["ผูกทุก button กับ handler จริง", "แสดง status ที่ตรงความจริง",
     " responsive และ font ไทย", "ไม่สร้างปุ่มที่ไม่มีระบบรองรับ"],
    ["HTML/CSS/JS", "Fetch API", "Responsive", "Accessibility", "UI state"],
    ["index.html", "STORE.html", "GOVERNANCE.html", "GROWTH.html"],
    ["ทุกปุ่มมี handler", "ไม่มี 404 จากลิงก์", "font ไทยอ่านได้", "แสดงข้อมูลจริง"],
    ["UI page", "JS handler", "UI test"],
    ["Backend Developer", "UI Designer"])
add("Mobile App Developer", "Development Team",
    "พัฒนาแอปมือถือหากโปรเจกต์ต้องการ (ยังไม่เปิด — proposed)",
    ["ประเมินความจำเป็นก่อนสร้าง", "เลือก cross-platform หากคุ้ม",
     "เชื่อม API เดิม", "ส่งStorm แอป"],
    ["React Native/Flutter", "Mobile UX", "API integration", "Store submission", "Testing"],
    ["ยังไม่มี — ต้องตัดสินใจ", "app.py API พร้อมอยู่แล้ว"],
    ["ยังไม่กำหนด — proposed", "ยังไม่กำหนด", "ยังไม่กำหนด", "ยังไม่กำหนด"],
    ["ยังไม่มี", "ยังไม่มี", "ยังไม่มี"],
    ["Frontend Developer", "Product Owner"])
add("Database Administrator", "Development Team",
    "ดูแลความต่อเนื่องของข้อมูลข้าม restart",
    ["ออกแบบชั้นจัดเก็บ (KV + GitHub)", "ตั้ง restore หลัง restart",
     "สำรองอัตโนมัติ", "ตรวจความสมบูรณ์"],
    ["Redis/Upstash", "GitHub API", "JSON schema", "Backup/restore", "Concurrency"],
    ["app.py remote KV", "github_backup.py", "engine_stats.py", "co_learning.py"],
    ["restore สำเร็จหลัง restart", "ไม่เสียออเดอร์", "มี backup ภายนอก", "lock ป้องกันชน"],
    ["Storage design", "Restore report", "Backup log"],
    ["Backend Developer", "DevOps Engineer"])

# --- 5 QA & Operations ---
add("QA / Tester", "QA & Operations",
    "หาข้อบกพร่องก่อนผู้ใช้เจอ ด้วย test ที่รันได้จริง",
    ["เขียน regression test", "รัน static analyst", "ทดสอบ endpoint จริง",
     "ตรวจหา copy-paste/คำผิด"],
    ["pytest-style scripting", "HTTP testing", "Static analysis", "Test design", "Bug reporting"],
    ["test_zyphere.py", "systems_analyst.py", "Dedup.check", "CI workflow"],
    ["test ผ่าน 100%", "analyst ≥16/16", "CI รัน test ก่อน deploy", "ไม่มีของก็อปปี้ผ่าน QA"],
    ["Test report", "Bug list", "Quality gate"],
    ["DevOps Engineer", "Tech Lead"])
add("DevOps Engineer", "QA & Operations",
    "ทำให้ deploy/restart ปลอดภัยและตรวจย้อนหลังได้",
    ["ตั้ง CI quality gate", "deploy ทีละขั้น", "restart เมื่อ process เก่า", "เก็บ log"],
    ["GitHub Actions", "Render API", "Shell", "Monitoring", "Rollback"],
    [".github/workflows/deploy.yml", "trigger2.py", "restart_svc.py", "check_deploys.py"],
    ["deploy 202/201", "health 200", "restart สำเร็จ", "log ครบ"],
    ["Deploy log", "Restart record", "Monitoring state"],
    ["QA/Tester", "Database Administrator"])
add("Technical Writer", "Support & Documentation",
    "เขียนเอกสารที่ผู้อื่นตรวจสอบและต่อยอดได้",
    ["เขียน user guide", "เขียน technical doc", "บันทึกการเปลี่ยนแปลง",
     "ระบุข้อจำกัดตรง ๆ"],
    ["Technical writing", "Thai language", "Structure", "Versioning", "Diagrams"],
    ["governance/*.md", "README.md", "SYSTEM_DESIGN_REVIEW.md", "ROLE_PROFILES_RESEARCH.md"],
    ["เอกสารตรงกับโค้ด", "มีแหล่งที่มา", "อัพเดทหลังเปลี่ยน", "ไม่กล่าวเกินจริง"],
    ["User guide", "API doc", "Changelog"],
    ["System Analyst", "IT Support"])
add("IT Support / Customer Support", "Support & Documentation",
    "รับเรื่องเมื่อใช้งานจริงแล้วส่งต่อให้ทีมที่เหมาะสม",
    ["รับเรื่องและจำแนกประเภท", "ตอบคำถามเบื้องต้น",
     "ส่งต่อปัญหาเชิงเทคนิค", "ติดตามผลและแจ้งผู้ใช้"],
    ["Communication", "Ticketing", "Triage", "Empathy", "Follow-up"],
    ["help.py", "data/support.json", "STORE_ADMIN.html", "LEARNING.html"],
    ["ตอบภายใน 24 ชม.", "ส่งต่อถูกแผนก", "ปิด ticket พร้อมบันทึก", "ผู้ใช้พอใจ"],
    ["Ticket log", "FAQ", "Escalation record"],
    ["Technical Writer", "Backend Developer"])

# --- Growth roles ---
add("Growth Manager / Growth Hacker", "Growth & Data Analytics",
    "วิ่งทดลองหาช่องทางโตอย่างรวดเร็วและวัดผลจริง",
    ["ออกแบบ A/B test", "สร้าง viral loop ในผลิตภัณฑ์", "วิเคราะห์ funnel", "ตัดสิ่งที่ไม่ทำงาน"],
    ["Growth mindset", "A/B testing", "Analytics", "Copywriting", "Product sense"],
    ["demand.py", "market.py", "marketing_promoter.py", "/api/store/stats"],
    ["มี experiment อย่างน้อย 1/สัปดาห์", "conversion เพิ่มขึ้นจริง", "cAC ลดลง", "record ทุกการทดลอง"],
    ["Experiment backlog", "A/B report", "Growth playbook"],
    ["Data Analyst", "Content Creator / Copywriter"], SRC_GROWTH)
add("Data Analyst", "Growth & Data Analytics",
    "ติดตั้ง tracking และอ่านพฤติกรรมผู้ใช้เพื่อบอกว่าควรปรับอะไร",
    ["กำหนด event/key metric", "วิเคราะห์ churn", "วัด ROI/channel", "ทำ dashboard"],
    ["SQL/JSON", "Statistics", "Tracking", "Visualization", "Experimentation"],
    ["store.py stats", "/api/store/stats", "LEARNING.html", "GOVERNANCE.html"],
    ["metric มีนิยามชัด", "dashboard อัพเดทจริง", "churn วัดได้", "ข้อสรุปมีข้อมูลรองรับ"],
    ["Metric dictionary", "Dashboard", "Insight report"],
    ["Growth Manager", "Product Owner"], SRC_GROWTH)
add("Paid Ads Specialist (Media Buyer)", "Performance Marketing",
    "หาลูกค้าใหม่ด้วยต้นทุนต่ำสุดบนแพลตฟอร์มที่เหมาะ",
    ["เลือก channel ตามงบ", "เขียน brief โฆษณา", "ปรับตาม CPA", "รายงานผล"],
    ["Media buying", "Budgeting", "Copy brief", "Analytics", "Compliance"],
    ["autopost.py", "marketing_promoter.py", "/api/store/stats"],
    ["CPA ตามเป้า", "ไม่ใช้เงินโดยไม่ได้รับอนุมัติ", "report ทุกแคมเปญ", "ห้ามเว็บพนัน/ผิดกฎหมาย"],
    ["Campaign brief", "Spend report", "Channel plan"],
    ["Content Creator / Copywriter", "Data Analyst"])
add("SEO & ASO Specialist", "Performance Marketing",
    "ดึงคนเข้าแบบไม่จ่ายโฆษณาในระยะยาว",
    ["วิจัย keyword", "ปรับ on-page/meta", "ทำความเร็วและโครงสร้างเว็บ", "เตรียม ASO เมื่อมีแอป"],
    ["SEO", "Keyword research", "Technical SEO", "ASO", "Analytics"],
    ["GitHub Pages", "tinyurl link", "index.html meta"],
    ["Traffic เพิ่มขึ้นจริง", "indexed page จริง", "ไม่มี death link", "ASO ยังไม่เริ่ม (ไม่มีแอป)"],
    ["Keyword map", "SEO audit", "Listing text"],
    ["Content Creator / Copywriter", "Frontend Developer"])
add("Content Creator / Copywriter", "Content & Creative",
    "เปลี่ยนเรื่อง IT ที่ซับซ้อนให้เข้าใจง่าย น่าเชื่อถือ",
    ["เขียนบทความ/คู่มือ", "เขียนสคริปต์วิดีโอ", "เขียนแคปชันโฆษณา", "ตรวจภาษาก่อนเผยแพร่"],
    ["Thai writing", "Editing", "Storytelling", "SEO copy", "Fact checking"],
    ["language.py", "council_review.py", "marketing_promoter.py", "book_design_system.py"],
    ["ข้อความไม่มีคำผิด", "อ่านจบและเข้าใจ", "มีแหล่งอ้างอิง", "ไม่กล่าวเกินจริง"],
    ["Article", "Script", "Caption set"],
    ["Graphic Designer & Video Editor", "Growth Manager"])
add("Graphic Designer & Video Editor", "Content & Creative",
    "สร้างภาพและวิดีโอสั้นที่ดูมืออาชีพและตรงแบรนด์",
    ["สร้างปก/แบนเนอร์ด้วย grid", "ตัดต่อวิดีโอจากภาพ+เสียง", "ใส่ subtitle", "วิจารณ์และปรับใหม่"],
    ["Typography", "Composition", "FFmpeg", "Color", "Critique loop"],
    ["image_studio.py", "creative_director.py", "media.py", "book_design_system.py"],
    ["ภาพผ่าน critique ≥80", "ไม่มีข้อความเลย", "อ่านได้ทุกขนาด", "Video composer ทำงานจริง"],
    ["Poster set", "MP4", "Design asset"],
    ["Content Creator / Copywriter", "UI Designer"])
add("CRM Specialist", "CRM & Community",
    "กระตุ้นคนที่สมัครแล้วแต่ยังไม่ใช้ ให้กลับมาใช้งานจริง",
    ["แบ่งกลุ่มผู้ใช้", "ตั้งข้อความอัตโนมัติ", "แจ้งฟีเจอร์ใหม่", "วัด reactivation"],
    ["Segmentation", "Automation", "Email/LINE", "Analytics", "Consent"],
    ["gmail_oauth.py", "users.py", "preferences.py", "STORE_ADMIN.html"],
    ["reactivation วัดได้", "ไม่ส่งโดยไม่ยินยอม", "มี unsubscribe", "logged ทุกครั้ง"],
    ["Campaign flow", "Segment list", "CRM report"],
    ["Community Manager", "Data Analyst"])
add("Community & Partnership Manager", "CRM & Community",
    "ดูแลชุมชนผู้ใช้และหาพาร์ทเนอร์มาช่วยรีวิว",
    ["ตอบคำถามในกลุ่ม", "สรรหา KOL/Influencer", "เจรจาร่วมงาน", "รายงานความรู้สึกผู้ใช้"],
    ["Community", "Negotiation", "Moderation", "Partnership", "Reporting"],
    ["autopost.py", "data/support.json", "GROWTH.html"],
    ["ตอบภายใน 24 ชม.", "มีพาร์ทเนอร์ที่ตรวจได้", "ไม่สร้างบัญชีแทนผู้ใช้", "feedback ส่งต่อทีม"],
    ["Community log", "Partner list", "Voice of user"],
    ["CRM Specialist", "Growth Manager"])


class RoleProfiles:
    def all(self):
        return {"ok": True, "count": len(P), "profiles": list(P.values()),
                "source_registry": sorted({u for urls in SOURCE_MAP.values() for u in urls})}

    def get(self, name=""):
        q = str(name or "").strip()
        if q in P:
            return {"ok": True, "profile": P[q]}
        low = q.lower()
        hits = [v for k, v in P.items() if low in k.lower() or low in v["group"].lower()]
        if len(hits) == 1:
            return {"ok": True, "profile": hits[0]}
        return {"ok": bool(hits), "matches": [x["role"] for x in hits],
                "profile": hits[0] if hits else None}

    def search(self, q=""):
        term = str(q or "").strip().lower()
        out = []
        for v in P.values():
            blob = json.dumps(v, ensure_ascii=False).lower()
            if not term or any(w in blob for w in term.split()):
                out.append({"role": v["role"], "group": v["group"],
                            "mission": v["mission"], "skills": v["skills"][:3],
                            "kpis": v["kpis"][:2]})
        return {"ok": True, "query": q, "count": len(out), "results": out}


RP = RoleProfiles()
