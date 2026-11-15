import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts
import base64

st.set_page_config(
    page_title="Build | Zyphere Studio", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ดีไซน์ CSS สมบูรณ์แบบ (ซ่อนกล่องแชทและซ่อนเครื่องเล่นเสียงทั้งหมด) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #1f1f1f;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ซ่อนกล่องแสดงข้อความแชทและเครื่องเล่นเสียงทั้งหมดไม่ให้เกะกะสายตา */
    [data-testid="stChatMessage"], .stAudio {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
        padding-top: 0.5rem;
    }

    .block-container {
        padding-top: 6vh !important;
        padding-bottom: 2rem !important;
        max-width: 880px !important;
        margin: 0 auto;
    }

    .logo-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-top: 5px;
        margin-bottom: 0px;
    }
    .svg-logo {
        width: 120px;
        height: 120px;
        overflow: visible !important;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 { transform-origin: center; animation: spinSlow 10s linear infinite; }
    .orbit-2 { transform-origin: center; animation: spinReverse 7s linear infinite; }
    .core-glow { transform-origin: center; animation: pulseCore 2s infinite alternate; }
    @keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes spinReverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 8px rgba(168, 85, 247, 0.5)); }
        100% { filter: drop-shadow(0 0 22px rgba(56, 189, 248, 0.9)); }
    }
    @keyframes pulseCore { 0% { transform: scale(0.9); opacity: 0.7; } 100% { transform: scale(1.1); opacity: 1; } }

    .logo-text {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 6px;
        color: #38bdf8;
        margin-top: 8px;
        margin-bottom: 6px;
        text-transform: uppercase;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
    }

    .hero-title {
        text-align: center;
        font-size: 36px;
        font-weight: 400;
        color: #1f1f1f;
        margin-top: 10px;
        margin-bottom: 30px;
        letter-spacing: -0.5px;
    }

    .user-profile-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        font-size: 12px;
        color: #3c4043;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    </style>
""", unsafe_allow_html=True)

AUTHORIZED_USERS = [
    {"name": "วรกันต์ ยาคำ", "email": "vorakangm@gmail.com", "role": "Sovereign Administrator"},
    {"name": "การัณยภาส ยาคำ", "email": "karanyapas@yakham.com", "role": "Authorized Executive"}
]

if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None
if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
if "verified_name" not in st.session_state:
    st.session_state.verified_name = ""
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-4Hz", rate="+0%")
    await communicate.save(output_path)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Google AI Studio")
    st.caption("Zyphere Sovereign Core Engine")
    st.markdown("---")
    
    if not st.session_state.is_verified:
        st.markdown("#### Sovereign Access")
        selected_user_name = st.selectbox("เลือกผู้มีสิทธิ์เข้าถึง:", [u["name"] for u in AUTHORIZED_USERS])
        input_email = st.text_input("ยืนยันอีเมลส่วนตัว", placeholder="user@gmail.com")
        
        if st.button("Unlock System", type="primary", use_container_width=True):
            matched_user = next((u for u in AUTHORIZED_USERS if u["name"] == selected_user_name and u["email"].strip().lower() == input_email.strip().lower()), None)
            if matched_user:
                st.session_state.is_verified = True
                st.session_state.verified_name = matched_user["name"]
                st.rerun()
            else:
                st.error("Access Denied: อีเมลไม่ตรงกับสิทธิ์เด็ดขาด")
        st.markdown("---")
    else:
        speaker_name = st.session_state.verified_name
        st.markdown(f"""
            <div class="user-profile-card">
                <b>Active Session:</b><br>
                {speaker_name}<br>
                <small style="color:#70757a;">Sovereign Security Level 1</small>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()
        st.markdown("---")

    st.markdown("**EXPLORE**")
    st.markdown("📄 Playground")
    st.markdown("🕒 History")
    
    st.markdown("**BUILD**")
    st.markdown("➕ **New app**")
    st.markdown("▦ My apps")
    st.markdown("🖼️ Gallery")
    
    st.markdown("**MANAGE**")
    st.markdown("📈 Dashboard")
    st.markdown("📑 Documentation")

if not st.session_state.is_verified:
    st.info("กรุณายืนยันตัวตนด้วยอีเมลที่แถบควบคุมด้านซ้ายเพื่อเปิดใช้งาน Zyphere Studio")
    st.stop()

speaker_name = st.session_state.verified_name

