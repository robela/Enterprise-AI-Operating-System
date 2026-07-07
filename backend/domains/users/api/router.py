"""Users REST API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.domains.users.api.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
)
from backend.domains.users.application.services.user_service import UserService
from backend.domains.users.infrastructure.persistence.user_repository_impl import (
    SQLAlchemyUserRepository,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(SQLAlchemyUserRepository(db))


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    user = await service.create_user(
        tenant_id=current_user.tenant_id,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        roles=body.roles,
    )
    return UserResponse.from_domain(user)


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    users = await service.list_users(current_user.tenant_id, skip=skip, limit=limit)
    return UserListResponse(items=[UserResponse.from_domain(u) for u in users], total=len(users))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    user = await service.get_user(user_id, current_user.tenant_id)
    return UserResponse.from_domain(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    user = await service.update_user(
        user_id, current_user.tenant_id, full_name=body.full_name, roles=body.roles
    )
    return UserResponse.from_domain(user)


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    await service.deactivate_user(user_id, current_user.tenant_id)
