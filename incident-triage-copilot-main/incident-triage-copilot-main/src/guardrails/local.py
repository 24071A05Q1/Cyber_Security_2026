from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    text: str
    status: str
    reasons: list[str]


INJECTION_PATTERNS = [
    r"ignore (all|any|the) previous instructions",
    r"reveal (the )?(system|developer) prompt",
    r"bypass (the )?(guardrail|safety|policy)",
    r"disable (the )?(security|logging|guardrail)",
]

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
}


class LocalGuardrail:
    def apply(self, text: str, source: str) -> GuardrailResult:
        lowered = text.lower()
        reasons = [pattern for pattern in INJECTION_PATTERNS if re.search(pattern, lowered)]
        if reasons:
            return GuardrailResult(False, "", f"blocked_{source.lower()}", ["prompt_injection"])

        masked = text
        pii_found: list[str] = []
        for name, pattern in PII_PATTERNS.items():
            if pattern.search(masked):
                pii_found.append(name)
                masked = pattern.sub(f"[{name.upper()}_MASKED]", masked)

        status = f"allowed_{source.lower()}"
        if pii_found:
            status += "_pii_masked"
        return GuardrailResult(True, masked, status, pii_found)
