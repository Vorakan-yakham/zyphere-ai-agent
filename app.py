import streamlit as st, os, io, base64, asyncio
st.set_page_config(page_title="Zyphere", page_icon="x", layout="wide", initial_sidebar_state="expanded")
params = st.query_params
nav = params.get("nav", "")
if "messages" not in st.session_state: st.session_state.messages=[]
if "pending" not in st.session_state: st.session_state.pending=""
if "last_audio" not in st.session_state: st.session_state.last_audio=None
if "user_name" not in st.session_state: st.session_state.user_name="Whisp"
NAV_PROMPTS = {
    "library": "เปิดคลังงานของฉัน สรุปงานที่เคยทำ",
    "scheduled": "ดูงานที่กำหนดเวลาไว้วันนี้ แล้วจัดลำดับให้หน่อย",
    "custom": "ปรับแต่งให้เธอพูดแบบเพื่อนร่วมงาน ตรงๆ อบอุ่น",
    "video": "ช่วยคิดสคริปต์วิดีโอสั้นๆ ให้หน่อย",
    "voice": "คุยกับฉันด้วยเสียง พูดตอบกลับเป็นภาษาไทย เสียงผู้ชาย",
    "todo": "ทำรายการงานวันนี้ให้หน่อย แบบเช็กลิสต์",
    "code": "เขียนโค้ดให้หน่อย อธิบายทีละบรรทัด",
    "summary": "สรุปงานวันนี้ให้สั้นๆ เข้าใจง่าย",
    "idea": "คิดไอเดียใหม่ๆ ให้หน่อย 5 ไอเดีย",
    "email": "ช่วยร่างอีเมลให้หน่อย สุภาพ เป็นทางการ",
    "translate": "ช่วยแปลภาษา ไทย-อังกฤษ ให้หน่อย",
    "math": "ช่วยคิดเลขและวางแผนให้หน่อย",
    "notebook": "สร้าง Notebook ใหม่ สรุปเรื่องที่ฉันจะถาม",
}
if nav in ("home","new"):
    st.session_state.messages=[]; st.session_state.pending=""; st.query_params.clear(); st.rerun()
if nav in NAV_PROMPTS:
    st.session_state.pending=NAV_PROMPTS[nav]; st.query_params.clear(); st.rerun()
