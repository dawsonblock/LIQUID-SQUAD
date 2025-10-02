"""Configuration settings for the LIQUID-SQUAD system.

This module uses pydantic-settings to load and validate environment variables.
All settings have sensible defaults for development and can be overridden via
environment variables or a .env file.
"""

from __future__ import annotations
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Server settings
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        
        # Authentication
        self.AUTH_TOKEN: Optional[str] = os.getenv("AUTH_TOKEN")
        
        # Rate limiting
        self.RATE_LIMIT_QPS: int = int(os.getenv("RATE_LIMIT_QPS", "5"))
        self.RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # CORS
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
        
        # Model configuration
        self.PRIMARY_MODEL_URL: str = os.getenv("PRIMARY_MODEL_URL", "")
        self.BACKUP_MODEL_URL: Optional[str] = os.getenv("BACKUP_MODEL_URL")
        self.MODEL_API_KEY: Optional[str] = os.getenv("MODEL_API_KEY")
        self.MODEL_NAME: Optional[str] = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        
        # Retrieval configuration
        self.RETRIEVAL_MODE: str = os.getenv("RETRIEVAL_MODE", "disabled")
        self.QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.ES_URL: str = os.getenv("ES_URL", "http://elasticsearch:9200")
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        # Self-loop configuration
        self.MAX_ROUNDS: int = int(os.getenv("MAX_ROUNDS", "3"))
        self.CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
        
        # Code execution
        self.CODE_EXEC: str = os.getenv("CODE_EXEC", "off")
        
    def validate(self) -> None:
        """Validate required settings."""
        if not self.PRIMARY_MODEL_URL and self.RETRIEVAL_MODE != "disabled":
            raise ValueError("PRIMARY_MODEL_URL must be set when retrieval is enabled")
        
        if self.RETRIEVAL_MODE not in ["disabled", "dense", "sparse", "dual"]:
            raise ValueError(f"Invalid RETRIEVAL_MODE: {self.RETRIEVAL_MODE}")


# Global settings instance
settings = Settings()
