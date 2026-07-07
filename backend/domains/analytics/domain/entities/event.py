"""Analytics event entity."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AnalyticsEvent:
    event_id: str
    tenant_id: str
    user_id: str | None
    event_name: str
    properties: dict[str, Any]
    session_id: str | None
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        tenant_id: str,
        event_name: str,
        properties: dict | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AnalyticsEvent:
        return cls(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            event_name=event_name,
            properties=properties or {},
            session_id=session_id,
            occurred_at=datetime.now(timezone.utc),
        )
