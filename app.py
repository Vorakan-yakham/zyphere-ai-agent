import streamlit as st
import os

st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide")

st.markdown("""
<style>
.stApp{background:#ffffff;color:#1f1f1f}
[data-testid="stSidebar"]{background:#f0f4f9 !important}
h1{color:#1f1f1f !important;font-weight:500}
.stChatMessage{background:#ffffff !important;border:none !important;box-shadow:none !important}
</style>
""", unsafe_allow_html=True)

def get_key(name):
    try:
        return st.secrets.get(name, "")
    except:
        return os.getenv(name, "")

with st.sidebar:
    st.markdown("### ✦ Zyphere")
    st.markdown("---")
    st.markdown("**＋ แชทใหม่**")
    st.markdown("คลัง")
    st.markdown("กำหนดเวลาแล้ว")
    st.markdown("ปรับแต่ง")
    st.markdown("วิดีโอ")
    st.markdown("---")
    st.markdown("Notebook")
    st.markdown("+ Notebook ใหม่")
    st.markdown("---")
    st.markdown("**BRAINS**")
    st.markdown("● Groq - Fast")
    st.markdown("● Groq - Deep")
    st.markdown("● Gemini - Long")
    st.markdown("● OpenRouter - Big")
    st.markdown("---")
    st.markdown("**Whisp - Vorakan**")

# Center like Gemini - no logo
st.markdown('<div style="text-align:center;margin-top:120px"><h1 style="font-size:44px;">เราจะเริ่มจากตรงไหนก่อนดี</h1></div>', unsafe_allow_html=True)

brain = st.selectbox("Model", ["01 GROQ - FAST", "02 GROQ - DEEP", "03 GEMINI - LONG", "04 OPENROUTER - BIG"], label_visibility="collapsed")
voice = st.toggle("🔊 ให้ Zyphere พูดตอบกลับ", value=False)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("พิมพ์ @ เพื่อดูเครื่องมือเชื่อมต่อ ทักษะ และอื่นๆ")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            keys = {
                "GROQ_API_KEY": get_key("GROQ_API_KEY"),
                "GEMINI_API_KEY": get_key("GEMINI_API_KEY"),
                "OPENROUTER_API_KEY": get_key("OPENROUTER_API_KEY"),
            }
            system = "You are Zyphere, coworker friend of Vorakan. Talk like a close teammate in Thai, warm, direct, simple, helpful."
            answer = ""
            if "GROQ" in brain:
                from groq import Groq
                client = Groq(api_key=keys["GROQ_API_KEY"])
                models_to_try = ["llama-3.1-8b-instant", "qwen-qwq-32b", "openai/gpt-oss-120b"]
                last_err = ""
                for model in models_to_try:
                    try:
                        with st.spinner("Zyphere กำลังคิด..."):
                            r = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system}] + st.session_state.messages, temperature=0.8, max_tokens=2000)
                            answer = r.choices[0].message.content
                        break
                    except Exception as e:
                        last_err = str(e)
                        continue
                if not answer:
                    answer = "Groq ลองทุกโมเดลแล้วติด: " + last_err + " ลองสลับไปใช้ GEMINI ดูก่อนนะ"
            elif "GEMINI" in brain:
                import google.generativeai as genai
                genai.configure(api_key=keys["GEMINI_API_KEY"])
                m = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
                with st.spinner("Zyphere กำลังคิด..."):
                    r = m.generate_content(prompt)
                    answer = r.text
            else:
                from openai import OpenAI
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=keys["OPENROUTER_API_KEY"])
                with st.spinner("Zyphere กำลังคิด..."):
                    r = client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role": "system", "content": system}] + st.session_state.messages)
                    answer = r.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            if voice and answer:
                try:
                    from gtts import gTTS
                    import io
                    tts = gTTS(text=answer[:1000], lang="th")
                    buf = io.BytesIO()
                    tts.write_to_fp(buf)
                    buf.seek(0)
                    st.audio(buf, format="audio/mp3")
                except:
                    pass
        except Exception as e:
            st.error(f"Error: {e}")
