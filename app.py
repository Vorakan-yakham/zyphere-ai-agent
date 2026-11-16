import streamlit as st
from core.brain import ask_zyphere
from core.persona import SYSTEM_PROMPT
from core.memory import load_memory

st.set_page_config(page_title="ZYP HERE", page_icon="🧠")
st.title("🧠 ZYP HERE - AI ของ Vorakan")
st.caption("V3 | เริ่มจาก 0 | อัพเดทไปเรื่อยๆ จนแซง Jarvis")

memory = load_memory()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\nความจำ: {memory}"}
    ]

for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("พิมพ์สั่ง Zyphere...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ask_zyphere(st.session_state.messages)
        full = st.write_stream([c['message']['content'] for c in response])
        st.session_state.messages.append({"role": "assistant", "content": full})
