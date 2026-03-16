from __future__ import annotations

import streamlit as st

from ui import render_admin_page, render_agent_dashboard, render_client_portal

st.set_page_config(page_title="DealFlow AI", layout="wide")
st.title("DealFlow AI")
st.caption("AI-assisted deal flow demo with conversation intelligence, policy retrieval, eligibility checks, and routed tasks.")

page = st.sidebar.radio(
    "Page",
    options=["Client Portal", "Agent Dashboard", "Admin Page"],
)

if page == "Client Portal":
    render_client_portal()
elif page == "Agent Dashboard":
    render_agent_dashboard()
else:
    render_admin_page()
