"""EventRuntime subscriber bounds: timeout_seconds + max_retries wiring."""

from __future__ import annotations

import asyncio

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
