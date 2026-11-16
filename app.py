import streamlit as st, os, base64
st.set_page_config(page_title="ZYP HERE", page_icon="◼", layout="wide")
# Load atom gif
logo_b64=""
try:
    with open("zyphere_atom.gif","rb") as f: logo_b64=base64.b64encode(f.read()).decode()
except: pass
st.markdown('''<style>
.stApp{background:linear-gradient(180deg,#ffffff 0%,#f8faff 40%,#eaf2ff 100%);color:#1f1f1f}
h1,h2,h3{color:#1f1f1f !important}
.sidebar .stApp{background:#ffffff}
.stChatMessage{background:#ffffff !important;border:1px solid #e8e8e8 !important;border-radius:20px;box-shadow:0 2px 12px rgba(0,0,0,0.04)}
input{border-radius:30px !important}
</style>''', unsafe_allow_html=True)
# Sidebar like Gemini
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center"><img src="data:image/gif;base64,{logo_b64}" width="90" style="border-radius:50%;background:#000;padding:5px;"><p style="font-weight:800;letter-spacing:2px;margin:5px 0 0;">ZYP HERE</p><p style="color:#888;font-size:12px">ATOM AI &bull; MONO TONE</p></div>', unsafe_allow_html=True)
    else:
        st.markdown("### ◼ ZYP HERE")
    st.markdown("---")
    st.markdown("**＋ แชทใหม่**")
    st.markdown("**▦ คลัง**")
    st.markdown("**◷ กำหนดเวลาแล้ว**")
    st.markdown("**✎ ปรับแต่ง**")
    st.markdown("**🎬 วิดีโอ**")
    st.markdown("---")
    st.markdown("**Notebook**")
    st.markdown("＋ Notebook ใหม่")
    st.markdown("---")
    st.markdown("**◉ BRAINS**")
    st.markdown("● 01 GROQ - FAST")
    st.markdown("● 02 GROQ - DEEP")
    st.markdown("● 03 GEMINI - LONG")
    st.markdown("● 04 OPENROUTER - BIG")
    st.markdown("● 05 HUGGING FACE")
    st.markdown("---")
    st.markdown("**Whisp** - Vorakan")
# Main - Gemini style center
st.markdown('<div style="text-align:center;margin-top:80px"><h1 style="font-size:42px;font-weight:500;">เราจะเริ่มจากตรงไหนก่อนดี</h1><p style="color:#666">Zyphere เพื่อนร่วมงานของคุณ - พิมพ์ก็ได้ พูดก็ได้</p></div>', unsafe_allow_html=True)
brain=st.selectbox("Model", ["01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], label_visibility="collapsed")
voice=st.toggle("🔊 ให้ Zyphere พูดตอบกลับ", value=True)
if "messages" not in st.session_state: st.session_state.messages=[]
# Show history
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])
prompt=st.chat_input("ถาม Zyphere ...  พิมพ์หรือพูดก็ได้")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            def get_key(n):
                try: return st.secrets.get(n,"")
                except: return os.getenv(n,"")
            keys={"GROQ_API_KEY":get_key("GROQ_API_KEY"),"GEMINI_API_KEY":get_key("GEMINI_API_KEY"),"OPENROUTER_API_KEY":get_key("OPENROUTER_API_KEY")}
            system="You are Zyphere, alive atom AI coworker friend of Vorakan. Talk like a close teammate in Thai, warm, direct, simple, helpful. Keep answers clear and friendly like Gemini."
            answer=""
            if "GROQ" in brain:
                from groq import Groq
                client=Groq(api_key=keys["GROQ_API_KEY"])
                pass # model chosen in loop
                models_to_try = ["llama-3.1-8b-instant", "qwen-qwq-32b", "openai/gpt-oss-120b"]
                    answer = ""
                    last_err = ""
                    for model in models_to_try:
                        try:
                            r=client.chat.completions.create(model=model, messages=[{"role":"system","content":system}]+st.session_state.messages, temperature=0.8, max_tokens=2000)
                            answer=r.choices[0].message.content
                            break
                        except Exception as e:
                            last_err=str(e)
                            continue
                    if not answer:
                        answer=f"Groq ลองทุกโมเดลแล้วติด: {last_err} ลองสลับไปใช้ GEMINI ดูก่อนนะ"
            elif "GEMINI" in brain:
                import google.generativeai as genai
                genai.configure(api_key=keys["GEMINI_API_KEY"])
                m=genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
                with st.spinner("Zyphere กำลังคิด..."):
                    r=m.generate_content(prompt); answer=r.text
            else:
                from openai import OpenAI
                client=OpenAI(base_url="https://openrouter.ai/api/v1", api_key=keys["OPENROUTER_API_KEY"])
                with st.spinner("Zyphere กำลังคิด..."):
                    r=client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role":"system","content":system}]+st.session_state.messages)
                    answer=r.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role":"assistant","content":answer})
            if voice and answer:
                try:
                    from gtts import gTTS
                    import io
                    tts=gTTS(text=answer[:1000], lang="th"); buf=io.BytesIO(); tts.write_to_fp(buf); buf.seek(0); st.audio(buf, format="audio/mp3")
                except: pass
        except Exception as e: st.error(f"Error: {e}")
st.markdown('<p style="text-align:center;color:#aaa;margin-top:60px;font-size:12px">ZYP HERE V8 &bull; GEMINI STYLE &bull; ATOM LOGO &bull; BY VORAKAN</p>', unsafe_allow_html=True)
