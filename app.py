import streamlit as st, os, io, base64, asyncio
st.set_page_config(page_title='Zyphere', page_icon='✦', layout='wide', initial_sidebar_state='expanded')
if 'messages' not in st.session_state: st.session_state.messages=[]
if 'pending' not in st.session_state: st.session_state.pending=''
if 'last_audio' not in st.session_state: st.session_state.last_audio=None
if 'user_name' not in st.session_state: st.session_state.user_name='Whisp'
if 'active' not in st.session_state: st.session_state.active='new'
nav=st.query_params.get('nav','')
MAP={'new':'','search':'ค้นหา','media':'เปิดสื่อ','artifacts':'เปิดอาร์ติแฟกต์','scheduled':'ดูงานวันนี้','custom':'ปรับแต่ง Zyphere','video':'คิดสคริปต์วิดีโอ','vibes':'เปิด Vibes'}
if nav:
    st.session_state.active=nav
    if nav=='new': st.session_state.messages=[]
    elif nav in MAP and MAP[nav]: st.session_state.pending=MAP[nav]
    st.query_params.clear(); st.rerun()
st.markdown("<style>.stApp{font-family:Prompt,sans-serif!important;background:#fff} [data-testid='stToolbar']{display:none} footer{display:none} header{visibility:hidden} section[data-testid='stSidebar']{background:#fff!important;width:280px!important;min-width:280px!important;border-right:1px solid #f0f0f0} div[data-testid='stSidebarContent']{padding:0!important} .g{padding:0 8px} .top{display:flex;align-items:center;gap:10px;padding:14px 12px 0 12px} .logo{width:26px;height:26px;border-radius:50%;background:conic-gradient(#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:14px} .tt{font-size:17px;font-weight:500} .gap28{height:28px} .it{display:flex;align-items:center;gap:12px;padding:0 12px;height:40px;border-radius:999px;text-decoration:none!important;color:#1f1f1f!important;font-size:14px} .it:hover{background:#f0f4f9!important} .it.on{background:#f0f4f9!important} .ic{width:22px;text-align:center;font-size:15px} .lb{font-size:12px;color:#5f6368;padding:22px 12px 8px} .user{display:flex;align-items:center;gap:10px;padding:14px 12px;margin-top:28px} .hero{font-size:28px;text-align:center;margin-top:110px;color:#1f1f1f} .center{max-width:720px;margin:22px auto 0;position:relative} .blob{position:absolute;inset:-40px -80px auto -80px;height:220px;background:radial-gradient(ellipse at center, rgba(66,133,244,.18), rgba(155,114,203,.12) 45%, transparent 70%);filter:blur(10px);z-index:0} .pill{position:relative;z-index:1;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,.10);padding:10px 12px 10px 18px} .chips{display:flex;gap:8px;justify-content:center;margin-top:16px} .chip{border:1px solid #eee;border-radius:999px;padding:7px 14px;font-size:13px;color:#444;background:#fff} .chat-ai{max-width:760px;margin:6px auto;font-size:15px;line-height:1.6}</style>", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,'')
    except: return os.getenv(n,'')
def make_audio(t):
    t=t[:900].strip()
    if not t: return None
    try:
        import edge_tts
        async def _s():
            c=edge_tts.Communicate(t,'th-TH-NiwatNeural',rate='+0%',pitch='-4Hz'); b=io.BytesIO()
            async for ch in c.stream():
                if ch['type']=='audio': b.write(ch['data'])
            return b.getvalue()
        loop=asyncio.new_event_loop()
        try: asyncio.set_event_loop(loop); d=loop.run_until_complete(_s())
        finally: loop.close()
        if d and len(d)>1000: return d
    except: pass
    try:
        from gtts import gTTS; b=io.BytesIO(); gTTS(text=t,lang='th',slow=False).write_to_fp(b); return b.getvalue()
    except: return None
def show_audio(d):
    b64=base64.b64encode(d).decode(); import streamlit.components.v1 as comp
    h="<div style='display:flex;gap:10px;background:#f0f4f9;border-radius:999px;padding:8px 14px'><audio id='z' autoplay src='data:audio/mp3;base64,"+b64+"' style='display:none'></audio><button onclick=\"document.getElementById('z').play()\" style='border:none;background:#fff;width:34px;height:34px;border-radius:50%'>\u25b6</button><span>\U0001f50a Zyphere กำลังพูด...</span></div>"
    comp.html(h, height=56)
