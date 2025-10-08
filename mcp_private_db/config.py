"""Configuration management for the MCP Private Database server."""

import os
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # Pinecone configuration
    PINECONE_API_KEY: str = Field(..., description="Pinecone API key")
    PINECONE_INDEX: str = Field(..., description="Pinecone index name")
    PINECONE_HOST: str = Field(..., description="Pinecone host/environment")
    NAMESPACE: Optional[str] = Field(None, description="Optional Pinecone namespace")
    
    # Search configuration
    DEFAULT_TOP_K: int = Field(8, ge=1, le=25, description="Default number of results to return")
    MAX_CONTENT_CHARS: int = Field(50000, ge=1000, description="Maximum content length before truncation")
    
    # Embedding configuration
    ENABLE_EMBEDDING: bool = Field(True, description="Whether to enable text embedding")
    EMBEDDING_PROVIDER: str = Field("openai", description="Embedding provider to use")
    EMBEDDING_MODEL: str = Field("text-embedding-3-large", description="Embedding model to use")
    EMBEDDING_DIMENSIONS: int = Field(3072, description="Embedding dimensions")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key for embeddings")
    
    # Metadata configuration
    METADATA_TEXT_KEYS: str = Field("text,chunk,content", description="Comma-separated keys to probe for text content")
    
    # Server configuration
    HOST: str = Field("0.0.0.0", description="Server host")
    PORT: int = Field(8000, description="Server port")
    
    # Authentication configuration
    SECRET_TOKEN: Optional[str] = Field(None, description="Bearer token for API authentication")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    @property
    def metadata_text_keys_list(self) -> list[str]:
        """Get metadata text keys as a list."""
        return [key.strip() for key in self.METADATA_TEXT_KEYS.split(",") if key.strip()]


# Global settings instance
def load_settings() -> Settings:
    """Load settings from environment variables."""
    # Load from .env file if it exists
    from dotenv import load_dotenv
    load_dotenv()  # Load from .env file
    
    return Settings(
        PINECONE_API_KEY=os.getenv("PINECONE_API_KEY", ""),
        PINECONE_INDEX=os.getenv("PINECONE_INDEX", ""),
        PINECONE_HOST=os.getenv("PINECONE_HOST", ""),
        NAMESPACE=os.getenv("NAMESPACE"),
        DEFAULT_TOP_K=int(os.getenv("DEFAULT_TOP_K", "8")),
        MAX_CONTENT_CHARS=int(os.getenv("MAX_CONTENT_CHARS", "50000")),
        ENABLE_EMBEDDING=os.getenv("ENABLE_EMBEDDING", "true").lower() == "true",
        EMBEDDING_PROVIDER=os.getenv("EMBEDDING_PROVIDER", "openai"),
        EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
        EMBEDDING_DIMENSIONS=int(os.getenv("EMBEDDING_DIMENSIONS", "3072")),
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        METADATA_TEXT_KEYS=os.getenv("METADATA_TEXT_KEYS", "text,chunk,content"),
        HOST=os.getenv("HOST", "0.0.0.0"),
        PORT=int(os.getenv("PORT", "8000")),
        SECRET_TOKEN=os.getenv("SECRET_TOKEN")
    )

settings = load_settings()
