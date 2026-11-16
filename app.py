# ZYPHERE V55 - GITHUB VERSION - SAME META AI EXACT UI
import streamlit as st, pathlib
st.set_page_config(page_title='Zyphere', page_icon='✦', layout='wide', initial_sidebar_state='collapsed')
html = pathlib.Path(__file__).parent.joinpath('index.html').read_text(encoding='utf-8')
# Remove Streamlit sidebar/header so the HTML clone fills the screen like meta.ai
st.markdown("<style>[data-testid='stSidebar']{display:none} [data-testid='stToolbar']{display:none} footer{display:none} .main .block-container{padding:0!important;max-width:100%!important}</style>", unsafe_allow_html=True)
import streamlit.components.v1 as components
components.html(html, height=900, scrolling=True)
