import streamlit as st, os, io, base64, asyncio
st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600&display=swap" rel="stylesheet">
<style>
.stApp, .stApp p, .stApp h1, .stApp span, .stApp div, .stApp input, .stApp button, .stApp label { font-family:'Prompt',sans-serif !important; }
[data-testid="stToolbar"]{display:none !important}
footer{display:none !important}
.stApp{background: radial-gradient(700px 420px at 62% 55%, #cfe0ff 0%, transparent 62%), #fff !important}
section[data-testid="stSidebar"]{background:#f0f4f9 !important; min-width:280px !important}
.hero{font-size:32px;font-weight:500;text-align:center;margin-top:110px}
.pill-center{max-width:680px;margin:24px auto 0;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,0.12);padding:8px 10px 8px 18px}
.pill-center div[data-testid="stTextInput"] > div > div > input{border:none !important;box-shadow:none !important;background:transparent !important;font-size:15px !important;height:44px !important}
.pill-center div[data-testid="stSelectbox"] > div > div{border:none !important;box-shadow:none !important;background:transparent !important;font-size:13px !important}
.pill-center button{border:none !important;background:#d3e3fd !important;box-shadow:none !important;border-radius:50% !important;width:38px !important;height:38px !important}
div[data-testid="stSidebar"] button{border:none !important;background:transparent !important;box-shadow:none !important;text-align:left !important;height:38px !important;border-radius:999px !important;font-size:14px !important}
div[data-testid="stSidebar"] button:hover{background:#e3e3e3 !important}
div[data-testid="stChatInput"]{max-width:680px !important; margin:0 auto !important}
div[data-testid="stChatInput"] > div{border-radius:999px !important; box-shadow:0 4px 24px rgba(0,0,0,0.12) !important; border:none !important}
.chat-ai{max-width:680px;margin:14px auto;font-size:15px;line-height:1.7}
.topbar{display:flex;justify-content:flex-end;gap:8px;padding:12px 18px 0 0}
.top-gray{background:#eef2f7;border:none;border-radius:999px;padding:8px 14px;font-size:13px}
.top-blue{background:#d3e3fd;border:none;border-radius:999px;padding:8px 16px;font-size:13px;font-weight:500}
</style>
""", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
# ---------- MALE VOICE - fixed, no asyncio.run crash ----------
def make_male_audio(text):
    text = text[:900].strip()
    if not text: return None, "empty"
    # Try 1: edge-tts male NiwatNeural with fresh loop
    try:
        import edge_tts
        async def _speak():
            comm = edge_tts.Communicate(text, "th-TH-NiwatNeural", rate="+0%", pitch="-4Hz")
            buf = io.BytesIO()
            async for chunk in comm.stream():
                if chunk["type"]=="audio": buf.write(chunk["data"])
            return buf.getvalue()
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(_speak())
        finally:
            loop.close()
        if data and len(data)>1000:
            return data, "Niwat - ผู้ชาย"
    except Exception as e:
        err1 = str(e)[:100]
    # Try 2: gTTS fallback (always works on Cloud)
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text, lang="th", slow=False).write_to_fp(buf)
        return buf.getvalue(), "gTTS - สำรอง"
    except Exception as e:
        return None, f"fail: {e}"
def show_audio_autoplay(data):
    b64 = base64.b64encode(data).decode()
    import streamlit.components.v1 as components
    components.html(f'<audio autoplay controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio><p style="font-family:Prompt;font-size:13px;color:#555">🔊 กำลังพูด... ถ้าไม่ได้ยิน กด Play ข้างบน</p>', height=70)
if "messages" not in st.session_state: st.session_state.messages=[]
if "pending" not in st.session_state: st.session_state.pending=""
if "last_audio" not in st.session_state: st.session_state.last_audio=None
if "last_audio_label" not in st.session_state: st.session_state.last_audio_label=""
def go(p): st.session_state.pending=p; st.rerun()
with st.sidebar:
    st.markdown('<div style="display:flex;align-items:center;gap:10px;padding:14px"><div style="width:32px;height:32px;border-radius:50%;background:conic-gradient(#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px">✦</div><b style="font-size:17px">Zyphere</b><span style="margin-left:auto;font-size:16px">⌕ &nbsp; ▭</span></div>', unsafe_allow_html=True)
    if st.button("✎  แชทใหม่", use_container_width=True):
        st.session_state.messages=[]; st.session_state.pending=""; st.session_state.last_audio=None; st.rerun()
    if st.button("⊞  คลัง", use_container_width=True): go("เปิดคลังงานของฉัน")
    if st.button("◷  กำหนดเวลาแล้ว", use_container_width=True): go("ดูงานที่กำหนดเวลาไว้วันนี้")
    if st.button("✎  ปรับแต่ง", use_container_width=True): go("ปรับแต่งให้เธอพูดแบบเพื่อนร่วมงาน")
    if st.button("▷  วิดีโอ", use_container_width=True): go("ช่วยคิดสคริปต์วิดีโอสั้นๆ")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:18px 12px 6px">Notebook</div>', unsafe_allow_html=True)
    if st.button("＋  Notebook ใหม่", use_container_width=True): go("สร้าง Notebook ใหม่")
    if st.session_state.messages:
        st.markdown('<div style="font-size:12px;color:#5f6368;padding:18px 12px 6px">ทั้งหมด</div>', unsafe_allow_html=True)
        seen=[]
        for m in st.session_state.messages:
            if m["role"]=="user" and m["content"] not in seen:
                seen.append(m["content"])
                st.button(f"💬  {m['content'][:28]}", use_container_width=True, key=f"hist_{len(seen)}")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:18px 12px 6px">BRAINS — Zyphere</div>', unsafe_allow_html=True)
    brain = st.selectbox("เลือกสมอง", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], key="brain_side")
    voice = st.checkbox("◉ ให้ Zyphere พูดตอบกลับ (เสียงผู้ชาย)", value=True)
    st.caption("ถ้าเสียงไม่ดัง ให้กดปุ่ม 🔊 ฟังอีกครั้ง ข้างล่างคำตอบ")
    # Replay button in sidebar - always visible
    if st.session_state.last_audio:
        st.markdown("---")
        st.markdown("**🔊 เสียงล่าสุด**")
        st.audio(st.session_state.last_audio, format="audio/mp3")
        st.caption(f"เสียง: {st.session_state.last_audio_label}")
    st.markdown('<div style="padding:14px 12px;font-size:14px">○ Whisp &nbsp; ⚙</div>', unsafe_allow_html=True)
st.markdown('<div class="topbar"><button class="top-gray">↓ ดาวน์โหลดแอป</button><button class="top-blue">✦ อัปเกรด</button><button class="top-gray">✦</button></div>', unsafe_allow_html=True)
has_chat = len(st.session_state.messages)>0 or bool(st.session_state.pending)
if not has_chat:
    st.markdown('<div class="hero">เราจะเริ่มจากตรงไหนก่อนดี</div>', unsafe_allow_html=True)
    st.markdown('<div class="pill-center">', unsafe_allow_html=True)
    with st.form("pill_center", clear_on_submit=True):
        c1,c2,c3,c4 = st.columns([0.4,4,1.6,0.5])
        with c1: st.markdown('<div style="font-size:24px;text-align:center;padding-top:6px">＋</div>', unsafe_allow_html=True)
        with c2: inp = st.text_input("q", placeholder="พิมพ์ @ เพื่อดูเครื่องมือเชื่อมต่อ ทักษะ และอื่นๆ", label_visibility="collapsed")
        with c3: brain_pill = st.selectbox("m", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], label_visibility="collapsed")
        with c4: sent = st.form_submit_button("↑")
    st.markdown('</div>', unsafe_allow_html=True)
    prompt = inp if sent else ""
    if brain_pill != "Zyphere อัตโนมัติ": brain = brain_pill
else:
    for m in st.session_state.messages:
        if m["role"]=="user":
            st.markdown(f'<div style="max-width:680px;margin:18px auto 6px;display:flex;justify-content:flex-end"><span style="background:#f0f4f9;border-radius:999px;padding:10px 18px;font-size:15px">{m["content"]}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai">{m["content"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="max-width:680px;margin:6px auto;font-size:16px;color:#888">👍 👎 ↻ ⧉ ⋯ &nbsp; 🔊</div>', unsafe_allow_html=True)
    # Show last audio player right under chat + replay button
    if st.session_state.last_audio:
        st.markdown('<div style="max-width:680px;margin:0 auto"><b>🔊 เสียง Zyphere (ผู้ชาย)</b></div>', unsafe_allow_html=True)
        show_audio_autoplay(st.session_state.last_audio)
        if st.button("🔊 ฟังอีกครั้ง", key="replay_main"):
            show_audio_autoplay(st.session_state.last_audio)
    inp2 = st.chat_input("ถาม Zyphere")
    prompt = st.session_state.pending or inp2 or ""
    if st.session_state.pending: st.session_state.pending=""
if prompt:
    if prompt not in [m["content"] for m in st.session_state.messages if m["role"]=="user"]:
        st.session_state.messages.append({"role":"user","content":prompt})
    st.markdown(f'<div style="max-width:680px;margin:18px auto 6px;display:flex;justify-content:flex-end"><span style="background:#f0f4f9;border-radius:999px;padding:10px 18px;font-size:15px">{prompt}</span></div>', unsafe_allow_html=True)
    with st.spinner("Zyphere กำลังคิด..."):
        try:
            system="You are Zyphere, coworker friend of Vorakan. Talk like a close male teammate in Thai, warm, direct, simple. Name is Zyphere."
            answer=""
            if "GEMINI" in brain:
                import google.generativeai as genai
                genai.configure(api_key=get_key("GEMINI_API_KEY"))
                m=genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
                answer=m.generate_content(prompt).text
            elif "OPENROUTER" in brain:
                from openai import OpenAI
                client=OpenAI(base_url="https://openrouter.ai/api/v1", api_key=get_key("OPENROUTER_API_KEY"))
                answer=client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role":"system","content":system}]+st.session_state.messages).choices[0].message.content
            else:
                from groq import Groq
                client=Groq(api_key=get_key("GROQ_API_KEY"))
                for model in ["llama-3.1-8b-instant","qwen-qwq-32b","openai/gpt-oss-120b"]:
                    try:
                        answer=client.chat.completions.create(model=model, messages=[{"role":"system","content":system}]+st.session_state.messages, temperature=0.8, max_tokens=2000).choices[0].message.content
                        break
                    except Exception as e: last=str(e); continue
                if not answer: answer="Groq ติด: "+last
            st.markdown(f'<div class="chat-ai">{answer}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role":"assistant","content":answer})
            if voice:
                with st.spinner("🔊 Zyphere กำลังทำเสียงผู้ชาย..."):
                    data, label = make_male_audio(answer)
                if data:
                    st.session_state.last_audio = data
                    st.session_state.last_audio_label = label
                    st.markdown(f'<div style="max-width:680px;margin:6px auto;color:#2e7d32">🔊 เสียงพร้อมแล้ว ({label}) — กด Play ถ้าเบราว์เซอร์ไม่เล่นเอง</div>', unsafe_allow_html=True)
                    show_audio_autoplay(data)
                    st.audio(data, format="audio/mp3")
                else:
                    st.warning(f"ทำเสียงไม่ได้: {label} — ลองกด 🔊 ฟังอีกครั้ง หรือเช็คว่าเปิดเสียงไว้ไหม")
            else:
                st.caption("ปิดเสียงไว้ — ติ๊ก ◉ ให้ Zyphere พูดตอบกลับ ในเมนูซ้ายเพื่อเปิดเสียง")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")
