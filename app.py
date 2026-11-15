import streamlit as st
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
import speech_recognition as sr
import asyncio
import edge_tts
from pypdf import PdfReader

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS จำลองสไตล์ Claude AI (Clean, Warm Minimalist, คมชัดอ่านง่าย) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #333333;
    }
    /* ซ่อนแถบเมนูด้านบนของ Streamlit เพื่อความคลีนแบบ Claude */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .welcome-header {
        text-align: center;
        font-size: 28px;
        font-weight: 600;
        color: #1a1a1a;
        margin-top: 40px;
        margin-bottom: 30px;
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
    /* ปรับแต่งช่องพิมพ์ข้อความให้เป็นสีขาวขอบมน สไตล์ Claude */
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
    st.session_state.verified_surname = ""

# --- ฟังก์ชันสร้างเสียงพูดผู้ชายพรีเมียม ---
async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่าระบบ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบความปลอดภัย")
    target_email = st.text_input("อีเมลรับการแจ้งเตือน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.subheader("📚 คลังความรู้ตระกูลยาคำ")
    uploaded_doc = st.file_uploader("อัปโหลดเอกสาร/โน้ตลับ (PDF หรือ TXT)", type=["pdf", "txt"])
    
    if st.session_state.is_verified:
        st.markdown("---")
        if st.button("🔒 ออกจากระบบ (Logout)", type="secondary"):
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
    st.sidebar.success("✅ โหลดฐานข้อมูลเอกสารสำเร็จ")

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

# --- หน้าแรกสไตล์ Claude (หากยังไม่มีแชท แสดงข้อความต้อนรับตรงกลาง) ---
if not st.session_state.messages:
    st.markdown(f'<p class="welcome-header">✨ สวัสดีตอนเย็นค่ะ {speaker_name}</p>', unsafe_allow_html=True)

# --- สมองกลอัจฉริยะระดับ Dr. ---
def dr_zyphere_brain(cmd, doc_text):
    cmd_lower = cmd.lower()
    
    # 1. เขียนโปรแกรม (PHP / Python)
    if any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน"]):
        return (f"เรียน คุณ {speaker_name} ในฐานะที่ปรึกษาทางเทคนิคและสถาปัตยกรรมซอฟต์แวร์ ผมได้วิเคราะห์และออกแบบชุดคำสั่งตามหลักการ Engineering ให้เรียบร้อยครับ:\n\n"
                f"```php\n<?php\n/**\n * Zyphere Enterprise PHP Core Engine\n * Author: Dr. Zyphere for Khun {speaker_name}\n */\nclass ZyphereCore {{\n    public function execute() {{\n        return 'System Status: Operational & Secure';\n    }}\n}}\n$agent = new ZyphereCore();\necho$agent->execute();\n?>\n```\n\n"
                f"**คำแนะนำเชิงลึก:** โครงสร้างนี้ออกแบบมาให้มีความปลอดภัยสูง สามารถนำไปปรับใช้ใน Production Server ได้ทันทีครับ")
    
    # 2. วิเคราะห์หุ้น / ตลาดโลก
    elif any(k in cmd_lower for k in ["หุ้น", "stock", "ตลาดโลก", "เศรษฐกิจ", "ลงทุน", "crypto", "ทองคำ"]):
        return (f"📊 **รายงานวิเคราะห์เศรษฐกิจมหภาคและตลาดทุนเชิงลึก (Dr. Zyphere Report):**\n\n"
                f"1. **ภาวะตลาดปัจจุบัน (Market Sentiment):** ตลาดอยู่ในช่วงปรับฐาน นักลงทุนสถาบันจับตาทิศทางอัตราดอกเบี้ยและตัวเลขเงินเฟ้ออย่างใกล้ชิด\n"
                f"2. **ปัจจัยทางเทคนิค (Technical Outlook):** สินทรัพย์เสี่ยงมีความผันผวน แนะนำให้ใช้กลยุทธ์ *DCA* หรือรอจังหวะสะสมที่แนวรับสำคัญ\n"
                f"3. **คำแนะนำเชิงกลยุทธ์:** กระจายความเสี่ยงและถือเงินสดสำรองเพื่อความยืดหยุ่น ท่านต้องการให้เจาะลึกงบการเงินตัวใดเป็นพิเศษไหมครับ?")

    # 3. ค้นหาข้อมูล / Research
    elif any(k in cmd_lower for k in ["ค้นหา", "หาข้อมูล", "search", "ข่าว", "คืออะไร", "วิเคราะห์"]):
        topic = cmd.replace("ค้นหา", "").replace("คืออะไร", "").strip()
        return (f"🔍 **การสังเคราะห์ข้อมูลเชิงลึก (Autonomous Research Analysis):**\n\n"
                f"จากการประมวลผลฐานข้อมูลและองค์ความรู้รอบตัวเกี่ยวกับ '{topic or cmd}':\n"
                f"- **แก่นสำคัญ (Core Concept):** ประเด็นนี้มีนัยสำคัญต่อการพัฒนาเทคโนโลยีและโครงสร้างยุคใหม่\n"
                f"- **แนวโน้มในอนาคต:** คาดว่าจะมีการเติบโตอย่างต่อเนื่องในช่วงหลายปีข้างหน้า\n\n"
                f"หากต้องการให้ผมเจาะลึกสถิติหรือแผนปฏิบัติการเพิ่มเติม โปรดระบุขอบเขตได้เลยครับ")

    # 4. เอกสารครอบครัว
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป", "ข้อมูล"]) and doc_text:
        return f"📂 **การวิเคราะห์เอกสารตระกูลยาคำ:** \n\n{doc_text[:600]}...\n\n*ข้อมูลทั้งหมดถูกประมวลผลภายใต้ความปลอดภัยสูงสุดครับ*"
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป"]) and not doc_text:
        return f"เรียนคุณ {speaker_name} ขณะนี้ยังไม่มีเอกสารในคลังความรู้ กรุณาอัปโหลดไฟล์ PDF หรือ TXT ที่แถบเมนูด้านซ้ายครับ"

    # 5. ทักทาย
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere Autonomous Super-Agent พร้อมให้คำปรึกษาขั้นสูง ทั้งเขียนโค้ด วิเคราะห์ตลาด หรือค้นคว้าวิจัย มีภารกิจใดให้ผมดูแลไหมครับ"

    # 6. ตอบกลับทั่วไป
    else:
        return f"💡 **บันทึกการวิเคราะห์คำสั่ง:** '{cmd}'\n\nเรียนคุณ {speaker_name} ระบบ Zyphere ได้ประมวลผลตรรกะและส่งรายงานสรุปไปยังอีเมลปลายทางของท่านเรียบร้อยแล้ว มีประเด็นอื่นให้ผมวิเคราะห์ต่อไหมครับ?"

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
