# Zyphere IT Organization (Large-Scale Software Project)

Map บทบาทไอทีที่จำเป็นเข้ากับ 12 ฝ่ายเดิม — ไม่สร้างฝ่ายใหม่ซ้ำ

## 1. Management & Governance

| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |
|---|---|---|---|
| Project Manager / Scrum Master | 11 | chief.py, app.py /api/chief/run | ยังไม่มี timeline จริง/งบประมาณ |
| Product Owner | 12/07 | demand.py, market.py, master_registry.py | ยังไม่มี backlog ที่ผู้ใช้จัดลำดับได้ |

## 2. Business & Analysis

| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |
|---|---|---|---|
| Business Analyst | 07/01 | help.py, intent.py, concept.py | ยังไม่มี workshop กับผู้ใช้จริง |
| System Analyst | 02/10 | systems_analyst.py, governance/registry.json | มี static check แล้ว ต้องเพิ่ม design review ก่อนพัฒนา |

## 3. Design Team

| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |
|---|---|---|---|
| UX Designer | 07 | index.html, book_design_system.py | ยังไม่มี wireframe artifact แยก |
| UI Designer | 07 | book_design_system.py, image_studio.py | Design System ยังไม่รวม Web UI |

## 4. Development Team

| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |
|---|---|---|---|
| System Architect / Tech Lead | 02 | systems_analyst.py, app.py | มีแล้วบางส่วน |
| Backend Developer | 02 | app.py, store.py, five_engines.py | ยังมี endpoint ที่ authz ไม่บังคับ |
| Frontend Developer | 07 | index.html, STORE.html, GOVERNANCE.html | หน้าเดิมบางปุ่มยังเป็น fallback |
| Mobile App Developer | 02 | ยังไม่มี | ยังไม่มี — ต้องตัดสินใจว่าจำเป็นหรือไม่ |
| Database Administrator | 09/03 | app.py remote KV, github_backup.py | ไม่มี relational DB/migration |

## 5. QA & Operations

| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |
|---|---|---|---|
| QA / Tester | 10 | test_zyphere.py, systems_analyst.py | CI เพิ่งเพิ่ม test gate |
| DevOps Engineer | 11 | trigger2.py, restart_svc.py, .github/workflows/deploy.yml | ยังไม่มี structured logging/metrics |

## 6. Support & Documentation

| บทบาท | ฝ่าย | สิ่งที่มีจริง | ขาด |
|---|---|---|---|
| Technical Writer | 09 | governance/*.md, README.md | มีเอกสารแต่ยังไม่มี user guide รวม |
| IT Support / Customer Support | 11/12 | help.py, support.json | ยังไม่มี ticket workflow |
