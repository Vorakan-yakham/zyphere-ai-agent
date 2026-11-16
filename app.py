import streamlit as st, os
st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* { font-family:'Prompt',sans-serif !important; }
header[data-testid="stHeader"]{display:none !important}
footer{display:none !important}
div[data-testid="stToolbar"]{display:none !important}
.stApp{background: radial-gradient(700px 420px at 68% 52%, #cfe0ff 0%, transparent 62%), radial-gradient(600px 350px at 32% 58%, #e8f0ff 0%, transparent 60%), #fff !important}
section[data-testid="stSidebar"]{width:280px !important; min-width:280px !important; background:#f0f4f9 !important; padding:14px 10px !important}
section[data-testid="stSidebar"] > div{padding-top:0 !important}
.block-container{padding:0 20px !important; max-width:100% !important}
div[data-testid="stVerticalBlock"]{gap:0 !important}
/* sidebar item - Gemini exact */
.side-item{display:flex;align-items:center;gap:12px;height:38px;padding:0 12px;border-radius:999px;font-size:14px;color:#1f1f1f;cursor:pointer}
.side-item.active{background:#e3e3e3}
.side-item .ic{width:20px;text-align:center;font-size:18px;line-height:1;color:#444}
.side-label{font-size:12px;color:#5f6368;padding:18px 12px 6px 12px}
.hero{font-size:32px !important;font-weight:500;text-align:center;margin-top:120px !important;color:#1f1f1f;letter-spacing:-0.3px}
.sub{font-size:14px;color:#5f6368;text-align:center;margin-top:4px}
/* ONE PILL - all in one row */
.pill-wrap{max-width:680px;margin:28px auto 0;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,0.12);padding:6px 8px 6px 14px;display:flex;align-items:center;gap:6px}
.pill-wrap div[data-testid="stTextInput"]{flex:1}
.pill-wrap div[data-testid="stTextInput"] > div > div > input{background:transparent !important;border:none !important;box-shadow:none !important;height:44px !important;font-size:15px !important;padding:0 6px !important}
.pill-wrap div[data-testid="stSelectbox"]{width:150px !important}
.pill-wrap div[data-testid="stSelectbox"] > div > div{background:transparent !important;border:none !important;box-shadow:none !important;font-size:13px !important}
.pill-wrap button{border:none !important;background:transparent !important;box-shadow:none !important;color:#1f1f1f !important}
.plus{font-size:24px;line-height:1;color:#1f1f1f;width:32px;text-align:center}
.mic{font-size:18px;line-height:1;width:36px;height:36px;border-radius:50%;background:#f0f4f9;display:flex;align-items:center;justify-content:center}
.chip{background:#fff;border:1px solid #e5e5e5;border-radius:999px;padding:7px 14px;font-size:13px;color:#333;box-shadow:0 1px 6px rgba(0,0,0,0.04)}
.topbar{display:flex;justify-content:flex-end;gap:8px;padding:12px 16px 0 0}
.top-gray{background:#eef2f7;border:none;border-radius:999px;padding:8px 14px;font-size:13px}
.top-blue{background:#d3e3fd;border:none;border-radius:999px;padding:8px 16px;font-size:13px;font-weight:500}
</style>
""", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
# --- LEFT MENU like Gemini ---
with st.sidebar:
    st.markdown('<div style="display:flex;align-items:center;gap:8px;padding:2px 12px 14px"><span style="font-size:20px">✦</span><b style="font-size:16px">Zyphere</b><span style="margin-left:auto;font-size:16px;color:#555">⌕ &nbsp; ▭</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-item active"><span class="ic">✎</span>แชทใหม่</div><div class="side-item"><span class="ic">⊞</span>คลัง</div><div class="side-item"><span class="ic">◷</span>กำหนดเวลาแล้ว</div><div class="side-item"><span class="ic">✎</span>ปรับแต่ง</div><div class="side-item"><span class="ic">▷</span>วิดีโอ</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">Notebook</div><div class="side-item"><span class="ic">＋</span>Notebook ใหม่</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">BRAINS — Zyphere</div><div class="side-item"><span class="ic">●</span>Groq · เร็ว</div><div class="side-item"><span class="ic">●</span>Groq · คิดลึก</div><div class="side-item"><span class="ic">●</span>Gemini · สรุปยาว</div><div class="side-item"><span class="ic">●</span>OpenRouter · ตัวใหญ่</div>', unsafe_allow_html=True)
    st.markdown('<div style="position:fixed;bottom:16px;left:12px;width:250px;display:flex;justify-content:space-between;align-items:center;padding:0 12px"><span style="font-size:14px">○ Whisp</span><span style="font-size:16px">⚙</span></div>', unsafe_allow_html=True)
# --- TOP RIGHT ---
st.markdown('<div class="topbar"><button class="top-gray">↓ ดาวน์โหลดแอป</button><button class="top-blue">✦ อัปเกรด</button><button class="top-gray">✦</button></div>', unsafe_allow_html=True)
if "messages" not in st.session_state: st.session_state.messages=[]
if not st.session_state.messages:
    st.markdown('<div class="hero">เราจะเริ่มจากตรงไหนก่อนดี</div><div class="sub">Zyphere เพื่อนร่วมงานของคุณ</div>', unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
# --- SINGLE PILL ---
st.markdown('<div class="pill-wrap">', unsafe_allow_html=True)
with st.form("pill", clear_on_submit=True):
    c1,c2,c3,c4,c5 = st.columns([0.5, 5, 1.8, 0.6, 0.6])
    with c1: st.markdown('<div class="plus">＋</div>', unsafe_allow_html=True)
    with c2: prompt = st.text_input("q", placeholder="พิมพ์ @ เพื่อดูเครื่องมือเชื่อมต่อ ทักษะ และอื่นๆ", label_visibility="collapsed")
    with c3: brain = st.selectbox("m", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], label_visibility="collapsed")
    with c4: st.markdown('<div class="mic">🎙</div>', unsafe_allow_html=True)
    with c5: sent = st.form_submit_button("➤")
    voice = st.checkbox("◉ ให้ Zyphere พูดตอบกลับ", value=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div style="display:flex;gap:8px;justify-content:center;margin-top:14px"><span class="chip">⌨ เขียนโค้ด</span><span class="chip">▤ สรุปงาน</span><span class="chip">✦ คิดไอเดีย</span><span class="chip">◉ อธิบายลึกๆ</span></div>', unsafe_allow_html=True)
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            system="You are Zyphere, coworker friend of Vorakan. Talk like a close teammate in Thai, warm, direct, simple."
            answer=""
            if "GEMINI" in brain:
                import google.generativeai as genai
                genai.configure(api_key=get_key("GEMINI_API_KEY"))
                m=genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
                with st.spinner("Zyphere กำลังคิด..."):
                    answer=m.generate_content(prompt).text
            elif "OPENROUTER" in brain:
                from openai import OpenAI
                client=OpenAI(base_url="https://openrouter.ai/api/v1", api_key=get_key("OPENROUTER_API_KEY"))
                with st.spinner("Zyphere กำลังคิด..."):
                    answer=client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role":"system","content":system}]+st.session_state.messages).choices[0].message.content
            else:
                from groq import Groq
                client=Groq(api_key=get_key("GROQ_API_KEY"))
                for model in ["llama-3.1-8b-instant","qwen-qwq-32b","openai/gpt-oss-120b"]:
                    try:
                        with st.spinner("Zyphere กำลังคิด..."):
                            answer=client.chat.completions.create(model=model, messages=[{"role":"system","content":system}]+st.session_state.messages, temperature=0.8, max_tokens=2000).choices[0].message.content
                        break
                    except Exception as e: last=str(e); continue
                if not answer: answer="Groq ติด: "+last
            st.markdown(answer)
            st.session_state.messages.append({"role":"assistant","content":answer})
            if voice and answer:
                try:
                    from gtts import gTTS; import io
                    tts=gTTS(text=answer[:1000], lang="th"); buf=io.BytesIO(); tts.write_to_fp(buf); buf.seek(0); st.audio(buf, format="audio/mp3")
                except: pass
        except Exception as e: st.error(f"Error: {e}")
