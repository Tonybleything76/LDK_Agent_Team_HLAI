"""
LD Course Factory — Streamlit UI
Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="LD Course Factory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Page registry ──────────────────────────────────────────────────────────────
from ui.pages.new_run import render as render_new_run
from ui.pages.run_history import render as render_history
from ui.pages.view_run import render as render_view_run

PAGES = {
    "New Run": render_new_run,
    "Run History": render_history,
}

# ── Sidebar nav ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏭 LD Course Factory")
    st.caption("Multi-agent course development pipeline")
    st.divider()
    page = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("v" + open("VERSION").read().strip() if __import__("os").path.exists("VERSION") else "")

# ── Route ──────────────────────────────────────────────────────────────────────
# Allow deep-linking into a specific run view via session state
if st.session_state.get("view_run"):
    render_view_run(st.session_state["view_run"])
else:
    PAGES[page]()
