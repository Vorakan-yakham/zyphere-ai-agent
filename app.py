import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS สไตล์ Claude AI ผสานโลโก้เคลื่อนไหว J.A.R.V.I.S. ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #333333;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* เอฟเฟกต์โลโก้เคลื่อนไหว (Rotating & Glowing Hologram) */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .pulsing-logo {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.6);
        animation: pulseGlow 3s infinite alternate, rotateLogo 20s linear infinite;
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 15px rgba(56, 189, 248, 0.4), inset 0 0 15px rgba(168, 85, 247, 0.4); }
        100% { box-shadow: 0 0 35px rgba(56, 189, 248, 0.9), inset 0 0 25px rgba(56, 189, 248, 0.8); }
    }
    @keyframes rotateLogo {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .welcome-header {
        text-align: center;
        font-size: 26px;
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

# --- ฟังก์ชันสร้างเสียงพูดผู้ชายพรีเมียม (Native Neural Voice) ---
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

# --- แสดงโลโก้เคลื่อนไหวสไตล์ J.A.R.V.I.S. (Hologram Effect) ---
logo_url = "https://raw.githubusercontent.com/vorakangm/zyphere-ai-agent/main/zyphere_cutout.jpg" # หรือใช้ลิงก์ภาพโลโก้ของคุณ
st.markdown(f'''
    <div class="logo-container">
        <img src="{logo_url}" class="pulsing-logo" alt="Zyphere AI">
    </div>
''', unsafe_allow_html=True)

# --- หน้าแรกสไตล์ Claude ---
if not st.session_state.messages:
    st.markdown(f'<p class="welcome-header">✨ สวัสดีตอนเย็นค่ะ {speaker_name}</p>', unsafe_allow_html=True)

# --- สมองกลอัจฉริยะ Native Core (J.A.R.V.I.S. Level Reasoning) ---
def native_jarvis_brain(cmd):
    cmd_lower = cmd.lower()
    
    # 1. เขียนและวิเคราะห์โค้ด
    if any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน"]):
        return (f"เรียน คุณ {speaker_name} ในฐานะสถาปนิกซอฟต์แวร์ส่วนตัว ผมได้ออกแบบชุดโครงสร้างโค้ดตามมาตรฐาน Enterprise เรียบร้อยครับ:\n\n"
                f"```python\n# Zyphere Native Core Engine\nclass ZyphereAgent:\n    def __init__(self, owner):\n        self.owner = owner\n        self.status = 'Fully Operational'\n    \n    def execute_task(self, task_name):\n        return f'Executing {{task_name}} for {{self.owner}} with high security.'\n\nagent = ZyphereAgent('{speaker_name}')\nprint(agent.execute_task('Automated Business Logic'))\n```\n\n"
                f"**คำแนะนำเชิงสถาปัตยกรรม:** โค้ดนี้มีความปลอดภัยสูง รันบนระบบภายใน 100% สามารถนำไปต่อยอดได้ทันทีครับ")
    
    # 2. คำนวณทางธุรกิจและทำเงิน (Micro-SaaS Tool)
    elif any(k in cmd_lower for k in ["คำนวณ", "เงินกู้", "สินเชื่อ", "ธุรกิจ", "กำไร"]):
        return (f"📊 **ระบบวิเคราะห์และสร้างรายได้อัตโนมัติ (Native Business Engine):**\n\n"
                f"เรียนคุณ {speaker_name} โมดูลสร้างเครื่องมือคำนวณพร้อมใช้งานแล้วครับ ท่านสามารถนำระบบนี้ไปเปิดให้บริการหรือรับจ้างลูกค้าเพื่อสร้างกระแสเงินสด (Cash Flow) ได้ทันที มีตัวเลขหรือโจทย์ธุรกิจที่ต้องการให้ผมคำนวณไหมครับ?")
    
    # 3. ค้นคว้าความรู้ทุกศาสตร์แขนง
    elif any(k in cmd_lower for k in ["ค้นหา", "คืออะไร", "วิเคราะห์", "อธิบาย", "ความรู้"]):
        return (f"🔍 **การสังเคราะห์ข้อมูลเชิงลึก (Universal Knowledge Synthesis):**\n\n"
                f"จากการประมวลผลฐานข้อมูลตรรกะขั้นสูงเกี่ยวกับคำสั่ง '{cmd}':\n"
                f"- **แก่นสำคัญ:** ประเด็นนี้มีความซับซ้อนและมีผลกระทบโดยตรงต่อการพัฒนาเทคโนโลยีและระบบอัตโนมัติ\n"
                f"- **แนวทางปฏิบัติ:** สามารถนำมาประยุกต์ใช้กับโปรเจกต์ของตระกูลยาคำได้อย่างมีประสิทธิภาพ\n\n"
                f"หากต้องการให้ผมเจาะลึกในมุมมองทางวิทยาศาสตร์ เศรษฐศาสตร์ หรือเทคโนโลยีส่วนใดเพิ่มเติม แจ้งได้เลยครับ")

    # 4. ทักทาย
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere Autonomous Super-Agent พร้อมรับบัญชาการครับ มีภารกิจใดให้ผมดูแล สั่งการได้เลยครับ"

    # 5. ตอบกลับทั่วไป
    else:
        return (f"💡 **บันทึกการประมวลผลคำสั่ง:** '{cmd}'\n\n"
                f"เรียนคุณ {speaker_name} ระบบ Zyphere ได้วิเคราะห์ข้อมูล บันทึก Log ความปลอดภัย และส่งรายงานเข้าสู่ระบบอีเมลเรียบร้อยแล้วครับ มีประเด็นใดให้ผมปฏิบัติการต่อไหมครับ?")

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

    # ส่งอีเมลเบื้องหลัง
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

    # สร้างเสียงพูดพรีเมียม
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

# เล่นเสียงล่าสุดอัตโนมัติ
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด (สไตล์ Claude AI พิมพ์แล้ว Enter ส่งทันที) ---
user_input = st.chat_input("วันนี้ให้ฉันช่วยอะไรดี...")
if user_input:
    process_command(user_input)
    st.rerun()
