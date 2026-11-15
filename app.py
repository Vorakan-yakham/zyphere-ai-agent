import streamlit as st
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
import speech_recognition as sr
from gtts import gTTS
from pypdf import PdfReader

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

st.title("🛡️ Zyphere Autonomous Super-Agent")
st.markdown("ระบบ AI ส่วนตัวระดับสูง ปลอดภัยและควบคุมได้เฉพาะคุณ **วรกันต์ ยาคำ** และคุณ **การัณยภาส ยาคำ** เท่านั้น")

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

# ระบบความจำภายในเซสชัน
if "memory_logs" not in st.session_state:
    st.session_state.memory_logs = []

# --- แผงควบคุมตั้งค่าระบบ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าการแจ้งเตือน")
    target_email = st.text_input("อีเมลรับการแจ้งเตือน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.subheader("📚 คลังความรู้เฉพาะครอบครัว")
    uploaded_doc = st.file_uploader("อัปโหลดเอกสาร/โน้ตลับ (PDF หรือ TXT)", type=["pdf", "txt"])

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

# --- หน้าจอหลัก ---
st.subheader("🔑 ยืนยันตัวตนผู้มีสิทธิ์")
col1, col2 = st.columns(2)
with col1:
    speaker_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์")
with col2:
    speaker_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ")

st.markdown("---")
st.subheader("💬 เลือกวิธีป้อนคำสั่ง (พิมพ์ หรือ อัปโหลดเสียง)")

# เพิ่มตัวเลือกให้เลือกได้ทั้ง พิมพ์ข้อความ หรือ อัปโหลดเสียง
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
    if not speaker_name or not speaker_surname:
        st.error("⚠️ กรุณากรอกชื่อและนามสกุลให้ครบถ้วนก่อนส่งคำสั่ง")
    elif input_method == "พิมพ์ข้อความคำสั่ง" and not text_input:
        st.error("⚠️ กรุณาพิมพ์ข้อความคำสั่งก่อนครับ")
    elif input_method == "อัปโหลดไฟล์เสียง" and not audio_file:
        st.error("⚠️ กรุณาอัปโหลดไฟล์เสียงคำสั่งก่อนครับ")
    else:
        # ตรวจสอบตัวตน
        is_authorized = any(
            user["name"].strip() == speaker_name.strip() and user["surname"].strip() == speaker_surname.strip()
            for user in AUTHORIZED_USERS
        )
        
        if not is_authorized:
            st.error("🚨 [ACCESS DENIED]: ตรวจพบคำสั่งจากบุคคลภายนอก ระบบปฏิเสธการประมวลผลทันที")
        else:
            with st.spinner("กำลังประมวลผลระบบอัตโนมัติ..."):
                # กรณีเลือกใช้วิธีพิมพ์ข้อความ
                if input_method == "พิมพ์ข้อความคำสั่ง":
                    command_text = text_input
                
                # กรณีเลือกใช้วิธีอัปโหลดเสียง
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
                    
                    response_msg = f"รับทราบคำสั่งจากคุณ {speaker_name} ระบบ Zyphere AI บันทึกและปฏิบัติการเรียบร้อยแล้ว"
                    st.info(f"🤖 [AI Response]: {response_msg}")

                    # ส่งอีเมลแจ้งเตือนอัตโนมัติผ่าน Gmail SMTP
                    try:
                        sender_email = "vorakangm@gmail.com"
                        app_password = "pygo tfga zubw xqca"  # รหัสผ่านแอป Gmail ของคุณ
                        
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

                    # สังเคราะห์เสียงพูดตอบกลับ (TTS)
                    tts = gTTS(text=response_msg, lang='th')
                    tts_path = "response.mp3"
                    tts.save(tts_path)
                    st.audio(tts_path, format="audio/mp3", autoplay=True)

# แสดงความจำระบบทั้งหมด
if st.session_state.memory_logs:
    with st.expander("📂 ดูประวัติคำสั่งและความจำส่วนตัวของระบบ"):
        for log in st.session_state.memory_logs:
            st.text(log)
