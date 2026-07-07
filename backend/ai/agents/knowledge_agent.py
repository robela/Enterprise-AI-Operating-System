"""Knowledge agent — answers questions using RAG."""
from backend.ai.agents.base_agent import BaseAgent, AgentContext, AgentResult
from backend.ai.providers import get_provider
from backend.ai.base import ChatMessage


class KnowledgeAgent(BaseAgent):
    agent_name = "knowledge"

    async def run(self, context: AgentContext) -> AgentResult:
        provider = get_provider()

        messages = [
            ChatMessage(role="system", content=(
                "You are a helpful enterprise AI assistant. "
                "Answer based on the provided context. "
                "If you don't know, say so clearly."
            )),
        ]
        # Inject conversation history
        for turn in context.conversation_history[-6:]:
            messages.append(ChatMessage(role=turn["role"], content=turn["content"]))
        messages.append(ChatMessage(role="user", content=context.user_query))

        response = await provider.chat(messages)

        return AgentResult(
            answer=response.content,
            agent_name=self.agent_name,
            metadata={"model": response.model, "provider": response.provider},
        )
