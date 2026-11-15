"""UI pieces: login, sidebar, HUD header, welcome screen, message rendering, optional voice."""
import asyncio
import base64
import hmac
import html
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import streamlit as st

from core import DEFAULT_MODEL, MODELS, SUPPORTED_TYPES, Attachment, get_api_key, parse_uploaded_file

USER_AVATAR = ":material/person:"
AI_AVATAR = ":material/blur_circular:"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
VOICE = "th-TH-NiwatNeural"
DEFAULT_ALLOWED = ["vorakangm@gmail.com", "admin@zyphere.com"]
MAX_TURNS_PER_SESSION = 80  # cost guard for the API key

# 24x24 line icons (monochrome, stroke = currentColor via CSS)
ICONS = {
    "layers": '<path d="M12 3 3 8l9 5 9-5-9-5Z"/><path d="m3 13 9 5 9-5"/>',
    "plane": '<path d="M21 3 3 10.5l7 2.5 2.5 7L21 3Z"/><path d="m10 13 4-4"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7.5"/>'
            '<path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/>',
    "film": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9.5 5 2.5-5 2.5v-5Z"/>',
}
SUGGESTIONS = [
    ("layers", "System Architecture", "ออกแบบสถาปัตยกรรม SaaS จัดการลูกค้าและใบสั่งซื้อ รองรับ 10,000 ผู้ใช้ พร้อมเปรียบเทียบตัวเลือกและความเสี่ยง",
     "ช่วยออกแบบสถาปัตยกรรมระบบ SaaS สำหรับจัดการลูกค้าและใบสั่งซื้อ ให้รองรับ 10,000 ผู้ใช้ พร้อมเปรียบเทียบตัวเลือกและความเสี่ยง"),
    ("plane", "Aerospace Analysis", "โดรนปีกตรึงหนัก 2.5 กก. ปีกกว้าง 1.8 ม. ความเร็วเดินทาง 18 m/s คำนวณ lift และตรวจความสมเหตุสมผล",
     "โดรนปีกตรึงหนัก 2.5 กก. ปีกกว้าง 1.8 ม. ต้องการความเร็วเดินทาง 18 m/s ช่วยคำนวณ lift ที่ต้องการและวิเคราะห์ว่าออกแบบสมเหตุสมผลไหม"),
    ("gear", "Robotics & Firmware", "inverse kinematics แขนกล 2 ข้อต่อ พร้อมโค้ด และข้อควรระวังเรื่อง singularity และ joint limit",
     "อธิบายและเขียนโค้ด inverse kinematics สำหรับแขนกล 2 ข้อต่อ (2-DOF planar) พร้อมข้อควรระวังเรื่อง singularity และ joint limit"),
    ("film", "Content Production", "สคริปต์วิดีโอสั้น 45 วินาทีเรื่อง AI ในงานวิศวกรรม พร้อม hook, shot list และ call-to-action",
     "เขียนสคริปต์วิดีโอสั้น 45 วินาทีเกี่ยวกับการใช้ AI ในงานวิศวกรรม พร้อม hook, shot list และ call-to-action"),
]

SETUP_TEXT = (
    "ช่องพิมพ์ใช้งานได้ตามปกติ แต่ **AI ยังไม่ตอบ** เพราะยังไม่ได้เชื่อมต่อ API key  \n"
    "Streamlit Cloud: เปิดแอป → **Manage app** → **Settings** → **Secrets** แล้ววาง 2 บรรทัดนี้ จากนั้นกด **Reboot app**"
)
SETUP_CODE = 'ANTHROPIC_API_KEY = "sk-ant-..."\naccess_code = "รหัสผ่านยาว ๆ ที่คุณตั้งเอง"'


def reactor_svg(size: int = 120) -> str:
    return (
        f'<svg class="zy-reactor" width="{size}" height="{size}" viewBox="0 0 120 120" fill="none" '
        'stroke="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        '<g class="zy-spin"><circle cx="60" cy="60" r="57" stroke-opacity=".38" stroke-width=".7" stroke-dasharray="1.4 4.6"/></g>'
        '<g class="zy-spin2"><circle cx="60" cy="60" r="48" stroke-opacity=".6" stroke-width=".9" stroke-dasharray="26 7 3 7"/></g>'
        '<circle cx="60" cy="60" r="39" stroke-opacity=".85" stroke-width="1"/>'
        '<g class="zy-spin"><circle cx="60" cy="60" r="27" stroke-opacity=".28" stroke-width="12" stroke-dasharray="10.6 5.3"/></g>'
        '<circle cx="60" cy="60" r="19" stroke-opacity=".9" stroke-width="1"/>'
        '<circle cx="60" cy="60" r="13" fill="currentColor" fill-opacity=".08" stroke-opacity=".9" stroke-width="1"/>'
        '<circle class="zy-core" cx="60" cy="60" r="5" fill="currentColor" stroke="none"/></svg>'
    )


