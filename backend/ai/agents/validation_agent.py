"""Validation agent — checks data or decisions for correctness."""
from backend.ai.agents.base_agent import BaseAgent, AgentContext, AgentResult
from backend.ai.providers import get_provider
from backend.ai.base import ChatMessage
from backend.ai.language import language_name


class ValidationAgent(BaseAgent):
    agent_name = "validation"

    async def run(self, context: AgentContext) -> AgentResult:
        provider = get_provider()
        language = context.metadata.get("language")
        target = language_name(language) if language else "the same language as the user's input"
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a validation specialist. "
                    "Your job is to check whether the user's input is correct, compliant, "
                    "and consistent. Return a JSON object with keys: valid (bool), "
                    "issues (list of strings), suggestions (list of strings). "
                    f"Write the issues and suggestions in {target}."
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
