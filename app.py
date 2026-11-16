import streamlit as st
import datetime, json, os

st.set_page_config(page_title="ZYP HERE", page_icon="🧠")
st.title("🧠 ZYP HERE - AI ของ Vorakan")
st.caption("V3.2 | แก้ Connection refused บน Streamlit Cloud")

# ---------- 1. Memory ----------
def load_memory():
    try:
        if os.path.exists("memory/memory.json"):
            with open("memory/memory.json","r",encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {"owner":"Vorakan Yakham","project":"zyphere-ai-agent","goal":"สร้าง AI ให้เก่งกว่า Jarvis","facts":[]}
memory = load_memory()

SYSTEM_PROMPT = f"""คุณคือ Zyphere AI Agent ระดับ Jarvis เจ้าของคือ Vorakan Yakham
กฎ: 1. คิดก่อนตอบเป็นขั้นตอน 2. ถ้าไม่รู้อย่าเดา 3. ตอบภาษาไทย ตรงๆ ลึกๆ
ความจำ: {memory} วันนี้คือ {datetime.date.today()}"""

if "messages" not in st.session_state:
    st.session_state.messages=[{"role":"system","content":SYSTEM_PROMPT}]

# ---------- 2. เช็คสมองแบบถูกต้อง: ต้องต่อเซิร์ฟเวอร์ได้จริง ----------
def check_ollama():
    try:
        import ollama
        ollama.list()  # ถ้าบรรทัดนี้พัง = เซิร์ฟเวอร์ไม่เปิด
        return True
    except Exception as e:
        return False

def check_groq():
    # ใช้ Groq ฟรีบน Cloud ถ้าใส่ API Key ไว้ใน Secrets
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        return bool(key)
    except:
        return False

HAS_OLLAMA = check_ollama()
HAS_GROQ = check_groq()

if HAS_OLLAMA:
    st.success("✅ โหมด Local: ต่อ Ollama บนเครื่องคุณแล้ว - ฉลาดเต็มที่")
elif HAS_GROQ:
    st.success("✅ โหมด Cloud: ต่อ Groq ฟรีแล้ว - ฉลาดเหมือนบนเครื่อง")
else:
    st.warning("⚠️ โหมด Demo บน Cloud: ยังไม่มีสมอง - ใส่ GROQ_API_KEY ใน Secrets เพื่อให้ฉลาดบนเว็บได้เลย วิธีอยู่ข้างล่าง")

# ---------- 3. แชท ----------
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("พิมพ์สั่ง Zyphere...")

if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        full = ""
        if HAS_OLLAMA:
            try:
                import ollama
                resp = ollama.chat(model="qwen3:14b", messages=st.session_state.messages, stream=True, options={"temperature":0.3})
                full = st.write_stream([c['message']['content'] for c in resp])
            except Exception as e:
                full = f"ต่อ Ollama ไม่ได้: {e}"
                st.markdown(full)
        elif HAS_GROQ:
            try:
                from groq import Groq
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # ใช้โมเดลฟรีที่ฉลาดสุดบน Groq ตอนนี้
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages,
                    temperature=0.3,
                    stream=True,
                )
                def gen():
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                full = st.write_stream(gen())
            except Exception as e:
                full = f"ต่อ Groq ไม่ได้: {e} - เช็ค GROQ_API_KEY ใน Secrets"
                st.markdown(full)
        else:
            full = f"""รับทราบครับ คุณสั่งว่า: **{prompt}**

ตอนนี้แอปอยู่บน Streamlit Cloud ซึ่งไม่มี Ollama ครับ เลยตอบแบบ Demo ให้ก่อน

**วิธีทำให้ฉลาดบนเว็บเลย (ฟรี 2 นาที):**
1. ไปที่ https://console.groq.com สมัครฟรี แล้วกด Create API Key
2. ใน Streamlit Cloud กด Manage app > Settings > Secrets ใส่แบบนี้:
```
GROQ_API_KEY = "gsk_xxxx ของคุณ"
```
3. กด Reboot แอป จะฉลาดทันทีด้วยโมเดล llama-3.3-70b ฟรี

หรือถ้าจะรันบนเครื่องตัวเองให้รัน `ollama serve` + `streamlit run app.py` ครับ"""
            st.markdown(full)
        st.session_state.messages.append({"role":"assistant","content":full})

with st.expander("📖 วิธีทำให้ Zyphere ฉลาดบนเว็บ (กดดู)"):
    st.markdown("""
    **ทางที่ 1 - บนเครื่อง (ฉลาดสุด ไม่เสียเงิน):**
    ```
    ollama pull qwen3:14b
    ollama serve
    streamlit run app.py
    ```
    **ทางที่ 2 - บน Cloud (ให้เพื่อนเล่นได้):**
    1. สมัคร https://console.groq.com ฟรี
    2. เอา API Key มาใส่ใน Secrets ของ Streamlit
    3. Reboot แอป
    """)
