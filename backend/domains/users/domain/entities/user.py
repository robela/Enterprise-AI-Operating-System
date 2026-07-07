"""User aggregate root entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from backend.domains.users.domain.value_objects.email import Email
from backend.domains.users.domain.events.user_events import UserCreated, UserUpdated, UserDeactivated


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class User:
    """User aggregate root."""

    user_id: str
    tenant_id: str
    email: Email
    full_name: str
    hashed_password: str
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    roles: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: datetime | None = None
    mfa_enabled: bool = False
    _domain_events: list = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        tenant_id: str,
        email: str,
        full_name: str,
        hashed_password: str,
        roles: list[str] | None = None,
    ) -> User:
        user = cls(
            user_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=Email(email),
            full_name=full_name,
            hashed_password=hashed_password,
            roles=roles or ["user"],
        )
        user._domain_events.append(
            UserCreated(
                aggregate_id=user.user_id,
                aggregate_type="User",
                tenant_id=tenant_id,
                email=str(user.email),
                full_name=full_name,
            )
        )
        return user

    def update(self, full_name: str | None = None, roles: list[str] | None = None) -> None:
        if full_name:
            self.full_name = full_name
        if roles is not None:
            self.roles = roles
        self.updated_at = datetime.now(timezone.utc)
        self._domain_events.append(
            UserUpdated(aggregate_id=self.user_id, aggregate_type="User", tenant_id=self.tenant_id)
        )

    def deactivate(self) -> None:
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)
        self._domain_events.append(
            UserDeactivated(aggregate_id=self.user_id, aggregate_type="User", tenant_id=self.tenant_id)
        )

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def record_login(self) -> None:
        self.last_login_at = datetime.now(timezone.utc)

    def pop_events(self) -> list:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
