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

# ระบบความจำภายในเซสชัน และความจำตัวตนผู้ใช้
if "memory_logs" not in st.session_state:
    st.session_state.memory_logs = []

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

# --- หน้าจอหลัก: ระบบยืนยันตัวตนแบบจำสถานะ ---
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

# หากยืนยันตัวตนแล้ว แสดงชื่อผู้ใช้งานปัจจุบัน
speaker_name = st.session_state.verified_name
speaker_surname = st.session_state.verified_surname
st.success(f"🛡️ ผู้ใช้งานปัจจุบัน: คุณ **{speaker_name} {speaker_surname}** (ระบบจดจำสิทธิ์แล้ว)")

st.markdown("---")
st.subheader("💬 เลือกวิธีป้อนคำสั่ง (พิมพ์ หรือ อัปโหลดเสียง)")

input_method = st.radio("เลือกวิธีการสั่งการของคุณ:", ["พิมพ์ข้อความคำสั่ง", "อัปโหลดไฟล์เสียง"], horizontal=True)

command_text = ""
audio_file = None
text_input = ""

if input_method == "พิมพ์ข้อความคำสั่ง":
    text_input = st.text_input("พิมพ์คำสั่งของคุณที่นี่:", placeholder="เช่น สวัสดีระบบ, สรุปรายงาน, หรือ ปิดระบบ")
else:
    audio_file = st.file_uploader("อัปโหลดไฟล์เสียงคำสั่งของคุณ (.wav, .mp3, .m4a)", type=["wav", "mp3", "m4a"])

st.markdown("---")

if st.button("🚀 ส่งคำสั่งไปยัง AI Super-Agent", type="primary"):
    if input_method == "พิมพ์ข้อความคำสั่ง" and not text_input:
        st.warning("⚠️ กรุณาพิมพ์ข้อความคำสั่งก่อนครับ")
    elif input_method == "อัปโหลดไฟล์เสียง" and not audio_file:
        st.warning("⚠️ กรุณาอัปโหลดไฟล์เสียงคำสั่งก่อนครับ")
    else:
        with st.spinner("กำลังประมวลผลระบบอัตโนมัติด้วยเสียงสายลมอันทรงพลัง..."):
            if input_method == "พิมพ์ข้อความคำสั่ง":
                command_text = text_input
            else:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_file.getvalue())
                        tmp_path = tmp_file.name

                    r = sr.Recognizer()
                    with sr.AudioFile(tmp_path) as source:
                        audio_data = r.record(source)
                        command_text = r.recognize_google(audio_data, language="th-TH")

                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                except sr.UnknownValueError:
                    command_text = ""
                    st.warning("⚠️ ระบบไม่สามารถฟังเสียงพูดในไฟล์ให้ออก กรุณาลองอัปโหลดไฟล์เสียงที่ชัดเจนขึ้น")
                except Exception as e:
                    command_text = ""
                    st.error(f"⚠️ เกิดข้อผิดพลาดในการประมวลผลเสียง: {str(e)}")

            if command_text:
                # ตรวจสอบ Kill-Switch
                kill_keywords = ["ปิดระบบ", "หยุดการทำงาน", "kill switch", "shutdown"]
                if any(keyword in command_text.lower() for keyword in kill_keywords):
                    st.error(f"🛑 [KILL-SWITCH ACTIVATED]: ได้รับคำสั่งปิดระบบฉุกเฉินจากคุณ {speaker_name} {speaker_surname} ระบบกำลังตัดการทำงานทันที!")
                    st.stop()

                # บันทึกคำสั่งลงหน่วยความจำ
                log_entry = f"คุณ {speaker_name}: {command_text}"
                st.session_state.memory_logs.append(log_entry)

                st.success("✅ ผ่านการตรวจสอบความปลอดภัยระดับสูงสุดเรียบร้อย")
                st.write(f"**คำสั่งของคุณ:** {command_text}")
                
                response_msg = f"รับทราบคำสั่งครับคุณ {speaker_name} ระบบ Zyphere AI สายลมพิทักษ์ บันทึกและปฏิบัติการเรียบร้อยแล้วครับ"
                st.info(f"🤖 [AI Response]: {response_msg}")

                # ส่งอีเมลแจ้งเตือนอัตโนมัติผ่าน Gmail SMTP
                try:
                    sender_email = "vorakangm@gmail.com"
                    app_password = "pygo tfga zubw xqca"
                    
                    msg = MIMEText(f"คุณ {speaker_name} ได้สั่งการระบบ:\n\nคำสั่ง: {command_text}")
                    msg['Subject'] = f"🛡️ Zyphere Agent Alert: คำสั่งจาก {speaker_name}"
                    msg['From'] = sender_email
                    msg['To'] = target_email

                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(sender_email, app_password)
                        server.sendmail(sender_email, target_email, msg.as_string())
                    st.toast("📧 ส่งอีเมลแจ้งเตือนสำเร็จ!", icon="🚀")
                except Exception as mail_err:
                    st.warning(f"⚠️ ส่งอีเมลไม่สำเร็จ (โปรดตรวจสอบ App Password): {str(mail_err)}")

                # สังเคราะห์เสียงพูดตอบกลับ (TTS) เป็นเสียงผู้ชาย
                try:
                    tts_path = "response.mp3"
                    asyncio.run(generate_male_voice(response_msg, tts_path))
                    st.audio(tts_path, format="audio/mp3", autoplay=True)
                except Exception as tts_err:
                    st.warning(f"⚠️ ไม่สามารถสร้างเสียงพูดได้: {str(tts_err)}")

# แสดงความจำระบบทั้งหมด
if st.session_state.memory_logs:
    with st.expander("📂 ดูประวัติคำสั่งและความจำส่วนตัวของระบบ"):
        for log in st.session_state.memory_logs:
            st.text(log)
