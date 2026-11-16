# ZYPHERE V54 - TRUE META AI CLONE FIX - CHECK THIS LINE
import streamlit as st, os
st.set_page_config(page_title='Zyphere', page_icon='✦', layout='wide', initial_sidebar_state='expanded')
if 'messages' not in st.session_state: st.session_state.messages=[]
if 'pending' not in st.session_state: st.session_state.pending=''
if 'last_audio' not in st.session_state: st.session_state.last_audio=None
if 'user_name' not in st.session_state: st.session_state.user_name='Whisp'
if 'show_add' not in st.session_state: st.session_state.show_add=False
if 'add_img' not in st.session_state: st.session_state.add_img=None
if 'add_text' not in st.session_state: st.session_state.add_text=''
if 'brain_main' not in st.session_state: st.session_state.brain_main='Zyphere อัตโนมัติ'
if 'collapsed' not in st.session_state: st.session_state.collapsed=False
# V54: if user stuck collapsed from V53, start expanded - sidebar must be visible
if st.session_state.get('v54_reset') is None: st.session_state.collapsed=False; st.session_state.v54_reset=True
if 'recent_files' not in st.session_state: st.session_state.recent_files=[]
if 'voice_on' not in st.session_state: st.session_state.voice_on=True
_act=st.query_params.get('action','')
if _act=='logout': st.session_state.messages=[]; st.query_params.clear(); st.rerun()
if _act=='login': st.session_state.user_name='Whisp'; st.query_params.clear(); st.rerun()

# --- META AI EXACT CSS ---
st.markdown("""<style>
.stApp{font-family:Prompt,sans-serif!important;background:#fff}
[data-testid='stToolbar']{display:none} footer{display:none}
section[data-testid='stSidebar']{background:#fff!important;width:280px!important;min-width:280px!important;border-right:1px solid #f0f0f0}
section[data-testid='stSidebar'] > div{padding-top:0!important}
div[data-testid='stSidebarContent']{padding:0 12px!important}
div[data-testid='stSidebarContent'] [data-testid='stVerticalBlock']{gap:4px!important}
section[data-testid='stSidebar'] .stButton>button{width:100%!important;text-align:left!important;justify-content:flex-start!important;background:transparent!important;border:none!important;border-radius:999px!important;height:36px!important;padding:0 12px!important;font-size:14px!important;color:#1f1f1f!important;box-shadow:none!important;white-space:nowrap!important;overflow:hidden!important}
section[data-testid='stSidebar'] .stButton>button:hover{background:#f0f4f9!important}
.main .block-container{max-width:760px!important;margin:auto!important;padding-top:140px!important}
.hero{font-size:28px!important;font-weight:700!important;text-align:center!important;color:#1f1f1f!important;margin-bottom:24px!important}
.pill{background:#fff!important;border-radius:24px!important;box-shadow:0 4px 24px rgba(0,0,0,.08)!important;padding:12px 14px!important;max-width:680px!important;margin:0 auto!important} .main .block-container{max-width:760px!important;margin:0 auto!important;padding-left:24px!important;padding-right:24px!important} [data-testid='stFileUploader']{max-width:560px!important;margin:0 auto!important;background:#fff!important;border-radius:0 0 24px 24px!important;box-shadow:0 20px 60px rgba(0,0,0,.25)!important;padding:0 24px 24px!important}
.chips{display:flex;gap:8px;justify-content:center;margin-top:16px}
.chip{border:1px solid #eee;border-radius:999px;padding:6px 14px;font-size:13px;background:#fff;cursor:pointer}
.chip:hover{background:#f0f0f0}
.chat-ai{max-width:760px;margin:16px auto;font-size:15px;line-height:1.7}
</style>""", unsafe_allow_html=True)
if st.session_state.collapsed:
    st.markdown("<style>section[data-testid='stSidebar']{width:64px!important;min-width:64px!important} section[data-testid='stSidebar'] .stButton>button{font-size:18px!important;justify-content:center!important;padding:0!important} .hide-collapsed{display:none!important}</style>", unsafe_allow_html=True)

def get_key(n):
    return os.environ.get(n,"") or (st.secrets.get(n,"") if hasattr(st,'secrets') else "")
def show_audio(b):
    if b: st.audio(b, format='audio/mp3')

