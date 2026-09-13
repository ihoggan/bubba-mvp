"""FastAPI endpoints for the sandbox."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bubba.diagnosis.application.service import InvestigationService
from bubba.diagnosis.domain.export import DiagnosisExport
from bubba.diagnosis.infrastructure.repository import InvestigationRepository

app = FastAPI(title="DecisionDesk v2 MVP", version="0.1.0")
service = InvestigationService()


class HealthResponse(BaseModel):
    """Health response payload."""
    status: str


class ExportResponse(BaseModel):
    """Diagnosis export response."""
    diagnosis: dict


class SearchResult(BaseModel):
    """Single search result summary."""
    id: str
    title: str
    symptom: str
    root_cause: str | None
    status: str
    engineer_confirmed: bool


class SearchResponse(BaseModel):
    """Search results response."""
    query: str
    search_type: str
    results: list[SearchResult]
    count: int


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return application health."""
    return HealthResponse(status="ok")


@app.get("/demo")
def demo() -> dict:
    """Return the synthetic investigation as JSON-serialisable data."""
    investigation = service.create_demo()
    return {
        "id": str(investigation.id),
        "title": investigation.title,
        "status": investigation.status.value,
        "root_cause": investigation.root_cause,
        "hypotheses": [
            {"statement": h.statement, "belief": h.belief.value, "status": h.status.value}
            for h in investigation.hypotheses
        ],
        "timeline": [
            {"occurred_at": e.occurred_at.isoformat(), "type": e.event_type, "summary": e.summary}
            for e in investigation.timeline
        ],
    }


@app.post("/diagnoses/demo/export", response_model=ExportResponse)
def export_demo() -> ExportResponse:
    """Export the demo investigation as a verified diagnosis.
    
    Returns 400 if the investigation is not export-ready:
    - Missing root_cause
    - engineer_confirmed is False
    - status is not resolved/closed
    """
    investigation = service.create_demo()
    
    try:
        export = DiagnosisExport.from_investigation(investigation)
        return ExportResponse(diagnosis=export.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/diagnoses/search/symptom", response_model=SearchResponse)
def search_by_symptom(q: str) -> SearchResponse:
    """Search investigations by symptom keyword.
    
    Args:
        q: Search query term
        
    Returns:
        List of matching investigations
    """
    repo = InvestigationRepository()
    results = repo.search_by_symptom(q)
    
    return SearchResponse(
        query=q,
        search_type="symptom",
        results=[SearchResult(**r) for r in results],
        count=len(results)
    )


@app.get("/diagnoses/search/root_cause", response_model=SearchResponse)
def search_by_root_cause(q: str) -> SearchResponse:
    """Search investigations by root cause keyword.
    
    Args:
        q: Search query term
        
    Returns:
        List of matching investigations
    """
    repo = InvestigationRepository()
    results = repo.search_by_root_cause(q)
    
    return SearchResponse(
        query=q,
        search_type="root_cause",
        results=[SearchResult(**r) for r in results],
        count=len(results)
    )


@app.get("/diagnoses/list", response_model=SearchResponse)
def list_all_diagnoses() -> SearchResponse:
    """List all stored investigations, newest first.
    
    Returns:
        List of all investigations
    """
    repo = InvestigationRepository()
    results = repo.list_all()
    
    return SearchResponse(
        query="",
        search_type="all",
        results=[SearchResult(**r) for r in results],
        count=len(results)
    )
