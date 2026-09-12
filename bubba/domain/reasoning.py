"""Deterministic reasoning services for hypothesis updates and test selection."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from bubba.diagnosis.domain.models import (
    BeliefLevel,
    ConfidenceUpdate,
    Evidence,
    Hypothesis,
    HypothesisStatus,
    Investigation,
    TestDefinition,
    TestRisk,
)

BELIEF_ORDER = {
    BeliefLevel.RULED_OUT: -3,
    BeliefLevel.VERY_WEAK: -2,
    BeliefLevel.WEAK: -1,
    BeliefLevel.UNASSESSED: 0,
    BeliefLevel.PLAUSIBLE: 1,
    BeliefLevel.STRONG: 2,
    BeliefLevel.VERY_STRONG: 3,
    BeliefLevel.CONFIRMED: 4,
}

RISK_PENALTY = {
    TestRisk.READ_ONLY: 0,
    TestRisk.LOW: 1,
    TestRisk.MEDIUM: 2,
    TestRisk.HIGH: 4,
}


@dataclass(frozen=True, slots=True)
class TestRecommendation:
    """Explainable recommendation for the next diagnostic test."""

    test_id: UUID
    score: int
    rationale: str


def update_belief(
    investigation: Investigation,
    hypothesis: Hypothesis,
    evidence: Evidence,
    strengthens: bool,
    rationale: str,
) -> ConfidenceUpdate:
    """Update an ordinal belief level and preserve the reason for the change."""
    previous = hypothesis.belief
    current_value = BELIEF_ORDER[previous]
    next_value = max(-3, min(3, current_value + (1 if strengthens else -1)))
    new_level = min(BELIEF_ORDER, key=lambda level: abs(BELIEF_ORDER[level] - next_value))

    if new_level in {BeliefLevel.RULED_OUT, BeliefLevel.VERY_WEAK, BeliefLevel.WEAK}:
        hypothesis.status = HypothesisStatus.WEAKENED
    elif new_level in {BeliefLevel.VERY_STRONG, BeliefLevel.CONFIRMED}:
        hypothesis.status = HypothesisStatus.CONFIRMED if new_level == BeliefLevel.CONFIRMED else HypothesisStatus.ACTIVE

    if strengthens:
        hypothesis.supporting_evidence.append(evidence.id)
    else:
        hypothesis.contradicting_evidence.append(evidence.id)

    hypothesis.belief = new_level
    update = ConfidenceUpdate(
        hypothesis_id=hypothesis.id,
        previous=previous,
        new=new_level,
        rationale=rationale,
        evidence_ids=[evidence.id],
    )
    investigation.confidence_updates.append(update)
    investigation.add_event(
        "confidence_updated",
        f"{hypothesis.statement}: {previous.value} -> {new_level.value}",
        {"hypothesis_id": str(hypothesis.id), "evidence_id": str(evidence.id), "rationale": rationale},
    )
    return update


def recommend_next_test(investigation: Investigation) -> TestRecommendation | None:
    """Rank available tests using transparent, non-probabilistic heuristics."""
    viable = [
        hypothesis
        for hypothesis in investigation.hypotheses
        if hypothesis.status not in {HypothesisStatus.RULED_OUT}
    ]
    if not viable or not investigation.tests:
        return None

    scored: list[tuple[int, TestDefinition, str]] = []
    for test in investigation.tests:
        applicable = [h for h in viable if h.id in test.applicable_hypotheses]
        if not applicable:
            continue

        coverage = len(applicable) * 3
        discrimination = len({BELIEF_ORDER[h.belief] for h in applicable}) * 2
        observability = 2 if test.observability.lower() in {"high", "very high"} else 1
        reversibility = 2 if test.reversibility.lower() in {"high", "easy"} else 1
        score = coverage + discrimination + observability + reversibility - RISK_PENALTY[test.risk]
        rationale = (
            f"Covers {len(applicable)} viable hypotheses; differentiates their current belief states; "
            f"observability={test.observability}; reversibility={test.reversibility}; risk={test.risk.value}."
        )
        scored.append((score, test, rationale))

    if not scored:
        return None
    score, test, rationale = max(scored, key=lambda item: item[0])
    return TestRecommendation(test_id=test.id, score=score, rationale=rationale)
