"""Zyphere Autonomous Executive OS - main entry point & UI controller."""
import streamlit as st

st.set_page_config(
    page_title="Zyphere Autonomous Executive OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core import MemoryBank, ZyphereAdvancedEngine  # noqa: E402
from ui.components import (  # noqa: E402
    auth_gate, generate_audio_response, render_audio_player, render_header, render_sidebar,
)
from ui.styles import inject_styles  # noqa: E402

inject_styles()
auth_gate()

if "memory" not in st.session_state:
    st.session_state.memory = MemoryBank()  # loads persisted records from data/memory.json
st.session_state.setdefault("messages", [])

memory = st.session_state.memory
file_data = render_sidebar(memory)
render_header()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Zyphere Autonomous Core กำลังอ่านไฟล์และประมวลผลเชิงลึก..."):
            result = ZyphereAdvancedEngine(memory).execute_pipeline(user_input, file_data)
            # Use a longer fence so backticks inside user/file content can't break the block
            output = (
                f"{result['summary']}\n\n"
                f"````python\n{result['code']}\n````\n\n"
                "ระบบพร้อมรับบรีฟหรือคำสั่งขยายผลในขั้นต่อไปแล้วครับ บรีฟงานถัดมาได้เลยครับคุณวรกันต์!"
            )
            st.markdown(output)
            render_audio_player(generate_audio_response("วิเคราะห์ไฟล์และประมวลผลระบบเรียบร้อยแล้วครับ"))
            st.session_state.messages.append({"role": "assistant", "content": output})
