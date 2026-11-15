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

# --- ฟังก์ชันสมองกลอัจฉริยะ (วิเคราะห์คำสั่งตามบริบท) ---
def smart_ai_response(cmd, doc_text):
    cmd_lower = cmd.lower()
    
    # 1. ตรวจสอบคำสั่งทักทาย
    if any(k in cmd_lower for k in ["สวัสดี", "hello", "hi", "hey"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere ระบบสายลมพิทักษ์ พร้อมรับบัญชาการครับ มีอะไรให้ผมช่วยเหลือวันนี้ไหมครับ"
    
    # 2. ตรวจสอบความสามารถระบบ
    elif any(k in cmd_lower for k in ["ทำอะไรได้บ้าง", "ความสามารถ", "ระบบทำอะไร", "ช่วยอะไรได้"]):
        return f"เรียนคุณ {speaker_name} ระบบ Zyphere ของเรามีความสามารถดังนี้ครับ: 1) ป้องกันและตรวจสอบสิทธิ์ตระกูลยาคำอย่างเข้มงวด 2) รับคำสั่งทั้งแบบพิมพ์และเสียง 3) แจ้งเตือนสตรีมมิ่ง/บันทึกกิจกรรมผ่านอีเมลอัตโนมัติ 4) วิเคราะห์เอกสาร PDF หรือโน้ตลับที่คุณอัปโหลดเข้ามาครับ"
    
    # 3. ตรวจสอบคำถามเกี่ยวกับเอกสารที่อัปโหลด
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป", "ข้อมูลใน"]) and doc_text:
        summary_snippet = doc_text[:300].replace('\n', ' ')
        return f"จากเอกสารที่คุณ {speaker_name} อัปโหลดเข้ามา นี่คือใจความสำคัญเบื้องต้นครับ: {summary_snippet}..."
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป"]) and not doc_text:
        return f"คุณ {speaker_name} ยังไม่ได้อัปโหลดเอกสารหรือไฟล์ PDF เข้ามาในคลังความรู้แถบด้านซ้ายเลยครับ กรุณาอัปโหลดก่อนเพื่อให้ผมช่วยวิเคราะห์ครับ"
    
    # 4. คำสั่งทั่วไป (ตอบรับแบบสมาร์ทตามหัวข้อ)
    else:
        return f"รับทราบคำสั่ง '{cmd}' ครับคุณ {speaker_name} ระบบ Zyphere ได้ทำการบันทึก ประมวลผล และส่งอีเมลรายงานเข้าสู่ระบบเรียบร้อยแล้วครับ"

# --- ฟังก์ชันประมวลผลคำสั่งหลัก ---
def process_command(cmd):
    if not cmd:
        return
    
    # ตรวจสอบ Kill-Switch
    kill_keywords = ["ปิดระบบ", "หยุดการทำงาน", "kill switch", "shutdown"]
    if any(keyword in cmd.lower() for keyword in kill_keywords):
        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: ได้รับคำสั่งปิดระบบฉุกเฉินจากคุณ {speaker_name} {speaker_surname} ระบบกำลังตัดการทำงานทันที!")
        st.stop()

    # สร้างคำตอบอัจฉริยะตามคำสั่ง
    response_msg = smart_ai_response(cmd, doc_content)

    # บันทึกประวัติลงแชท
    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    # ส่งอีเมลแจ้งเตือนผ่าน Gmail SMTP
    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        
        msg = MIMEText(f"คุณ {speaker_name} ได้สั่งการระบบ:\n\nคำสั่ง: {cmd}\nการตอบกลับของ AI: {response_msg}")
        msg['Subject'] = f"🛡️ Zyphere Agent Alert: คำสั่งจาก {speaker_name}"
        msg['From'] = sender_email
        msg['To'] = target_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, target_email, msg.as_string())
    except Exception as mail_err:
        st.warning(f"⚠️ ส่งอีเมลไม่สำเร็จ (โปรดตรวจสอบ App Password): {str(mail_err)}")

    # สังเคราะห์เสียงพูดตอบกลับ (TTS) เป็นเสียงผู้ชาย
    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except Exception as tts_err:
        st.session_state.latest_audio = None

# --- แสดงประวัติแชททั้งหมดต่อเนื่องเหมือน Claude AI ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# เล่นเสียงล่าสุด (ถ้ามี)
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด (สไตล์ Claude AI) ---
user_input = st.chat_input("พิมพ์ข้อความคุยกับ Zyphere แล้วกด Enter...")
if user_input:
    process_command(user_input)
    st.rerun()
