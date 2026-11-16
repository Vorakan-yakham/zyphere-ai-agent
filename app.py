import streamlit as st, os
st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* DO NOT use * selector - it breaks Streamlit icons. Only text elements get Prompt */
.stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span, .stApp div, .stApp input, .stApp textarea, .stApp button, .stApp label { font-family:'Prompt',sans-serif !important; }
/* Restore Material icon font for sidebar toggle */
[data-testid="collapsedControl"] span, [data-testid="stSidebarCollapsedControl"] span { font-family:'Material Symbols',sans-serif !important; }
[data-testid="stToolbar"]{display:none !important}
footer{display:none !important}
.stApp{background: radial-gradient(680px 420px at 62% 55%, #cfe0ff 0%, transparent 62%), #fff !important}
section[data-testid="stSidebar"]{background:#f0f4f9 !important; min-width:280px !important}
.hero{font-size:32px;font-weight:500;text-align:center;margin-top:100px}
.sub{font-size:14px;color:#5f6368;text-align:center;margin-top:4px}
div[data-testid="stSidebar"] button{border:none !important;background:transparent !important;box-shadow:none !important;text-align:left !important;height:38px !important;border-radius:999px !important;font-size:14px !important}
div[data-testid="stSidebar"] button:hover{background:#e3e3e3 !important}
/* CENTER PILL - one capsule, form in middle */
.pill-box{max-width:680px;margin:24px auto 0;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,0.12);padding:8px 10px 8px 18px}
.pill-box div[data-testid="stTextInput"] > div > div > input{border:none !important;box-shadow:none !important;background:transparent !important;font-size:15px !important;height:44px !important}
.pill-box div[data-testid="stSelectbox"] > div > div{border:none !important;box-shadow:none !important;background:transparent !important;font-size:13px !important}
.pill-box button{border:none !important;background:#f0f4f9 !important;box-shadow:none !important;border-radius:50% !important;width:38px !important;height:38px !important}
</style>
""", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
if "messages" not in st.session_state: st.session_state.messages=[]
if "pending" not in st.session_state: st.session_state.pending=""
def go(p): st.session_state.pending=p; st.rerun()
with st.sidebar:
    st.markdown('<div style="display:flex;align-items:center;gap:10px;padding:14px"><div style="width:38px;height:38px;border-radius:50%;background:conic-gradient(#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:19px">✦</div><div><div style="font-size:17px;font-weight:600">Zyphere</div><div style="font-size:11px;color:#5f6368">เพื่อนร่วมงานของคุณ</div></div></div>', unsafe_allow_html=True)
    if st.button("✎  แชทใหม่", use_container_width=True):
        st.session_state.messages=[]; st.session_state.pending=""; st.rerun()
    if st.button("⌕  ค้นหาแชท", use_container_width=True): go("สรุปให้หน่อยว่าฉันเคยคุยเรื่องอะไรบ้าง")
    if st.button("⊞  คลัง", use_container_width=True): go("เปิดคลังงานของฉัน สรุปงานที่เคยทำ")
    if st.button("◷  กำหนดเวลาแล้ว", use_container_width=True): go("ดูงานที่กำหนดเวลาไว้วันนี้ แล้วจัดลำดับให้หน่อย")
    if st.button("✎  ปรับแต่ง Zyphere", use_container_width=True): go("ปรับแต่งให้เธอพูดแบบเพื่อนร่วมงาน ตรงๆ อบอุ่น")
    if st.button("▷  วิดีโอ", use_container_width=True): go("ช่วยคิดสคริปต์วิดีโอสั้นๆ ให้หน่อย")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:18px 12px 6px">เครื่องมือที่ใช้บ่อย</div>', unsafe_allow_html=True)
    if st.button("🎙  พูดคุยด้วยเสียง", use_container_width=True): go("คุยกับฉันด้วยเสียง พูดตอบกลับเป็นภาษาไทย")
    if st.button("✓  รายการงานของฉัน", use_container_width=True): go("ทำรายการงานวันนี้ให้หน่อย แบบเช็กลิสต์")
    if st.button("⌨  เขียนโค้ดให้หน่อย", use_container_width=True): go("เขียนโค้ดให้หน่อย อธิบายทีละบรรทัด")
    if st.button("▤  สรุปงาน", use_container_width=True): go("สรุปงานวันนี้ให้สั้นๆ เข้าใจง่าย")
    if st.button("✦  คิดไอเดีย", use_container_width=True): go("คิดไอเดียใหม่ๆ ให้หน่อย 5 ไอเดีย")
    if st.button("◉  อธิบายลึกๆ", use_container_width=True): go("อธิบายเรื่องนี้ให้ลึกๆ แบบเข้าใจง่าย")
    if st.button("📝  เขียนอีเมล / เอกสาร", use_container_width=True): go("ช่วยร่างอีเมลให้หน่อย สุภาพ เป็นทางการ")
    if st.button("🌐  แปลภาษา", use_container_width=True): go("ช่วยแปลภาษา ไทย-อังกฤษ ให้หน่อย")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:18px 12px 6px">Notebook</div>', unsafe_allow_html=True)
    if st.button("＋  Notebook ใหม่", use_container_width=True): go("สร้าง Notebook ใหม่ สรุปเรื่องที่ฉันจะถาม")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:18px 12px 6px">BRAINS — Zyphere</div>', unsafe_allow_html=True)
    brain = st.selectbox("เลือกสมอง", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], key="brain_side")
    voice = st.checkbox("◉ ให้ Zyphere พูดตอบกลับ", value=True)
    st.markdown('<div style="padding:14px 12px;font-size:14px">○ Whisp &nbsp; ⚙</div>', unsafe_allow_html=True)
if not st.session_state.messages and not st.session_state.pending:
    st.markdown('<div class="hero">เราจะเริ่มจากตรงไหนก่อนดี</div><div class="sub">Zyphere เพื่อนร่วมงานของคุณ — พิมพ์แล้วกด Enter ได้เลย</div>', unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
# CENTER PILL - native form, Enter works, single capsule
st.markdown('<div class="pill-box">', unsafe_allow_html=True)
with st.form("pill", clear_on_submit=True):
    c1,c2,c3,c4 = st.columns([0.4,4,1.6,0.5])
    with c1: st.markdown('<div style="font-size:24px;text-align:center;padding-top:6px">＋</div>', unsafe_allow_html=True)
    with c2: user_input = st.text_input("q", placeholder="ถาม Zyphere", label_visibility="collapsed")
    with c3: brain_pill = st.selectbox("m", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], label_visibility="collapsed")
    with c4: sent = st.form_submit_button("↑")
st.markdown('</div>', unsafe_allow_html=True)
prompt = st.session_state.pending or (user_input if sent or user_input else "")
if st.session_state.pending: st.session_state.pending=""
if brain_pill != "Zyphere อัตโนมัติ": brain = brain_pill
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
                with st.spinner("Zyphere กำลังคิด..."): answer=m.generate_content(prompt).text
            elif "OPENROUTER" in brain:
                from openai import OpenAI
                client=OpenAI(base_url="https://openrouter.ai/api/v1", api_key=get_key("OPENROUTER_API_KEY"))
                with st.spinner("Zyphere กำลังคิด..."): answer=client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role":"system","content":system}]+st.session_state.messages).choices[0].message.content
            else:
                from groq import Groq
                client=Groq(api_key=get_key("GROQ_API_KEY"))
                for model in ["llama-3.1-8b-instant","qwen-qwq-32b","openai/gpt-oss-120b"]:
                    try:
                        with st.spinner("Zyphere กำลังคิด..."): answer=client.chat.completions.create(model=model, messages=[{"role":"system","content":system}]+st.session_state.messages, temperature=0.8, max_tokens=2000).choices[0].message.content
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
