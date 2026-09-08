"""Mock AI provider for testing and development."""
from typing import AsyncIterator

from backend.ai.base import BaseAIProvider, ChatMessage, ChatResponse


class MockProvider(BaseAIProvider):
    """Mock provider that returns predetermined responses for testing."""
    
    provider_name = "mock"

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> ChatResponse:
        # Extract the last user message
        user_query = ""
        for msg in reversed(messages):
            if msg.role == "user":
                user_query = msg.content
                break
        
        # Generate mock response based on query
        response_map = {
            "test": "This is a test response from the Mock Provider.",
            "what": "Enterprise AI is a multi-tenant AI operating system designed for enterprise applications. It supports various AI providers, RAG pipelines, and advanced agent orchestration.",
            "hello": "Hello! I'm the Enterprise AI Assistant. How can I help you today?",
            "help": "I can assist with questions, document analysis, translations, and more. What would you like to know?",
        }
        
        # Find matching response (case-insensitive)
        answer = "I understand your question. Could you provide more details?"
        for key, resp in response_map.items():
            if key.lower() in user_query.lower():
                answer = resp
                break
        
        return ChatResponse(
            content=answer,
            model="mock-model",
            provider=self.provider_name,
            input_tokens=len(user_query.split()),
            output_tokens=len(answer.split()),
            finish_reason="stop",
        )

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream responses (mock: return all at once)."""
        response = await self.chat(messages, temperature, max_tokens, **kwargs)
        yield response.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for a batch of texts."""
        return [[0.1] * 1536 for _ in texts]
