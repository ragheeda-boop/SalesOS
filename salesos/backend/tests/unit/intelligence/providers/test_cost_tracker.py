"""Cost tracker tests — persistence, budgets, summary."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intelligence.providers.cost_tracker import CostTracker, CostRecord


def test_cost_tracker_track():
    tracker = CostTracker()
    record = tracker.track(provider="openai", model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50)
    assert record.provider == "openai"
    assert record.total_tokens == 150
    assert record.cost > 0


def test_cost_tracker_with_persist_flag():
    tracker = CostTracker()
    record = tracker.track(provider="anthropic", model="claude-3-5-sonnet-20241022", prompt_tokens=200, completion_tokens=100, persist=False)
    assert record.provider == "anthropic"
    assert len(tracker._records) == 1


@pytest.mark.asyncio
async def test_cost_tracker_persist_to_db():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_factory = MagicMock(return_value=mock_session)

    tracker = CostTracker(db_session_factory=mock_factory)
    tracker.track(provider="openai", model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50, tenant_id="tenant-1")

    await tracker.persist_to_db()

    assert mock_session.execute.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_cost_tracker_load_from_db():
    class MockRow(dict):
        pass

    mock_row = MockRow({
        "id": "test-id",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "cost": 0.001,
        "latency_ms": 100.0,
        "operation": "completion",
        "tenant_id": "tenant-1",
        "user_id": None,
        "success": True,
        "error": None,
        "retry_count": 0,
        "timestamp": "2026-07-16T00:00:00+00:00",
    })

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [mock_row]

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.execute.return_value = mock_result
    mock_factory = MagicMock(return_value=mock_session)

    tracker = CostTracker(db_session_factory=mock_factory)
    records = await tracker.load_records_from_db(tenant_id="tenant-1")

    assert len(records) == 1
    assert records[0].provider == "openai"
    assert records[0].total_tokens == 150


def test_cost_tracker_budget():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 10.0)
    assert tracker.is_budget_exceeded("tenant-1") is False

    tracker.track(provider="openai", model="gpt-4o", prompt_tokens=1000000, completion_tokens=500000, tenant_id="tenant-1")
    assert tracker.get_spend("tenant-1") > 0


def test_cost_tracker_summary():
    tracker = CostTracker()
    tracker.track(provider="openai", model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50)
    tracker.track(provider="anthropic", model="claude-3-haiku", prompt_tokens=200, completion_tokens=100)

    summary = tracker.get_summary()
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 450


def test_cost_tracker_summary_empty():
    tracker = CostTracker()
    summary = tracker.get_summary("nonexistent")
    assert summary["total_calls"] == 0


def test_cost_tracker_budget_exceeded():
    tracker = CostTracker()
    tracker.set_budget("tenant-2", 0.001)
    tracker.track(provider="openai", model="gpt-4o", prompt_tokens=500, completion_tokens=200, tenant_id="tenant-2")
    assert tracker.is_budget_exceeded("tenant-2") is True


def test_cost_tracker_track_failure():
    tracker = CostTracker()
    record = tracker.track(provider="openai", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=5, success=False, error="API error")
    assert record.success is False
    assert record.error == "API error"


def test_cost_tracker_grouping():
    tracker = CostTracker()
    tracker.track(provider="openai", model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50, tenant_id="t1")
    tracker.track(provider="openai", model="gpt-4o", prompt_tokens=200, completion_tokens=100, tenant_id="t1")
    tracker.track(provider="anthropic", model="claude-3-haiku", prompt_tokens=50, completion_tokens=25, tenant_id="t1")

    summary = tracker.get_summary("t1")
    assert summary["by_provider"]["openai"]["calls"] == 2
    assert summary["by_provider"]["anthropic"]["calls"] == 1
    assert summary["by_model"]["gpt-4o-mini"]["calls"] == 1
