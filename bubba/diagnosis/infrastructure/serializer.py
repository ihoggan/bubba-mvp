"""JSON serialization for Investigation domain objects."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from bubba.diagnosis.domain.models import Investigation


class InvestigationEncoder(json.JSONEncoder):
    """JSON encoder for Investigation and related objects."""
    
    def default(self, obj: Any) -> Any:
        """Encode objects to JSON-serializable format."""
        if isinstance(obj, (datetime, UUID)):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def serialize_investigation(investigation: Investigation) -> str:
    """Serialize Investigation to JSON string.
    
    Args:
        investigation: Investigation object to serialize
        
    Returns:
        JSON string representation
    """
    # Convert to dict first, then serialize
    inv_dict = asdict(investigation)
    return json.dumps(inv_dict, cls=InvestigationEncoder, default=str)


def deserialize_investigation(json_str: str) -> Investigation | None:
    """Deserialize Investigation from JSON string.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Investigation object, or None if deserialization fails
    """
    try:
        data = json.loads(json_str)
        
        if not isinstance(data, dict):
            print(f"Error: JSON data is not a dict, got {type(data)}")
            return None
        
        # Reconstruct Investigation from JSON dict
        from bubba.diagnosis.domain.models import InvestigationStatus
        
        investigation = Investigation(
            title=data.get("title", ""),
            symptom=__rebuild_symptom(data.get("symptom", {})),
            status=__rebuild_enum(data.get("status", "new"), "InvestigationStatus"),
        )
        
        # Restore ID
        investigation.id = UUID(data.get("id", investigation.id))
        
        # Restore hypotheses
        for hyp_data in data.get("hypotheses", []):
            hypothesis = __rebuild_hypothesis(hyp_data)
            investigation.hypotheses.append(hypothesis)
        
        # Restore tests
        for test_data in data.get("tests", []):
            test = __rebuild_test(test_data)
            investigation.tests.append(test)
        
        # Restore executions
        for exec_data in data.get("executions", []):
            execution = __rebuild_execution(exec_data)
            investigation.executions.append(execution)
        
        # Restore interventions
        for interv_data in data.get("interventions", []):
            intervention = __rebuild_intervention(interv_data)
            investigation.interventions.append(intervention)
        
        # Restore verifications
        for verif_data in data.get("verifications", []):
            verification = __rebuild_verification(verif_data)
            investigation.verifications.append(verification)
        
        # Restore timeline
        for event_data in data.get("timeline", []):
            event = __rebuild_timeline_event(event_data)
            investigation.timeline.append(event)
        
        # Restore other fields
        investigation.root_cause = data.get("root_cause")
        investigation.engineer_confirmed = data.get("engineer_confirmed", False)
        
        return investigation
        
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        print(f"Failed to deserialize investigation: {e}")
        return None


# ============================================================================
# HELPER FUNCTIONS: Rebuild domain objects from dicts
# ============================================================================

def __rebuild_symptom(data: dict):
    """Rebuild Symptom from dict."""
    from bubba.diagnosis.domain.models import Symptom
    
    return Symptom(
        what_is_wrong=data.get("what_is_wrong", ""),
        expected_behaviour=data.get("expected_behaviour", ""),
        actual_behaviour=data.get("actual_behaviour", ""),
        affected_scope=data.get("affected_scope", ""),
    )


def __rebuild_hypothesis(data: dict):
    """Rebuild Hypothesis from dict."""
    from bubba.diagnosis.domain.models import Hypothesis
    
    hypothesis = Hypothesis(
        statement=data.get("statement", ""),
        rationale=data.get("rationale", ""),
    )
    hypothesis.id = UUID(data.get("id", hypothesis.id))
    hypothesis.belief = __rebuild_enum(data.get("belief", "unassessed"), "BeliefLevel")
    hypothesis.status = __rebuild_enum(data.get("status", "active"), "HypothesisStatus")
    hypothesis.supporting_evidence = [UUID(e) for e in data.get("supporting_evidence", []) if e]
    hypothesis.contradicting_evidence = [UUID(e) for e in data.get("contradicting_evidence", []) if e]
    
    return hypothesis


def __rebuild_test(data: dict):
    """Rebuild TestDefinition from dict."""
    from bubba.diagnosis.domain.models import TestDefinition
    
    test = TestDefinition(
        name=data.get("name", ""),
        description=data.get("description", ""),
        method=data.get("method", ""),
        expected_result=data.get("expected_result", ""),
    )
    test.id = UUID(data.get("id", test.id))
    test.risk = __rebuild_enum(data.get("risk", "read_only"), "TestRisk")
    
    return test


def __rebuild_execution(data: dict):
    """Rebuild TestExecution from dict."""
    from bubba.diagnosis.domain.models import TestExecution
    
    execution = TestExecution(
        test_id=UUID(data.get("test_id", "00000000-0000-0000-0000-000000000000")),
    )
    execution.id = UUID(data.get("id", execution.id))
    execution.occurred_at = __rebuild_datetime(data.get("occurred_at"))
    execution.result = data.get("result", "")
    execution.observation = data.get("observation", "")
    
    # Rebuild evidence
    for evidence_data in data.get("evidence", []):
        evidence = __rebuild_evidence(evidence_data)
        execution.evidence.append(evidence)
    
    return execution


def __rebuild_evidence(data: dict):
    """Rebuild Evidence from dict."""
    from bubba.diagnosis.domain.models import Evidence
    
    evidence = Evidence(
        observation=data.get("observation", ""),
        source=data.get("source", ""),
        reliability=data.get("reliability", "unknown"),
    )
    evidence.id = UUID(data.get("id", evidence.id))
    
    return evidence


def __rebuild_intervention(data: dict):
    """Rebuild Intervention from dict."""
    from bubba.diagnosis.domain.models import Intervention
    
    intervention = Intervention(
        description=data.get("description", ""),
        expected_effect=data.get("expected_effect", ""),
    )
    intervention.id = UUID(data.get("id", intervention.id))
    intervention.status = __rebuild_enum(data.get("status", "proposed"), "InterventionStatus")
    
    return intervention


def __rebuild_verification(data: dict):
    """Rebuild Verification from dict."""
    from bubba.diagnosis.domain.models import Verification
    
    verification = Verification(
        description=data.get("description", ""),
        actual_result=data.get("actual_result", ""),
        passed=data.get("passed", False),
    )
    verification.id = UUID(data.get("id", verification.id))
    
    return verification


def __rebuild_timeline_event(data: dict):
    """Rebuild TimelineEvent from dict."""
    from bubba.diagnosis.domain.models import TimelineEvent
    
    event = TimelineEvent(
        event_type=data.get("event_type", ""),
        summary=data.get("summary", ""),
        payload=data.get("payload"),
    )
    event.occurred_at = __rebuild_datetime(data.get("occurred_at"))
    
    return event


def __rebuild_datetime(dt_str: str) -> datetime:
    """Rebuild datetime from ISO string."""
    if not dt_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return datetime.now()


def __rebuild_enum(value: str, enum_name: str):
    """Rebuild Enum from string value."""
    from bubba.diagnosis import domain
    
    if not value:
        return None
    
    try:
        enum_class = getattr(domain.models, enum_name)
        return enum_class(value)
    except (ValueError, AttributeError):
        try:
            return list(enum_class)[0]  # Fallback to first enum value
        except:
            return None
