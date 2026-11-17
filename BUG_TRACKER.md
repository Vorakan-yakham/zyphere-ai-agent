# Bug Tracker — Zyphere

| ID | อาการ | สาเหตุจริง | สถานะ | บทเรียน |
|---|---|---|---|---|
| B01 | Enter ไม่ตอบ | dev agent ลบ `)`/`}` ของ finalPrompt → JS พังทั้งไฟล์ | Fixed | ต้องมี node --check ก่อน push |
| B02 | `WX is not defined` | ตัวแปรถูกลบแต่ยังใช้ | Fixed | token ต้องอยู่ใน test |
| B03 | เสียงรัว | streaming TTS ตัดบรรทัดสั้น ๆ ของเพลง | Fixed | noStreamTTS สำหรับเพลง/นิทาน |
| B04 | ทักทายแทนคำขอ | regex กว้างเกินไป | Fixed | isPureGreeting + selfTest |
| B05 | dev agent ทำลายโค้ด + หลาย process รันพร้อมกัน | ไม่มี syntax gate / single-instance lock | Fixed | ปิด default ด้วย `DEV_ENABLE=1`; ตรวจไม่มี process ค้าง |
| B06 | live knowledge=1 | ไม่มี remote KV/cron | Open | Milestone 2 |
| B07 | เสียงแย่งกันพูด / ฟังมั่ว | stopSpeak ไม่ล้างคิว, drain flag race, ไมค์ฟังขณะพูด | Fixed | ล้างคิว+token guard+abort mic; ทดสอบ q=0 หลัง stopSpeak |
| B08 | หมุนโลโก้นานก่อนตอบ | await knowledgeContext/localCommand ก่อน stream | Fixed | แยกคำสั่ง sync; ทั่วไป stream ทันที |

กฎ: ห้ามปิด bug โดยไม่มีหลักฐานทดสอบ
