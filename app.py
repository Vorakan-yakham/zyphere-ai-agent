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

# --- 2. Custom CSS ปรับแต่ง UI และปุ่ม Login ให้แสดงผลชัดเจน 100% ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* บังคับข้อความทั่วไปและ Label เป็นสีขาวสว่าง */
    label, p, span, div[data-baseweb="typography"] {
        color: #ffffff !important;
    }
    
    /* กำหนดสีตอนไฮไลต์ข้อความ */
    ::selection {
        background: #00f3ff;
        color: #000000;
    }
    ::-moz-selection {
        background: #00f3ff;
        color: #000000;
    }
    
    .neon-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 50vh;
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

    /* บังคับตัวอักษรในช่อง input ให้เป็นสีดำเข้ม พื้นหลังขาว */
    input, div[data-baseweb="input"] input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #ffffff !important;
    }

    /* แก้ไขปุ่ม Authenticate ให้แสดงผลชัดเจน ตัวหนังสือสีดำ พื้นหลังขาวขอบฟ้า ตลอดเวลา */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        border: 2px solid #00f3ff !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        background-color: #00f3ff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 2px solid #ffffff !important;
    }
    
    div.stButton > button p {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. ฟังก์ชันเสียงพรีเมียม (Edge TTS - ปรับความทุ้มและจังหวะธรรมชาติ) ---
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

# --- 4. ระบบจัดการสถานะการเข้าสู่ระบบ & Email Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

ALLOWED_EMAILS = ["vorakangm@gmail.com", "admin@zyphere.com"]
admin_secret = st.secrets.get("admin_email", None)
if admin_secret and admin_secret not in ALLOWED_EMAILS:
    ALLOWED_EMAILS.append(admin_secret)

if not st.session_state.authenticated:
    st.markdown("<div style='text-align: center; margin-top: 100px;'><h2>⚡ ZYPHERE ACCESS</h2></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_email = st.text_input("Enter authorized email:")
        if st.button("Authenticate"):
            if user_email.strip().lower() in ALLOWED_EMAILS:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied. Invalid email.")
    st.stop()

# --- 5. สถาปัตยกรรมหลักของ Zyphere (4-Axis Engine & UI) ---
st.markdown("""
    <div class="neon-container">
        <div class="neon-atom">⚛️</div>
        <h3 style="letter-spacing: 2px; color: #00f3ff; margin-top: 20px;">ZYPHERE</h3>
        <p style="color: #8b949e; font-size: 14px;">4-Axis Intelligence & Audio-First Assistant</p>
    </div>
""", unsafe_allow_html=True)

# ช่องรับข้อความสนทนา
user_input = st.chat_input("พูดคุยกับ Zyphere (Knowledge / Aerospace / Robotics / Content)...")

if user_input:
    response_text = f"รับทราบครับคุณวรกันต์ ระบบกำลังประมวลผลคำขอเกี่ยวกับ {user_input} ให้ทันทีครับ"
    audio_path = generate_male_voice(response_text)
    play_audio_invisible(audio_path)
