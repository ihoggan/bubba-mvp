"""New Investigation page — Create and save a new investigation."""

import streamlit as st
from uuid import uuid4

from bubba.diagnosis.domain.models import (
    Investigation,
    InvestigationStatus,
    Symptom,
    Hypothesis,
)
from bubba.diagnosis.infrastructure.repository import InvestigationRepository

st.set_page_config(page_title="New Investigation", layout="wide")

st.title("📝 New Investigation")
st.caption("Capture a new incident — symptom, scope, and initial hypotheses")

st.divider()

# Initialize session state for form
if "form_step" not in st.session_state:
    st.session_state.form_step = 1

# Step 1: Symptom Capture
if st.session_state.form_step == 1:
    st.subheader("Step 1: What's the Problem?")
    
    with st.form("symptom_form"):
        title = st.text_input(
            "Investigation title",
            placeholder="e.g., 'User cannot print to network printer'",
            help="Short, searchable title for this incident"
        )
        
        st.write("**Describe the symptom:**")
        
        what_is_wrong = st.text_area(
            "What is wrong (as reported)",
            placeholder="e.g., 'Application crashes on startup'",
            height=80
        )
        
        expected_behaviour = st.text_area(
            "Expected behaviour",
            placeholder="e.g., 'Application starts and user can log in'",
            height=80
        )
        
        actual_behaviour = st.text_area(
            "Actual behaviour",
            placeholder="e.g., 'Application starts but shows error dialog before login screen'",
            height=80
        )
        
        affected_scope = st.text_input(
            "Who/what is affected",
            placeholder="e.g., 'One user, one workstation' or 'Department, all Windows endpoints'",
            help="Scope helps identify blast radius and similar cases"
        )
        
        submitted = st.form_submit_button("Next: Initial Hypotheses", type="primary")
        
        if submitted:
            if title and what_is_wrong and expected_behaviour and actual_behaviour and affected_scope:
                st.session_state.symptom_data = {
                    "title": title,
                    "what_is_wrong": what_is_wrong,
                    "expected_behaviour": expected_behaviour,
                    "actual_behaviour": actual_behaviour,
                    "affected_scope": affected_scope,
                }
                st.session_state.form_step = 2
                st.rerun()
            else:
                st.error("All fields required.")

# Step 2: Initial Hypotheses
elif st.session_state.form_step == 2:
    st.subheader("Step 2: Initial Hypotheses")
    st.caption("What might be causing this? Add 2-4 candidate explanations.")
    
    # Display captured symptom for reference
    with st.expander("📋 Symptom Summary (read-only)"):
        st.write(f"**Title:** {st.session_state.symptom_data['title']}")
        st.write(f"**Problem:** {st.session_state.symptom_data['what_is_wrong']}")
        st.write(f"**Scope:** {st.session_state.symptom_data['affected_scope']}")
    
    with st.form("hypotheses_form"):
        st.write("Add initial hypotheses (at least 2):")
        
        hypotheses = []
        for i in range(1, 5):
            col1, col2 = st.columns(2)
            with col1:
                statement = st.text_input(
                    f"Hypothesis {i} statement",
                    placeholder="e.g., 'Network connectivity issue'",
                    key=f"hyp_statement_{i}"
                )
            with col2:
                rationale = st.text_area(
                    f"Hypothesis {i} rationale",
                    placeholder="Why is this plausible?",
                    height=60,
                    key=f"hyp_rationale_{i}"
                )
            
            if statement and rationale:
                hypotheses.append({
                    "statement": statement,
                    "rationale": rationale
                })
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("← Back", type="secondary"):
                st.session_state.form_step = 1
                st.rerun()
        
        with col2:
            if st.form_submit_button("Save Investigation", type="primary"):
                if len(hypotheses) >= 2:
                    st.session_state.hypotheses_data = hypotheses
                    st.session_state.form_step = 3
                    st.rerun()
                else:
                    st.error("Add at least 2 hypotheses.")

# Step 3: Save to Database
elif st.session_state.form_step == 3:
    st.subheader("Step 3: Save Investigation")
    
    # Build Investigation object
    symptom = Symptom(
        what_is_wrong=st.session_state.symptom_data["what_is_wrong"],
        expected_behaviour=st.session_state.symptom_data["expected_behaviour"],
        actual_behaviour=st.session_state.symptom_data["actual_behaviour"],
        affected_scope=st.session_state.symptom_data["affected_scope"],
    )
    
    investigation = Investigation(
        title=st.session_state.symptom_data["title"],
        symptom=symptom,
        status=InvestigationStatus.CHARACTERISING,
    )
    
    for hyp_data in st.session_state.hypotheses_data:
        hypothesis = Hypothesis(
            statement=hyp_data["statement"],
            rationale=hyp_data["rationale"],
        )
        investigation.hypotheses.append(hypothesis)
    
    investigation.add_event(
        "investigation_created",
        f"Investigation created: {investigation.title}",
        {"scope": investigation.symptom.affected_scope}
    )
    
    # Save to database
    repo = InvestigationRepository()
    investigation_id = repo.save(investigation)
    
    st.success(f"✅ Investigation saved! ID: `{investigation_id}`")
    st.write(f"**Title:** {investigation.title}")
    st.write(f"**Hypotheses:** {len(investigation.hypotheses)}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Edit This Investigation", type="primary", use_container_width=True):
            st.session_state.investigation_id = investigation_id
            st.switch_page("pages/02_edit_investigation.py")
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.switch_page("app.py")
    
    # Reset form
    if st.button("➕ Create Another", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
