from bubba.diagnosis.application.service import InvestigationService
from bubba.diagnosis.domain.models import BeliefLevel, InterventionStatus
from bubba.diagnosis.domain.reasoning import recommend_next_test


def test_demo_preserves_correct_diagnosis_after_failed_remediation() -> None:
    investigation = InvestigationService().create_demo()

    policy_hypothesis = next(
        h for h in investigation.hypotheses if "Application-control policy" in h.statement
    )

    assert policy_hypothesis.belief == BeliefLevel.CONFIRMED
    assert investigation.interventions[0].status == InterventionStatus.VERIFIED_EFFECTIVE
    assert investigation.engineer_confirmed is True

    failure_events = [
        e for e in investigation.timeline if e.event_type == "remediation_failure_classified"
    ]
    assert failure_events
    assert "Diagnosis retained" in failure_events[0].summary


def test_every_confidence_update_has_evidence() -> None:
    investigation = InvestigationService().create_demo()
    assert investigation.confidence_updates
    assert all(update.evidence_ids for update in investigation.confidence_updates)


def test_next_test_is_explainable() -> None:
    investigation = InvestigationService().create_demo()
    recommendation = recommend_next_test(investigation)
    assert recommendation is not None
    assert recommendation.rationale
    assert "hypotheses" in recommendation.rationale
