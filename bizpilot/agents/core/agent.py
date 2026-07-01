"""
Core Orchestrator Agent — BizPilot Root Agent.

This module defines `core_agent`, the ADK LlmAgent that serves as the
root agent of the entire BizPilot multi-agent system. It is the only agent
that directly interfaces with the user.

Architecture:
    User ↔ core_agent (orchestrator, root)
               ├── strategy_agent   (sub-agent, added later)
               ├── intelligence_agent (sub-agent, added later)
               └── growth_agent     (sub-agent, added later)

The core agent:
  - Never answers business questions directly.
  - Detects the user's language automatically.
  - Analyzes the request to decide which specialists to invoke.
  - Delegates tasks to sub-agents via ADK's native agent transfer.
  - Collects structured outputs from sub-agents.
  - Compiles and returns one unified Executive Report.
"""

import os
import pathlib
import logging

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from bizpilot.agents.core.tools import (
    detect_language,
    analyze_business_request,
    compile_executive_report,
    orchestrate,
)
from bizpilot.config.settings import settings

# ---------------------------------------------------------------------------
# Load system prompt from prompt.md
# ---------------------------------------------------------------------------

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompt.md"


def _load_prompt() -> str:
    """Reads the system prompt from the co-located prompt.md file."""
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Core Orchestrator prompt not found at: {_PROMPT_PATH}"
    )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

_CORE_TOOLS: list[FunctionTool] = [
    FunctionTool(detect_language),
    FunctionTool(analyze_business_request),
    FunctionTool(compile_executive_report),
]

# ---------------------------------------------------------------------------
# Core Orchestrator Agent Definition
# ---------------------------------------------------------------------------

core_agent = LlmAgent(
    name="core_agent",
    model=settings.DEFAULT_LLM_MODEL,
    description=(
        "The BizPilot Master Orchestrator. Accepts business situations from "
        "users, detects their language, delegates analysis to specialist agents "
        "(strategy, intelligence, growth), and synthesizes one Executive Report."
    ),
    instruction=_load_prompt(),
    tools=_CORE_TOOLS,
    # Sub-agents will be injected here once implemented:
    # sub_agents=[strategy_agent, intelligence_agent, growth_agent],

    # Enforce a chat-style interaction (user ↔ agent back-and-forth):
    # mode is left as default so that the Runner can configure it as 'chat'.

    # Store the final compiled report in session state under this key so
    # downstream services (API layer, webhooks) can retrieve it without
    # re-parsing the conversation.
    output_key="executive_report",
)
