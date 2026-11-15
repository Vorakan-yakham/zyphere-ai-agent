import asyncio
import edge_tts
import streamlit as st

async def generate_male_voice(text, output_path):
    # เลือกใช้เสียงผู้ชายไทย NiwatNeural
    voice = "th-TH-NiwatNeural"
    
    # ปรับแต่งคำศัพท์เพื่อให้ระบบออกเสียงภาษาไทยได้ราบรื่นขึ้น
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    
    # ปรับ pitch ให้ทุ้มลง (-5Hz) และ rate ให้ช้าลงเล็กน้อย (-2%) 
    # เพื่อลดความแข็งกระด้างและทำให้โทนเสียงดูละมุนสุขุมขึ้น
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-5Hz", rate="-2%")
    await communicate.save(output_path)

def play_audio_invisible(audio_file_path):
    # ฟังก์ชันสำหรับเล่นเสียงแบบซ่อน (Invisible Autoplay) ตามดีไซน์ที่คุณวรกันต์ต้องการ
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()
    
    import base64
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
