# Project Master Plan — Zyphere

## วิสัยทัศน์
AI Assistant ที่สนทนาธรรมชาติ จำได้ เรียนรู้เอง ใช้เครื่องมือได้ และพัฒนาต่อได้โดยไม่ทำลายของเดิม

## เป้าหมายสูงสุด (วัดผลได้)
1. ตอบตรงคำถาม ไม่ทักทายแทนคำขอ
2. เสียง/ข้อความไปด้วยกัน ไม่รัว ไม่ซ้ำ
3. ทุก commit ต้องผ่าน test + node --check
4. ความรู้บน live ต้องเพิ่มขึ้นจริงเมื่อรัน cron/remote KV
5. ไม่มี regression ซ้ำจาก dev agent

## สถานะจริงตอนนี้
- Live: v22, 19 features, knowledge=1 เรื่อง
- โครงสร้าง: single-file backend (app.py) + SPA (index.html)
- ผ่าน `python test_zyphere.py`
- dev agent: PAUSED (เหตุผล: เคยเขียนทับของทำงานอยู่)
- Render free: หลับเมื่อไม่มีคนใช้; ยังไม่ตั้ง remote KV/cron

## หลักการทำงาน
- Incremental + Backward Compatibility
- ตรวจก่อนแก้ (git diff / baseline) เสมอ
- แยก Bug Fix / Improvement / New Feature / Optimization ให้ชัด
- ห้ามรายงาน success ก่อน through test
