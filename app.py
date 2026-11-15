import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS สไตล์ Claude AI ผสานโลโก้เวกเตอร์เคลื่อนไหวพรีเมียม ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #333333;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
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
    }
    .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #555555 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* โลโก้เวกเตอร์เคลื่อนไหวสไตล์ J.A.R.V.I.S. (SVG Animation) */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 25px;
        margin-bottom: 10px;
    }
    .svg-logo {
        width: 110px;
        height: 110px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 {
        transform-origin: center;
        animation: spinSlow 12s linear infinite;
    }
    .orbit-2 {
        transform-origin: center;
        animation: spinReverse 8s linear infinite;
    }
    .core-dot {
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
        0% { filter: drop-shadow(0 0 5px rgba(0,0,0,0.1)); }
        100% { filter: drop-shadow(0 0 15px rgba(0,0,0,0.3)); }
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
        margin-bottom: 20px;
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

# --- ฟังก์ชันสร้างเสียงพูดผู้ชายพรีเมียม ---
async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่า (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ระบบควบคุมความปลอดภัย")
    target_email = st.text_input("อีเมลรับรายงาน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.markdown("### 💼 โมดูลสร้างเงิน (Micro-SaaS)")
    selected_tool = st.selectbox("เลือกเครื่องมือธุรกิจ:", [
        "ระบบคำนวณสินเชื่อและวางแผนการเงิน",
        "ระบบประเมินจุดคุ้มทุนร้านค้าออนไลน์"
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

# --- แสดงโลโก้เวกเตอร์เคลื่อนไหวสไตล์ J.A.R.V.I.S. (Monotone SVG) ---
st.markdown('''
    <div class="logo-container">
        <svg class="svg-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <!-- วงแหวนรอบนอกหมุนทวนเข็ม -->
            <g class="orbit-2">
                <ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#222222" stroke-width="1.5" stroke-dasharray="6 4"/>
            </g>
            <!-- วงแหวนรอบนอกหมุนตามเข็ม -->
            <g class="orbit-1">
                <ellipse cx="50" cy="50" rx="16" ry="42" fill="none" stroke="#111111" stroke-width="2"/>
            </g>
            <!-- วงแหวนกลาง -->
            <circle cx="50" cy="50" r="28" fill="none" stroke="#444444" stroke-width="1" stroke-dasharray="4 2"/>
            <!-- แกนกลางพลังงานกระพริบ -->
            <circle class="core-dot" cx="50" cy="50" r="10" fill="#1a1a1a"/>
            <circle cx="50" cy="50" r="4" fill="#ffffff"/>
        </svg>
    </div>
''', unsafe_allow_html=True)

# --- หน้าแรกสไตล์ Claude ---
if not st.session_state.messages:
    st.markdown(f'<p class="welcome-header">✨ สวัสดีตอนเย็นค่ะ {speaker_name}</p>', unsafe_allow_html=True)

# --- สมองกลอัจฉริยะ Native Core ---
def native_jarvis_brain(cmd):
    cmd_lower = cmd.lower()
    
    if any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน"]):
        return (f"เรียน คุณ {speaker_name} ในฐานะสถาปนิกซอฟต์แวร์ส่วนตัว ผมได้ออกแบบชุดโครงสร้างโค้ดตามมาตรฐาน Enterprise เรียบร้อยครับ:\n\n"
                f"```python\n# Zyphere Native Core Engine\nclass ZyphereAgent:\n    def __init__(self, owner):\n        self.owner = owner\n        self.status = 'Fully Operational'\n    \n    def execute_task(self, task_name):\n        return f'Executing {{task_name}} for {{self.owner}} with high security.'\n\nagent = ZyphereAgent('{speaker_name}')\nprint(agent.execute_task('Automated Business Logic'))\n```\n\n"
                f"**คำแนะนำเชิงสถาปัตยกรรม:** โค้ดนี้มีความปลอดภัยสูง รันบนระบบภายใน 100% สามารถนำไปต่อยอดได้ทันทีครับ")
    
    elif any(k in cmd_lower for k in ["คำนวณ", "เงินกู้", "สินเชื่อ", "ธุรกิจ", "กำไร"]):
        return (f"📊 **ระบบวิเคราะห์และสร้างรายได้อัตโนมัติ (Native Business Engine):**\n\n"
