"""AI safety policy — content filtering and guardrails."""
from __future__ import annotations
import unicodedata
from collections.abc import Iterable
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


def _normalize(text: str) -> str:
    """Fold full-width/compatibility characters, case, and repeated whitespace."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


class SafetyPolicy:
    """Basic prompt injection and content safety filter.

    The patterns are English. For other languages, pass the English translation of the
    message in also_check so the same patterns apply.

    In production, augment with:
    - Azure Content Safety API
    - OpenAI Moderation endpoint
    - Custom fine-tuned classifier
    """

    def check_input(self, text: str, also_check: Iterable[str | None] = ()) -> SafetyResult:
        for candidate in (text, *also_check):
            if not candidate:
                continue
            normalized = _normalize(candidate)
            for pattern in BLOCKED_PATTERNS:
                if pattern in normalized:
                    return SafetyResult(
                        safe=False,
                        reason="Potential prompt injection detected",
                        blocked_pattern=pattern,
                    )
        return SafetyResult(safe=True)

    def check_output(self, text: str) -> SafetyResult:
        # Add PII detection, harmful content checks, etc.
        return SafetyResult(safe=True)
