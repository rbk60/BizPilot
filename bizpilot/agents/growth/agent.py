"""
bizpilot/agents/growth/agent.py

Growth Strategist Agent.
Creates marketing strategies, sales optimization, and KPI recommendations.

Fix: All hardcoded HR-SaaS fallback data removed.
"""

import logging
import os
from typing import Dict, Any

from bizpilot.schemas import GrowthReport

logger = logging.getLogger(__name__)


def _load_instructions() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "You are the Growth Strategist Agent. Generate growth recommendations "
        "ONLY based on the provided context. Never invent marketing data or revenue figures."
    )


def run_growth(payload: dict) -> GrowthReport:
    """
    Execute the Growth agent.
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
            f"Formulate a growth action plan based ONLY on the above."
        )
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=instruction,
                response_mime_type="application/json",
                response_schema=GrowthReport,
            ),
        )
        raw = response.text.strip().lstrip("```json").rstrip("```").strip()
        return GrowthReport.parse_raw(raw)
    except Exception as e:
        logger.warning(f"Growth structured output failed ({e}); trying plain-text")

    # Attempt 2: Plain-text Gemini
    try:
        client = get_gemini_client()
        plain_prompt = (
            f"Based ONLY on this context:\n\n\"{problem}\"\n\n"
            f"Suggest a marketing strategy, sales approach, and 3-5 relevant KPIs. "
            f"Do not invent any data not mentioned."
        )
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=plain_prompt,
        )
        text = response.text or "Insufficient context for growth planning."
        return GrowthReport(
            marketing_strategy=text,
            sales_optimization="Provide your current sales process for tailored recommendations.",
            customer_acquisition="Describe your target customers for acquisition strategies.",
            content_recommendations="Share your content goals for personalized recommendations.",
            kpi_suggestions=[
                "Define your primary growth metric",
                "Track customer acquisition cost (CAC)",
                "Monitor customer lifetime value (LTV)",
            ],
        )
    except Exception as e:
        logger.error(f"Growth plain-text fallback failed: {e}")

    # Attempt 3: Honest minimal
    return GrowthReport(
        marketing_strategy=f"Growth planning temporarily unavailable. Context: {problem[:200]}",
        sales_optimization="Please provide more details about your sales process.",
        customer_acquisition="Describe your target customers for acquisition strategies.",
        content_recommendations="Share your content goals for personalized recommendations.",
        kpi_suggestions=["More business context needed to suggest relevant KPIs"],
    )
