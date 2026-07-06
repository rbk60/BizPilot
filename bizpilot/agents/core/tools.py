"""
bizpilot/agents/core/tools.py

Core orchestration tools for BizPilot.

Architecture:
  detect_language()         — Zero-cost heuristic (no API call)
  analyze_business_request() — Zero-cost heuristic (no API call)
  compile_executive_report() — Used by ADK agent tool calling
  orchestrate()             — Single Gemini call generates entire report

Key fixes applied:
  - detect_language() and analyze_business_request() no longer call Gemini
    (they were consuming 2 of the 5 API calls per request for free-tier users)
  - orchestrate() now uses ONE Gemini call instead of 5
  - All hardcoded HR-SaaS fallback data removed
  - Fallback on quota error returns honest error, not fake report
"""

from __future__ import annotations

import json
import logging
import re
import pathlib
from typing import Any, Dict, List
from abc import ABC, abstractmethod

from bizpilot.schemas import BusinessRequest, ExecutionPlan, ExecutiveReport
from bizpilot.security import validate_api_key

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language detection — zero-cost heuristics, no API call
# ---------------------------------------------------------------------------

def _detect_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))

def _detect_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4E00-\u9FFF]", text))

def _detect_japanese(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30FF]", text))

def _detect_korean(text: str) -> bool:
    return bool(re.search(r"[\uAC00-\uD7AF]", text))

_FRENCH_MARKERS = {
    "bonjour", "salut", "merci", "vous", "nous", "entreprise",
    "aider", "stratégie", "marché", "client", "produit",
}
_DARIJA_MARKERS = {
    "wesh", "labès", "labes", "salam", "ahla", "marhba",
    "tnajm", "tfaserli", "kifek", "tounsi", "yasser", "bahi",
    "saha", "baraka", "mrigel", "chkoun", "chnoua", "wqt",
}

def detect_language(text: str) -> dict:
    """Detect language using zero-cost heuristics. Never calls Gemini."""
    if _detect_arabic(text):
        return {"language_code": "ar", "language_name": "Arabic"}
    if _detect_chinese(text):
        return {"language_code": "zh", "language_name": "Chinese"}
    if _detect_japanese(text):
        return {"language_code": "ja", "language_name": "Japanese"}
    if _detect_korean(text):
        return {"language_code": "ko", "language_name": "Korean"}

    lowered = text.lower()
    words = set(lowered.split())

    # Darija before French (Darija may use romanized Arabic)
    if words & _DARIJA_MARKERS:
        return {"language_code": "aeb", "language_name": "Tunisian Darija"}
    if words & _FRENCH_MARKERS:
        return {"language_code": "fr", "language_name": "French"}

    return {"language_code": "en", "language_name": "English"}


# ---------------------------------------------------------------------------
# Industry extraction — zero-cost
# ---------------------------------------------------------------------------

_INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "fintech": ["fintech", "payments", "financial technology", "banking", "insurance"],
    "saas": ["saas", "software as a service", "cloud platform", "subscription"],
    "healthcare": ["healthcare", "medical", "clinic", "hospital", "pharma"],
    "ecommerce": ["ecommerce", "e-commerce", "online store", "marketplace", "shopify"],
    "retail": ["retail", "shop", "boutique", "clothing", "fashion", "clothes"],
    "food": ["restaurant", "food", "cafe", "catering", "delivery"],
    "real estate": ["real estate", "property", "construction", "housing"],
    "education": ["education", "school", "training", "tutoring", "e-learning"],
    "consulting": ["consulting", "consulting firm", "advisory", "freelance"],
}

def _extract_industry(text: str) -> str:
    lowered = text.lower()
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return industry
    return "General Business"


# ---------------------------------------------------------------------------
# Business request analysis — zero-cost heuristics, no API call
# ---------------------------------------------------------------------------

_STRATEGY_KEYWORDS = {"strategy", "strategic", "roadmap", "plan", "vision", "mission", "swot"}
_INTELLIGENCE_KEYWORDS = {"research", "market", "competitor", "analysis", "insight", "trend", "industry"}
_GROWTH_KEYWORDS = {"growth", "scale", "revenue", "kpi", "marketing", "sales", "acquisition", "customer"}

