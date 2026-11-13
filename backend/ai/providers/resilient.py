"""Timeouts and retries for any provider.

Only temporary failures are retried (timeouts, connection errors, rate limits, 5xx). Bad
requests, auth errors, and safety blocks fail at once, since retrying cannot fix them.
"""
from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import AsyncIterator, TypeVar

import structlog

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse
from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)

T = TypeVar("T")

_TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
# Exception class names used by the provider SDKs (openai, anthropic, httpx, google).
_TRANSIENT_NAMES = {
    "APIConnectionError",
    "APITimeoutError",
    "RateLimitError",
    "InternalServerError",
    "ServiceUnavailable",
    "ResourceExhausted",
    "DeadlineExceeded",
    "TooManyRequests",
    "BadGateway",
    "GatewayTimeout",
    "TimeoutException",
    "ConnectError",
    "ConnectTimeout",
    "ReadTimeout",
    "RemoteProtocolError",
}


def is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError, ConnectionError)):
        return True
    for status in (
        getattr(exc, "status_code", None),
        getattr(exc, "code", None),
        getattr(getattr(exc, "response", None), "status_code", None),
    ):
        if isinstance(status, int) and status in _TRANSIENT_STATUS:
            return True
    return type(exc).__name__ in _TRANSIENT_NAMES


class ResilientProvider(BaseAIProvider):
    """Wraps a provider with a per-call timeout and retries with exponential backoff."""

    def __init__(
        self,
        inner: BaseAIProvider,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        base_delay_seconds: float | None = None,
    ):
        self.inner = inner
        self.provider_name = inner.provider_name
        self.timeout_seconds = timeout_seconds or settings.llm_timeout_seconds
        self.max_retries = max(0, settings.llm_max_retries if max_retries is None else max_retries)
        self.base_delay_seconds = (
            settings.llm_retry_base_delay_seconds if base_delay_seconds is None else base_delay_seconds
        )

    async def chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> ChatResponse:
        return await self._call(
            "chat",
            lambda: self.inner.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs),
        )

    async def stream_chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> AsyncIterator[str]:
        # Not retried: part of the answer may already have reached the user.
        async for piece in self.inner.stream_chat(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield piece

    async def embed(self, texts: list[str], input_type: str | None = None) -> list[list[float]]:
        return await self._call("embed", lambda: self.inner.embed(texts, input_type=input_type))

    async def _call(self, operation: str, make_call: Callable[[], Awaitable[T]]) -> T:
        attempt = 0
        while True:
            try:
                return await asyncio.wait_for(make_call(), timeout=self.timeout_seconds)
            except Exception as exc:
                if attempt >= self.max_retries or not is_transient(exc):
                    raise
                delay = self.base_delay_seconds * (2**attempt) * (1 + random.random() * 0.25)
                attempt += 1
                logger.warning(
                    "llm_call_retry",
                    provider=self.provider_name,
                    operation=operation,
                    attempt=attempt,
                    error_type=type(exc).__name__,
                    delay_seconds=round(delay, 2),
                )
                await asyncio.sleep(delay)
