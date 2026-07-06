"""
bizpilot/agents/intelligence/agent.py

Market Intelligence Agent.
Performs market analysis, competitor research, and opportunity identification.

Fix: All hardcoded HR-SaaS fallback data removed.
"""

import logging
import os
from typing import Dict, Any

from bizpilot.schemas import IntelligenceReport

logger = logging.getLogger(__name__)


def _load_instructions() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "You are the Market Intelligence Agent. Provide market analysis ONLY based on "
        "the provided context. Never invent competitors, market sizes, or industry data."
    )


def run_intelligence(payload: dict) -> IntelligenceReport:
    """
    Execute the Intelligence agent.
    Falls back gracefully without returning fake HR-SaaS data.
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
            f"Perform market intelligence analysis based ONLY on the above."
        )
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=instruction,
                response_mime_type="application/json",
                response_schema=IntelligenceReport,
            ),
        )
        raw = response.text.strip().lstrip("```json").rstrip("```").strip()
        return IntelligenceReport.parse_raw(raw)
    except Exception as e:
        logger.warning(f"Intelligence structured output failed ({e}); trying plain-text")

    # Attempt 2: Plain-text Gemini
    try:
        client = get_gemini_client()
        plain_prompt = (
            f"Based ONLY on this context:\n\n\"{problem}\"\n\n"
            f"Provide brief market analysis, customer insights, and key opportunities. "
            f"Do not invent any data not mentioned."
        )
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=plain_prompt,
        )
        text = response.text or "Insufficient context for market analysis."
        return IntelligenceReport(
            market_analysis=text,
            competitor_analysis="Provide competitor information for a detailed analysis.",
            customer_insights="Describe your target customers for personalized insights.",
            industry_opportunities="More context needed to identify specific opportunities.",
            threat_assessment="Provide more business details for threat assessment.",
        )
    except Exception as e:
        logger.error(f"Intelligence plain-text fallback failed: {e}")

    # Attempt 3: Honest minimal
    return IntelligenceReport(
        market_analysis=f"Analysis temporarily unavailable. Context: {problem[:200]}",
        competitor_analysis="Please provide competitor information for analysis.",
        customer_insights="Please describe your target customers.",
        industry_opportunities="More business context needed.",
        threat_assessment="Please provide more details for threat assessment.",
    )
