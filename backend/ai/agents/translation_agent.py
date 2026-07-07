"""Translation agent."""
from backend.ai.agents.base_agent import BaseAgent, AgentContext, AgentResult
from backend.ai.providers import get_provider
from backend.ai.base import ChatMessage


class TranslationAgent(BaseAgent):
    agent_name = "translation"

    async def run(self, context: AgentContext) -> AgentResult:
        provider = get_provider()
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a professional translator. "
                    "Translate the user's text accurately, preserving tone and meaning. "
                    "Return only the translated text, nothing else."
                ),
            ),
            ChatMessage(role="user", content=context.user_query),
        ]
        response = await provider.chat(messages, temperature=0.3)
        return AgentResult(answer=response.content, agent_name=self.agent_name)
