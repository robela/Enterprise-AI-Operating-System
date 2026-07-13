"""Celery application and document processing worker."""
from celery import Celery

from backend.core.config.settings import settings

celery_app = Celery(
    "enterprise_ai_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "backend.workers.document_processor.*": {"queue": "documents"},
        "backend.workers.ai_worker.*": {"queue": "ai"},
        "backend.workers.notification_worker.*": {"queue": "notifications"},
    },
)