def analyze_business_request(text: str) -> dict:
    """Analyze request using zero-cost heuristics. Never calls Gemini."""
    lang = detect_language(text)
    industry = _extract_industry(text)
    lowered = text.lower()

    required_agents: List[str] = []
    if any(kw in lowered for kw in _STRATEGY_KEYWORDS):
        required_agents.append("strategy_agent")
    if any(kw in lowered for kw in _INTELLIGENCE_KEYWORDS):
        required_agents.append("intelligence_agent")
    if any(kw in lowered for kw in _GROWTH_KEYWORDS):
        required_agents.append("growth_agent")
    if not required_agents:
        required_agents = ["strategy_agent", "intelligence_agent", "growth_agent"]

    return {
        "problem_statement": text[:500],
        "industry": industry,
        "language_code": lang["language_code"],
        "language_name": lang["language_name"],
        "required_agents": required_agents,
    }


# ---------------------------------------------------------------------------
# compile_executive_report — used by ADK LlmAgent tool calling
# ---------------------------------------------------------------------------

def compile_executive_report(
    problem_statement: str,
    language_code: str,
    strategy_output: str = None,
    intelligence_output: str = None,
    growth_output: str = None,
) -> dict:
    """Build a markdown executive report from pre-computed agent outputs.

    If outputs are None, runs the corresponding specialist agent.
    Returns {"report": markdown_string, "language_code": str}.
    """
    from bizpilot.agents.strategy.agent import run_strategy
    from bizpilot.agents.intelligence.agent import run_intelligence
    from bizpilot.agents.growth.agent import run_growth

    payload = {"problem_statement": problem_statement, "language_code": language_code}

    if strategy_output is None:
        try:
            rep = run_strategy(payload)
            strategy_output = _format_strategy_report(rep)
        except Exception as e:
            logger.error(f"Strategy agent failed: {e}")
            strategy_output = ""

    if intelligence_output is None:
        try:
            rep = run_intelligence(payload)
            intelligence_output = _format_intelligence_report(rep)
        except Exception as e:
            logger.error(f"Intelligence agent failed: {e}")
            intelligence_output = ""

    if growth_output is None:
        try:
            rep = run_growth(payload)
            growth_output = _format_growth_report(rep)
        except Exception as e:
            logger.error(f"Growth agent failed: {e}")
            growth_output = ""

    sections: List[str] = []
    header = "# 📊 BizPilot Executive Report"
    if language_code == "ar":
        header += " (RTL)"
    sections.append(header)
    sections.append("## Executive Summary")
    sections.append(problem_statement)

    if strategy_output:
        sections.append("## Strategic Recommendations")
        sections.append(strategy_output)
    if intelligence_output:
        sections.append("## Situation Analysis")
        sections.append(intelligence_output)
    if growth_output:
        sections.append("## Growth & Action Plan")
        sections.append(growth_output)

    sections.append("## Success Metrics")
    sections.append("- Define KPIs and measurement cadence.")

    report = "\n\n".join(sections)
    return {"report": report, "language_code": language_code}


# ---------------------------------------------------------------------------
# Report formatters
# ---------------------------------------------------------------------------

def _format_strategy_report(rep) -> str:
    from bizpilot.schemas import StrategyReport
    if not rep:
        return ""
    if isinstance(rep, str):
        return rep
    if isinstance(rep, dict):
        try:
            rep = StrategyReport.parse_obj(rep)
        except Exception:
            return str(rep)
    if isinstance(rep, StrategyReport):
        lines = []
        if rep.swot_analysis:
            lines.append("### SWOT Analysis")
            for cat, items in rep.swot_analysis.items():
                lines.append(f"- **{cat}**:")
                for item in items:
                    lines.append(f"  - {item}")
        if rep.strategic_recommendations:
            lines.append("### Strategic Recommendations")
            for rec in rep.strategic_recommendations:
                lines.append(f"- {rec}")
        if rep.business_priorities:
            lines.append("### Business Priorities")
            for p in rep.business_priorities:
                lines.append(f"- {p}")
        if rep.risks:
            lines.append("### Identified Risks")
            for r in rep.risks:
                lines.append(f"- {r}")
        if rep.roadmap:
            lines.append("### Roadmap")
            for phase in rep.roadmap:
                lines.append(f"- {phase}")
        return "\n".join(lines)
    return str(rep)


