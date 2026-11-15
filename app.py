import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS สไตล์ Claude AI และโลโก้จำลองอัจฉริยะ (Hologram Atom Animation) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #333333;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ดีไซน์โลโก้จำลองอะตอมเรืองแสงสไตล์ J.A.R.V.I.S. */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    .reactor-core {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: radial-gradient(circle, #38bdf8 0%, #0284c7 60%, #0f172a 100%);
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.7), inset 0 0 15px rgba(255, 255, 255, 0.8);
        position: relative;
        animation: pulseCore 2.5s infinite alternate;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .reactor-ring {
        position: absolute;
        width: 120px;
        height: 120px;
        border: 2px dashed #38bdf8;
        border-radius: 50%;
        animation: spinRing 10s linear infinite;
    }
    @keyframes pulseCore {
        0% { transform: scale(0.95); box-shadow: 0 0 20px rgba(56, 189, 248, 0.5); }
        100% { transform: scale(1.05); box-shadow: 0 0 40px rgba(56, 189, 248, 0.9); }
    }
    @keyframes spinRing {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .welcome-header {
        text-align: center;
        font-size: 26px;
        font-weight: 600;
        color: #1a1a1a;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e5e5df !important;
        border-radius: 12px !important;
        padding: 16px !important;
        color: #222222 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        margin-bottom: 12px;
    }
    [data-testid="stChatInput"] textarea {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }
    </style>
""", unsafe_allow_html=True)

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
