# Existing Departments Audit

ตรวจจากโค้ดจริง 2026-11-18 — ไม่ได้คาดเดา

| แผนก | แหล่งข้อมูลจริง | หน้าที่ | ฝ่ายเป้าหมาย |
|---|---|---|---|
| นักวิเคราะห์ระบบ | systems_analyst.py | ตรวจสถาปัตยกรรม/secret/route | 02,10 |
| ฐานข้อมูล | app.py remote KV + github_backup.py | KV + GitHub persistence | 03,09 |
| โปรแกรมเมอร์ | app.py + test_zyphere.py | เขียนโค้ด commit/deploy | 02 |
| ฝ่ายวิชาการ | scholars.py (46), faculty_expansion.py | 46 คณะ 184 สาขา | 01,04 |
| ฝ่ายภาษา | language.py + co_learning | แก้คำ ตรวจข้อความ | 04 |
| ฝ่ายออกแบบผลิตภัณฑ์ | book_design_system.py | ปก layout grid | 07,02 |
| ฝ่ายผลิตหนังสือ | book_team.py..v5 | ผลิตเล่ม + QA | 07 |
| ฝ่ายการตลาด | marketing_promoter.py | PROMO.md โพสต์ | 07,12 |
| ฝ่ายทดสอบ | test_zyphere.py + systems_analyst.py | regression 11/11 | 10 |
| ฝ่ายปฏิบัติการ | Render + trigger2.py + restart | deploy/restart | 11 |
| ฝ่ายความปลอดภัย | safety.py, authz.py, audit.py | fail-closed gate | 10 |

## ข้อสังเกต

- role_registry.py มี 10 seed แต่ co_learning.py มี 11 — ต้องใช้ Master Registry เป็นแหล่งกลาง
- 46 คณะอยู่ใน scholars.py และ faculty_expansion.py ซ้ำกัน — ให้ Master Registry เป็นตัวกลาง
- ศูนย์ยุทธศาสตร์ 15 แห่งยังเป็น 'proposed' ทั้งหมด (เครื่องหมาย *)
- ไม่มีพนักงานมนุษย์ใน 11 แผนก — เป็น AI agent + owner (มนุษย์) คนเดียว