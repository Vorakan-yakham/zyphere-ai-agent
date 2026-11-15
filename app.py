import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
import asyncio
import edge_tts

st.set_page_config(page_title="Zyphere Autonomous Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์ CSS สไตล์ Claude AI ผสาน Neon Atom Logo และปุ่มไมโครโฟน ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fcfbf9;
        color: #333333;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ซ่อนแถบเครื่องเล่นเสียง แต่ระบบยังอ่านออกเสียงเบื้องหลัง */
    audio {
        display: none !important;
    }
    
    /* ปุ่มกดสไตล์ Monotone Minimalist เรียบหรู */
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        cursor: pointer !important;
    }
    .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #555555 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    a, button, [role="button"], input[type="submit"] {
        cursor: pointer !important;
    }
    
    /* โลโก้ Neon Atom เคลื่อนไหวสไตล์ J.A.R.V.I.S. */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .svg-logo {
        width: 110px;
        height: 110px;
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }
    .orbit-1 {
        transform-origin: center;
        animation: spinSlow 10s linear infinite;
    }
    .orbit-2 {
        transform-origin: center;
        animation: spinReverse 7s linear infinite;
    }
    .core-glow {
        transform-origin: center;
        animation: pulseCore 2s infinite alternate;
    }
    @keyframes spinSlow {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @keyframes spinReverse {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
    }
    @keyframes pulseLogo {
        0% { filter: drop-shadow(0 0 8px rgba(168, 85, 247, 0.4)); }
        100% { filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.8)); }
    }
    @keyframes pulseCore {
        0% { transform: scale(0.9); opacity: 0.7; }
        100% { transform: scale(1.1); opacity: 1; }
    }

    .welcome-header {
        text-align: center;
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e
