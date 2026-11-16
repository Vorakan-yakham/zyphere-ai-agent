import streamlit as st
import datetime, json, os

st.set_page_config(page_title="ZYP HERE - Local", page_icon="🧠")
st.title("🧠 ZYP HERE - AI ของ Vorakan")
st.caption("V3.3 Local Only | No-API 100% | รันบนคอมตัวเองที่ localhost:8501")

# ความจำ
def load_memory():
    try:
        if os.path.exists("memory/memory.json"):
            with open("memory/memory.json","r",encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {"owner":"Vorakan Yakham","project":"zyphere-ai-agent","goal":"เก่งกว่า Jarvis"}
memory=load_memory()

SYSTEM_PROMPT=f"""คุณคือ Zyphere AI Agent ระดับ Jarvis เจ้าของคือ Vorakan Yakham
กฎ: 1. คิดก่อนตอบเป็นขั้นตอน 2. ถ้าไม่รู้บอกว่าไม่รู้ อย่าเดา 3. ตอบภาษาไทย ตรงๆ ลึกๆ
ความจำ: {memory} วันนี้คือ {datetime.date.today()}"""

if "messages" not in st.session_state:
    st.session_state.messages=[{"role":"system","content":SYSTEM_PROMPT}]

# เช็ค Ollama แบบถูกต้อง
def check_ollama():
    try:
        import ollama
        ollama.list()
        return True, ""
    except Exception as e:
        return False, str(e)

HAS_OLLAMA, ERR = check_ollama()
if HAS_OLLAMA:
    st.success("✅ ต่อ Ollama ได้แล้ว - ฉลาดเต็มที่ ไม่ใช้ API")
else:
    st.error("❌ ยังต่อ Ollama ไม่ได้ - เปิด CMD อีกหน้าต่างแล้วพิมพ์ `ollama serve` ก่อน")
    st.code(f"Error: {ERR}", language="text")

for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt=st.chat_input("พิมพ์สั่ง Zyphere...")

if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        if not HAS_OLLAMA:
            st.markdown("ยังต่อสมองไม่ได้ครับ ทำตามนี้:\n1. เปิด CMD หน้าต่างใหม่\n2. พิมพ์ `ollama serve` แล้ว Enter\n3. เปิด CMD อีกหน้าต่าง พิมพ์ `ollama pull qwen3:14b`\n4. กลับมาหน้านี้กด Refresh")
        else:
            try:
                import ollama
                resp=ollama.chat(model="qwen3:14b", messages=st.session_state.messages, stream=True, options={"temperature":0.3})
                full=st.write_stream([c['message']['content'] for c in resp])
                st.session_state.messages.append({"role":"assistant","content":full})
            except Exception as e:
                st.markdown(f"Error: {e}")
                st.markdown("ลองพิมพ์ใน CMD: `ollama pull qwen3:14b`")

with st.expander("📖 วิธีเปิด Zyphere บนคอมตัวเอง"):
    st.markdown("""
    **ต้องเปิด 2 หน้าต่าง CMD พร้อมกัน:**
    - หน้าต่างที่ 1: `ollama serve`
    - หน้าต่างที่ 2: `streamlit run app.py`
    แล้วเปิดเว็บ http://localhost:8501
    """)
