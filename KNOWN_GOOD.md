# Known-Good Baseline

Commit: `db2638a` — พื้นฐานที่ทดสอบผ่านและห้าม dev agent ทำลาย

## โซนห้ามแตะ (PROTECTED)
- `spkTok` / `curAud` / `function speak(` / `function sayOne(` — ระบบเสียง
- `const GREET` / `function greetLang(` / `function localAns(` — ทักทายหลายภาษา
- `function deepAnalyze(` / `function solveHard(` — การคิดวิเคราะห์
- `ttsNorm` / `ttsParts` / `mkAud` — เตรียมเสียง

## กฎเหล็ก
1. ถ้า patch แตะโซนข้างบน → ปัดทิ้งทันที
2. ถ้า verify ไม่เจอ token ข้างบน → rollback
3. ทุก commit ต้องผ่าน `python test_zyphere.py`

บทเรียน: โค้ดที่ทำงานอยู่แล้วคือสมบัตรมากกว่าความสวยงาม — อย่า rename ของที่ไม่พัง
