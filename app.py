import streamlit as st
import os
import tempfile
import speech_recognition as sr
from gtts import gTTS

st.set_page_config(page_title="Private Super-Agent", page_icon="🛡️", layout="centered")

st.title("🛡️ Private Autonomous Super-Agent")
st.markdown("ระบบ AI ส่วนตัว ปลอดภัยสูงสุด ควบคุมและสั่งการได้เฉพาะคุณ **วรกันต์ ยาคำ** และคุณ **การัณยภาส ยาคำ** เท่านั้น")

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

# ช่องเก็บความจำภายในระบบ (Session State)
if "memory_logs" not in st.session_state:
    st.session_state.memory_logs = []

st.subheader("🔑 ยืนยันตัวตนผู้มีสิทธิ์")
col1, col2 = st.columns(2)
with col1:
    speaker_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์")
with col2:
    speaker_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ")

st.markdown("---")
st.subheader("🎙️ บันทึกเสียงคำสั่ง")
audio_file = st.file_uploader("อัปโหลดไฟล์เสียงคำสั่งของคุณ (.wav)", type=["wav", "mp3", "m4a"])

if st.button("🚀 ส่งคำสั่งไปยัง AI", type="primary"):
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
            with st.spinner("กำลังแปลงเสียงและประมวลผล..."):
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

                    # บันทึกคำสั่งลงหน่วยความจำ
                    st.session_state.memory_logs.append(f"คุณ {speaker_name}: {command_text}")

                    st.success("✅ ผ่านการตรวจสอบความปลอดภัยเรียบร้อย")
                    st.write(f"**ข้อความจากเสียงของคุณ:** {command_text}")
                    
                    response_msg = f"รับทราบคำสั่งจากคุณ {speaker_name} ระบบได้บันทึกและพร้อมปฏิบัติการตามคำสั่งเรียบร้อยครับ"
                    st.info(f"🤖 [AI Response]: {response_msg}")

                    # สร้างเสียงพูดตอบกลับอัตโนมัติ (Text-to-Speech)
                    tts = gTTS(text=response_msg, lang='th')
                    tts_path = "response.mp3"
                    tts.save(tts_path)
                    st.audio(tts_path, format="audio/mp3", autoplay=True)

# แสดงบันทึกความจำระบบส่วนตัว
if st.session_state.memory_logs:
    with st.expander("📂 ดูประวัติคำสั่งและความจำส่วนตัวของระบบ"):
        for log in st.session_state.memory_logs:
            st.text(log)
