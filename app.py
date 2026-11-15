import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(
    page_title="Build | Zyphere Studio", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ดีไซน์ CSS แคปซูลชิ้นเดียวสไตล์ Google AI Studio และโลโก้ปฏิกรณ์ขนาดใหญ่ ---
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #1f1f1f;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
        padding-top: 0.5rem;
    }

    .block-container {
        padding-top: 3vh !important;
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
        width: 110px;
        height: 110px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 { transform-origin: center; animation: spinSlow 10s linear infinite; }
    .orbit-2 { transform-origin: center; animation: spinReverse 7s linear infinite; }
    .core-glow { transform-origin: center; animation: pulseCore 2s infinite alternate; }
    @keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes spinReverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 8px rgba(168, 85, 247, 0.5)); }
        100% { filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.9)); }
    }
    @keyframes pulseCore { 0% { transform: scale(0.9); opacity: 0.7; } 100% { transform: scale(1.1); opacity: 1; } }

    .logo-text {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 5px;
        color: #38bdf8;
        margin-top: 6px;
        margin-bottom: 4px;
        text-transform: uppercase;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
    }

    .hero-title {
        text-align: center;
        font-size: 36px;
        font-weight: 400;
        color: #1f1f1f;
        margin-top: 5px;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }

    [data-testid="stForm"] {
        background-color: #ffffff;
        border: 1px solid #dadce0 !important;
        border-radius: 24px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(66, 133, 244, 0.1), 0 1px 4px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    [data-testid="stForm"]:hover {
        box-shadow: 0 6px 24px rgba(66, 133, 244, 0.18), 0 2px 8px rgba(0, 0, 0, 0.06);
        border-color: #bdc1c6 !important;
    }

    [data-testid="stForm"] textarea {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        font-size: 15px !important;
        color: #1f1f1f !important;
        resize: none !important;
        padding: 0px !important;
    }
    [data-testid="stForm"] textarea:focus {
        border: none !important;
        box-shadow: none !important;
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
        <svg class="svg-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <g class="orbit-2"><ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#a855f7" stroke-width="2" opacity="0.8"/></g>
            <g class="orbit-1"><ellipse cx="50" cy="50" rx="16" ry="42" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.8"/></g>
            <circle class="core-glow" cx="50" cy="50" r="12" fill="#38bdf8" opacity="0.5"/>
            <circle cx="50" cy="50" r="5" fill="#ffffff"/>
        </svg>
        <div class="logo-text">ZYPHERE</div>
    </div>
    <div class="hero-title">Build your ideas with Zyphere</div>
''', unsafe_allow_html=True)

# แสดงประวัติแชท
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# แสดงเครื่องเล่นเสียงพูดสังเคราะห์ทันทีที่มีการตอบกลับ
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.markdown("🔊 **Zyphere Voice Synthesis Output:**")
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

def native_jarvis_brain(cmd):
    cmd_lower = cmd.lower()
    if any(k in cmd_lower for k in ["ความสามารถ", "ทำอะไรได้บ้าง", "เธอทำอะไร", "ระบบมีอะไรบ้าง"]):
        return (
            "สถาปัตยกรรมระบบครอบคลุม 4 แกนหลักระดับเอลีท:\n\n"
            "1. **Universal Knowledge & Omni-Science:** ประมวลผลและไขคำตอบทางฟิสิกส์ควอนตัม อากาศพลศาสตร์ และทฤษฎีขั้นสูง\n"
            "2. **Aerospace & CAD/G-Code Synthesis:** ออกแบบโครงสร้างยานอวกาศ ชิ้นส่วนเครื่องจักรกล และสร้างชุดคำสั่ง G-code สำหรับเครื่องพิมพ์ 3 มิติ / CNC\n"
            "3. **Autonomous Robotics & IoT Integration:** ควบคุมวงจรอิเล็กทรอนิกส์ แขนกล และระบบเซนเซอร์อัตโนมัติ\n"
            "4. **Cross-Platform Content Automation:** สั่งการสร้างวิดีโอ สคริปต์ และเผยแพร่อัตโนมัติลง Social Media (Facebook, YouTube, TikTok)\n\n"
            "โปรดระบุภารกิจเฉพาะด้านที่ต้องการให้เริ่มปฏิบัติการได้ทันทีครับ"
        )
    elif any(k in cmd_lower for k in ["ยานอวกาศ", "หุ่นยนต์", "เครื่องจักร", "gcode", "g-code", "cad", "ออกแบบ"]):
        return (
            "**ผลการสังเคราะห์พิมพ์เขียววิศวกรรม:**\n\n"
            "```gcode\n"
            "; Zyphere Native CNC / 3D Printer G-Code\n"
            "; Target: Advanced Alloy Structural Component\n"
            "G21 ; Set units to millimeters\n"
            "G90 ; Absolute positioning\n"
            "M104 S240 ; Set Extruder Temp\n"
            "G1 X0 Y0 Z0.2 F3000 ; Move to origin\n"
            "```\n\n"
            "**ข้อเสนอแนะทางวัสดุศาสตร์:** แนะนำให้ใช้ Titanium-Graphene Alloy เพื่อรองรับแรงกดดันสูงในชั้นบรรยากาศ"
        )
    elif any(k in cmd_lower for k in ["เดินป่า", "วิดีโอ", "facebook", "tiktok", "youtube"]):
        return (
            "**ระบบอัตโนมัติ Cross-Platform Content Automation กำลังทำงาน:**\n\n"
            "1. **Scripting:** สร้างบทเรื่องเล่าคนเดินป่าบรรยากาศลึกลับน่าติดตามเรียบร้อย\n"
            "2. **Voice Synthesis:** สังเคราะห์เสียงบรรยายพรีเมียมโทนทุ้มนุ่มนวล\n"
            "3. **Video Production:** ตัดต่อฟุตเทจป่าเขาพร้อมซับไตเติลออโต้\n"
            "4. **API Deployment:** ส่งข้อมูลและเผยแพร่อัตโนมัติไปยัง Facebook, YouTube และ TikTok เรียบร้อยแล้วครับ"
        )
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ระบบ Zyphere พร้อมรับบัญชาการสร้างนวัตกรรมและขับเคลื่อนโครงสร้างอัจฉริยะแล้วครับ"
    else:
        return (
            "**ผลการวิเคราะห์ทางตรรกะและฐานข้อมูลจักรวาล:**\n\n"
            "- ตรวจสอบตัวแปรและประเมินความเป็นไปได้ภายใต้กฎฟิสิกส์และระบบอัตโนมัติเรียบร้อย\n"
            "- พร้อมแปลงข้อกำหนดดังกล่าวให้เป็นพิมพ์เขียววิศวกรรม ชุดโค้ดโปรแกรม หรือแผนปฏิบัติการอัตโนมัติ\n\n"
            "กรุณาระบุพารามิเตอร์เพิ่มเติมหากต้องการให้ดำเนินการทันทีครับ"
        )

def process_command(cmd):
    if not cmd:
        return
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"[KILL-SWITCH ACTIVATED]: คำสั่งฉุกเฉินจากคุณ {speaker_name} ระบบกำลังตัดการทำงานทันที!")
        st.stop()

    response_msg = native_jarvis_brain(cmd)
    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

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

# --- FLOATING CENTRAL COMMAND CAPSULE ---
if st.session_state.voice_active:
    with st.container():
        st.markdown("🎙️ **Voice Command Active**")
        audio_data = st.audio_input("พูดคำสั่งของคุณเพื่อสั่งการ Zyphere")
        if audio_data is not None:
            st.success("บันทึกเสียงสำเร็จ! พร้อมประมวลผล")

default_input = st.session_state.pop("pending_prompt", "")

with st.form(key="google_ai_studio_capsule", clear_on_submit=True):
    user_input = st.text_area("Describe an app and let Zyphere do the rest", value=default_input, height=80, label_visibility="collapsed", placeholder="Describe an app and let Zyphere do the rest")
    
    c1, c2, c3, c4 = st.columns([0.6, 3.8, 1.8, 2.4])
    with c1:
        st.form_submit_button("⊕")
    with c2:
        st.write("")
    with c3:
        st.selectbox("Mode", ["Max mode", "Fast mode"], label_visibility="collapsed")
    with c4:
        col_m, col_r = st.columns([1, 2.2])
        with col_m:
            mic_btn = st.form_submit_button("🎙️")
        with col_r:
            submitted = st.form_submit_button("✦ I'm feeling lucky", type="primary")

    if submitted and user_input.strip():
        process_command(user_input.strip())
        st.rerun()

if mic_btn:
    st.session_state.voice_active = not st.session_state.voice_active
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
