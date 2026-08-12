"""IL-2A: _save_decision must bind JSONB as json text + CAST (not raw list/dict).

Raw list/dict binds raise asyncpg DataError ('list' object has no attribute
'encode') and can stall ~pool_timeout under PgBouncer.
"""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.decision_runtime import DecisionEngine
from runtime.decision_runtime.models import DecisionObject, DecisionType


def _decision(**kwargs) -> DecisionObject:
    base = dict(
        decision_id="did-il2a-save-1",
        company_id="00000000-0000-0000-0000-000000000001",
        tenant_id="326e0825-1834-4399-8cca-77c2679f172b",
        decision_type=DecisionType.RECOMMEND_CALL,
        priority=50,
        confidence=0.5,
        reasoning="unit",
        evidence=["a"],
        supporting_features={"intent_score": 1.0},
        context_snapshot={"business": {}},
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    base.update(kwargs)
    return DecisionObject(**base)


def _engine_with_session(session: MagicMock) -> DecisionEngine:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=None)
    factory = MagicMock(return_value=cm)
    return DecisionEngine(
        session_factory=factory,
        context_builder=MagicMock(),
        policy_engine=MagicMock(),
        recommendation_engine=MagicMock(),
        event_runtime=MagicMock(),
    )


@pytest.mark.asyncio
async def test_save_decision_jsonb_uses_cast_and_dumps():
    session = MagicMock()
    existing = MagicMock()
    existing.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(side_effect=[existing, MagicMock()])
    session.commit = AsyncMock()

    eng = _engine_with_session(session)
    with patch(
        "app.database.apply_tenant_guc", new_callable=AsyncMock
    ) as guc:
        await eng._save_decision(_decision())

    guc.assert_awaited_once()
    assert session.execute.await_count == 2
    insert_call = session.execute.await_args_list[1]
    sql = str(insert_call.args[0])
    params = insert_call.args[1]
    assert "CAST(:evidence AS jsonb)" in sql
    assert "CAST(:features AS jsonb)" in sql
    assert "CAST(:ctx AS jsonb)" in sql
    assert params["evidence"] == json.dumps(["a"])
    assert params["features"] == json.dumps({"intent_score": 1.0})
    assert params["ctx"] == json.dumps({"business": {}})
    assert isinstance(params["evidence"], str)
    assert not isinstance(params["evidence"], list)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_decision_skips_insert_when_exists():
    session = MagicMock()
    existing = MagicMock()
    existing.scalar_one_or_none.return_value = 1
    session.execute = AsyncMock(return_value=existing)
    session.commit = AsyncMock()

    eng = _engine_with_session(session)
    with patch("app.database.apply_tenant_guc", new_callable=AsyncMock):
        await eng._save_decision(_decision())

    assert session.execute.await_count == 1
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_evaluate_continues_when_persist_fails():
    """Persist errors must not block in-memory NBA (IL-2A unblock)."""
    from runtime.context_runtime import CompanyContext
    from runtime.policy_runtime import PolicyResult, PolicyEvaluation
    from runtime.recommendation_runtime import Recommendation

    ctx = CompanyContext()
    cb = MagicMock()
    cb.build = AsyncMock(return_value=ctx)
    pe = MagicMock()
    pe.evaluate = AsyncMock(return_value=[])
    pe.metrics.snapshot.return_value = {}
    rec = Recommendation(
        recommendation_id="r1",
        decision_id="d1",
        company_id="c1",
        tenant_id="t1",
        title="t",
        description="b",
        priority=1,
        confidence=0.5,
    )
    re = MagicMock()
    re.generate = AsyncMock(return_value=rec)
    er = MagicMock()
    er.publish = AsyncMock()

    eng = DecisionEngine(
        session_factory=MagicMock(),
        context_builder=cb,
        policy_engine=pe,
        recommendation_engine=re,
        event_runtime=er,
    )
    eng._save_decision = AsyncMock(side_effect=RuntimeError("db down"))

    result = await eng.evaluate("c1", "t1")
    assert result is not None
    assert result["company_id"] == "c1"
    assert eng.metrics.decisions_created == 1


@pytest.mark.asyncio
async def test_evaluate_returns_before_slow_event_publish():
    """HTTP evaluate must not await EventRuntime fan-out (RetryPolicy ~30s).

    Same class of stall as identity register: publish store + subscribers
    with 3×10s wait_for blocks the response even when decision is persisted.
    """
    from runtime.context_runtime import CompanyContext
    from runtime.recommendation_runtime import Recommendation

    ctx = CompanyContext()
    cb = MagicMock()
    cb.build = AsyncMock(return_value=ctx)
    pe = MagicMock()
    pe.evaluate = AsyncMock(return_value=[])
    pe.metrics.snapshot.return_value = {}
    rec = Recommendation(
        recommendation_id="r1",
        decision_id="d1",
        company_id="c1",
        tenant_id="t1",
        title="t",
        description="b",
        priority=1,
        confidence=0.5,
    )
    re = MagicMock()
    re.generate = AsyncMock(return_value=rec)

    publish_started = asyncio.Event()
    publish_release = asyncio.Event()

    async def _slow_publish(_event):
        publish_started.set()
        await publish_release.wait()

    er = MagicMock()
    er.publish = AsyncMock(side_effect=_slow_publish)

    eng = DecisionEngine(
        session_factory=MagicMock(),
        context_builder=cb,
        policy_engine=pe,
        recommendation_engine=re,
        event_runtime=er,
    )
    eng._save_decision = AsyncMock()

    t0 = asyncio.get_running_loop().time()
    result = await eng.evaluate("c1", "t1")
    elapsed = asyncio.get_running_loop().time() - t0

    assert result is not None
    assert result.get("decision_id")
    assert elapsed < 1.0, f"evaluate blocked on publish: {elapsed:.2f}s"
    # call_soon defers create_task until after current coroutine yields
    await asyncio.sleep(0)
    await asyncio.wait_for(publish_started.wait(), timeout=1.0)
    assert er.publish.await_count == 1
    publish_release.set()
    # Let the background task finish cleanly.
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_evaluate_background_tasks_queues_publish_not_inline():
    """Starlette BackgroundTasks path must not start publish during evaluate."""
    from runtime.context_runtime import CompanyContext
    from runtime.recommendation_runtime import Recommendation

    ctx = CompanyContext()
    cb = MagicMock()
    cb.build = AsyncMock(return_value=ctx)
    pe = MagicMock()
    pe.evaluate = AsyncMock(return_value=[])
    pe.metrics.snapshot.return_value = {}
    rec = Recommendation(
        recommendation_id="r1",
        decision_id="d1",
        company_id="c1",
        tenant_id="t1",
        title="t",
        description="b",
        priority=1,
        confidence=0.5,
    )
    re = MagicMock()
    re.generate = AsyncMock(return_value=rec)
    er = MagicMock()
    er.publish = AsyncMock()

    queued: list = []

    class _BG:
        def add_task(self, fn, *args, **kwargs):
            queued.append((fn, args, kwargs))

    eng = DecisionEngine(
        session_factory=MagicMock(),
        context_builder=cb,
        policy_engine=pe,
        recommendation_engine=re,
        event_runtime=er,
    )
    eng._save_decision = AsyncMock()

    result = await eng.evaluate("c1", "t1", background_tasks=_BG())
    await asyncio.sleep(0)

    assert result is not None
    assert result.get("decision_id")
    assert er.publish.await_count == 0
    assert len(queued) == 1
    fn, args, kwargs = queued[0]
    await fn(*args, **kwargs)
    assert er.publish.await_count == 1
