"""Notification entity."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


@dataclass
class Notification:
    notification_id: str
    tenant_id: str
    recipient_id: str
    channel: NotificationChannel
    subject: str
    body: str
    status: NotificationStatus = NotificationStatus.PENDING
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = None

    @classmethod
    def create(
        cls,
        tenant_id: str,
        recipient_id: str,
        channel: NotificationChannel,
        subject: str,
        body: str,
        metadata: dict | None = None,
    ) -> Notification:
        return cls(
            notification_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            channel=channel,
            subject=subject,
            body=body,
            metadata=metadata or {},
        )

    def mark_sent(self) -> None:
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        self.status = NotificationStatus.FAILED
