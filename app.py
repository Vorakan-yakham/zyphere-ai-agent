import streamlit as st
import os
st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
* { font-family: 'Prompt',sans-serif !important; color:#1f1f1f; }
header[data-testid="stHeader"]{display:none !important}
footer{display:none !important}
.stApp{background: radial-gradient(800px 500px at 70% 55%, #d6e4ff 0%, transparent 60%), radial-gradient(700px 400px at 30% 60%, #e8f0ff 0%, transparent 60%), #ffffff !important}
[data-testid="stSidebar"]{background:#f0f4f9 !important}
.mono{color:#1f1f1f !important; filter:grayscale(1) !important}
.mono-icon{font-size:16px;color:#444 !important;line-height:1}
div[data-testid="stTextInput"] > div > div > input{
  background:#fff !important; border-radius:999px !important; height:60px !important;
  padding:0 20px !important; font-size:16px !important; border:none !important;
  box-shadow:0 6px 28px rgba(0,0,0,0.12) !important;
}
.chip{background:#fff;border:1px solid #e0e0e0;border-radius:999px;padding:8px 16px;font-size:13px;color:#333;box-shadow:0 2px 8px rgba(0,0,0,0.04)}
.top-btn{background:#eef2f7;border:none;border-radius:999px;padding:8px 14px;font-size:13px;color:#1f1f1f}
.top-blue{background:#d3e3fd;border:none;border-radius:999px;padding:8px 16px;font-weight:500;color:#1f1f1f}
</style>
""", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
# Sidebar - MONO TONE ONLY, no colored emoji
with st.sidebar:
    st.markdown("### <span class='mono'>✦ &nbsp; Zyphere</span>", unsafe_allow_html=True)
    st.markdown("<span class='mono-icon'>⌕</span> &nbsp; ค้นหา", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<span class='mono-icon'>✎</span> &nbsp; แชทใหม่", unsafe_allow_html=True)
    st.markdown("<span class='mono-icon'>⊞</span> &nbsp; คลัง", unsafe_allow_html=True)
    st.markdown("<span class='mono-icon'>◷</span> &nbsp; กำหนดเวลาแล้ว", unsafe_allow_html=True)
    st.markdown("<span class='mono-icon'>✎</span> &nbsp; ปรับแต่ง", unsafe_allow_html=True)
    st.markdown("<span class='mono-icon'>▷</span> &nbsp; วิดีโอ", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Notebook**")
    st.markdown("<span class='mono-icon'>＋</span> &nbsp; Notebook ใหม่", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**BRAINS**")
    st.markdown("● Groq · เร็ว")
    st.markdown("● Groq · คิดลึก")
    st.markdown("● Gemini · สรุปยาว")
    st.markdown("● OpenRouter · ตัวใหญ่")
    st.markdown("---")
    st.markdown("○ Whisp - Vorakan &nbsp; ⚙", unsafe_allow_html=True)
# Top right - mono
st.markdown('<div style="display:flex;justify-content:flex-end;gap:8px;margin:10px 18px 0 0"><button class="top-btn">↓ ดาวน์โหลดแอป</button><button class="top-blue">✦ อัปเกรด</button><button class="top-btn">✦</button></div>', unsafe_allow_html=True)
if "messages" not in st.session_state:
    st.session_state.messages = []
if not st.session_state.messages:
    st.markdown('<div style="text-align:center;margin-top:110px"><h1 style="font-size:42px;font-weight:500;">เราจะเริ่มจากตรงไหนก่อนดี</h1><p style="color:#5f6368">Zyphere เพื่อนร่วมงานของคุณ — พิมพ์ก็ได้ พูดก็ได้</p></div>', unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
# Single pill - MONO icons only
st.markdown('<div style="max-width:720px;margin:28px auto 0;">', unsafe_allow_html=True)
with st.form("pill", clear_on_submit=True):
    prompt = st.text_input("q", placeholder="ถาม Zyphere", label_visibility="collapsed")
    c1, c2, c3, c4 = st.columns([1, 3, 2, 1])
    with c1:
        st.markdown('<div style="text-align:center;font-size:22px;color:#444">＋</div>', unsafe_allow_html=True)
    with c2:
        brain = st.selectbox("m", ["Zyphere อัตโนมัติ", "01 GROQ - FAST", "02 GROQ - DEEP", "03 GEMINI - LONG", "04 OPENROUTER - BIG"], label_visibility="collapsed")
    with c3:
        voice = st.checkbox("◉ พูดตอบกลับ", value=True)
    with c4:
        sent = st.form_submit_button("◉ 🎙", help="พูด")
    submit = st.form_submit_button("➤ ส่ง", use_container_width=True)
st.markdown('<div style="display:flex;gap:8px;justify-content:center;margin-top:14px"><span class="chip">⌨ เขียนโค้ดให้หน่อย</span><span class="chip">▤ สรุปงานวันนี้</span><span class="chip">✦ คิดไอเดียให้หน่อย</span><span class="chip">◉ อธิบายลึกๆ</span></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
if prompt or sent:
    user_text = prompt if prompt else "สวัสดี Zyphere"
    if prompt:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.chat_message("assistant"):
            try:
                keys = {"GROQ_API_KEY": get_key("GROQ_API_KEY"), "GEMINI_API_KEY": get_key("GEMINI_API_KEY"), "OPENROUTER_API_KEY": get_key("OPENROUTER_API_KEY")}
                system = "You are Zyphere, coworker friend of Vorakan. Talk like a close teammate in Thai, warm, direct, simple."
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
