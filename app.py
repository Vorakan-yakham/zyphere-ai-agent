import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(
    page_title="Build | Zyphere Studio", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ดีไซน์ CSS สมบูรณ์แบบ (เพิ่มตัวหนังสือ ZYPHERE ใต้โลโก้ปฏิกรณ์ที่กำลังหมุน) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #1f1f1f;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    audio { display: none !important; }

    /* ปรับแต่ง Sidebar ให้พอดีสายตา */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
        padding-top: 0.5rem;
    }

    /* จัดกลุ่มเนื้อหาหลักให้อยู่กึ่งกลางหน้าจออย่างสมบูรณ์แบบ */
    .block-container {
        padding-top: 5vh !important;
        padding-bottom: 2rem !important;
        max-width: 850px !important;
        margin: 0 auto;
    }

    /* โลโก้ปฏิกรณ์ Neon Atom เคลื่อนไหวสไตล์ J.A.R.V.I.S. พร้อมข้อความ ZYPHERE ด้านล่าง */
    .logo-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-top: 5px;
        margin-bottom: 0px;
    }
    .svg-logo {
        width: 70px;
        height: 70px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 { transform-origin: center; animation: spinSlow 10s linear infinite; }
    .orbit-2 { transform-origin: center; animation: spinReverse 7s linear infinite; }
    .core-glow { transform-origin: center; animation: pulseCore 2s infinite alternate; }
    @keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes spinReverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.4)); }
        100% { filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.8)); }
    }
    @keyframes pulseCore { 0% { transform: scale(0.9); opacity: 0.7;
