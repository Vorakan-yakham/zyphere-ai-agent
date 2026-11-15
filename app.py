import streamlit as st
import edge_tts
import asyncio
import base64
import os

# --- 1. ตั้งค่าหน้าเว็บแบบ Minimal & Distraction-free ---
st.set_page_config(
    page_title="Zyphere",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. Custom CSS ซ่อน UI ที่ไม่จำเป็น เพื่อให้โฟกัสที่เสียงและความสะอาดตา ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* จัดกึ่งกลางสำหรับ Neon Atom Logo */
    .neon-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
    }
    
    .neon-atom {
        font-size: 80px;
        animation: pulse 2s infinite;
        text-shadow: 0 0 20px rgba(0, 243, 255, 0.6);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.05); opacity: 1; text-shadow: 0 0 35px rgba(0, 243, 255, 0.9); }
        100% { transform: scale(1); opacity: 0.8; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. ฟังก์ชันสร้างเสียงและเล่นเสียงแบบซ่อน (Audio-first Feedback) ---
def generate_male_voice(text, output_path="temp_audio.mp3"):
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-5Hz", rate="-2%")
    asyncio.run(communicate.save(output_path))
    return output_path

def play_audio_invisible(audio_file_path):
    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

# --- 4. ระบบจัดการสถานะการเข้าสู่ระบบ (Email-based Auth) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ตรวจสอบ Secrets สำหรับอีเมลแอดมิน
ADMIN_EMAIL = st.secrets.get("admin_email", "admin@zyphere.com")

if not st.session_state.authenticated:
    st.markdown("<div style='text-align: center; margin-top: 100px;'><h2>⚡ ZYPHERE ACCESS</h2></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_email = st.text_input("Enter authorized email:")
        if st.button("Authenticate"):
            if user_email == ADMIN_EMAIL:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied.")
    st.stop()

# --- 5. UI หลักของ Zyphere ---
st.markdown("""
    <div class="neon-container">
        <div class="neon-atom">⚛️</div>
        <h3 style="letter-spacing: 2px; color: #00f3ff; margin-top: 20px;">ZYPHERE</h3>
    </div>
""", unsafe_allow_html=True)

# ช่องรับข้อความแบบมินิมอล
user_input = st.chat_input("พูดคุยกับ Zyphere...")

if user_input:
    # ตรรกะการตอบสนองแบบ stochastic / conversational mirroring
    response_text = f"รับทราบครับคุณวรกันต์ ผมกำลังดำเนินการในส่วนของ {user_input} ให้ทันทีครับ"
    
    # สร้างไฟล์เสียงทุ้มนุ่มนวล
    audio_path = generate_male_voice(response_text)
    
    # เล่นเสียงอัตโนมัติแบบไร้รอยต่อ
    play_audio_invisible(audio_path)
