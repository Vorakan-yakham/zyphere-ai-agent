# 🧠 ZYP HERE V3.2

## แก้ Connection refused
V3.1 เช็คแค่ import ollama ได้ไหม เลยขึ้น Local หลอกๆ
V3.2 เช็คด้วย ollama.list() ต้องต่อเซิร์ฟเวอร์ได้จริงถึงจะขึ้น Local

## วิธีทำให้ฉลาดบน Cloud ฟรี
1. สมัคร https://console.groq.com ฟรี -> Create API Key
2. Streamlit Cloud > Manage app > Secrets ใส่:
GROQ_API_KEY = "gsk_xxx"
3. Reboot

## วิธีรันบนเครื่อง
ollama pull qwen3:14b
ollama serve
streamlit run app.py
