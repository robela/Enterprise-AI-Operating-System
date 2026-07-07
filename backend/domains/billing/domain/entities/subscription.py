"""Billing / subscription entity."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    UNPAID = "unpaid"


@dataclass
class Subscription:
    subscription_id: str
    tenant_id: str
    plan_id: str
    status: SubscriptionStatus = SubscriptionStatus.TRIALING
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    amount_cents: int = 0
    currency: str = "USD"
    current_period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: datetime | None = None
    cancelled_at: datetime | None = None
    external_subscription_id: str = ""  # Stripe / Paddle subscription ID

    @classmethod
    def create(
        cls,
        tenant_id: str,
        plan_id: str,
        billing_period: BillingPeriod = BillingPeriod.MONTHLY,
        amount_cents: int = 0,
    ) -> Subscription:
        return cls(
            subscription_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            plan_id=plan_id,
            billing_period=billing_period,
            amount_cents=amount_cents,
        )

    def cancel(self) -> None:
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        self.status = SubscriptionStatus.ACTIVE
