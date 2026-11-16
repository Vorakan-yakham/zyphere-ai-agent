"""Monochrome luxury design system (black / graphite / white) with strict contrast."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Noto+Sans+Thai:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #050506;
    --s1: #0b0b0d;
    --s2: #121215;
    --line: rgba(255, 255, 255, 0.10);
    --line2: rgba(255, 255, 255, 0.24);
    --text: #f1f1f1;
    --muted: #8b8b93;
    --mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
}

html, body, [class*="css"], .stApp { font-family: 'Inter', 'Noto Sans Thai', system-ui, sans-serif; }
.stApp {
    color: var(--text);
    background:
        radial-gradient(1100px 620px at 50% -18%, rgba(255, 255, 255, 0.075), transparent 62%),
        linear-gradient(rgba(255, 255, 255, 0.022) 1px, transparent 1px) 0 0 / 56px 56px,
        linear-gradient(90deg, rgba(255, 255, 255, 0.022) 1px, transparent 1px) 0 0 / 56px 56px,
        var(--bg);
}
.block-container { max-width: 1040px; padding-top: 4rem; }

/* Header stays (it holds the sidebar toggle) but is invisible chrome */
header[data-testid="stHeader"] { background: transparent !important; pointer-events: none; }
header[data-testid="stHeader"] * { pointer-events: auto; }
div[data-testid="stToolbar"], div[data-testid="stDecoration"], #MainMenu, footer { visibility: hidden; }

.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp span, .stMarkdown { color: var(--text); }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #26262b; border-radius: 4px; }

/* ---- bottom chat bar (no white band) ---- */
div[data-testid="stBottom"], div[data-testid="stBottom"] > div, div[data-testid="stBottomBlockContainer"] { background: transparent !important; }
div[data-testid="stChatInput"] { background: transparent !important; padding-bottom: 14px !important; }
div[data-testid="stChatInput"] > div {
    background: var(--s1) !important; border: 1px solid var(--line2) !important; border-radius: 8px !important;
    box-shadow: 0 14px 44px rgba(0, 0, 0, 0.7) !important;
}
div[data-testid="stChatInput"] > div:focus-within { border-color: #ffffff !important; box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.08), 0 14px 44px rgba(0, 0, 0, 0.7) !important; }
div[data-testid="stChatInput"] textarea {
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; background: transparent !important; font-size: 15px !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important; }
div[data-testid="stChatInput"] button { color: #ffffff !important; }

/* ---- sidebar ---- */
section[data-testid="stSidebar"] { background: #070708 !important; border-right: 1px solid var(--line) !important; }
section[data-testid="stSidebar"] * { color: var(--text); }
section[data-testid="stSidebar"] small, .zy-muted { color: var(--muted) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--line) !important; }

/* ---- uploader ---- */
div[data-testid="stFileUploader"] section { background: var(--s1) !important; border: 1px dashed var(--line2) !important; border-radius: 6px !important; }
div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] div {
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
}

/* ---- inputs ---- */
div[data-baseweb="input"] { background: var(--s1) !important; border: 1px solid var(--line2) !important; border-radius: 6px !important; }
div[data-baseweb="input"]:focus-within { border-color: #ffffff !important; }
div[data-baseweb="input"] input { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; background: transparent !important; }
div[data-baseweb="select"] > div { background: var(--s1) !important; border: 1px solid var(--line2) !important; border-radius: 6px !important; }
div[data-baseweb="select"] * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
div[data-baseweb="popover"] * { color: #ffffff !important; }
div[data-baseweb="popover"] ul { background: var(--s2) !important; }

/* ---- buttons: ghost, invert on hover ---- */
div.stButton > button, div.stDownloadButton > button {
    background: transparent !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    border: 1px solid var(--line2) !important; border-radius: 6px !important; font-weight: 500 !important;
    letter-spacing: 0.04em; width: 100% !important; transition: all .18s ease;
}
div.stButton > button *, div.stDownloadButton > button * { color: inherit !important; -webkit-text-fill-color: inherit !important; }
div.stButton > button:hover, div.stDownloadButton > button:hover {
    background: #ffffff !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important;
    border-color: #ffffff !important; box-shadow: 0 0 24px rgba(255, 255, 255, 0.25);
}

/* ---- chat messages ---- */
div[data-testid="stChatMessage"] {
    background: var(--s1); border: 1px solid var(--line); border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: transparent; border-color: transparent; border-left: 1px solid var(--line2); border-radius: 0;
}
[data-testid^="stChatMessageAvatar"] {
    background: transparent !important; border: 1px solid var(--line2) !important; color: #ffffff !important; border-radius: 50% !important;
}
[data-testid^="stChatMessageAvatar"] * { color: #ffffff !important; }

/* ---- code ---- */
pre, code, div[data-testid="stCode"] { background: #000000 !important; color: #e8e8ea !important; font-family: var(--mono) !important; border-radius: 6px !important; }
pre { border: 1px solid var(--line) !important; }
pre code span { color: #e8e8ea !important; }

/* ---- expander / status ---- */
div[data-testid="stExpander"], div[data-testid="stStatus"] { background: var(--s1) !important; border: 1px solid var(--line) !important; border-radius: 6px !important; }
div[data-testid="stExpander"] summary, div[data-testid="stStatus"] summary { font-family: var(--mono); font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; }

/* ---- brand ---- */
.zy-hero { text-align: center; padding: 6px 0 4px; }
.zy-wordmark {
    font-weight: 300; font-size: 30px; letter-spacing: 0.55em; text-transform: uppercase; margin: 10px 0 4px; padding-left: 0.55em;
    color: #ffffff !important; text-shadow: 0 0 28px rgba(255, 255, 255, 0.28);
}
.zy-wordmark.small { font-size: 20px; margin: 4px 0 2px; }
.zy-eyebrow { font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.3em; text-transform: uppercase; color: var(--muted) !important; }
.zy-greet { font-weight: 300; font-size: 19px; color: var(--text) !important; margin: 18px 0 14px; letter-spacing: 0.01em; }
.zy-hud { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin: 12px 0 22px; }
.zy-chip {
    display: inline-flex; align-items: center; gap: 7px; font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.16em; text-transform: uppercase;
    border: 1px solid var(--line2); border-radius: 3px; padding: 4px 10px; color: #d6d6da !important; background: rgba(255, 255, 255, 0.02);
}
.zy-chip.solid { background: #ffffff; color: #000000 !important; border-color: #ffffff; }
.zy-dot { width: 6px; height: 6px; border-radius: 50%; background: #ffffff; box-shadow: 0 0 8px #ffffff; animation: zy-pulse 2.2s ease-in-out infinite; }
.zy-chip.solid .zy-dot { background: #000000; box-shadow: none; }
.zy-dot.off { background: #55555c; box-shadow: none; animation: none; }
.zy-card { background: var(--s1); border: 1px solid var(--line); border-radius: 6px; padding: 16px 18px; margin-bottom: 8px; min-height: 104px; transition: border-color .2s; }
.zy-card:hover { border-color: var(--line2); }
.zy-card svg { width: 22px; height: 22px; stroke: #ffffff; fill: none; stroke-width: 1.4; stroke-linecap: round; stroke-linejoin: round; margin-bottom: 10px; }
.zy-card .t { font-weight: 500; letter-spacing: 0.05em; margin-bottom: 4px; }
.zy-card .d { color: var(--muted) !important; font-size: 12.5px; line-height: 1.55; }
.zy-notice { border: 1px solid var(--line2); border-left: 3px solid #ffffff; border-radius: 4px; background: var(--s1); padding: 14px 18px; margin: 6px 0 16px; }
.zy-notice b { letter-spacing: 0.04em; }
.zy-mem { background: var(--s1); padding: 8px 10px; border-radius: 4px; margin-bottom: 6px; font-size: 11.5px; border-left: 2px solid var(--line2); line-height: 1.5; }
.zy-mem .ts { font-family: var(--mono); font-size: 10px; color: var(--muted) !important; letter-spacing: 0.06em; }
.zy-file { font-family: var(--mono); font-size: 11px; letter-spacing: 0.04em; border: 1px solid var(--line); border-radius: 3px; padding: 5px 9px; margin-bottom: 5px; color: #d6d6da !important; }

/* primary (emergency) button + segmented view switch */
div.stButton > button[data-testid="stBaseButton-primary"] {
    background: #ffffff !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-weight: 700 !important; letter-spacing: .12em;
}
div.stButton > button[data-testid="stBaseButton-primary"]:hover { box-shadow: 0 0 28px rgba(255,255,255,.55); }
div[data-testid="stSegmentedControl"] { justify-content: center; margin: 0 0 18px; }
div[data-testid="stSegmentedControl"] button {
    background: transparent !important; border: 1px solid var(--line2) !important; color: #d6d6da !important; border-radius: 3px !important;
    font-family: var(--mono); font-size: 11px; letter-spacing: .2em; text-transform: uppercase;
}
div[data-testid="stSegmentedControl"] button[aria-checked="true"], div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background: #ffffff !important; color: #000000 !important; border-color: #ffffff !important;
}
div[data-testid="stSegmentedControl"] button[aria-checked="true"] *, div[data-testid="stSegmentedControl"] button[aria-pressed="true"] * { color: #000000 !important; }
div[data-testid="stProgressBarTrack"] { background: rgba(255,255,255,.12) !important; }
div[data-testid="stProgressBarTrack"] > div { background: #ffffff !important; }
div[data-testid="stAudioInput"] { background: var(--s1) !important; border: 1px solid var(--line2) !important; border-radius: 6px !important; }
div[data-testid="stAudioInput"] * { color: #ffffff !important; }
.zy-log { display: flex; gap: 10px; align-items: baseline; padding: 7px 0; border-bottom: 1px solid var(--line); font-size: 13px; line-height: 1.5; }
.zy-log .ts { font-family: var(--mono); font-size: 10.5px; color: var(--muted) !important; white-space: nowrap; }
.zy-log .zy-chip { flex: none; }

/* reactor animation */
.zy-reactor { color: #ffffff; filter: drop-shadow(0 0 14px rgba(255, 255, 255, 0.35)); }
.zy-spin  { transform-origin: 60px 60px; animation: zy-rot 38s linear infinite; }
.zy-spin2 { transform-origin: 60px 60px; animation: zy-rot 24s linear infinite reverse; }
.zy-core  { animation: zy-pulse 2.6s ease-in-out infinite; }
@keyframes zy-rot { to { transform: rotate(360deg); } }
@keyframes zy-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
@media (prefers-reduced-motion: reduce) { .zy-spin, .zy-spin2, .zy-core, .zy-dot { animation: none; } }
</style>
"""


def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
