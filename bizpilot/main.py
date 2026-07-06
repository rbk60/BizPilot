"""
BizPilot Application Entry Point.

Provides two execution modes:
  1. `adk web bizpilot` — Launch the ADK developer web UI.
  2. `python -m bizpilot.main` — Programmatic runner.
"""

import httpx
import urllib3
import sys

# Configure stdout to use UTF-8 to prevent UnicodeEncodeError with emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global monkey-patch to bypass local SSL issues
_orig_init = httpx.Client.__init__
def _patched_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_init

_orig_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _orig_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init

import asyncio
import sys
import os

from dotenv import load_dotenv

# Charge le fichier .env
load_dotenv()

# Rend les clés visibles pour ADK / google-genai
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

print("GOOGLE_API_KEY =", os.getenv("GOOGLE_API_KEY"))
print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))

from bizpilot.config.settings import settings
from bizpilot.utils import setup_logger

logger = setup_logger(__name__)


async def _run_programmatic(user_message: str) -> None:
    """Runs the core agent programmatically."""

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

    try:
        report_printed = False
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(event.content.parts[0].text)
                    report_printed = True
                break
        if not report_printed:
            raise RuntimeError("ADK Runner returned no response.")
    except Exception as e:
        logger.warning(
            f"ADK Runner failed ({e}); invoking direct programmatic fallback orchestration..."
        )
        try:
            from bizpilot.agents.core.tools import (
                detect_language,
                analyze_business_request,
                compile_executive_report,
            )
            # Step 1: Detect language
            lang_result = detect_language(user_message)
            # Step 2: Analyze request
            analysis_result = analyze_business_request(user_message)
            # Step 3: Compile executive report (passing None triggers subagent runs or fallbacks)
            report_result = compile_executive_report(
                problem_statement=analysis_result.get("problem_statement", user_message),
                language_code=lang_result.get("language_code", "en"),
                strategy_output=None,
                intelligence_output=None,
                growth_output=None,
            )
            print(report_result.get("report", "Failed to generate report."))
            logger.error(f"Fallback orchestration also failed: {fallback_err}")
            print(
                "I'm sorry, I was unable to generate a response at this time.\n"
                "This is likely due to a temporary API issue. Please try again in a moment."
            )

    print("\n" + "=" * 60)
    logger.info("BizPilot run complete.")


def main() -> int:
    logger.info(
        f"BizPilot starting | env={settings.APP_ENV} | model={settings.DEFAULT_LLM_MODEL}"
    )

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