with st.sidebar:
    a=st.session_state.active
    def it(k,ic,txt): return "<a class='it"+(" on" if a==k else "")+"' href='?nav="+k+"'><span class='ic'>"+ic+"</span>"+txt+"</a>"
    hist=''
    seen=[]
    for m in st.session_state.messages:
        if m['role']=='user' and m['content'] not in seen: seen.append(m['content']); hist+="<a class='it' href='?nav=search'><span class='ic'>\U0001f4ac</span>"+m['content'][:30]+"</a>"
    if not hist: hist="<a class='it' href='?nav=new'><span class='ic'>\U0001f4ac</span>เริ่มต้นการสนทนา</a>"
    html="<div class='g'><div class='top'><div class='logo'>\u2726</div><div class='tt'>Zyphere</div><div style='margin-left:auto;font-size:16px'>\u2315</div></div><div class='gap28'></div>"+it('new','\u270e','แชทใหม่')+it('media','\u25a6','คลัง')+it('scheduled','\u25f7','กำหนดเวลาแล้ว')+it('custom','\u25ce','ปรับแต่ง')+it('video','\u25a1','วิดีโอ')+"<div class='lb'>Notebook</div><a class='it' href='?nav=new'><span class='ic'>＋</span>Notebook ใหม่</a><div class='lb'>ทั้งหมด</div>"+hist+"<div class='user'><div style='width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#4285f4,#9b72cb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600'>W</div><div><b>Whisp</b></div><span style='margin-left:auto'>\u2699</span></div></div>"
    st.markdown(html, unsafe_allow_html=True)
    brain=st.selectbox('สมอง',['Zyphere อัตโนมัติ','01 GROQ - FAST','02 GROQ - DEEP','03 GEMINI - LONG','04 OPENROUTER - BIG'], label_visibility='collapsed')
    voice=st.checkbox('ให้ Zyphere พูดตอบกลับ (เสียงผู้ชาย)', value=True)
has_chat=len(st.session_state.messages)>0 or bool(st.session_state.pending)
prompt=''
if not has_chat:
    st.markdown("<div class='hero'>เราจะเริ่มจากตรงไหนก่อนดี</div>", unsafe_allow_html=True)
    st.markdown("<div class='center'><div class='blob'></div><div class='pill'>", unsafe_allow_html=True)
    with st.form('f', clear_on_submit=True):
        c1,c2,c3,c4=st.columns([0.4,4,1.7,0.5])
        with c1: st.markdown("<div style='font-size:22px;text-align:center;padding-top:4px'>＋</div>", unsafe_allow_html=True)
        with c2: inp=st.text_input('q', placeholder='ถาม Zyphere', label_visibility='collapsed')
        with c3: bp=st.selectbox('m',['Zyphere อัตโนมัติ','01 GROQ - FAST','02 GROQ - DEEP','03 GEMINI - LONG','04 OPENROUTER - BIG'], label_visibility='collapsed')
        with c4: sent=st.form_submit_button('↑')
    st.markdown('</div><div class="chips"><span class="chip">ค้นพบ</span><span class="chip">ถามอะไรก็ได้</span><span class="chip">ดำเนินการ</span><span class="chip">สร้างรูปภาพ</span></div></div>', unsafe_allow_html=True)
    if sent: prompt=inp; brain=bp
else:
    for m in st.session_state.messages:
        if m['role']=='user': st.markdown("<div style='max-width:760px;margin:12px auto 2px;display:flex;justify-content:flex-end'><span style='background:#f0f4f9;border-radius:999px;padding:10px 18px'>"+m['content']+"</span></div>", unsafe_allow_html=True)
        else: st.markdown("<div class='chat-ai'>"+m['content']+"</div>", unsafe_allow_html=True)
    if st.session_state.last_audio: show_audio(st.session_state.last_audio)
    inp2=st.chat_input('ถาม Zyphere')
    prompt=st.session_state.pending or inp2 or ''
    if st.session_state.pending: st.session_state.pending=''
if prompt:
    if prompt not in [m['content'] for m in st.session_state.messages if m['role']=='user']: st.session_state.messages.append({'role':'user','content':prompt})
    with st.spinner('Zyphere กำลังคิด...'):
        try:
            sys='You are Zyphere, coworker friend. Talk Thai warm direct.'; ans=''
            if 'GEMINI' in brain:
                import google.generativeai as genai; genai.configure(api_key=get_key('GEMINI_API_KEY')); mm=genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys); ans=mm.generate_content(prompt).text
            elif 'OPENROUTER' in brain:
                from openai import OpenAI; cl=OpenAI(base_url='https://openrouter.ai/api/v1', api_key=get_key('OPENROUTER_API_KEY')); ans=cl.chat.completions.create(model='qwen/qwen3-235b-a22b:free', messages=[{'role':'system','content':sys}]+st.session_state.messages).choices[0].message.content
            else:
                from groq import Groq; cl=Groq(api_key=get_key('GROQ_API_KEY')); last=''
                for mdl in ['llama-3.1-8b-instant','qwen-qwq-32b','openai/gpt-oss-120b']:
                    try: ans=cl.chat.completions.create(model=mdl, messages=[{'role':'system','content':sys}]+st.session_state.messages, temperature=0.8, max_tokens=2000).choices[0].message.content; break
                    except Exception as e: last=str(e); continue
                if not ans: ans='Groq ติด: '+last
            st.session_state.messages.append({'role':'assistant','content':ans})
            if voice:
                d=make_audio(ans)
                if d: st.session_state.last_audio=d; show_audio(d)
            st.rerun()
        except Exception as e: st.error('Error: '+str(e))