# --- SIDEBAR LIKE META AI ---
with st.sidebar:
    if st.button('✦ Zyphere' if not st.session_state.collapsed else '✦', key='v54_logo'):
        st.session_state.collapsed=not st.session_state.collapsed; st.rerun()
    if not st.session_state.collapsed:
        if st.button('✎  แชทใหม่                                          Ctrl+Shift+O', key='v54_new'): st.session_state.messages=[]; st.rerun()
        if st.button('⌕  ค้นหา                                              Ctrl+K', key='v54_search'): pass
        if st.button('▦  สื่อ', key='v54_media'): pass
        if st.button('◈  อาร์ติแฟกต์', key='v54_art'): pass
        if st.button('◷  กำหนดเวลาแล้ว', key='v54_sched'): pass
        if st.button('♡  Vibes', key='v54_vibes'): pass
        st.markdown("<div style='font-size:12px;color:#888;padding:16px 12px 4px'>ประวัติ</div>", unsafe_allow_html=True)
        if st.button('สร้าง AI ฟรีสุดฉลาด', key='v54_h1'): st.session_state.pending='สร้าง AI ฟรีสุดฉลาด'; st.rerun()
        if st.button('SEO สำหรับน้ำพริกกากหมู', key='v54_h2'): st.session_state.pending='SEO สำหรับน้ำพริกกากหมู'; st.rerun()
        st.markdown("<div style='position:fixed;bottom:0;left:0;width:280px;background:#fff;padding:12px;border-top:1px solid #f0f0f0'><div style='display:flex;align-items:center;gap:10px;padding:0 12px'><div style='width:32px;height:32px;border-radius:50%;background:#7b61ff;color:#fff;display:flex;align-items:center;justify-content:center'>W</div><div><b style='font-size:14px'>Whisp</b><div style='font-size:12px;color:#888'>เจ้าของ Zyphere</div></div></div><a href='?action=logout' target='_self' style='display:flex;padding:0 12px;height:36px;align-items:center;text-decoration:none;color:#1f1f1f;font-size:14px'>↪ ออกจากระบบ</a><a href='?action=login' target='_self' style='display:flex;padding:0 12px;height:36px;align-items:center;text-decoration:none;color:#1f1f1f;font-size:14px'>⇄ สลับบัญชี / เข้าสู่ระบบ</a></div>", unsafe_allow_html=True)
    else:
        for ic,k in [('✎','v54_c_new'),('⌕','v54_c_search'),('▦','v54_c_media'),('◈','v54_c_art'),('◷','v54_c_sched'),('♡','v54_c_vibes')]:
            if st.button(ic, key=k): pass
        st.markdown("<div style='position:fixed;bottom:0;left:0;width:64px;background:#fff;padding:12px 0;text-align:center'><div style='width:32px;height:32px;border-radius:50%;background:#7b61ff;color:#fff;display:flex;align-items:center;justify-content:center;margin:auto'>W</div></div>", unsafe_allow_html=True)

# --- MAIN ---
has_chat=len(st.session_state.messages)>0 or bool(st.session_state.pending)
prompt=''
brain=st.session_state.get('brain_main','Zyphere อัตโนมัติ')
if not has_chat:
    st.markdown("<div class='hero'>เราควรเริ่มจากตรงไหนดี</div>", unsafe_allow_html=True)
    # Meta AI style popup for + : centered modal
    if st.session_state.show_add:
        st.markdown("<div style='background:#fff;border-radius:24px 24px 0 0;box-shadow:0 20px 60px rgba(0,0,0,.25);padding:24px 24px 0;max-width:560px;margin:0 auto'><b style='font-size:18px'>เพิ่มสื่อและไฟล์</b><br><span style='font-size:13px;color:#666'>อัพโหลดอะไรก็ได้ที่คุณต้องการ</span></div>", unsafe_allow_html=True)
        _up=st.file_uploader('คลิกเพื่อดู หรือลากแล้ววางที่นี่', type=['png','jpg','jpeg','webp','pdf','txt','docx','csv'], label_visibility='visible', key='v54_picker')
        if _up is not None:
            st.session_state.add_img=_up
            if _up.name not in st.session_state.recent_files: st.session_state.recent_files.insert(0,_up.name)
            st.session_state.show_add=False; st.rerun()
        if st.session_state.recent_files:
            st.markdown("<div style='font-size:13px;font-weight:600;margin:8px 0;text-align:center'>รายการอัพโหลดล่าสุด</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center'>"+" ".join(["<span style='display:inline-block;background:#f0f4f9;border-radius:12px;padding:8px 12px;font-size:12px;margin:2px'>"+n+"</span>" for n in st.session_state.recent_files[:6]])+"</div>", unsafe_allow_html=True)
        if st.button('✕ ปิด', key='v54_close'): st.session_state.show_add=False; st.rerun()
    if st.session_state.add_img is not None:
        st.markdown("<div style='text-align:center'><span style='background:#fff;border-radius:999px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:6px 12px;font-size:13px'>📎 "+st.session_state.add_img.name+"</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='pill'>", unsafe_allow_html=True)
    with st.form('f', clear_on_submit=True):
        c1,c2,c3,c4=st.columns([0.4,4,1.7,0.5])
        with c1: plus=st.form_submit_button('＋')
        with c2: inp=st.text_input('q', placeholder='ถาม Zyphere...', label_visibility='collapsed')
        with c3: bp=st.selectbox('m',['Zyphere อัตโนมัติ','01 GROQ - FAST','02 GROQ - DEEP','03 GEMINI - LONG','04 OPENROUTER - BIG'], label_visibility='collapsed', key='brain_main')
        with c4: sent=st.form_submit_button('↑')
        # second row inside pill: mic + instant
        st.markdown("<div style='display:flex;justify-content:flex-end;gap:8px;margin-top:8px;font-size:13px;color:#666'><span style='border:1px solid #eee;border-radius:999px;padding:4px 12px'>รูปอินสแตนท์</span><span>🎤</span></div>", unsafe_allow_html=True)
    st.markdown("</div><div class='chips'><span class='chip'>ค้นพบ</span><span class='chip'>ถามอะไรก็ได้</span><span class='chip'>ดำเนินการ</span><span class='chip'>สร้างรูปภาพ</span></div>", unsafe_allow_html=True)
    if plus: st.session_state.show_add=not st.session_state.show_add; st.rerun()
    if sent: prompt=inp; brain=bp
