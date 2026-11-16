# ZYPHERE — Autonomous Executive OS (Local Edition)

AI ส่วนตัวที่รัน **ทั้งหมดในเครื่องคุณ** ไม่ใช้ API ของค่ายใด ไม่มีค่าใช้จ่ายต่อข้อความ ข้อมูลไม่ออกนอกเครื่อง
คุยด้วยคีย์บอร์ดหรือไมค์ ตอบกลับเป็นเสียงได้ รับรู้ภาพจากกล้องได้ คิดเองเป็นรอบ ๆ ภายใต้กฎความปลอดภัยเดิม

## ติดตั้ง
```bash
# 1) สมอง: ติดตั้ง Ollama จาก https://ollama.com แล้ว
ollama pull qwen2.5:7b-instruct          # แชท (RAM 8GB+) ; เครื่องแรงลอง qwen2.5:14b-instruct
ollama pull qwen2.5vl:7b                 # ไม่บังคับ: ให้ AI "มองภาพ" จากกล้อง/รูปที่แนบ

# 2) แอป
pip install -r requirements.txt
pip install -r requirements-voice.txt    # ไม่บังคับ: เสียงตอบแบบออฟไลน์ (ใหญ่ ~2GB)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # ตั้ง access_code
streamlit run app.py
```
ครั้งแรกที่ใช้ไมค์/เสียงตอบ จะดาวน์โหลดโมเดลเสียง 1 ครั้ง หลังจากนั้นใช้ออฟไลน์ได้

## สิ่งที่ใช้แทนของเดิม
| ส่วน | เดิม | ตอนนี้ |
|---|---|---|
| สมอง `core/llm.py` | Anthropic API | Ollama ในเครื่อง (อินเทอร์เฟซเดิม `LLM(key, model)`) |
| ไมค์ `core/voice.py` | Google web endpoint | faster-whisper ออฟไลน์ (`ZYPHERE_STT_MODEL=small\|medium\|large-v3`) |
| เสียงตอบ `core/tts.py` | edge-tts (ออนไลน์) | Meta MMS-TTS ไทย/อังกฤษ -> เสียงระบบ (pyttsx3) |
| เซ็นเซอร์ `core/sensors.py` | — | กล้อง (แสง/การเคลื่อนไหว/ใบหน้า/คน) + Arduino serial แบบอ่านอย่างเดียว |
| ตรวจทานตัวเอง | — | สวิตช์ **Self-check** ใน sidebar: ตอบ -> ตรวจ -> เพิ่มข้อแก้ไข |

## ตัวแปรสภาพแวดล้อม (ไม่บังคับ)
`ZYPHERE_MODEL` โมเดลแชทเริ่มต้น · `ZYPHERE_VISION_MODEL` โมเดลมองภาพ · `ZYPHERE_NUM_CTX` (ค่าเริ่ม 8192, เพิ่มถ้า RAM พอ)
`OLLAMA_HOST` · `ZYPHERE_TTS=system` · `ZYPHERE_SERIAL=COM3` (ต้อง `pip install pyserial`)

## ความปลอดภัย (คงเดิมทั้งหมด)
AI คิด จดบทเรียน และเขียน+ทดสอบทักษะใน sandbox ได้เอง ส่วนอื่นเป็นข้อเสนอที่รอ Approve · `/kill` หยุดทุกอย่างและอยู่ข้ามการรีสตาร์ต
กล้องตรวจ "มีใบหน้า" เท่านั้น ไม่ระบุตัวบุคคล · ภาพจากกล้องถูกแนบกับข้อความถัดไปครั้งเดียว

## ข้อจำกัดที่ต้องรู้
* โมเดลโอเพนซอร์สขนาดที่รันในเครื่องทั่วไป (7B–14B) **ไม่ฉลาดเท่าโมเดลคลาวด์ใหญ่ ๆ** ความแม่นขึ้นกับ RAM/GPU; Deep analysis + Self-check ช่วยได้แต่ช้าลง
* การ "เรียนรู้" = บทเรียน + ทักษะที่แอปเก็บไว้ น้ำหนักโมเดลไม่เปลี่ยน
* Streamlit ทำงานแบบรับคำขอ: กล้องคือ "ถ่ายภาพแล้วคุย" ไม่ใช่เฝ้าดูวิดีโอต่อเนื่อง (ทำได้ใน Phase ถัดไปด้วย streamlit-webrtc)
* เสียงไทยออฟไลน์ยังเป็นจุดอ่อนที่สุด: MMS ฟังเป็นหุ่นยนต์เล็กน้อย
* OpenCV 5.x ตัดตัวตรวจจับใบหน้าแบบเดิมออก จึงล็อกเป็น 4.x ใน requirements
