import streamlit as st, os, io, base64, asyncio
st.set_page_config(page_title='Zyphere', page_icon='✦', layout='wide', initial_sidebar_state='expanded')
if 'messages' not in st.session_state: st.session_state.messages=[]
if 'pending' not in st.session_state: st.session_state.pending=''
if 'last_audio' not in st.session_state: st.session_state.last_audio=None
if 'user_name' not in st.session_state: st.session_state.user_name='Whisp'
if 'active' not in st.session_state: st.session_state.active='new'
if 'show_add' not in st.session_state: st.session_state.show_add=False
if 'add_text' not in st.session_state: st.session_state.add_text=''
if 'add_img' not in st.session_state: st.session_state.add_img=None
nav=st.query_params.get('nav','')
if st.query_params.get('add','')=='1': st.session_state.show_add=not st.session_state.show_add; st.query_params.clear(); st.rerun()
MAP={'new':'','search':'ค้นหา','media':'เปิดสื่อ','artifacts':'เปิดอาร์ติแฟกต์','scheduled':'ดูงานวันนี้','custom':'ปรับแต่ง Zyphere','video':'คิดสคริปต์วิดีโอ','vibes':'เปิด Vibes'}
if nav:
    st.session_state.active=nav
    if nav=='new': st.session_state.messages=[]
    elif nav in MAP and MAP[nav]: st.session_state.pending=MAP[nav]
    st.query_params.clear(); st.rerun()
st.markdown("<style>.stApp{font-family:Prompt,sans-serif!important;background:#fff} [data-testid='stToolbar']{display:none} footer{display:none} header{visibility:visible} [data-testid='stHeader']{background:transparent} [data-testid='collapsedControl']{display:flex!important;visibility:visible!important} section[data-testid='stSidebar'] [data-testid='stVerticalBlock']{gap:2px!important} section[data-testid='stSidebar'] [data-testid='stVerticalBlock']>div{margin:0!important;padding:0!important} section[data-testid='stSidebar'] .stButton{margin:0!important;padding:0!important} section[data-testid='stSidebar'] .stMarkdown{margin:0!important;padding:0!important} section[data-testid='stSidebar']{background:#fff!important;visibility:visible!important;transform:none!important;width:280px!important;min-width:280px!important;border-right:1px solid #f0f0f0} div[data-testid='stSidebarContent']{padding:0!important} .g{padding:0 8px} .top{display:flex;align-items:center;gap:10px;padding:10px 12px 0 12px} .logo{width:26px;height:26px;border-radius:50%;background:conic-gradient(#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:14px} .tt{font-size:17px;font-weight:500} .gap28{height:12px} .stButton>button{background:transparent!important;border:none!important;box-shadow:none!important;text-align:left!important;justify-content:flex-start!important;padding:0 12px!important;height:32px!important;min-height:32px!important;line-height:32px!important;border-radius:999px!important;font-size:14px!important;color:#1f1f1f!important;width:100%!important} .stButton>button:hover{background:#f0f4f9!important} .stButton>button:focus{box-shadow:none!important} .it{display:flex;align-items:center;gap:12px;padding:0 12px;height:40px;border-radius:999px;text-decoration:none!important;color:#1f1f1f!important;font-size:14px} .it:hover{background:#f0f4f9!important} .it.on{background:#f0f4f9!important} .ic{width:22px;text-align:center;font-size:15px} .lb{font-size:12px;color:#5f6368;padding:10px 12px 2px;line-height:1} .user{display:flex;align-items:center;gap:10px;padding:8px 12px;margin-top:10px} .hero{font-size:28px;text-align:center;margin-top:110px;color:#1f1f1f} .center{max-width:720px;margin:22px auto 0;position:relative} .blob{position:absolute;inset:-40px -80px auto -80px;height:220px;background:radial-gradient(ellipse at center, rgba(66,133,244,.18), rgba(155,114,203,.12) 45%, transparent 70%);filter:blur(10px);z-index:0} .pill{position:relative;z-index:1;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,.10);padding:10px 12px 10px 18px} .chips{display:flex;gap:8px;justify-content:center;margin-top:16px} .chip{border:1px solid #eee;border-radius:999px;padding:7px 14px;font-size:13px;color:#444;background:#fff} .chat-ai{max-width:760px;margin:6px auto;font-size:15px;line-height:1.6}</style>", unsafe_allow_html=True)
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
    h="<div style='max-width:760px;margin:6px auto'><audio id='z' src='data:audio/mp3;base64,"+b64+"' style='display:none'></audio><button onclick=\"document.getElementById('z').play()\" style='border:1px solid #eee;background:#fff;width:32px;height:32px;border-radius:50%;cursor:pointer'>\u25b6</button></div>"
    comp.html(h, height=40)
