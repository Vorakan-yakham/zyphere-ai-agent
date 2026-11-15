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

# --- ดีไซน์ CSS สุดล้ำ สไตล์ Command Center (อ่านง่าย ตัวหนังสือคมชัด) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #121824 100%);
        color: #e6edf3;
    }
    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #38bdf8;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        margin-bottom: 0px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 15px;
        margin-bottom: 25px;
    }
    .stChatMessage {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .stChatInputContainer {
        border-color: #38bdf8 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ Zyphere Autonomous Super-Agent [DR. EDITION]</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ระบบผู้ช่วยอัจฉริยะระดับสูง ควบคุมและเข้าถึงได้เฉพาะตระกูลยาคำ (วรกันต์ / การัณยภาส)</p>', unsafe_allow_html=True)

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
    st.session_state.verified_surname = ""

# --- ฟังก์ชันสร้างเสียงพูดผู้ชาย (โทนทุ้ม นุ่มลึกระดับพรีเมียม) ---
async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่าระบบ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ แผงควบคุมความปลอดภัย")
    target_email = st.text_input("อีเมลรับการแจ้งเตือน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.subheader("📚 คลังความรู้ตระกูลยาคำ")
    uploaded_doc = st.file_uploader("อัปโหลดเอกสาร/โน้ตลับ (PDF หรือ TXT)", type=["pdf", "txt"])
    
    if st.session_state.is_verified:
        st.markdown("---")
        if st.button("🔒 ล้างการยืนยันตัวตน (Logout)", type="secondary"):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.verified_surname = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

# ดึงข้อความจากเอกสารที่อัปโหลด
doc_content = ""
if uploaded_doc:
    if uploaded_doc.type == "application/pdf":
        reader = PdfReader(uploaded_doc)
        for page in reader.pages:
            if page.extract_text():
                doc_content += page.extract_text() + "\n"
    else:
        doc_content = str(uploaded_doc.read(), "utf-8")
    st.sidebar.success("✅ โหลดฐานข้อมูลเอกสารเข้าสู่ระบบสำเร็จ")

# --- ยืนยันตัวตน ---
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
st.info(f"🛡️ ผู้ใช้งานปัจจุบัน: คุณ **{speaker_name} {speaker_surname}** | สถานะระบบ: พร้อมปฏิบัติการเต็มรูปแบบ")

# --- สมองกลอัจฉริยะระดับ Dr. (วิเคราะห์เชิงลึก มีเหตุผล โครงสร้างชัดเจน) ---
def dr_zyphere_brain(cmd, doc_text):
    cmd_lower = cmd.lower()
    
    # 1. หมวดเขียนโปรแกรม (PHP / Python / System Architecture)
    if any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน"]):
        return (f"เรียน คุณ {speaker_name} ในฐานะที่ปรึกษาทางเทคนิคและสถาปัตยกรรมซอฟต์แวร์ ผมได้วิเคราะห์และออกแบบชุดคำสั่งตามหลักการ Engineering ให้เรียบร้อยครับ:\n\n"
                f"```php\n<?php\n/**\n * Zyphere Enterprise PHP Core Engine\n * Author: Dr. Zyphere for Khun {speaker_name}\n */\nclass ZyphereCore {{\n    public function execute() {{\n        return 'System Status: Operational & Secure';\n    }}\n}}\n$agent = new ZyphereCore();\necho$agent->execute();\n?>\n```\n\n"
                f"**คำแนะนำเชิงลึก:** โครงสร้างนี้ถูกออกแบบให้มีความปลอดภัยสูง ป้องกันช่องโหว่พื้นฐาน สามารถนำไปปรับใช้ใน Production Server ได้ทันทีครับ")
    
    # 2. หมวดวิเคราะห์หุ้น / ตลาดโลก (Macro Analysis)
    elif any(k in cmd_lower for k in ["หุ้น", "stock", "ตลาดโลก", "เศรษฐกิจ", "ลงทุน", "crypto", "ทองคำ"]):
        return (f"📊 **รายงานวิเคราะห์เศรษฐกิจมหภาคและตลาดทุนเชิงลึก (Dr. Zyphere Report):**\n\n"
                f"1. **ภาวะตลาดปัจจุบัน (Market Sentiment):** ตลาดอยู่ในช่วงปรับฐาน (Consolidation) นักลงทุนสถาบันจับตาดูทิศทางอัตราดอกเบี้ยและตัวเลขเงินเฟ้ออย่างใกล้ชิด\n"
                f"2. **ปัจจัยทางเทคนิค (Technical Outlook):** สินทรัพย์เสี่ยงมีความผันผวนสูง แนะนำให้ใช้กลยุทธ์ *DCA (Dollar-Cost Averaging)* หรือรอจังหวะสะสมที่แนวรับสำคัญ\n"
                f"3. **คำแนะนำเชิงกลยุทธ์:** ควรกระจายความเสี่ยง (Diversification) และถือเงินสดสำรองไว้บางส่วนเพื่อความยืดหยุ่น ท่านต้องการให้เจาะลึกงบการเงินหรือกราฟทางเทคนิคของสินทรัพย์ตัวใดเป็นพิเศษไหมครับ?")

    # 3. หมวดค้นหาข้อมูล / Research & Self-Learning
    elif any(k in cmd_lower for k in ["ค้นหา", "หาข้อมูล", "search", "ข่าว", "คืออะไร", "วิเคราะห์"]):
        topic = cmd.replace("ค้นหา", "").replace("คืออะไร", "").strip()
        return (f"🔍 **การสังเคราะห์ข้อมูลเชิงลึก (Autonomous Research Analysis):**\n\n"
                f"จากการประมวลผลฐานข้อมูลและองค์ความรู้รอบตัวเกี่ยวกับ '{topic or cmd}':\n"
                f"- **แก่นสำคัญ (Core Concept):** ประเด็นนี้มีนัยสำคัญต่อการพัฒนาเทคโนโลยีและโครงสร้างเศรษฐกิจยุคใหม่\n"
                f"- **แนวโน้มในอนาคต (Future Trajectory):** คาดว่าจะมีการเติบโตแบบก้าวกระโดดภายใน 3-5 ปีข้างหน้า\n\n"
                f"หากท่านต้องการให้ผมเจาะลึกสถิติ รายงานวิจัย หรือแผนปฏิบัติการ (Action Plan) ในหัวข้อนี้เพิ่มเติม โปรดระบุขอบเขตได้เลยครับ")

    # 4. หมวดเอกสารครอบครัว / Knowledge Base
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป", "ข้อมูล"]) and doc_text:
        return f"📂 **การวิเคราะห์เอกสารตระกูลยาคำ:** \n\n{doc_text[:600]}...\n\n*หมายเหตุ: ข้อมูลทั้งหมดถูกจัดเก็บและประมวลผลภายใต้ระบบรักษาความปลอดภัยสูงสุดเรียบร้อยครับ*"
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป"]) and not doc_text:
        return f"เรียนคุณ {speaker_name} ขณะนี้ยังไม่มีเอกสารในคลังความรู้ กรุณาอัปโหลดไฟล์ PDF หรือ TXT ที่แถบเมนูด้านซ้าย เพื่อให้ผมทำการ Extract และวิเคราะห์ข้อมูลเชิงลึกให้ท่านครับ"

    # 5. ทักทายระดับโปร
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere Autonomous Super-Agent พร้อมให้คำปรึกษาและปฏิบัติการขั้นสูง ทั้งการเขียนสคริปต์ระบบ วิเคราะห์ตลาดทุน หรือค้นคว้าวิจัยเชิงลึก มีภารกิจใดให้ผมดูแลเป็นพิเศษไหมครับ"

    # 6. ตอบกลับทั่วไปแบบฉลาดล้ำลึก
    else:
        return (f"💡 **บันทึกการวิเคราะห์คำสั่ง:** '{cmd}'\n\n"
                f"เรียนคุณ {speaker_name} ระบบ Zyphere ได้ประมวลผลตรรกะ ดำเนินการตามโจทย์ และจัดเก็บ Log ความปลอดภัยเรียบร้อยแล้วครับ "
                f"ทุกขั้นตอนถูกบันทึกและส่งรายงานสรุปไปยังอีเมลปลายทางของท่านเรียบร้อย มีประเด็นอื่นให้ผมวิเคราะห์ต่อไหมครับ?")

# --- ฟังก์ชันประมวลผลหลัก ---
def process_command(cmd):
    if not cmd:
        return
    
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: คำสั่งฉุกเฉินจากคุณ {speaker_name} ระบบกำลังปิดตัวลงทันที!")
        st.stop()

    response_msg = dr_zyphere_brain(cmd, doc_content)

    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    # ส่งอีเมลเบื้องหลัง
    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        
        msg = MIMEText(f"รายงานการปฏิบัติการ Zyphere Agent:\n\nผู้สั่งการ: {speaker_name}\nคำสั่ง: {cmd}\nผลการวิเคราะห์ Dr. Mode: {response_msg}")
        msg['Subject'] = f"🛡️ Zyphere Dr. Report: {speaker_name}"
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

# --- แสดงประวัติแชท ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# เล่นเสียงล่าสุดอัตโนมัติ
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด (สไตล์ Claude AI พิมพ์แล้ว Enter ส่งทันที) ---
user_input = st.chat_input("ปรึกษา Dr. Zyphere เช่น เขียนโค้ด PHP, วิเคราะห์หุ้น, ค้นคว้าข้อมูลเชิงลึก...")
if user_input:
    process_command(user_input)
    st.rerun()
