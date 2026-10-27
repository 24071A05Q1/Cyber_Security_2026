from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    ai_provider: str = os.getenv("AI_PROVIDER", "local").lower()
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "")
    bedrock_knowledge_base_id: str = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")
    bedrock_guardrail_id: str = os.getenv("BEDROCK_GUARDRAIL_ID", "")
    bedrock_guardrail_version: str = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
    top_k: int = int(os.getenv("TOP_K", "3"))
    model_path: Path = ROOT / "artifacts" / "incident_classifier.joblib"
    runbook_path: Path = ROOT / "data" / "runbooks.csv"
    incident_path: Path = ROOT / "data" / "incidents.csv"
    audit_path: Path = ROOT / "logs" / "triage_audit.jsonl"


settings = Settings()
