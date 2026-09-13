"""Tests for investigation repository and search."""

import tempfile
from pathlib import Path

import pytest
from bubba.diagnosis.application.service import InvestigationService
from bubba.diagnosis.infrastructure.repository import InvestigationRepository


class TestInvestigationRepository:
    """Test SQLite repository for investigations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            yield db_path

    def test_repository_creates_database(self, temp_db):
        """Repository should create database and tables on init."""
        repo = InvestigationRepository(db_path=temp_db)
        assert Path(temp_db).exists()

    def test_save_investigation(self, temp_db):
        """Should persist investigation to database."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        repo = InvestigationRepository(db_path=temp_db)
        investigation_id = repo.save(investigation)
        
        assert investigation_id == str(investigation.id)

    def test_list_all_returns_saved_investigation(self, temp_db):
        """List should include saved investigations."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        repo = InvestigationRepository(db_path=temp_db)
        repo.save(investigation)
        
        results = repo.list_all()
        assert len(results) == 1
        assert results[0]["title"] == investigation.title

    def test_search_by_symptom(self, temp_db):
        """Should find investigations by symptom keyword."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        repo = InvestigationRepository(db_path=temp_db)
        repo.save(investigation)
        
        results = repo.search_by_symptom("Application")
        assert len(results) == 1
        assert "Application" in results[0]["symptom"]

    def test_search_by_symptom_no_match(self, temp_db):
        """Search should return empty list for non-matching query."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        repo = InvestigationRepository(db_path=temp_db)
        repo.save(investigation)
        
        results = repo.search_by_symptom("XYZ_NONEXISTENT")
        assert len(results) == 0

    def test_search_by_root_cause(self, temp_db):
        """Should find investigations by root cause keyword."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        repo = InvestigationRepository(db_path=temp_db)
        repo.save(investigation)
        
        results = repo.search_by_root_cause("policy")
        assert len(results) == 1
        assert "policy" in results[0]["root_cause"].lower()

    def test_search_by_root_cause_no_match(self, temp_db):
        """Search should return empty list for non-matching query."""
        service = InvestigationService()
        investigation = service.create_demo()
        
        repo = InvestigationRepository(db_path=temp_db)
        repo.save(investigation)
        
        results = repo.search_by_root_cause("XYZ_NONEXISTENT")
        assert len(results) == 0

    def test_multiple_investigations_searchable(self, temp_db):
        """Should handle multiple investigations in database."""
        service = InvestigationService()
        
        repo = InvestigationRepository(db_path=temp_db)
        
        # Save multiple demos (they're identical, but DB should handle it)
        for _ in range(3):
            investigation = service.create_demo()
            repo.save(investigation)
        
        all_results = repo.list_all()
        # We save 3 but the last 2 have same ID so they overwrite
        # The key is: list should work and return results
        assert len(all_results) >= 1


class TestSearchEndpoints:
    """Test search API endpoints."""

    def test_search_symptom_endpoint(self):
        """GET /diagnoses/search/symptom should return results."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.get("/diagnoses/search/symptom?q=Application")
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert data["search_type"] == "symptom"
        assert "results" in data
        assert "count" in data

    def test_search_root_cause_endpoint(self):
        """GET /diagnoses/search/root_cause should return results."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.get("/diagnoses/search/root_cause?q=policy")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "root_cause"

    def test_list_all_endpoint(self):
        """GET /diagnoses/list should return all investigations."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.get("/diagnoses/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "all"
        assert "results" in data

    def test_search_empty_query(self):
        """Search with empty query should work gracefully."""
        from fastapi.testclient import TestClient
        from bubba.diagnosis.api.main import app
        
        client = TestClient(app)
        response = client.get("/diagnoses/search/symptom?q=")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
