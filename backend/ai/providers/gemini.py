"""Google Gemini provider adapter."""
from typing import AsyncIterator

import google.generativeai as genai

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse
from backend.core.config.settings import settings


class GeminiProvider(BaseAIProvider):
    provider_name = "gemini"

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = "gemini-1.5-pro"

    async def chat(
        self, messages: list[ChatMessage], temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> ChatResponse:
        model = genai.GenerativeModel(self._model_name)
        history = [
            {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
            for m in messages[:-1]
        ]
        chat = model.start_chat(history=history)
        response = await chat.send_message_async(
            messages[-1].content,
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
        model = genai.GenerativeModel(self._model_name)
        response = await model.generate_content_async(
            messages[-1].content,
            generation_config=genai.GenerationConfig(temperature=temperature),
            stream=True,
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            result = await genai.embed_content_async(
                model="models/text-embedding-004", content=text
            )
            results.append(result["embedding"])
        return results
