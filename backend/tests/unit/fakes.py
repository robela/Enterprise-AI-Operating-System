"""Test doubles shared by the multilingual tests."""
from __future__ import annotations

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse


class FakeProvider(BaseAIProvider):
    """Returns queued chat replies and fixed vectors; records every call."""

    provider_name = "fake"

    def __init__(self, replies: list[str] | None = None, vectors: dict[str, list[float]] | None = None):
        self.replies = list(replies or [])
        self.vectors = vectors or {}
        self.chat_calls: list[list[ChatMessage]] = []
        self.embed_calls: list[tuple[list[str], str | None]] = []

    async def chat(self, messages, temperature=0.7, max_tokens=2048, **kwargs) -> ChatResponse:
        self.chat_calls.append(list(messages))
        content = self.replies.pop(0) if self.replies else ""
        return ChatResponse(content=content, model="fake", provider=self.provider_name)

    async def stream_chat(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        yield ""

    async def embed(self, texts, input_type=None):
        self.embed_calls.append((list(texts), input_type))
        return [self.vectors.get(text, [0.0, 0.0, 1.0]) for text in texts]


class FailingProvider(FakeProvider):
    async def chat(self, messages, temperature=0.7, max_tokens=2048, **kwargs) -> ChatResponse:
        raise RuntimeError("provider unavailable")
