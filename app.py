"""Zyphere Autonomous Executive OS - main entry point & UI controller."""
import hashlib

import streamlit as st

st.set_page_config(
    page_title="Zyphere Autonomous Executive OS",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core import (  # noqa: E402
    LLM, Brain, Guard, LLMError, MemoryBank, Scheduler, Store, ZyphereAdvancedEngine, get_api_key,
)
from core import commands  # noqa: E402
from core.voice import VoiceError, transcribe  # noqa: E402
from ui.cognition import render_cognition, render_skills, state_of  # noqa: E402
from ui.components import (  # noqa: E402
    AI_AVATAR, MAX_TURNS_PER_SESSION, USER_AVATAR, auth_gate, badges, render_header, render_history,
    render_offline_notice, render_sidebar, render_welcome, speak,
)
from ui.styles import inject_styles  # noqa: E402

inject_styles()
auth_gate()


@st.cache_resource(show_spinner=False)
def get_scheduler(api_key: str, db_path: str) -> Scheduler:
    """One background loop per server process (shared by all browser sessions)."""
    store = Store(db_path)
    guard = Guard(store)
    brain = Brain(store, guard, lambda model: LLM(api_key, model))
    sched = Scheduler(store, guard, brain)
    sched.start()
    return sched


st.session_state.setdefault("messages", [])
st.session_state.setdefault("turns", 0)
st.session_state.setdefault("mic_n", 0)
if "memory" not in st.session_state:
    st.session_state.memory = MemoryBank()  # SQLite: data/zyphere.db
memory = st.session_state.memory
guard = Guard(memory)

try:
    api_key = get_api_key(st.secrets)
except Exception:
    api_key = get_api_key(None)
online = bool(api_key)

scheduler = get_scheduler(api_key, memory.path) if online else None
brain = Brain(memory, guard, lambda model: LLM(api_key, model)) if online else None

settings = render_sidebar(memory)
auto_state = state_of(guard)

VIEWS = ["Console", "Cognition", "Skills"]
view = st.segmented_control("View", VIEWS, default="Console", key="view", label_visibility="collapsed") or "Console"

has_chat = bool(st.session_state.messages)
header_slot = st.empty()
with header_slot.container():
    render_header(settings, len(memory), online, compact=(has_chat or view != "Console"), auto=auto_state)

if not online:
    render_offline_notice()

if view == "Cognition":
    render_cognition(memory, guard, scheduler, brain, online)
    st.stop()
if view == "Skills":
    render_skills(memory, brain, online)
    st.stop()

# ------------------------------- Console ----------------------------------
suggestion = None
welcome_slot = st.empty()
if not has_chat:
    with welcome_slot.container():
        suggestion = render_welcome()
render_history(st.session_state.messages)

# Voice input: record -> transcribe -> treated exactly like typed text
voice_prompt = None
with st.expander("Voice input", icon=":material/mic:"):
    audio = st.audio_input("Speak", key=f"mic_{st.session_state.mic_n}", label_visibility="collapsed")
if audio is not None:
    data = audio.getvalue()
    digest = hashlib.sha1(data).hexdigest()
    if digest != st.session_state.get("last_audio"):
        st.session_state.last_audio = digest
        try:
            with st.spinner("กำลังฟัง…"):
                voice_prompt = transcribe(data, settings.lang)
            st.session_state.mic_n += 1  # resets the recorder for the next utterance
        except VoiceError as e:
            st.warning(str(e))

limit_hit = st.session_state.turns >= MAX_TURNS_PER_SESSION
if limit_hit:
    st.warning("ถึงขีดจำกัดจำนวนข้อความของเซสชันนี้แล้ว กด Purge memory & chat หรือ Sign out เพื่อเริ่มใหม่")

# The input is never disabled by a missing key: that made the app look broken.
prompt = st.chat_input("บรีฟงาน ถามคำถาม สั่ง /help หรือแนบไฟล์ในแถบข้าง…", disabled=limit_hit) or suggestion or voice_prompt

if prompt:
    welcome_slot.empty()
    with header_slot.container():
        render_header(settings, len(memory), online, compact=True, auto=auto_state)

    # Local commands (/kill, /status, "หยุดฉุกเฉิน", ...) never reach the LLM
    reply = commands.handle(prompt, memory, guard, brain, scheduler)
    if reply is not None:
        st.session_state.messages.append({"role": "user", "content": prompt, "local": True})
        st.session_state.messages.append({"role": "assistant", "content": reply, "axis": "System", "local": True})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=AI_AVATAR):
            st.markdown(badges("System", False), unsafe_allow_html=True)
            st.markdown(reply)
        if settings.voice:
            speak(reply)
        st.stop()

    if not online:
        st.toast("ยังไม่ได้เชื่อมต่อสมอง AI — ดูวิธีตั้งค่าด้านบน", icon=":material/info:")
        st.stop()

    history = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AI_AVATAR):
        try:
            engine = ZyphereAdvancedEngine(memory, LLM(api_key, settings.model))
            axis = engine.classify_axis(prompt, settings.attachments)
            st.markdown(badges(axis, settings.deep), unsafe_allow_html=True)

            plan = None
            if settings.deep:
                with st.status("กำลังวิเคราะห์เชิงลึก…", expanded=False) as status:
                    plan = engine.plan(history, prompt, settings.attachments, axis)
                    st.markdown(plan)
                    status.update(label="วิเคราะห์เสร็จแล้ว — กำลังเรียบเรียงคำตอบ", state="complete")

            answer = st.write_stream(
                engine.stream_answer(history, prompt, settings.attachments, axis, plan,
                                     max_tokens=8000 if settings.deep else 4096)
            )
            answer = answer if isinstance(answer, str) else "".join(str(x) for x in answer)

            engine.record(prompt, axis, settings.attachments, answer)
            with header_slot.container():  # refresh the memory counter
                render_header(settings, len(memory), online, compact=True, auto=auto_state)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "axis": axis, "reasoning": plan}
            )
            st.session_state.turns += 1
            if settings.voice:
                speak(answer)
        except LLMError as e:
            st.error(str(e))
            st.session_state.messages.pop()  # don't keep an unanswered user turn in history
