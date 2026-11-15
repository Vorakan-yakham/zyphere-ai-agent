import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(
    page_title="Zyphere Autonomous Super-Agent Studio", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ดีไซน์ CSS แก้ไขตำแหน่งโลโก้และจัดเลย์เอาต์ให้สวยงามสมบูรณ์แบบ ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
        color: #1a1a1a;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    audio { display: none !important; }

    /* ปรับแต่ง Sidebar ให้ดูหรูหราสะอาดตา */
    [data-testid="stSidebar"] {
        background-color: #f1f3f5;
        border-right: 1px solid #e9ecef;
        padding-top: 1rem;
    }

    /* บีบช่องว่างตู้คอนเทนเนอร์หลักให้กระชับสมส่วน */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 98% !important;
    }

    /* กล่อง Prompt แคปซูลชิ้นเดียวไร้รอยต่อ จำลองแบบ AI Studio */
    [data-testid="stForm"] {
        background-color: #ffffff;
        border: 1px solid #ced4da !important;
        border-radius: 14px;
        padding: 6px 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03);
    }
    [data-testid="stForm"] input {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        font-size: 14px !important;
    }

    /* ปุ่มกดสไตล์ Monotone Minimalist พรีเมียม */
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 6px !important;
        padding: 0.35rem 0.8rem !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #555555 !important;
    }

    /* โลโก้ Neon Atom กลางหน้าจอ จัดระยะห่างให้สง่างาม */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .svg-logo {
        width: 60px;
        height: 60px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 { transform-origin: center; animation: spinSlow 12s linear infinite; }
    .orbit-2 { transform-origin: center; animation: spinReverse 8s linear infinite; }
    .core-glow { transform-origin: center; animation: pulseCore 2s infinite alternate; }
    @keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes spinReverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.15)); }
        100% { filter: drop-shadow(0 0 8px rgba(0, 0, 0, 0.35)); }
    }
    @keyframes pulseCore { 0% { transform: scale(0.9); opacity: 0.7; } 100% { transform: scale(1.1); opacity: 1; } }

    .welcome-title {
        text-align: center;
        font-size: 22px;
        font-weight: 600;
        color: #1a1a1a;
        margin-top: 5px;
        margin-bottom: 15px;
        letter-spacing: -0.3px;
    }

    /* กล่องข้อความแชทพรีเมียม */
    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e9ecef !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        color: #1a1a1a !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.02);
        margin-bottom: 10px;
    }

    /* การ์ดข้อมูลผู้ใช้งานมุมซ้ายล่าง */
    .user-profile-card {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 8px 10px;
        font-size: 11px;
        color: #1a1a1a;
        margin-top: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์ ยาคำ", "email": "vorakangm@gmail.com", "role": "Sovereign Administrator"},
    {"name": "การัณยภาส ยาคำ", "email": "karanyapas@yakham.com", "role": "Authorized Executive"}
]

if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None
if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
    st.session_state.verified_name = ""
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

async def generate_male_voice(text, output_path):
    voice = "th-TH-NiwatNeural"
    tts_text = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    communicate = edge_tts.Communicate(tts_text, voice, pitch="-4Hz", rate="+0%")
    await communicate.save(output_path)

