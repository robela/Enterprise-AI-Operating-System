"""Audit log entity — immutable record of every action."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditLog:
    """Immutable audit record — never update, only append."""
    log_id: str
    tenant_id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    ip_address: str | None
    user_agent: str | None
    result: str  # success | failure
    details: dict[str, Any]
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        tenant_id: str,
        action: str,
        resource_type: str,
        result: str = "success",
        user_id: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        return cls(
            log_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            details=details or {},
            occurred_at=datetime.now(timezone.utc),
        )
