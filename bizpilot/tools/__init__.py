"""
Global shared tools for ADK Agents.
Tools registered here are available to multiple agents for executing external actions.
"""

from typing import Any


def shared_system_tool(*args: Any, **kwargs: Any) -> str:
    """
    Placeholder shared tool description.
    This will be used to define custom ADK tool decorators or registration helpers.
    """
    return "Shared system tool executed."
