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
| B09 | เสียง 2 คนแทรกกัน | `speak()` resolve ทันที → server+browser TTS เล่นพร้อมกัน; stream กับปกติคนละ token | Fixed | voiceOwner arbiter + รอ onended จริง; ทดสอบ utt=0 |
| B10 | เสียงช้ากว่าข้อความหลายวินาที | edge-tts ใช้ 700-980ms/ก้อน | Mitigated | prefetch ก้อนถัดไปล่วงหน้า; ถ้าต้องการ 0ms ใช้เสียงในเครื่อง |
| B11 | อ่านบทความมีช่วงเงียบ 5 วิ | speak() ไม่มี prefetch + ttsParts ตัดไม่ทำงาน → ก้อนยาว | Fixed | speak() ใช้ prefetch + ตัดตามคำ 380 ตัว/ก้อน; ทดสอบ parts=4 max=367 |
| B12 | วิดีโอสร้างไม่ได้ (ffmpeg failed) | dev agent ใส่ `return True` ทิ้งไว้ใน `_tts_save()` ก่อนโค้ดจริง → รายงานสำเร็จแต่ไม่สร้างไฟล์ mp3 → ffmpeg หาไฟล์ไม่เจอ | Fixed | ลบ `return True`; ทดสอบสร้าง MP4 สำเร็จ 11.84s 1280x720 H264+AAC |

กฎ: ห้ามปิด bug โดยไม่มีหลักฐานทดสอบ
