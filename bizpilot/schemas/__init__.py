"""Pydantic schemas for BizPilot inputs and outputs.

These models are used for all inter‑agent communication and for the final
ExecutiveReport returned to the user.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class BusinessRequest(BaseModel):
    """User's business request after language detection and industry extraction."""

    problem_statement: str = Field(..., description="Full user request text")
    industry: str = Field(..., description="Detected industry domain")
    language_code: str = Field(..., description="BCP‑47 language code, e.g. 'en'")
    language_name: str = Field(..., description="Human readable language name")

    @validator("problem_statement", "industry", "language_code", "language_name")
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non‑empty string")
        return v.strip()


class ExecutionPlan(BaseModel):
    """Plan indicating which specialist agents should be invoked."""

    required_agents: List[str] = Field(..., description="Names of agents to run")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional free‑form parameters passed to sub‑agents",
    )

    @validator("required_agents", each_item=True)
    def agent_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("agent name cannot be empty")
        return v.strip()


class StrategyReport(BaseModel):
    """Output produced by the Strategy specialist agent."""

    swot_analysis: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="SWOT categories mapped to list of bullet points",
    )
    strategic_recommendations: List[str] = Field(
        default_factory=list,
        description="High‑level strategic actions",
    )
    business_priorities: List[str] = Field(default_factory=list, description="Key priorities")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    roadmap: List[str] = Field(default_factory=list, description="Planned milestones or phases")

    @root_validator(skip_on_failure=True)
    def at_least_one_section(cls, values):
        if not any(values.get(k) for k in [
            "swot_analysis",
            "strategic_recommendations",
            "business_priorities",
            "risks",
            "roadmap",
        ]):
            raise ValueError("StrategyReport must contain at least one populated field")
        return values


class IntelligenceReport(BaseModel):
    """Output produced by the Intelligence specialist agent."""

    market_analysis: str = Field(..., description="Narrative market overview")
    competitor_analysis: str = Field(..., description="Key competitors and positioning")
    customer_insights: str = Field(..., description="Insights about target customers")
    industry_opportunities: str = Field(..., description="Potential opportunities in the sector")
    threat_assessment: str = Field(..., description="Potential threats and mitigations")

    @validator(
        "market_analysis",
        "competitor_analysis",
        "customer_insights",
        "industry_opportunities",
        "threat_assessment",
    )
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field cannot be empty")
        return v.strip()


class GrowthReport(BaseModel):
    """Output produced by the Growth specialist agent."""

    marketing_strategy: str = Field(..., description="Proposed marketing approach")
    sales_optimization: str = Field(..., description="Ways to improve sales processes")
    customer_acquisition: str = Field(..., description="Acquisition channels and tactics")
    content_recommendations: str = Field(..., description="Content ideas to support growth")
    kpi_suggestions: List[str] = Field(default_factory=list, description="KPIs to track progress")

    @validator(
        "marketing_strategy",
        "sales_optimization",
        "customer_acquisition",
        "content_recommendations",
    )
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field cannot be empty")
        return v.strip()


class ExecutiveReport(BaseModel):
    """Final merged report produced by the Core orchestrator.

    ``sections`` keys correspond to agent names (e.g. ``strategy``, ``intelligence``, ``growth``)
    and contain rendered Markdown strings.
    """

    summary: str = Field(..., description="Executive summary of the overall analysis")
    language_code: str = Field(..., description="BCP‑47 language code for the report")
    sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of section name to rendered Markdown content",
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional additional information")

    @validator("summary", "language_code")
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field cannot be empty")
        return v.strip()

    @validator("sections")
    def sections_not_empty(cls, v: Dict[str, str]) -> Dict[str, str]:
        if not v:
            raise ValueError("sections must contain at least one entry")
        return v
