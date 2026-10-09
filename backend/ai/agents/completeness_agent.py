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
    "child_age": re.compile(r"\b(?:\d+\s*(?:years?|months?|weeks?)(?:\s+old)?|age\s*(?:is|:)?\s*\d+)\b", re.IGNORECASE),
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
}
_FIELD_QUESTIONS = {
    "child_age": "What is the child's age?",
    "general_danger_signs": "Are there any general danger signs, such as inability to drink, vomiting everything, convulsions, or unconsciousness?",
    "main_symptoms": "What are the child's main symptoms?",
    "nutrition_status": "What is known about the child's nutrition or feeding status?",
    "immunization_status": "What is the child's immunization status?",
    "other_problems": "Are there any other problems that need assessment?",
}


class CompletenessAgent(BaseAgent):
    agent_name = "completeness"

    def __init__(self, session_factory: Callable[[], AsyncSession] = AsyncSessionLocal):
        self._session_factory = session_factory

    async def run(self, context: AgentContext) -> AgentResult:
        combined_text = "\n".join(
            [context.user_query] + [str(message.get("content", "")) for message in context.conversation_history]
        )
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
            questions = [f"- {_FIELD_QUESTIONS.get(field, f'Please provide: {field.replace("_", " ")}.')}" for field in missing_fields]
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
            },
        )


def _workflow_match_score(required_fields: list[str], text: str) -> tuple[int, int]:
    """Prefer the approved workflow with the strongest observed fact match."""
    matched_fields = sum(
        bool((pattern := _FIELD_PATTERNS.get(field)) and pattern.search(text))
        for field in required_fields
    )
    return matched_fields, len(required_fields)