with st.sidebar:
    st.markdown("<div class='g'><div class='top'><div class='logo'>✦</div><div class='tt'>Zyphere</div><div style='margin-left:auto;font-size:16px'>⌕</div></div><div class='gap28'></div></div>", unsafe_allow_html=True)
    if st.button('✎  แชทใหม่', key='sb_new'): st.session_state.messages=[]; st.session_state.active='new'; st.rerun()
    if st.button('▦  คลัง', key='sb_media'): st.session_state.pending='เปิดสื่อ'; st.session_state.active='media'; st.rerun()
    if st.button('◷  กำหนดเวลาแล้ว', key='sb_sched'): st.session_state.pending='ดูงานวันนี้'; st.session_state.active='scheduled'; st.rerun()
    if st.button('◎  ปรับแต่ง', key='sb_custom'): st.session_state.pending='ปรับแต่ง Zyphere'; st.session_state.active='custom'; st.rerun()
    if st.button('▢  วิดีโอ', key='sb_video'): st.session_state.pending='คิดสคริปต์วิดีโอ'; st.session_state.active='video'; st.rerun()
    st.markdown("<div class='lb'>Notebook</div>", unsafe_allow_html=True)
    if st.button('＋  Notebook ใหม่', key='sb_nb'): st.session_state.messages=[]; st.session_state.active='new'; st.rerun()
    st.markdown("<div class='lb'>ทั้งหมด</div>", unsafe_allow_html=True)
    _seen=[]
    _has=False
    for m in st.session_state.messages:
        if m['role']=='user' and m['content'] not in _seen:
            _seen.append(m['content']); _has=True
            if st.button(m['content'][:30], key='hist_'+str(len(_seen))): st.session_state.pending=m['content']; st.rerun()
    if not _has:
        if st.button('เริ่มต้นการสนทนา', key='sb_start'): st.session_state.pending='เริ่มต้นการสนทนา'; st.rerun()
    st.markdown("<div class='user'><div style='width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#4285f4,#9b72cb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600'>W</div><div><b>Whisp</b></div><span style='margin-left:auto'>⚙</span></div></div>", unsafe_allow_html=True)
    brain=st.selectbox('สมอง',['Zyphere อัตโนมัติ','01 GROQ - FAST','02 GROQ - DEEP','03 GEMINI - LONG','04 OPENROUTER - BIG'], label_visibility='collapsed')
    voice=st.checkbox('ให้ Zyphere พูดตอบกลับ (เสียงผู้ชาย)', value=False)
has_chat=len(st.session_state.messages)>0 or bool(st.session_state.pending)
prompt=''
if not has_chat:
    st.markdown("<div class='hero'>เราจะเริ่มจากตรงไหนก่อนดี</div>", unsafe_allow_html=True)
    st.markdown("<div class='center'><div class='blob'></div><div class='pill'>", unsafe_allow_html=True)
    if st.session_state.show_add:
        st.markdown("<div style='background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.10);padding:14px;margin-bottom:10px'><b>＋ เพิ่มให้ Zyphere ทำงาน</b><br><span style='font-size:13px;color:#666'>เพิ่มรูป / ไฟล์ / ข้อความ แล้วพิมพ์สั่งข้างล่าง Zyphere จะเอาไปทำงานด้วย</span></div>", unsafe_allow_html=True)
        up=st.file_uploader('เพิ่มรูป / ไฟล์', type=['png','jpg','jpeg','webp','pdf','txt','docx','csv'], label_visibility='collapsed')
        if up is not None:
            st.session_state.add_img=up
            st.success('เพิ่มแล้ว: '+up.name+' - Zyphere จะเห็นไฟล์นี้ตอนคุณพิมพ์สั่ง')
            if up.type and 'image' in up.type: st.image(up, width=200)
        st.session_state.add_text=st.text_area('เพิ่มข้อความ / คำสั่งยาวๆ', value=st.session_state.add_text, placeholder='วางข้อความยาวๆ ตรงนี้ เช่น บทความ โค้ด เนื้อหาที่จะให้ Zyphere สรุป...', height=100)
        if st.button('＋ เพิ่มการสนทนาใหม่ (เริ่มแชทใหม่ + เก็บแชทเก่าไว้)'):
            st.session_state.messages=[]; st.session_state.show_add=False; st.rerun()

    with st.form('f', clear_on_submit=True):
        c1,c2,c3,c4=st.columns([0.4,4,1.7,0.5])
        with c1:
            if st.form_submit_button('＋'): st.session_state.show_add=not st.session_state.show_add
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
    _extra=''
    if st.session_state.add_text: _extra='\n\n[ข้อความที่แนบมา]\n'+st.session_state.add_text
    if st.session_state.add_img is not None: _extra+='\n\n[ผู้ใช้แนบไฟล์: '+st.session_state.add_img.name+']'
    if prompt not in [m['content'] for m in st.session_state.messages if m['role']=='user']: st.session_state.messages.append({'role':'user','content':prompt})
    if _extra: prompt=prompt+_extra
    with st.spinner('Zyphere กำลังคิด...'):
        try:
            sys='You are Zyphere, smart coworker. Talk Thai, direct, professional, smart. NEVER use emoji, emoticons, icons, smiley faces, or symbols like :) :( :D. Answer with clean text only, no emoji. No greeting emoji. Be concise and intelligent.'; ans=''
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
            import re as _re
            ans=_re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\u2700-\u27BF\uFE0F\u200D]+','',ans)
            ans=ans.replace('😊','').replace('🙂','').replace('😀','').replace('😄','').replace('👍','').replace('🔊','').replace(':)','').replace(':-)','').strip()
            st.session_state.messages.append({'role':'assistant','content':ans})
            if voice:
                d=make_audio(ans)
                if d: st.session_state.last_audio=d; show_audio(d)
            st.rerun()
        except Exception as e: st.error('Error: '+str(e))
