# ตรวจสอบงานทุกด้านโดยทีม QA อิสระ

KEEP=17 · FIX=1 · UNKNOWN=0

| ด้าน | ผล | หลักฐาน | ผู้ตรวจ |
|---|---|---|---|
| backend /api/health | KEEP | HTTP 200 {"ok": true, "name": "zyphere", "version": 22, "features": ["search", "fetch", " | นักตรวจสอบระบบ |
| backend /api/brain/status | KEEP | HTTP 200 {"ok": true, "providers": ["groq", "openrouter", "gemini", "hf"], "enabled": tru | นักตรวจสอบระบบ |
| backend /api/council/autonomous/status | KEEP | HTTP 200 {"ok": true, "busy": false, "last": null, "departments": 6, "note": "แต่ละแผนกเร | นักตรวจสอบระบบ |
| backend /api/supervisors/status | KEEP | HTTP 200 {"ok": true, "count": 10, "rounds": 0, "last": [], "log": []} | นักตรวจสอบระบบ |
| backend /api/conversation/status | KEEP | HTTP 200 {"ok": true, "lessons": 13, "corrections": 13, "recent": [{"t": 1795006257, "use | นักตรวจสอบระบบ |
| backend /api/media/capabilities | KEEP | HTTP 200 {"ok": true, "capabilities": {"mp3_tts": true, "mp4_video": true, "metadata": tr | นักตรวจสอบระบบ |
| backend /api/auto-grow/status | KEEP | HTTP 200 {"ok": true, "gaps": [{"id": "storefront_theme", "severity": "high", "evidence": | นักตรวจสอบระบบ |
| TTS ตัวเลขไทย | KEEP | PASS Thai TTS numbers - 23 cardinal fixtures + context cases
 | นักตรวจสอบภาษา |
| UI สร้างภาพ/วิดีโอในแชท | KEEP | download button=True, old modal=False | นักตรวจสอบประสบการณ์ผู้ใช้ |
| วิดีโอ + เสียง | KEEP | bytes=5762531 audio=True | นักตรวจสอบสื่อ |
| grafpic lab own_image_lab.py | KEEP | found | นักตรวจสอบสื่อ |
| grafpic lab photo_enhancement.py | KEEP | found | นักตรวจสอบสื่อ |
| grafpic lab media_twin_track.py | KEEP | found | นักตรวจสอบสื่อ |
| หนังสือ + บรรณาธิการ | FIX | {"ok": false, "results": [{"book": "books/01_%E0%B8%9F%E0%B8%B4%E0%B8%AA%E0%B8%B4%E0%B8%81%E0%B8%AA%E0%B9%8C%E0%B8%84%E0%B8%A7%E0%B8%AD%E0%B8%99%E0%B8%95%E0%B8%B1%E0%B8%A1/book_v2. | นักตรวจสอบหนังสือ |
| มาตรฐานหนังสือ human_editor.py | KEEP | found | นักตรวจสอบหนังสือ |
| มาตรฐานหนังสือ content_visual.py | KEEP | found | นักตรวจสอบหนังสือ |
| ความปลอดภัย secret | KEEP | found | นักตรวจสอบความปลอดภัย |
| โปร่งใส (ไม่ claims ยอดขาย) | KEEP | method_transfer honesty rule | นักตรวจสอบความปลอดภัย |

หลักการ: ของที่ผ่านแล้วไม่ลบ — แก้เฉพาะที่หลักฐานบอกว่าพัง
