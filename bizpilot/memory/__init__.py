"""Conversation memory layer with extensible interface.

Provides an abstract ``MemoryInterface`` and a simple in‑memory implementation
``InMemoryConversationMemory``. Future back‑ends (Redis, Firestore, vector DB, …)
can subclass ``MemoryInterface`` without changing callers.
"""

from __future__ import annotations

import abc
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MemoryInterface(abc.ABC):
    """Abstract base class for conversation memory implementations.

    Subclasses must implement ``save`` and ``load`` methods. The interface enables
    future integration with persistent stores such as Redis, Firestore, or vector
    databases.
    """

    @abc.abstractmethod
    def save(self, key: str, value: Any) -> None:
        """Persist ``value`` under ``key``.

        Args:
            key: Identifier for the stored value.
            value: Arbitrary JSON‑serialisable data.
        """

    @abc.abstractmethod
    def load(self, key: str) -> Any:
        """Retrieve the value stored under ``key``.

        Raises:
            KeyError: If ``key`` is not present in the store.
        """


class InMemoryConversationMemory(MemoryInterface):
    """Simple in‑memory implementation used for development and tests.

    The data lives only for the lifetime of the Python process and is stored in a
    plain ``dict``. It satisfies the ``MemoryInterface`` contract and can be swapped
    out for a persistent implementation without changing the rest of the codebase.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        logger.debug("InMemoryConversationMemory initialized")

    def save(self, key: str, value: Any) -> None:
        self._store[key] = value
        logger.debug("Saved key '%s' to in‑memory memory", key)

    def load(self, key: str) -> Any:
        try:
            value = self._store[key]
            logger.debug("Loaded key '%s' from in‑memory memory", key)
            return value
        except KeyError as exc:
            logger.error("Key '%s' not found in memory", key)
            raise exc
