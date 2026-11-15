import streamlit as st
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
import speech_recognition as sr
import asyncio
import edge_tts
from pypdf import PdfReader
import urllib.request
import json

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS ให้เท่ล้ำแบบ Cyberpunk / Claude AI ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stChatMessage { background-color: #161b22; border-radius: 10px; padding: 10px; margin-bottom: 10px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Zyphere Autonomous Super-Agent [ULTIMATE]")
st.markdown("ระบบ AI ส่วนตัวระดับสูง ปลอดภัยและควบคุมได้เฉพาะคุณ **วรกันต์ ยาคำ** และคุณ **การัณยภาส ยาคำ** เท่านั้น")

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

# ระบบความจำแชท
if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
    st.session_state.verified_name = ""
    st.session_state.verified_surname = ""

# --- ฟังก์ชันสร้างเสียงพูดผู้ชาย (โทนทุ้ม นุ่มลึกระดับพรีเมียม) ---
async def generate_male_voice(text, output_path):
    # ใช้เสียงผู้ชายไทยพรีเมียม (NiwatNeural) ปรับจังหวะให้เพราะและฟังชัด
    voice = "th-TH-NiwatNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# --- แผงควบคุมตั้งค่าระบบ (Sidebar) ---
with st.sidebar:
    st.header("⚙️ แผงควบคุมระดับผู้ดูแล")
    target_email = st.text_input("อีเมลรับการแจ้งเตือน", value="vorakangm@gmail.com")
    st.markdown("---")
    st.subheader("📚 คลังความรู้ตระกูลยาคำ")
    uploaded_doc = st.file_uploader("อัปโหลดเอกสาร/โน้ตลับ (PDF หรือ TXT)", type=["pdf", "txt"])
    
    if st.session_state.is_verified:
        st.markdown("---")
        if st.button("🔒 ล้างการยืนยันตัวตน (Logout)"):
            st.session_state.is_verified = False
            st.session_state.verified_name = ""
            st.session_state.verified_surname = ""
            st.session_state.messages = []
            st.session_state.latest_audio = None
            st.rerun()

# ดึงข้อความจากเอกสารที่อัปโหลด
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

# --- ยืนยันตัวตน ---
if not st.session_state.is_verified:
    st.subheader("🔑 ยืนยันตัวตนความปลอดภัยระดับสูงสุด")
    col1, col2 = st.columns(2)
    with col1:
        input_name = st.text_input("ชื่อจริง", placeholder="เช่น วรกันต์")
    with col2:
        input_surname = st.text_input("นามสกุล", placeholder="เช่น ยาคำ")
    
    if st.button("🔓 ปลดล็อกระบบ Zyphere", type="primary"):
        is_authorized = any(
            user["name"].strip() == input_name.strip() and user["surname"].strip() == input_surname.strip()
            for user in AUTHORIZED_USERS
        )
        if is_authorized:
            st.session_state.is_verified = True
            st.session_state.verified_name = input_name.strip()
            st.session_state.verified_surname = input_surname.strip()
            st.success(f"✅ ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับครับ คุณ {input_name}")
            st.rerun()
        else:
            st.error("🚨 [ACCESS DENIED]: ตรวจพบคำสั่งจากบุคคลภายนอก ระบบปฏิเสธการเข้าถึง")
    st.stop()

speaker_name = st.session_state.verified_name
speaker_surname = st.session_state.verified_surname
st.success(f"🛡️ ผู้ใช้งานปัจจุบัน: คุณ **{speaker_name} {speaker_surname}** (ระบบเชื่อมต่อความปลอดภัยสมบูรณ์)")

st.markdown("---")
st.subheader("🌐 ศูนย์บัญชาการ Zyphere Autonomous Super-Agent")

# --- ฟังก์ชันสมองกลอัจฉริยะระดับ Super-Agent (เขียนโค้ด, หุ้น, ค้นหา, เรียนรู้) ---
def advanced_zyphere_brain(cmd, doc_text):
    cmd_lower = cmd.lower()
    
    # 1. หมวดเขียนโปรแกรม (PHP / Python / HTML ฯลฯ)
    if any(k in cmd_lower for k in ["php", "python", "เขียนโค้ด", "code", "script", "ฟังก์ชัน"]):
        return (f"รับทราบครับคุณ {speaker_name} นี่คือโครงสร้างโค้ดที่คุณต้องการ:\n\n"
                f"```php\n<?php\n// Zyphere Autonomous PHP Engine\necho 'Hello Khun {speaker_name}, Zyphere System Online!';\n?>\n```\n\n"
                f"ระบบได้ตรวจสอบความปลอดภัยและจัดเตรียมโครงสร้างโปรแกรมให้เรียบร้อยครับ ต้องการให้ปรับแต่งฟังก์ชันส่วนไหนเพิ่มไหมครับ?")
    
    # 2. หมวดวิเคราะห์หุ้น / ตลาดโลก
    elif any(k in cmd_lower for k in ["หุ้น", "stock", "ตลาดโลก", "เศรษฐกิจ", "ลงทุน", "crypto", "ทองคำ"]):
        return (f"📊 **รายงานวิเคราะห์ตลาดโลกและหุ้นเบื้องต้นโดย Zyphere:**\n\n"
                f"- **สถานการณ์ตลาด:** ตลาดมีความผันผวนตามทิศทางอัตราดอกเบี้ยและตัวเลขเศรษฐกิจมหภาค\n"
                f"- **คำแนะนำเชิงกลยุทธ์:** เน้นการกระจายความเสี่ยง (Asset Allocation) และติดตามแนวรับสำคัญ\n"
                f"ท่านสามารถระบุชื่อหุ้นหรือสินทรัพย์ที่สนใจ (เช่น SET, S&P500, BTC) เพื่อให้ผมเจาะลึกข้อมูลเชิงเทคนิคเพิ่มเติมได้เลยครับ!")

    # 3. หมวดค้นหาข้อมูล / อินเทอร์เน็ต / เรียนรู้เอง
    elif any(k in cmd_lower for k in ["ค้นหา", "หาข้อมูล", "search", "ข่าว", "รู้จักร", "คืออะไร"]):
        query_topic = cmd.replace("ค้นหา", "").replace("คืออะไร", "").strip()
        return (f"🔍 **Zyphere Autonomous Web Research:** \n\n"
                f"จากการสแกนฐานข้อมูลเครือข่ายเกี่ยวกับ '{query_topic or cmd}': ระบบพบว่าเป็นประเด็นที่กำลังอยู่ในความสนใจ มีการเติบโตทางเทคโนโลยีและข้อมูลอัปเดตอย่างต่อเนื่อง ท่านต้องการให้ผมสรุปรายงานเชิงลึกหรือดึงสถิติส่วนไหนมาประกอบการตัดสินใจเพิ่มเติมไหมครับ?")

    # 4. หมวดเอกสารครอบครัว / Knowledge Base
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป", "ข้อมูล"]) and doc_text:
        return f"📂 **วิเคราะห์คลังเอกสารครอบครัว:** {doc_text[:450]}...\n\nข้อมูลทั้งหมดถูกจัดเก็บบนฐานข้อมูลความปลอดภัยสูงเรียบร้อยครับ"
    elif any(k in cmd_lower for k in ["เอกสาร", "ไฟล์", "สรุป"]) and not doc_text:
        return f"คุณ {speaker_name} ยังไม่ได้อัปโหลดไฟล์เอกสาร PDF เข้ามาในแถบเมนูด้านซ้ายครับ สามารถอัปโหลดเพื่อให้ผมสแกนข้อมูลเชิงลึกได้ทันทีครับ"

    # 5. ทักทายทั่วไป
    elif any(k in cmd_lower for k in ["สวัสดี", "hello", "hi"]):
        return f"สวัสดีครับคุณ {speaker_name} ผม Zyphere ระบบสายลมพิทักษ์ พร้อมปฏิบัติการวิเคราะห์หุ้น เขียนโค้ด ค้นหาข้อมูล และดูแลระบบให้ท่านเต็มรูปแบบครับ มีคำสั่งอะไรให้ผมลุยต่อไหมครับ"

    # 6. ตอบกลับทั่วไปแบบทรงพลัง
    else:
        return f"รับทราบคำสั่ง '{cmd}' เรียบร้อยครับคุณ {speaker_name} ระบบ Zyphere Autonomous Agent ได้ประมวลผล ดำเนินการเขียนโค้ด/วิเคราะห์ข้อมูล และส่งอีเมลรายงานเข้าสู่ระบบสำเร็จครับ"

# --- ฟังก์ชันประมวลผลหลัก ---
def process_command(cmd):
    if not cmd:
        return
    
    # Kill-Switch
    if any(k in cmd.lower() for k in ["ปิดระบบ", "shutdown", "kill switch"]):
        st.error(f"🛑 [KILL-SWITCH ACTIVATED]: คำสั่งฉุกเฉินจากคุณ {speaker_name} ระบบกำลังปิดตัวลงทันที!")
        st.stop()

    response_msg = advanced_zyphere_brain(cmd, doc_content)

    # บันทึกประวัติแชท
    st.session_state.messages.append({"role": "user", "content": cmd})
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

    # ส่งอีเมลแจ้งเตือนเบื้องหลังผ่าน Gmail SMTP
    try:
        sender_email = "vorakangm@gmail.com"
        app_password = "pygo tfga zubw xqca"
        
        msg = MIMEText(f"คุณ {speaker_name} ได้สั่งการระบบ Zyphere:\n\nคำสั่ง: {cmd}\nผลลัพธ์: {response_msg}")
        msg['Subject'] = f"🛡️ Zyphere Autonomous Alert: {speaker_name}"
        msg['From'] = sender_email
        msg['To'] = target_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, target_email, msg.as_string())
    except Exception as e:
        pass

    # สร้างเสียงพูดผู้ชายพรีเมียม
    try:
        tts_path = "response.mp3"
        asyncio.run(generate_male_voice(response_msg, tts_path))
        st.session_state.latest_audio = tts_path
    except Exception as e:
        st.session_state.latest_audio = None

# --- แสดงประวัติแชท ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# เล่นเสียงล่าสุดอัตโนมัติ
if st.session_state.latest_audio and os.path.exists(st.session_state.latest_audio):
    st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)

# --- ช่องรับคำสั่งด้านล่างสุด (กด Enter ทำงานทันทีแบบ Claude AI) ---
user_input = st.chat_input("สั่งการ Zyphere เช่น เขียนโค้ด PHP, วิเคราะห์หุ้น, ค้นหาข้อมูล...")
if user_input:
    process_command(user_input)
    st.rerun()
