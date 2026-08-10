"""AI Foundation F2 -- Cost and Budget tests."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.providers.cost_tracker import (
    BudgetExceededError,
    BudgetConfig,
    CostRecord,
    CostTracker,
    PeriodSummary,
    get_cost_tracker,
    init_cost_tracker,
)


def make_async_mock(return_value=None):
    m = AsyncMock()
    m.__aenter__ = AsyncMock(return_value=m)
    m.__aexit__ = AsyncMock(return_value=None)
    if return_value is not None:
        m.execute = AsyncMock(return_value=return_value)
    m.begin = MagicMock()
    m.begin.__aenter__ = AsyncMock(return_value=m)
    m.begin.__aexit__ = AsyncMock(return_value=None)
    return m


def make_factory(session):
    def factory():
        return session
    return factory


def make_exec_result_scalar(value):
    r = MagicMock()
    r.scalar_one = MagicMock(return_value=value)
    return r


class Row(dict):
    pass


def make_exec_result_rows(rows):
    r = MagicMock()
    mapped = [Row(item) for item in rows]
    map_obj = MagicMock()
    map_obj.all.return_value = mapped
    r.mappings.return_value = map_obj
    return r


def make_exec_result_one(row_dict):
    r = MagicMock()
    for k, v in row_dict.items():
        setattr(r, k, v)
    r.one_or_none = MagicMock(return_value=r)
    return r


def make_exec_result_one_none():
    r = MagicMock()
    r.one_or_none = MagicMock(return_value=None)
    return r


class TestInitialization:
    def test_init_cost_tracker_sets_global(self):
        session = make_async_mock()
        tracker = init_cost_tracker(make_factory(session))
        assert get_cost_tracker() is tracker

    def test_get_cost_tracker_raises_when_not_initialized(self):
        import intelligence.providers.cost_tracker as ct
        ct._cost_tracker = None
        with pytest.raises(RuntimeError, match="not initialized"):
            get_cost_tracker()
        init_cost_tracker(make_factory(make_async_mock()))


class TestBudgetManagement:
    @pytest.mark.asyncio
    async def test_set_budget_creates_new(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        config = await tracker.set_budget("tenant-1", 1000, enforced=True)
        assert config.tenant_id == "tenant-1"
        assert config.monthly_budget_cents == 1000
        assert config.is_enforced is True
        assert config.period_spend_cents == 0
        session.execute.assert_called()
        session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_budget_returns_none_for_unknown(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one_none())
        tracker = CostTracker(make_factory(session))
        result = await tracker.get_budget("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_budget_returns_config(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one({
            "tenant_id": "t1",
            "monthly_budget_cents": 2000,
            "period_start": date(2026, 8, 1),
            "period_spend_cents": 500,
            "is_enforced": True,
        }))
        tracker = CostTracker(make_factory(session))
        result = await tracker.get_budget("t1")
        assert result.monthly_budget_cents == 2000
        assert result.period_spend_cents == 500
        assert result.is_enforced is True


class TestBudgetEnforcement:
    @pytest.mark.asyncio
    async def test_check_budget_allows_when_under(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one({
            "tenant_id": "t1",
            "monthly_budget_cents": 10000,
            "period_start": date(2026, 8, 1),
            "period_spend_cents": 5000,
            "is_enforced": True,
        }))
        tracker = CostTracker(make_factory(session))
        result = await tracker.check_budget("t1", 0.05)
        assert result.allowed is True
        assert result.would_exceed is False
        assert result.monthly_budget == 100.0
        assert result.current_spend == 50.0

    @pytest.mark.asyncio
    async def test_check_budget_blocks_when_exceeded(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one({
            "tenant_id": "t1",
            "monthly_budget_cents": 1000,
            "period_start": date(2026, 8, 1),
            "period_spend_cents": 990,
            "is_enforced": True,
        }))
        tracker = CostTracker(make_factory(session))
        result = await tracker.check_budget("t1", 0.50)
        assert result.allowed is False
        assert result.would_exceed is True

    @pytest.mark.asyncio
    async def test_check_budget_no_record_allows(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one_none())
        tracker = CostTracker(make_factory(session))
        result = await tracker.check_budget("t1", 0.10)
        assert result.allowed is True
        assert result.would_exceed is False
        assert result.monthly_budget == 0.0

    @pytest.mark.asyncio
    async def test_check_budget_not_enforced_allows(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one({
            "tenant_id": "t1",
            "monthly_budget_cents": 1000,
            "period_start": date(2026, 8, 1),
            "period_spend_cents": 99999,
            "is_enforced": False,
        }))
        tracker = CostTracker(make_factory(session))
        result = await tracker.check_budget("t1", 0.10)
        assert result.allowed is True


class TestMonthlyReset:
    @pytest.mark.asyncio
    async def test_check_budget_resets_on_new_month(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_one({
            "tenant_id": "t1",
            "monthly_budget_cents": 10000,
            "period_start": date(2026, 7, 1),
            "period_spend_cents": 9999,
            "is_enforced": True,
        }))
        tracker = CostTracker(make_factory(session))
        result = await tracker.check_budget("t1", 0.50)
        assert result.allowed is True
        assert result.would_exceed is False


class TestBudgetExceededError:
    def test_error_message(self):
        err = BudgetExceededError("t1", 5.23, 5.00)
        assert "t1" in str(err)
        assert "5.2300" in str(err)
        assert "5.00" in str(err)


class TestCostRecording:
    @pytest.mark.asyncio
    async def test_track_persists_to_db(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        record = await tracker.track(
            tenant_id="t1",
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            operation="chat",
            user_id="user-1",
            latency_ms=123.45,
        )
        assert record.tenant_id == "t1"
        assert record.provider == "openai"
        assert record.model == "gpt-4o-mini"
        assert record.total_tokens == 150
        assert record.operation == "chat"
        assert record.user_id == "user-1"
        assert record.latency_ms == 123.45
        assert record.success is True
        assert record.retry_count == 0
        assert record.cost > 0
        session.execute.assert_called()
        session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_track_failed_request(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        record = await tracker.track(
            tenant_id="t1",
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=0,
            completion_tokens=0,
            success=False,
            error="Rate limited",
            retry_count=1,
        )
        assert record.success is False
        assert record.error == "Rate limited"
        assert record.retry_count == 1
        assert record.cost == 0.0

    @pytest.mark.asyncio
    async def test_track_with_retry_count(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        record = await tracker.track(
            tenant_id="t1",
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            retry_count=2,
        )
        assert record.retry_count == 2
        assert record.success is True

    @pytest.mark.asyncio
    async def test_track_unique_ids(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        r1 = await tracker.track(
            tenant_id="t1", provider="openai", model="gpt-4o-mini",
            prompt_tokens=10, completion_tokens=5,
        )
        r2 = await tracker.track(
            tenant_id="t1", provider="openai", model="gpt-4o-mini",
            prompt_tokens=10, completion_tokens=5,
        )
        assert r1.id != r2.id


class TestProviderModelAttribution:
    @pytest.mark.asyncio
    async def test_attribution(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        r1 = await tracker.track(
            tenant_id="t1", provider="openai", model="gpt-4o",
            prompt_tokens=100, completion_tokens=50,
        )
        r2 = await tracker.track(
            tenant_id="t1", provider="anthropic", model="claude-3-5-sonnet-20241022",
            prompt_tokens=200, completion_tokens=100,
        )
        assert r1.provider == "openai"
        assert r1.model == "gpt-4o"
        assert r2.provider == "anthropic"
        assert r2.model == "claude-3-5-sonnet-20241022"


class TestDeductBudget:
    @pytest.mark.asyncio
    async def test_deduct_budget(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        await tracker.deduct_budget("t1", 0.0045)
        session.execute.assert_called()
        session.begin.assert_called()


class TestGetRecords:
    @pytest.mark.asyncio
    async def test_returns_entries(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_rows([{
            "id": "abc123",
            "tenant_id": "t1",
            "user_id": "u1",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "operation": "chat",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost": 0.00015,
            "latency_ms": 100.0,
            "success": True,
            "error": None,
            "retry_count": 0,
            "timestamp": datetime(2026, 8, 10, tzinfo=timezone.utc),
        }]))
        tracker = CostTracker(make_factory(session))
        records = await tracker.get_records(tenant_id="t1", limit=10)
        assert len(records) == 1
        assert records[0].provider == "openai"
        assert records[0].tenant_id == "t1"

    @pytest.mark.asyncio
    async def test_empty(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_rows([]))
        tracker = CostTracker(make_factory(session))
        records = await tracker.get_records(tenant_id="t1")
        assert records == []

    @pytest.mark.asyncio
    async def test_filters_by_provider(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_rows([]))
        tracker = CostTracker(make_factory(session))
        records = await tracker.get_records(tenant_id="t1", provider="openai")
        assert isinstance(records, list)


class TestGetSpend:
    @pytest.mark.asyncio
    async def test_returns_total(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_scalar(0.0123))
        tracker = CostTracker(make_factory(session))
        spend = await tracker.get_spend("t1")
        assert spend == 0.0123

    @pytest.mark.asyncio
    async def test_with_since(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_scalar(0.005))
        tracker = CostTracker(make_factory(session))
        since = datetime.now(timezone.utc) - timedelta(days=7)
        spend = await tracker.get_spend("t1", since=since)
        assert spend == 0.005


class TestPeriodSummary:
    @pytest.mark.asyncio
    async def test_summary(self):
        session = make_async_mock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return make_exec_result_one({
                    "tenant_id": "t1",
                    "monthly_budget_cents": 5000,
                    "period_start": date(2026, 8, 1),
                    "period_spend_cents": 1200,
                    "is_enforced": True,
                })
            elif call_count[0] == 2:
                return make_exec_result_scalar(0.012)
            else:
                r = MagicMock()
                r.total_calls = 5
                r.total_cost = 0.012
                r.total_tokens = 3000
                r.one = MagicMock(return_value=r)
                return r

        session.execute = AsyncMock(side_effect=side_effect)
        tracker = CostTracker(make_factory(session))
        summary = await tracker.get_period_summary("t1")
        assert summary.tenant_id == "t1"
        assert summary.total_calls == 5
        assert summary.total_cost == 0.012
        assert summary.total_tokens == 3000
        assert isinstance(summary, PeriodSummary)


class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_different_tenants_separate(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        r1 = await tracker.track(
            tenant_id="tenant-a", provider="openai", model="gpt-4o-mini",
            prompt_tokens=100, completion_tokens=50,
        )
        r2 = await tracker.track(
            tenant_id="tenant-b", provider="openai", model="gpt-4o-mini",
            prompt_tokens=100, completion_tokens=50,
        )
        assert r1.tenant_id == "tenant-a"
        assert r2.tenant_id == "tenant-b"
        assert r1.id != r2.id

    @pytest.mark.asyncio
    async def test_get_spend_scoped_to_tenant(self):
        session = make_async_mock()
        session.execute = AsyncMock(return_value=make_exec_result_scalar(0.005))
        tracker = CostTracker(make_factory(session))
        spend = await tracker.get_spend("specific-tenant")
        assert spend == 0.005


class TestSingleAccountingPath:
    @pytest.mark.asyncio
    async def test_track_creates_unique_id(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        r1 = await tracker.track(
            tenant_id="t1", provider="openai", model="gpt-4o-mini",
            prompt_tokens=10, completion_tokens=5,
        )
        r2 = await tracker.track(
            tenant_id="t1", provider="openai", model="gpt-4o-mini",
            prompt_tokens=10, completion_tokens=5,
        )
        assert r1.id != r2.id

    @pytest.mark.asyncio
    async def test_track_records_all_fields(self):
        session = make_async_mock()
        tracker = CostTracker(make_factory(session))
        record = await tracker.track(
            tenant_id="t1",
            provider="gemini",
            model="gemini-1.5-flash",
            prompt_tokens=500,
            completion_tokens=200,
            operation="embed",
            user_id="u123",
            latency_ms=50.0,
            success=True,
        )
        assert record.tenant_id == "t1"
        assert record.provider == "gemini"
        assert record.model == "gemini-1.5-flash"
        assert record.operation == "embed"
        assert record.user_id == "u123"
        assert record.success is True
        assert record.total_tokens == 700
