import streamlit as st, os
st.set_page_config(page_title="ZYP HERE", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* { font-family:'Prompt',sans-serif !important; }
/* DO NOT hide header - it holds the sidebar open button */
header[data-testid="stHeader"]{background:transparent !important}
[data-testid="stToolbar"]{display:none !important}
footer{display:none !important}
.stApp{background: radial-gradient(680px 420px at 62% 55%, #cfe0ff 0%, transparent 62%), radial-gradient(550px 320px at 38% 58%, #e6f0ff 0%, transparent 60%), #fff !important}
section[data-testid="stSidebar"]{width:280px !important; min-width:280px !important; background:#f0f4f9 !important}
section[data-testid="stSidebar"] > div{padding-top:0 !important}
.block-container{padding:0 !important; max-width:100% !important}
div[data-testid="stVerticalBlock"]{gap:0 !important}
.logo-row{display:flex;align-items:center;gap:10px;padding:16px 14px 12px}
.logo-anim{width:38px;height:38px;min-width:38px;border-radius:50%;background:conic-gradient(from 0deg,#4285f4,#9b72cb,#d96570,#f9ab00,#4285f4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:19px;animation:spinGlow 2.8s ease-in-out infinite}
@keyframes spinGlow{0%,100%{transform:rotate(0deg) scale(1)}50%{transform:rotate(180deg) scale(1.1);box-shadow:0 0 20px rgba(66,133,244,.55)}}
.side-label{font-size:12px;color:#5f6368;padding:18px 22px 6px}
div[data-testid="stSidebar"] button{border:none !important;background:transparent !important;box-shadow:none !important;text-align:left !important;padding:4px 12px !important;height:38px !important;border-radius:999px !important;font-size:14px !important;color:#1f1f1f !important}
div[data-testid="stSidebar"] button:hover{background:#e3e3e3 !important}
.topbar{display:flex;justify-content:flex-end;gap:8px;padding:12px 18px 0 0}
.top-gray{background:#eef2f7;border:none;border-radius:999px;padding:8px 14px;font-size:13px}
.top-blue{background:#d3e3fd;border:none;border-radius:999px;padding:8px 16px;font-size:13px;font-weight:500}
.hero{font-size:32px;font-weight:500;text-align:center;margin-top:120px;color:#1f1f1f}
</style>
""", unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
if "messages" not in st.session_state: st.session_state.messages=[]
if "quick" not in st.session_state: st.session_state.quick=""
def menu(label, prompt=""):
    if st.sidebar.button(label, use_container_width=True):
        if prompt:
            st.session_state.quick = prompt
        elif "แชทใหม่" in label:
            st.session_state.messages=[]; st.session_state.quick=""
        st.rerun()
# --- LEFT - REAL BUTTONS, all usable ---
with st.sidebar:
    st.markdown('<div class="logo-row"><div class="logo-anim">✦</div><div><div style="font-size:17px;font-weight:600;line-height:1.1">Zyphere</div><div style="font-size:11px;color:#5f6368">เพื่อนร่วมงานของคุณ</div></div></div>', unsafe_allow_html=True)
    menu("✎  แชทใหม่")
    menu("⌕  ค้นหาแชท", "ค้นหาแชทเก่าให้หน่อย สรุปให้ว่าผมเคยคุยเรื่องอะไรบ้าง")
    menu("⊞  คลัง", "เปิดคลังงานของฉัน สรุปไฟล์และงานที่เคยทำ")
    menu("◷  กำหนดเวลาแล้ว", "ดูงานที่กำหนดเวลาไว้วันนี้ แล้วจัดลำดับให้หน่อย")
    menu("✎  ปรับแต่ง Zyphere", "ปรับแต่ง Zyphere ให้พูดแบบเพื่อนร่วมงาน ตรงๆ อบอุ่น")
    menu("▷  วิดีโอ", "ช่วยคิดสคริปต์วิดีโอสั้นๆ ให้หน่อย")
    st.markdown('<div class="side-label">เครื่องมือที่ใช้บ่อย</div>', unsafe_allow_html=True)
    menu("🎙  พูดคุยด้วยเสียง", "คุยกับฉันด้วยเสียง พูดตอบกลับเป็นภาษาไทย")
    menu("✓  รายการงานของฉัน", "ทำรายการงานวันนี้ให้หน่อย แบบเช็กลิสต์")
    menu("⌨  เขียนโค้ดให้หน่อย", "เขียนโค้ดให้หน่อย อธิบายทีละบรรทัด")
    menu("▤  สรุปงาน", "สรุปงานวันนี้ให้สั้นๆ เข้าใจง่าย")
    menu("✦  คิดไอเดีย", "คิดไอเดียใหม่ๆ ให้หน่อย 5 ไอเดีย")
    menu("◉  อธิบายลึกๆ", "อธิบายเรื่องนี้ให้ลึกๆ แบบเข้าใจง่าย")
    menu("📝  เขียนอีเมล / เอกสาร", "ช่วยร่างอีเมล / เอกสารให้หน่อย สุภาพ เป็นทางการ")
    menu("🌐  แปลภาษา", "ช่วยแปลภาษาให้หน่อย ไทย-อังกฤษ")
    st.markdown('<div class="side-label">Notebook</div>', unsafe_allow_html=True)
    menu("＋  Notebook ใหม่", "สร้าง Notebook ใหม่ สรุปเรื่องที่ฉันจะถาม")
    st.markdown('<div class="side-label">BRAINS — Zyphere</div>', unsafe_allow_html=True)
    st.selectbox("เลือกสมอง", ["Zyphere อัตโนมัติ","01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], key="brain_side")
    voice = st.checkbox("◉ ให้ Zyphere พูดตอบกลับ", value=True)
    st.markdown('<div style="position:fixed;bottom:16px;left:12px;width:250px;display:flex;justify-content:space-between;align-items:center;padding:0 12px"><span style="font-size:14px">○ Whisp</span><span style="font-size:16px">⚙</span></div>', unsafe_allow_html=True)
st.markdown('<div class="topbar"><button class="top-gray">↓ ดาวน์โหลดแอป</button><button class="top-blue">✦ อัปเกรด</button><button class="top-gray">✦</button></div>', unsafe_allow_html=True)
qp = st.query_params
prompt = qp.get("q", "") or st.session_state.quick
brain = qp.get("brain", "") or st.session_state.get("brain_side","Zyphere อัตโนมัติ")
if qp.get("q"):
    st.query_params.clear()
    st.session_state.quick=""
if not st.session_state.messages and not prompt:
    st.markdown('<div class="hero">เราจะเริ่มจากตรงไหนก่อนดี</div>', unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
import streamlit.components.v1 as components
pill_html = """
<div style="max-width:680px;margin:28px auto 0;background:#fff;border-radius:999px;box-shadow:0 4px 24px rgba(0,0,0,0.12);padding:8px 10px 8px 14px;display:flex;align-items:center;gap:8px;font-family:Prompt,sans-serif">
  <span style="font-size:24px;line-height:1">＋</span>
  <form id="f" style="flex:1;display:flex;align-items:center;gap:8px;margin:0">
    <input id="q" name="q" placeholder="ถาม Zyphere" style="flex:1;border:none;outline:none;font-size:15px;font-family:Prompt,sans-serif;background:transparent" />
    <select name="brain" style="border:none;outline:none;font-size:13px;background:transparent;font-family:Prompt,sans-serif"><option>Zyphere อัตโนมัติ</option><option>01 GROQ - FAST</option><option>02 GROQ - DEEP</option><option>03 GEMINI - LONG</option><option>04 OPENROUTER - BIG</option></select>
    <button type="button" onclick="voice()" style="border:none;background:#f0f4f9;width:36px;height:36px;border-radius:50%;font-size:16px;cursor:pointer">🎙</button>
  </form>
</div>
<script>
function voice(){ try{ var r=new (window.SpeechRecognition||window.webkitSpeechRecognition)(); r.lang='th-TH'; r.onresult=function(e){ document.getElementById('q').value=e.results[0][0].transcript; document.getElementById('f').requestSubmit(); }; r.start(); }catch(e){ alert('เบราว์เซอร์นี้ไม่รองรับไมค์ ลองพิมพ์แทนได้เลย'); } }
document.getElementById('f').addEventListener('submit', function(e){ e.preventDefault(); var q=document.getElementById('q').value; var b=document.querySelector('select[name=brain]').value; if(!q) return; var url=new URL(window.parent.location.href); url.searchParams.set('q',q); url.searchParams.set('brain',b); window.parent.location.href=url.toString(); });
</script>
"""
components.html(pill_html, height=80)
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
