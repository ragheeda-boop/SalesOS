"""Tests for Copilot domain — Phase 11.

Covers:
- B-1: search_companies tool (timeout, structured results)
- B-2: Feedback service (submit, stats, per-tool breakdown)
- B-3: Tool telemetry (log, stats, percentiles, volume, breakdown)
- B-4: Arabic copilot (detection, RTL, prompts, Saudi context)
"""

from unittest.mock import AsyncMock

import pytest

from domains.copilot.arabic import ArabicCopilotEngine
from domains.copilot.feedback_service import CopilotFeedbackService
from domains.copilot.models import (
    CopilotFeedback,
    CopilotFeedbackStats,
    FeedbackRating,
    ToolCallRecord,
    ToolTelemetryStats,
)
from domains.copilot.schemas import (
    ArabicDetectRequest,
    CopilotFeedbackSubmit,
    SearchCompaniesRequest,
)
from domains.copilot.telemetry_service import ToolTelemetryService, _percentile
from domains.copilot.tools import SearchCompaniesTool, ToolResult
from domains.search.contracts.models import SearchResult

# ═══════════════════════════════════════════════════════════════
# B-1: Search Companies Tool
# ═══════════════════════════════════════════════════════════════


class TestSearchCompaniesTool:
    """Tests for the search_companies copilot tool."""

    def test_tool_schema(self):
        tool = SearchCompaniesTool()
        schema = tool.get_schema()
        assert schema["name"] == "search_companies"
        assert "query" in schema["parameters"]["properties"]
        assert "query" in schema["parameters"]["required"]

    @pytest.mark.asyncio
    async def test_execute_empty_query_returns_error(self):
        tool = SearchCompaniesTool()
        result = await tool.execute({"query": ""}, {"tenant_id": "t1"})
        assert result.success is False
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_no_repo_returns_error(self):
        tool = SearchCompaniesTool(search_repo=None)
        result = await tool.execute({"query": "ACME"}, {"tenant_id": "t1"})
        assert result.success is False
        assert "not configured" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_structured_results(self):
        mock_repo = AsyncMock()
        search_result = SearchResult(
            items=[
                {
                    "id": "c1", "name_ar": "أكمة",
                    "name_en": "ACME Corp", "cr_number": "1010123456",
                    "city": "Riyadh", "industry": "Tech", "rank": 0.95,
                },
                {
                    "id": "c2", "name_ar": "شركةテスト",
                    "name_en": "TestCo", "cr_number": "1010654321",
                    "city": "Jeddah", "industry": "Finance", "rank": 0.82,
                },
            ],
            total=2,
            strategy="postgres",
            duration_ms=15.3,
        )
        mock_repo.search = AsyncMock(return_value=search_result)

        tool = SearchCompaniesTool(search_repo=mock_repo)
        result = await tool.execute(
            {"query": "ACME", "limit": 10},
            {"tenant_id": "t1"},
        )

        assert result.success is True
        assert len(result.data) == 2
        assert result.total == 2
        assert result.data[0]["id"] == "c1"
        assert result.data[0]["name_en"] == "ACME Corp"
        assert result.data[0]["score"] == 0.95
        assert result.tool_name == "search_companies"

    @pytest.mark.asyncio
    async def test_execute_passes_filters(self):
        mock_repo = AsyncMock()
        mock_repo.search = AsyncMock(return_value=SearchResult(items=[], total=0))

        tool = SearchCompaniesTool(search_repo=mock_repo)
        await tool.execute(
            {"query": "tech", "city": "Riyadh", "industry": "IT"},
            {"tenant_id": "t1"},
        )

        called_query = mock_repo.search.call_args[0][0]
        assert called_query.query == "tech"
        assert called_query.filters["city"] == "Riyadh"
        assert called_query.filters["industry"] == "IT"
        assert called_query.tenant_id == "t1"

    @pytest.mark.asyncio
    async def test_execute_timeout_returns_error(self):
        import asyncio

        async def slow_search(_query):
            await asyncio.sleep(2)
            return SearchResult(items=[], total=0)

        mock_repo = AsyncMock()
        mock_repo.search = slow_search

        tool = SearchCompaniesTool(search_repo=mock_repo)
        result = await tool.execute({"query": "slow"}, {"tenant_id": "t1"})
        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_exception_returns_error(self):
        mock_repo = AsyncMock()
        mock_repo.search = AsyncMock(side_effect=RuntimeError("db down"))

        tool = SearchCompaniesTool(search_repo=mock_repo)
        result = await tool.execute({"query": "test"}, {"tenant_id": "t1"})
        assert result.success is False
        assert "db down" in result.error

    def test_result_dataclass(self):
        r = ToolResult(success=True, data=[{"id": "1"}], total=1, latency_ms=5.0, tool_name="test")
        assert r.success is True
        assert len(r.data) == 1
        assert r.latency_ms == 5.0


