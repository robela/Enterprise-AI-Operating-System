"""Chat agent for source-backed missing-information checks."""
from __future__ import annotations

import re
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.agents.base_agent import AgentContext, AgentResult, BaseAgent
from backend.core.database.session import AsyncSessionLocal
from backend.infrastructure.persistence.models import ExtractedWorkflowModel


_FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "child_age": re.compile(
        r"\b(?:\d+\s*(?:years?|months?|weeks?)(?:\s+old)?|age\s*(?:\((?:years?|months?)\))?\s*(?:is|:)?\s*\d+)\b",
        re.IGNORECASE,
    ),
    "general_danger_signs": re.compile(
        r"\b(?:danger signs?|unable to drink|not able to drink|vomits? everything|convulsions?|seizures?|unconscious)\b",
        re.IGNORECASE,
    ),
    "main_symptoms": re.compile(
        r"\b(?:fever|cough|diarrh(?:ea|oea)|vomiting|difficulty breathing|breathing problem)\b",
        re.IGNORECASE,
    ),
    "nutrition_status": re.compile(r"\b(?:nutrition|weight|malnourished|feeding|appetite)\b", re.IGNORECASE),
    "immunization_status": re.compile(r"\b(?:immuni[sz]ation|vaccin(?:e|ated|ation))\b", re.IGNORECASE),
    "other_problems": re.compile(r"\b(?:other problem|additional problem|also has)\b", re.IGNORECASE),
    # Built-in danger-sign checklist fields. A reported danger sign does not answer
    # "other danger signs"; only an explicit statement about other signs does.
    "other_danger_signs": re.compile(r"\b(?:other|additional|more|no|any)\s+danger\s+signs?\b", re.IGNORECASE),
    "symptom_assessment": re.compile(
        r"\b(?:cough|diarrh(?:ea|oea)|malnutrition|malnourished|ear (?:problem|pain|discharge|infection))\b",
        re.IGNORECASE,
    ),
    "child_weight": re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:kg|kgs|kilograms?)\b|\bweight\s*(?:\(kg\))?\s*(?:is|:)?\s*\d", re.IGNORECASE
    ),
}
_FIELD_QUESTIONS = {
    "child_age": "What is the child's age?",
    "general_danger_signs": "Are there any general danger signs, such as inability to drink, vomiting everything, convulsions, or unconsciousness?",
    "main_symptoms": "What are the child's main symptoms?",
    "nutrition_status": "What is known about the child's nutrition or feeding status?",
    "immunization_status": "What is the child's immunization status?",
    "other_problems": "Are there any other problems that need assessment?",
    "other_danger_signs": "Are there any other general danger signs (unable to drink or breastfeed, vomits everything, convulsions, lethargic or unconscious)?",
    "symptom_assessment": "Assess for cough, diarrhoea, malnutrition, and ear problems, depending on the child's age. What did you find?",
    "child_weight": "What is the child's weight (kg)? It is needed for accurate drug dose calculation.",
}

# Built-in rule: when a general danger sign is reported, ask these regardless of the
# tenant's approved workflows.
_DANGER_SIGN_PATTERN = re.compile(
    r"\b(?:lethargic|lethargy|unconscious|convulsions?|convulsing|seizures?|fits"
    r"|(?:unable to|not able to|cannot|can't) (?:drink|breastfeed|breast feed)"
    r"|vomit(?:s|ing)? everything)\b",
    re.IGNORECASE,
)
DANGER_SIGN_CHECKLIST_ID = "builtin:danger-signs"
_DANGER_SIGN_FIELDS = ["child_age", "other_danger_signs", "symptom_assessment", "child_weight"]


_NEGATION_BEFORE = re.compile(r"\b(?:no|not|without|denies|never)\s+(?:\w+\s+)?$", re.IGNORECASE)


def has_danger_sign(text: str) -> bool:
    """True when a general danger sign is reported and not negated ("no convulsions")."""
    return any(
        not _NEGATION_BEFORE.search(text[max(0, match.start() - 20) : match.start()])
        for match in _DANGER_SIGN_PATTERN.finditer(text)
    )


# Answers submitted from the chat's follow-up form start with one of its field labels
# (frontend ClinicalFollowUpForm), lowercased.
FOLLOW_UP_FORM_PREFIXES = (
    "child's age:",
    "child's age (years):",
    "general danger signs:",
    "main symptoms:",
    "nutrition or feeding status:",
    "immunization status:",
    "other problems:",
    "other danger signs:",
    "cough, diarrhoea, malnutrition, ear problems:",
    "child's weight (kg):",
)


def is_follow_up_form_answer(text: str) -> bool:
    return text.strip().lower().startswith(FOLLOW_UP_FORM_PREFIXES)


