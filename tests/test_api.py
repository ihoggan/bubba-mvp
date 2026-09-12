from fastapi.testclient import TestClient

from bubba.diagnosis.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_endpoint() -> None:
    response = client.get("/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert "root_cause" in data
    assert len(data["hypotheses"]) == 4
