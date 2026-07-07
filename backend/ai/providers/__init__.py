"""AI provider factory — resolves provider by name."""
from backend.ai.base import BaseAIProvider
from backend.core.config.settings import settings


def get_provider(provider_name: str | None = None) -> BaseAIProvider:
    name = (provider_name or settings.ai_provider).lower()
    if name == "openai":
        from backend.ai.providers.openai import OpenAIProvider
        return OpenAIProvider()
    if name == "azure_openai":
        from backend.ai.providers.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider()
    if name == "anthropic":
        from backend.ai.providers.anthropic import AnthropicProvider
        return AnthropicProvider()
    if name == "gemini":
        from backend.ai.providers.gemini import GeminiProvider
        return GeminiProvider()
    if name == "ollama":
        from backend.ai.providers.ollama import OllamaProvider
        return OllamaProvider()
    raise ValueError(f"Unknown AI provider: {name!r}")
