import streamlit as st
import os
import tempfile
import speech_recognition as sr

st.set_page_config(page_title="Private Super-Agent", page_icon="🛡️", layout="centered")

st.title("🛡️ Private Autonomous Super-Agent")
st.markdown("ระบบ AI ส่วนตัว ปลอดภัยสูงสุด ควบคุมและสั่งการได้เฉพาะคุณ **วรกันต์ ยาคำ** และคุณ **การัณยภาส ยาคำ** เท่านั้น")

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

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
                    # บันทึกไฟล์เสียงชั่วคราว
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_file.getvalue())
                        tmp_path = tmp_file.name

                    # แปลงเสียงเป็นข้อความด้วย SpeechRecognition (รองรับภาษาไทย th-TH)
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

                    st.success("✅ ผ่านการตรวจสอบความปลอดภัยเรียบร้อย")
                    st.write(f"**ข้อความจากเสียงของคุณ:** {command_text}")
                    st.info(f"🤖 [AI Response]: รับทราบคำสั่งจากคุณ {speaker_name} พร้อมปฏิบัติการและเรียนรู้ข้อมูลเรียบร้อยครับ!")
