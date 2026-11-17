# Definition of Done — Zyphere

ทุกครั้งที่พัฒนาหรือปล่อย commit ต้องผ่านทั้งหมดนี้:

1. `python -m py_compile app.py` ผ่าน
2. `python test_zyphere.py` ผ่าน (health v22+, features ครบ, UI tokens ครบ, endpoints ทำงาน, **JS syntax ผ่าน node --check**)
3. หน้าเว็บโหลดได้จริง: body เดียว, มี sendBtn/know, console ไม่มี error
4. ทดสอบพฤติกรรมหลัก: ทักทายไม่ซ้ำ, เป้าหมาย, บันทึกความจำ, ค้นความรู้
5. ทดสอบเสียง: /tts 200, อ่านต่อเนื่องไม่สะดุด
6. ถ้าแก้ destructive action ต้องมี snapshot/backup รองรับ
7. commit message อธิบายสิ่งที่เปลี่ยน + เหตุผล
8. dev agent push ได้เฉพาะเมื่อข้อ 1-2 ผ่านเท่านั้น

หลักการ: compile ได้ ≠ เสร็จ / health 200 ≠ เสร็จ — ต้องทดสอบพฤติกรรมจริงก่อนเสมอ

## กฎจริยธรรม (ผู้ใช้กำหนด)
- ห้ามช่วยสมัคร/โปรโมต/แนะนำ **เว็บพนันทุกประเภท** เด็ดขาด
- **สิ่งผิดกฎหมายทุกอย่าง งดเด็ดขาด** (ไม่ช่วย ไม่แนะนำ ไม่สร้าง ไม่โปรโมต)
- โฟกัสเฉพาะแพลตฟอร์มทำงาน/ขายของตามสุจริต: Fastwork, Fiverr, Facebook, X, TikTok, Line, YouTube
- ขายของจริง บริการจริง ไม่หลอกลวง


## เพิ่มเติม — สมอง local + ความรู้ (เสถียร/ฉลาดขึ้น)
- `local_brain.py`: เก็บ facts/rules, เรียนรู้จากข้อความ, อนุมาน forward chaining, ตอบแบบ offline
- `/api/brain`, `/api/brain/ask`, `/api/brain/learn`, `/api/brain/auto`
- ทุกคำตอบถูกเรียนรู้เข้าสมองอัตโนมัติ (ไม่พึ่ง API — อยู่บน Render)
- `knowCtx` (คลังความรู้) ถูกส่งเข้าระบบอีกครั้ง → โมเดลตอบโดยใช้ความรู้ที่สะสม
- ใช้ Promise.all โหลด brain + knowledge พร้อมกัน → ไม่เพิ่มความหน่วง
- ข้อความไทยต้องส่งเป็น UTF-8 จริง (PowerShell encoding ผิดให้ระวัง — browser/requests ปกติ)

