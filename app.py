import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(
    page_title="Zyphere Autonomous Super-Agent Studio", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ดีไซน์ CSS จำลองกล่อง Prompt Box สไตล์ Google AI Studio แบบเป๊ะๆ ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #1a1a1a;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    audio { display: none !important; }

    /* ปุ่มสไตล์ Monotone Minimalist */
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background-color: #333333 !important;
    }

    /* โลโก้ Neon Atom กลางหน้าจอ */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .svg-logo {
        width: 80px;
        height: 80px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 { transform-origin: center; animation: spinSlow 10s linear infinite; }
    .orbit-2 { transform-origin: center; animation: spinReverse 7s linear infinite; }
    .core-glow { transform-origin: center; animation: pulseCore 2s infinite alternate; }
    @keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes spinReverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.4)); }
        100% { filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.7)); }
    }
    @keyframes pulseCore { 0% { transform: scale(0.9); opacity: 0.7; } 100% { transform: scale(1.1); opacity: 1; } }

    .welcome-title {
        text-align: center;
        font-size: 26px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 20px;
    }

    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e5e5df !important;
        border-radius: 10px !important;
        padding: 14px !important;
        color: #1a1a1a !important;
        margin-bottom: 10px;
    }

    .user-profile-card {
        background-color: #f1f0ea;
        border: 1px solid #e0dfd5;
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
        color: #333333;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None
if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
    st.session_state.verified_name = ""
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-4Hz", rate="+0%")
    await communicate.save(output_path)

# --- 1. SIDEBAR ด้านซ้าย ---
with st.sidebar:
    st.markdown("### Zyphere Studio")
    st.caption("Autonomous Agent Control Hub")
    st.markdown("---")
    st.markdown("### การใช้งาน")
    st.markdown("- Playground")
    st.markdown("- History")
    st.markdown("- Engineering CAD")
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not st.session_state.is_verified:
        st.markdown("#### ยืนยันตัวตนเข้าใช้งาน")
        input_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์", key="sidebar_name")
        input_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ", key="sidebar_surname")
        if st.button("Unlock System", type="primary", use_container_width=True):
            is_authorized = any(
                user["name"].strip() == input_name.strip() and user["surname"].strip() == input_surname.strip()
                for user in AUTHORIZED_USERS
            )
            if is_authorized:
                st.session_state.is_verified = True
                st.session_state.verified_name = input_name.strip()
                st.rerun()
            else:
                st.error("Access Denied")
    else:
        speaker_name = st.session_state.verified_name
        st.markdown(f"""
            <div class="user-profile-card">
                <b>ผู้ใช้งานปัจจุบัน:</b><br>
                {speaker_name} ยาคำ<br>
                <small style="color:#666;">Sovereign Security Level 1</small>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

if not st.session_state.is_verified:
    st.info("กรุณายืนยันตัวตนที่แผงควบคุมด้านซ้ายล่างเพื่อเริ่มต้นใช้งานระบบ Zyphere")
    st.stop()

speaker_name = st.session_state.verified_name

# --- 2. RIGHT PANEL ด้านขวา (Settings) ---
main_col, right_col = st.columns([3.2, 1.2])

with right_col:
    st.markdown("### Run settings")
    st.caption("Engine: Zyphere Autonomous Neural Core")
    selected_tool = st.selectbox("โมดูลปฏิบัติการหลัก:", [
        "โมดูลคำนวณและออกแบบยานอวกาศ",
        "โมดูลสังเคราะห์ G-Code & CAD ชิ้นส่วน",
        "โมดูลควบคุมวงจรอิเล็กทรอนิกส์และหุ่นยนต์",
        "ระบบประเมินจุดคุ้มทุนธุรกิจอัตโนมัติ"
    ])
    st.markdown("---")
    st.markdown("### System Instructions")
    send_email_enabled = st.checkbox("เปิดใช้งานระบบส่งรายงานอีเมลอัตโนมัติ", value=False)
    target_email = st.text_input("อีเมลรับรายงาน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.markdown("### Thinking level")
    st.caption("High / Autonomous Discovery Enabled")

# --- 3. MAIN CENTER PANEL ตรงกลาง ---
with main_col:
    st.markdown('''
        <div class="logo-container">
            <svg class="svg-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <g class="orbit-2"><ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#a855f7" stroke-width="2" opacity="0.8"/></g>
                <g class="orbit-1"><ellipse cx="50" cy="50" rx="16" ry="42" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.8"/></g>
                <circle class="core-glow" cx="50" cy="50" r="12" fill="#38bdf8" opacity="0.5"/>
                <circle cx="50" cy="50" r="5" fill="#ffffff"/>
            </svg>
        </div>
    ''', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown(f'<div class="welcome-title">Build with Zyphere Autonomous Engine</div>', unsafe_allow_html=True)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
        st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# สมองกลอัจฉริยะ
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

    if send_email_enabled:
        try:
            sender_email = "vorakangm@gmail.com"
            app_password = "pygo tfga zubw xqca"
            msg = MIMEText(f"รายงานการปฏิบัติการ Zyphere:\n\nผู้สั่งการ: {speaker_name}\nคำสั่ง: {cmd}\nผลการวิเคราะห์: {response_msg}")
            msg['Subject'] = f"Zyphere Report: {speaker_name}"
            msg['From'] = sender_email
            msg['To'] = target_email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, target_email, msg.as_string())
        except:
            pass

    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except:
        st.session_state.latest_audio = None

# --- 4. FLOATING COMMAND BOX ด้านล่างสุด (ถอดแบบปุ่ม AI Studio ในภาพเป๊ะๆ)[cite: 6] ---
with main_col:
    st.markdown("---")
    
    # หากกดปุ่มไมโครโฟน ให้เปิดแผงบันทึกเสียง
    if st.session_state.voice_active:
        with st.container():
            st.markdown("🎙️ **ระบบบันทึกเสียงสนทนา (Voice Input Active)**")
            audio_data = st.audio_input("พูดคำสั่งของคุณเพื่อคุยกับ Zyphere")
            if audio_data is not None:
                st.success("บันทึกเสียงสำเร็จ! (พร้อมประมวลผลคำสั่งเสียง)")

    # ใช้ Form เพื่อจำลองกล่องแคปซูล Prompt Box ด้านล่าง
    with st.form(key="ai_studio_prompt_box", clear_on_submit=True):
        user_input = st.text_input("Start typing a prompt to see what our models can do", label_visibility="collapsed")
        
        c1, c2, c3, c4, c5, c6 = st.columns([0.6, 0.6, 1.2, 3.2, 0.8, 1.4])
        with c1:
            st.form_submit_button("➕")
        with c2:
            st.form_submit_button("👁️‍🗨️")
        with c3:
            st.form_submit_button("🛠️ Tools")
        with c4:
            st.markdown("<span style='font-size:12px; color:#555;'>✨ Zyphere Core Engine</span>", unsafe_allow_html=True)
        with c5:
            mic_btn = st.form_submit_button("🎙️")
        with c6:
            submitted = st.form_submit_button("Run Ctrl ↵", type="primary")
            
        if submitted and user_input:
            process_command(user_input)
            st.rerun()

    # ถ้าผู้ใช้กดปุ่มไอคอนไมโครโฟน (🎙️) ในฟอร์ม
    if mic_btn:
        st.session_state.voice_active = not st.session_state.voice_active
        st.rerun()