st.markdown("<link href='https://fonts.googleapis.com/css2?family=Prompt:wght@400;500&display=swap' rel='stylesheet'><style>.stApp,.stApp p,.stApp div,.stApp span,.stApp input,.stApp button,.stApp label{font-family:'Prompt',sans-serif !important} [data-testid='stToolbar']{display:none !important} footer{display:none !important} .stApp{background:#fff !important} section[data-testid='stSidebar']{background:#f0f4f9 !important;width:280px !important;min-width:280px !important;padding-top:0 !important} section[data-testid='stSidebar']>div{padding-top:0 !important} div[data-testid='stSidebarContent']{padding:0 !important} .gem-sidebar{padding:0 8px} .gem-top{display:flex;align-items:center;gap:8px;padding:12px 8px 10px 8px} .gem-logo{width:26px;height:26px;border-radius:50%;background:conic-gradient(#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:14px} .gem-title{font-size:17px;font-weight:500} .gem-top-right{margin-left:auto;display:flex;gap:14px;color:#444} .gem-item{display:flex;align-items:center;gap:14px;padding:0 12px;height:40px;border-radius:999px;text-decoration:none !important;color:#1f1f1f !important;font-size:14px} .gem-item:hover{background:#e8eaed !important} .gem-item.active{background:#e8eaed !important;font-weight:500} .gem-item .ic{width:20px;text-align:center} .gem-label{font-size:12px;color:#5f6368;padding:18px 12px 6px} .gem-user{display:flex;align-items:center;gap:10px;padding:10px 12px;margin-top:18px} .gem-avatar{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#4285f4,#9b72cb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600} .hero{font-size:28px;text-align:center;margin-top:36px} .pill-center{max-width:768px;margin:12px auto 0;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,0.12);padding:8px 10px 8px 18px} .pill-center div[data-testid='stTextInput']>div>div>input{border:none !important;box-shadow:none !important;background:transparent !important;font-size:15px !important;height:44px !important} .pill-center div[data-testid='stSelectbox']>div>div{border:none !important;box-shadow:none !important;background:transparent !important} .pill-center button{border:none !important;background:#d3e3fd !important;box-shadow:none !important;border-radius:50% !important;width:38px !important;height:38px !important} div[data-testid='stChatInput']{max-width:768px !important;margin:0 auto !important} div[data-testid='stChatInput']>div{border-radius:999px !important;box-shadow:0 4px 24px rgba(0,0,0,0.12) !important;border:none !important} .chat-ai{max-width:768px;margin:4px auto 2px;font-size:15px;line-height:1.55;padding:2px 0} .block-container{padding-top:0 !important}</style>", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
def make_male_audio(text):
    text=text[:900].strip()
    if not text: return None,"empty"
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
        if data and len(data)>1000: return data,"Niwat"
    except: pass
    try:
        from gtts import gTTS
        buf=io.BytesIO(); gTTS(text=text,lang="th",slow=False).write_to_fp(buf); return buf.getvalue(),"gTTS"
    except Exception as e: return None,str(e)
def show_audio(data):
    b64=base64.b64encode(data).decode()
    import streamlit.components.v1 as components
    html="<div style='display:flex;align-items:center;gap:10px;background:#f0f4f9;border-radius:999px;padding:8px 14px;max-width:768px'><audio id='zy' autoplay src='data:audio/mp3;base64,"+b64+"' style='display:none'></audio><button onclick=\"document.getElementById('zy').play()\" style='border:none;background:#fff;width:34px;height:34px;border-radius:50%;cursor:pointer'>▶</button><span style='font-family:Prompt;font-size:13px'>🔊 Zyphere กำลังพูด... กด ▶ ถ้าเสียงไม่ดัง</span></div>"
    components.html(html, height=56)
with st.sidebar:
    hist=""
    if st.session_state.messages:
        seen=[]
        for m in st.session_state.messages:
            if m["role"]=="user" and m["content"] not in seen:
                seen.append(m["content"]); hist+="<a class='gem-item' href='?nav=home'><span class='ic'>💬</span>"+m["content"][:28]+"</a>"
    if not hist: hist="<a class='gem-item' href='?nav=new'><span class='ic'>💬</span>เริ่มต้นการสนทนา</a>"
    sidebar_html="<div class='gem-sidebar'><div class='gem-top'><div class='gem-logo'>✦</div><div class='gem-title'>Zyphere</div><div class='gem-top-right'><span>⌕</span><span>▭</span></div></div><a class='gem-item active' href='?nav=new'><span class='ic'>✎</span>แชทใหม่</a><a class='gem-item' href='?nav=library'><span class='ic'>⊞</span>คลัง</a><a class='gem-item' href='?nav=scheduled'><span class='ic'>◷</span>กำหนดเวลาแล้ว</a><a class='gem-item' href='?nav=custom'><span class='ic'>✎</span>ปรับแต่ง Zyphere</a><a class='gem-item' href='?nav=video'><span class='ic'>▷</span>วิดีโอ</a><div class='gem-label'>เครื่องมือ</div><a class='gem-item' href='?nav=voice'><span class='ic'>🎙</span>พูดคุยด้วยเสียง</a><a class='gem-item' href='?nav=todo'><span class='ic'>✓</span>รายการงานของฉัน</a><a class='gem-item' href='?nav=code'><span class='ic'>⌨</span>เขียนโค้ดให้หน่อย</a><a class='gem-item' href='?nav=summary'><span class='ic'>▤</span>สรุปงาน</a><a class='gem-item' href='?nav=idea'><span class='ic'>✦</span>คิดไอเดีย</a><a class='gem-item' href='?nav=email'><span class='ic'>📝</span>เขียนอีเมล / เอกสาร</a><a class='gem-item' href='?nav=translate'><span class='ic'>🌐</span>แปลภาษา</a><a class='gem-item' href='?nav=math'><span class='ic'>🧮</span>คิดเลข / วางแผน</a><div class='gem-label'>Notebook</div><a class='gem-item' href='?nav=notebook'><span class='ic'>＋</span>Notebook ใหม่</a><div class='gem-label'>ทั้งหมด</div>"+hist+"<div class='gem-label'>BRAINS — Zyphere</div></div>"
    st.markdown(sidebar_html, unsafe_allow_html=True)
    brain=st.selectbox("เลือกสมอง", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], key="brain_side", label_visibility="collapsed")
    voice=st.checkbox("◉ ให้ Zyphere พูดตอบกลับ (เสียงผู้ชาย)", value=True)
    st.markdown("<div class='gem-user'><div class='gem-avatar'>W</div><div><b style='font-size:14px'>"+st.session_state.user_name+"</b><br><span style='font-size:12px;color:#5f6368'>เจ้าของ Zyphere</span></div><span style='margin-left:auto'>⚙</span></div>", unsafe_allow_html=True)
