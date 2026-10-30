"""Google Gemini provider adapter."""
from typing import AsyncIterator

import google.generativeai as genai

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse
from backend.core.config.settings import settings

_EMBEDDING_TASK_TYPES = {"document": "retrieval_document", "query": "retrieval_query"}


class GeminiProvider(BaseAIProvider):
    provider_name = "gemini"
    _known_fallback_models = ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro")

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = self._resolve_model_name(settings.gemini_model)

    @classmethod
    def _resolve_model_name(cls, configured_name: str | None) -> str:
        raw = (configured_name or "").strip()
        if not raw:
            return "gemini-2.0-flash"

        normalized = raw.replace("models/", "")
        if normalized in cls._known_fallback_models:
            return normalized

        # The repo uses an older google-generativeai SDK. Newer model names like
        # gemini-2.5-flash can be rejected by the service/client combination.
        if "2.5" in normalized or normalized.startswith("gemini-2."):
            return "gemini-2.0-flash"

        return normalized

    def _prepare(self, messages: list[ChatMessage]) -> tuple[genai.GenerativeModel, list[dict]]:
        """Send system messages as Gemini's system instruction and the rest as turns."""
        system = "\n\n".join(m.content for m in messages if m.role == "system") or None
        turns = [
            {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
            for m in messages
            if m.role != "system"
        ]
        if not turns:
            turns, system = [{"role": "user", "parts": [system or ""]}], None
        return genai.GenerativeModel(self._model_name, system_instruction=system), turns

    async def chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> ChatResponse:
        model, turns = self._prepare(messages)
        response = await model.generate_content_async(
            turns,
            generation_config=genai.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
        )
        return ChatResponse(
            content=response.text,
            model=self._model_name,
            provider=self.provider_name,
        )

    async def stream_chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> AsyncIterator[str]:
        model, turns = self._prepare(messages)
        response = await model.generate_content_async(
            turns,
            generation_config=genai.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
            stream=True,
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embed(self, texts: list[str], input_type: str | None = None) -> list[list[float]]:
        if not texts:
            return []
        # The SDK sends a list as batched requests (up to 100 texts per call).
        result = await genai.embed_content_async(
            model=settings.gemini_embedding_model,
            content=list(texts),
            task_type=_EMBEDDING_TASK_TYPES.get(input_type or ""),
            output_dimensionality=settings.embedding_dimension,
        )
        return result["embedding"]
