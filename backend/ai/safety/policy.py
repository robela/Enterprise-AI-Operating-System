"""AI safety policy — content filtering and guardrails."""
from __future__ import annotations
from dataclasses import dataclass


BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "you are now",
    "pretend you are",
    "jailbreak",
]


@dataclass
class SafetyResult:
    safe: bool
    reason: str = ""
    blocked_pattern: str = ""


class SafetyPolicy:
    """Basic prompt injection and content safety filter.

    In production, augment with:
    - Azure Content Safety API
    - OpenAI Moderation endpoint
    - Custom fine-tuned classifier
    """

    def check_input(self, text: str) -> SafetyResult:
        lower = text.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern in lower:
                return SafetyResult(
                    safe=False,
                    reason="Potential prompt injection detected",
                    blocked_pattern=pattern,
                )
        return SafetyResult(safe=True)

    def check_output(self, text: str) -> SafetyResult:
        # Add PII detection, harmful content checks, etc.
        return SafetyResult(safe=True)