has_chat=len(st.session_state.messages)>0 or bool(st.session_state.pending)
if not has_chat:
    st.markdown("<div class='hero'>สวัสดี "+st.session_state.user_name+" เราจะเริ่มจากตรงไหนก่อนดี</div>", unsafe_allow_html=True)
    st.markdown("<div class='pill-center'>", unsafe_allow_html=True)
    with st.form("pill_center", clear_on_submit=True):
        c1,c2,c3,c4=st.columns([0.4,4,1.6,0.5])
        with c1: st.markdown("<div style='font-size:24px;text-align:center;padding-top:6px'>＋</div>", unsafe_allow_html=True)
        with c2: inp=st.text_input("q", placeholder="พิมพ์ @ เพื่อดูเครื่องมือเชื่อมต่อ ทักษะ และอื่นๆ", label_visibility="collapsed")
        with c3: brain_pill=st.selectbox("m", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], label_visibility="collapsed")
        with c4: sent=st.form_submit_button("↑")
    st.markdown("</div>", unsafe_allow_html=True)
    prompt=inp if sent else ""
    if brain_pill!="Zyphere อัตโนมัติ": brain=brain_pill
else:
    for m in st.session_state.messages:
        if m["role"]=="user": st.markdown("<div style='max-width:768px;margin:12px auto 2px;display:flex;justify-content:flex-end'><span style='background:#f0f4f9;border-radius:999px;padding:10px 18px;font-size:15px'>"+m["content"]+"</span></div>", unsafe_allow_html=True)
        else: st.markdown("<div class='chat-ai'>"+m["content"]+"</div>", unsafe_allow_html=True)
    if st.session_state.last_audio: show_audio(st.session_state.last_audio)
    inp2=st.chat_input("ถาม Zyphere")
    prompt=st.session_state.pending or inp2 or ""
    if st.session_state.pending: st.session_state.pending=""
if prompt:
    if prompt not in [m["content"] for m in st.session_state.messages if m["role"]=="user"]: st.session_state.messages.append({"role":"user","content":prompt})
    st.markdown("<div style='max-width:768px;margin:12px auto 2px;display:flex;justify-content:flex-end'><span style='background:#f0f4f9;border-radius:999px;padding:10px 18px;font-size:15px'>"+prompt+"</span></div>", unsafe_allow_html=True)
    with st.spinner("Zyphere กำลังคิด..."):
        try:
            uname=st.session_state.user_name or "Whisp"
            system="You are Zyphere, coworker friend of "+uname+". Talk like a close male teammate in Thai, warm, direct, simple. Name is Zyphere."
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
            st.markdown("<div class='chat-ai'>"+answer+"</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role":"assistant","content":answer})
            if voice:
                data,label=make_male_audio(answer)
                if data:
                    st.session_state.last_audio=data; show_audio(data)
            st.rerun()
        except Exception as e: st.error("Error: "+str(e))
