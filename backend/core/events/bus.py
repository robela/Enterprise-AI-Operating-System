"""Base domain event and in-process event bus."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
import uuid


@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str = "default"
    aggregate_id: str = ""
    aggregate_type: str = ""

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


Handler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    """Simple in-process async event bus.

    For production use, replace publish() with Kafka/RabbitMQ publishing
    while keeping the same subscribe() interface for local handlers.
    """

    def __init__(self):
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._process())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _process(self) -> None:
        while True:
            event = await self._queue.get()
            handlers = self._handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    import structlog
                    structlog.get_logger(__name__).exception(
                        "event_handler_error", event_type=event.event_type
                    )
            self._queue.task_done()


event_bus = EventBus()
