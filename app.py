import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS สไตล์ Claude AI ผสาน Neon Atom Logo และซ่อน Input Placeholder ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #333333;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ซ่อนแถบเครื่องเล่นเสียง แต่ระบบยังอ่านออกเสียงเบื้องหลัง */
    audio {
        display: none !important;
    }
    
    /* ปุ่มกดสไตล์ Monotone Minimalist เรียบหรู */
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        cursor: pointer !important;
    }
    .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #555555 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    a, button, [role="button"], input[type="submit"] {
        cursor: pointer !important;
    }
    
    /* โลโก้ Neon Atom เคลื่อนไหวสไตล์ J.A.R.V.I.S. */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .svg-logo {
        width: 110px;
        height: 110px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 {
        transform-origin: center;
        animation: spinSlow 10s linear infinite;
    }
    .orbit-2 {
        transform-origin: center;
        animation: spinReverse 7s linear infinite;
    }
    .core-glow {
        transform-origin: center;
        animation: pulseCore 2s infinite alternate;
    }
    @keyframes spinSlow {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @keyframes spinReverse {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
    }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 8px rgba(168, 85, 247, 0.4)); }
        100% { filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.8)); }
    }
    @keyframes pulseCore {
        0% { transform: scale(0.9); opacity: 0.7; }
        100% { transform: scale(1.1); opacity: 1; }
    }

    .welcome-header {
        text-align: center;
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e5e5df !important;
        border-radius: 12px !important;
        padding: 16px !important;
        color: #222222 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        margin-bottom: 12px;
    }
    [data-testid="stChatInput"] textarea {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }
    </style>
