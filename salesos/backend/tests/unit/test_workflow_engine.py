"""Tests for Workflow Engine — models, repository, engine, conditions, templates."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from domains.workflow.models import Workflow, WorkflowStep, WorkflowExecution, WorkflowExecutionStep
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.engine import WorkflowEngine, _eval_condition, _resolve_config
from domains.workflow.templates import WORKFLOW_TEMPLATES


# ── Fixtures ──

@pytest.fixture
def repo():
    return InMemoryWorkflowRepository()


@pytest.fixture
def engine(repo):
    return WorkflowEngine(repo)


def _wf(tenant_id: str = "tenant-1", status: str = "active") -> Workflow:
    wf = Workflow(
        id=uuid.uuid4().hex[:12],
        tenant_id=tenant_id,
        name="Test Workflow",
        status=status,
        trigger_type="manual",
    )
    wf.steps = [
        WorkflowStep(id=uuid.uuid4().hex[:12], workflow_id=wf.id, step_type="send_email",
                     config={"to": "test@example.com", "subject": "Hello", "body": "Test body"}, order=0),
        WorkflowStep(id=uuid.uuid4().hex[:12], workflow_id=wf.id, step_type="create_task",
                     config={"title": "Test Task", "assignee": "user-1"}, order=1),
    ]
    return wf


# ── Model Tests ──

class TestWorkflowModels:
    def test_workflow_defaults(self):
        wf = Workflow(id="wf-1", tenant_id="t-1", name="Test")
        assert wf.status == "draft"
        assert wf.trigger_type == "manual"
        assert wf.steps == []
        assert isinstance(wf.created_at, datetime)
        assert isinstance(wf.updated_at, datetime)

    def test_workflow_step_defaults(self):
        step = WorkflowStep(id="s-1", workflow_id="wf-1", step_type="webhook")
        assert step.config == {}
        assert step.order == 0
        assert step.condition is None

    def test_workflow_execution_defaults(self):
        ex = WorkflowExecution(id="ex-1", workflow_id="wf-1", tenant_id="t-1")
        assert ex.status == "running"
        assert ex.trigger_event == "manual"
        assert ex.step_results == []

    def test_workflow_execution_step_defaults(self):
        es = WorkflowExecutionStep(id="es-1", execution_id="ex-1", step_id="s-1", step_type="send_email")
        assert es.status == "pending"
        assert es.result is None
        assert es.error is None


# ── Repository Tests ──

class TestWorkflowRepository:
    @pytest.mark.asyncio
    async def test_create_and_get_workflow(self, repo):
        wf = _wf()
        created = await repo.create(wf)
        assert created.id == wf.id

        fetched = await repo.get(wf.id, "tenant-1")
        assert fetched is not None
        assert fetched.name == "Test Workflow"
        assert len(fetched.steps) == 2

    @pytest.mark.asyncio
    async def test_get_workflow_wrong_tenant(self, repo):
        wf = _wf()
        await repo.create(wf)
        fetched = await repo.get(wf.id, "other-tenant")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_list_workflows_by_tenant(self, repo):
        wf1 = _wf("t-1")
        wf2 = _wf("t-1")
        wf3 = _wf("t-2")
        await repo.create(wf1)
        await repo.create(wf2)
        await repo.create(wf3)

        t1_list = await repo.list("t-1")
        assert len(t1_list) == 2

        t2_list = await repo.list("t-2")
        assert len(t2_list) == 1

    @pytest.mark.asyncio
    async def test_update_workflow(self, repo):
        wf = _wf()
        await repo.create(wf)
        wf.name = "Updated"
        updated = await repo.update(wf)
        assert updated.name == "Updated"
        assert updated.updated_at >= wf.created_at

    @pytest.mark.asyncio
    async def test_delete_workflow(self, repo):
        wf = _wf()
        await repo.create(wf)
        await repo.delete(wf.id, "tenant-1")
        fetched = await repo.get(wf.id, "tenant-1")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_workflow_wrong_tenant(self, repo):
        wf = _wf()
        await repo.create(wf)
        await repo.delete(wf.id, "other-tenant")
        fetched = await repo.get(wf.id, "tenant-1")
        assert fetched is not None

    @pytest.mark.asyncio
    async def test_execution_crud(self, repo):
        ex = WorkflowExecution(id="ex-1", workflow_id="wf-1", tenant_id="t-1")
        await repo.create_execution(ex)
        fetched = await repo.get_execution("ex-1", "t-1")
        assert fetched is not None
        assert fetched.status == "running"

        ex.status = "completed"
        await repo.update_execution(ex)
        updated = await repo.get_execution("ex-1", "t-1")
        assert updated.status == "completed"

    @pytest.mark.asyncio
    async def test_list_executions(self, repo):
        for i in range(3):
            await repo.create_execution(
                WorkflowExecution(id=f"ex-{i}", workflow_id=f"wf-{i}", tenant_id="t-1")
            )
        ex_list = await repo.list_executions("t-1")
        assert len(ex_list) == 3

    @pytest.mark.asyncio
    async def test_list_executions_filtered_by_workflow(self, repo):
        await repo.create_execution(WorkflowExecution(id="ex-1", workflow_id="wf-1", tenant_id="t-1"))
        await repo.create_execution(WorkflowExecution(id="ex-2", workflow_id="wf-2", tenant_id="t-1"))
        filtered = await repo.list_executions("t-1", workflow_id="wf-1")
        assert len(filtered) == 1
        assert filtered[0].id == "ex-1"


# ── Engine Tests ──

class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, engine, repo):
        wf = _wf()
        await repo.create(wf)

        execution = await engine.execute(wf, {"trigger": "manual"})

        assert execution.status == "completed"
        assert len(execution.step_results) == 2
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[1].status == "completed"
        assert execution.step_results[0].result["sent"] is True
        assert execution.step_results[1].result["created"] is True

    @pytest.mark.asyncio
    async def test_execute_workflow_updates_execution_status(self, engine, repo):
        wf = _wf()
        await repo.create(wf)

        execution = await engine.execute(wf, {})

        # Verify it was stored in repo
        stored = await repo.get_execution(execution.id, "tenant-1")
        assert stored is not None
        assert stored.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_create_task_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="create_task",
                         config={"title": "My Task", "assignee": "user-1", "description": "Do it"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[0].result["created"] is True
        assert execution.step_results[0].result["title"] == "My Task"

    @pytest.mark.asyncio
    async def test_execute_update_crm_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="update_crm",
                         config={"entity": "opportunity", "entity_id": "opp-1",
                                 "fields": {"stage": "closed_won"}}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[0].result["updated"] is True
        assert execution.step_results[0].result["entity"] == "opportunity"

    @pytest.mark.asyncio
    async def test_execute_webhook_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="webhook",
                         config={"url": "https://hooks.example.com/notify", "method": "POST"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[0].result["called"] is True

    @pytest.mark.asyncio
    async def test_execute_nba_recommend_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="nba_recommend",
                         config={"action": "follow_up", "reason": "High interest detected"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[0].result["recommended"] is True

    @pytest.mark.asyncio
    async def test_execute_send_email_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="send_email",
                         config={"to": "user@example.com", "subject": "Alert", "body": "Hello"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[0].result["sent"] is True

    @pytest.mark.asyncio
    async def test_send_email_missing_to_fails(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="send_email",
                         config={"subject": "No to"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.status == "failed"
        assert "send_email: 'to' address is required" in execution.error

    @pytest.mark.asyncio
    async def test_update_crm_missing_entity_id_fails(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="update_crm",
                         config={"entity": "opportunity"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.status == "failed"
        assert "entity_id" in execution.error

    @pytest.mark.asyncio
    async def test_create_task_missing_title_fails(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="create_task",
                         config={"assignee": "user-1"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.status == "failed"
        assert "title" in execution.error

    @pytest.mark.asyncio
    async def test_unregistered_step_type_fails(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="unknown_type", config={}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.status == "failed"
        assert "No handler registered" in execution.error

    @pytest.mark.asyncio
    async def test_context_resolved_in_config(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="send_email",
                         config={"to": "{{context.user_email}}", "subject": "Hi {{context.name}}", "body": "OK"},
                         order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {"user_email": "user@co.com", "name": "Alice"})
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[0].result["to"] == "user@co.com"
        assert execution.step_results[0].result["subject"] == "Hi Alice"

    @pytest.mark.asyncio
    async def test_steps_execute_in_order(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="create_task",
                         config={"title": "First"}, order=1),
            WorkflowStep(id="s2", workflow_id=wf.id, step_type="create_task",
                         config={"title": "Zero"}, order=0),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {})
        assert execution.step_results[0].result["title"] == "Zero"
        assert execution.step_results[1].result["title"] == "First"


# ── Condition Tests ──

class TestStepConditions:
    @pytest.mark.asyncio
    async def test_condition_true_executes_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="create_task",
                         config={"title": "Conditional"}, order=0,
                         condition="context.amount > 1000"),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {"amount": 5000})
        assert execution.step_results[0].status == "completed"

    @pytest.mark.asyncio
    async def test_condition_false_skips_step(self, engine, repo):
        wf = _wf(status="active")
        wf.steps = [
            WorkflowStep(id="s1", workflow_id=wf.id, step_type="create_task",
                         config={"title": "Conditional"}, order=0,
                         condition="context.amount > 1000"),
        ]
        await repo.create(wf)
        execution = await engine.execute(wf, {"amount": 500})
        assert execution.step_results[0].status == "skipped"

    @pytest.mark.asyncio
    async def test_condition_equals(self):
        assert _eval_condition("context.stage == closed_won", {"stage": "closed_won"}) is True
        assert _eval_condition("context.stage == closed_won", {"stage": "negotiation"}) is False

    @pytest.mark.asyncio
    async def test_condition_not_equals(self):
        assert _eval_condition("context.stage != closed_won", {"stage": "negotiation"}) is True
        assert _eval_condition("context.stage != closed_won", {"stage": "closed_won"}) is False

    @pytest.mark.asyncio
    async def test_condition_greater_than(self):
        assert _eval_condition("context.amount > 10000", {"amount": 20000}) is True
        assert _eval_condition("context.amount > 10000", {"amount": 5000}) is False

    @pytest.mark.asyncio
    async def test_condition_less_than(self):
        assert _eval_condition("context.amount < 10000", {"amount": 5000}) is True
        assert _eval_condition("context.amount < 10000", {"amount": 20000}) is False

    @pytest.mark.asyncio
    async def test_condition_greater_equal(self):
        assert _eval_condition("context.amount >= 10000", {"amount": 10000}) is True
        assert _eval_condition("context.amount >= 10000", {"amount": 9999}) is False

    @pytest.mark.asyncio
    async def test_condition_less_equal(self):
        assert _eval_condition("context.amount <= 10000", {"amount": 10000}) is True
        assert _eval_condition("context.amount <= 10000", {"amount": 10001}) is False

    @pytest.mark.asyncio
    async def test_condition_in_list(self):
        assert _eval_condition("context.stage in [closed_won,closed_lost]", {"stage": "closed_won"}) is True
        assert _eval_condition("context.stage in [closed_won,closed_lost]", {"stage": "negotiation"}) is False

    @pytest.mark.asyncio
    async def test_condition_not_in_list(self):
        assert _eval_condition("context.stage not in [closed_won,closed_lost]", {"stage": "negotiation"}) is True
        assert _eval_condition("context.stage not in [closed_won,closed_lost]", {"stage": "closed_won"}) is False

    @pytest.mark.asyncio
    async def test_no_condition_always_executes(self):
        assert _eval_condition(None, {}) is True
        assert _eval_condition("", {}) is True

    @pytest.mark.asyncio
    async def test_condition_with_resolve_config(self):
        result = _resolve_config("{{context.user_email}}", {"user_email": "a@b.com"})
        assert result == "a@b.com"

    @pytest.mark.asyncio
    async def test_resolve_config_no_placeholder(self):
        result = _resolve_config("static_value", {"key": "val"})
        assert result == "static_value"

    @pytest.mark.asyncio
    async def test_resolve_config_non_string(self):
        result = _resolve_config(42, {})
        assert result == 42


# ── Template Tests ──

class TestWorkflowTemplates:
    def test_templates_defined(self):
        assert len(WORKFLOW_TEMPLATES) == 4
        assert "lead_followup" in WORKFLOW_TEMPLATES
        assert "deal_review" in WORKFLOW_TEMPLATES
        assert "meeting_prep" in WORKFLOW_TEMPLATES
        assert "lost_deal_analysis" in WORKFLOW_TEMPLATES

    def test_lead_followup_steps(self):
        tpl = WORKFLOW_TEMPLATES["lead_followup"]
        assert tpl.trigger_type == "event"
        assert len(tpl.steps) == 2
        assert tpl.steps[0].step_type == "send_email"
        assert tpl.steps[1].step_type == "create_task"

    def test_deal_review_steps(self):
        tpl = WORKFLOW_TEMPLATES["deal_review"]
        assert len(tpl.steps) == 2
        assert tpl.steps[0].step_type == "send_email"
        assert tpl.steps[1].step_type == "update_crm"

    def test_meeting_prep_steps(self):
        tpl = WORKFLOW_TEMPLATES["meeting_prep"]
        assert len(tpl.steps) == 2
        assert tpl.steps[0].step_type == "nba_recommend"
        assert tpl.steps[1].step_type == "create_task"

    def test_lost_deal_analysis_steps(self):
        tpl = WORKFLOW_TEMPLATES["lost_deal_analysis"]
        assert len(tpl.steps) == 2
        assert tpl.steps[0].step_type == "create_task"
        assert tpl.steps[1].step_type == "send_email"
        assert tpl.steps[1].condition == "context.amount > 10000"

    @pytest.mark.asyncio
    async def test_lost_deal_condition_skips_email(self, engine, repo):
        tpl = WORKFLOW_TEMPLATES["lost_deal_analysis"]
        wf = Workflow(
            id=uuid.uuid4().hex[:12], tenant_id="t-1", name=tpl.name,
            status="active", trigger_type=tpl.trigger_type, steps=tpl.steps,
        )
        for s in wf.steps:
            s.workflow_id = wf.id
        await repo.create(wf)

        execution = await engine.execute(wf, {
            "deal_name": "Small Deal", "amount": 500, "owner": "u1", "manager_email": "m@co.com",
        })
        # Step 0 (create_task) completes, Step 1 (send_email) skipped because amount < 10000
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[1].status == "skipped"
        assert execution.status == "completed"

    @pytest.mark.asyncio
    async def test_lost_deal_condition_sends_email(self, engine, repo):
        tpl = WORKFLOW_TEMPLATES["lost_deal_analysis"]
        wf = Workflow(
            id=uuid.uuid4().hex[:12], tenant_id="t-1", name=tpl.name,
            status="active", trigger_type=tpl.trigger_type, steps=tpl.steps,
        )
        for s in wf.steps:
            s.workflow_id = wf.id
        await repo.create(wf)

        execution = await engine.execute(wf, {
            "deal_name": "Big Deal", "amount": 50000, "owner": "u1", "manager_email": "m@co.com",
        })
        assert execution.step_results[0].status == "completed"
        assert execution.step_results[1].status == "completed"

    def test_template_default_status_draft(self):
        for key, tpl in WORKFLOW_TEMPLATES.items():
            assert tpl.status == "draft", f"Template {key} should be draft"

    def test_template_has_correct_trigger_type(self):
        assert WORKFLOW_TEMPLATES["lead_followup"].trigger_type == "event"
        assert WORKFLOW_TEMPLATES["deal_review"].trigger_type == "event"
        assert WORKFLOW_TEMPLATES["lost_deal_analysis"].trigger_type == "event"
