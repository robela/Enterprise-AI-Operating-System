"""Deterministic extraction of reviewable workflow drafts from PDF pages."""
from __future__ import annotations

from dataclasses import dataclass
import re

from backend.ai.graph.completeness import extract_requirement_candidates


_FIELD_ALIASES = {
    "age": "child_age",
    "danger sign": "general_danger_signs",
    "symptom": "main_symptoms",
    "nutrition": "nutrition_status",
    "immunization": "immunization_status",
    "other problem": "other_problems",
}
_TITLE_PREFIX = re.compile(r"^(?:[■▼➤—-]\s*)*", re.IGNORECASE)


@dataclass(frozen=True)
class WorkflowDraft:
    name: str
    workflow_type: str
    steps: list[str]
    required_fields: list[str]
    source_pages: list[int]
    source_excerpt: str
    confidence: str


def extract_workflow_drafts(pages: list[str], limit: int = 25) -> list[WorkflowDraft]:
    """Group explicit PDF instructions into page-backed workflow drafts."""
    candidates = extract_requirement_candidates(pages, limit=limit * 6)
    by_page: dict[int, list[str]] = {}
    for candidate in candidates:
        by_page.setdefault(candidate.page_number, []).append(candidate.text)

    drafts: list[WorkflowDraft] = []
    for page_number, steps in by_page.items():
        if len(steps) < 2:
            continue
        title = _TITLE_PREFIX.sub("", steps[0]).rstrip(".")[:120]
        normalized_steps = list(dict.fromkeys(steps))
        source_excerpt = " ".join(normalized_steps)[:1500]
        field_keys = _infer_required_fields(source_excerpt)
        drafts.append(
            WorkflowDraft(
                name=title or f"Assessment workflow (page {page_number})",
                workflow_type="assessment",
                steps=normalized_steps,
                required_fields=field_keys,
                source_pages=[page_number],
                source_excerpt=source_excerpt,
                confidence="medium",
            )
        )
        if len(drafts) >= limit:
            break
    return drafts


def _infer_required_fields(source_text: str) -> list[str]:
    normalized = source_text.casefold()
    return [field for phrase, field in _FIELD_ALIASES.items() if phrase in normalized]