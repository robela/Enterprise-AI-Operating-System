"""Agent orchestrator — routes tasks to specialised agents."""
from __future__ import annotations

import structlog

from backend.ai.agents.base_agent import AgentContext, AgentResult
from backend.ai.agents.knowledge_agent import KnowledgeAgent
from backend.ai.agents.validation_agent import ValidationAgent
from backend.ai.agents.translation_agent import TranslationAgent

logger = structlog.get_logger(__name__)


class OrchestratorAgent:
    """
    Top-level agent that:
    1. Classifies the user intent.
    2. Routes to the appropriate specialist agent(s).
    3. Assembles the final response.
    """

    def __init__(self):
        self._knowledge = KnowledgeAgent()
        self._validation = ValidationAgent()
        self._translation = TranslationAgent()

    async def run(self, context: AgentContext) -> AgentResult:
        logger.info("orchestrator_run", user_query=context.user_query[:80])

        intent = await self._classify_intent(context)
        logger.info("intent_classified", intent=intent)

        if intent == "knowledge":
            return await self._knowledge.run(context)
        if intent == "validation":
            return await self._validation.run(context)
        if intent == "translation":
            return await self._translation.run(context)

        # Default: pass directly to knowledge agent
        return await self._knowledge.run(context)

    async def _classify_intent(self, context: AgentContext) -> str:
        """Simple keyword-based intent classifier — replace with LLM call in production."""
        q = context.user_query.lower()
        if any(w in q for w in ["translate", "translation", "in french", "in spanish"]):
            return "translation"
        if any(w in q for w in ["validate", "check", "verify", "is valid"]):
            return "validation"
        return "knowledge"
