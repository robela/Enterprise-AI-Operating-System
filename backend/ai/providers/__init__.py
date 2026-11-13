"""AI provider factory — resolves provider by name."""
import structlog

from backend.ai.base import BaseAIProvider
from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)


def get_embedding_provider() -> BaseAIProvider:
    """Provider for embeddings. EMBEDDING_PROVIDER overrides AI_PROVIDER so the vector
    index can stay on one embedding model when the chat model changes."""
    configured = (settings.embedding_provider or settings.ai_provider).lower()
    provider = get_provider(configured)
    if provider.provider_name == "mock" and configured != "mock":
        # Mock vectors are identical for every text, so anything indexed now must be re-ingested.
        logger.warning("embedding_provider_fell_back_to_mock", configured_provider=configured)
    return provider


def get_provider(provider_name: str | None = None) -> BaseAIProvider:
    """The named provider (default AI_PROVIDER), with timeouts and retries."""
    from backend.ai.providers.resilient import ResilientProvider

    return ResilientProvider(_build_provider(provider_name))


def _build_provider(provider_name: str | None = None) -> BaseAIProvider:
    name = (provider_name or settings.ai_provider).lower()

    # If no API key is configured for the default provider, use mock for testing
    if name == "openai" and not settings.openai_api_key:
        from backend.ai.providers.mock import MockProvider
        return MockProvider()
    if name == "gemini" and (not settings.gemini_api_key or not settings.gemini_model):
        from backend.ai.providers.mock import MockProvider
        return MockProvider()

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
        try:
            from backend.ai.providers.gemini import GeminiProvider
            return GeminiProvider()
        except Exception:
            from backend.ai.providers.mock import MockProvider
            return MockProvider()
    if name == "ollama":
        from backend.ai.providers.ollama import OllamaProvider
        return OllamaProvider()
    if name == "mock":
        from backend.ai.providers.mock import MockProvider
        return MockProvider()
    raise ValueError(f"Unknown AI provider: {name!r}")
