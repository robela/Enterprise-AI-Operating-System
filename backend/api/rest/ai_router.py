"""AI REST endpoints — chat, RAG query, agent dispatch."""
from typing import Annotated
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.core.database.session import get_db
from backend.ai.orchestration.orchestrator import OrchestratorAgent
from backend.ai.agents.base_agent import AgentContext
from backend.ai.rag.pipeline import RAGPipeline
from backend.ai.safety.policy import SafetyPolicy
from backend.infrastructure.persistence.models import (
    ConversationModel,
    MessageModel,
    OrganizationModel,
)

router = APIRouter(prefix="/ai", tags=["ai"])
_safety = SafetyPolicy()


class ChatRequest(BaseModel):
    message: str | None = None  # Single message (legacy)
    messages: list[dict] | None = None  # Messages array (new format)
    conversation_history: list[dict] = []
    conversation_id: str | None = None
    sector: str | None = None
    provider: str | None = None
    stream: bool = False
    document_program: list[str] | None = None
    document_module: list[str] | None = None
    document_type: str | None = None


class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    message_id: str | None = None
    conversation_id: str | None = None
    sources: list[str] = []
    agent: str = ""
    requires_human_review: bool = False
    trace: list[dict] | None = None
    completeness: "CompletenessMetadata | None" = None


class CompletenessMetadata(BaseModel):
    workflow_id: str | None = None
    missing_fields: list[str] = []
    source_pages: list[int] = []


class Conversation(BaseModel):
    id: str
    title: str
    sector: str | None = None
    created_at: str
    updated_at: str
    last_updated: str
    message_count: int
    messages: list[dict] | None = None


class Program(BaseModel):
    id: str
    name: str
    description: str | None = None


class Module(BaseModel):
    id: str
    program_id: str
    name: str
    description: str | None = None


class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "en"


# In-memory storage (in production, use database)
_conversations: dict = {}
_programs: list[Program] = [
    Program(id="prog1", name="Program A", description="Description for Program A"),
    Program(id="prog2", name="Program B", description="Description for Program B"),
]
_modules: list[Module] = [
    Module(id="mod1", program_id="prog1", name="Module 1", description="Module 1 Description"),
    Module(id="mod2", program_id="prog1", name="Module 2", description="Module 2 Description"),
    Module(id="mod3", program_id="prog2", name="Module 3", description="Module 3 Description"),
]


def _normalize_sector(sector: str | None) -> str | None:
    if not sector:
        return None
    normalized = sector.strip().lower().replace(" ", "-")
    return normalized or None


def _with_sector_prefix(title: str, sector: str | None) -> str:
    normalized = _normalize_sector(sector)
    if not normalized:
        return title
    return f"[sector:{normalized}] {title}"


