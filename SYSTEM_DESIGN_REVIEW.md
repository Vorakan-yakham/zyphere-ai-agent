# SYSTEM DESIGN REVIEW — ก่อนพัฒนา

จัดทำโดยนักวิเคราะห์ระบบ Zyphere

divisions=12 engines=5

## คำแนะนำก่อนพัฒนาต่อ

- ใช้ Master Registry (governance/registry.json) เป็นแหล่งความจริงกลาง ห้าม duplicates ใน scholars.py/faculty_expansion.py อีกต่อไป
- ทุกโมดูลใหม่ต้องมี docstring + endpoint status + test ก่อน deploy
- แยก Retrieval / Memory / Model Training / Evaluation ออกจากกันเสมอ — การอัพเดทความรู้ใน KB ไม่ใช่การฝึกโมเดล
- งานสร้างสื่อหนัก (image diffusion/video/3D) ต้องส่งไป engine ภายนอก Render Free ไม่มี GPU และไม่มี persistent disk
- authz ต้องบังคับทีละกลุ่ม endpoint เริ่มจาก store/admin ก่อน
- CI ต้องรัน test_zyphere.py + systems_analyst.py ก่อน deploy

## เกณฑ์ผ่าน (gates)

- **ก่อนเพิ่มแผนก/ศูนย์ใหม่**: Master Registry + เหตุผล + ผู้รับผิดชอบ
- **ก่อนปล่อย feature ใหม่**: โค้ดจริง + endpoint + test + ผลลัพธ์ตรวจได้
- **ก่อนอ้างว่าทำงานอัตโนมัติ**: มี scheduler/job log ที่ตรวจได้จริง