"""IL-2B.2: claim/lease/dispatcher hardening unit tests.

Covers:
  - recover_expired_leases bumps lease_generation + fails orphan runs
  - CLAIMED→RUNNING rowcount=0 aborts without agent execution
  - missing lease_generation refused
  - state machine PENDING transitions
  - tenant-scoped Grounding session factory pins GUC
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.agent_runtime import AgentRuntime
from runtime.agent_runtime.queue import recover_expired_leases
from runtime.agent_runtime.state_machine import is_valid_transition


TID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_recover_expired_leases_sql_bumps_gen_and_fails_orphan_runs():
    session = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = SimpleNamespace(recovered_count=2)
    session.execute = AsyncMock(return_value=result)

    count = await recover_expired_leases(session, TID)

    assert count == 2
    sql = str(session.execute.await_args.args[0])
    assert "lease_generation = COALESCE(lease_generation, 0) + 1" in sql
    assert "UPDATE agent_runs" in sql
    assert "Lease expired; recovered for retry" in sql
    assert "RETURNING id" in sql
    params = session.execute.await_args.args[1]
    assert params["tenant_id"] == TID


@pytest.mark.asyncio
async def test_run_task_aborts_when_claimed_to_running_fence_rejects():
    """Stale gen / recover race: do not execute agent when rowcount=0."""
    task = SimpleNamespace(
        id=uuid.uuid4(),
        kind="brand",
        lease_generation=3,
        budget=4,
        input_data={},
        entity_id=None,
    )
    session = AsyncMock()
    transition = MagicMock()
    transition.rowcount = 0
    session.execute = AsyncMock(return_value=transition)
    session.add = MagicMock()
    session.commit = AsyncMock()

    executed = {"agent": False}

    async def boom(*_a, **_k):
        executed["agent"] = True
        raise AssertionError("agent must not run")

    runtime = AgentRuntime(session_factory=AsyncMock())
    with (
        patch("runtime.agent_runtime.apply_tenant_guc", new_callable=AsyncMock),
        patch.object(runtime, "_execute_agent", side_effect=boom),
    ):
        out = await runtime.run_task(session, task, TID)

    assert out["status"] == "STALE"
    assert executed["agent"] is False
    session.commit.assert_awaited()
    added = session.add.call_args.args[0]
    assert added.status == "FAILED"
    assert "fence rejected" in (added.result_summary or "")


@pytest.mark.asyncio
async def test_run_task_refuses_missing_lease_generation():
    task = SimpleNamespace(id=uuid.uuid4(), kind="brand")
    session = AsyncMock()
    runtime = AgentRuntime(session_factory=AsyncMock())

    out = await runtime.run_task(session, task, TID)

    assert out["status"] == "FAILED"
    assert "lease_generation" in out["error"]
    session.execute.assert_not_called()


def test_pending_transitions_include_claimed_and_exhausted():
    assert is_valid_transition("PENDING", "CLAIMED")
    assert is_valid_transition("PENDING", "EXHAUSTED")
    assert not is_valid_transition("PENDING", "RUNNING")


@pytest.mark.asyncio
async def test_tenant_scoped_session_factory_applies_guc():
    from runtime.agent_runtime import _tenant_scoped_session_factory

    inner_session = object()
    guc_calls: list = []

    class InnerCM:
        async def __aenter__(self):
            return inner_session

        async def __aexit__(self, *args):
            return False

    def base_factory():
        return InnerCM()

    async def fake_guc(sess, tenant_id=None):
        guc_calls.append((sess, tenant_id))

    factory = _tenant_scoped_session_factory(base_factory, TID)
    with patch("runtime.agent_runtime.apply_tenant_guc", side_effect=fake_guc):
        async with factory() as sess:
            assert sess is inner_session

    assert guc_calls == [(inner_session, TID)]