# ═══════════════════════════════════════════════════════════════
# B-2: Copilot Feedback
# ═══════════════════════════════════════════════════════════════


class TestCopilotFeedback:
    """Tests for feedback submission and statistics."""

    def test_submit_feedback_up(self):
        svc = CopilotFeedbackService()
        fb = svc.submit(
            conversation_id="conv1",
            message_id="msg1",
            user_id="u1",
            tenant_id="t1",
            rating="up",
            comment="Great answer",
            tool_name="search_companies",
        )
        assert fb.rating == FeedbackRating.UP
        assert fb.conversation_id == "conv1"
        assert fb.tool_name == "search_companies"
        assert fb.id

    def test_submit_feedback_down(self):
        svc = CopilotFeedbackService()
        fb = svc.submit(
            conversation_id="conv1",
            message_id="msg2",
            user_id="u1",
            tenant_id="t1",
            rating="down",
        )
        assert fb.rating == FeedbackRating.DOWN

    def test_stats_empty(self):
        svc = CopilotFeedbackService()
        stats = svc.get_stats()
        assert stats.total_feedback == 0
        assert stats.satisfaction_rate == 0.0

    def test_stats_with_data(self):
        svc = CopilotFeedbackService()
        for _ in range(7):
            svc.submit(
                conversation_id="c1", message_id="m1",
                user_id="u1", tenant_id="t1", rating="up",
            )
        for _ in range(3):
            svc.submit(
                conversation_id="c1", message_id="m2",
                user_id="u1", tenant_id="t1", rating="down",
            )

        stats = svc.get_stats()
        assert stats.total_feedback == 10
        assert stats.positive_count == 7
        assert stats.negative_count == 3
        assert stats.satisfaction_rate == pytest.approx(0.7, abs=0.01)

    def test_stats_by_tool(self):
        svc = CopilotFeedbackService()
        svc.submit(
            conversation_id="c1", message_id="m1",
            user_id="u1", tenant_id="t1",
            rating="up", tool_name="search",
        )
        svc.submit(
            conversation_id="c1", message_id="m2",
            user_id="u1", tenant_id="t1",
            rating="down", tool_name="search",
        )
        svc.submit(
            conversation_id="c1", message_id="m3",
            user_id="u1", tenant_id="t1",
            rating="up", tool_name="research",
        )

        stats = svc.get_stats()
        assert stats.by_tool["search"]["positive"] == 1
        assert stats.by_tool["search"]["negative"] == 1
        assert stats.by_tool["research"]["positive"] == 1

    def test_stats_by_tenant(self):
        svc = CopilotFeedbackService()
        svc.submit(
            conversation_id="c1", message_id="m1",
            user_id="u1", tenant_id="t1", rating="up",
        )
        svc.submit(
            conversation_id="c1", message_id="m2",
            user_id="u2", tenant_id="t2", rating="down",
        )

        stats_t1 = svc.get_stats(tenant_id="t1")
        assert stats_t1.total_feedback == 1
        stats_t2 = svc.get_stats(tenant_id="t2")
        assert stats_t2.total_feedback == 1

    def test_list_feedback_pagination(self):
        svc = CopilotFeedbackService()
        for i in range(15):
            svc.submit(
                conversation_id="c1", message_id=f"m{i}",
                user_id="u1", tenant_id="t1", rating="up",
            )

        page1 = svc.list_feedback(tenant_id="t1", limit=10, offset=0)
        page2 = svc.list_feedback(tenant_id="t1", limit=10, offset=10)
        assert len(page1) == 10
        assert len(page2) == 5

    def test_count(self):
        svc = CopilotFeedbackService()
        svc.submit(conversation_id="c1", message_id="m1", user_id="u1", tenant_id="t1", rating="up")
        svc.submit(conversation_id="c1", message_id="m2", user_id="u1", tenant_id="t2", rating="up")
        assert svc.count() == 2
        assert svc.count(tenant_id="t1") == 1


# ═══════════════════════════════════════════════════════════════
# B-3: Tool Telemetry
# ═══════════════════════════════════════════════════════════════


