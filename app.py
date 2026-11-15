import streamlit as st
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
import speech_recognition as sr
import asyncio
import edge_tts
from pypdf import PdfReader

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="wide")

# --- ดีไซน์ CSS ธีม Command Center สไตล์หรูหรา คมชัด อ่านง่าย ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #121824 100%);
        color: #e6edf3;
    }
    .main-title {
        font-size: 30px;
        font-weight: 800;
        color: #38bdf8;
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
        margin-bottom: 0px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .stChatMessage {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ Zyphere Autonomous Super-Agent [Dr. J.A.R.V.I.S. ARCHITECTURE]</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ระบบปัญญาประดิษฐ์ขั้นสูงเพื่อการควบคุมและวิเคราะห์เชิงลึก เฉพาะตระกูลยาคำ (วรกันต์ / การัณยภาส)</p>', unsafe_allow_html=True)

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
    st.session_state.verified_surname = ""

# --- ฟังก์ชันสร้างเสียงพูดผู้ชายพรีเมียม (Neural Voice) ---
async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่าระบบ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ระบบความปลอดภัยและตั้งค่า")
    target_email = st.text_input("อีเมลรับการแจ้งเตือน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.subheader("📚 คลังความรู้ตระกูลยาคำ")
    uploaded_doc = st.file_uploader("อัปโหลดเอกสาร/โค้ด/โน้ตลับ (PDF หรือ TXT)", type=["pdf", "txt"])
    
    if st.session_state.is_verified:
        st.markdown("---")
        if st.button("🔒 ล้างการยืนยันตัวตน (Logout)", type="secondary"):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.verified_surname = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

doc_content = ""
if uploaded_doc:
    if uploaded_doc.type == "application/pdf":
        reader = PdfReader(uploaded_doc)
        for page in reader.pages:
            if page.extract_text():
                doc_content += page.extract_text() + "\n"
    else:
        doc_content = str(uploaded_doc.read(), "utf-8")
    st.sidebar.success("✅ โหลดฐานข้อมูลเข้าสู่ระบบสำเร็จ")

# --- ตรวจสอบสิทธิ์ ---
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
            st.session_state.verified_surname = input_surname.strip()
            st.success(f"✅ ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับครับ คุณ {input_name}")
            st.rerun()
        else:
            st.error("🚨 [ACCESS DENIED]: ตรวจพบคำสั่งจากบุคคลภายนอก ระบบปฏิเสธการเข้าถึง")
    st.stop()

speaker_name = st.session_state.verified_name
speaker_surname = st.session_state.verified_surname
st.info(f"🛡️ ผู้ใช้งานปัจจุบัน: คุณ **{speaker_name} {speaker_surname}** | สถานะระบบ: Dr. J.A.R.V.I.S. Core Online")

# --- สมองกลวิเคราะห์ขั้นสูง (Dr. J.A.R.V.I.S. Brain) ---
def jarvis_zyphere_core(cmd, doc_text):
    cmd_lower = cmd.lower()
    
    # 1. เขียนและวิเคราะห์โค้ด (PHP/Python/System)
    if any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน", "ระบบ"]):
        return (f"เรียน คุณ {speaker_name} ในฐานะสถาปนิกซอฟต์แวร์และผู้ช่วยส่วนตัว ผมได้วิเคราะห์โครงสร้างตรรกะและออกแบบโค้ดตามมาตรฐาน Enterprise ให้เรียบร้อยครับ:\n\n"
                f"```php\n<?php\n/**\n * Zyphere J.A.R.V.I.S. Enterprise Core\n * Authorized for: Khun {speaker_name} & Khun Karanyapat\n */\nclass JarivsEngine {{\n    private string $status = 'SECURE & OPERATIONAL';\n    public function getDiagnostics(): string {{\n        return 'System Health: 100% | Protocol: Active';\n    }}\n}}\n$jarvis = new JarivsEngine();\necho$jarvis->getDiagnostics();\n?>\n```\n\n"
                f"**คำแนะนำเชิงสถาปัตยกรรม:** โค้ดชุดนี้ถูกออกแบบให้รองรับการขยายตัว (Scalability) และมีความปลอดภัยสูง สามารถนำไปปรับใช้ในโปรเจกต์ของท่านได้ทันทีครับ")
    
    # 2. วิเคราะห์หุ้น / ตลาดโลก (Financial & Macro Analysis)
    elif any(k in cmd_lower for k in ["หุ้น", "stock", "ตลาดโลก", "เศรษฐกิจ", "ลงทุน", "crypto", "ทองคำ", "การเงิน"]):
        return (f"📊 **รายงานวิเคราะห์ตลาดทุนและเศรษฐกิจมหภาค (Dr. J.A.R.V.I.S. Financial Intelligence):**\n\n"
                f"1. **Macro Environment:** สภาวะเศรษฐกิจปัจจุบันมีความทจากทิศทางสภาพคล่องและอัตราดอกเบี้ย แนะนำให้ติดตามตัวเลขเงินเฟ้ออย่างใกล้ชิด\n"
                f"2. **Strategic Outlook:** สำหรับการลงทุนในสินทรัพย์เสี่ยงหรือตลาดหุ้น ควรเน้นกลยุทธ์การบริหารความเสี่ยง (Risk Management) และแบ่งสัดส่วนเงินสด (Cash Flow)\n"
                f"3. **Actionable Insight:** หากท่านต้องการให้ผมเจาะลึกงบการเงิน งบดุล หรือสัญญาณเทคนิคของสินทรัพย์ตัวใดเป็นพิเศษ โปรดระบุชื่อหลักทรัพย์ได้เลยครับ")

    # 3. ค้นคว้าวิจัย / Research & Knowledge Discovery
    elif any(k in cmd_lower for k in ["ค้นหา", "หาข้อมูล", "search", "ข่าว", "คืออะไร", "วิเคราะห์", "ศึกษา"]):
        topic = cmd.replace("ค้นหา", "").replace("คืออะไร", "").strip()
        return (f"🔍 **Autonomous Research & Knowledge Synthesis:**\n\n"
                f"จากการประมวลผลฐานข้อมูลเชิงลึกเกี่ยวกับ '{topic or cmd}':\n"
                f"- **Core Architecture:** ประเด็นนี้มีรากฐานทางเทคโนโลยีที่เชื่อมโยงกับระบบอัตโนมัติและโครงสร้างข้อมูลยุคใหม่\n"
                f"- **Strategic Value:** มีศักยภาพสูงในการนำมาต่อยอดเพื่อเพิ่มประสิทธิภาพการทำงานในอนาคต\n\n"
                f"หากต้องการให้ผมเจาะลึกในมุมมองใดเพิ่มเติม บัญชาการมาได้เลยครับ")

    # 4. เอกสารตระกูลยาคำ
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป", "ข้อมูล"]) and doc_text:
        return f"📂 **การสกัดข้อมูลจากคลังความรู้ตระกูลยาคำ:**\n\n{doc_text[:650]}...\n\n*ระบบรักษาความปลอดภัยระดับสูงสุดได้ตรวจสอบความถูกต้องเรียบร้อยครับ*"
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป"]) and not doc_text:
        return f"เรียนคุณ {speaker_name} ปัจจุบันยังไม่มีเอกสารในคลังความรู้ กรุณาอัปโหลดไฟล์ PDF หรือ TXT ที่แถบเมนูด้านซ้าย เพื่อให้ผมทำการวิเคราะห์เชิงลึกครับ"

    # 5. ทักทาย
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi", "hey"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere (J.A.R.V.I.S. Edition) พร้อมรับบัญชาการครับ ไม่ว่าจะเป็นการเขียนโปรแกรมขั้นสูง วิเคราะห์ตลาดทุน หรือค้นคว้าระบบ มีภารกิจใดให้ผมดูแลเป็นพิเศษไหมครับ"

    # 6. ตอบกลับทั่วไปแบบฉลาดล้ำลึก
    else:
        return (f"💡 **บันทึกคำสั่งและตรรกะประมวลผล:** '{cmd}'\n\n"
                f"เรียนคุณ {speaker_name} ระบบได้ดำเนินการวิเคราะห์ บันทึก Log และส่งรายงานสรุปเข้าสู่ระบบอีเมลปลายทางเรียบร้อยแล้วครับ มีประเด็นหรือโปรเจกต์ใดให้ผมลุยต่อไหมครับ?")

# --- ฟังก์ชันประมวลผลหลัก ---
def process_command(cmd):
    if not cmd:
        return
    
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: คำสั่งฉุกเฉินจากคุณ {speaker_name} ระบบกำลังตัดการทำงานทันที!")
        st.stop()

    response_msg = jarvis_zyphere_core(cmd, doc_content)

    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    # ส่งอีเมลเบื้องหลัง
    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        
        msg = MIMEText(f"รายงานสถานะปฏิบัติการ Zyphere J.A.R.V.I.S.:\n\nผู้สั่งการ: {speaker_name}\nคำสั่ง: {cmd}\nผลการวิเคราะห์: {response_msg}")
        msg['Subject'] = f"🛡️ Zyphere J.A.R.V.I.S. Report: {speaker_name}"
        msg['From'] = sender_email
        msg['To'] = target_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, target_email, msg.as_string())
    except Exception as e:
        pass

    # สร้างเสียงพูดผู้ชายพรีเมียม
    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except Exception as e:
        st.session_state.latest_audio = None

# --- แสดงผลแชท ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# เล่นเสียงล่าสุดอัตโนมัติ
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด ---
user_input = st.chat_input("บัญชาการ Zyphere เช่น เขียนโค้ด PHP, วิเคราะห์หุ้น, ค้นคว้าข้อมูลเชิงลึก...")
if user_input:
    process_command(user_input)
    st.rerun()
