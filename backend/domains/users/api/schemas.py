"""Pydantic schemas for the users API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from backend.domains.users.domain.entities.user import User


class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    roles: Optional[list[str]] = None

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    roles: Optional[list[str]] = None


class UserResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    full_name: str
    status: str
    roles: list[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    mfa_enabled: bool

    @classmethod
    def from_domain(cls, user: User) -> UserResponse:
        return cls(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            email=str(user.email),
            full_name=user.full_name,
            status=user.status.value,
            roles=user.roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            mfa_enabled=user.mfa_enabled,
        )


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
