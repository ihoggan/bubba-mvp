"""FastAPI endpoints for the sandbox."""

from fastapi import FastAPI
from pydantic import BaseModel

from bubba.diagnosis.application.service import InvestigationService

app = FastAPI(title="DecisionDesk v2 MVP", version="0.1.0")
service = InvestigationService()


class HealthResponse(BaseModel):
    """Health response payload."""

    status: str


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
