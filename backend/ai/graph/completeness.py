"""Extract review candidates for completeness rules from source PDF text."""
from __future__ import annotations

import re
from dataclasses import dataclass


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
_REQUIREMENT_INSTRUCTION = re.compile(
    r"^(?:[■▼➤—-]\s*)*(?:assess|ask|check|determine|measure|look for|evaluate|record)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RequirementCandidate:
    """A source-backed item that must be approved before becoming a rule."""

    text: str
    page_number: int


def extract_requirement_candidates(pages: list[str], limit: int = 50) -> list[RequirementCandidate]:
    """Return unique, explicit assessment candidates with their PDF page number.

    This deliberately does not infer clinical requirements. Its output is a review
    queue for a clinician or guideline owner to approve and structure as rules.
    """
    candidates: list[RequirementCandidate] = []
    seen: set[str] = set()

    for page_number, page_text in enumerate(pages, start=1):
        for raw_sentence in _SENTENCE_BOUNDARY.split(page_text):
            sentence = " ".join(raw_sentence.split())
            normalized = sentence.casefold()
            if len(sentence) < 12 or normalized in seen:
                continue
            if not _REQUIREMENT_INSTRUCTION.search(sentence):
                continue

            seen.add(normalized)
            candidates.append(RequirementCandidate(text=sentence, page_number=page_number))
            if len(candidates) >= limit:
                return candidates

    return candidates