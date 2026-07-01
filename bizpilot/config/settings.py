"""
Application Configuration and Environment Settings management.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings configuration class.
    Loads and validates environment variables from .env file or system environment.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Configuration
    GEMINI_API_KEY: Optional[str] = None

    # Google Cloud / Vertex AI settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: Optional[str] = "us-central1"

    # Application Settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Default model selection for ADK Agents
    DEFAULT_LLM_MODEL: str = "gemini-2.5-flash"


# Instantiate a singleton settings object
settings = Settings()
