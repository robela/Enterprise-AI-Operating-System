"""Identity / Auth REST API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.domains.identity.application.services.auth_service import AuthService
from backend.domains.users.infrastructure.persistence.user_repository_impl import (
    SQLAlchemyUserRepository,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(SQLAlchemyUserRepository(db))


@router.post("/token")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    tenant_id: str = Form(default="default"),
    service: AuthService = Depends(get_auth_service),
):
    """OAuth2 password flow — returns access + refresh tokens."""
    return await service.login(
        email=form.username, password=form.password, tenant_id=tenant_id
    )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str = Form(...),
    service: AuthService = Depends(get_auth_service),
):
    return await service.refresh(refresh_token)
