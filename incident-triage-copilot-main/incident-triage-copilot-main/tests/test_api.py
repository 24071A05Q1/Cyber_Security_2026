from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_triage_returns_citations():
    response = client.post("/triage", json={
        "title": "Projector shows no signal",
        "description": "The projector is on but cannot display the instructor laptop through HDMI.",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "av"
    assert payload["citations"]
