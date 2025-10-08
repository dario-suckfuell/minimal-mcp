"""Text embedding functionality with provider support."""

from typing import List
import logging
from .config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Custom exception for embedding-related errors."""
    pass


class Embedder:
    """Base class for text embedders."""
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        raise NotImplementedError


class OpenAIEmbedder(Embedder):
    """OpenAI-based text embedder."""
    
    def __init__(self, api_key: str):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise EmbeddingError("OpenAI package not installed. Install with: pip install openai")
    
    def embed_text(self, text: str) -> List[float]:
        """Embed text using the configured OpenAI model."""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=settings.EMBEDDING_MODEL,
                dimensions=settings.EMBEDDING_DIMENSIONS
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise EmbeddingError(f"Failed to embed text: {e}")


def get_embedder() -> Embedder:
    """Get the configured embedder instance."""
    if not settings.ENABLE_EMBEDDING:
        raise EmbeddingError("Embedding is disabled. Set ENABLE_EMBEDDING=true to enable.")
    
    if settings.EMBEDDING_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise EmbeddingError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        return OpenAIEmbedder(settings.OPENAI_API_KEY)
    else:
        raise EmbeddingError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")


def embed_text(text: str) -> List[float]:
    """Embed text using the configured embedder."""
    embedder = get_embedder()
    return embedder.embed_text(text)
