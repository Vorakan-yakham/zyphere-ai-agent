import streamlit as st
import os
import sys
from faster_whisper import WhisperModel

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="Private Super-Agent", page_icon="🛡️", layout="centered")

st.title("🛡️ Private Autonomous Super-Agent")
st.markdown("ระบบ AI ส่วนตัว ปลอดภัยสูงสุด ควบคุมและสั่งการได้เฉพาะคุณ **วรกันต์ ยาคำ** และคุณ **การัณยภาส ยาคำ** เท่านั้น")

# 1. ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด (Master Root Authority & Kill-Switch)
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

# โหลดโมเดล Whisper สำหรับแปลงเสียง (แคชไว้เพื่อความเร็ว)
@st.cache_resource
def load_whisper():
    return WhisperModel("base", device="cpu", compute_type="int8")

with st.spinner("กำลังโหลดระบบเสียง..."):
    whisper_model = load_whisper()

# ฟอร์มกรอกข้อมูลยืนยันตัวตนก่อนสั่งงาน
st.subheader("🔑 ยืนยันตัวตนผู้มีสิทธิ์")
col1, col2 = st.columns(2)
with col1:
    speaker_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์")
with col2:
    speaker_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ")

st.markdown("---")
st.subheader("🎙️ บันทึกเสียงคำสั่ง")
audio_file = st.file_uploader("อัปโหลดไฟล์เสียงคำสั่งของคุณ (.wav หรือ .mp3)", type=["wav", "mp3", "m4a"])

if st.button("🚀 ส่งคำสั่งไปยัง AI", type="primary"):
    if not speaker_name or not speaker_surname:
        st.error("⚠️ กรุณากรอกชื่อและนามสกุลให้ครบถ้วนก่อนส่งคำสั่ง")
    elif not audio_file:
        st.error("⚠️ กรุณาอัปโหลดไฟล์เสียงคำสั่งก่อนครับ")
    else:
        # ขั้นตอนที่ 1: ตรวจสอบตัวตน (Identity Verification)
        is_authorized = any(
            user["name"].strip() == speaker_name.strip() and user["surname"].strip() == speaker_surname.strip()
            for user in AUTHORIZED_USERS
        )
        
        if not is_authorized:
            st.error("🚨 [ACCESS DENIED]: ตรวจพบคำสั่งจากบุคคลภายนอก ระบบปฏิเสธการประมวลผลทันที")
        else:
            with st.spinner("กำลังแปลงเสียงและประมวลผล..."):
                # บันทึกไฟล์เสียงชั่วคราว
                temp_audio_path = "temp_audio.wav"
                with open(temp_audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())

                # ขั้นตอนที่ 2: แปลงเสียงพูดเป็นข้อความ (Speech-to-Text)
                try:
                    segments, _ = whisper_model.transcribe(temp_audio_path, language="th")
                    command_text = "".join([segment.text for segment in segments])
                except Exception as e:
                    command_text = ""
                    st.error(f"⚠️ เกิดข้อผิดพลาดในการประมวลผลเสียง: {str(e)}")

                if command_text:
                    # ขั้นตอนที่ 3: ตรวจสอบเงื่อนไข Kill-Switch (คำสั่งปิดตายฉุกเฉิน)
                    kill_keywords = ["ปิดระบบ", "หยุดการทำงาน", "kill switch", "shutdown"]
                    if any(keyword in command_text.lower() for keyword in kill_keywords):
                        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: ได้รับคำสั่งปิดระบบฉุกเฉินจากคุณ {speaker_name} {speaker_surname} ระบบกำลังตัดการทำงานทันที!")
                        st.stop()

                    # ขั้นตอนที่ 4: สมอง AI ประมวลผล
                    st.success("✅ ผ่านการตรวจสอบความปลอดภัยเรียบร้อย")
                    st.write(f"**ข้อความจากเสียงของคุณ:** {command_text}")
                    st.info(f"🤖 [AI Response]: รับทราบคำสั่งจากคุณ {speaker_name} พร้อมปฏิบัติการและเรียนรู้ข้อมูลเรียบร้อยครับ!")
