"""Tests for diagnosis export functionality."""

import json
from datetime import datetime

import pytest
from bubba.diagnosis.application.service import InvestigationService
from bubba.diagnosis.domain.export import DiagnosisExport
from bubba.diagnosis.domain.models import InvestigationStatus


class TestDiagnosisExport:
    """Test the DiagnosisExport schema and conversion."""

    def test_demo_investigation_is_export_ready(self):
        """Demo investigation must have all required fields for export."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        assert investigation.root_cause is not None
        assert investigation.engineer_confirmed is True
        assert investigation.status == InvestigationStatus.RESOLVED

    def test_export_from_demo_succeeds(self):
        """Converting demo investigation to DiagnosisExport should succeed."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        export = DiagnosisExport.from_investigation(investigation)
        
        assert export.id == str(investigation.id)
        assert export.title == investigation.title
        assert export.root_cause == investigation.root_cause
        assert export.engineer_confirmed is True
        assert export.investigation_status == "resolved"

    def test_export_includes_symptom(self):
        """Export must capture the symptom."""
        service = InvestigationService()
        investigation = service.create_demo()
        export = DiagnosisExport.from_investigation(investigation)
        
        assert export.symptom_what_is_wrong == investigation.symptom.what_is_wrong
        assert export.symptom_expected_behaviour == investigation.symptom.expected_behaviour
        assert export.symptom_actual_behaviour == investigation.symptom.actual_behaviour
        assert export.symptom_affected_scope == investigation.symptom.affected_scope

    def test_export_includes_hypotheses(self):
        """Export must include explored hypotheses with evidence."""
        service = InvestigationService()
        investigation = service.create_demo()
        export = DiagnosisExport.from_investigation(investigation)
        
        assert len(export.hypotheses_explored) == len(investigation.hypotheses)
        
        for exported_hyp, orig_hyp in zip(export.hypotheses_explored, investigation.hypotheses):
            assert exported_hyp.statement == orig_hyp.statement
            assert exported_hyp.rationale == orig_hyp.rationale
            assert exported_hyp.final_status == orig_hyp.status.value
            assert exported_hyp.final_belief == orig_hyp.belief.value

    def test_export_includes_interventions(self):
        """Export must include interventions and verification status."""
        service = InvestigationService()
        investigation = service.create_demo()
        export = DiagnosisExport.from_investigation(investigation)
        
        assert len(export.interventions_applied) == len(investigation.interventions)
        
        for exported_interv, orig_interv in zip(export.interventions_applied, investigation.interventions):
            assert exported_interv.description == orig_interv.description
            assert exported_interv.status == orig_interv.status.value

    def test_export_to_dict_is_json_serializable(self):
        """Export.to_dict() must be JSON-serializable."""
        service = InvestigationService()
        investigation = service.create_demo()
        export = DiagnosisExport.from_investigation(investigation)
        
        export_dict = export.to_dict()
        json_str = json.dumps(export_dict)
        
        assert json_str is not None
        parsed = json.loads(json_str)
        assert parsed["id"] == export.id
        assert parsed["root_cause"] == export.root_cause

    def test_export_fails_without_root_cause(self):
        """Export should fail if root_cause is not set."""
        service = InvestigationService()
        investigation = service.create_demo()
        investigation.root_cause = None
        
        with pytest.raises(ValueError, match="Cannot export: no root_cause"):
            DiagnosisExport.from_investigation(investigation)

    def test_export_fails_without_engineer_confirmation(self):
        """Export should fail if engineer has not confirmed."""
        service = InvestigationService()
        investigation = service.create_demo()
        investigation.engineer_confirmed = False
        
        with pytest.raises(ValueError, match="Cannot export: engineer has not confirmed"):
            DiagnosisExport.from_investigation(investigation)

    def test_export_fails_if_not_resolved(self):
        """Export should fail if investigation is not resolved/closed."""
        service = InvestigationService()
        investigation = service.create_demo()
        investigation.status = InvestigationStatus.INVESTIGATING
        
        with pytest.raises(ValueError, match="Cannot export: investigation status"):
            DiagnosisExport.from_investigation(investigation)


class TestExportEndpoint:
    """Test the FastAPI export endpoint."""

    def test_export_demo_endpoint_returns_200(self):
        """POST /diagnoses/demo/export should return 200 with valid demo."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.post("/diagnoses/demo/export")
        
        assert response.status_code == 200

    def test_export_demo_endpoint_has_diagnosis(self):
        """Response should contain 'diagnosis' field with exported data."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.post("/diagnoses/demo/export")
        
        data = response.json()
        assert "diagnosis" in data
        assert data["diagnosis"]["id"] is not None
        assert data["diagnosis"]["root_cause"] is not None

    def test_export_demo_endpoint_includes_symptom(self):
        """Export should include full symptom data."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.post("/diagnoses/demo/export")
        
        diagnosis = response.json()["diagnosis"]
        assert "symptom_what_is_wrong" in diagnosis
        assert "symptom_expected_behaviour" in diagnosis
        assert "symptom_actual_behaviour" in diagnosis
        assert "symptom_affected_scope" in diagnosis

    def test_export_demo_endpoint_includes_hypotheses(self):
        """Export should include hypotheses with evidence."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.post("/diagnoses/demo/export")
        
        diagnosis = response.json()["diagnosis"]
        assert "hypotheses_explored" in diagnosis
        assert len(diagnosis["hypotheses_explored"]) > 0
        
        for hyp in diagnosis["hypotheses_explored"]:
            assert "statement" in hyp
            assert "final_status" in hyp
            assert "supporting_evidence" in hyp
            assert "contradicting_evidence" in hyp

    def test_export_demo_endpoint_is_json_valid(self):
        """Response should be valid JSON with all required fields."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.post("/diagnoses/demo/export")
        
        diagnosis = response.json()["diagnosis"]
        
        required_fields = [
            "id", "title",
            "symptom_what_is_wrong", "symptom_expected_behaviour",
            "symptom_actual_behaviour", "symptom_affected_scope",
            "hypotheses_explored", "root_cause", "root_cause_confidence",
            "interventions_applied",
            "engineer_confirmed", "investigation_status",
            "exported_at"
        ]
        
        for field in required_fields:
            assert field in diagnosis, f"Missing required field: {field}"
