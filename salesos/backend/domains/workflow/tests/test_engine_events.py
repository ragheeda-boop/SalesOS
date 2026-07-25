"""Tests for WorkflowEngine domain event emission."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from domains.workflow.engine import WorkflowEngine
from domains.workflow.models import Workflow, WorkflowStep, WorkflowExecution
from domains.workflow.repository import InMemoryWorkflowRepository


@pytest.fixture
def repo() -> InMemoryWorkflowRepository:
    return InMemoryWorkflowRepository()


@pytest.fixture
def event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def engine(repo: InMemoryWorkflowRepository, event_bus: AsyncMock) -> WorkflowEngine:
    return WorkflowEngine(repository=repo, event_bus=event_bus)


@pytest.mark.asyncio
async def test_engine_emits_completed_event(engine: WorkflowEngine, repo: InMemoryWorkflowRepository, event_bus: AsyncMock):
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Test", trigger_type="manual", status="active",
        steps=[
            WorkflowStep(id="s1", workflow_id="wf1", step_type="log_message", config={"message": "hello"}, order=0),
        ],
    )
    await repo.create(wf)
    execution = await engine.execute(wf, {"trigger": "manual"})
    assert execution.status == "completed"
    event_bus.publish.assert_awaited_once()
    args, _ = event_bus.publish.await_args
    event = args[0]
    from sdk.events.domain_events import WorkflowCompleted
    assert isinstance(event, WorkflowCompleted)
    assert event.aggregate_id == "wf1"
    assert event.tenant_id == "t1"


@pytest.mark.asyncio
async def test_engine_emits_failed_event(engine: WorkflowEngine, repo: InMemoryWorkflowRepository, event_bus: AsyncMock):
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Failing", trigger_type="manual", status="active",
        steps=[
            WorkflowStep(id="s1", workflow_id="wf1", step_type="send_email", config={"to": ""}, order=0),
        ],
    )
    await repo.create(wf)
    execution = await engine.execute(wf, {})
    assert execution.status == "failed"
    event_bus.publish.assert_awaited_once()
    args, _ = event_bus.publish.await_args
    event = args[0]
    from sdk.events.domain_events import WorkflowFailed
    assert isinstance(event, WorkflowFailed)


@pytest.mark.asyncio
async def test_engine_does_not_emit_without_event_bus(repo: InMemoryWorkflowRepository):
    engine = WorkflowEngine(repository=repo)
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Test", trigger_type="manual", status="active",
        steps=[
            WorkflowStep(id="s1", workflow_id="wf1", step_type="log_message", config={"message": "hello"}, order=0),
        ],
    )
    await repo.create(wf)
    execution = await engine.execute(wf, {})
    assert execution.status == "completed"


@pytest.mark.asyncio
async def test_engine_emits_timed_out_event(engine: WorkflowEngine, repo: InMemoryWorkflowRepository, event_bus: AsyncMock):
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Timeout", trigger_type="manual", status="active",
        timeout_seconds=0.05,
        steps=[
            WorkflowStep(id="s1", workflow_id="wf1", step_type="log_message", config={"message": "hello"}, order=0),
        ],
    )
    await repo.create(wf)

    async def slow_handler(config, ctx, step=None):
        import asyncio
        await asyncio.sleep(10)
        return {}

    engine.register_handler("log_message", slow_handler)
    execution = await engine.execute(wf, {})
    assert execution.status == "timed_out"
    event_bus.publish.assert_awaited_once()
    args, _ = event_bus.publish.await_args
    event = args[0]
    from sdk.events.domain_events import WorkflowFailed
    assert isinstance(event, WorkflowFailed)