# --- MAIN CENTER ---
st.markdown('''
    <div class="logo-container">
        <svg class="svg-logo" viewBox="-20 -20 140 140" xmlns="http://www.w3.org/2000/svg">
            <g class="orbit-2"><ellipse cx="50" cy="50" rx="46" ry="18" fill="none" stroke="#a855f7" stroke-width="2.5" opacity="0.85"/></g>
            <g class="orbit-1"><ellipse cx="50" cy="50" rx="18" ry="46" fill="none" stroke="#38bdf8" stroke-width="2.5" opacity="0.85"/></g>
            <circle class="core-glow" cx="50" cy="50" r="14" fill="#38bdf8" opacity="0.5"/>
            <circle cx="50" cy="50" r="6" fill="#ffffff"/>
        </svg>
        <div class="logo-text">ZYPHERE</div>
    </div>
    <div class="hero-title">Build your ideas with Zyphere</div>
''', unsafe_allow_html=True)

# เล่นเสียงอัตโนมัติแบบซ่อน (Invisible Autoplay Audio)
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    with open(st.session_state.latest_audio, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}"></audio>', unsafe_allow_html=True)

def native_jarvis_brain(cmd):
    cmd_lower = cmd.lower()
    if any(k in cmd_lower for k in ["ความสามารถ", "ทำอะไรได้บ้าง", "เธอทำอะไร", "ระบบมีอะไรบ้าง"]):
        return "สถาปัตยกรรมระบบครอบคลุม 4 แกนหลักระดับเอลีท ได้แก่ องคาพยพความรู้อจักรวาล, อากาศพลศาสตร์และ CAD, หุ่นยนต์อัตโนมัติ IoT, และระบบเผยแพร่คอนเทนต์อัตโนมัติครับ"
    elif any(k in cmd_lower for k in ["ยานอวกาศ", "หุ่นยนต์", "เครื่องจักร", "gcode", "g-code", "cad", "ออกแบบ"]):
        return "กำลังสังเคราะห์พิมพ์เขียววิศวกรรมและชุดคำสั่งจีโค้ดสำหรับโครงสร้างโลหะผสมไทเทเนียมกราฟีนเรียบร้อยแล้วครับ"
    elif any(k in cmd_lower for k in ["เดินป่า", "วิดีโอ", "facebook", "tiktok", "youtube"]):
        return "ระบบอัตโนมัติ Cross-Platform กำลังสร้างวิดีโอและเผยแพร่ลงโซเชียลมีเดียให้คุณทันทีครับ"
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ระบบ Zyphere พร้อมรับบัญชาการครับ"
    else:
        return f"รับทราบคำสั่งครับคุณ {speaker_name} กำลังประมวลผลข้อมูลผ่านโครงข่ายประสาทเทียมของ Zyphere ทันทีครับ"

def process_command(cmd):
    if not cmd:
        return
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"[KILL-SWITCH ACTIVATED]: ตัดการทำงานทันทีตามคำสั่งคุณ {speaker_name}")
        st.stop()

    response_msg = native_jarvis_brain(cmd)
    st.session_state.messages.append({"role": "user", "content": cmd})

    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        msg = MIMEText(f"รายงานการปฏิบัติการ Zyphere:\n\nผู้สั่งการ: {speaker_name}\nคำสั่ง: {cmd}\nผลการวิเคราะห์: {response_msg}")
        msg['Subject'] = f"Zyphere Report: {speaker_name}"
        msg['From'] = sender_email
        msg['To'] = "vorakangm@gmail.com"
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, "vorakangm@gmail.com", msg.as_string())
    except:
        pass

    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except:
        st.session_state.latest_audio = None

# --- CHAT INPUT ---
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pop("pending_prompt")
    process_command(prompt)
    st.rerun()

user_input = st.chat_input("Describe an app and let Zyphere do the rest")
if user_input:
    process_command(user_input)
    st.rerun()

# --- QUICK SHORTCUT PILLS ด้านล่าง ---
st.markdown("<br>", unsafe_allow_html=True)
p1, p2, p3, p4, p5 = st.columns(5)
with p1:
    if st.button("🤖 Build an Android app", use_container_width=True):
        st.session_state.pending_prompt = "ออกแบบแอปพลิเคชัน Android อัจฉริยะ"
        st.rerun()
with p2:
    if st.button("📍 Google Maps Integration", use_container_width=True):
        st.session_state.pending_prompt = "เชื่อมต่อระบบนำทางและข้อมูลแผนที่ Google Maps"
        st.rerun()
with p3:
    if st.button("🎮 Create a game", use_container_width=True):
        st.session_state.pending_prompt = "สร้างเกมจำลองฟิสิกส์ 3 มิติ"
        st.rerun()
with p4:
    if st.button("🌐 Three.js 3D scenes", use_container_width=True):
        st.session_state.pending_prompt = "สร้างฉากจำลองโมเดล 3D ด้วย Three.js"
        st.rerun()
with p5:
    if st.button("🛰️ Aerospace CAD Design", use_container_width=True):
        st.session_state.pending_prompt = "ออกแบบพิมพ์เขียวชิ้นส่วนยานอวกาศ"
        st.rerun()
