"""
bizpilot/agents/strategy/agent.py

Business Strategy Agent.
Generates SWOT analysis, strategic recommendations, and roadmap.

Fix: All hardcoded HR-SaaS fallback data removed.
Fallback is a dynamic Gemini plain-text call based on the real user context.
If Gemini fails, returns an honest minimal StrategyReport.
"""

import logging
import os
from typing import Dict, Any

from bizpilot.schemas import StrategyReport

logger = logging.getLogger(__name__)


def _load_instructions() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "You are the Business Strategy Agent. Generate SWOT analysis and strategic "
        "recommendations ONLY based on the provided business context. Never invent data."
    )


def run_strategy(payload: dict) -> StrategyReport:
    """
    Execute the Strategy agent.
    
    Attempts:
    1. Structured JSON output via Gemini (for ADK tool use).
    2. Plain-text Gemini call using real payload (no hardcoded data).
    3. Honest minimal response — never fake data.
    """
    from bizpilot.utils import get_gemini_client
    from bizpilot.config.settings import settings
    from google.genai import types
    import json

    instruction = _load_instructions()
    problem = payload.get("problem_statement", str(payload))

    # Attempt 1: Structured JSON
    try:
        client = get_gemini_client()
        prompt = (
            f"Business context: {json.dumps(payload)}\n\n"
            f"Generate a strategic report based ONLY on the above. Do not invent any data."
        )
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=instruction,
                response_mime_type="application/json",
                response_schema=StrategyReport,
            ),
        )
        raw = response.text.strip().lstrip("```json").rstrip("```").strip()
        return StrategyReport.parse_raw(raw)
    except Exception as e:
        logger.warning(f"Strategy structured output failed ({e}); trying plain-text")

    # Attempt 2: Plain-text Gemini
    try:
        client = get_gemini_client()
        plain_prompt = (
            f"Based ONLY on this business context:\n\n\"{problem}\"\n\n"
            f"Generate a concise SWOT analysis and 3 strategic recommendations. "
            f"Do not assume any data not explicitly mentioned."
        )
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=plain_prompt,
        )
        text = response.text or ""
        return StrategyReport(
            swot_analysis={"Analysis": [text]},
            strategic_recommendations=["See analysis above"],
            business_priorities=["Review the analysis and prioritize accordingly"],
            risks=["Assess risks based on the analysis above"],
            roadmap=["Define roadmap based on strategic recommendations"],
        )
    except Exception as e:
        logger.error(f"Strategy plain-text fallback failed: {e}")

    # Attempt 3: Honest minimal — no fake data
    return StrategyReport(
        swot_analysis={
            "Note": [
                "Analysis temporarily unavailable.",
                f"Context received: {problem[:200]}",
            ]
        },
        strategic_recommendations=[
            "Please provide more business details for personalized recommendations."
        ],
        business_priorities=["More information needed"],
        risks=["Unable to assess risks without more context"],
        roadmap=["Please try again when the service is available"],
    )
