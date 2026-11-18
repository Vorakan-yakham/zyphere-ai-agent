# Risk Register

| ความเสี่ยง | รายละเอียด | ระดับ | แนวทาง |
|---|---|---|---|
| Hardcoded credential | set_pw.py มีรหัสจริงฝังในโค้ด | critical | เปลี่ยนเป็น env var |
| Fake status | self-reported counters | high | แยก status จริงออกจากตัวเลข |
| No GPU | Render free ไม่มี GPU | high | ส่งไป engine ภายนอก |
| Fragmented source of truth | 46 คณะอยู่ 2 ไฟล์ | medium | ใช้ Master Registry เป็นกลาง |
| No CI gate | GitHub Actions ไม่รัน test | medium | เพิ่ม test job |
| Authz ไม่ครบ | endpoint ส่วนใหญ่เปิด | medium | บังคับทีละกลุ่ม |