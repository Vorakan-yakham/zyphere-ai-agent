"""UI pieces: secure login, sidebar/settings, welcome screen, message rendering, optional voice."""
import asyncio
import base64
import hmac
import html
import os
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional

import streamlit as st

from core import MODELS, DEFAULT_MODEL, SUPPORTED_TYPES, Attachment, get_api_key, parse_uploaded_file

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
VOICE = "th-TH-NiwatNeural"
DEFAULT_ALLOWED = ["vorakangm@gmail.com", "admin@zyphere.com"]
MAX_TURNS_PER_SESSION = 80  # cost guard for the API key

SUGGESTIONS = [
    ("🏗️", "ออกแบบสถาปัตยกรรม", "ช่วยออกแบบสถาปัตยกรรมระบบ SaaS สำหรับจัดการลูกค้าและใบสั่งซื้อ ให้รองรับ 10,000 ผู้ใช้ พร้อมเปรียบเทียบตัวเลือกและความเสี่ยง"),
    ("🛩️", "วิเคราะห์โดรน", "โดรนปีกตรึงหนัก 2.5 กก. ปีกกว้าง 1.8 ม. ต้องการความเร็วเดินทาง 18 m/s ช่วยคำนวณ lift ที่ต้องการและวิเคราะห์ว่าออกแบบสมเหตุสมผลไหม"),
    ("🦾", "แขนกล / Firmware", "อธิบายและเขียนโค้ด inverse kinematics สำหรับแขนกล 2 ข้อต่อ (2-DOF planar) พร้อมข้อควรระวังเรื่อง singularity และ joint limit"),
    ("🎬", "สคริปต์คอนเทนต์", "เขียนสคริปต์วิดีโอสั้น 45 วินาทีเกี่ยวกับการใช้ AI ในงานวิศวกรรม พร้อม hook, shot list และ call-to-action"),
]


@dataclass
class Settings:
    model: str
    deep: bool
    voice: bool
    attachments: List[Attachment]


# ---------- Auth ----------
def _secret(name: str):
    try:
        return st.secrets.get(name, None)
    except Exception:  # no secrets file
        return None


def _allowed_emails() -> List[str]:
    configured = _secret("allowed_emails")
    if isinstance(configured, str):
        configured = [e for e in configured.split(",")]
    emails = [e.strip().lower() for e in (configured or DEFAULT_ALLOWED) if e.strip()]
    admin = _secret("admin_email")
    if admin and admin.strip().lower() not in emails:
        emails.append(admin.strip().lower())
    return emails


