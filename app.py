import streamlit as st
import datetime
import json
import os

st.set_page_config(page_title="ZYP HERE", page_icon="🧠")
st.title("🧠 ZYP HERE - AI ของ Vorakan")
st.caption("V3.1 | รันได้ทั้งบนเครื่อง + บน Streamlit Cloud")

# --- โหลดความจำแบบปลอดภัย ไม่พังบน Cloud ---
MEMORY_FILE = "memory/memory.json"
def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"owner": "Vorakan Yakham", "project": "zyphere-ai-agent", "goal": "สร้าง AI ให้เก่งกว่า Jarvis", "facts": []}

memory = load_memory()

SYSTEM_PROMPT = f"""
คุณคือ Zyphere AI Agent ระดับ Jarvis
เจ้าของคือ Vorakan Yakham
กฎ: 1. คิดก่อนตอบเสมอ คิดเป็นขั้นตอน 1,2,3
2. ถ้าไม่รู้ อย่าเดามั่ว ให้บอกว่าไม่รู้
3. ตอบภาษาไทย ตรงๆ ลึกๆ มีเหตุผล
4. ถ้าโดนสั่งงานยาวๆ ให้วางแผนก่อนทำ
ความจำ: {memory}
วันนี้คือ {datetime.date.today()}
"""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- เช็คว่ารันบนเครื่องตัวเองหรือบน Cloud ---
try:
    import ollama
    HAS_OLLAMA = True
except:
    HAS_OLLAMA = False

if HAS_OLLAMA:
    st.success("✅ โหมด Local: ต่อกับ Ollama บนเครื่องคุณแล้ว - ฉลาดเต็มที่")
else:
    st.warning("⚠️ โหมด Cloud Demo: บน Streamlit Cloud ไม่มี Ollama - จะตอบแบบ Demo ให้ก่อน ถ้าอยากฉลาดเต็มที่ ให้รันบนเครื่องตัวเองด้วยคำสั่ง streamlit run app.py")

for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("พิมพ์สั่ง Zyphere...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if HAS_OLLAMA:
            try:
                response = ollama.chat(model="qwen3:14b", messages=st.session_state.messages, stream=True, options={"temperature": 0.3})
                full = st.write_stream([c['message']['content'] for c in response])
            except Exception as e:
                full = f"ต่อ Ollama ไม่ได้ครับ ให้เช็คว่าได้รัน `ollama pull qwen3:14b` และ `ollama serve` แล้วหรือยัง\n\nError: {e}"
                st.markdown(full)
        else:
            # โหมด Demo บน Cloud ไม่พัง
            full = f"รับทราบครับ คุณสั่งว่า: **{prompt}**\n\nตอนนี้คุณกำลังรันบน Streamlit Cloud ซึ่งไม่มีสมอง Ollama ครับ ถ้าอยากให้ Zyphere ฉลาดเต็มที่ ให้โหลดไฟล์นี้ไปรันบนเครื่องตัวเองด้วย `streamlit run app.py` แล้วมันจะต่อกับโมเดล `qwen3:14b` ในเครื่องคุณทันทีครับ"
            st.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
