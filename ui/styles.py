"""Strict Dark-Neon CSS with contrast overrides."""
import streamlit as st

CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp { background-color: #0b0f19; color: #ffffff !important; }

label, p, span, div, h1, h2, h3, h4, h5, h6, .stMarkdown { color: #ffffff !important; }

section[data-testid="stSidebar"] {
    background-color: #0e1117 !important;
    border-right: 1px solid #30363d !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] small { color: #ffffff !important; }

div[data-testid="stFileUploader"] {
    background-color: #161b22 !important;
    border: 2px dashed #00f3ff !important;
    border-radius: 10px !important;
    padding: 10px !important;
}
div[data-testid="stFileUploader"] section { background-color: #161b22 !important; }
div[data-testid="stFileUploader"] span,
div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
div[data-testid="stFileUploader"] button {
    background-color: #ffffff !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
}

div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border-radius: 8px !important;
    border: 2px solid #00f3ff !important;
}
div[data-baseweb="input"] input {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    background-color: transparent !important;
    font-weight: 700 !important;
}

div[data-testid="stChatInput"] { background-color: transparent !important; padding-bottom: 20px !important; }
div[data-testid="stChatInput"] > div {
    background-color: #161b22 !important;
    border: 1px solid #00f3ff !important;
    border-radius: 24px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
    padding: 6px 14px !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border: 1px solid #00f3ff !important;
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.5) !important;
}
div[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background-color: transparent !important;
    font-size: 15px !important;
}

pre, code, .stCodeBlock, div[data-testid="stCode"] {
    background-color: #030712 !important;
    color: #00f3ff !important;
    border: 1px solid #1f2937 !important;
    border-radius: 10px !important;
    font-family: 'Fira Code', 'Courier New', Courier, monospace !important;
}
pre code span { color: #38bdf8 !important; }

div.stButton > button {
    background-color: #ffffff !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    border: 2px solid #00f3ff !important;
    width: 100% !important;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background-color: #00f3ff !important;
    color: #000000 !important;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.6);
}

.neon-glow { text-shadow: 0 0 20px rgba(0, 243, 255, 0.6); }
</style>
"""


def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
