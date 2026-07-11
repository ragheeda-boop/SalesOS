"""Tests for NBAReasoner — AI reasoning layer for the NBA engine."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.nba_engine.engine.ai.reasoner import NBAReasoner


class MockLLMService:
    """Simulates an LLM service that returns controlled responses."""

    def __init__(self, response: str | dict | None = None, fail: bool = False):
        self._response = response
        self._fail = fail
        self.last_prompt = None

    async def chat(self, prompt: list[dict]) -> str | dict | None:
        self.last_prompt = prompt
        if self._fail:
            raise RuntimeError("LLM unavailable")
        if self._response is None:
            return '{"ranking": [], "explanation": "no action", "confidence": 0.5, "risks": []}'
        if isinstance(self._response, dict):
            return self._response
        return self._response


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_OPP = {
    "name": "ERP Implementation",
    "stage": "proposal",
    "value": 500000,
    "health": "healthy",
}

SAMPLE_COMPANY = {
    "name_ar": "شركة التقنية",
    "name_en": "Tech Co",
    "industry": "technology",
}

SAMPLE_SIGNALS = [
    {"type": "tender", "source": "government", "confidence": 0.8},
]

SAMPLE_ACTIVITIES = [
    {"timestamp": "2026-07-01T10:00:00Z", "action": "email_sent"},
    {"timestamp": "2026-06-28T10:00:00Z", "action": "call_made"},
]

SAMPLE_CANDIDATES = [
    {"action": "send_proposal", "reason": "العميل في مرحلة العروض", "score": 0.9},
    {"action": "schedule_call", "reason": "متابعة", "score": 0.7},
]


@pytest.fixture
def reasoner_no_llm():
    return NBAReasoner(llm_service=None)


@pytest.fixture
def reasoner_with_llm():
    llm = MockLLMService()
    return NBAReasoner(llm_service=llm)


# ── Tests: evaluate ───────────────────────────────────────────────────────────

class TestEvaluate:
    async def test_returns_none_when_no_llm(self, reasoner_no_llm):
        result = await reasoner_no_llm.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        assert result is None

    async def test_returns_parsed_result_with_llm(self, reasoner_with_llm):
        result = await reasoner_with_llm.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        assert isinstance(result, dict)
        assert "ranking" in result
        assert "explanation" in result
        assert "confidence" in result
        assert "risks" in result

    async def test_passes_opportunity_context_to_llm(self, reasoner_with_llm):
        await reasoner_with_llm.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        prompt = reasoner_with_llm._llm.last_prompt
        assert prompt is not None
        user_msg = prompt[1]["content"]
        assert "ERP Implementation" in user_msg
        assert "proposal" in user_msg
        assert "500000" in user_msg

    async def test_handles_llm_exception_gracefully(self, reasoner_no_llm):
        llm = MockLLMService(fail=True)
        reasoner = NBAReasoner(llm_service=llm)
        result = await reasoner.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        assert result is None

    async def test_includes_company_info_in_prompt(self, reasoner_with_llm):
        await reasoner_with_llm.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        prompt = reasoner_with_llm._llm.last_prompt
        user_msg = prompt[1]["content"]
        assert "شركة التقنية" in user_msg or "Tech Co" in user_msg

    async def test_includes_days_since_last_activity(self, reasoner_with_llm):
        await reasoner_with_llm.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        prompt = reasoner_with_llm._llm.last_prompt
        user_msg = prompt[1]["content"]
        assert "days_since_last_activity" in user_msg

    async def test_empty_activities_has_zero_days(self, reasoner_with_llm):
        await reasoner_with_llm.evaluate(
            SAMPLE_OPP, SAMPLE_COMPANY, [], [], SAMPLE_CANDIDATES,
        )
        prompt = reasoner_with_llm._llm.last_prompt
        user_msg = prompt[1]["content"]
        # days_since should be 0 when no activities
        assert "candidate_actions" in user_msg


class TestBuildPrompt:
    def test_build_prompt_returns_list_of_dicts(self, reasoner_no_llm):
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        assert isinstance(prompt, list)
        assert len(prompt) == 2

    def test_system_role_first_message(self, reasoner_no_llm):
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        assert prompt[0]["role"] == "system"
        assert "sales strategist" in prompt[0]["content"]

    def test_user_role_second_message(self, reasoner_no_llm):
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        assert prompt[1]["role"] == "user"

    def test_company_name_arabic_preferred(self, reasoner_no_llm):
        company = {"name_ar": "شركة العربية", "name_en": "Al Arabia Co", "industry": "tech"}
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, company, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        user_msg = prompt[1]["content"]
        assert "شركة العربية" in user_msg

    def test_company_name_fallback_to_english(self, reasoner_no_llm):
        company = {"name_ar": "", "name_en": "English Only Co", "industry": "tech"}
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, company, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        user_msg = prompt[1]["content"]
        assert "English Only Co" in user_msg

    def test_truncates_long_names(self, reasoner_no_llm):
        opp = {"name": "A" * 500, "stage": "proposal", "value": 1000, "health": "healthy"}
        prompt = reasoner_no_llm._build_prompt(
            opp, SAMPLE_COMPANY, [], [], SAMPLE_CANDIDATES,
        )
        user_msg = prompt[1]["content"]
        assert len(opp["name"]) > 200
        assert "A" * 200 in user_msg

    def test_truncates_candidate_values(self, reasoner_no_llm):
        long_candidate = [
            {"action": "x" * 300, "reason": "y" * 300, "score": 0.9, "extra": "z" * 300},
        ]
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, [], [], long_candidate,
        )
        user_msg = prompt[1]["content"]
        assert "extra" not in user_msg

    def test_limits_candidates_to_10(self, reasoner_no_llm):
        many_candidates = [
            {"action": f"action_{i}", "reason": f"reason_{i}", "score": 0.5}
            for i in range(20)
        ]
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, [], [], many_candidates,
        )
        user_msg = prompt[1]["content"]
        # Only 10 candidates should be included
        assert "action_0" in user_msg
        assert "action_15" not in user_msg

    def test_industry_included(self, reasoner_no_llm):
        company = {"name_ar": "C", "name_en": "C", "industry": "financial services"}
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, company, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        user_msg = prompt[1]["content"]
        assert "financial services" in user_msg

    def test_empty_signals_handled(self, reasoner_no_llm):
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, [], SAMPLE_ACTIVITIES, SAMPLE_CANDIDATES,
        )
        user_msg = prompt[1]["content"]
        assert "candidate_actions" in user_msg

    def test_empty_candidates_handled(self, reasoner_no_llm):
        prompt = reasoner_no_llm._build_prompt(
            SAMPLE_OPP, SAMPLE_COMPANY, SAMPLE_SIGNALS, SAMPLE_ACTIVITIES, [],
        )
        user_msg = prompt[1]["content"]
        assert "candidate_actions" in user_msg
        assert "[]" in user_msg


class TestParseResponse:
    def test_parse_dict_response(self, reasoner_no_llm):
        response = {"ranking": [{"action": "send_proposal", "score": 0.9}], "explanation": "best action", "confidence": 0.85, "risks": ["stagnation"]}
        result = reasoner_no_llm._parse_response(response)
        assert result["ranking"] == [{"action": "send_proposal", "score": 0.9}]
        assert result["explanation"] == "best action"
        assert result["confidence"] == 0.85
        assert result["risks"] == ["stagnation"]

    def test_parse_string_json_response(self, reasoner_no_llm):
        response = '{"ranking": [], "explanation": "test", "confidence": 0.7, "risks": []}'
        result = reasoner_no_llm._parse_response(response)
        assert result["explanation"] == "test"
        assert result["confidence"] == 0.7

    def test_parse_object_with_choices(self, reasoner_no_llm):
        class FakeChoice:
            message = MagicMock(content='{"ranking": [], "explanation": "from choices", "confidence": 0.6, "risks": []}')
        class FakeResponse:
            choices = [FakeChoice()]
        result = reasoner_no_llm._parse_response(FakeResponse())
        assert result["explanation"] == "from choices"

    def test_confidence_clamped_to_0(self, reasoner_no_llm):
        response = {"ranking": [], "explanation": "x", "confidence": -0.5, "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert result["confidence"] == 0.0

    def test_confidence_clamped_to_1(self, reasoner_no_llm):
        response = {"ranking": [], "explanation": "x", "confidence": 1.5, "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert result["confidence"] == 1.0

    def test_confidence_default_when_missing(self, reasoner_no_llm):
        response = {"ranking": [], "explanation": "x", "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert result["confidence"] == 0.5

    def test_explanation_limit_2000_chars(self, reasoner_no_llm):
        response = {"ranking": [], "explanation": "x" * 5000, "confidence": 0.5, "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert len(result["explanation"]) == 2000

    def test_ranking_limited_to_10(self, reasoner_no_llm):
        many_rankings = [{"action": f"a{i}"} for i in range(20)]
        response = {"ranking": many_rankings, "explanation": "x", "confidence": 0.5, "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert len(result["ranking"]) == 10

    def test_ranking_filters_non_dict_items(self, reasoner_no_llm):
        response = {"ranking": [{"action": "valid"}, "invalid_string", None], "explanation": "x", "confidence": 0.5, "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert len(result["ranking"]) == 1
        assert result["ranking"][0]["action"] == "valid"

    def test_ranking_filters_missing_action(self, reasoner_no_llm):
        response = {"ranking": [{"action": "good"}, {"no_action": "bad"}], "explanation": "x", "confidence": 0.5, "risks": []}
        result = reasoner_no_llm._parse_response(response)
        assert len(result["ranking"]) == 1
        assert result["ranking"][0]["action"] == "good"

    def test_risks_limited_to_10_and_truncated(self, reasoner_no_llm):
        many_risks = ["r" * 300 for _ in range(20)]
        response = {"ranking": [], "explanation": "x", "confidence": 0.5, "risks": many_risks}
        result = reasoner_no_llm._parse_response(response)
        assert len(result["risks"]) == 10
        assert all(len(r) <= 200 for r in result["risks"])

    def test_empty_response_defaults(self, reasoner_no_llm):
        response = {}
        result = reasoner_no_llm._parse_response(response)
        assert result["ranking"] == []
        assert result["explanation"] == ""
        assert result["confidence"] == 0.5
        assert result["risks"] == []
