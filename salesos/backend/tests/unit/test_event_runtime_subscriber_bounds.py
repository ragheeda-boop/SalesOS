"""EventRuntime subscriber bounds: timeout_seconds + max_retries wiring."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.event_runtime import EventRuntime, RetryPolicy
from sdk.events.base import DomainEvent


def _event() -> DomainEvent:
    return DomainEvent(
        event_id="e1",
        event_type="decision.created",
        event_version=1,
        aggregate_id="d1",
        aggregate_type="decision",
        tenant_id="t1",
        data={"decision_id": "d1"},
    )


@pytest.mark.asyncio
async def test_retry_policy_honors_timeout_seconds():
    started = asyncio.Event()

    async def slow(_event):
        started.set()
        await asyncio.sleep(5.0)

    policy = RetryPolicy(max_retries=1, timeout_seconds=0.05, jitter=False)
    t0 = asyncio.get_running_loop().time()
    ok, err = await policy.execute(slow, _event(), "slow_sub")
    elapsed = asyncio.get_running_loop().time() - t0

    assert ok is False
    assert err == "timeout"
    assert started.is_set()
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_register_passes_timeout_to_retry_policy():
    runtime = EventRuntime(session_factory=None, logger=None)
    calls = {"n": 0}

    async def slow(_event):
        calls["n"] += 1
        await asyncio.sleep(5.0)

    runtime.register(
        "decision.created",
        slow,
        name="bounded",
        max_retries=1,
        timeout_seconds=0.05,
    )

    t0 = asyncio.get_running_loop().time()
    lifecycle = await runtime.publish(_event())
    elapsed = asyncio.get_running_loop().time() - t0

    assert calls["n"] == 1
    assert "bounded" in lifecycle.subscriber_errors
    assert lifecycle.subscriber_errors["bounded"] == "timeout"
    assert elapsed < 1.0
    assert lifecycle.dead_lettered is True


@pytest.mark.asyncio
async def test_store_exception_still_fans_out():
    """IL-2A: durable store failure must not skip in-process subscribers."""
    calls = {"n": 0}

    async def handler(_event):
        calls["n"] += 1

    class _BoomSession:
        async def __aenter__(self):
            raise RuntimeError("store broken")

        async def __aexit__(self, *args):
            return False

    runtime = EventRuntime(session_factory=lambda: _BoomSession(), logger=None)
    runtime.register(
        "decision.created",
        handler,
        name="il2a",
        max_retries=1,
        timeout_seconds=1.0,
    )

    lifecycle = await runtime.publish(_event())
    assert calls["n"] == 1
    assert "il2a" in lifecycle.subscriber_results


@pytest.mark.asyncio
async def test_store_checkout_timeout_still_fans_out():
    """Pool checkout hang must not block fan-out past store budget."""
    calls = {"n": 0}

    async def handler(_event):
        calls["n"] += 1

    class _SlowCheckout:
        async def __aenter__(self):
            await asyncio.sleep(5.0)
            return MagicMock()

        async def __aexit__(self, *args):
            return False

    runtime = EventRuntime(session_factory=lambda: _SlowCheckout(), logger=None)
    runtime.register(
        "decision.created",
        handler,
        name="il2a",
        max_retries=1,
        timeout_seconds=1.0,
    )

    t0 = asyncio.get_running_loop().time()
    lifecycle = await runtime.publish(_event())
    elapsed = asyncio.get_running_loop().time() - t0

    assert calls["n"] == 1
    assert elapsed < 3.0
    assert "il2a" in lifecycle.subscriber_results


@pytest.mark.asyncio
async def test_postgres_event_store_append_uses_json_dumps_binds():
    """Append must CAST JSONB from dumps — raw dict binds fail under asyncpg."""
    from sdk.events.store import PostgresEventStore

    session = AsyncMock()
    session.execute = AsyncMock()
    store = PostgresEventStore(session)
    await store.append(_event())

    assert session.execute.await_count == 1
    params = session.execute.await_args.args[1]
    assert isinstance(params["data"], str)
    assert isinstance(params["metadata"], str)
    assert '"decision_id"' in params["data"]
    assert params["event_type"] == "decision.created"
    assert params["id"]
