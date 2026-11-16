import streamlit as st
import os

st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&family=Kanit:wght@300;400;500&display=swap" rel="stylesheet">
<style>
* { font-family: 'Prompt','Kanit',sans-serif !important; }
header[data-testid="stHeader"]{display:none !important}
[data-testid="stToolbar"]{display:none !important}
footer{display:none !important}
.stApp{background: radial-gradient(800px 500px at 70% 55%, #cfe4ff 0%, transparent 60%), radial-gradient(700px 400px at 30% 60%, #e8f0ff 0%, transparent 60%), #ffffff !important; color:#1f1f1f}
[data-testid="stSidebar"]{background:#f0f4f9 !important; border-right:none !important; padding-top:12px}
[data-testid="stSidebar"] p{font-size:14px}
.main-center{max-width:720px;margin:0 auto}
.hero{font-size:38px;font-weight:500;text-align:center;margin-top:110px;color:#1f1f1f;letter-spacing:-0.5px}
.sub{color:#5f6368;text-align:center;font-size:15px;margin-top:6px}
/* Pill input */
div[data-testid="stTextInput"] > div > div > input{
  background:#fff !important; border-radius:999px !important; height:58px !important;
  padding-left:52px !important; padding-right:170px !important;
  font-size:16px !important; border:none !important; box-shadow:0 6px 28px rgba(0,0,0,0.12) !important;
}
div[data-testid="stTextInput"]{position:relative}
.topbar{display:flex;justify-content:flex-end;gap:8px;margin:10px 18px 0 0}
.pill-btn{background:#eef2f7;border:none;border-radius:999px;padding:8px 14px;font-size:13px}
.pill-blue{background:#d3e3fd;border:none;border-radius:999px;padding:8px 16px;font-weight:500}
.chip{background:#fff;border:1px solid #e8e8e8;border-radius:999px;padding:7px 14px;font-size:13px;box-shadow:0 2px 8px rgba(0,0,0,0.05)}
</style>
""", unsafe_allow_html=True)

def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")

with st.sidebar:
    st.markdown("### ✦ &nbsp; Zyphere")
    st.markdown("🔍 &nbsp; ค้นหา")
    st.markdown("---")
    st.markdown("**✎ &nbsp; แชทใหม่**")
    st.markdown("⊞ &nbsp; คลัง")
    st.markdown("◷ &nbsp; กำหนดเวลาแล้ว")
    st.markdown("✎ &nbsp; ปรับแต่ง")
    st.markdown("▶ &nbsp; วิดีโอ")
    st.markdown("---")
    st.markdown("**Notebook**")
    st.markdown("+ &nbsp; Notebook ใหม่")
    st.markdown("---")
    st.markdown("**BRAINS - Zyphere**")
    st.markdown("● Groq · เร็ว")
    st.markdown("● Groq · คิดลึก")
    st.markdown("● Gemini · สรุปยาว")
    st.markdown("● OpenRouter · ตัวใหญ่")
    st.markdown("---")
    st.markdown("👤 **Whisp - Vorakan** &nbsp; ⚙️")

# Top right like Gemini
st.markdown('<div class="topbar"><button class="pill-btn">⬇ ดาวน์โหลดแอป</button><button class="pill-blue">✦ อัปเกรด</button><button class="pill-btn">✦</button></div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show history if exists, else show hero
if not st.session_state.messages:
    st.markdown('<div class="main-center"><div class="hero">เราจะเริ่มจากตรงไหนก่อนดี</div><div class="sub">Zyphere เพื่อนร่วมงานของคุณ — พิมพ์ก็ได้ พูดก็ได้</div></div>', unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# Center pill input - like Gemini
st.markdown('<div class="main-center">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    with st.form("pill", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 6, 2])
        with c1:
            st.markdown('<div style="font-size:24px;text-align:center;margin-top:8px">＋</div>', unsafe_allow_html=True)
        with c2:
            prompt = st.text_input("q", placeholder="ถาม Zyphere", label_visibility="collapsed")
        with c3:
            brain = st.selectbox("m", ["Zyphere อัตโนมัติ", "01 GROQ - FAST", "02 GROQ - DEEP", "03 GEMINI - LONG", "04 OPENROUTER - BIG"], label_visibility="collapsed")
        c4, c5 = st.columns([6, 1])
        with c5:
            mic = st.form_submit_button("🎤")
        with c4:
            sent = st.form_submit_button("➤ ส่ง", use_container_width=True)
        voice = st.checkbox("🔊 ให้ Zyphere พูดตอบกลับ", value=True)
    # quick chips like Gemini suggestions
    st.markdown('<div style="display:flex;gap:8px;justify-content:center;margin-top:12px"><span class="chip">💻 เขียนโค้ดให้หน่อย</span><span class="chip">📄 สรุปงานวันนี้</span><span class="chip">🎨 คิดไอเดียให้หน่อย</span><span class="chip">🧠 อธิบายลึกๆ</span></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt or (mic):
    user_text = prompt if prompt else "สวัสดี Zyphere (สั่งด้วยเสียง)"
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        try:
            keys = {"GROQ_API_KEY": get_key("GROQ_API_KEY"), "GEMINI_API_KEY": get_key("GEMINI_API_KEY"), "OPENROUTER_API_KEY": get_key("OPENROUTER_API_KEY")}
            system = "You are Zyphere, coworker friend of Vorakan. Talk like a close teammate in Thai, warm, direct, simple, helpful."
            answer = ""
            if "GEMINI" in brain:
                import google.generativeai as genai
                genai.configure(api_key=keys["GEMINI_API_KEY"])
                m = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
                with st.spinner("Zyphere กำลังคิด..."):
                    r = m.generate_content(user_text)
                    answer = r.text
            elif "OPENROUTER" in brain:
                from openai import OpenAI
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=keys["OPENROUTER_API_KEY"])
                with st.spinner("Zyphere กำลังคิด..."):
                    r = client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role": "system", "content": system}] + st.session_state.messages)
                    answer = r.choices[0].message.content
            else:
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
                    answer = "Groq ลองทุกโมเดลแล้วติด: " + last_err
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
