"""Dark-neon design system with strict contrast rules."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Thai:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #070b14;
    --bg-soft: #0e1422;
    --card: rgba(22, 30, 48, 0.72);
    --border: rgba(120, 160, 255, 0.16);
    --accent: #00f3ff;
    --accent-2: #7c5cff;
    --text: #f5f8ff;
    --muted: #93a0b8;
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', 'Noto Sans Thai', system-ui, sans-serif;
}
.stApp {
    background:
        radial-gradient(900px 500px at 12% -10%, rgba(124, 92, 255, 0.18), transparent 60%),
        radial-gradient(800px 480px at 95% 0%, rgba(0, 243, 255, 0.12), transparent 55%),
        var(--bg);
    color: var(--text);
}

/* Keep the header (sidebar toggle lives there) but make it invisible chrome */
header[data-testid="stHeader"] { background: transparent !important; }
div[data-testid="stToolbar"], div[data-testid="stDecoration"], #MainMenu, footer { visibility: hidden; }

/* Text contrast */
.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp span, .stMarkdown { color: var(--text); }
.block-container { padding-top: 1.5rem; max-width: 1100px; }

/* Bottom chat bar: remove the default white band */
div[data-testid="stBottom"], div[data-testid="stBottom"] > div,
div[data-testid="stBottomBlockContainer"] { background: transparent !important; }
div[data-testid="stChatInput"] { background: transparent !important; padding-bottom: 12px !important; }
div[data-testid="stChatInput"] > div {
    background: var(--bg-soft) !important;
    border: 1px solid rgba(0, 243, 255, 0.55) !important;
    border-radius: 22px !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.55) !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    box-shadow: 0 0 0 1px var(--accent), 0 0 28px rgba(0, 243, 255, 0.35) !important;
}
div[data-testid="stChatInput"] textarea {
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    background: transparent !important; font-size: 15px !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1120 0%, #080c17 100%) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text); }
section[data-testid="stSidebar"] small, .zy-muted { color: var(--muted) !important; }

/* File uploader */
div[data-testid="stFileUploader"] section {
    background: var(--card) !important; border: 1.5px dashed rgba(0, 243, 255, 0.6) !important; border-radius: 12px !important;
}
div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] div { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
div[data-testid="stFileUploader"] button {
    background: #ffffff !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important;
    font-weight: 700 !important; border-radius: 8px !important;
}

/* Inputs (login) */
div[data-baseweb="input"] { background: #ffffff !important; border-radius: 10px !important; border: 2px solid var(--accent) !important; }
div[data-baseweb="input"] input {
    color: #000000 !important; -webkit-text-fill-color: #000000 !important;
    background: transparent !important; font-weight: 600 !important;
}
div[data-baseweb="select"] > div { background: var(--bg-soft) !important; border-color: var(--border) !important; }
div[data-baseweb="select"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }

/* Buttons */
div.stButton > button, div.stDownloadButton > button {
    background: #ffffff !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important;
    border: 1.5px solid var(--accent) !important; border-radius: 10px !important; font-weight: 700 !important;
    width: 100% !important; transition: all .2s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    background: var(--accent) !important; box-shadow: 0 0 18px rgba(0, 243, 255, 0.55);
}

/* Chat messages as glass cards */
div[data-testid="stChatMessage"] {
    background: var(--card); border: 1px solid var(--border); border-radius: 16px;
    padding: 14px 18px; margin-bottom: 12px; backdrop-filter: blur(10px);
}

/* Code */
pre, code, div[data-testid="stCode"] {
    background: #030712 !important; color: #8be9ff !important; border-radius: 10px !important;
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace !important;
}
pre { border: 1px solid #1f2937 !important; }

/* Expander (reasoning) */
div[data-testid="stExpander"] { background: rgba(124, 92, 255, 0.07); border: 1px solid rgba(124, 92, 255, 0.3); border-radius: 12px; }

/* Brand pieces */
.zy-title {
    font-weight: 700; letter-spacing: 1.5px; text-align: center; margin: 0;
    background: linear-gradient(90deg, #ffffff 0%, var(--accent) 45%, var(--accent-2) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent !important; -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 18px rgba(0, 243, 255, 0.35));
}
.zy-sub { text-align: center; color: var(--muted) !important; font-size: 14px; margin: 6px 0 22px; }
.zy-badge {
    display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600;
    background: rgba(0, 243, 255, 0.1); border: 1px solid rgba(0, 243, 255, 0.45); color: var(--accent) !important; margin-right: 6px;
}
.zy-badge.deep { background: rgba(124, 92, 255, 0.14); border-color: rgba(124, 92, 255, 0.6); color: #b9a8ff !important; }
.zy-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 12px 14px; margin-bottom: 8px;
}
.zy-mem { background: var(--card); padding: 8px 10px; border-radius: 8px; margin-bottom: 6px; font-size: 11px; border-left: 3px solid var(--accent); }
</style>
"""


def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
