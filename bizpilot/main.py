"""
BizPilot Application Entry Point.

Provides two execution modes:
  1. `adk web bizpilot` — Launch the ADK developer web UI (recommended for dev).
  2. `python -m bizpilot.main` — Programmatic runner for scripting and testing.

ADK discovery: The ADK CLI discovers the root agent via the module path
`bizpilot.agents.core.agent:core_agent`. See README for setup instructions.
"""

import asyncio
import sys

from bizpilot.config.settings import settings
from bizpilot.utils import setup_logger

logger = setup_logger(__name__)


async def _run_programmatic(user_message: str) -> None:
    """Runs the core agent programmatically for a single user message.

    This is useful for smoke-testing the agent without launching the full
    ADK web interface.

    Args:
        user_message: The business situation text submitted by the user.
    """
    # Import here to avoid loading ADK at module level when not needed.
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from bizpilot.agents.core.agent import core_agent

    logger.info("Initializing BizPilot session service...")
    session_service = InMemorySessionService()

    APP_NAME = "bizpilot"
    USER_ID = "local_user"
    SESSION_ID = "session_001"

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        app_name=APP_NAME,
        agent=core_agent,
        session_service=session_service,
    )

    logger.info(f"Sending request to Core Orchestrator: {user_message[:80]}...")
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )

    print("\n" + "=" * 60)
    print("BizPilot — Executive Report")
    print("=" * 60 + "\n")

    final_response = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
                print(final_response)
            break

    print("\n" + "=" * 60)
    logger.info("BizPilot run complete.")


def main() -> int:
    """Main entry point for programmatic execution."""
    logger.info(f"BizPilot starting | env={settings.APP_ENV} | model={settings.DEFAULT_LLM_MODEL}")

    # Default demo request — override via CLI arg
    demo_request = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "We are a SaaS startup in the HR tech space with 50 employees. "
            "We have strong product-market fit but are struggling to scale "
            "our enterprise sales motion. Revenue is $2M ARR and growing at "
            "30% YoY. What should we focus on to reach $10M ARR in 18 months?"
        )
    )

    asyncio.run(_run_programmatic(demo_request))
    return 0


if __name__ == "__main__":
    sys.exit(main())
