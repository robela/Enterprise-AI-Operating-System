"""Organization entity."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class Organization:
    org_id: str
    name: str
    slug: str
    plan: PlanType = PlanType.FREE
    max_users: int = 10
    max_ai_requests_per_month: int = 1000
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    settings: dict = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, slug: str, plan: PlanType = PlanType.FREE) -> Organization:
        return cls(org_id=str(uuid.uuid4()), name=name, slug=slug, plan=plan)
