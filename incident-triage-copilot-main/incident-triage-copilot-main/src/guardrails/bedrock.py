from __future__ import annotations

import boto3

from src.config import settings
from src.guardrails.local import GuardrailResult


class BedrockGuardrail:
    def __init__(self) -> None:
        if not settings.bedrock_guardrail_id:
            raise ValueError("BEDROCK_GUARDRAIL_ID is required for Bedrock guardrails.")
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def apply(self, text: str, source: str) -> GuardrailResult:
        response = self.client.apply_guardrail(
            guardrailIdentifier=settings.bedrock_guardrail_id,
            guardrailVersion=settings.bedrock_guardrail_version,
            source=source.upper(),
            content=[{"text": {"text": text}}],
            outputScope="FULL",
        )
        action = response.get("action", "NONE")
        outputs = response.get("outputs", [])
        output_text = " ".join(item.get("text", "") for item in outputs).strip() or text
        allowed = action != "GUARDRAIL_INTERVENED"
        return GuardrailResult(
            allowed=allowed,
            text=output_text if allowed else "",
            status="allowed" if allowed else "blocked",
            reasons=[action],
        )
