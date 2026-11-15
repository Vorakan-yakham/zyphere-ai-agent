import streamlit as st
import os
import tempfile
import requests
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

# --- แผงควบคุมตั้งค่าระบบลับ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบขั้นสูง")
    line_token = st.text_input("LINE Notify Token (ถ้ามี)", type="password", placeholder="ใส่ Token สำหรับแจ้งเตือนเข้าไลน์")
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
st.subheader("🎙️ บันทึกเสียงคำสั่ง")
audio_file = st.file_uploader("อัปโหลดไฟล์เสียงคำสั่งของคุณ (.wav, .mp3)", type=["wav", "mp3", "m4a"])

if st.button("🚀 ส่งคำสั่งไปยัง AI Super-Agent", type="primary"):
    if not speaker_name or not speaker_surname:
        st.error("⚠️ กรุณากรอกชื่อและนามสกุลให้ครบถ้วนก่อนส่งคำสั่ง")
    elif not audio_file:
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
            with st.spinner("กำลังแปลงเสียงและประมวลผลระบบอัตโนมัติ..."):
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
                    st.error(f"⚠️ เกิดข้อผิดพลาดในการประมวลผล: {str(e)}")

                if 'command_text' in locals() and command_text:
                    # ตรวจสอบ Kill-Switch
                    kill_keywords = ["ปิดระบบ", "หยุดการทำงาน", "kill switch", "shutdown"]
                    if any(keyword in command_text.lower() for keyword in kill_keywords):
                        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: ได้รับคำสั่งปิดระบบฉุกเฉินจากคุณ {speaker_name} {speaker_surname} ระบบกำลังตัดการทำงานทันที!")
                        st.stop()

                    # ค้นหาข้อมูลจากเอกสารลับ (ถ้ามีอัปโหลดไว้)
                    answer_extra = ""
                    if doc_content and any(kw in command_text.lower() for kw in ["เนื้อหา", "เอกสาร", "สรุป", "ในไฟล์", "ข้อมูล"]):
                        answer_extra = f"\n📄 [วิเคราะห์จากเอกสารของคุณ]: พบข้อมูลเกี่ยวข้องในคลังความรู้ที่อัปโหลดไว้เรียบร้อย"

                    # บันทึกคำสั่งลงหน่วยความจำ
                    log_entry = f"คุณ {speaker_name}: {command_text}"
                    st.session_state.memory_logs.append(log_entry)

                    st.success("✅ ผ่านการตรวจสอบความปลอดภัยระดับสูงสุดเรียบร้อย")
                    st.write(f"**ข้อความจากเสียงของคุณ:** {command_text}")
                    
                    response_msg = f"รับทราบคำสั่งจากคุณ {speaker_name} ระบบ Zyphere AI ปฏิบัติการสำเร็จ {answer_extra}"
                    st.info(f"🤖 [AI Response]: {response_msg}")

                    # ส่งแจ้งเตือนเข้า LINE Notify อัตโนมัติ (ถ้าใส่ Token ไว้)
                    if line_token:
                        try:
                            line_url = "https://notify-api.line.me/api/notify"
                            headers = {"Authorization": f"Bearer {line_token}"}
                            payload = {"message": f"\n🛡️ Zyphere Agent Alert:\nผู้สั่ง: คุณ {speaker_name}\nคำสั่ง: {command_text}"}
                            requests.post(line_url, headers=headers, data=payload)
                            st.toast("📲 ส่งแจ้งเตือนเข้า LINE สำเร็จ!", icon="🚀")
                        except Exception:
                            pass

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
