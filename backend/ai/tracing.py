"""Per-request trace records: what ran for an AI request and how it went.

Traces hold metadata only (agent, counts, timings, document IDs), never question or
answer text, so they are safe to keep after a conversation is deleted. Agent metadata is
copied through an allowlist so a new agent cannot put user content into a trace by
accident."""
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.persistence.models import RequestTraceModel

logger = structlog.get_logger(__name__)

# Agent metadata copied into ``details``. Add a key here only if it never holds user text.
DETAIL_KEYS = frozenset(
    {
        "workflow_id",
        "missing_fields",
        "source_pages",
        "used_translated_input",
        "machine_translated",
        "tenant_prompt_override",
        "policy",
    }
)


class Stopwatch:
    def __init__(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)


def build_trace(
    *,
    tenant_id: str,
    endpoint: str,
    status: str,
    latency_ms: int,
    user_id: str | None = None,
    conversation_id: str | None = None,
    message_id: str | None = None,
    agent: str | None = None,
    language: str | None = None,
    sources: Iterable[str] = (),
    requires_human_review: bool = False,
    metadata: dict[str, Any] | None = None,
    error: BaseException | None = None,
) -> RequestTraceModel:
    metadata = metadata or {}
    return RequestTraceModel(
        trace_id=str(uuid4()),
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        endpoint=endpoint,
        agent=agent or None,
        status=status,
        language=language,
        reranker=metadata.get("reranker"),
        query_rewritten=bool(metadata.get("query_rewritten", False)),
        chunks_used=int(metadata.get("chunks_used") or 0),
        sources=list(sources),
        requires_human_review=requires_human_review,
        latency_ms=latency_ms,
        # The exception class only: messages can echo the request.
        error_type=type(error).__name__ if error else None,
        details={key: value for key, value in metadata.items() if key in DETAIL_KEYS},
        created_at=datetime.now(timezone.utc),
    )


async def save_trace(session: AsyncSession, trace: RequestTraceModel) -> None:
    """Commit a trace in its own session. Never raises: a trace must not break a request."""
    try:
        session.add(trace)
        await session.commit()
    except Exception as exc:  # pragma: no cover - depends on database availability
        logger.warning("request_trace_not_saved", error_type=type(exc).__name__)
        await session.rollback()
