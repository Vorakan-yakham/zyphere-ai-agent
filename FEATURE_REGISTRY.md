# Feature Registry — Zyphere v22

| ระบบ | สถานะ | หมายเหตุ |
|---|---|---|
| แชท/streaming | ผ่าน | ตอบตรง ไม่ทักทายแทนคำขอ |
| เสียง TTS | ผ่าน | Niwat ชาย, streaming + single-shot สำหรับเพลง/นิทาน |
| ความจำถาวร | ผ่าน | memory.json + remote KV option |
| เรียนรู้เอง | ผ่าน | 128 หัวข้อ, frontier, watchlist |
| ภาษา | ผ่าน | 13 ภาษาทักทาย, แปล, เรียบเรียง |
| เพลง/นิทาน | ผ่าน | ใช้ AI ก่อน ถ้าไม่มีคีย์ fallback localSong/localStory |
| คำสั่งแชท | ผ่าน | `คำสั่ง` แสดงรายการทั้งหมด |
| เป้าหมาย/งาน | ผ่าน | goals + briefing |
| ไฟล์ยาว | ผ่าน | chunked map-reduce |
| วิดีโอ | ผ่าน | FFmpeg + ภาพฟรี |
| Backup/restore | ผ่าน | token + snapshot |
| dev agent | PAUSED | ต้องแก้ guard ให้แน่นก่อนเปิดใหม่ |

Features ใน /api/health: 19 รายการ
Live knowledge ขณะสำรวจ: 1 เรื่อง (ยังน้อยมาก)
