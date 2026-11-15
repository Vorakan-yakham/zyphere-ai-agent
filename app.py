import streamlit as st
import edge_tts
import asyncio
import base64
import os
from datetime import datetime

# --- 1. System Configuration ---
st.set_page_config(
    page_title="Zyphere Autonomous Core",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. Bulletproof Contrast CSS (Hard Override All Elements) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0e1117;
        color: #ffffff !important;
    }
    
    /* บังคับตัวหนังสือทั่วไปให้เป็นสีขาวสว่างบนพื้นมืด */
    label, p, span, div[data-baseweb="typography"], h1, h2, h3, h4 {
        color: #ffffff !important;
    }
    
    /* บังคับช่องกรอกอีเมล (Auth Input) ให้พื้นหลังขาว ตัวหนังสือดำสนิท */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-radius: 6px !important;
        border: 2px solid #00f3ff !important;
    }
    
    div[data-baseweb="input"] input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: transparent !important;
        font-weight: 700 !important;
    }
    
    /* บังคับช่อง Chat Input ด้านล่างให้พื้นหลังขาว ตัวหนังสือดำสนิท 100% */
    .stChatInput {
        background-color: #0e1117 !important;
    }
    
    .stChatInput textarea {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* บังคับข้อความในกล่องแชท (Chat Message Text) ให้เป็นสีขาวอ่านง่าย */
    .stChatMessage p, .stChatMessage div {
        color: #ffffff !important;
    }

    /* ปุ่ม Authenticate & Action Buttons */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        border: 2px solid #00f3ff !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        background-color: #00f3ff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    div.stButton > button p {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    .neon-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    .neon-atom {
        font-size: 60px;
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

# --- 3. Audio Synthesis (Edge TTS) ---
def generate_male_voice(text, output_path="temp_audio.mp3"):
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    try:
        communicate = edge_tts.Communicate(tts_text, voice, pitch="-5Hz", rate="-2%")
        asyncio.run(communicate.save(output_path))
        return output_path
    except Exception:
        return None

def play_audio_invisible(audio_file_path):
    if audio_file_path and os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

# --- 4. Authentication Management ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

ALLOWED_EMAILS = ["vorakangm@gmail.com", "admin@zyphere.com"]
admin_secret = st.secrets.get("admin_email", None)
if admin_secret and admin_secret not in ALLOWED_EMAILS:
    ALLOWED_EMAILS.append(admin_secret)

if not st.session_state.authenticated:
    st.markdown("<div style='text-align: center; margin-top: 80px;'><h2>⚡ ZYPHERE ACCESS CONTROL</h2></div>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        user_email = st.text_input("Authorized Email", placeholder="")
        if st.button("Authenticate"):
            if user_email.strip().lower() in ALLOWED_EMAILS:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied. Invalid credentials.")
    st.stop()

# --- 5. Autonomous Executive Core ---
if "memory_bank" not in st.session_state:
    st.session_state.memory_bank = []

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("""
    <div class="neon-container">
        <div class="neon-atom">⚛️</div>
        <h3 style="letter-spacing: 2px; color: #00f3ff; text-align: center; margin-top: 5px;">ZYPHERE AUTONOMOUS OS</h3>
        <p style="color: #8b949e; font-size: 12px; text-align: center;">Executive Agent Core | 4-Axis Architecture</p>
    </div>
""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Zyphere กำลังประมวลผลเป้าหมาย..."):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.memory_bank.append({"timestamp": timestamp, "goal": user_prompt})
            
            response_output = (
                f"รับทราบและบันทึกเป้าหมายของคุณวรกันต์เรียบร้อยแล้ว "
                f"ระบบกำลังดำเนินการตาม Grand Vision ที่คุณตั้งไว้:\n\n"
                "```python\n"
                "# --- ZYPHERE AUTONOMOUS EXECUTION ENGINE ---\n"
                f"# Target Goal: {user_prompt}\n"
                f"# Status: ACTIVE SYNC\n\n"
                "class CoreExecutor:\n"
                "    def __init__(self):\n"
                "        self.status = 'READY'\n"
                "    def run(self):\n"
                "        return 'SUCCESS: Autonomous pipeline executed.'\n"
                "```\n\n"
                "ระบบพร้อมปฏิบัติการขั้นต่อไปแล้วครับ บรีฟคำสั่งถัดมาได้เลยครับคุณวรกันต์!"
            )

            st.markdown(response_output)
            audio_path = generate_male_voice("รับทราบและประมวลผลเป้าหมายเรียบร้อยแล้วครับ")
            play_audio_invisible(audio_path)
            
            st.session_state.messages.append({"role": "assistant", "content": response_output})
