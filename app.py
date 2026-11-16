import streamlit as st
import os
st.set_page_config(page_title="ZYP HERE", page_icon="◼", layout="centered")
st.markdown('''<style>
.stApp{background:#0a0a0a;color:#f5f5f5}
h1,h2,h3{color:#ffffff !important;letter-spacing:2px}
.stChatMessage{background:#111111 !important;border:1px solid #222222 !important;border-radius:16px}
.stButton>button{background:#ffffff !important;color:#000000 !important;border-radius:20px;font-weight:700}
.stTextInput input{background:#111111 !important;color:#fff !important;border:1px solid #333 !important}
.brain-card{background:#111111;border:1px solid #262626;border-radius:16px;padding:14px;margin-bottom:8px}
.badge{display:inline-block;background:#fff;color:#000;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700}
</style>''', unsafe_allow_html=True)
st.markdown('<div style="text-align:center"><div style="font-size:64px">◼</div><h1>ZYP HERE</h1><p style="color:#888">MONO TONE AI &bull; 4 BRAINS &bull; BY VORAKAN</p></div>', unsafe_allow_html=True)
def get_key(name):
    try:
        return st.secrets.get(name, "")
    except:
        return os.getenv(name, "")
keys = {"GROQ_API_KEY": get_key("GROQ_API_KEY"), "GEMINI_API_KEY": get_key("GEMINI_API_KEY"), "OPENROUTER_API_KEY": get_key("OPENROUTER_API_KEY"), "HF_TOKEN": get_key("HF_TOKEN")}
st.markdown("### ◉ STATUS")
for k,v in keys.items():
    icon = "●" if v else "○"
    label = {"GROQ_API_KEY":"01 / GROQ - FAST + DEEP","GEMINI_API_KEY":"02 / GEMINI - LONG DOCS","OPENROUTER_API_KEY":"03 / OPENROUTER - BIG MODEL","HF_TOKEN":"04 / HUGGING FACE - OPEN MODELS"}[k]
    st.markdown(f'<div class="brain-card">{icon} {label} &nbsp; <span class="badge">{"CONNECTED" if v else "NO KEY"}</span></div>', unsafe_allow_html=True)
st.markdown("### ◉ SELECT BRAIN")
brain = st.radio("Brain", ["01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG","05 HUGGING FACE"], horizontal=True, label_visibility="collapsed")
if "messages" not in st.session_state:
    st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
prompt = st.chat_input("Ask Zyphere ...")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            answer = ""
            if "GROQ" in brain:
                from groq import Groq
                if not keys["GROQ_API_KEY"]:
                    answer = "ยังไม่มี GROQ_API_KEY ใน Secrets ครับ ใส่แล้ว Reboot"
                else:
                    client = Groq(api_key=keys["GROQ_API_KEY"])
                    model = "llama-3.3-70b-versatile" if "FAST" in brain else "deepseek-r1-distill-llama-70b"
                    with st.spinner("Thinking ..."):
                        r = client.chat.completions.create(model=model, messages=[{"role":"system","content":"You are Zyphere AI of Vorakan Yakham. Answer in Thai, deep, clear, direct."}] + st.session_state.messages, temperature=0.7, max_tokens=2000)
                        answer = r.choices[0].message.content
            elif "GEMINI" in brain:
                import google.generativeai as genai
                if not keys["GEMINI_API_KEY"]:
                    answer = "ยังไม่มี GEMINI_API_KEY ใน Secrets ครับ"
                else:
                    genai.configure(api_key=keys["GEMINI_API_KEY"])
                    m = genai.GenerativeModel("gemini-2.5-flash")
                    with st.spinner("Thinking ..."):
                        r = m.generate_content(prompt)
                        answer = r.text
            elif "OPENROUTER" in brain:
                from openai import OpenAI
                if not keys["OPENROUTER_API_KEY"]:
                    answer = "ยังไม่มี OPENROUTER_API_KEY ใน Secrets ครับ"
                else:
                    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=keys["OPENROUTER_API_KEY"])
                    with st.spinner("Thinking ..."):
                        r = client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=st.session_state.messages)
                        answer = r.choices[0].message.content
            else:
                answer = "Hugging Face Brain พร้อมแล้ว ใส่ HF_TOKEN ใน Secrets แล้วเลือกโมเดลที่ต้องการได้เลย"
            st.markdown(answer)
            st.session_state.messages.append({"role":"assistant","content":answer})
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("เช็คว่าใส่ Key ใน Secrets ถูกต้องแล้ว Reboot")
st.markdown('<p style="text-align:center;color:#555;margin-top:30px">ZYP HERE V5 &bull; MONO TONE &bull; 4 BRAINS</p>', unsafe_allow_html=True)