else:
    for m in st.session_state.messages:
        if m['role']=='user': st.markdown("<div style='max-width:760px;margin:12px auto 2px;display:flex;justify-content:flex-end'><span style='background:#f0f4f9;border-radius:999px;padding:10px 18px'>"+m['content']+"</span></div>", unsafe_allow_html=True)
        else: st.markdown("<div class='chat-ai'>"+m['content']+"</div>", unsafe_allow_html=True)
    if st.session_state.last_audio: show_audio(st.session_state.last_audio)
    inp2=st.chat_input('ถาม Zyphere...')
    prompt=st.session_state.pending or inp2 or ''
    if st.session_state.pending: st.session_state.pending=''
if prompt:
    if prompt not in [m['content'] for m in st.session_state.messages if m['role']=='user']: st.session_state.messages.append({'role':'user','content':prompt})
    _extra=''
    if st.session_state.add_text: _extra+='\n\n[ข้อความที่แนบมา]\n'+st.session_state.add_text
    if st.session_state.add_img is not None: _extra+='\n\n[ผู้ใช้แนบไฟล์: '+st.session_state.add_img.name+']'
    if _extra: prompt=prompt+_extra
    with st.spinner('Zyphere กำลังคิด...'):
        try:
            sys='You are Zyphere, smart coworker. Talk Thai, direct, professional, smart. NEVER use emoji. Answer with clean text only.'
            ans=''
            if 'GEMINI' in brain:
                import google.generativeai as genai
                genai.configure(api_key=get_key('GEMINI_API_KEY'))
                model=genai.GenerativeModel('gemini-2.0-flash')
                ans=model.generate_content(prompt).text
            elif 'OPENROUTER' in brain:
                from openai import OpenAI
                c=OpenAI(base_url='https://openrouter.ai/api/v1', api_key=get_key('OPENROUTER_API_KEY'))
                ans=c.chat.completions.create(model='meta-llama/llama-3.1-8b-instruct', messages=[{'role':'user','content':prompt}]).choices[0].message.content
            else:
                from groq import Groq
                c=Groq(api_key=get_key('GROQ_API_KEY'))
                mdl='llama-3.3-70b-versatile' if 'DEEP' in brain else 'llama-3.1-8b-instant'
                ans=c.chat.completions.create(model=mdl, messages=[{'role':'system','content':sys},{'role':'user','content':prompt}]).choices[0].message.content
            st.session_state.messages.append({'role':'assistant','content':ans})
            # Voice: male voice via gTTS, only when user clicks play later - store audio
            try:
                from gtts import gTTS
                import io
                buf=io.BytesIO(); gTTS(text=ans[:800], lang='th').write_to_fp(buf); st.session_state.last_audio=buf.getvalue()
            except: pass
            st.rerun()
        except Exception as e:
            st.session_state.messages.append({'role':'assistant','content':'ต่อสมองไม่ได้: '+str(e)[:200]}); st.rerun()
