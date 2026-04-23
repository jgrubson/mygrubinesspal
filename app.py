import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="MyGrubinessPal",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """<style>
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        visibility: hidden !important; height: 0 !important; position: fixed !important;
    }
    .stApp > header { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    iframe { border: none !important; }
    </style>""",
    unsafe_allow_html=True,
)

html = Path("frontend.html").read_text(encoding="utf-8")
html = html.replace("{{SUPABASE_URL}}", st.secrets["SUPABASE_URL"])
html = html.replace("{{SUPABASE_KEY}}", st.secrets["SUPABASE_KEY"])

st.html(html, height=4000)
