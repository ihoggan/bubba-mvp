"""View Investigation page — Full narrative display of a saved case."""

import streamlit as st

from bubba.diagnosis.infrastructure.repository import InvestigationRepository
from bubba.diagnosis.web.wording import belief_emoji

st.set_page_config(page_title="View Investigation", layout="wide")

st.title("📖 View Investigation")

repo = InvestigationRepository()

# Get investigation ID from session or selectbox
if "investigation_id" not in st.session_state:
    all_cases = repo.list_all()
    if not all_cases:
        st.error("No investigations found.")
        st.stop()
    
    selected = st.selectbox(
        "Select investigation to view",
        options=[c["id"] for c in all_cases],
        format_func=lambda id: next((c["title"] for c in all_cases if c["id"] == id), id)
    )
    st.session_state.investigation_id = selected

investigation_id = st.session_state.investigation_id

# Load full investigation
investigation = repo.get_by_id(investigation_id)

if not investigation:
    st.error("Investigation not found.")
    st.stop()

# ============================================================================
# HEADER
# ============================================================================
st.write(f"### {investigation.title}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    status_emoji = "🔍" if investigation.status.value in ["investigating", "characterising"] else "✅"
    st.metric(f"{status_emoji} Status", investigation.status.value.upper())
with col2:
    confirmed_emoji = "✅" if investigation.engineer_confirmed else "❌"
    st.metric(f"{confirmed_emoji} Confirmed", "Yes" if investigation.engineer_confirmed else "No")
with col3:
    has_root = "✅" if investigation.root_cause else "❌"
    st.metric(f"{has_root} Root Cause", "Identified" if investigation.root_cause else "Pending")
with col4:
    st.metric("Hypotheses", len(investigation.hypotheses))

st.divider()

# ============================================================================
# SECTION 1: THE INCIDENT
# ============================================================================
st.subheader("📋 The Incident")

col1, col2 = st.columns([2, 1])

with col1:
    st.write(f"**Problem:** {investigation.symptom.what_is_wrong}")
    st.write(f"**Expected:** {investigation.symptom.expected_behaviour}")
    st.write(f"**Actual:** {investigation.symptom.actual_behaviour}")
    st.write(f"**Scope:** {investigation.symptom.affected_scope}")
    
    if investigation.root_cause:
        st.write(f"**Root Cause:** {investigation.root_cause}")
    else:
        st.info("Root cause not yet identified")

with col2:
    st.write("**Investigation State:**")
    st.write(f"Status: `{investigation.status.value}`")
    st.write(f"Confirmed: `{investigation.engineer_confirmed}`")

st.divider()

# ============================================================================
# SECTION 2: TIMELINE
# ============================================================================
st.subheader("🔬 Investigation Timeline")
st.caption("Chronological record of events")

if investigation.timeline:
    for event in investigation.timeline:
        with st.expander(f"📌 {event.event_type}"):
            st.write(event.summary)
            if event.payload:
                st.write(event.payload)
else:
    st.info("No timeline events yet.")

st.divider()

# ============================================================================
# SECTION 3: HYPOTHESES
# ============================================================================
st.subheader("🧩 Hypotheses Explored")
st.caption("Candidate explanations and their evidence")

if investigation.hypotheses:
    for hypothesis in investigation.hypotheses:
        status_icon = {
            "confirmed": "✅",
            "active": "🔍",
            "weakened": "↘️",
            "ruled_out": "🚫"
        }.get(hypothesis.status.value, "•")
        
        with st.container(border=True):
            st.write(f"{status_icon} **{hypothesis.statement}**")
            belief_label = belief_emoji(hypothesis.belief.value)
            st.write(f"Current belief: {belief_label}")
            
            if hypothesis.supporting_evidence:
                st.write("**Evidence that supports:**")
                # Note: full evidence objects would need to be loaded from executions
                st.write(f"  {len(hypothesis.supporting_evidence)} pieces of supporting evidence")
            
            if hypothesis.contradicting_evidence:
                st.write("**Evidence that contradicts:**")
                st.write(f"  {len(hypothesis.contradicting_evidence)} pieces of contradicting evidence")
else:
    st.info("No hypotheses defined yet.")

st.divider()

# ============================================================================
# SECTION 4: TESTS & INTERVENTIONS
# ============================================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧪 Tests Run")
    st.write(f"**Total: {len(investigation.executions)}**")
    for execution in investigation.executions:
        st.write(f"• {execution.observation}")

with col2:
    st.subheader("🔧 Interventions")
    st.write(f"**Total: {len(investigation.interventions)}**")
    for intervention in investigation.interventions:
        status_icon = "✅" if intervention.status.value == "verified_effective" else "⚠️"
        st.write(f"{status_icon} {intervention.description}")
        st.caption(f"Status: {intervention.status.value}")

st.divider()

# ============================================================================
# SECTION 5: EXPORT & ACTIONS
# ============================================================================
st.subheader("📤 Actions")

if investigation.engineer_confirmed and investigation.root_cause:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Export to JSON", type="primary", use_container_width=True):
            st.info("Exporting to KB format...")
            st.json({
                "id": str(investigation.id),
                "title": investigation.title,
                "symptom": investigation.symptom.what_is_wrong,
                "root_cause": investigation.root_cause,
                "status": investigation.status.value,
                "engineer_confirmed": investigation.engineer_confirmed,
                "hypotheses": len(investigation.hypotheses),
                "tests": len(investigation.executions),
            })
            st.success("✅ Ready to ingest into Bubba Core KB")
    
    with col2:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.investigation_id = investigation_id
            st.switch_page("pages/02_edit_investigation.py")
    
    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
else:
    st.warning("⚠️ Export requires: confirmed diagnosis + root cause identified")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Edit to Complete", type="primary", use_container_width=True):
            st.session_state.investigation_id = investigation_id
            st.switch_page("pages/02_edit_investigation.py")
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
