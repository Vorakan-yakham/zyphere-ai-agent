# Technical Decisions — Zyphere

| เรื่อง | ตัดสินใจ | เหตุผล |
|---|---|---|
| backend | http.server แทน flask | ทำงานได้แล้ว อย่าเปลี่ยนของที่ไม่พัง |
| frontend | SPA ไฟล์เดียว | deploy ง่ายบน GitHub Pages |
| เสียง | edge-tts ฝั่ง server | ไม่ต้องคีย์, เสียงชาย Niwat |
| ข้อมูล | JSON + remote KV | ถาวรข้าม restart |
| dev agent | PAUSED | เคยทำลาย working code หลายครั้ง |
| syntax gate | node --check | จับ JS พังก่อน push |
| ขอบเขตการแก้ | baseline + reapply | ปลอดภัยกว่าแก้รายจุดแบบสุ่ม |

หลักการ: ถ้าไม่มีหลักฐานว่าดีขึ้นจริง → ไม่ปล่อย commit
