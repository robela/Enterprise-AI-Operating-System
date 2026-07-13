"""Validation agent — checks data or decisions for correctness."""
from backend.ai.agents.base_agent import BaseAgent, AgentContext, AgentResult
from backend.ai.providers import get_provider
from backend.ai.base import ChatMessage


class ValidationAgent(BaseAgent):
    agent_name = "validation"

    async def run(self, context: AgentContext) -> AgentResult:
        provider = get_provider()
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a validation specialist. "
                    "Your job is to check whether the user's input is correct, compliant, "
                    "and consistent. Return a JSON object with keys: valid (bool), "
                    "issues (list of strings), suggestions (list of strings)."
                ),
            ),
            ChatMessage(role="user", content=context.user_query),
        ]
        response = await provider.chat(messages, temperature=0.1)
        return AgentResult(
            answer=response.content,
            agent_name=self.agent_name,
            requires_human_review=True,  # Validation results always need review
        )
