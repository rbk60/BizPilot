"""
Shared internal utilities module.
Provides logging configuration, formatting helpers, input validation, and language detection templates.
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
    """
    Placeholder for language detection.
    Can be integrated with LangDetect or custom model calls.
    """
    # Quick regex checks or simple heuristic
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
        return "ja"
    return "en"


def format_agent_response(response: Dict[str, Any]) -> str:
    """Formats raw agent outputs into structured reports."""
    # Standard format wrapper
    return f"Response received: {response}"


def validate_input_data(data: Any) -> bool:
    """Helper to check basic integrity constraints prior to passing to agents."""
    return data is not None