def _format_intelligence_report(rep) -> str:
    from bizpilot.schemas import IntelligenceReport
    if not rep:
        return ""
    if isinstance(rep, str):
        return rep
    if isinstance(rep, dict):
        try:
            rep = IntelligenceReport.parse_obj(rep)
        except Exception:
            return str(rep)
    if isinstance(rep, IntelligenceReport):
        return "\n\n".join([
            f"### Market Analysis\n{rep.market_analysis}",
            f"### Competitor Analysis\n{rep.competitor_analysis}",
            f"### Customer Insights\n{rep.customer_insights}",
            f"### Industry Opportunities\n{rep.industry_opportunities}",
            f"### Threat Assessment\n{rep.threat_assessment}",
        ])
    return str(rep)


def _format_growth_report(rep) -> str:
    from bizpilot.schemas import GrowthReport
    if not rep:
        return ""
    if isinstance(rep, str):
        return rep
    if isinstance(rep, dict):
        try:
            rep = GrowthReport.parse_obj(rep)
        except Exception:
            return str(rep)
    if isinstance(rep, GrowthReport):
        lines = [
            f"### Marketing Strategy\n{rep.marketing_strategy}",
            f"### Sales Optimization\n{rep.sales_optimization}",
            f"### Customer Acquisition\n{rep.customer_acquisition}",
            f"### Content Recommendations\n{rep.content_recommendations}",
        ]
        if rep.kpi_suggestions:
            lines.append("### KPI Suggestions")
            lines.extend(f"- {k}" for k in rep.kpi_suggestions)
        return "\n\n".join(lines)
    return str(rep)


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATION — Single Gemini call for the entire analysis
# ---------------------------------------------------------------------------

def _load_system_prompt() -> str:
    """Load the BizPilot consultant system prompt."""
    p = pathlib.Path(__file__).parent / "prompt.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "You are BizPilot, an expert AI Business Consultant."


def orchestrate(user_message: str) -> Dict[str, Any]:
    """
    Orchestrate a full business analysis using a SINGLE Gemini call.

    Architecture change: Instead of 5 separate Gemini calls
    (language, analysis, strategy, intelligence, growth), we now use
    ONE call that generates the complete report. This reduces quota
    consumption by 80% and eliminates quota exhaustion on free tiers.

    Returns dict with keys: summary, language_code, sections
    (compatible with ExecutiveReport schema).
    """
    validate_api_key()

    # Zero-cost pre-processing
    lang_info = detect_language(user_message)
    language_code = lang_info["language_code"]
    language_name = lang_info["language_name"]
    industry = _extract_industry(user_message)

    system_prompt = _load_system_prompt()

    # Build a rich prompt that instructs Gemini to produce the full report
    analysis_prompt = f"""The user has requested a comprehensive business analysis.

User message: \"\"\"{user_message}\"\"\"

Detected language: {language_name} (code: {language_code})
Detected industry: {industry}

Please generate a complete, personalized Executive Business Report in {language_name}.

Include these sections (only if relevant information exists):
1. Executive Summary — Summarize the business situation
2. SWOT Analysis — Strengths, Weaknesses, Opportunities, Threats
3. Strategic Recommendations — Concrete action steps
4. Market Intelligence — Market context, competitors, opportunities
5. Growth & Action Plan — Marketing, sales, customer acquisition
6. KPIs — Key metrics to track
7. 90-Day Roadmap — Prioritized milestones

CRITICAL RULES:
- Base EVERYTHING on the user's actual message. Do NOT invent facts.
- If information is missing, clearly state what additional info is needed.
- Never invent revenue, ARR, number of employees, competitors, or market size.
- Reply entirely in {language_name}.
- Format as clean Markdown with headers.
"""

    try:
        from bizpilot.utils import get_gemini_client
        from bizpilot.config.settings import settings
        from google.genai import types

        client = get_gemini_client()
        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            ),
        )
        report_text = response.text or ""
    except Exception as e:
        logger.error(f"Orchestration Gemini call failed: {e}")
        report_text = (
            "I'm sorry, I couldn't generate a response at the moment. "
            "Please try again in a few seconds."
        )

    return {
        "summary": report_text,
        "language_code": language_code,
        "sections": {"report": report_text},
    }


# ---------------------------------------------------------------------------
# MCP Server interface stub
# ---------------------------------------------------------------------------
class MCPServerInterface(ABC):
    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def stop(self) -> None: ...
    @abstractmethod
    def register_agent(self, name: str, agent: Any) -> None: ...
    @abstractmethod
    def dispatch(self, request: Any) -> Any: ...
