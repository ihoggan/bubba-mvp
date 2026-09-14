"""JSON serialization for Investigation domain objects.

Round-trip contract: an Investigation serialized with ``serialize_investigation``
must reconstruct to an equivalent Investigation via ``deserialize_investigation``,
preserving every nested collection (hypotheses, tests, executions, confidence
updates, interventions, verifications, timeline) and their identity/timestamps.
"""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from bubba.diagnosis.domain.models import (
    BeliefLevel,
    ConfidenceUpdate,
    Evidence,
    Hypothesis,
    HypothesisExpectation,
    HypothesisStatus,
    Intervention,
    InterventionStatus,
    Investigation,
    InvestigationStatus,
    Symptom,
    TestDefinition,
    TestExecution,
    TestRisk,
    TimelineEvent,
    Verification,
)


class InvestigationEncoder(json.JSONEncoder):
    """JSON encoder for Investigation and related objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, UUID)):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def serialize_investigation(investigation: Investigation) -> str:
    """Serialize an Investigation to a JSON string."""
    inv_dict = asdict(investigation)
    return json.dumps(inv_dict, cls=InvestigationEncoder, default=str)


def deserialize_investigation(json_str: str) -> Investigation | None:
    """Deserialize an Investigation from a JSON string.

    Returns None only when the input is not a JSON object. A structural
    mismatch against the domain model is a real defect and is allowed to
    raise, rather than being silently swallowed into a None.
    """
    data = json.loads(json_str)
    if not isinstance(data, dict):
        return None

    investigation = Investigation(
        title=data.get("title", ""),
        symptom=_rebuild_symptom(data.get("symptom", {})),
        status=_enum(InvestigationStatus, data.get("status"), InvestigationStatus.NEW),
    )
    investigation.id = _uuid(data.get("id"), investigation.id)

    investigation.hypotheses = [_rebuild_hypothesis(h) for h in data.get("hypotheses", [])]
    investigation.tests = [_rebuild_test(t) for t in data.get("tests", [])]
    investigation.executions = [_rebuild_execution(e) for e in data.get("executions", [])]
    investigation.confidence_updates = [
        _rebuild_confidence_update(c) for c in data.get("confidence_updates", [])
    ]
    investigation.interventions = [_rebuild_intervention(i) for i in data.get("interventions", [])]
    investigation.verifications = [_rebuild_verification(v) for v in data.get("verifications", [])]
    investigation.timeline = [_rebuild_timeline_event(ev) for ev in data.get("timeline", [])]

    investigation.root_cause = data.get("root_cause")
    investigation.engineer_confirmed = data.get("engineer_confirmed", False)
    return investigation


# ---------------------------------------------------------------------------
# Scalar coercion helpers
# ---------------------------------------------------------------------------

def _uuid(value: Any, default: UUID | None = None) -> UUID:
    if value in (None, ""):
        if default is None:
            raise ValueError("missing required UUID with no default")
        return default
    return UUID(str(value))


def _uuid_list(values: Any) -> list[UUID]:
    return [UUID(str(v)) for v in (values or []) if v]


def _enum(enum_cls, value: Any, default):
    if value in (None, ""):
        return default
    return enum_cls(value)


def _dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Domain object reconstruction (mirrors bubba.diagnosis.domain.models)
# ---------------------------------------------------------------------------

def _rebuild_symptom(data: dict) -> Symptom:
    symptom = Symptom(
        what_is_wrong=data.get("what_is_wrong", ""),
        expected_behaviour=data.get("expected_behaviour", ""),
        actual_behaviour=data.get("actual_behaviour", ""),
        affected_scope=data.get("affected_scope", ""),
    )
    symptom.id = _uuid(data.get("id"), symptom.id)
    return symptom


def _rebuild_expectation(data: dict) -> HypothesisExpectation:
    return HypothesisExpectation(
        test_id=_uuid(data.get("test_id")),
        expected_positive=data.get("expected_positive", ""),
        expected_negative=data.get("expected_negative", ""),
        interpretation=data.get("interpretation", ""),
    )


def _rebuild_hypothesis(data: dict) -> Hypothesis:
    hypothesis = Hypothesis(
        statement=data.get("statement", ""),
        rationale=data.get("rationale", ""),
    )
    hypothesis.id = _uuid(data.get("id"), hypothesis.id)
    hypothesis.status = _enum(HypothesisStatus, data.get("status"), HypothesisStatus.ACTIVE)
    hypothesis.belief = _enum(BeliefLevel, data.get("belief"), BeliefLevel.UNASSESSED)
    hypothesis.expectations = [_rebuild_expectation(e) for e in data.get("expectations", [])]
    hypothesis.supporting_evidence = _uuid_list(data.get("supporting_evidence"))
    hypothesis.contradicting_evidence = _uuid_list(data.get("contradicting_evidence"))
    return hypothesis


def _rebuild_test(data: dict) -> TestDefinition:
    test = TestDefinition(
        name=data.get("name", ""),
        purpose=data.get("purpose", ""),
        risk=_enum(TestRisk, data.get("risk"), TestRisk.READ_ONLY),
        reversibility=data.get("reversibility", ""),
        observability=data.get("observability", ""),
        cost=data.get("cost", ""),
    )
    test.id = _uuid(data.get("id"), test.id)
    test.applicable_hypotheses = _uuid_list(data.get("applicable_hypotheses"))
    return test


def _rebuild_evidence(data: dict) -> Evidence:
    evidence = Evidence(
        observation=data.get("observation", ""),
        source=data.get("source", ""),
        reliability=data.get("reliability", "unknown"),
        context=data.get("context", ""),
    )
    evidence.id = _uuid(data.get("id"), evidence.id)
    observed_at = _dt(data.get("observed_at"))
    if observed_at is not None:
        evidence.observed_at = observed_at
    return evidence


def _rebuild_execution(data: dict) -> TestExecution:
    execution = TestExecution(
        test_id=_uuid(data.get("test_id")),
        method=data.get("method", ""),
        observation=data.get("observation", ""),
        result=data.get("result", ""),
    )
    execution.id = _uuid(data.get("id"), execution.id)
    executed_at = _dt(data.get("executed_at"))
    if executed_at is not None:
        execution.executed_at = executed_at
    execution.evidence = [_rebuild_evidence(e) for e in data.get("evidence", [])]
    return execution


def _rebuild_confidence_update(data: dict) -> ConfidenceUpdate:
    update = ConfidenceUpdate(
        hypothesis_id=_uuid(data.get("hypothesis_id")),
        previous=_enum(BeliefLevel, data.get("previous"), BeliefLevel.UNASSESSED),
        new=_enum(BeliefLevel, data.get("new"), BeliefLevel.UNASSESSED),
        rationale=data.get("rationale", ""),
        evidence_ids=_uuid_list(data.get("evidence_ids")),
    )
    update.id = _uuid(data.get("id"), update.id)
    created_at = _dt(data.get("created_at"))
    if created_at is not None:
        update.created_at = created_at
    return update


def _rebuild_intervention(data: dict) -> Intervention:
    intervention = Intervention(
        description=data.get("description", ""),
        expected_effect=data.get("expected_effect", ""),
        target=data.get("target", ""),
        status=_enum(InterventionStatus, data.get("status"), InterventionStatus.PROPOSED),
    )
    intervention.id = _uuid(data.get("id"), intervention.id)
    intervention.executed_at = _dt(data.get("executed_at"))
    return intervention


def _rebuild_verification(data: dict) -> Verification:
    verification = Verification(
        criterion=data.get("criterion", ""),
        method=data.get("method", ""),
        expected_result=data.get("expected_result", ""),
        actual_result=data.get("actual_result", ""),
        passed=data.get("passed", False),
        evidence_ids=_uuid_list(data.get("evidence_ids")),
    )
    verification.id = _uuid(data.get("id"), verification.id)
    verified_at = _dt(data.get("verified_at"))
    if verified_at is not None:
        verification.verified_at = verified_at
    return verification


def _rebuild_timeline_event(data: dict) -> TimelineEvent:
    event = TimelineEvent(
        event_type=data.get("event_type", ""),
        summary=data.get("summary", ""),
        payload=data.get("payload") or {},
    )
    event.id = _uuid(data.get("id"), event.id)
    occurred_at = _dt(data.get("occurred_at"))
    if occurred_at is not None:
        event.occurred_at = occurred_at
    return event
