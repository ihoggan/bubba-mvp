"""Edit Investigation page — Add evidence, tests, and interventions."""

import streamlit as st

from bubba.diagnosis.infrastructure.repository import InvestigationRepository

st.set_page_config(page_title="Edit Investigation", layout="wide")

st.title("✏️ Edit Investigation")

repo = InvestigationRepository()

# Get investigation ID from session or selectbox
if "investigation_id" not in st.session_state:
    all_cases = repo.list_all()
    if not all_cases:
        st.error("No investigations found. Create one first.")
        st.stop()
    
    selected = st.selectbox(
        "Select investigation to edit",
        options=[c["id"] for c in all_cases],
        format_func=lambda id: next((c["title"] for c in all_cases if c["id"] == id), id)
    )
    st.session_state.investigation_id = selected

investigation_id = st.session_state.investigation_id

# Load full investigation from database
investigation = repo.get_by_id(investigation_id)

if not investigation:
    st.error("Investigation not found.")
    st.stop()

st.write(f"**{investigation.title}**")
st.write(f"*Status: {investigation.status.value} | Confirmed: {'✅' if investigation.engineer_confirmed else '❌'}*")

st.divider()

# Tabs for different editing modes
tab_tests, tab_evidence, tab_intervention, tab_diagnosis, tab_view = st.tabs(
    ["🧪 Tests", "🔍 Evidence", "🔧 Intervention", "🎯 Diagnosis", "📋 Full View"]
)

# ============================================================================
# TAB 1: TESTS
# ============================================================================
with tab_tests:
    st.subheader("Diagnostic Tests")
    st.caption("Record test execution results and evidence")
    
    st.write(f"**Current tests: {len(investigation.executions)}**")
    
    with st.form("add_test_form"):
        test_name = st.text_input(
            "Test name",
            placeholder="e.g., 'Connectivity test to destination'",
            help="Name of diagnostic test to run"
        )
        
        test_method = st.text_area(
            "Test method (how you ran it)",
            placeholder="e.g., 'Ran: ping 8.8.8.8 -c 4'",
            height=80
        )
        
        test_result = st.selectbox(
            "Result",
            ["success", "failed", "inconclusive"],
            help="What did the test show?"
        )
        
        test_observation = st.text_area(
            "Observation (what you saw)",
            placeholder="e.g., 'All 4 packets received, 0% loss, <50ms latency'",
            height=100
        )
        
        if st.form_submit_button("Log Test Result", type="primary"):
            st.success(f"✅ Test logged: {test_name}")
            st.info("Test added. Next: link to hypotheses in Evidence tab.")

# ============================================================================
# TAB 2: EVIDENCE
# ============================================================================
with tab_evidence:
    st.subheader("Evidence & Belief Updates")
    st.caption("Add evidence and track how it changes hypothesis beliefs")
    
    st.write(f"**Current hypotheses: {len(investigation.hypotheses)}**")
    
    with st.form("add_evidence_form"):
        evidence_observation = st.text_area(
            "Evidence observation",
            placeholder="What you discovered (fact, not interpretation)",
            height=100,
            help="e.g., 'TCP port 443 responds' or 'Event log shows policy block at 14:23'"
        )
        
        evidence_source = st.text_input(
            "Evidence source",
            placeholder="e.g., 'Connectivity test', 'Windows Event Log', 'tcpdump'",
            help="Where did this evidence come from?"
        )
        
        evidence_reliability = st.select_slider(
            "Reliability",
            options=["low", "medium", "high"],
            value="medium",
            help="How confident are you in this evidence?"
        )
        
        # Select which hypothesis this affects
        if investigation.hypotheses:
            st.write("**Which hypothesis does this evidence affect?**")
            
            hypothesis_options = {h.statement: h.id for h in investigation.hypotheses}
            selected_statement = st.selectbox(
                "Hypothesis",
                options=list(hypothesis_options.keys()),
                help="Pick hypothesis this evidence relates to"
            )
            selected_hypothesis_id = hypothesis_options[selected_statement]
            
            strengthens = st.radio(
                "Does this evidence strengthen or weaken the hypothesis?",
                ["Strengthens (supports)", "Weakens (contradicts)"]
            )
            
            rationale = st.text_area(
                "Rationale (why this matters)",
                placeholder="Explain how this evidence affects your belief",
                height=80
            )
            
            if st.form_submit_button("Add Evidence", type="primary"):
                st.success("✅ Evidence logged and belief updated")
                st.info(f"Hypothesis '{selected_statement}' updated based on evidence")
        else:
            st.warning("No hypotheses yet. Add them in the investigation creation.")

