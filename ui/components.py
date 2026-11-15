"""Reusable UI pieces: auth gate, audio (Edge TTS), sidebar, header."""
import asyncio
import base64
import html
import os
import uuid

import edge_tts
import streamlit as st

from core.parser import SUPPORTED_TYPES, parse_uploaded_file

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
VOICE = "th-TH-NiwatNeural"
DEFAULT_ALLOWED = ["vorakangm@gmail.com", "admin@zyphere.com"]


# ---------- Audio ----------
def generate_audio_response(text: str):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    _cleanup_audio()
    path = os.path.join(AUDIO_DIR, f"{uuid.uuid4().hex}.mp3")
    clean = text.replace("Zyphere", "ไซเฟอร์").replace("zyphere", "ไซเฟอร์")
    try:
        comm = edge_tts.Communicate(clean, VOICE, pitch="-5Hz", rate="-2%")
        asyncio.run(comm.save(path))
        return path
    except Exception as e:  # network/service errors must not crash the UI
        print(f"Audio Generation Error: {e}")
        return None


def _cleanup_audio(keep: int = 5) -> None:
    files = sorted(
        (os.path.join(AUDIO_DIR, f) for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")),
        key=os.path.getmtime,
    )
    for f in files[:-keep] if keep else files:
        try:
            os.remove(f)
        except OSError:
            pass


def render_audio_player(path) -> None:
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<audio autoplay style="display:none;">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
            unsafe_allow_html=True,
        )


# ---------- Auth ----------
def _allowed_emails() -> list:
    emails = list(DEFAULT_ALLOWED)
    try:
        extra = st.secrets.get("admin_email", None)
    except Exception:  # no secrets.toml present
        extra = None
    if extra and extra not in emails:
        emails.append(extra.strip().lower())
    return emails


def auth_gate() -> None:
    st.session_state.setdefault("authenticated", False)
    if st.session_state.authenticated:
        return
    st.markdown(
        "<div style='text-align:center; margin-top:120px;'>"
        "<h1 class='neon-glow'>⚡ ZYPHERE SECURITY CORE</h1>"
        "<p>Authorized Personnel Only</p></div>",
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 2, 1])
    with col:
        email = st.text_input("Enter Authorized Email")
        if st.button("AUTHENTICATE SYSTEM"):
            if email.strip().lower() in _allowed_emails():
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied: Unrecognized Credentials.")
    st.stop()


# ---------- Sidebar ----------
def render_sidebar(memory):
    """Renders file hub + memory inspector. Returns (filename, text) or None."""
    with st.sidebar:
        st.markdown("### 📁 Autonomous File Hub")
        up = st.file_uploader("Upload Project File / Code / Dataset", type=SUPPORTED_TYPES)
        file_data = parse_uploaded_file(up)
        if file_data:
            st.success(f"Loaded: {file_data[0]}")

        st.markdown("---")
        st.markdown("### 🧠 Autonomous Memory Bank")
        st.write(f"Total Stored Operations: {len(memory)}")
        for m in memory.recent(6):
            # Escape: goals are user input rendered with unsafe_allow_html
            st.markdown(
                "<div style='background:#161b22; padding:8px; border-radius:6px; margin-bottom:6px;"
                " font-size:11px; border-left:3px solid #00f3ff;'>"
                f"<b>{html.escape(m['timestamp'])}</b><br>{html.escape(m['goal'])}</div>",
                unsafe_allow_html=True,
            )
        if st.button("Purge Memory Bank"):
            memory.clear()
            st.session_state.messages = []
            st.rerun()
    return file_data


def render_header() -> None:
    st.markdown(
        "<div style='text-align:center; margin-top:10px; margin-bottom:25px;'>"
        "<h2 class='neon-glow' style='letter-spacing:2px;'>⚡ ZYPHERE AUTONOMOUS EXECUTIVE OS</h2>"
        "<p style='color:#8b949e; font-size:13px;'>File Analysis Enabled | Persistent Memory & Code Synthesis</p>"
        "</div>",
        unsafe_allow_html=True,
    )
