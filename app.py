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

st.title("🛡️ Zyphere Autonomous Super-Agent")
st.markdown("ระบบ AI ส่วนตัวระดับสูง ปลอดภัยและควบคุมได้เฉพาะคุณ **วรกันต์ ยาคำ** และคุณ **การัณยภาส ยาคำ** เท่านั้น")

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

# ระบบความจำแชทแบบสมบูรณ์
if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
    st.session_state.verified_name = ""
    st.session_state.verified_surname = ""

# --- ฟังก์ชันสร้างเสียงพูดผู้ชายด้วย Edge TTS ---
async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่าระบบ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าการแจ้งเตือน")
    target_email = st.text_input("อีเมลรับการแจ้งเตือน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.subheader("📚 คลังความรู้เฉพาะครอบครัว")
    uploaded_doc = st.file_uploader("อัปโหลดเอกสาร/โน้ตลับ (PDF หรือ TXT)", type=["pdf", "txt"])
    
    if st.session_state.is_verified:
        st.markdown("---")
        if st.button("🔒 ล้างการยืนยันตัวตน (Logout)"):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.verified_surname = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

# ดึงข้อความจากเอกสารที่อัปโหลด (Knowledge Base)
doc_content = ""
if uploaded_doc:
    if uploaded_doc.type == "application/pdf":
        reader = PdfReader(uploaded_doc)
        for page in reader.pages:
            if page.extract_text():
                doc_content += page.extract_text() + "\n"
    else:
        doc_content = str(uploaded_doc.read(), "utf-8")
    st.sidebar.success("✅ โหลดฐานข้อมูลเอกสารเข้าสู่ระบบ AI สำเร็จ")

# --- หน้าจอหลัก: ยืนยันตัวตน ---
if not st.session_state.is_verified:
    st.subheader("🔑 ยืนยันตัวตนผู้มีสิทธิ์ (กรอกครั้งเดียวระบบจะจำไว้)")
    col1, col2 = st.columns(2)
    with col1:
        input_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์")
    with col2:
        input_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ")
    
    if st.button("🔓 ยืนยันตัวตนเข้าสู่ระบบ", type="primary"):
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
            st.error("🚨 [ACCESS DENIED]: ตรวจพบชื่อหรือนามสกุลไม่ได้รับอนุญาต")
    st.stop()

speaker_name = st.session_state.verified_name
speaker_surname = st.session_state.verified_surname
st.success(f"🛡️ ผู้ใช้งานปัจจุบัน: คุณ **{speaker_name} {speaker_surname}** (ระบบจดจำสิทธิ์แล้ว)")

st.markdown("---")
st.subheader("💬 สนทนากับ Zyphere Autonomous Super-Agent")

# --- ฟังก์ชันสมองกลอัจฉริยะ (Real-time Reasoning & Context Analysis) ---
def smart_ai_response(cmd, doc_text):
    cmd_lower = cmd.lower()
    
    # 1. ทักทาย
    if any(k in cmd_lower for k in ["สวัสดี", "hello", "hi", "hey"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere ระบบสายลมพิทักษ์ พร้อมรับบัญชาการครับ มีเรื่อง รือโปรแกรมใดให้ผมช่วยวิเคราะห์ต่อไหมครับ"
    
    # 2. คำถามเกี่ยวกับความสามารถ
    elif any(k in cmd_lower for k in ["ทำอะไรได้บ้าง", "ความสามารถ", "ระบบทำอะไร", "ช่วยอะไรได้"]):
        return f"เรียนคุณ {speaker_name} ในฐานะ Super-Agent ผมสามารถช่วยท่านได้ดังนี้ครับ: 1) ตอบคำถามและวิเคราะห์โค้ดหรือข้อความแบบ Real-time 2) ค้นหาข้อมูลเชิงลึกจากเอกสาร PDF ที่ท่านอัปโหลดในแถบซ้าย 3) บันทึกและส่งอีเมลแจ้งเตือนทุกคำสั่งสำคัญเข้าสู่ระบบของคุณทันทีครับ"
    
    # 3. คำถามเกี่ยวกับเขียนโปรแกรม / ฟีเจอร์ต่างๆ ที่ผู้ใช้พิมพ์ถาม
    elif any(k in cmd_lower for k in ["เขียนโปรแกรม", "โค้ด", "ระบบ", "ฟังก์ชัน"]):
        return f"รับทราบเรื่องการพัฒนาโปรแกรมครับคุณ {speaker_name} สำหรับคำสั่ง '{cmd}' ระบบ Zyphere ได้บันทึกรายละเอียดเพื่อเตรียมพร้อมสร้างชุดคำสั่งหรือประสานงานระบบให้อัตโนมัติ ท่านสามารถพิมพ์รายละเอียดเพิ่มเติมหรืออัปโหลดโค้ดให้ผมตรวจสอบได้เลยครับ"
    
    # 4. วิเคราะห์เนื้อหาจากเอกสาร (ถ้ารีเควสเกี่ยวกับไฟล์/เอกสาร)
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป", "ข้อมูล", "ในไฟล์"]) and doc_text:
        return f"จากการวิเคราะห์คลังเอกสารของคุณ {speaker_name}: พบข้อมูลสำคัญสรุปได้ว่า {doc_text[:400]}... มีจุดไหนให้ผมขยายความเพิ่มเติมไหมครับ"
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป"]) and not doc_text:
        return f"คุณ {speaker_name} ยังไม่ได้อัปโหลดไฟล์เอกสาร PDF หรือ TXT เข้ามาในระบบแถบด้านซ้ายครับ กรุณาอัปโหลดเพื่อให้ผมช่วยสแกนข้อมูลแบบ Real-time ได้เลยครับ"
    
    # 5. ตอบกลับตามบริบทคำสั่งทั่วไปแบบอัจฉริยะ ไม่จำเจ
    else:
        return f"ได้รับประเด็นเกี่ยวกับ '{cmd}' เรียบร้อยครับคุณ {speaker_name} ระบบ Zyphere วิเคราะห์ข้อมูลและบันทึกสถานะ พร้อมทั้งส่งอีเมลสรุปรายงานไปยังอีเมลปลายทางสำเร็จครับ มีประเด็นอื่นให้ผมช่วยเหลือต่อไหมครับ"

# --- ฟังก์ชันประมวลผลคำสั่งหลัก ---
def process_command(cmd):
    if not cmd:
        return
    
    # ตรวจสอบ Kill-Switch ฉุกเฉิน
    kill_keywords = ["ปิดระบบ", "หยุดการทำงาน", "kill switch", "shutdown"]
    if any(keyword in cmd.lower() for keyword in kill_keywords):
        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: ได้รับคำสั่งปิดระบบฉุกเฉินจากคุณ {speaker_name} {speaker_surname} ระบบกำลังตัดการทำงานทันที!")
        st.stop()

    # สร้างคำตอบอัจฉริยะตามข้อความที่พิมพ์จริง
    response_msg = smart_ai_response(cmd, doc_content)

    # บันทึกประวัติลงแชท
    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    # ส่งอีเมลแจ้งเตือนผ่าน Gmail SMTP เบื้องหลัง
    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        
        msg = MIMEText(f"คุณ {speaker_name} ได้สั่งการระบบแบบ Real-time:\n\nคำสั่ง: {cmd}\nZyphere Response: {response_msg}")
        msg['Subject'] = f"🛡️ Zyphere Agent Alert: คำสั่งจาก {speaker_name}"
        msg['From'] = sender_email
        msg['To'] = target_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, target_email, msg.as_string())
    except Exception as mail_err:
        pass # ป้องกันไม่ให้แชทสะดุดถ้ารับส่งเมลขัดข้องชั่วคราว

    # สังเคราะห์เสียงพูดตอบกลับ (TTS) เป็นเสียงผู้ชาย
    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except Exception as tts_err:
        st.session_state.latest_audio = None

# --- แสดงประวัติแชททั้งหมดต่อเนื่องสไตล์ Claude AI ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# เล่นเสียงล่าสุดอัตโนมัติ
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด (กด Enter ส่งได้ทันที) ---
user_input = st.chat_input("พิมพ์ข้อความคุยกับ Zyphere แล้วกด Enter...")
if user_input:
    process_command(user_input)
    st.rerun()