def current_case(user_query: str, history: list[str]) -> list[str]:
    """The user messages of the latest case, oldest first.

    A case is the last message that is not a follow-up form reply, plus the form replies
    after it. A new question later in the same chat starts a new case, so facts from an
    earlier case never count as answers.
    """
    messages = [text for text in history if text.strip()]
    # The chat endpoint's history already includes the current message.
    if messages and messages[-1].strip() == user_query.strip():
        messages.pop()
    messages.append(user_query)
    start = len(messages) - 1
    while start > 0 and is_follow_up_form_answer(messages[start]):
        start -= 1
    return messages[start:]


class CompletenessAgent(BaseAgent):
    agent_name = "completeness"

    def __init__(self, session_factory: Callable[[], AsyncSession] = AsyncSessionLocal):
        self._session_factory = session_factory

    async def run(self, context: AgentContext) -> AgentResult:
        # The field patterns are English, so also match against the English translation
        # of a non-English question. Earlier turns are not translated.
        english_query = context.metadata.get("english_query") or ""
        history = [
            str(message.get("content", ""))
            for message in context.conversation_history
            if message.get("role", "user") == "user"
        ]
        combined_text = "\n".join(current_case(context.user_query, history) + [english_query])
        if has_danger_sign(combined_text):
            return _danger_sign_result(combined_text, used_translated_input=bool(english_query))

        async with self._session_factory() as db:
            result = await db.execute(
                select(ExtractedWorkflowModel).where(
                    ExtractedWorkflowModel.tenant_id == context.tenant_id,
                    ExtractedWorkflowModel.status == "approved",
                ).order_by(ExtractedWorkflowModel.updated_at.desc())
            )
            workflows = list(result.scalars().all())

        if not workflows:
            return AgentResult(
                answer="No approved workflow is available for this tenant. Approve an extracted workflow in Documents before checking missing information.",
                agent_name=self.agent_name,
                requires_human_review=True,
            )

        workflow = max(
            workflows,
            key=lambda item: _workflow_match_score(item.required_fields or [], combined_text),
        )
        present_fields: set[str] = set()
        for field in workflow.required_fields or []:
            pattern = _FIELD_PATTERNS.get(field)
            if pattern and pattern.search(combined_text):
                present_fields.add(field)
        missing_fields = [field for field in (workflow.required_fields or []) if field not in present_fields]
        source_pages = ", ".join(str(page) for page in (workflow.source_pages or [])) or "not recorded"

        if not missing_fields:
            answer = f"## Completeness check\n\nAll required fields in **{workflow.name}** are present.\n\nSource: document pages {source_pages}."
        else:
            questions = [
                f"- {_FIELD_QUESTIONS.get(field, 'Please provide: ' + field.replace('_', ' ') + '.')}"
                for field in missing_fields
            ]
            answer = (
                f"## Missing information\n\nBased on the approved **{workflow.name}** workflow, please provide:\n\n"
                + "\n".join(questions)
                + f"\n\nSource: document pages {source_pages}."
            )

        return AgentResult(
            answer=answer,
            sources=[workflow.document_id],
            agent_name=self.agent_name,
            requires_human_review=True,
            metadata={
                "workflow_id": workflow.workflow_id,
                "missing_fields": missing_fields,
                "source_pages": workflow.source_pages or [],
                "used_translated_input": bool(english_query),
            },
        )


def _danger_sign_result(text: str, used_translated_input: bool) -> AgentResult:
    missing_fields = [field for field in _DANGER_SIGN_FIELDS if not _FIELD_PATTERNS[field].search(text)]
    source = "Source: built-in danger-sign checklist (not from an approved document)."
    if not missing_fields:
        answer = f"## Completeness check\n\nAll details in the danger-sign checklist are present.\n\n{source}"
    else:
        questions = [f"- {_FIELD_QUESTIONS[field]}" for field in missing_fields]
        answer = (
            "## Missing information\n\nA general danger sign was reported. Please provide:\n\n"
            + "\n".join(questions)
            + f"\n\n{source}"
        )
    return AgentResult(
        answer=answer,
        agent_name=CompletenessAgent.agent_name,
        requires_human_review=True,
        metadata={
            "workflow_id": DANGER_SIGN_CHECKLIST_ID,
            "missing_fields": missing_fields,
            "source_pages": [],
            "used_translated_input": used_translated_input,
        },
    )


def _workflow_match_score(required_fields: list[str], text: str) -> tuple[int, int]:
    """Prefer the approved workflow with the strongest observed fact match."""
    matched_fields = sum(
        bool((pattern := _FIELD_PATTERNS.get(field)) and pattern.search(text))
        for field in required_fields
    )
    return matched_fields, len(required_fields)