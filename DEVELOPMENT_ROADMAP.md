# Development Roadmap — Zyphere

## Milestone 1 — Stabilize & Document (สถานะ: กำลังดำเนินการ)
เป้าหมาย: หยุด regression, จัดทำเอกสารจริง, ผ่าน test
- [x] สำรวจของจริง (git status, test, endpoints, live health)
- [x] คืน baseline ที่ผ่าน test
- [x] สร้าง 9 เอกสารกำกับโปรเจกต์
- [ ] ตรวจ dev agent ก่อนเปิดใช้งานอีกครั้ง
- [ ] เกณฑ์ผ่าน: test_zyphere.py + node --check + browser 3 คำสั่ง

## Milestone 2 — Live Knowledge Growth (ยังไม่เริ่ม)
- ตั้ง remote KV จริง
- ตั้ง cron /api/learn/tick
- เป้าหมาย: knowledge บน live > 10 เรื่องภายใน 24 ชม.

## Milestone 3 — Capability Leap (ยังไม่เริ่ม)
- Multi-model / RAG / tool orchestration
- เป้าหมาย: ตอบคำถามซับซ้อนได้ตรงขึ้น วัดจาก self-test + ชุดคำถามจริง

## Milestone 4 — JARVIS-like Autonomy (ยังไม่เริ่ม)
- ปฏิทิน/งาน/การแจ้งเตือนจริง
- ต้องมีบริการภายนอกและการยืนยันสิทธิ์
