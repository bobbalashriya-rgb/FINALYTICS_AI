import os
import logging
from core.embeddings.base import BaseEmbeddingProvider
from core.embeddings.providers import (
    DeterministicLocalEmbeddingProvider,
    OpenAIEmbeddingProvider,
    GeminiEmbeddingProvider,
)

logger = logging.getLogger(__name__)

_default_provider: BaseEmbeddingProvider | None = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory function returning the configured embedding provider based on environment settings.
    Defaults to DeterministicLocalEmbeddingProvider.
    """
    global _default_provider
    if _default_provider is not None:
        return _default_provider

    provider_type = os.getenv("EMBEDDING_PROVIDER", "local").lower().strip()

    if provider_type == "openai":
        try:
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            _default_provider = OpenAIEmbeddingProvider(model_name=model)
            logger.info("Initialized OpenAIEmbeddingProvider with model: %s", model)
            return _default_provider
        except Exception as exc:
            logger.warning(
                "Failed to initialize OpenAIEmbeddingProvider (%s), falling back to local: %s",
                provider_type,
                exc,
            )

    elif provider_type in ("gemini", "google"):
        try:
            model = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
            _default_provider = GeminiEmbeddingProvider(model_name=model)
            logger.info("Initialized GeminiEmbeddingProvider with model: %s", model)
            return _default_provider
        except Exception as exc:
            logger.warning(
                "Failed to initialize GeminiEmbeddingProvider (%s), falling back to local: %s",
                provider_type,
                exc,
            )

    # Default fallback
    _default_provider = DeterministicLocalEmbeddingProvider()
    logger.info(
        "Using DeterministicLocalEmbeddingProvider (model: %s, dim: %d)",
        _default_provider.model_name,
        _default_provider.dimension,
    )
    return _default_provider
