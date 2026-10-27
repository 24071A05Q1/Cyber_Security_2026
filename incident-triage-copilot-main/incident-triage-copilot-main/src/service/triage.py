from __future__ import annotations

import time
import uuid

from src.classification.predict import predict_category
from src.config import settings
from src.generation.bedrock import BedrockResponseGenerator
from src.generation.local import LocalResponseGenerator
from src.guardrails.bedrock import BedrockGuardrail
from src.guardrails.local import LocalGuardrail
from src.retrieval.bedrock import BedrockKnowledgeBaseRetriever
from src.retrieval.local import get_local_retriever
from src.schemas import Citation, IncidentRequest, TriageResponse
from src.storage.audit import append_audit_event


def _severity(text: str, confidence: float) -> str:
    lowered = text.lower()
    urgent_terms = ["entire room", "class stopped", "no power", "offline", "multiple devices", "packet loss"]
    if any(term in lowered for term in urgent_terms):
        return "high"
    return "medium" if confidence >= 0.60 else "low"


def _providers():
    if settings.ai_provider == "bedrock":
        return BedrockGuardrail(), BedrockKnowledgeBaseRetriever(), BedrockResponseGenerator()
    return LocalGuardrail(), get_local_retriever(), LocalResponseGenerator()


def triage_incident(request: IncidentRequest) -> TriageResponse:
    started = time.perf_counter()
    incident_id = f"DEMO-{uuid.uuid4().hex[:10].upper()}"
    guardrail, retriever, generator = _providers()
    original_text = f"{request.title}. {request.description}"

    input_result = guardrail.apply(original_text, "INPUT")
    if not input_result.allowed:
        response = TriageResponse(
            incident_id=incident_id,
            category="blocked",
            severity="unknown",
            confidence=0.0,
            needs_human_review=True,
            root_cause_hypothesis="The request was blocked by the input guardrail.",
            recommended_actions=["Remove unsafe instructions or sensitive content and resubmit the incident."],
            citations=[],
            guardrail_status=input_result.status,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        append_audit_event(response.model_dump())
        return response

    category, confidence = predict_category(input_result.text)
    documents = retriever.retrieve(input_result.text, category=category, top_k=settings.top_k)
    hypothesis, actions = generator.generate(input_result.text, category, documents)
    generated_text = hypothesis + "\n" + "\n".join(actions)
    output_result = guardrail.apply(generated_text, "OUTPUT")

    if not output_result.allowed:
        hypothesis = "The generated recommendation was blocked by the output guardrail."
        actions = ["Route the incident and retrieved evidence to a human analyst."]

    response = TriageResponse(
        incident_id=incident_id,
        category=category,
        severity=_severity(input_result.text, confidence),
        confidence=round(confidence, 4),
        needs_human_review=confidence < settings.confidence_threshold or not output_result.allowed,
        root_cause_hypothesis=hypothesis,
        recommended_actions=actions,
        citations=[Citation(
            source_id=doc.source_id,
            title=doc.title,
            excerpt=doc.content[:300],
            score=round(doc.score, 4),
        ) for doc in documents],
        guardrail_status=f"{input_result.status}|{output_result.status}",
        latency_ms=round((time.perf_counter() - started) * 1000, 2),
    )
    append_audit_event(response.model_dump())
    return response
