"""
BizPilot Test Suite — Core Orchestrator Agent.

Tests cover:
  - Language detection accuracy across 6 languages
  - Business request routing logic
  - Industry extraction heuristics
  - Executive report compilation and structure
  - Core agent ADK object validity
"""

import pytest

from bizpilot.agents.core.tools import (
    analyze_business_request,
    compile_executive_report,
    detect_language,
    _extract_industry,
)


# ---------------------------------------------------------------------------
# Language Detection Tests
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    def test_english_default(self):
        result = detect_language("We are a SaaS startup looking to grow revenue")
        assert result["language_code"] == "en"
        assert result["language_name"] == "English"

    def test_arabic(self):
        result = detect_language("نحن شركة ناشئة في مجال التكنولوجيا المالية")
        assert result["language_code"] == "ar"
        assert result["language_name"] == "Arabic"

    def test_chinese(self):
        result = detect_language("我们是一家科技初创公司")
        assert result["language_code"] == "zh"
        assert result["language_name"] == "Chinese"

    def test_french(self):
        result = detect_language("Nous avons une startup dans le secteur de la santé pour vous aider")
        assert result["language_code"] == "fr"
        assert result["language_name"] == "French"

    def test_spanish(self):
        # Use clearly Spanish words not shared with French keyword list
        result = detect_language("tenemos una estrategia para los clientes con las empresas")
        assert result["language_code"] == "es"
        assert result["language_name"] == "Spanish"

    def test_japanese(self):
        # Pure hiragana/katakana — no kanji that could match Chinese detection
        result = detect_language("わたしたちはテクノロジーのスタートアップです")
        assert result["language_code"] == "ja"
        assert result["language_name"] == "Japanese"

    def test_korean(self):
        result = detect_language("우리는 기술 스타트업입니다")
        assert result["language_code"] == "ko"
        assert result["language_name"] == "Korean"


# ---------------------------------------------------------------------------
# Industry Extraction Tests
# ---------------------------------------------------------------------------

class TestExtractIndustry:
    def test_fintech(self):
        assert _extract_industry("our fintech payments company") == "fintech"

    def test_saas(self):
        assert _extract_industry("b2b saas platform for enterprises") == "saas"

    def test_healthcare(self):
        assert _extract_industry("medical health clinic management") == "healthcare"

    def test_ecommerce(self):
        assert _extract_industry("our online ecommerce marketplace") == "ecommerce"

    def test_general_fallback(self):
        assert _extract_industry("a small local business") == "General Business"


# ---------------------------------------------------------------------------
# Request Analysis Tests
# ---------------------------------------------------------------------------

class TestAnalyzeBusinessRequest:
    def test_strategy_keyword_routing(self):
        result = analyze_business_request(
            "We need a competitive strategy and market position analysis."
        )
        assert "strategy_agent" in result["required_agents"]

    def test_intelligence_keyword_routing(self):
        result = analyze_business_request(
            "We need deep market research and competitor analysis."
        )
        assert "intelligence_agent" in result["required_agents"]

    def test_growth_keyword_routing(self):
        result = analyze_business_request(
            "We need a growth roadmap and KPI plan to scale revenue."
        )
        assert "growth_agent" in result["required_agents"]

    def test_all_agents_when_no_keywords(self):
        result = analyze_business_request("Help us improve our business.")
        assert result["required_agents"] == ["strategy_agent", "intelligence_agent", "growth_agent"]

    def test_language_detected_in_result(self):
        result = analyze_business_request("Our fintech startup needs a growth plan.")
        assert result["language_code"] == "en"
        assert result["language_name"] == "English"

    def test_industry_detected_in_result(self):
        result = analyze_business_request("Our fintech startup needs a growth plan.")
        assert result["industry"] == "fintech"

    def test_problem_statement_truncated(self):
        long_request = "A" * 600
        result = analyze_business_request(long_request)
        assert len(result["problem_statement"]) <= 500


# ---------------------------------------------------------------------------
# Report Compilation Tests
# ---------------------------------------------------------------------------

class TestCompileExecutiveReport:
    def test_report_contains_required_sections(self):
        result = compile_executive_report(
            problem_statement="Fintech growth challenge",
            language_code="en",
            strategy_output="Expand into B2B partnerships.",
            intelligence_output="Market growing at 18% CAGR.",
            growth_output="Target enterprise segment in Q3.",
        )
        report = result["report"]
        assert "# 📊 BizPilot" in report
        assert "Executive Summary" in report
        assert "Strategic Recommendations" in report
        assert "Situation Analysis" in report
        assert "Growth & Action Plan" in report
        assert "Success Metrics" in report

    def test_report_preserves_language_code(self):
        result = compile_executive_report(
            problem_statement="Test",
            language_code="fr",
            strategy_output="Stratégie A",
            intelligence_output="Marché B",
            growth_output="Plan C",
        )
        assert result["language_code"] == "fr"

    def test_rtl_header_added_for_arabic(self):
        result = compile_executive_report(
            problem_statement="تحدي النمو",
            language_code="ar",
            strategy_output="استراتيجية",
            intelligence_output="السوق",
            growth_output="خطة النمو",
        )
        assert "RTL" in result["report"]

    def test_missing_agent_outputs_handled_gracefully(self):
        result = compile_executive_report(
            problem_statement="Simple question",
            language_code="en",
            strategy_output="",
            intelligence_output="",
            growth_output="",
        )
        assert "not available for this request" in result["report"]


# ---------------------------------------------------------------------------
# Core Agent ADK Object Tests
# ---------------------------------------------------------------------------

class TestCoreAgentObject:
    def test_core_agent_is_llm_agent(self):
        from google.adk.agents import LlmAgent
        from bizpilot.agents.core.agent import core_agent
        assert isinstance(core_agent, LlmAgent)

    def test_core_agent_name(self):
        from bizpilot.agents.core.agent import core_agent
        assert core_agent.name == "core_agent"

    def test_core_agent_output_key(self):
        from bizpilot.agents.core.agent import core_agent
        assert core_agent.output_key == "executive_report"

    def test_core_agent_has_three_tools(self):
        from bizpilot.agents.core.agent import core_agent
        assert len(core_agent.tools) == 3

    def test_core_agent_tool_names(self):
        from bizpilot.agents.core.agent import core_agent
        tool_names = [t.name for t in core_agent.tools]
        assert "detect_language" in tool_names
        assert "analyze_business_request" in tool_names
        assert "compile_executive_report" in tool_names

    def test_core_agent_instruction_loaded(self):
        from bizpilot.agents.core.agent import core_agent
        assert len(core_agent.instruction) > 100
        assert "CORE" in core_agent.instruction
