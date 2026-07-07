"""Ollama local LLM provider adapter."""
from typing import AsyncIterator

import httpx

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse
from backend.core.config.settings import settings


class OllamaProvider(BaseAIProvider):
    provider_name = "ollama"

    def __init__(self):
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model

    async def chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> ChatResponse:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            response.raise_for_status()
            data = response.json()
            return ChatResponse(
                content=data["message"]["content"],
                model=self._model,
                provider=self.provider_name,
            )

    async def stream_chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        chunk = json.loads(line)
                        if content := chunk.get("message", {}).get("content"):
                            yield content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        async with httpx.AsyncClient(timeout=60) as client:
            for text in texts:
                resp = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
        return embeddings
