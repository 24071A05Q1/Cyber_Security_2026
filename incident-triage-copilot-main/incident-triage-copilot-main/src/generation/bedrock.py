from __future__ import annotations

import boto3

from src.config import settings
from src.retrieval.base import RetrievedDocument


class BedrockResponseGenerator:
    def __init__(self) -> None:
        if not settings.bedrock_model_id:
            raise ValueError("BEDROCK_MODEL_ID is required for Bedrock mode.")
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def generate(self, incident_text: str, category: str, documents: list[RetrievedDocument]) -> tuple[str, list[str]]:
        evidence = "\n\n".join(
            f"[{doc.source_id}] {doc.title}\n{doc.content}" for doc in documents
        )
        prompt = f"""You are an IT incident-triage copilot. Use only the supplied evidence.
Do not claim certainty. Do not execute changes. Cite source IDs in the hypothesis.
Return exactly this format:
HYPOTHESIS: <one paragraph>
ACTIONS:
- <action>
- <action>

Category: {category}
Incident: {incident_text}
Evidence:
{evidence}
"""
        response = self.client.converse(
            modelId=settings.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.1, "maxTokens": 500},
        )
        text = response["output"]["message"]["content"][0]["text"]
        hypothesis = text
        actions: list[str] = []
        if "ACTIONS:" in text:
            hypothesis, action_text = text.split("ACTIONS:", 1)
            hypothesis = hypothesis.replace("HYPOTHESIS:", "").strip()
            actions = [line.lstrip("- ").strip() for line in action_text.splitlines() if line.strip().startswith("-")]
        return hypothesis.strip(), actions or ["Escalate to a human analyst with the retrieved evidence."]