def _split_sector_title(raw_title: str | None) -> tuple[str | None, str]:
    title = (raw_title or "").strip() or "Untitled"
    prefix = "[sector:"
    if not title.startswith(prefix):
        return None, title

    closing_index = title.find("] ")
    if closing_index == -1:
        return None, title

    sector = title[len(prefix):closing_index].strip() or None
    clean_title = title[closing_index + 2 :].strip() or "Untitled"
    return sector, clean_title


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        # Extract message from either format
        message = body.message
        if not message and body.messages:
            # Get the last user message from the messages array
            for msg in reversed(body.messages):
                if msg.get("role") == "user":
                    message = msg.get("content", "")
                    break
        
        if not message:
            raise HTTPException(status_code=400, detail="No message provided")

        now = datetime.utcnow()
        normalized_sector = _normalize_sector(body.sector)

        # Reuse existing conversation when possible; otherwise create one.
        conversation = None
        if body.conversation_id:
            query = select(ConversationModel).where(
                ConversationModel.conversation_id == body.conversation_id,
                ConversationModel.user_id == current_user.user_id,
                ConversationModel.tenant_id == current_user.tenant_id,
            )
            result = await db.execute(query)
            conversation = result.scalars().first()

            if conversation and normalized_sector:
                conversation_sector, _ = _split_sector_title(conversation.title)
                if conversation_sector != normalized_sector:
                    raise HTTPException(status_code=409, detail="Conversation belongs to a different sector")

        if not conversation:
            initial_title = message.strip()[:80] or "New Conversation"
            conversation = ConversationModel(
                conversation_id=str(uuid4()),
                user_id=current_user.user_id,
                tenant_id=current_user.tenant_id,
                title=_with_sector_prefix(initial_title, normalized_sector),
                created_at=now,
                updated_at=now,
                message_count=0,
            )
            db.add(conversation)
            await db.flush()

        user_message = MessageModel(
            message_id=str(uuid4()),
            conversation_id=conversation.conversation_id,
            role="user",
            content=message,
            citations={},
            images={},
            videos={},
            audio_url=None,
            created_at=now,
        )
        db.add(user_message)
        
        safety = _safety.check_input(message)
        requires_human_review = False
        answer_text = ""
        sources: list[str] = []
        agent_name = ""
        trace: list[dict] | None = None

        if not safety.safe:
            requires_human_review = True
            answer_text = "I'm unable to process that request."
            trace = [{"policy": "blocked_input"}]
        else:
            tenant_settings: dict = {}
            tenant_org = await db.scalar(
                select(OrganizationModel).where(
                    OrganizationModel.slug == current_user.tenant_id,
                    OrganizationModel.is_active.is_(True),
                )
            )
            if tenant_org and isinstance(tenant_org.settings, dict):
                tenant_settings = tenant_org.settings

            history_result = await db.execute(
                select(MessageModel.role, MessageModel.content)
                .where(
                    MessageModel.conversation_id == conversation.conversation_id,
                    MessageModel.role == "user",
                )
                .order_by(MessageModel.created_at)
            )
            conversation_history = [
                {"role": role, "content": content}
                for role, content in history_result.all()
            ]

            orchestrator = OrchestratorAgent()
            context = AgentContext(
                user_query=message,
                tenant_id=current_user.tenant_id,
                user_id=current_user.user_id,
                conversation_history=conversation_history or body.conversation_history,
                metadata={"tenant_settings": tenant_settings},
            )
            result = await orchestrator.run(context)
            answer_text = result.answer
            sources = result.sources
            agent_name = result.agent_name
            requires_human_review = result.requires_human_review
            trace = [result.metadata] if result.metadata else None

        assistant_message_id = str(uuid4())
        assistant_message = MessageModel(
            message_id=assistant_message_id,
            conversation_id=conversation.conversation_id,
            role="assistant",
            content=answer_text,
            citations={"sources": sources},
            images={},
            videos={},
            audio_url=None,
            created_at=datetime.utcnow(),
        )
        db.add(assistant_message)

        conversation.message_count = (conversation.message_count or 0) + 2
        conversation.updated_at = datetime.utcnow()
        await db.flush()

        return ChatResponse(
            answer=answer_text,
            message_id=assistant_message_id,
            conversation_id=conversation.conversation_id,
            sources=sources,
            agent=agent_name,
            requires_human_review=requires_human_review,
            trace=trace,
            completeness=(
                CompletenessMetadata(
                    workflow_id=result.metadata.get("workflow_id"),
                    missing_fields=result.metadata.get("missing_fields", []),
                    source_pages=result.metadata.get("source_pages", []),
                )
                if agent_name == "completeness" else None
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Chat endpoint error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=ChatResponse)
async def rag_query(
    body: RAGQueryRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    pipeline = RAGPipeline(tenant_id=current_user.tenant_id)
    result = await pipeline.query(body.question, top_k=body.top_k)
    return ChatResponse(
        answer=result["answer"],
        message_id=str(uuid4()),
        sources=result["sources"]
    )


# ============ Conversation Management ============

@router.post("/chat/conversations", response_model=Conversation)
async def create_conversation(
    body: dict,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new conversation."""
    conv_id = str(uuid4())
    now = datetime.utcnow()
    normalized_sector = _normalize_sector(body.get("sector"))
    plain_title = body.get("title", "New Conversation")
    
    conversation = ConversationModel(
        conversation_id=conv_id,
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        title=_with_sector_prefix(plain_title, normalized_sector),
        created_at=now,
        updated_at=now,
        message_count=0,
    )
    
    db.add(conversation)
    await db.flush()
    
    return Conversation(
        id=conv_id,
        title=plain_title,
        sector=normalized_sector,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
        last_updated=now.isoformat(),
        message_count=0,
        messages=[],
    )


@router.get("/chat/conversations/list", response_model=list[Conversation])
async def get_conversations(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sector: str | None = None,
):
    """List all conversations for the user."""
    normalized_sector = _normalize_sector(sector)
    query = select(ConversationModel).where(
        ConversationModel.user_id == current_user.user_id,
        ConversationModel.tenant_id == current_user.tenant_id,
    )

    if normalized_sector:
        query = query.where(
            ConversationModel.title.like(f"[sector:{normalized_sector}]%")
        )

    query = query.order_by(ConversationModel.updated_at.desc())
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return [
        Conversation(
            id=conv.conversation_id,
            title=_split_sector_title(conv.title)[1],
            sector=_split_sector_title(conv.title)[0],
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            last_updated=conv.updated_at.isoformat(),
            message_count=conv.message_count,
            messages=[],
        )
        for conv in conversations
    ]


@router.get("/chat/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific conversation with messages."""
    query = select(ConversationModel).where(
        ConversationModel.conversation_id == conversation_id,
        ConversationModel.user_id == current_user.user_id,
        ConversationModel.tenant_id == current_user.tenant_id,
    )
    
    result = await db.execute(query)
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages_query = (
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at.asc())
    )
    messages_result = await db.execute(messages_query)
    ordered_messages = messages_result.scalars().all()

    messages = [
        {
            "id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "citations": msg.citations,
            "images": msg.images,
            "audio_url": msg.audio_url,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in ordered_messages
    ]
    
    return Conversation(
        id=conversation.conversation_id,
        title=_split_sector_title(conversation.title)[1],
        sector=_split_sector_title(conversation.title)[0],
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        last_updated=conversation.updated_at.isoformat(),
        message_count=conversation.message_count,
        messages=messages,
    )


@router.put("/chat/{conversation_id}/messages/{message_id}")
async def edit_message(
    conversation_id: str,
    message_id: str,
    body: dict,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Edit a message in a conversation."""
    conversation_query = select(ConversationModel).where(
        ConversationModel.conversation_id == conversation_id,
        ConversationModel.user_id == current_user.user_id,
        ConversationModel.tenant_id == current_user.tenant_id,
    )

    conversation_result = await db.execute(conversation_query)
    conversation = conversation_result.scalars().first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = select(MessageModel).where(
        MessageModel.message_id == message_id,
        MessageModel.conversation_id == conversation_id,
    )
    
    result = await db.execute(query)
    message = result.scalars().first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.content = body.get("content", message.content)
    message.updated_at = datetime.utcnow()
    await db.flush()
    
    return {"status": "success"}


@router.delete("/chat/conversations/{conversation_id}/messages")
async def clear_conversation(
    conversation_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Clear all messages in a conversation."""
    query = select(ConversationModel).where(
        ConversationModel.conversation_id == conversation_id,
        ConversationModel.user_id == current_user.user_id,
        ConversationModel.tenant_id == current_user.tenant_id,
    )
    
    result = await db.execute(query)
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.execute(
        delete(MessageModel).where(MessageModel.conversation_id == conversation_id)
    )
    
    conversation.message_count = 0
    conversation.updated_at = datetime.utcnow()
    await db.flush()
    
    return {"status": "success"}


@router.delete("/chat/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a conversation."""
    query = select(ConversationModel).where(
        ConversationModel.conversation_id == conversation_id,
        ConversationModel.user_id == current_user.user_id,
        ConversationModel.tenant_id == current_user.tenant_id,
    )
    
    result = await db.execute(query)
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.flush()
    
    return {"status": "success"}


# ============ Text-to-Speech ============

@router.post("/chat/text-to-speech")
async def text_to_speech(
    body: TextToSpeechRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Generate speech from text."""
    # In production, use a TTS service (Google Cloud TTS, Azure Speech, etc.)
    # For now, return a placeholder audio blob
    from fastapi.responses import StreamingResponse
    import io
    
    # Placeholder: return a simple WAV file header
    # In production, integrate with actual TTS API
    audio_data = io.BytesIO()
    audio_data.write(b"fake-audio-data")  # Replace with real TTS output
    audio_data.seek(0)
    
    return StreamingResponse(
        audio_data,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=speech.wav"},
    )


@router.post("/chat/transcribe")
async def transcribe_audio(
    file: bytes,
    language: str = "en",
    current_user: Annotated[CurrentUser, Depends(get_current_user)] = None,
):
    """Transcribe audio to text (STT)."""
    # In production, use speech-to-text service (Google Cloud Speech, Azure Speech, etc.)
    return {"text": "Transcribed text would appear here"}


# ============ Programs & Modules ============

@router.get("/programs", response_model=list[Program])
async def get_programs(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Get all programs."""
    return _programs


@router.get("/program-modules", response_model=list[Module])
async def get_program_modules(
    program_id: str | None = None,
    current_user: Annotated[CurrentUser, Depends(get_current_user)] = None,
):
    """Get modules, optionally filtered by program."""
    if program_id:
        return [m for m in _modules if m.program_id == program_id]
    return _modules
