# System Architecture — Zyphere

## ส่วนประกอบ
- `app.py` (149 KB): ThreadingHTTPServer, 37 endpoints, การเรียนรู้, ความจำ, วิดีโอ, TTS, backup/restore
- `index.html` (141 KB): SPA, Agent loop, streaming TTS, คำสั่งในแชท, UI คลังความรู้
- `libs/`: jszip, mammoth, pdf, xlsx (อ่านไฟล์ฝั่ง browser)
- `fonts/`: Noto Sans Thai
- `data/`: memory, knowledge, learning, watch, goals, history, snapshots (สร้างตอน start)
- `dev_agent.py`: autonomous patcher (PAUSED)

## ข้อมูลถาวร
- Local JSON files
- Remote KV (Upstash) ถ้าตั้ง env
- Backup/restore + snapshots

## ความเสี่ยงที่รู้
- single-file ใหญ่ → แก้ผิดจุดหนึ่งกระทบทั้งระบบ (เคยเกิด)
- Render free ไม่เก็บข้อมูลถาวรถ้าไม่ตั้ง remote KV
- dev agent ต้องมี syntax gate เท่านั้นถึงเฉลิม

## เกณฑ์ยอมรับ
ทุกการเปลี่ยนต้องผ่าน `test_zyphere.py` + `node --check` ก่อน push