def auth_gate() -> None:
    st.session_state.setdefault("authenticated", False)
    if st.session_state.authenticated:
        return

    access_code = _secret("access_code")
    st.markdown("<div style='margin-top:90px'></div><h1 class='zy-title'>⚡ ZYPHERE SECURITY CORE</h1>"
                "<p class='zy-sub'>Authorized Personnel Only</p>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        # The app spends API credits, so an email alone (public in the repo) is not enough.
        if get_api_key(st.secrets if _secret("ANTHROPIC_API_KEY") else None) and not access_code:
            st.error("ยังไม่ได้ตั้งค่า `access_code` ใน Secrets — ระบบปิดการเข้าสู่ระบบไว้เพื่อป้องกันการใช้ API key โดยผู้อื่น")
            st.code('access_code = "รหัสผ่านของคุณ"', language="toml")
            st.stop()

        email = st.text_input("Authorized Email")
        code = st.text_input("Access Code", type="password") if access_code else ""
        if st.button("AUTHENTICATE SYSTEM"):
            email_ok = email.strip().lower() in _allowed_emails()
            code_ok = (not access_code) or hmac.compare_digest(code.encode(), str(access_code).encode())
            if email_ok and code_ok:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied: Unrecognized Credentials.")
    st.stop()


# ---------- Voice (optional) ----------
def _speakable(text: str, limit: int = 400) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[`*#>|_\-]+", " ", text)
    return " ".join(text.split())[:limit]


def speak(text: str) -> None:
    """Edge-TTS read-out of the first part of an answer. Never raises."""
    try:
        import edge_tts
        spoken = _speakable(text).replace("Zyphere", "ไซเฟอร์")
        if not spoken:
            return
        os.makedirs(AUDIO_DIR, exist_ok=True)
        for f in sorted((os.path.join(AUDIO_DIR, x) for x in os.listdir(AUDIO_DIR)), key=os.path.getmtime)[:-5]:
            os.remove(f)
        path = os.path.join(AUDIO_DIR, f"{uuid.uuid4().hex}.mp3")
        asyncio.run(edge_tts.Communicate(spoken, VOICE, pitch="-5Hz", rate="-2%").save(path))
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        st.markdown(f'<audio autoplay controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" '
                    f'type="audio/mp3"></audio>', unsafe_allow_html=True)
    except Exception as e:
        print(f"Audio Generation Error: {e}")


# ---------- Sidebar ----------
def render_sidebar(memory, has_llm: bool) -> Settings:
    with st.sidebar:
        st.markdown("<h3 style='margin-bottom:0'>⚡ ZYPHERE</h3><small>Autonomous Executive OS</small>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("**🧠 Intelligence**")
        default = _secret("default_model") or DEFAULT_MODEL
        keys = list(MODELS)
        model = st.selectbox("Model", keys, index=keys.index(default) if default in keys else 0,
                             format_func=lambda k: MODELS[k], label_visibility="collapsed")
        deep = st.toggle("Deep Analysis (คิดก่อนตอบ)", value=False,
                         help="ให้ AI วิเคราะห์เป้าหมาย ข้อสมมติ ตัวเลือก และความเสี่ยงก่อนเขียนคำตอบ ช้ากว่าและใช้โควตามากกว่า แต่คำตอบลึกกว่า")
        voice = st.toggle("🔊 อ่านคำตอบออกเสียง", value=False)
        if not has_llm:
            st.warning("ยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY")

        st.markdown("---")
        st.markdown("**📁 File Hub**")
        st.caption("ไฟล์ที่แนบจะถูกส่งให้ AI ในทุกข้อความ จนกว่าจะลบออก")
        ups = st.file_uploader("Upload", type=SUPPORTED_TYPES, accept_multiple_files=True, label_visibility="collapsed")
        attachments: List[Attachment] = []
        for up in ups or []:
            try:
                att = parse_uploaded_file(up)
                if att:
                    attachments.append(att)
            except ValueError as e:
                st.error(str(e))
        if attachments:
            st.success("Loaded: " + ", ".join(a.name for a in attachments))

        st.markdown("---")
        st.markdown("**💾 Memory Bank**")
        st.caption(f"Stored operations: {len(memory)}")
        for m in memory.recent(5):
            st.markdown(f"<div class='zy-mem'><b>{html.escape(m['timestamp'])}</b><br>{html.escape(m['goal'][:140])}</div>",
                        unsafe_allow_html=True)

        msgs = st.session_state.get("messages", [])
        if msgs:
            md = "\n\n".join(f"**{'คุณ' if m['role'] == 'user' else 'Zyphere'}:**\n\n{m['content']}" for m in msgs)
            st.download_button("⬇️ Export chat (.md)", md, file_name="zyphere_chat.md", mime="text/markdown")
        if st.button("Purge Memory & Chat"):
            memory.clear()
            st.session_state.messages = []
            st.session_state.turns = 0
            st.rerun()
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()
    return Settings(model=model, deep=deep, voice=voice, attachments=attachments)


# ---------- Main area ----------
def render_header() -> None:
    st.markdown("<h1 class='zy-title'>⚡ ZYPHERE AUTONOMOUS EXECUTIVE OS</h1>"
                "<p class='zy-sub'>วิเคราะห์ · ออกแบบ · เขียนโค้ด — 4-Axis Intelligence with Persistent Memory</p>",
                unsafe_allow_html=True)


def render_welcome() -> Optional[str]:
    """Shown on an empty chat. Returns a prompt if a suggestion card was clicked."""
    st.markdown("<p class='zy-sub' style='margin-top:30px'>เริ่มจากบรีฟงานด้านล่าง แนบไฟล์ในแถบข้าง หรือเลือกตัวอย่าง</p>",
                unsafe_allow_html=True)
    clicked = None
    cols = st.columns(2)
    for i, (icon, title, prompt) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            st.markdown(f"<div class='zy-card'><b>{icon} {html.escape(title)}</b><br>"
                        f"<small class='zy-muted'>{html.escape(prompt[:90])}…</small></div>", unsafe_allow_html=True)
            if st.button("ใช้ตัวอย่างนี้", key=f"sugg_{i}"):
                clicked = prompt
    return clicked


def badges(axis: str, deep: bool) -> str:
    out = f"<span class='zy-badge'>{html.escape(axis)}</span>"
    if deep:
        out += "<span class='zy-badge deep'>Deep Analysis</span>"
    return out


def render_history(messages: List[dict]) -> None:
    for m in messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant" and m.get("axis"):
                st.markdown(badges(m["axis"], bool(m.get("reasoning"))), unsafe_allow_html=True)
                if m.get("reasoning"):
                    with st.expander("🧠 การวิเคราะห์ก่อนตอบ"):
                        st.markdown(m["reasoning"])
            st.markdown(m["content"])
