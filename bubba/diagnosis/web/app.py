"""Streamlit sandbox UI — refined narrative-focused incident investigation."""

import streamlit as st

from bubba.diagnosis.application.service import InvestigationService
from bubba.diagnosis.infrastructure.repository import InvestigationRepository
from bubba.diagnosis.web.wording import EventNarrator, evidence_reliability_label, belief_emoji

st.set_page_config(page_title="Bubba.Diagnosis", layout="wide")
service = InvestigationService()
repo = InvestigationRepository()

st.title("Bubba.Diagnosis")
st.caption("Evidence-driven incident investigation — structured walkthrough")

# ============================================================================
# TABS: Current Investigation vs Search Past Cases
# ============================================================================
tab_current, tab_search = st.tabs(["Current Investigation", "Search Past Cases"])

# ============================================================================
# TAB 1: CURRENT INVESTIGATION (existing UI)
# ============================================================================
with tab_current:
    investigation = service.create_demo()
    recommendation = service.next_test(investigation)

    # SECTION 1: THE INCIDENT
    st.subheader("📋 The Incident")
    left, right = st.columns([2, 1])

    with left:
        st.write(f"**Problem:** {investigation.symptom.what_is_wrong}")
        st.write(f"**Expected:** {investigation.symptom.expected_behaviour}")
        st.write(f"**Actual:** {investigation.symptom.actual_behaviour}")
        st.write(f"**Scope:** {investigation.symptom.affected_scope}")

    with right:
        status_emoji = "🔍" if investigation.status.value in ("investigating", "characterising") else "✅"
        st.metric(f"{status_emoji} Investigation", investigation.status.value.upper())
        st.metric("Hypotheses tested", len(investigation.hypotheses))
        st.metric("Evidence collected", len(investigation.executions))

    # SECTION 2: THE INVESTIGATION NARRATIVE
    st.subheader("🔬 How We Got Here")
    narrator = EventNarrator()
    for event in investigation.timeline:
        narrative_line = narrator.translate_event(event)
        st.write(narrative_line)

    # SECTION 3: COMPETING HYPOTHESES (WITH EVIDENCE LINKING)
    st.subheader("🧩 Hypotheses Explored")
    st.caption("Each hypothesis shows what evidence supported or contradicted it")

    # Build evidence lookup for quick access
    evidence_by_id = {}
    for execution in investigation.executions:
        for evidence in execution.evidence:
            evidence_by_id[evidence.id] = evidence

    for hypothesis in investigation.hypotheses:
        status_icon = {
            "confirmed": "✅",
            "active": "🔍",
            "weakened": "↘️",
            "ruled_out": "🚫"
        }.get(hypothesis.status.value, "•")
        
        with st.container(border=True):
            # Hypothesis statement + belief
            st.write(f"{status_icon} **{hypothesis.statement}**")
            belief_label = belief_emoji(hypothesis.belief.value)
            st.write(f"Current belief: {belief_label}")
            
            # Supporting evidence
            if hypothesis.supporting_evidence:
                st.write("**Evidence that supports this:**")
                for evidence_id in hypothesis.supporting_evidence:
                    if evidence_id in evidence_by_id:
                        evidence = evidence_by_id[evidence_id]
                        reliability = evidence_reliability_label(evidence.reliability)
                        st.write(f"  • {reliability} — {evidence.observation}")
                        if evidence.source and evidence.source != "unknown":
                            st.caption(f"    Source: {evidence.source}")
            
            # Contradicting evidence
            if hypothesis.contradicting_evidence:
                st.write("**Evidence that weakens this:**")
                for evidence_id in hypothesis.contradicting_evidence:
                    if evidence_id in evidence_by_id:
                        evidence = evidence_by_id[evidence_id]
                        reliability = evidence_reliability_label(evidence.reliability)
                        st.write(f"  • {reliability} — {evidence.observation}")
                        if evidence.source and evidence.source != "unknown":
                            st.caption(f"    Source: {evidence.source}")

    # SECTION 4: DIAGNOSIS & REMEDIATION
    st.subheader("🎯 Diagnosis & Fix")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**What we found:**")
        if investigation.root_cause:
            st.success(investigation.root_cause)
        else:
            st.warning("Root cause not yet established")

    with col2:
        st.write("**Verification:**")
        for verification in investigation.verifications:
            status = "✅ PASS" if verification.passed else "❌ FAIL"
            st.write(f"{status} — {verification.actual_result}")

    # Interventions detail
    if investigation.interventions:
        st.write("**Fix applied:**")
        for intervention in investigation.interventions:
            status_icon = "✅" if intervention.status.value == "verified_effective" else "⚠️"
            st.write(f"{status_icon} {intervention.description}")
            st.caption(f"Status: {intervention.status.value}")

    # SECTION 5: NEXT STEP (if applicable)
    if investigation.status.value in ("characterising", "investigating"):
        st.subheader("➡️ Next Step")
        if recommendation:
            test = next(t for t in investigation.tests if t.id == recommendation.test_id)
            st.info(f"**{test.name}**\n\n{recommendation.rationale}\n\n(Recommendation score: {recommendation.score})")
        else:
            st.warning("No eligible diagnostic test found.")


# ============================================================================
# TAB 2: SEARCH PAST CASES
# ============================================================================
with tab_search:
    st.subheader("🔍 Search Past Investigations")
    st.caption("Find similar cases by symptom or root cause")

    search_type = st.radio("Search by:", ["Symptom", "Root Cause", "List All"])

    if search_type == "Symptom":
        query = st.text_input("Enter symptom keyword:", placeholder="e.g., 'network', 'connectivity'")
        if query:
            results = repo.search_by_symptom(query)
            st.write(f"**Found {len(results)} case(s)**")
            
            if results:
                for result in results:
                    with st.container(border=True):
                        st.write(f"**{result['title']}**")
                        st.write(f"**Symptom:** {result['symptom']}")
                        if result['root_cause']:
                            st.write(f"**Root Cause:** {result['root_cause']}")
                        status_icon = "✅" if result['engineer_confirmed'] else "⚠️"
                        st.write(f"{status_icon} Status: `{result['status']}`  |  Confirmed: `{result['engineer_confirmed']}`")
            else:
                st.info("No matching cases found.")

    elif search_type == "Root Cause":
        query = st.text_input("Enter root cause keyword:", placeholder="e.g., 'policy', 'configuration'")
        if query:
            results = repo.search_by_root_cause(query)
            st.write(f"**Found {len(results)} case(s)**")
            
            if results:
                for result in results:
                    with st.container(border=True):
                        st.write(f"**{result['title']}**")
                        st.write(f"**Symptom:** {result['symptom']}")
                        if result['root_cause']:
                            st.write(f"**Root Cause:** {result['root_cause']}")
                        status_icon = "✅" if result['engineer_confirmed'] else "⚠️"
                        st.write(f"{status_icon} Status: `{result['status']}`  |  Confirmed: `{result['engineer_confirmed']}`")
            else:
                st.info("No matching cases found.")

    else:  # List All
        results = repo.list_all()
        st.write(f"**Total cases: {len(results)}**")
        
        if results:
            for result in results:
                with st.container(border=True):
                    st.write(f"**{result['title']}**")
                    st.write(f"**Symptom:** {result['symptom']}")
                    if result['root_cause']:
                        st.write(f"**Root Cause:** {result['root_cause']}")
                    status_icon = "✅" if result['engineer_confirmed'] else "⚠️"
                    st.write(f"{status_icon} Status: `{result['status']}`  |  Confirmed: `{result['engineer_confirmed']}`")
        else:
            st.info("No cases stored yet.")
