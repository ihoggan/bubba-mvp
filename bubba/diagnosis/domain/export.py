"""Export schema for verified diagnoses into the knowledge base."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from bubba.diagnosis.domain.models import Investigation


@dataclass(slots=True)
class ExportedEvidence:
    """Simplified evidence for KB export."""
    observation: str
    source: str
    reliability: str


@dataclass(slots=True)
class ExportedHypothesis:
    """Hypothesis journey: explored, tested, outcome."""
    statement: str
    rationale: str
    final_status: str  # "ruled_out" | "confirmed" | "weakened"
    final_belief: str
    supporting_evidence: list[ExportedEvidence]
    contradicting_evidence: list[ExportedEvidence]


@dataclass(slots=True)
class ExportedIntervention:
    """Fix applied and its verification."""
    description: str
    expected_effect: str
    status: str
    verified: bool


@dataclass(slots=True)
class DiagnosisExport:
    """Verified diagnosis ready for KB ingestion."""
    
    id: str
    title: str
    
    # The problem
    symptom_what_is_wrong: str
    symptom_expected_behaviour: str
    symptom_actual_behaviour: str
    symptom_affected_scope: str
    
    # The investigation
    hypotheses_explored: list[ExportedHypothesis]
    root_cause: str
    root_cause_confidence: str
    
    # The fix
    interventions_applied: list[ExportedIntervention]
    
    # Quality gates
    engineer_confirmed: bool
    investigation_status: str
    
    # Metadata
    exported_at: str  # ISO format string for JSON serialization
    investigation_duration_hours: float | None = None
    
    @staticmethod
    def from_investigation(inv: Investigation) -> DiagnosisExport:
        """Convert a resolved Investigation into an exportable diagnosis.
        
        Raises ValueError if investigation is not export-ready.
        """
        # Verify export readiness
        if not inv.root_cause:
            raise ValueError("Cannot export: no root_cause identified")
        
        if not inv.engineer_confirmed:
            raise ValueError("Cannot export: engineer has not confirmed diagnosis")
        
        if inv.status.value not in ("resolved", "closed"):
            raise ValueError(f"Cannot export: investigation status is {inv.status.value}, must be resolved/closed")
        
        # Build evidence dicts for quick lookup
        evidence_by_id = {}
        for execution in inv.executions:
            for evidence in execution.evidence:
                evidence_by_id[evidence.id] = evidence
        
        # Transform hypotheses
        exported_hypotheses = []
        for hyp in inv.hypotheses:
            supporting = [
                ExportedEvidence(
                    observation=evidence_by_id[eid].observation,
                    source=evidence_by_id[eid].source,
                    reliability=evidence_by_id[eid].reliability
                )
                for eid in hyp.supporting_evidence
                if eid in evidence_by_id
            ]
            contradicting = [
                ExportedEvidence(
                    observation=evidence_by_id[eid].observation,
                    source=evidence_by_id[eid].source,
                    reliability=evidence_by_id[eid].reliability
                )
                for eid in hyp.contradicting_evidence
                if eid in evidence_by_id
            ]
            
            exported_hypotheses.append(ExportedHypothesis(
                statement=hyp.statement,
                rationale=hyp.rationale,
                final_status=hyp.status.value,
                final_belief=hyp.belief.value,
                supporting_evidence=supporting,
                contradicting_evidence=contradicting
            ))
        
        # Transform interventions
        exported_interventions = [
            ExportedIntervention(
                description=interv.description,
                expected_effect=interv.expected_effect,
                status=interv.status.value,
                verified=interv.status.value == "verified_effective"
            )
            for interv in inv.interventions
        ]
        
        return DiagnosisExport(
            id=str(inv.id),
            title=inv.title,
            symptom_what_is_wrong=inv.symptom.what_is_wrong,
            symptom_expected_behaviour=inv.symptom.expected_behaviour,
            symptom_actual_behaviour=inv.symptom.actual_behaviour,
            symptom_affected_scope=inv.symptom.affected_scope,
            hypotheses_explored=exported_hypotheses,
            root_cause=inv.root_cause,
            root_cause_confidence=inv.hypotheses[0].belief.value if inv.hypotheses else "unknown",
            interventions_applied=exported_interventions,
            engineer_confirmed=inv.engineer_confirmed,
            investigation_status=inv.status.value,
            exported_at=datetime.now().isoformat(),
            investigation_duration_hours=None  # Could calculate from timeline if needed
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON export."""
        return asdict(self)
