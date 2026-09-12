"""Domain entities for the DecisionDesk investigation lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class EpistemicType(StrEnum):
    """Type of knowledge represented by a statement."""

    FACT = "fact"
    OBSERVATION = "observation"
    ASSUMPTION = "assumption"
    HYPOTHESIS = "hypothesis"
    INFERENCE = "inference"
    CONCLUSION = "conclusion"


class HypothesisStatus(StrEnum):
    """Lifecycle state of a hypothesis."""

    ACTIVE = "active"
    WEAKENED = "weakened"
    RULED_OUT = "ruled_out"
    CONFIRMED = "confirmed"


class BeliefLevel(StrEnum):
    """Ordinal confidence state, deliberately not a probability."""

    UNASSESSED = "unassessed"
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    PLAUSIBLE = "plausible"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    CONFIRMED = "confirmed"
    RULED_OUT = "ruled_out"


class InvestigationStatus(StrEnum):
    """High-level investigation lifecycle."""

    NEW = "new"
    CHARACTERISING = "characterising"
    INVESTIGATING = "investigating"
    VERIFYING = "verifying"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TestRisk(StrEnum):
    """Operational risk of executing a test."""

    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InterventionStatus(StrEnum):
    """State of a deliberate environment change."""

    PROPOSED = "proposed"
    AUTHORISED = "authorised"
    EXECUTED = "executed"
    FAILED_TO_APPLY = "failed_to_apply"
    VERIFIED_EFFECTIVE = "verified_effective"
    VERIFIED_INEFFECTIVE = "verified_ineffective"


@dataclass(slots=True)
class Evidence:
    """A provenance-bearing observation or artefact."""

    observation: str
    source: str
    reliability: str = "unknown"
    context: str = ""
    id: UUID = field(default_factory=uuid4)
    observed_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class HypothesisExpectation:
    """Expected observations and their interpretation for a test/hypothesis pair."""

    test_id: UUID
    expected_positive: str
    expected_negative: str
    interpretation: str


@dataclass(slots=True)
class Hypothesis:
    """A testable candidate explanation for the symptom."""

    statement: str
    rationale: str
    id: UUID = field(default_factory=uuid4)
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    belief: BeliefLevel = BeliefLevel.UNASSESSED
    expectations: list[HypothesisExpectation] = field(default_factory=list)
    supporting_evidence: list[UUID] = field(default_factory=list)
    contradicting_evidence: list[UUID] = field(default_factory=list)


@dataclass(slots=True)
class TestDefinition:
    """Reusable diagnostic test definition."""

    name: str
    purpose: str
    risk: TestRisk
    reversibility: str
    observability: str
    cost: str
    id: UUID = field(default_factory=uuid4)
    applicable_hypotheses: list[UUID] = field(default_factory=list)


@dataclass(slots=True)
class TestExecution:
    """One concrete execution of a test inside an investigation."""

    test_id: UUID
    method: str
    observation: str
    result: str
    id: UUID = field(default_factory=uuid4)
    executed_at: datetime = field(default_factory=utc_now)
    evidence: list[Evidence] = field(default_factory=list)


@dataclass(slots=True)
class ConfidenceUpdate:
    """Immutable record explaining a belief change."""

    hypothesis_id: UUID
    previous: BeliefLevel
    new: BeliefLevel
    rationale: str
    evidence_ids: list[UUID]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Intervention:
    """Deliberate change intended to remediate a suspected cause."""

    description: str
    expected_effect: str
    target: str
    status: InterventionStatus = InterventionStatus.PROPOSED
    id: UUID = field(default_factory=uuid4)
    executed_at: datetime | None = None


@dataclass(slots=True)
class Verification:
    """Independent check of an intervention or service outcome."""

    criterion: str
    method: str
    expected_result: str
    actual_result: str
    passed: bool
    evidence_ids: list[UUID]
    id: UUID = field(default_factory=uuid4)
    verified_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class TimelineEvent:
    """Append-only investigation event for auditability."""

    event_type: str
    summary: str
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Symptom:
    """Precise representation of the observed problem."""

    what_is_wrong: str
    expected_behaviour: str
    actual_behaviour: str
    affected_scope: str
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class Investigation:
    """Aggregate representing an end-to-end incident investigation."""

    title: str
    symptom: Symptom
    id: UUID = field(default_factory=uuid4)
    status: InvestigationStatus = InvestigationStatus.CHARACTERISING
    hypotheses: list[Hypothesis] = field(default_factory=list)
    tests: list[TestDefinition] = field(default_factory=list)
    executions: list[TestExecution] = field(default_factory=list)
    confidence_updates: list[ConfidenceUpdate] = field(default_factory=list)
    interventions: list[Intervention] = field(default_factory=list)
    verifications: list[Verification] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)
    root_cause: str | None = None
    engineer_confirmed: bool = False

    def add_event(self, event_type: str, summary: str, payload: dict[str, Any]) -> TimelineEvent:
        """Append an immutable event to the investigation timeline."""
        event = TimelineEvent(event_type=event_type, summary=summary, payload=payload)
        self.timeline.append(event)
        return event
