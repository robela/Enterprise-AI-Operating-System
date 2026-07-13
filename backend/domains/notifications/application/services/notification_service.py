"""Notification service."""
import smtplib
from email.mime.text import MIMEText

import structlog

from backend.core.config.settings import settings
from backend.domains.notifications.domain.entities import Notification, NotificationChannel

logger = structlog.get_logger(__name__)


class NotificationService:
    async def send(self, notification: Notification) -> bool:
        try:
            if notification.channel == NotificationChannel.EMAIL:
                await self._send_email(notification)
            else:
                logger.info(
                    "notification_channel_not_implemented",
                    channel=notification.channel,
                    notification_id=notification.notification_id,
                )
            notification.mark_sent()
            return True
        except Exception as exc:
            logger.error("notification_send_failed", error=str(exc))
            notification.mark_failed()
            return False

    async def _send_email(self, notification: Notification) -> None:
        msg = MIMEText(notification.body, "html")
        msg["Subject"] = notification.subject
        msg["From"] = settings.email_from
        msg["To"] = notification.recipient_id  # recipient_id is email in this context

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
