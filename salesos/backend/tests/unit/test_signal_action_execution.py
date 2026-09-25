from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date

import pytest

from app.modules.signal_actions.actions import ActionExecutor
from app.modules.signal_actions.models import ActionType, ActionUrgency, NextBestAction

TENANT_ID = "00000000-0000-0000-0000-000000000001"
COMPANY_ID = "00000000-0000-0000-0000-000000000002"


class _Result:
    def __init__(self, rows=(), rowcount=1):
        self._rows = list(rows)
        self.rowcount = rowcount

    def fetchall(self):
        return self._rows


class _State:
    def __init__(self, company_matches=()):
        self.company_matches = list(company_matches)
        self.tasks = {}
        self.actions = {}
        self.statements = []


class _Session:
    def __init__(self, state):
        self.state = state

    async def execute(self, statement, params=None):
        sql = str(statement)
        args = params or {}
        self.state.statements.append((sql, args))
        if "SELECT id FROM companies" in sql:
            return _Result(self.state.company_matches)
        if "INSERT INTO tasks" in sql:
            self.state.tasks.setdefault(str(args["id"]), args)
        if "INSERT INTO agent_sales_actions" in sql:
            self.state.actions.setdefault(str(args["id"]), args)
        if "UPDATE agent_sales_actions" in sql:
            return _Result(rowcount=1 if str(args["id"]) in self.state.actions else 0)
        return _Result()

    async def commit(self):
        return None

    async def rollback(self):
        return None


def _factory(state):
    @asynccontextmanager
    async def session_context():
        yield _Session(state)

    return session_context


def _nba(action_type=ActionType.CALL):
    return NextBestAction(
        id="nba-stable-1",
        tenant_id=TENANT_ID,
        company_name="Acme",
        action_type=action_type,
        urgency=ActionUrgency.TODAY,
        title="Call Acme about expansion",
        rationale="Expansion signal detected",
    )


@pytest.mark.asyncio
async def test_execute_creates_tenant_linked_crm_task_and_is_idempotent():
    state = _State(company_matches=[(COMPANY_ID,)])
    executor = ActionExecutor(_factory(state))

    first = await executor.execute(_nba(), TENANT_ID, "user-1")
    second = await executor.execute(_nba(), TENANT_ID, "user-1")

    assert first.id == second.id
    assert len(state.tasks) == 1
    assert len(state.actions) == 1
    task = next(iter(state.tasks.values()))
    action = next(iter(state.actions.values()))
    assert str(task["tenant_id"]) == TENANT_ID
    assert task["company_id"] == COMPANY_ID
    assert task["title"] == "Call Acme about expansion"
    assert task["priority"] == "high"
    assert task["due_date"] == date.today()
    task_insert = next(sql for sql, _ in state.statements if "INSERT INTO tasks" in sql)
    assert "'nba'" in task_insert
    assert action["user_id"] == "user-1"
    assert first.metadata["crm_task_created"] is True
    assert first.metadata["company_id"] == COMPANY_ID
    assert any("set_config('app.tenant_id'" in sql for sql, _ in state.statements)


@pytest.mark.asyncio
async def test_no_action_records_a_skipped_audit_without_creating_task():
    state = _State()
    executor = ActionExecutor(_factory(state))

    action = await executor.execute(_nba(ActionType.NO_ACTION), TENANT_ID, "user-1")

    assert action.status == "skipped"
    assert action.metadata["crm_task_created"] is False
    assert state.tasks == {}
    assert len(state.actions) == 1


@pytest.mark.asyncio
async def test_blank_company_name_never_links_to_an_empty_name_record():
    state = _State(company_matches=[(COMPANY_ID,)])
    executor = ActionExecutor(_factory(state))
    nba = _nba()
    nba.company_name = "  "

    action = await executor.execute(nba, TENANT_ID, "user-1")

    assert action.metadata.get("company_id") is None
    assert state.tasks
    assert next(iter(state.tasks.values()))["company_id"] is None
    assert not any("SELECT id FROM companies" in sql for sql, _ in state.statements)


@pytest.mark.asyncio
async def test_completing_action_also_completes_linked_task():
    state = _State()
    executor = ActionExecutor(_factory(state))
    action = await executor.execute(_nba(), TENANT_ID, "user-1")

    assert await executor.complete(action.id, TENANT_ID, "positive", "Call completed")

    task_update = next(
        sql for sql, _ in state.statements if "UPDATE tasks" in sql
    )
    assert "tenant_id::text = :tenant_id" in task_update
    assert state.actions[action.id]["tenant_id"] == TENANT_ID
