import edge_tts
import asyncio
import base64
import streamlit as st

def generate_male_voice(text, output_path):
    # เลือกใช้เสียงผู้ชายไทย NiwatNeural พร้อมปรับ pitch และ rate ให้ละมุนขึ้น
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    
    # รัน edge_tts แบบซิงโครนัสเพื่อป้องกันแอปค้าง
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-5Hz", rate="-2%")
    asyncio.run(communicate.save(output_path))

def play_audio_invisible(audio_file_path):
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
