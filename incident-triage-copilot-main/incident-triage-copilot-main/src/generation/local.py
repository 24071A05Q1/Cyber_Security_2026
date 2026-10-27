from __future__ import annotations

import re

from src.retrieval.base import RetrievedDocument


class LocalResponseGenerator:
    def generate(self, incident_text: str, category: str, documents: list[RetrievedDocument]) -> tuple[str, list[str]]:
        if not documents:
            return (
                f"The available evidence is insufficient to determine the root cause of this {category} incident.",
                ["Route the incident to a human analyst and collect additional diagnostic evidence."],
            )
        primary = documents[0]
        hypothesis = (
            f"The incident most likely matches the '{primary.title}' failure pattern. "
            f"This is a hypothesis based on the highest-ranked approved runbook [{primary.source_id}]."
        )
        sentences = re.split(r"(?<=[A-Za-z])\.\s+(?=[A-Z])", primary.content.strip())
        actions = [sentence.strip().rstrip(".") for sentence in sentences if sentence.strip()][:4]
        return hypothesis, [f"{action}." for action in actions]
