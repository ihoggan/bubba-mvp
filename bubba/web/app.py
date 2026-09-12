"""Streamlit sandbox UI."""

import streamlit as st

from bubba.diagnosis.application.service import InvestigationService

st.set_page_config(page_title="DecisionDesk v2 MVP", layout="wide")
service = InvestigationService()

st.title("DecisionDesk v2 MVP")
st.caption("Evidence-driven incident investigation sandbox — synthetic data only")

investigation = service.create_demo()
recommendation = service.next_test(investigation)

left, right = st.columns([2, 1])
with left:
    st.subheader("Symptom")
    st.write(f"**Problem:** {investigation.symptom.what_is_wrong}")
    st.write(f"**Expected:** {investigation.symptom.expected_behaviour}")
    st.write(f"**Actual:** {investigation.symptom.actual_behaviour}")
    st.write(f"**Scope:** {investigation.symptom.affected_scope}")

with right:
    st.subheader("Investigation state")
    st.metric("Status", investigation.status.value.upper())
    st.metric("Hypotheses", len(investigation.hypotheses))
    st.metric("Evidence-bearing executions", len(investigation.executions))

st.subheader("Competing hypotheses")
for hypothesis in investigation.hypotheses:
    with st.container(border=True):
        st.write(f"**{hypothesis.statement}**")
        st.write(f"Belief: `{hypothesis.belief.value}`  |  Status: `{hypothesis.status.value}`")
        if hypothesis.supporting_evidence:
            st.write(f"Supporting evidence: {len(hypothesis.supporting_evidence)}")
        if hypothesis.contradicting_evidence:
            st.write(f"Contradicting evidence: {len(hypothesis.contradicting_evidence)}")

st.subheader("Next-test reasoning")
if recommendation:
    test = next(t for t in investigation.tests if t.id == recommendation.test_id)
    st.info(f"**{test.name}** — score {recommendation.score}\n\n{recommendation.rationale}")
else:
    st.warning("No eligible diagnostic test found.")

st.subheader("Diagnosis vs remediation")
for intervention in investigation.interventions:
    st.write(f"**Intervention:** {intervention.description}")
    st.write(f"Status: `{intervention.status.value}`")
    st.write(
        "The remediation initially failed to apply. The underlying diagnosis was retained because fresh evidence explained the remediation failure without contradicting the causal hypothesis."
    )

st.subheader("Root cause and verification")
st.success(investigation.root_cause or "Not established")
for verification in investigation.verifications:
    st.write(f"Verification: {'PASS' if verification.passed else 'FAIL'} — {verification.actual_result}")

st.subheader("Investigation timeline")
for event in investigation.timeline:
    st.write(f"`{event.occurred_at.isoformat()}` **{event.event_type}** — {event.summary}")
