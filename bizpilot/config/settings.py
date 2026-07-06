"""
Application Configuration and Environment Settings management.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini / Google API Keys
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Google Cloud / Vertex AI settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "us-central1"

    # Application Settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Default model selection
    DEFAULT_LLM_MODEL: str = "gemini-2.5-flash-lite"


settings = Settings()