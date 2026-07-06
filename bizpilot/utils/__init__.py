"""
bizpilot/utils/__init__.py

Shared utilities: logging, Gemini client factory, helpers.

Fix: get_gemini_client() is no longer a singleton.
A singleton caused stale connections after network errors.
Each call now creates a fresh client (lightweight object).
"""

import logging
import re
from typing import Any, Dict


def setup_logger(name: str) -> logging.Logger:
    """Configures and returns a standardized console logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def detect_language(text: str) -> str:
    """Simple language detection returning a BCP-47 code. No API call."""
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
        return "ja"
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    return "en"


def format_agent_response(response: Dict[str, Any]) -> str:
    """Formats raw agent outputs into structured reports."""
    return f"Response received: {response}"


def validate_input_data(data: Any) -> bool:
    """Check basic integrity constraints prior to passing to agents."""
    return data is not None


def get_gemini_client():
    """
    Creates a google.genai.Client with SSL verification disabled.
    
    Note: Creates a fresh client on each call (not a singleton).
    This avoids stale connection issues after network errors or rate limit
    backoffs. The genai.Client object is lightweight — no connection is
    established until a model call is made.
    """
    from google import genai
    from bizpilot.config.settings import settings

    api_key = settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY
    return genai.Client(api_key=api_key)
