"""Anthropic Claude provider adapter."""
from typing import AsyncIterator

import anthropic

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse
from backend.core.config.settings import settings


class AnthropicProvider(BaseAIProvider):
    provider_name = "anthropic"

    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = "claude-3-5-sonnet-20241022"

    async def chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> ChatResponse:
        system = next((m.content for m in messages if m.role == "system"), None)
        human_messages = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        params = dict(model=self._model, messages=human_messages, max_tokens=max_tokens, **kwargs)
        if system:
            params["system"] = system

        response = await self._client.messages.create(**params)
        return ChatResponse(
            content=response.content[0].text,
            model=self._model,
            provider=self.provider_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    async def stream_chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> AsyncIterator[str]:
        system = next((m.content for m in messages if m.role == "system"), None)
        human_messages = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        params = dict(model=self._model, messages=human_messages, max_tokens=max_tokens)
        if system:
            params["system"] = system
        async with self._client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Anthropic doesn't expose embeddings — delegate to OpenAI
        from backend.ai.providers.openai import OpenAIProvider
        return await OpenAIProvider().embed(texts)