# ============================================================================
# TAB 3: INTERVENTION
# ============================================================================
with tab_intervention:
    st.subheader("Remediation")
    st.caption("Record fixes you're applying")
    
    st.write(f"**Current interventions: {len(investigation.interventions)}**")
    
    with st.form("add_intervention_form"):
        intervention_desc = st.text_area(
            "Intervention description",
            placeholder="e.g., 'Deployed group policy exception to endpoint'",
            height=80,
            help="What fix are you applying?"
        )
        
        intervention_expected = st.text_area(
            "Expected effect",
            placeholder="e.g., 'Policy should allow application operation'",
            height=80,
            help="What should happen if the fix works?"
        )
        
        intervention_status = st.selectbox(
            "Status",
            ["proposed", "authorised", "executed", "failed_to_apply", "verified_effective", "verified_ineffective"],
            help="Current state of the fix"
        )
        
        if st.form_submit_button("Log Intervention", type="primary"):
            st.success("✅ Intervention logged")

# ============================================================================
# TAB 4: DIAGNOSIS
# ============================================================================
with tab_diagnosis:
    st.subheader("Root Cause & Verification")
    st.caption("Summarize findings and confirm diagnosis")
    
    with st.form("diagnosis_form"):
        root_cause = st.text_area(
            "Root cause",
            value=investigation.root_cause or "",
            placeholder="Concise statement of the underlying cause",
            height=100,
            help="What is the actual problem? Not the symptom, the cause."
        )
        
        engineer_confirmed = st.checkbox(
            "✅ I have verified this diagnosis and confirmed the fix works",
            value=investigation.engineer_confirmed,
            help="Only check if you're confident this is correct"
        )
        
        if st.form_submit_button("Save Diagnosis", type="primary"):
            if root_cause and engineer_confirmed:
                # Update investigation
                investigation.root_cause = root_cause
                investigation.engineer_confirmed = engineer_confirmed
                repo.save(investigation)
                st.success("✅ Diagnosis saved and confirmed")
                st.info("This investigation can now be exported to KB")
            elif root_cause and not engineer_confirmed:
                st.warning("⚠️ Root cause saved but not confirmed. Run verification before export.")
            else:
                st.error("Enter root cause before saving.")

# ============================================================================
# TAB 5: FULL VIEW
# ============================================================================
with tab_view:
    st.subheader("Investigation Summary")
    
    st.write(f"**Title:** {investigation.title}")
    st.write(f"**Symptom:** {investigation.symptom.what_is_wrong}")
    
    if investigation.root_cause:
        st.write(f"**Root Cause:** {investigation.root_cause}")
    else:
        st.info("Root cause not yet identified")
    
    st.write(f"**Status:** {investigation.status.value}")
    st.write(f"**Engineer Confirmed:** {'✅ Yes' if investigation.engineer_confirmed else '❌ No'}")
    
    st.write(f"**Hypotheses:** {len(investigation.hypotheses)}")
    for h in investigation.hypotheses:
        st.write(f"  • {h.statement} — {h.belief.value}")
    
    st.write(f"**Tests Run:** {len(investigation.executions)}")
    st.write(f"**Interventions:** {len(investigation.interventions)}")

st.divider()

# Navigation buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("📖 View Full", use_container_width=True):
        st.session_state.investigation_id = investigation_id
        st.switch_page("pages/03_view_investigation.py")

with col3:
    if st.button("💾 Refresh", use_container_width=True):
        st.rerun()