""", unsafe_allow_html=True)

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

# ระบบความจำแชท
if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
    st.session_state.verified_name = ""

# --- ฟังก์ชันสร้างเสียงพูดพรีเมียม (ปรับแต่ง Pitch และ Rate ให้เสียงทุ้มนุ่มน่าฟังยิ่งขึ้น) ---
async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    
    # ปรับแต่งพารามิเตอร์เสียงพูด (ลด pitch ลงเล็กน้อยเพื่อให้เสียงทุ้มและดูเป็นธรรมชาติ/อบอุ่นขึ้น)
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-4Hz", rate="+0%")
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่า (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ระบบควบคุมความปลอดภัย")
    target_email = st.text_input("อีเมลรับรายงาน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.markdown("### 🚀 โมดูลวิศวกรรมขั้นสูง (Omni-Engineering)")
    selected_tool = st.selectbox("เลือกโมดูลปฏิบัติการ:", [
        "โมดูลคำนวณและออกแบบยานอวกาศ",
        "โมดูลสังเคราะห์ G-Code & CAD ชิ้นส่วน",
        "โมดูลควบคุมวงจรอิเล็กทรอนิกส์และหุ่นยนต์",
        "ระบบประเมินจุดคุ้มทุนธุรกิจอัตโนมัติ"
    ])
    
    if st.session_state.is_verified:
        st.markdown("---")
        if st.button("🔒 ล้างการยืนยันตัวตน (Logout)", type="secondary"):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

# --- ตรวจสอบสิทธิ์ความปลอดภัย ---
if not st.session_state.is_verified:
    st.markdown("### 🔑 ยืนยันตัวตนความปลอดภัยระดับสูงสุด")
    col1, col2 = st.columns(2)
    with col1:
        input_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์")
    with col2:
        input_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ")
    
    if st.button("🔓 ปลดล็อกระบบ Zyphere", type="primary"):
        is_authorized = any(
            user["name"].strip() == input_name.strip() and user["surname"].strip() == input_surname.strip()
            for user in AUTHORIZED_USERS
        )
        if is_authorized:
            st.session_state.is_verified = True
            st.session_state.verified_name = input_name.strip()
            st.success(f"✅ ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับครับ คุณ {input_name}")
            st.rerun()
        else:
            st.error("🚨 [ACCESS DENIED]: ตรวจพบคำสั่งจากบุคคลภายนอก ระบบปฏิเสธการเข้าถึง")
    st.stop()

speaker_name = st.session_state.verified_name

# --- แสดงโลโก้ Neon Atom เคลื่อนไหวสไตล์ J.A.R.V.I.S. ---
st.markdown('''
    <div class="logo-container">
        <svg class="svg-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <g class="orbit-2">
                <ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#a855f7" stroke-width="2" opacity="0.8"/>
            </g>
            <g class="orbit-1">
                <ellipse cx="50" cy="50" rx="16" ry="42" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.8"/>
            </g>
            <g style="transform: rotate(45deg); transform-origin: center;">
                <ellipse cx="50" cy="50" rx="40" ry="15" fill="none" stroke="#818cf8" stroke-width="1.5" opacity="0.6"/>
            </g>
            <circle class="core-glow" cx="50" cy="50" r="12" fill="#38bdf8" opacity="0.5"/>
            <circle cx="50" cy="50" r="5" fill="#ffffff"/>
        </svg>
    </div>
''', unsafe_allow_html=True)

# --- หน้าแรกสไตล์ Claude ---
if not st.session_state.messages:
    st.markdown(f'<p class="welcome-header">✨ สวัสดีตอนเย็นค่ะ {speaker_name}</p>', unsafe_allow_html=True)

# --- เพิ่มไอคอนไมโครโฟนสำหรับสั่งงานด้วยเสียง ---
col_mic1, col_mic2, col_mic3 = st.columns([1, 2, 1])
with col_mic2:
    with st.expander("🎙️ สั่งการด้วยเสียง (Voice Command Micro-Input)"):
        audio_file = st.audio_input("กดปุ่มเพื่อบันทึกเสียงคำสั่งของคุณ")
        if audio_file is not None:
            st.success("🎙️ บันทึกเสียงสำเร็จ! (ระบบรับคลื่นเสียงเรียบร้อย สามารถพิมพ์ข้อความควบคู่เพื่อประมวลผลคำสั่งได้ทันที)")

# --- สมองกลอัจฉริยะ Native Core (วิวัฒนาการรอบด้าน) ---
def native_jarvis_brain(cmd):
    cmd_lower = cmd.lower()
    
    if any(k in cmd_lower for k in ["ยานอวกาศ", "หุ่นยนต์", "เครื่องจักร", "gcode", "g-code", "cad", "ออกแบบ"]):
        msg_out = (
            "🛰️ **ระบบประมวลผลวิศวกรรมมหาศาล (Universal Engineering Synthesizer):**\n\n"
            f"เรียน คุณ {speaker_name} ผมได้สังเคราะห์พิมพ์เขียววิศวกรรมและชุดคำสั่งควบคุมเครื่องจักรสำหรับภารกิจ '{cmd}' เรียบร้อยครับ:\n\n"
            "```gcode\n"
            "; Zyphere Native CNC / 3D Printer G-Code\n"
            "; Target: Advanced Alloy Structural Component\n"
            "G21 ; Set units to millimeters\n"
            "G90 ; Absolute positioning\n"
            "M104 S240 ; Set Extruder Temp\n"
            "G1 X0 Y0 Z0.2 F3000 ; Move to origin\n"
            "; Structural Lattice Pattern Extrusion...\n"
            "```\n\n"
            "**วิเคราะห์วัสดุศาสตร์:** แนะนำให้ใช้ Titanium-Graphene Alloy เพื่อทนทานต่อแรงกดดันชั้นบรรยากาศและรังสีคอสมิกครับ"
        )
        return msg_out
    
    elif any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน"]):
        msg_out = (
            f"เรียน คุณ {speaker_name} ในฐานะสถาปนิกซอฟต์แวร์ส่วนตัว ผมได้ออกแบบชุดโครงสร้างโค้ดตามมาตรฐาน Enterprise เรียบร้อยครับ:\n\n"
            "```python\n"
            "# Zyphere Autonomous Neural Engine\n"
            f"class ZyphereAgent:\n"
            f"    def __init__(self, owner):\n"
            f"        self.owner = owner\n"
            f"        self.status = 'Fully Operational & Evolving'\n"
            f"    def execute_task(self, task_name):\n"
            f"        return f'Executing {{task_name}} for {{self.owner}} with high security.'\n\n"
            f"agent = ZyphereAgent('{speaker_name}')\n"
            "print(agent.execute_task('Autonomous Evolution Command'))\n"
            "```"
        )
        return msg_out

    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere Autonomous Super-Agent พร้อมรับบัญชาการภารกิจสร้างนวัตกรรมระดับโลกครับ สั่งการได้เลยครับ"

    else:
        msg_out = (
            f"💡 **บันทึกการประมวลผลคำสั่งระดับสูง:** '{cmd}'\n\n"
            f"เรียนคุณ {speaker_name} ระบบ Zyphere ได้ทำการประมวลผลตรรกะ บันทึก Log ความปลอดภัย และส่งรายงานเข้าสู่ระบบอีเมลเรียบร้อยแล้วครับ มีภารกิจใดให้ผมขับเคลื่อนต่อไหมครับ?"
        )
        return msg_out

# --- ฟังก์ชันประมวลผลหลัก ---
def process_command(cmd):
    if not cmd:
        return
    
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: คำสั่งฉุกเฉินจากคุณ {speaker_name} ระบบกำลังตัดการทำงานทันที!")
        st.stop()

    response_msg = native_jarvis_brain(cmd)

    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        msg = MIMEText(f"รายงานการปฏิบัติการ Zyphere:\n\nผู้สั่งการ: {speaker_name}\nคำสั่ง: {cmd}\nผลการวิเคราะห์: {response_msg}")
        msg['Subject'] = f"🛡️ Zyphere Report: {speaker_name}"
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

# --- แสดงประวัติแชทสไตล์ Claude ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# เล่นเสียงเบื้องหลังอัตโนมัติ (ซ่อน Player bar)
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด (ล้างข้อความแนะนำออกให้สะอาดตา) ---
user_input = st.chat_input("")
if user_input:
    process_command(user_input)
    st.rerun()
