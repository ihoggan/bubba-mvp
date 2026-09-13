"""Streamlit home page — Investigation dashboard."""

import streamlit as st

st.set_page_config(page_title="Bubba.Diagnosis", layout="wide")

st.title("📋 Bubba.Diagnosis")
st.caption("Evidence-driven incident investigation — solo technician tool")

st.write("""
### Welcome to your investigation workspace

Use the sidebar to navigate:

- **New Investigation** — Start investigating a new incident
- **Edit Investigation** — Continue work on an existing case
- **View Investigation** — Open a saved case in full detail
- **Search Cases** — Find similar incidents by symptom or root cause
""")

st.divider()

st.subheader("🎯 Quick Stats")

from bubba.diagnosis.infrastructure.repository import InvestigationRepository

repo = InvestigationRepository()
all_cases = repo.list_all()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Cases", len(all_cases))
with col2:
    confirmed = sum(1 for c in all_cases if c["engineer_confirmed"])
    st.metric("Confirmed Diagnoses", confirmed)
with col3:
    st.metric("Root Causes Identified", sum(1 for c in all_cases if c["root_cause"]))

if all_cases:
    st.write("**Recent cases:**")
    for case in all_cases[:5]:
        st.write(f"• **{case['title']}** — {case['status']}")
else:
    st.info("No cases yet. Start with 'New Investigation' to begin.")