class TestToolTelemetry:
    """Tests for tool telemetry logging and aggregation."""

    def test_log_returns_record(self):
        svc = ToolTelemetryService()
        rec = svc.log(
            tool_name="search_companies",
            tenant_id="t1",
            success=True,
            latency_ms=45.2,
            result_count=5,
        )
        assert rec.tool_name == "search_companies"
        assert rec.success is True
        assert rec.latency_ms == 45.2

    def test_stats_empty(self):
        svc = ToolTelemetryService()
        stats = svc.get_stats()
        assert stats.total_calls == 0
        assert stats.success_rate == 0.0

    def test_stats_with_data(self):
        svc = ToolTelemetryService()
        for i in range(10):
            svc.log(
                tool_name="search_companies",
                tenant_id="t1",
                success=i < 8,
                latency_ms=10 + i * 5,
                result_count=i,
            )

        stats = svc.get_stats(tool_name="search_companies", tenant_id="t1")
        assert stats.total_calls == 10
        assert stats.success_count == 8
        assert stats.failure_count == 2
        assert stats.success_rate == pytest.approx(0.8, abs=0.01)

    def test_latency_percentiles(self):
        svc = ToolTelemetryService()
        for i in range(100):
            svc.log(
                tool_name="test",
                tenant_id="t1",
                success=True,
                latency_ms=float(i + 1),
                result_count=0,
            )

        stats = svc.get_stats(tool_name="test")
        assert stats.latency_p50_ms == pytest.approx(50.0, abs=5)
        assert stats.latency_p95_ms == pytest.approx(95.0, abs=5)
        assert stats.latency_p99_ms == pytest.approx(99.0, abs=5)

    def test_percentile_helper(self):
        assert _percentile([], 50) == 0.0
        assert _percentile([1, 2, 3], 50) == 2.0
        assert _percentile([1, 2, 3, 4, 5], 95) == 5.0
        assert _percentile(list(range(1, 101)), 99) >= 99

    def test_tool_breakdown(self):
        svc = ToolTelemetryService()
        svc.log(tool_name="search", tenant_id="t1", success=True, latency_ms=10, result_count=5)
        svc.log(tool_name="research", tenant_id="t1", success=True, latency_ms=20, result_count=3)

        breakdown = svc.get_tool_breakdown(tenant_id="t1")
        assert "search" in breakdown
        assert "research" in breakdown
        assert breakdown["search"].total_calls == 1

    def test_volume_over_time(self):
        svc = ToolTelemetryService()
        for _ in range(5):
            svc.log(tool_name="search", tenant_id="t1", success=True, latency_ms=10, result_count=1)

        volume = svc.get_volume_over_time(tool_name="search", tenant_id="t1", period_hours=1)
        assert len(volume) >= 1
        assert volume[0]["total"] == 5
        assert volume[0]["success"] == 5

    def test_count(self):
        svc = ToolTelemetryService()
        svc.log(tool_name="a", tenant_id="t1", success=True, latency_ms=1, result_count=0)
        svc.log(tool_name="b", tenant_id="t1", success=True, latency_ms=1, result_count=0)
        svc.log(tool_name="a", tenant_id="t2", success=True, latency_ms=1, result_count=0)

        assert svc.count() == 3
        assert svc.count(tool_name="a") == 2
        assert svc.count(tenant_id="t1") == 2

    def test_result_count_avg(self):
        svc = ToolTelemetryService()
        svc.log(tool_name="search", success=True, latency_ms=10, result_count=5)
        svc.log(tool_name="search", success=True, latency_ms=10, result_count=10)

        stats = svc.get_stats(tool_name="search")
        assert stats.result_count_avg == pytest.approx(7.5)


# ═══════════════════════════════════════════════════════════════
# B-4: Arabic Copilot
# ═══════════════════════════════════════════════════════════════


