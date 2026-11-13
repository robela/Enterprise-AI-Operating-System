"""Agent orchestrator — routes tasks to specialised agents."""
from __future__ import annotations

import structlog
import re

from backend.ai.agents.base_agent import AgentContext, AgentResult
from backend.ai.agents.knowledge_agent import KnowledgeAgent
from backend.ai.agents.validation_agent import ValidationAgent
from backend.ai.agents.translation_agent import TranslationAgent
from backend.ai.agents.completeness_agent import (
    CompletenessAgent,
    has_danger_sign,
    is_follow_up_form_answer,
)
from backend.ai.language import base_language
from backend.ai.multilingual import localize_answer
from backend.ai.providers import get_provider

logger = structlog.get_logger(__name__)


class OrchestratorAgent:
    """
    Top-level agent that:
    1. Classifies the user intent.
    2. Routes to the appropriate specialist agent(s).
    3. Assembles the final response.

    Reads context.metadata["language"] (answer language) and
    context.metadata["english_query"] (English translation) when the caller provides them.
    """

    def __init__(self):
        self._knowledge = KnowledgeAgent()
        self._validation = ValidationAgent()
        self._translation = TranslationAgent()
        self._completeness = CompletenessAgent()

    async def run(self, context: AgentContext) -> AgentResult:
        language = context.metadata.get("language")
        # Log sizes and codes only; the query itself may contain health information.
        logger.info("orchestrator_run", query_chars=len(context.user_query), language=language)

        intent = await self._classify_intent(context)
        logger.info("intent_classified", intent=intent)

        if intent == "knowledge":
            return await self._knowledge.run(context)
        if intent == "completeness":
            return await self._localize(await self._completeness.run(context), language)
        if intent == "validation":
            return await self._validation.run(context)
        if intent == "translation":
            return await self._translation.run(context)

        # Default: pass directly to knowledge agent
        return await self._knowledge.run(context)

    async def _classify_intent(self, context: AgentContext) -> str:
        """Simple keyword-based intent classifier — replace with LLM call in production.

        Also checks the English translation, so non-English questions route the same way.
        """
        queries = [context.user_query.lower()]
        english_query = context.metadata.get("english_query")
        if english_query:
            queries.append(english_query.lower())

        if any(_is_translation(q) for q in queries):
            return "translation"
        if any(_is_completeness(q) for q in queries):
            return "completeness"
        if any(any(w in q for w in ["validate", "check", "verify", "is valid"]) for q in queries):
            return "validation"
        return "knowledge"

    async def _localize(self, result: AgentResult, language: str | None) -> AgentResult:
        """Translate a fixed English answer. Keeps the English original so a reviewer can
        compare, since these answers support clinical follow-up."""
        if not language or base_language(language) == "en":
            return result
        translated = await localize_answer(result.answer, language, get_provider())
        if not translated:
            return result
        result.answer = f"{translated}\n\n---\n\n*English original:*\n\n{result.answer}"
        result.metadata = {**result.metadata, "machine_translated": True, "language": language}
        return result


def _is_translation(q: str) -> bool:
    return any(w in q for w in ["translate", "translation", "in french", "in spanish"])


def _is_completeness(q: str) -> bool:
    if any(phrase in q for phrase in ["missing information", "missing questions", "missed questions", "check missing", "check missed"]):
        return True
    if "child" in q and re.search(
        r"\b(?:cough|fever|diarrh(?:ea|oea)|vomiting|difficulty breathing|breathing problem)\b", q
    ):
        return True
    if "child" in q and has_danger_sign(q):
        return True
    return is_follow_up_form_answer(q)
