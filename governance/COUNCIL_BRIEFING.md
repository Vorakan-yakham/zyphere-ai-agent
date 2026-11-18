# การประชุมสภา Zyphere ตามความต้องการของเจ้าของ

ความต้องการของเจ้าของ (พูดแทนโดยผู้ช่วย):
- แก้หน้าร้าน/OUTDESIGN ให้สมบูรณ์และดึงดูดคนซื้อ
- หนังสือ: ตั้งราคาให้เหมาะสม, แก้ข้อความเก่า, เปลี่ยนปกใหม่ ไม่ใช้ภาพเก่าซ้ำ
- นักวิเคราะห์ใช้ความรู้เยอะ ๆ วางแผนอนาคต
- โปรแกรมเมอร์เขียนตามที่นักวิเคราะห์วางไว้
- database ถ้ามี ให้ทุกฝ่ายประสานกัน
- หาช่องทางทำเงินใหม่ ๆ ไม่ใช่รอ ebook อย่างเดียว (คนหลงเข้ามาซื้อไม่พอ)
- ห้ามให้เจ้าของต้องจ้ำจี้จ้ำชาย — ระบบต้องกระตุ้นตัวเอง

## คำตอบของแต่ละฝ่าย

### นักวิเคราะห์ความรู้ (local-evidence)

นักวิเคราะห์ความรู้: ใช้ข้อมูลจริง {"products": 46, "channels": 6, "qa_keep": 18, "qa_fix": 0, "world_topics": 0} → ต้องขยาย world topics และอ่าน BOOK_DESIGN_STANDARD ก่อนตัดสิน

### นักออกแบบกราฟิก (local-evidence)

นักออกแบบกราฟิก: ใช้ข้อมูลจริง {"products": 46, "channels": 6, "qa_keep": 18, "qa_fix": 0, "world_topics": 0} → ปกต้องสื่อเนื้อหา + typography ใหม่ ใช้ own_image_lab ไม่ใช้ภาพซ้ำ

### นักเศรษฐศาสตร์/ราคา (local-evidence)

นักเศรษฐศาสตร์/ราคา: ใช้ข้อมูลจริง {"products": 46, "channels": 6, "qa_keep": 18, "qa_fix": 0, "world_topics": 0} → ราคาจาก market_price + ความยาวจริง + เตรียม 6 ช่องทางฟรี

### โปรแกรมเมอร์ (local-evidence)

โปรแกรมเมอร์: ใช้ข้อมูลจริง {"products": 46, "channels": 6, "qa_keep": 18, "qa_fix": 0, "world_topics": 0} → เขียน STORE_V2.html, commerce.json, ปกใหม่ แล้ว commit อัตโนมัติ

### หัวหน้าฐานข้อมูล (local-evidence)

หัวหน้าฐานข้อมูล: ใช้ข้อมูลจริง {"products": 46, "channels": 6, "qa_keep": 18, "qa_fix": 0, "world_topics": 0} → เก็บ products/channels/qa/metrics ใน data/commerce.json ให้ทุกฝ่ายอ่าน

### QA (local-evidence)

QA: ใช้ข้อมูลจริง {"products": 46, "channels": 6, "qa_keep": 18, "qa_fix": 0, "world_topics": 0} → ตรวจ file จริง + ราคา + ภาษา + ไม่มีคำอ้างยอดขาย ไม่ผ่านให้ HOLD

## มติที่ต้องปฏิบัติ (work orders)

- สร้าง STORE_V2.html ใหม่: hero ชัด, การ์ดสินค้า, CTA, QR, ช่องทางรายได้ 6 ช่องทาง
- ตั้งราคาทุกเล่มด้วย market_price + ความยาวจริง เปลี่ยนสถานะเป็น review จนกว่า QA จะผ่าน
- ปกใหม่ต้องสร้างจากเนื้อหาจริง (motif ตามหัวข้อ) + typography ใหม่ ไม่ใช้ภาพเก่าซ้ำ
- เก็บ products/channels/qa/metrics ลง data/commerce.json เป็นแหล่งร่วมของทุกฝ่าย
- ระบบกระตุ้นตัวเองทุก 30 นาที: analyze → plan → code → QA → learn ไม่ต้องรอเจ้าของ

คำสั่งนี้ถูกส่งเข้า ALL_HANDS_ORDER.md และ autonomy workflow แล้ว