class TestArabicCopilot:
    """Tests for Arabic NLP detection, RTL, prompts, and Saudi context."""

    def test_detect_arabic(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("مرحبا، كيف حالك اليوم؟")
        assert result.is_arabic is True
        assert result.arabic_ratio > 0.5

    def test_detect_english(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("Hello, how are you today?")
        assert result.is_arabic is False
        assert result.arabic_ratio < 0.3

    def test_detect_mixed(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("شركة ACME هي شركة رائدة")
        assert result.is_arabic is True
        assert result.arabic_ratio > 0.3

    def test_detect_empty(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("")
        assert result.is_arabic is False

    def test_detect_language(self):
        engine = ArabicCopilotEngine()
        assert engine.detect_language("مرحبا") == "ar"
        assert engine.detect_language("hello") == "en"

    def test_detect_cr_number(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("السجل التجاري 1010123456")
        assert "commercial_registration" in result.detected_entities

    def test_detect_zatca(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("زاتكا تدير الضرائب")
        assert "zatca" in result.detected_entities

    def test_detect_vat(self):
        engine = ArabicCopilotEngine()
        result = engine.detect("ضريبة القيمة المضافة 15%")
        assert "vat" in result.detected_entities

    def test_rtl_markers_arabic(self):
        engine = ArabicCopilotEngine()
        text = "مرحبا بكم في منصة SalesOS"
        result = engine.add_rtl_markers(text)
        assert "\u202B" in result  # RTL embedding

    def test_rtl_markers_mixed_with_numbers(self):
        engine = ArabicCopilotEngine()
        text = "السجل التجاري 1010123456"
        result = engine.add_rtl_markers(text)
        assert "\u202B" in result
        assert "\u202A" in result  # LTR for numbers

    def test_rtl_markers_pure_latin(self):
        engine = ArabicCopilotEngine()
        text = "Hello World 123"
        result = engine.add_rtl_markers(text)
        assert "\u202B" not in result

    def test_rtl_markers_empty(self):
        engine = ArabicCopilotEngine()
        assert engine.add_rtl_markers("") == ""
        assert engine.add_rtl_markers(None) is None

    def test_prompt_template_arabic(self):
        engine = ArabicCopilotEngine()
        template = engine.get_prompt_template("research", "ar")
        assert "السجل التجاري" in template
        assert "ZATCA" in template

    def test_prompt_template_english(self):
        engine = ArabicCopilotEngine()
        template = engine.get_prompt_template("research", "en")
        assert "Commercial Registration" in template

    def test_prompt_template_default(self):
        engine = ArabicCopilotEngine()
        template = engine.get_prompt_template("unknown_intent", "ar")
        assert len(template) > 0

    def test_enrich_saudi_context_cr(self):
        engine = ArabicCopilotEngine()
        ctx = engine.enrich_saudi_context("شركة برقم سجل تجاري 1010123456", {})
        assert ctx["cr_number"] == "1010123456"
        assert ctx["is_arabic"] is True
        assert ctx["language"] == "ar"

    def test_enrich_saudi_context_preserves_existing(self):
        engine = ArabicCopilotEngine()
        ctx = engine.enrich_saudi_context("test query", {"company_id": "c1"})
        assert ctx["company_id"] == "c1"

    def test_saudi_context_terms_loaded(self):
        engine = ArabicCopilotEngine()
        assert len(engine.SAUDI_CONTEXT_TERMS) > 0
        assert "سجل_تجاري" in engine.SAUDI_CONTEXT_TERMS


# ═══════════════════════════════════════════════════════════════
# Model dataclass tests
# ═══════════════════════════════════════════════════════════════


class TestModels:
    """Tests for domain model defaults and construction."""

    def test_copilot_feedback_defaults(self):
        fb = CopilotFeedback()
        assert fb.id
        assert fb.rating == FeedbackRating.UP
        assert fb.created_at

    def test_tool_call_record_defaults(self):
        rec = ToolCallRecord()
        assert rec.id
        assert rec.success is True
        assert rec.timestamp

    def test_tool_telemetry_stats_defaults(self):
        stats = ToolTelemetryStats()
        assert stats.tool_name == "overall"
        assert stats.total_calls == 0

    def test_feedback_stats_defaults(self):
        stats = CopilotFeedbackStats()
        assert stats.total_feedback == 0
        assert stats.satisfaction_rate == 0.0


# ═══════════════════════════════════════════════════════════════
# Schema validation tests
# ═══════════════════════════════════════════════════════════════


class TestSchemas:
    """Tests for Pydantic schema validation."""

    def test_feedback_submit_valid(self):
        body = CopilotFeedbackSubmit(
            conversation_id="conv1",
            message_id="msg1",
            rating="up",
        )
        assert body.rating == "up"
        assert body.comment == ""

    def test_feedback_submit_invalid_rating(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CopilotFeedbackSubmit(
                conversation_id="conv1",
                message_id="msg1",
                rating="invalid",
            )

    def test_search_request_valid(self):
        req = SearchCompaniesRequest(query="ACME")
        assert req.query == "ACME"
        assert req.limit == 10

    def test_search_request_empty_query(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SearchCompaniesRequest(query="")

    def test_arabic_detect_request(self):
        req = ArabicDetectRequest(text="مرحبا")
        assert req.text == "مرحبا"