def greeting() -> str:
    try:
        from zoneinfo import ZoneInfo
        hour = datetime.now(ZoneInfo("Asia/Bangkok")).hour
    except Exception:
        hour = datetime.now().hour
    if 5 <= hour < 11:
        return "สวัสดีตอนเช้าครับ คุณวรกันต์ — ระบบพร้อมรับคำสั่ง"
    if 11 <= hour < 17:
        return "สวัสดีตอนบ่ายครับ คุณวรกันต์ — ระบบพร้อมรับคำสั่ง"
    if 17 <= hour < 21:
        return "สวัสดีตอนเย็นครับ คุณวรกันต์ — ระบบพร้อมรับคำสั่ง"
    return "สวัสดีครับ คุณวรกันต์ — ดึกแล้ว แต่ระบบพร้อมเสมอ"


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
        configured = configured.split(",")
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
    st.markdown(
        f"<div class='zy-hero' style='margin-top:70px'>{reactor_svg(110)}"
        "<div class='zy-wordmark'>Zyphere</div>"
        "<div class='zy-eyebrow'>Security Core · Authorized Personnel Only</div></div><div style='height:26px'></div>",
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        # The app spends API credits, so an email alone (public in the repo) is not enough.
        if get_api_key(st.secrets if _secret("ANTHROPIC_API_KEY") else None) and not access_code:
            st.error("ยังไม่ได้ตั้งค่า `access_code` ใน Secrets — ระบบปิดการเข้าสู่ระบบไว้เพื่อป้องกันการใช้ API key โดยผู้อื่น")
            st.code('access_code = "รหัสผ่านของคุณ"', language="toml")
            st.stop()

        email = st.text_input("Authorized email")
        code = st.text_input("Access code", type="password") if access_code else ""
        if st.button("Authenticate", icon=":material/lock_open:"):
            email_ok = email.strip().lower() in _allowed_emails()
            code_ok = (not access_code) or hmac.compare_digest(code.encode(), str(access_code).encode())
            if email_ok and code_ok:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access denied: unrecognized credentials.")
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
def _label(text: str) -> None:
    st.markdown(f"<div class='zy-eyebrow' style='margin:14px 0 6px'>{html.escape(text)}</div>", unsafe_allow_html=True)


def render_sidebar(memory) -> Settings:
    with st.sidebar:
        st.markdown(f"<div style='display:flex;align-items:center;gap:12px'>{reactor_svg(34)}"
                    "<div><div style='letter-spacing:.32em;font-weight:500'>ZYPHERE</div>"
                    "<div class='zy-eyebrow' style='font-size:9px'>Executive OS</div></div></div>", unsafe_allow_html=True)
        st.markdown("---")

        _label("Intelligence")
        default = _secret("default_model") or DEFAULT_MODEL
        keys = list(MODELS)
        model = st.selectbox("Model", keys, index=keys.index(default) if default in keys else 0,
                             format_func=lambda k: MODELS[k], label_visibility="collapsed")
        deep = st.toggle("Deep analysis", value=False,
                         help="AI วิเคราะห์เป้าหมาย ข้อสมมติ ตัวเลือก และความเสี่ยงก่อนเขียนคำตอบ ช้ากว่าและใช้โควตามากกว่า แต่ลึกกว่า")
        voice = st.toggle("Voice response", value=False, help="อ่านคำตอบออกเสียง (ภาษาไทย)")

        _label("File hub")
        st.caption("ไฟล์ที่แนบจะถูกส่งให้ AI ทุกข้อความ จนกว่าจะลบออก")
        ups = st.file_uploader("Upload", type=SUPPORTED_TYPES, accept_multiple_files=True, label_visibility="collapsed")
        attachments: List[Attachment] = []
        for up in ups or []:
            try:
                att = parse_uploaded_file(up)
                if att:
                    attachments.append(att)
            except ValueError as e:
                st.error(str(e))
        for a in attachments:
            st.markdown(f"<div class='zy-file'>{html.escape(a.name)} · {a.kind.upper()}</div>", unsafe_allow_html=True)

        _label(f"Memory bank · {len(memory):03d}")
        for m in memory.recent(5):
            st.markdown(f"<div class='zy-mem'><span class='ts'>{html.escape(m['timestamp'])}</span><br>"
                        f"{html.escape(m['goal'][:120])}</div>", unsafe_allow_html=True)

        st.markdown("---")
        msgs = st.session_state.get("messages", [])
        if msgs:
            md = "\n\n".join(f"**{'คุณ' if m['role'] == 'user' else 'Zyphere'}:**\n\n{m['content']}" for m in msgs)
            st.download_button("Export chat", md, file_name="zyphere_chat.md", mime="text/markdown", icon=":material/download:")
        if st.button("Purge memory & chat", icon=":material/delete_sweep:"):
            memory.clear()
            st.session_state.messages = []
            st.session_state.turns = 0
            st.rerun()
        if st.button("Sign out", icon=":material/logout:"):
            st.session_state.clear()
            st.rerun()
    return Settings(model=model, deep=deep, voice=voice, attachments=attachments)


# ---------- Main area ----------
def hud(settings: Settings, memory_count: int, online: bool, files: int) -> str:
    model = MODELS[settings.model].split("—")[0].strip().upper()
    status = ("<span class='zy-dot'></span>Online" if online else "<span class='zy-dot off'></span>Offline")
    chips = [f"<span class='zy-chip solid'>{status}</span>" if online else f"<span class='zy-chip'>{status}</span>",
             f"<span class='zy-chip'>{html.escape(model)}</span>",
             f"<span class='zy-chip'>Memory {memory_count:03d}</span>",
             f"<span class='zy-chip'>Files {files:02d}</span>",
             f"<span class='zy-chip'>{'Deep analysis' if settings.deep else 'Standard'}</span>"]
    return "<div class='zy-hud'>" + "".join(chips) + "</div>"


def render_header(settings: Settings, memory_count: int, online: bool, compact: bool) -> None:
    if compact:
        st.markdown(f"<div class='zy-hero'>{reactor_svg(44)}<div class='zy-wordmark small'>Zyphere</div>"
                    + hud(settings, memory_count, online, len(settings.attachments)) + "</div>", unsafe_allow_html=True)
        return
    st.markdown(f"<div class='zy-hero' style='margin-top:14px'>{reactor_svg(132)}<div class='zy-wordmark'>Zyphere</div>"
                "<div class='zy-eyebrow'>Autonomous Executive OS</div>"
                f"<div class='zy-greet'>{html.escape(greeting())}</div>"
                + hud(settings, memory_count, online, len(settings.attachments)) + "</div>", unsafe_allow_html=True)


def render_offline_notice() -> None:
    st.markdown("<div class='zy-notice'><div class='zy-eyebrow' style='margin-bottom:6px'>Brain offline</div>"
                + html.escape(SETUP_TEXT).replace("**", "").replace("  \n", "<br>") + "</div>", unsafe_allow_html=True)
    st.code(SETUP_CODE, language="toml")


def render_welcome() -> Optional[str]:
    """Shown on an empty chat. Returns a prompt if a card was clicked."""
    clicked = None
    cols = st.columns(2)
    for i, (icon, title, desc, prompt) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            st.markdown(f"<div class='zy-card'><svg viewBox='0 0 24 24'>{ICONS[icon]}</svg>"
                        f"<div class='t'>{html.escape(title)}</div><div class='d'>{html.escape(desc)}</div></div>",
                        unsafe_allow_html=True)
            if st.button("Run this brief", key=f"sugg_{i}", icon=":material/arrow_outward:"):
                clicked = prompt
    return clicked


def badges(axis: str, deep: bool) -> str:
    out = f"<span class='zy-chip'>{html.escape(axis)}</span> "
    if deep:
        out += "<span class='zy-chip solid'>Deep analysis</span>"
    return out


def render_history(messages: List[dict]) -> None:
    for m in messages:
        with st.chat_message(m["role"], avatar=USER_AVATAR if m["role"] == "user" else AI_AVATAR):
            if m["role"] == "assistant" and m.get("axis"):
                st.markdown(badges(m["axis"], bool(m.get("reasoning"))), unsafe_allow_html=True)
                if m.get("reasoning"):
                    with st.expander("Analysis trace"):
                        st.markdown(m["reasoning"])
            st.markdown(m["content"])
