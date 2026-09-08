"""Feedback management endpoints."""
from typing import Annotated
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.core.database.session import get_db
from backend.infrastructure.persistence.models import (
    FeedbackModel,
    DislikeReasonModel,
    SurveyModel,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# Models
class LikeFeedback(BaseModel):
    conversation_id: str
    message_id: str
    liked: bool


class LikeFeedbackResponse(BaseModel):
    feedback_id: str
    conversation_id: str
    message_id: str
    liked: bool
    created_at: str


class DislikeOption(BaseModel):
    id: str
    name: str
    category: str  # "length" | "accuracy" | "clarity" | "translation" | "relevance"
    description: str | None = None


class CategoricalFeedback(BaseModel):
    conversation_id: str
    message_id: str
    feedback_id: str
    feedback_tags: list[str]


class CategoricalFeedbackResponse(BaseModel):
    feedback_id: str
    message_id: str
    conversation_id: str
    feedback_tags: list[str]
    created_at: str


class SurveySubmission(BaseModel):
    conversation_id: str
    action_taken: list[str]
    intent_changed: bool
    additional_feedback: str | None = None


class SurveyResponse(BaseModel):
    conversation_id: str
    action_taken: list[str]
    intent_changed: bool
    additional_feedback: str | None = None
    created_at: str


# Sample dislike options (in production, fetch from database)
DISLIKE_OPTIONS = [
    DislikeOption(id="d1", name="Too long", category="length", description="Response was too verbose"),
    DislikeOption(id="d2", name="Too short", category="length", description="Response lacked detail"),
    DislikeOption(id="a1", name="Inaccurate", category="accuracy", description="Information was incorrect"),
    DislikeOption(id="a2", name="Outdated", category="accuracy", description="Information is no longer current"),
    DislikeOption(id="c1", name="Unclear", category="clarity", description="Hard to understand"),
    DislikeOption(id="c2", name="Confusing", category="clarity", description="Content was confusing"),
    DislikeOption(id="t1", name="Poor translation", category="translation", description="Translation quality was poor"),
    DislikeOption(id="r1", name="Not relevant", category="relevance", description="Didn't answer my question"),
]


@router.post("/like", response_model=LikeFeedbackResponse)
async def submit_like_feedback(
    body: LikeFeedback,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit like/dislike feedback for a message."""
    feedback_id = str(uuid.uuid4())
    
    feedback = FeedbackModel(
        feedback_id=feedback_id,
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        user_id=current_user.user_id,
        liked=body.liked,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(feedback)
    await db.flush()
    
    return LikeFeedbackResponse(
        feedback_id=feedback_id,
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        liked=body.liked,
        created_at=datetime.utcnow().isoformat(),
    )


@router.get("/dislike-options", response_model=list[DislikeOption])
async def get_dislike_options(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get available dislike reason options from database."""
    query = select(DislikeReasonModel).where(
        DislikeReasonModel.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    options = result.scalars().all()
    
    return [
        DislikeOption(
            id=opt.dislike_reason_id,
            name=opt.name,
            category=opt.category,
            description=opt.description,
        )
        for opt in options
    ]


@router.post("/categorical", response_model=CategoricalFeedbackResponse)
async def submit_categorical_feedback(
    body: CategoricalFeedback,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit categorical feedback (reasons for dislike)."""
    feedback_id = str(uuid.uuid4())
    
    feedback = FeedbackModel(
        feedback_id=feedback_id,
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        user_id=current_user.user_id,
        categorical_tags=body.feedback_tags,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(feedback)
    await db.flush()
    
    return CategoricalFeedbackResponse(
        feedback_id=feedback_id,
        message_id=body.message_id,
        conversation_id=body.conversation_id,
        feedback_tags=body.feedback_tags,
        created_at=datetime.utcnow().isoformat(),
    )


@router.post("/survey", response_model=SurveyResponse)
async def submit_survey(
    body: SurveySubmission,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit post-chat survey responses."""
    survey_id = str(uuid.uuid4())
    
    survey = SurveyModel(
        survey_id=survey_id,
        conversation_id=body.conversation_id,
        user_id=current_user.user_id,
        action_taken=body.action_taken,
        intent_changed=body.intent_changed,
        additional_feedback=body.additional_feedback,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(survey)
    await db.flush()
    
    return SurveyResponse(
        conversation_id=body.conversation_id,
        action_taken=body.action_taken,
        intent_changed=body.intent_changed,
        additional_feedback=body.additional_feedback,
        created_at=datetime.utcnow().isoformat(),
    )
