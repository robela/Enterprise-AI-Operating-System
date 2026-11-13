"""Timeouts and retries around providers."""
import asyncio

import pytest

from backend.ai.base import ChatMessage
from backend.ai.providers import get_provider
from backend.ai.providers.resilient import ResilientProvider, is_transient
from fakes import FakeProvider


class RateLimitError(Exception):
    """Same class name the OpenAI SDK uses."""


class StatusError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class FlakyProvider(FakeProvider):
    def __init__(self, errors: list[Exception]):
        super().__init__(replies=["ok"])
        self.errors = list(errors)
        self.attempts = 0

    async def chat(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        self.attempts += 1
        if self.errors:
            raise self.errors.pop(0)
        return await super().chat(messages, temperature, max_tokens, **kwargs)


def _resilient(inner, **kwargs) -> ResilientProvider:
    return ResilientProvider(inner, base_delay_seconds=0, **kwargs)


async def test_retries_temporary_failures_then_succeeds() -> None:
    inner = FlakyProvider([RateLimitError("slow down"), StatusError(503)])

    response = await _resilient(inner, max_retries=2).chat([ChatMessage(role="user", content="hi")])

    assert response.content == "ok"
    assert inner.attempts == 3


async def test_gives_up_after_max_retries() -> None:
    inner = FlakyProvider([StatusError(503)] * 3)

    with pytest.raises(StatusError):
        await _resilient(inner, max_retries=2).chat([ChatMessage(role="user", content="hi")])
    assert inner.attempts == 3


async def test_does_not_retry_permanent_failures() -> None:
    inner = FlakyProvider([StatusError(400)])

    with pytest.raises(StatusError):
        await _resilient(inner, max_retries=2).chat([ChatMessage(role="user", content="hi")])
    assert inner.attempts == 1


async def test_times_out_slow_calls() -> None:
    class SlowProvider(FakeProvider):
        async def embed(self, texts, input_type=None):
            await asyncio.sleep(1)
            return []

    with pytest.raises(TimeoutError):
        await _resilient(SlowProvider(), timeout_seconds=0.01, max_retries=0).embed(["x"])


async def test_stream_passes_through() -> None:
    pieces = [piece async for piece in _resilient(FakeProvider()).stream_chat([])]

    assert pieces == [""]


def test_transient_detection() -> None:
    assert is_transient(TimeoutError())
    assert is_transient(StatusError(429))
    assert is_transient(RateLimitError())
    assert not is_transient(StatusError(401))
    assert not is_transient(ValueError("bad request"))


def test_get_provider_wraps_and_keeps_the_name() -> None:
    provider = get_provider("mock")

    assert isinstance(provider, ResilientProvider)
    assert provider.provider_name == "mock"
