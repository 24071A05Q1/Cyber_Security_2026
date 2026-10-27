from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.schemas import IncidentRequest, TriageResponse
from src.service.triage import triage_incident

app = FastAPI(
    title="AI Incident-Triage Copilot",
    version="0.1.0",
    description="Classify incidents, retrieve approved runbooks, and generate guarded recommendations.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
def triage(request: IncidentRequest) -> TriageResponse:
    try:
        return triage_incident(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
