"""Tests for the Workflow Service — validates CRUD + execute + validation."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from domains.workflow.models import Workflow, WorkflowStep, WorkflowExecution, WorkflowExecutionStep
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.engine import WorkflowEngine
from domains.workflow.service import WorkflowService, WorkflowValidationError


@pytest.fixture
def repo() -> InMemoryWorkflowRepository:
    return InMemoryWorkflowRepository()


@pytest.fixture
def engine(repo: InMemoryWorkflowRepository) -> WorkflowEngine:
    return WorkflowEngine(repo)


@pytest.fixture
def svc(repo: InMemoryWorkflowRepository, engine: WorkflowEngine) -> WorkflowService:
    return WorkflowService(repository=repo, engine=engine)


@pytest.fixture
def sample_steps() -> list[dict]:
    return [
        {"step_type": "send_email", "config": {"to": "test@example.com", "subject": "Hello", "body": "Test"}, "order": 0},
        {"step_type": "create_task", "config": {"title": "Follow up", "assignee": "owner"}, "order": 1},
    ]


class TestWorkflowService:
    """Validates WorkflowService CRUD operations, validation, and execution."""

    @pytest.mark.asyncio
    async def test_create_workflow(self, svc: WorkflowService, sample_steps: list[dict]):
        wf = await svc.create(
            tenant_id="tenant-1",
            name="Test Workflow",
            description="A test workflow",
            trigger_type="manual",
            status="draft",
            steps=sample_steps,
        )
        assert wf.id is not None
        assert wf.tenant_id == "tenant-1"
        assert wf.name == "Test Workflow"
        assert len(wf.steps) == 2
        assert wf.status == "draft"

    @pytest.mark.asyncio
    async def test_create_workflow_with_template(self, svc: WorkflowService):
        wf = await svc.create(
            tenant_id="tenant-1",
            name="From Template",
            template="lead_followup",
        )
        assert wf.id is not None
        assert len(wf.steps) == 2
        assert wf.steps[0].step_type == "send_email"
        assert wf.steps[1].step_type == "create_task"

    @pytest.mark.asyncio
    async def test_create_workflow_empty_name_raises(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="name is required"):
            await svc.create(tenant_id="tenant-1", name="   ")

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_trigger(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="Invalid trigger_type"):
            await svc.create(tenant_id="tenant-1", name="Test", trigger_type="invalid")

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_step_type(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="Invalid step_type"):
            await svc.create(
                tenant_id="tenant-1",
                name="Test",
                steps=[{"step_type": "invalid_type", "config": {}, "order": 0}],
            )

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_template(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="Template 'unknown' not found"):
            await svc.create(tenant_id="tenant-1", name="Test", template="unknown")

    @pytest.mark.asyncio
    async def test_list_workflows(self, svc: WorkflowService, sample_steps: list[dict]):
        await svc.create(tenant_id="tenant-1", name="WF 1", steps=sample_steps)
        await svc.create(tenant_id="tenant-1", name="WF 2", steps=sample_steps)
        await svc.create(tenant_id="tenant-2", name="WF 3", steps=sample_steps)

        wfs = await svc.list("tenant-1")
        assert len(wfs) == 2
        assert all(w.tenant_id == "tenant-1" for w in wfs)

    @pytest.mark.asyncio
    async def test_get_workflow(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(tenant_id="tenant-1", name="Test", steps=sample_steps)
        fetched = await svc.get(created.id, "tenant-1")
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Test"

    @pytest.mark.asyncio
    async def test_get_workflow_wrong_tenant(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(tenant_id="tenant-1", name="Test", steps=sample_steps)
        fetched = await svc.get(created.id, "tenant-2")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, svc: WorkflowService):
        fetched = await svc.get("nonexistent", "tenant-1")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_update_workflow(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(tenant_id="tenant-1", name="Original", steps=sample_steps)
        updated = await svc.update(
            workflow_id=created.id,
            tenant_id="tenant-1",
            name="Updated",
            description="New description",
        )
        assert updated.name == "Updated"
        assert updated.description == "New description"
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="not found"):
            await svc.update(workflow_id="nonexistent", tenant_id="tenant-1", name="New")

    @pytest.mark.asyncio
    async def test_delete_workflow(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(tenant_id="tenant-1", name="Delete me", steps=sample_steps)
        await svc.delete(created.id, "tenant-1")
        fetched = await svc.get(created.id, "tenant-1")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="not found"):
            await svc.delete("nonexistent", "tenant-1")

    @pytest.mark.asyncio
    async def test_execute_active_workflow(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(
            tenant_id="tenant-1",
            name="Execute me",
            status="active",
            steps=sample_steps,
        )
        execution = await svc.execute(created.id, "tenant-1", {"trigger": "manual"})
        assert execution is not None
        assert execution.status == "completed"
        assert len(execution.step_results) == 2
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[1].status == "completed"

    @pytest.mark.asyncio
    async def test_execute_draft_workflow_raises(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(
            tenant_id="tenant-1",
            name="Draft WF",
            status="draft",
            steps=sample_steps,
        )
        with pytest.raises(WorkflowValidationError, match="must be 'active'"):
            await svc.execute(created.id, "tenant-1")

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, svc: WorkflowService):
        with pytest.raises(WorkflowValidationError, match="not found"):
            await svc.execute("nonexistent", "tenant-1")

    @pytest.mark.asyncio
    async def test_execute_with_condition(self, svc: WorkflowService):
        steps = [
            {"step_type": "send_email", "config": {"to": "a@b.com", "subject": "Hi", "body": "Test"}, "order": 0, "condition": "context.amount > 100"},
        ]
        created = await svc.create(
            tenant_id="tenant-1",
            name="Conditional",
            status="active",
            steps=steps,
        )
        execution = await svc.execute(created.id, "tenant-1", {"amount": 50})
        assert execution.step_results[0].status == "skipped"

    @pytest.mark.asyncio
    async def test_execute_with_condition_met(self, svc: WorkflowService):
        steps = [
            {"step_type": "send_email", "config": {"to": "a@b.com", "subject": "Hi", "body": "Test"}, "order": 0, "condition": "context.amount > 100"},
        ]
        created = await svc.create(
            tenant_id="tenant-1",
            name="Conditional",
            status="active",
            steps=steps,
        )
        execution = await svc.execute(created.id, "tenant-1", {"amount": 200})
        assert execution.step_results[0].status == "completed"

    @pytest.mark.asyncio
    async def test_list_executions(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(
            tenant_id="tenant-1",
            name="Exec WF",
            status="active",
            steps=sample_steps,
        )
        await svc.execute(created.id, "tenant-1")
        await svc.execute(created.id, "tenant-1")

        executions = await svc.list_executions("tenant-1", created.id)
        assert len(executions) == 2

    @pytest.mark.asyncio
    async def test_get_execution(self, svc: WorkflowService, sample_steps: list[dict]):
        created = await svc.create(
            tenant_id="tenant-1",
            name="Exec WF",
            status="active",
            steps=sample_steps,
        )
        execution = await svc.execute(created.id, "tenant-1")
        fetched = await svc.get_execution(execution.id, "tenant-1")
        assert fetched is not None
        assert fetched.id == execution.id

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, svc: WorkflowService):
        fetched = await svc.get_execution("nonexistent", "tenant-1")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_execution_fails_on_bad_step(self, svc: WorkflowService):
        steps = [
            {"step_type": "send_email", "config": {}, "order": 0},
        ]
        created = await svc.create(
            tenant_id="tenant-1",
            name="Bad WF",
            status="active",
            steps=steps,
        )
        execution = await svc.execute(created.id, "tenant-1")
        assert execution.status == "failed"
        assert execution.error is not None

    @pytest.mark.asyncio
    async def test_decision_platform_block(self, svc: WorkflowService, sample_steps: list[dict]):
        class BlockingDecisionPlatform:
            async def evaluate(self, workflow_id: str, context: dict) -> dict:
                return {"block": True, "reason": "Policy violation"}

        svc._decision_platform = BlockingDecisionPlatform()
        created = await svc.create(
            tenant_id="tenant-1",
            name="Blocked WF",
            status="active",
            trigger_type="event",
            steps=sample_steps,
        )
        execution = await svc.execute(created.id, "tenant-1", {"trigger": "event"})
        assert execution.status == "skipped"
        assert "Blocked by Decision Platform" in (execution.error or "")

    @pytest.mark.asyncio
    async def test_decision_platform_non_blocking(self, svc: WorkflowService, sample_steps: list[dict]):
        class NonBlockingDecisionPlatform:
            async def evaluate(self, workflow_id: str, context: dict) -> dict:
                return {"block": False, "score": 0.9}

        svc._decision_platform = NonBlockingDecisionPlatform()
        created = await svc.create(
            tenant_id="tenant-1",
            name="Allowed WF",
            status="active",
            trigger_type="event",
            steps=sample_steps,
        )
        execution = await svc.execute(created.id, "tenant-1", {"trigger": "event"})
        assert execution.status == "completed"

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, svc: WorkflowService):
        await svc.create(tenant_id="tenant-1", name="WF A")
        await svc.create(tenant_id="tenant-2", name="WF B")

        wfs_1 = await svc.list("tenant-1")
        wfs_2 = await svc.list("tenant-2")
        assert len(wfs_1) == 1
        assert len(wfs_2) == 1
        assert wfs_1[0].name == "WF A"
        assert wfs_2[0].name == "WF B"
