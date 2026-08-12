"""EventRuntime subscriber bounds: timeout_seconds + max_retries wiring."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_retry_policy_logs_structured_retry_fields():
    """Retry logs must carry step/subscriber/event_type/decision_id/retry extras."""
    logger = MagicMock()

    async def boom(_event):
        raise RuntimeError("fail once")

    policy = RetryPolicy(max_retries=1, timeout_seconds=1.0, jitter=False)
    ok, err = await policy.execute(boom, _event(), "il2a", logger=logger)

    assert ok is False
    assert err == "fail once"
    logger.warn.assert_called()
    kwargs = logger.warn.call_args.kwargs
    assert kwargs["step"] == "retry"
    assert kwargs["subscriber"] == "il2a"
    assert kwargs["event_type"] == "decision.created"
    assert kwargs["decision_id"] == "d1"
    assert kwargs["retry"] == 1
    assert "event" not in kwargs  # renamed to event_type for Railway JSON


@pytest.mark.asyncio
async def test_store_ok_logs_step_elapsed_decision_id():
    logger = MagicMock()

    class _OkSession:
        async def __aenter__(self):
            session = MagicMock()
            session.commit = AsyncMock()
            return session

        async def __aexit__(self, *args):
            return False

    with patch(
        "runtime.event_runtime.PostgresEventStore"
    ) as store_cls:
        store_cls.return_value.append = AsyncMock()
        runtime = EventRuntime(
            session_factory=lambda: _OkSession(), logger=logger
        )
        runtime.register(
            "decision.created",
            AsyncMock(),
            name="il2a",
            max_retries=1,
            timeout_seconds=1.0,
        )
        await runtime.publish(_event())

    store_calls = [
        c for c in logger.info.call_args_list if c.args and c.args[0] == "event_runtime.store_ok"
    ]
    assert store_calls
    kwargs = store_calls[0].kwargs
    assert kwargs["step"] == "store"
    assert kwargs["event_type"] == "decision.created"
    assert kwargs["decision_id"] == "d1"
    assert "elapsed_ms" in kwargs



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
