from __future__ import annotations

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    score: float


class TriageResponse(BaseModel):
    incident_id: str
    category: str
    severity: str
    confidence: float
    needs_human_review: bool
    root_cause_hypothesis: str
    recommended_actions: list[str]
    citations: list[Citation]
    guardrail_status: str
    latency_ms: float
