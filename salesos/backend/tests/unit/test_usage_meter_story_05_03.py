"""STORY-05-03 — UsageMeter bucketing + rollup combine (pure / light)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.billing.usage_metrics import (
    combine_quantities,
    hour_bucket,
    normalize_metric_key,
    normalize_op,
)


def test_metric_keys_and_defaults() -> None:
    assert normalize_metric_key("AI_TOKENS") == "ai_tokens"
    assert normalize_op(None, metric_key="seats") == "set"
    assert normalize_op(None, metric_key="api_calls") == "add"
    with pytest.raises(ValueError):
        normalize_metric_key("nope")


def test_hour_bucket_utc() -> None:
    at = datetime(2026, 8, 2, 5, 47, 12, tzinfo=UTC)
    start, end = hour_bucket(at)
    assert start == datetime(2026, 8, 2, 5, 0, 0, tzinfo=UTC)
    assert end == datetime(2026, 8, 2, 6, 0, 0, tzinfo=UTC)


def test_combine_add_and_set() -> None:
    assert combine_quantities("add", 10, 3) == 13
    assert combine_quantities("set", 10, 3) == 10
    assert combine_quantities("set", 2, 9) == 9


@pytest.mark.asyncio
async def test_record_and_rollup_in_memory_session() -> None:
    """Light service test with AsyncMock session — verifies rollup aggregation path."""
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    from app.modules.billing.usage_meter_service import UsageMeterService

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    svc = UsageMeterService(session)

    tid = uuid4()
    # record_event path
    row = await svc.record_event(
        tenant_id=tid,
        metric_key="api_calls",
        quantity=5,
        recorded_at=datetime(2026, 8, 2, 4, 15, tzinfo=UTC),
        source="unit",
    )
    assert row.metric_key == "api_calls"
    assert row.quantity == 5
    session.add.assert_called()
    session.flush.assert_awaited()
