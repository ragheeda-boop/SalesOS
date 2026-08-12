"""Unit tests for dispatcher GUC pinning and single-claim execution.

Proves:
  A — apply_tenant_guc is called on every session used for
      recover/retire/claim/run, with the dispatch tenant_id.
  C — claimed rows are passed to run_task; handlers must not claim again.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from runtime.agent_runtime import dispatcher as disp

TID = "11111111-1111-1111-1111-111111111111"


class _SessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *args):
        return False


def _task(task_id: str, kind: str):
    return SimpleNamespace(id=task_id, kind=kind, lease_generation=1, budget=4)


def _session_factory(session):
    def factory():
        return _SessionCM(session)

    return factory


class FakeRuntime:
    executed: list

    def __init__(self, _factory):
        pass

    async def run_task(self, session, task, tenant_id):
        FakeRuntime.executed.append((id(session), task, tenant_id))


@pytest.mark.asyncio
async def test_guc_applied_on_cleanup_and_claim_sessions():
    """Empty queue: GUC on recover/retire session and both claim sessions."""
    session = AsyncMock()
    guc_calls: list[tuple] = []

    async def fake_guc(sess, tenant_id=None):
        guc_calls.append((id(sess), tenant_id))

    with (
        patch.object(disp, "async_session", _session_factory(session)),
        patch.object(disp, "apply_tenant_guc", side_effect=fake_guc),
        patch.object(disp, "_recover_expired_leases", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_retire_exhausted", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_claim_due", new_callable=AsyncMock, return_value=[]),
    ):
        stats = await disp.dispatch_all(TID)

    assert stats["claimed_fast"] == 0
    assert stats["claimed_research"] == 0
    assert stats["errors"] == []
    assert len(guc_calls) == 3
    assert all(tid == TID for _, tid in guc_calls)
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_guc_applied_on_run_sessions_per_claimed_task():
    """Each already-claimed task opens a run session that also gets GUC."""
    session = AsyncMock()
    fast = [_task("f1", "brand"), _task("f2", "portrait")]
    research = [_task("r1", "research_company")]
    guc_tenants: list[str | None] = []

    async def fake_guc(_sess, tenant_id=None):
        guc_tenants.append(tenant_id)

    async def fake_claim(_session, _tenant_id, **kwargs):
        if kwargs.get("kinds_include") is not None:
            return list(fast)
        return list(research)

    FakeRuntime.executed = []

    with (
        patch.object(disp, "async_session", _session_factory(session)),
        patch.object(disp, "apply_tenant_guc", side_effect=fake_guc),
        patch.object(disp, "_recover_expired_leases", new_callable=AsyncMock, return_value=1),
        patch.object(disp, "_retire_exhausted", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_claim_due", side_effect=fake_claim),
        patch("runtime.agent_runtime.AgentRuntime", FakeRuntime),
    ):
        stats = await disp.dispatch_all(TID)

    # 1 cleanup + 2 claim + 3 run sessions
    assert len(guc_tenants) == 6
    assert all(t == TID for t in guc_tenants)
    assert stats["claimed_fast"] == 2
    assert stats["claimed_research"] == 1
    assert stats["recovered"] == 1


@pytest.mark.asyncio
async def test_claimed_tasks_are_executed_without_second_claim():
    """First claim is the only claim; those rows are the ones run_task sees."""
    session = AsyncMock()
    fast = [_task("f1", "brand"), _task("f2", "simple_lookup")]
    research = [_task("r1", "identify")]
    claim_calls: list[dict] = []

    async def fake_claim(_session, tenant_id, **kwargs):
        claim_calls.append({"tenant_id": tenant_id, **kwargs})
        if kwargs.get("kinds_include") is not None:
            return list(fast)
        return list(research)

    FakeRuntime.executed = []

    with (
        patch.object(disp, "async_session", _session_factory(session)),
        patch.object(disp, "apply_tenant_guc", new_callable=AsyncMock),
        patch.object(disp, "_recover_expired_leases", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_retire_exhausted", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_claim_due", side_effect=fake_claim),
        patch("runtime.agent_runtime.AgentRuntime", FakeRuntime),
    ):
        stats = await disp.dispatch_all(TID)

    assert len(claim_calls) == 2, "handlers must not call claim_due a second time"
    assert claim_calls[0]["kinds_include"] is not None
    assert claim_calls[1]["kinds_exclude"] is not None
    executed_ids = {t.id for _, t, _ in FakeRuntime.executed}
    assert executed_ids == {"f1", "f2", "r1"}
    assert all(tid == TID for _, _, tid in FakeRuntime.executed)
    assert stats["claimed_fast"] == 2
    assert stats["claimed_research"] == 1


@pytest.mark.asyncio
async def test_handlers_do_not_discard_first_claim_when_batch_exceeds_concurrency():
    """All claimed rows run, not only min(concurrency, count) re-claims."""
    session = AsyncMock()
    fast = [_task(f"f{i}", "brand") for i in range(8)]

    async def fake_claim(_session, _tenant_id, **kwargs):
        if kwargs.get("kinds_include") is not None:
            return list(fast)
        return []

    FakeRuntime.executed = []

    with (
        patch.object(disp, "async_session", _session_factory(session)),
        patch.object(disp, "apply_tenant_guc", new_callable=AsyncMock),
        patch.object(disp, "_recover_expired_leases", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_retire_exhausted", new_callable=AsyncMock, return_value=0),
        patch.object(disp, "_claim_due", side_effect=fake_claim),
        patch("runtime.agent_runtime.AgentRuntime", FakeRuntime),
    ):
        stats = await disp.dispatch_all(TID)

    assert stats["claimed_fast"] == 8
    assert {t.id for _, t, _ in FakeRuntime.executed} == {f"f{i}" for i in range(8)}


def test_dispatcher_source_has_no_handler_claim():
    """Source guard: run path must not call claim_due."""
    import inspect

    src = inspect.getsource(disp._run_claimed_task)
    assert "_claim_due" not in src
    assert "claim_due" not in src
    assert "apply_tenant_guc" in src
    assert "run_task" in src


def test_run_task_repins_guc_after_commit():
    """set_config is_local=true; run_task must re-pin after the RUNNING commit."""
    import inspect
    from runtime.agent_runtime import AgentRuntime

    src = inspect.getsource(AgentRuntime._run_task_internal)
    assert src.count("apply_tenant_guc") >= 2
