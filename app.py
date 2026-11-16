import streamlit as st, os, io, base64, asyncio
st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600&display=swap" rel="stylesheet">
<style>
.stApp, .stApp p, .stApp h1, .stApp span, .stApp div, .stApp input, .stApp button, .stApp label { font-family:'Prompt',sans-serif !important; }
[data-testid="stToolbar"]{display:none !important}
footer{display:none !important} [data-testid="collapsedControl"]{display:flex !important; visibility:visible !important; color:#1f1f1f !important}
    section[data-testid="stSidebar"]{padding-top:0 !important}
    section[data-testid="stSidebar"] > div{padding-top:0 !important}
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]{gap:0 !important}
    div[data-testid="stSidebar"] button > div{justify-content:flex-start !important; text-align:left !important}
    div[data-testid="stSidebar"] button:hover{background:#e8eaed !important}
     .block-container{padding-top:0 !important; padding-bottom:0 !important; max-width:100% !important} [data-testid="stVerticalBlock"]{gap:4px !important} .stMarkdown{margin:0 !important; padding:0 !important}
.stApp{background: radial-gradient(700px 420px at 62% 55%, #cfe0ff 0%, transparent 62%), #fff !important}
section[data-testid="stSidebar"]{background:#f0f4f9 !important; min-width:290px !important; display:block !important; visibility:visible !important; transform:none !important} section[data-testid="stSidebar"][aria-expanded="false"]{display:block !important; visibility:visible !important; margin-left:0 !important} [data-testid="collapsedControl"]{display:flex !important; visibility:visible !important} [data-testid="stSidebarCollapsedControl"]{display:flex !important}
.hero{font-size:28px;font-weight:400;text-align:center;margin-top:36px;margin-bottom:0;line-height:1.4;color:#1f1f1f}
.pill-center{max-width:768px;margin:12px auto 0;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,0.12);padding:8px 10px 8px 18px}
.pill-center div[data-testid="stTextInput"] > div > div > input{border:none !important;box-shadow:none !important;background:transparent !important;font-size:15px !important;height:44px !important}
.pill-center div[data-testid="stSelectbox"] > div > div{border:none !important;box-shadow:none !important;background:transparent !important;font-size:13px !important}
.pill-center button{border:none !important;background:#d3e3fd !important;box-shadow:none !important;border-radius:50% !important;width:38px !important;height:38px !important}

div[data-testid="stSidebar"] .stButton > button, div[data-testid="stSidebar"] button{
  border:none !important; border-width:0 !important; outline:none !important;
  background:transparent !important; background-color:transparent !important;
  box-shadow:none !important; -webkit-box-shadow:none !important;
  text-align:left !important; justify-content:flex-start !important; align-items:center !important;
  height:36px !important; padding:0 12px 0 12px !important; margin:0 !important;
  border-radius:999px !important; color:#1f1f1f !important; font-size:14px !important; font-weight:400 !important;
}
div[data-testid="stSidebar"] .stButton > button:hover{background:#e8eaed !important}
    div[data-testid="stSidebar"] .stButton:first-of-type > button{background:#e8eaed !important; font-weight:500 !important}
div[data-testid="stSidebar"] .stButton > button:active, div[data-testid="stSidebar"] .stButton > button:focus{border:none !important; box-shadow:none !important; outline:none !important}
div[data-testid="stSidebar"] .stButton{margin:0 !important; padding:0 !important; border:none !important}
border-radius:999px !important;font-size:14px !important}
div[data-testid="stSidebar"] button:hover{background:#e3e3e3 !important}
div[data-testid="stSidebar"] button[kind="primary"]{background:#f0f4f9 !important; color:#1f1f1f !important; font-weight:500 !important}
div[data-testid="stChatInput"]{max-width:768px !important; margin:0 auto !important}
div[data-testid="stChatInput"] > div{border-radius:999px !important; box-shadow:0 4px 24px rgba(0,0,0,0.12) !important; border:none !important}
.chat-ai{max-width:768px;margin:4px auto 2px;font-size:15px;line-height:1.55;padding:2px 0}
.topbar{display:flex;justify-content:flex-end;gap:6px;padding:8px 14px 0 0}
.top-gray{background:#eef2f7;border:none;border-radius:999px;padding:8px 14px;font-size:13px}
.top-blue{background:#d3e3fd;border:none;border-radius:999px;padding:8px 16px;font-size:13px;font-weight:500}
.login-box{background:#fff;border-radius:16px;padding:14px;margin:10px 0;box-shadow:0 2px 12px rgba(0,0,0,0.08)}
.user-card{display:flex;align-items:center;gap:10px;padding:10px 12px;background:transparent}
.avatar{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#4285f4,#9b72cb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600}
</style>
""", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
def make_male_audio(text):
    text=text[:900].strip()
    if not text: return None, "empty"
    try:
        import edge_tts
        async def _speak():
            comm=edge_tts.Communicate(text,"th-TH-NiwatNeural",rate="+0%",pitch="-4Hz")
            buf=io.BytesIO()
            async for chunk in comm.stream():
                if chunk["type"]=="audio": buf.write(chunk["data"])
            return buf.getvalue()
        loop=asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop); data=loop.run_until_complete(_speak())
        finally: loop.close()
        if data and len(data)>1000: return data, "Niwat - ผู้ชาย"
    except: pass
    try:
        from gtts import gTTS
        buf=io.BytesIO(); gTTS(text=text,lang="th",slow=False).write_to_fp(buf); return buf.getvalue(), "gTTS - สำรอง"
    except Exception as e: return None, str(e)
def show_audio(data):
    # Light player - no black bar, just small play button like Gemini
    b64=base64.b64encode(data).decode()
    import streamlit.components.v1 as components
    components.html(f'''
    <div style="display:flex;align-items:center;gap:10px;background:#f0f4f9;border-radius:999px;padding:8px 14px;max-width:680px">
      <audio id="zy" autoplay src="data:audio/mp3;base64,{b64}" style="display:none"></audio>
      <button onclick="document.getElementById('zy').play()" style="border:none;background:#fff;width:34px;height:34px;border-radius:50%;cursor:pointer;font-size:15px;box-shadow:0 1px 4px rgba(0,0,0,0.15)">&#9654;</button>
      <span style="font-family:Prompt;font-size:13px;color:#444">🔊 Zyphere กำลังพูด... กด ▶ ถ้าเสียงไม่ดัง</span>
      <button onclick="document.getElementById('zy').play()" style="border:none;background:transparent;cursor:pointer;font-size:13px;color:#1a73e8">ฟังอีกครั้ง</button>
    </div>
    ''', height=56)
if "messages" not in st.session_state: st.session_state.messages=[]
if "pending" not in st.session_state: st.session_state.pending=""
if "last_audio" not in st.session_state: st.session_state.last_audio=None
if "last_audio_label" not in st.session_state: st.session_state.last_audio_label=""
if "user_name" not in st.session_state: st.session_state.user_name=""
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "show_login" not in st.session_state: st.session_state.show_login=False
def go(p): st.session_state.pending=p; st.rerun()
def home(): st.session_state.messages=[]; st.session_state.pending=""; st.session_state.last_audio=None; st.rerun()
# ================= LEFT MENU =================
with st.sidebar:
    st.markdown('<div style="display:flex;align-items:center;gap:10px;padding:10px 12px 6px 12px;margin-top:0"><div style="width:24px;height:24px;border-radius:50%;background:conic-gradient(#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:17px">✦</div><b style="font-size:18px">Zyphere</b><span style="margin-left:auto;font-size:13px;color:#555">⌕</span></div>', unsafe_allow_html=True)
    if st.button("✎  แชทใหม่", use_container_width=True, key="gemini_newchat"): home()
    # Gemini has no 'แชท' header - direct list
    # removed duplicate new chat - already at top
    if st.button("⌕  ค้นหาแชท", use_container_width=True): go("สรุปให้หน่อยว่าฉันเคยคุยเรื่องอะไรบ้าง")
    if st.button("⊞  คลัง", use_container_width=True): go("เปิดคลังงานของฉัน สรุปงานที่เคยทำ")
    if st.button("◷  กำหนดเวลาแล้ว", use_container_width=True): go("ดูงานที่กำหนดเวลาไว้วันนี้ แล้วจัดลำดับให้หน่อย")
    if st.button("✎  ปรับแต่ง Zyphere", use_container_width=True): go("ปรับแต่งให้เธอพูดแบบเพื่อนร่วมงาน ตรงๆ อบอุ่น")
    if st.button("▷  วิดีโอ", use_container_width=True): go("ช่วยคิดสคริปต์วิดีโอสั้นๆ ให้หน่อย")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:14px 12px 6px">เครื่องมือ</div>', unsafe_allow_html=True)
    if st.button("🎙  พูดคุยด้วยเสียง", use_container_width=True): go("คุยกับฉันด้วยเสียง พูดตอบกลับเป็นภาษาไทย เสียงผู้ชาย")
    if st.button("✓  รายการงานของฉัน", use_container_width=True): go("ทำรายการงานวันนี้ให้หน่อย แบบเช็กลิสต์")
    if st.button("⌨  เขียนโค้ดให้หน่อย", use_container_width=True): go("เขียนโค้ดให้หน่อย อธิบายทีละบรรทัด")
    if st.button("▤  สรุปงาน", use_container_width=True): go("สรุปงานวันนี้ให้สั้นๆ เข้าใจง่าย")
    if st.button("✦  คิดไอเดีย", use_container_width=True): go("คิดไอเดียใหม่ๆ ให้หน่อย 5 ไอเดีย")
    if st.button("◉  อธิบายลึกๆ", use_container_width=True): go("อธิบายเรื่องนี้ให้ลึกๆ แบบเข้าใจง่าย")
    if st.button("📝  เขียนอีเมล / เอกสาร", use_container_width=True): go("ช่วยร่างอีเมลให้หน่อย สุภาพ เป็นทางการ")
    if st.button("🌐  แปลภาษา", use_container_width=True): go("ช่วยแปลภาษา ไทย-อังกฤษ ให้หน่อย")
    if st.button("🧮  คิดเลข / วางแผน", use_container_width=True): go("ช่วยคิดเลขและวางแผนให้หน่อย")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:14px 12px 6px">Notebook</div>', unsafe_allow_html=True)
    if st.button("＋  Notebook ใหม่", use_container_width=True): go("สร้าง Notebook ใหม่ สรุปเรื่องที่ฉันจะถาม")
    if st.session_state.messages:
        st.markdown('<div style="font-size:12px;color:#5f6368;padding:14px 12px 6px">ประวัติ - บทความที่เคยสนทนา</div>', unsafe_allow_html=True)
        seen=[]
        for m in st.session_state.messages:
            if m["role"]=="user" and m["content"] not in seen:
                seen.append(m["content"])
                st.button(f"💬  {m['content'][:28]}", use_container_width=True, key=f"hist_{len(seen)}")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:14px 12px 6px">BRAINS — Zyphere</div>', unsafe_allow_html=True)
    brain = st.selectbox("เลือกสมอง", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], key="brain_side")
    voice = st.checkbox("◉ ให้ Zyphere พูดตอบกลับ (เสียงผู้ชาย)", value=True)
    if st.session_state.last_audio:
        st.markdown(f"🔊 เสียงล่าสุดพร้อมแล้ว ({st.session_state.last_audio_label})")
    # ============ LOGIN - BOTTOM LEFT LIKE GEMINI ============
    st.markdown("---")
    st.markdown('<div style="font-size:12px;color:#5f6368;padding:4px 12px">บัญชีของฉัน</div>', unsafe_allow_html=True)
    if not st.session_state.logged_in:
        if st.button("👤  เข้าสู่ระบบ", use_container_width=True, type="primary"):
            st.session_state.show_login=True; st.rerun()
        if st.session_state.show_login:
            st.markdown('<div class="login-box"><b>👋 เข้าสู่ระบบ Zyphere</b><br><span style="font-size:13px;color:#666">ใส่ชื่อเล่นของคุณ Zyphere จะจำได้</span></div>', unsafe_allow_html=True)
            name = st.text_input("ชื่อเล่น", value="Whisp", placeholder="เช่น Whisp / Vorakan", key="login_name")
            if st.button("➜  เข้าสู่ระบบเลย", use_container_width=True, type="primary"):
                st.session_state.user_name = name.strip() or "Whisp"
                st.session_state.logged_in=True; st.session_state.show_login=False; st.rerun()
            if st.button("✕  ปิด", use_container_width=True):
                st.session_state.show_login=False; st.rerun()
            st.caption("ยังไม่ต้องใช้รหัสผ่าน — ระบบจะจำชื่อคุณในเครื่องนี้ ถ้าอยากได้ Google Login บอกผมได้")
        else:
            st.caption("ยังไม่เข้าสู่ระบบ — กด 👤 เข้าสู่ระบบ แล้ว Zyphere จะทักชื่อคุณ")
    else:
        initial = st.session_state.user_name[:1].upper() if st.session_state.user_name else "W"
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;padding:10px 12px;background:transparent"><div class="avatar">{initial}</div><div><b style="font-size:14px">{st.session_state.user_name}</b><br><span style="font-size:12px;color:#5f6368">เจ้าของ Zyphere</span></div><span style="margin-left:auto">⚙</span></div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("⚙  ตั้งค่า", use_container_width=True): go("เปิดตั้งค่า Zyphere")
        with c2:
            if st.button("↩  ออก", use_container_width=True):
                st.session_state.logged_in=False; st.session_state.user_name=""; st.session_state.messages=[]; st.rerun()
# banner removed - Gemini has no gap
st.markdown('<div class="topbar"><button class="top-gray">↓ ดาวน์โหลดแอป</button><button class="top-blue">✦ อัปเกรด</button><button class="top-gray">✦</button></div>', unsafe_allow_html=True)
has_chat = len(st.session_state.messages)>0 or bool(st.session_state.pending)
if not has_chat:
    greet = f"สวัสดี {st.session_state.user_name} เราจะเริ่มจากตรงไหนก่อนดี" if st.session_state.logged_in else "เราจะเริ่มจากตรงไหนก่อนดี"
    st.markdown(f'<div class="hero">{greet}</div>', unsafe_allow_html=True)
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
            st.markdown(f'<div style="max-width:768px;margin:12px auto 2px;display:flex;justify-content:flex-end"><span style="background:#f0f4f9;border-radius:999px;padding:10px 18px;font-size:15px">{m["content"]}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai">{m["content"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="max-width:768px;margin:0 auto 10px;font-size:14px;color:#888">👍 👎 ↻ ⧉ ⋯ &nbsp; 🔊</div>', unsafe_allow_html=True)
    if st.session_state.last_audio:
        pass  # no black bar, light player only
        show_audio(st.session_state.last_audio)
    inp2 = st.chat_input("ถาม Zyphere")
    prompt = st.session_state.pending or inp2 or ""
    if st.session_state.pending: st.session_state.pending=""
if prompt:
    if prompt not in [m["content"] for m in st.session_state.messages if m["role"]=="user"]:
        st.session_state.messages.append({"role":"user","content":prompt})
    st.markdown(f'<div style="max-width:768px;margin:12px auto 2px;display:flex;justify-content:flex-end"><span style="background:#f0f4f9;border-radius:999px;padding:10px 18px;font-size:15px">{prompt}</span></div>', unsafe_allow_html=True)
    with st.spinner("Zyphere กำลังคิด..."):
        try:
            uname = st.session_state.user_name or "Whisp"
            system=f"You are Zyphere, coworker friend of {uname}. Talk like a close male teammate in Thai, warm, direct, simple. Name is Zyphere. Call user {uname}."
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
                    st.session_state.last_audio=data; st.session_state.last_audio_label=label
                    st.markdown(f'<div style="max-width:680px;margin:6px auto;color:#2e7d32">🔊 เสียงพร้อมแล้ว ({label})</div>', unsafe_allow_html=True)
                    show_audio(data)
                else: st.warning(f"ทำเสียงไม่ได้: {label}")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")
