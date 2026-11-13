"""Knowledge agent — answers questions using RAG."""
from backend.ai.agents.base_agent import BaseAgent, AgentContext, AgentResult
from backend.ai.prompts.registry import prompt_registry
from backend.ai.rag.pipeline import RAGPipeline
from backend.ai.rag.reranker import build_reranker


class KnowledgeAgent(BaseAgent):
    agent_name = "knowledge"

    async def run(self, context: AgentContext) -> AgentResult:
        tenant_settings = context.metadata.get("tenant_settings", {})
        system_prompt = prompt_registry.get_for_tenant(
            "rag_system_v1",
            tenant_id=context.tenant_id,
            tenant_settings=tenant_settings,
        )

        reranker = build_reranker(tenant_settings)
        rag = RAGPipeline(tenant_id=context.tenant_id, reranker=reranker)
        rag_result = await rag.query(
            question=context.user_query,
            system_prompt=system_prompt,
            language=context.metadata.get("language"),
            english_query=context.metadata.get("english_query"),
            history=[
                str(message.get("content", ""))
                for message in context.conversation_history
                if message.get("role", "user") == "user"
            ],
        )

        return AgentResult(
            answer=rag_result["answer"],
            sources=rag_result["sources"],
            agent_name=self.agent_name,
            metadata={
                "chunks_used": rag_result.get("chunks_used", 0),
                "language": rag_result.get("language"),
                "reranker": reranker.name,
                "query_rewritten": rag_result.get("query_rewritten", False),
                "tenant_prompt_override": bool(
                    (tenant_settings.get("prompts", {}) or {}).get("rag_system_v1")
                ),
            },
        )