# --- 1. SIDEBAR ด้านซ้าย ---
with st.sidebar:
    st.markdown("### Zyphere Studio")
    st.caption("Autonomous Agent Control Hub")
    st.markdown("---")
    
    st.markdown("**EXPLORE**")
    st.markdown("- Playground")
    st.markdown("- History")
    
    st.markdown("**BUILD**")
    st.markdown("- + New agent")
    st.markdown("- My agents")
    st.markdown("- Gallery")
    
    st.markdown("**MANAGE**")
    st.markdown("- Dashboard")
    st.markdown("- Documentation")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not st.session_state.is_verified:
        st.markdown("**Sovereign Login**")
        selected_user_name = st.selectbox("เลือกผู้มีสิทธิ์เข้าถึง:", [u["name"] for u in AUTHORIZED_USERS])
        input_email = st.text_input("ยืนยันอีเมลส่วนตัว", placeholder="input email...")
        
        if st.button("Unlock System", type="primary", use_container_width=True):
            matched_user = next((u for u in AUTHORIZED_USERS if u["name"] == selected_user_name and u["email"].strip().lower() == input_email.strip().lower()), None)
            if matched_user:
                st.session_state.is_verified = True
                st.session_state.verified_name = matched_user["name"]
                st.rerun()
            else:
                st.error("Access Denied: อีเมลไม่ตรงกับสิทธิ์เด็ดขาด")
    else:
        speaker_name = st.session_state.verified_name
        st.markdown(f"""
            <div class="user-profile-card">
                <b>Active Session:</b><br>
                {speaker_name}<br>
                <small style="color:#666;">Sovereign Security Level 1</small>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

if not st.session_state.is_verified:
    st.info("กรุณายืนยันตัวตนด้วยอีเมลที่แผงควบคุมด้านซ้ายล่าง เพื่อเริ่มใช้งานระบบ Zyphere")
    st.stop()

speaker_name = st.session_state.verified_name

# --- 2. LAYOUT: แบ่ง 2 คอลัมน์สมส่วน (3.8 : 1.1) ---
main_col, right_col = st.columns([3.8, 1.1], gap="medium")

with right_col:
    st.markdown("##### Run settings")
    st.caption("Engine: Zyphere Neural Core v4.2")
    selected_model = st.selectbox("Model & Core:", [
        "Zyphere 4 Hydrogen (Omni-Science)",
        "Zyphere Aerospace & CAD Synthesizer",
        "Zyphere Quantum Physics Engine",
        "Zyphere Multi-Platform Publisher"
    ])
    
    st.markdown("---")
    st.markdown("##### System Instructions")
    send_email_enabled = st.checkbox("เปิดใช้งานระบบส่งรายงานอีเมลอัตโนมัติ", value=False)
    target_email = st.text_input("อีเมลรับรายงาน", value="vorakangm@gmail.com")
    
    st.markdown("---")
    st.markdown("##### Thinking level")
    thinking_level = st.select_slider("Select depth:", options=["Low", "Medium", "High", "Autonomous Maximum"], value="Autonomous Maximum")
    
    st.markdown("---")
    st.markdown("##### Advanced Tools")
    structured_outputs = st.checkbox("Structured outputs", value=True)
    code_execution = st.checkbox("Code execution (Python/G-Code)", value=True)
    function_calling = st.checkbox("Function calling (IoT/Hardware)", value=True)
    grounding_search = st.checkbox("Grounding with Sovereign Web Search", value=True)

with main_col:
    # โลโก้ Neon Atom กลับมาอยู่ตรงกลางสง่างาม
    st.markdown('''
        <div class="logo-container">
            <svg class="svg-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <g class="orbit-2"><ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#1a1a1a" stroke-width="1.5" opacity="0.7"/></g>
                <g class="orbit-1"><ellipse cx="50" cy="50" rx="16" ry="42" fill="none" stroke="#666666" stroke-width="1.5" opacity="0.7"/></g>
                <circle class="core-glow" cx="50" cy="50" r="10" fill="#1a1a1a" opacity="0.4"/>
                <circle cx="50" cy="50" r="4" fill="#1a1a1a"/>
            </svg>
        </div>
    ''', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown(f'<div class="welcome-title">Build with Zyphere 4 Hydrogen</div>', unsafe_allow_html=True)
        
        st.markdown("""
            <div style="font-size:13px; color:#555; margin-bottom:8px; font-weight:500;">Quick Prompt Suggestions:[cite: 13]</div>
        """, unsafe_allow_html=True)
        
        t1, t2 = st.columns(2)
        with t1:
            if st.button("🛰️ ออกแบบโครงสร้างชิ้นส่วนยานอวกาศ Titanium-Graphene", use_container_width=True):
                st.session_state.pending_prompt = "ออกแบบโครงสร้างชิ้นส่วนยานอวกาศ Titanium-Graphene"
                st.rerun()
            if st.button("🌲 สร้างวิดีโอเรื่องเล่าคนเดินป่า พร้อมโพสต์ลง Social", use_container_width=True):
                st.session_state.pending_prompt = "สร้างวิดีโอเรื่องเล่าคนเดินป่า แล้วโพสต์ลง Facebook, YouTube และ TikTok ให้หน่อย"
                st.rerun()
        with t2:
            if st.button("⚡ เขียนโค้ดระบบควบคุมแขนกล IoT Autonomous", use_container_width=True):
                st.session_state.pending_prompt = "เขียนโค้ดระบบควบคุมแขนกล IoT Autonomous"
                st.rerun()
            if st.button("📊 วิเคราะห์จุดคุ้มทุนธุรกิจอัจฉริยะอัตโนมัติ", use_container_width=True):
                st.session_state.pending_prompt = "ระบบประเมินจุดคุ้มทุนธุรกิจอัตโนมัติ"
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
        st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

def native_jarvis_brain(cmd):
    cmd_lower = cmd.lower()
    if any(k in cmd_lower for k in ["ความสามารถ", "ทำอะไรได้บ้าง", "เธอทำอะไร", "ระบบมีอะไรบ้าง"]):
        return (
            "สถาปัตยกรรมระบบครอบคลุม 4 แกนหลักระดับเอลีท:\n\n"
            "1. **Universal Knowledge & Omni-Science:** ประมวลผลและไขคำตอบทางฟิสิกส์ควอนตัม อากาศพลศาสตร์ และทฤษฎีขั้นสูง\n"
            "2. **Aerospace & CAD/G-Code Synthesis:** ออกแบบโครงสร้างยานอวกาศ ชิ้นส่วนเครื่องจักรกล และสร้างชุดคำสั่ง G-code สำหรับเครื่องพิมพ์ 3 มิติ / CNC\n"
            "3. **Autonomous Robotics & IoT Integration:** ควบคุมวงจรอิเล็กทรอนิกส์ แขนกล และระบบเซนเซอร์อัตโนมัติ\n"
            "4. **Cross-Platform Content Automation:** สั่งการสร้างวิดีโอ สคริปต์ และเผยแพร่อัตโนมัติลง Social Media (Facebook, YouTube, TikTok)\n\n"
            "โปรดระบุภารกิจเฉพาะด้านที่ต้องการให้เริ่มปฏิบัติการได้ทันทีครับ"
        )
    elif any(k in cmd_lower for k in ["ยานอวกาศ", "หุ่นยนต์", "เครื่องจักร", "gcode", "g-code", "cad", "ออกแบบ"]):
        return (
            "**ผลการสังเคราะห์พิมพ์เขียววิศวกรรม:**\n\n"
            "```gcode\n"
            "; Zyphere Native CNC / 3D Printer G-Code\n"
            "; Target: Advanced Alloy Structural Component\n"
            "G21 ; Set units to millimeters\n"
            "G90 ; Absolute positioning\n"
            "M104 S240 ; Set Extruder Temp\n"
            "G1 X0 Y0 Z0.2 F3000 ; Move to origin\n"
            "```\n\n"
            "**ข้อเสนอแนะทางวัสดุศาสตร์:** แนะนำให้ใช้ Titanium-Graphene Alloy เพื่อรองรับแรงกดดันสูงในชั้นบรรยากาศ"
        )
    elif any(k in cmd_lower for k in ["เดินป่า", "วิดีโอ", "facebook", "tiktok", "youtube"]):
        return (
            "**ระบบอัตโนมัติ Cross-Platform Content Automation กำลังทำงาน:**\n\n"
            "1. **Scripting:** สร้างบทเรื่องเล่าคนเดินป่าบรรยากาศลึกลับน่าติดตามเรียบร้อย\n"
            "2. **Voice Synthesis:** สังเคราะห์เสียงบรรยายพรีเมียมโทนทุ้มนุ่มนวล\n"
            "3. **Video Production:** ตัดต่อฟุตเทจป่าเขาพร้อมซับไตเติลออโต้\n"
            "4. **API Deployment:** ส่งข้อมูลและเผยแพร่อัตโนมัติไปยัง Facebook, YouTube และ TikTok เรียบร้อยแล้วครับ"
        )
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ระบบ Zyphere พร้อมรับบัญชาการสร้างนวัตกรรมและขับเคลื่อนโครงสร้างอัจฉริยะแล้วครับ"
    else:
        return (
            "**ผลการวิเคราะห์ทางตรรกะและฐานข้อมูลจักรวาล:**\n\n"
            "- ตรวจสอบตัวแปรและประเมินความเป็นไปได้ภายใต้กฎฟิสิกส์และระบบอัตโนมัติเรียบร้อย\n"
            "- พร้อมแปลงข้อกำหนดดังกล่าวให้เป็นพิมพ์เขียววิศวกรรม ชุดโค้ดโปรแกรม หรือแผนปฏิบัติการอัตโนมัติ\n\n"
            "กรุณาระบุพารามิเตอร์เพิ่มเติมหากต้องการให้ดำเนินการทันทีครับ"
        )

def process_command(cmd):
    if not cmd:
        return
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"[KILL-SWITCH ACTIVATED]: คำสั่งฉุกเฉินจากคุณ {speaker_name} ระบบกำลังตัดการทำงานทันที!")
        st.stop()

    response_msg = native_jarvis_brain(cmd)
    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    if send_email_enabled:
        try:
            sender_email = "vorakangm@gmail.com"
            app_password = "pygo tfga zubw xqca"
            msg = MIMEText(f"รายงานการปฏิบัติการ Zyphere:\n\nผู้สั่งการ: {speaker_name}\nคำสั่ง: {cmd}\nผลการวิเคราะห์: {response_msg}")
            msg['Subject'] = f"Zyphere Report: {speaker_name}"
            msg['From'] = sender_email
            msg['To'] = target_email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, target_email, msg.as_string())
        except:
            pass

    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except:
        st.session_state.latest_audio = None

# --- 3. FLOATING COMMAND BOX ด้านล่างสุด ---
with main_col:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.voice_active:
        with st.container():
            st.markdown("🎙️ **Voice Input Active (พูดคำสั่งของคุณ)**")
            audio_data = st.audio_input("บันทึกเสียงพูดเพื่อสั่งการ Zyphere")
            if audio_data is not None:
                st.success("บันทึกเสียงสำเร็จ! พร้อมประมวลผลคำสั่ง")

    default_input = st.session_state.pop("pending_prompt", "")

    with st.form(key="ai_studio_prompt_box", clear_on_submit=True):
        user_input = st.text_input("Start typing a prompt to see what our models can do", value=default_input, label_visibility="collapsed")
        
        c1, c2, c3, c4, c5, c6 = st.columns([0.4, 0.4, 0.9, 3.8, 0.6, 1.0])
        with c1:
            st.form_submit_button("+")
        with c2:
            st.form_submit_button("⊙")
        with c3:
            st.form_submit_button("Tools")
        with c4:
            st.markdown("<span style='font-size:11px; color:#666;'>Zyphere Core Engine</span>", unsafe_allow_html=True)
        with c5:
            mic_btn = st.form_submit_button("🎤")
        with c6:
            submitted = st.form_submit_button("Run ↵", type="primary")
            
        if submitted and user_input:
            process_command(user_input)
            st.rerun()

    if mic_btn:
        st.session_state.voice_active = not st.session_state.voice_active
        st.rerun()
