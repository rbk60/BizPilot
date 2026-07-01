"""Security utilities for BizPilot.

- API key validation
- Input validation decorator using Pydantic schemas
- Structured JSON logging helper
"""

import logging
from functools import wraps
from typing import Any, Callable, Type

from bizpilot.config.settings import settings
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def validate_api_key() -> None:
    """Ensures the Gemini API key is set.

    Raises:
        RuntimeError: If ``settings.GEMINI_API_KEY`` is missing or empty.
    """
    if not getattr(settings, "GEMINI_API_KEY", None):
        raise RuntimeError("GEMINI_API_KEY is not configured. Set it in the .env file.")


def input_validator(schema: Type[BaseModel]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that validates the first positional argument against a Pydantic schema.

    The wrapped function must accept the payload as its first argument. If validation
    fails a ``ValueError`` is raised and the error is logged.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(payload: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                validated = schema.parse_obj(payload)
            except ValidationError as exc:
                logger.error(
                    "Input validation failed for %s: %s",
                    func.__name__,
                    exc.errors(),
                )
                raise ValueError(f"Invalid input for {func.__name__}: {exc}") from exc
            return func(validated, *args, **kwargs)

        return wrapper

    return decorator


def get_structured_logger(request_id: str) -> logging.LoggerAdapter:
    """Returns a LoggerAdapter that adds a ``request_id`` field to all log records.
    """
    return logging.LoggerAdapter(logger, {"request_id": request_id})
