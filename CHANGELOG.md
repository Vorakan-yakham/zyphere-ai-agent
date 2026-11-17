# CHANGELOG — วัดว่าดีขึ้นจริง

## รอบนี้ ( genuine improvement )

**ก่อน → หลัง (ตรวจได้)**
- พิมพ์ “เขียนเพลงให้หน่อยสิ” → ได้คำทักทายแทนเพลง → **หลัง: `isPureGreeting()=false` ส่งต่อ `writeSong()` จริง**
- พิมพ์ “สวัสดีครับ” → ได้คำทักทาย (ถูกต้อง) → **หลัง: ยังถูกต้อง และไม่กลืนคำขอที่ตามมา**
- เสียงเพลง → พูดรัวหลายก้อน → **หลัง: `noStreamTTS` พูดรอบเดียวจบ**
- ไม่มีคำสั่งช่วยจำ → **หลัง: พิมพ์ `คำสั่ง` ได้รายการคำสั่งทั้งหมด**
- ไม่มี self-test → **หลัง: `selfTest()` ตรวจ 7 กรณีคำสั่ง/คำทักทาย อัตโนมัติ**

**หลักฐาน**
- `python test_zyphere.py` → ALL REGRESSION TESTS PASSED
- `node --check` → JS SYNTAX OK
- ตรวจใน browser: `selfTest().ok === true`

## ซ่อม regression (ตรวจก่อนแก้)
**ก่อน → หลัง**
- กด Enter → ขึ้นบรรทัดใหม่แต่ไม่ตอบ → **หลัง: Enter ส่งข้อความแล้ว** (สาเหตุ: JS SyntaxError ทำให้ event listener ไม่ติดตั้ง)
- พิมพ์ “อ่านนิทานให้ฟังสักเรื่องสิ” → `WX is not defined` → **หลัง: มี WX แล้ว + คำสั่ง tellStory ทำงาน (รอคีย์ AI เท่านั้น)**
- ข้อความ error เพลงเป็น `??????` → **หลัง: “แต่งเพลงไม่ได้: …” อ่านรู้เรื่อง**

**การตรวจก่อนแก้:** ตรวจ `git diff 6cae4d6` พบ b45f39c ลบ `)`/`}` ของ finalPrompt → คืนจาก known-good ไม่แตะจุดอื่น

## Milestone 1 — Stabilize & Document
- สำรวจของจริงก่อนแตะไฟล์: git status, test, live health, 37 endpoints
- จัดทำเอกสาร 9 ไฟล์ตาม directive (แผน/สถาปัตยกรรม/roadmap/registry/progress/bug/decisions/test/changelog)
- คืน baseline ที่ผ่าน test แล้วใส่ WX + นิทานกลับ
- ตรวจแล้ว: test PASS, node --check OK, browser 3 คำสั่ง ไม่มี console error
- dev agent ยัง PAUSED (กันทำลายของทำงานอยู่)

## Milestone 2 — Offline story/song generation
ก่อน → หลัง
- พิมพ์ “เขียนเพลง…” โดยไม่มีคีย์ AI → error → **หลัง: ได้เพลงจริงจาก localSong()**
- พิมพ์ “อ่านนิทาน…” โดยไม่มีคีย์ AI → error → **หลัง: ได้นิทานจริงจาก localStory()**
- ทั้งสองยังพยายามใช้ AI ก่อน ถ้าไม่มีคีย์ค่อย fallback (backward compatible)

## ปิด Milestone 1 — Anti-Loop
ก่อน → หลัง
- ก่อน: dev agent หลาย process รันพร้อมกัน, push ซ้ำ, ทำลาย working code
- หลัง: `dev_agent.py` ปิด default (`DEV_ENABLE=1`), ตรวจไม่มี process ค้าง, test ผ่าน
- บทเรียน: กลยุทธ์ auto-patch ล้มเหลว → เปลี่ยนเป็น human-reviewed commit

## ซ่อม B07 — เสียงแย่งกันพูด
ก่อน → หลัง
- ก่อน: `stopSpeak()` ไม่ล้างคิว → ก้อนเก่าเล่นทับก้อนใหม่
- หลัง: ล้าง `ttsQ` + เพิ่ม token guard ใน `drainTTS` + abort ไมค์ตอนพูด
- ตรวจ: หลัง `stopSpeak()` → `ttsQ.length=0`, `ttsPlaying=false`, ไม่มี console error

## ซ่อมความหน่วง — ตอบช้า/หมุนโลโก้นาน
ก่อน → หลัง
- ก่อน: ทุกคำถามรอ `knowledgeContext()` + `localCommand()` เสร็จก่อนเริ่ม stream → หน่วง
- หลัง: คำสั่งที่รู้จักตรวจ sync ก่อน; คำถามทั่วไปเริ่ม stream ทันที ไม่รอ work เสริม
- ตรวจ: server ~300-500ms (เร็วอยู่), browser คำสั่ง “มีอะไรใหม่” ตอบใน ~700ms รวม render

หลักการ: ทุก commit ต้องระบุ “ก่อน/หลัง” แบบวัดได้ ไม่ใช่แค่ “เปลี่ยนแล้ว”
