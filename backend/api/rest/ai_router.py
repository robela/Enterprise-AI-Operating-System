"""AI REST endpoints — chat, RAG query, agent dispatch."""
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.ai.orchestration.orchestrator import OrchestratorAgent
from backend.ai.agents.base_agent import AgentContext
from backend.ai.rag.pipeline import RAGPipeline
from backend.ai.safety.policy import SafetyPolicy

router = APIRouter(prefix="/ai", tags=["ai"])
_safety = SafetyPolicy()


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []
    provider: str | None = None
    stream: bool = False


class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    agent: str = ""
    requires_human_review: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    safety = _safety.check_input(body.message)
    if not safety.safe:
        return ChatResponse(answer="I'm unable to process that request.", requires_human_review=True)

    orchestrator = OrchestratorAgent()
    context = AgentContext(
        user_query=body.message,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        conversation_history=body.conversation_history,
    )
    result = await orchestrator.run(context)
    return ChatResponse(
        answer=result.answer,
        sources=result.sources,
        agent=result.agent_name,
        requires_human_review=result.requires_human_review,
    )


@router.post("/rag/query", response_model=ChatResponse)
async def rag_query(
    body: RAGQueryRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    pipeline = RAGPipeline(tenant_id=current_user.tenant_id)
    result = await pipeline.query(body.question, top_k=body.top_k)
    return ChatResponse(answer=result["answer"], sources=result["sources"])
