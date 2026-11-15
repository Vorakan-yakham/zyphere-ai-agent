"""Zyphere Autonomous Executive OS - main entry point & UI controller."""
import streamlit as st

st.set_page_config(
    page_title="Zyphere Autonomous Executive OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core import LLM, LLMError, MemoryBank, ZyphereAdvancedEngine, get_api_key  # noqa: E402
from ui.components import (  # noqa: E402
    MAX_TURNS_PER_SESSION, auth_gate, badges, render_header, render_history,
    render_sidebar, render_welcome, speak,
)
from ui.styles import inject_styles  # noqa: E402

inject_styles()
auth_gate()

st.session_state.setdefault("messages", [])
st.session_state.setdefault("turns", 0)
if "memory" not in st.session_state:
    st.session_state.memory = MemoryBank()  # persisted in data/memory.json
memory = st.session_state.memory

try:
    api_key = get_api_key(st.secrets)
except Exception:
    api_key = get_api_key(None)

settings = render_sidebar(memory, has_llm=bool(api_key))
render_header()

suggestion = None
if not st.session_state.messages:
    suggestion = render_welcome()
render_history(st.session_state.messages)

limit_hit = st.session_state.turns >= MAX_TURNS_PER_SESSION
if limit_hit:
    st.warning("ถึงขีดจำกัดจำนวนข้อความของเซสชันนี้แล้ว กด Purge Memory & Chat หรือ Sign out เพื่อเริ่มใหม่")

prompt = st.chat_input("บรีฟงาน ถามคำถาม หรือแนบไฟล์ในแถบข้าง…", disabled=(not api_key) or limit_hit) or suggestion

if prompt:
    history = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            engine = ZyphereAdvancedEngine(memory, LLM(api_key, settings.model))
            axis = engine.classify_axis(prompt, settings.attachments)
            st.markdown(badges(axis, settings.deep), unsafe_allow_html=True)

            plan = None
            if settings.deep:
                with st.status("🧠 กำลังวิเคราะห์เชิงลึก…", expanded=False) as status:
                    plan = engine.plan(history, prompt, settings.attachments, axis)
                    st.markdown(plan)
                    status.update(label="🧠 วิเคราะห์เสร็จแล้ว — กำลังเรียบเรียงคำตอบ", state="complete")

            answer = st.write_stream(
                engine.stream_answer(history, prompt, settings.attachments, axis, plan,
                                     max_tokens=8000 if settings.deep else 4096)
            )
            answer = answer if isinstance(answer, str) else "".join(str(x) for x in answer)

            engine.record(prompt, axis, settings.attachments, answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "axis": axis, "reasoning": plan}
            )
            st.session_state.turns += 1
            if settings.voice:
                speak(answer)
        except LLMError as e:
            st.error(str(e))
            st.session_state.messages.pop()  # don't keep an unanswered user turn in history
