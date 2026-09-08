"""Settings endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.security.oauth2 import get_current_user, CurrentUser

router = APIRouter(prefix="/settings", tags=["settings"])


class GlobalSettings(BaseModel):
    tts_enabled: bool = True
    stt_enabled: bool = True
    surveys_enabled: bool = True
    tracer_enabled: bool = True
    languages: list[str] = ["en"]


@router.get("/global", response_model=GlobalSettings)
async def get_global_settings(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Get global application settings."""
    # Check user role for admin features
    tracer_enabled = current_user.role == "admin"
    
    return GlobalSettings(
        tts_enabled=True,
        stt_enabled=True,
        surveys_enabled=True,
        tracer_enabled=tracer_enabled,
        languages=["en", "es", "fr"],
    )
