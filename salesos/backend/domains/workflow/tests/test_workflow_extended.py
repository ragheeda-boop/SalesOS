"""Extended Workflow domain tests — engine handlers, event subscriber, resolution."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domains.workflow.engine import WorkflowEngine, _eval_condition, _resolve_config
from domains.workflow.models import Workflow, WorkflowExecution, WorkflowExecutionStep, WorkflowStep
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.service import WorkflowService
from domains.workflow.templates import LEAD_FOLLOWUP, LOST_DEAL_ANALYSIS


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_step(step_id="step1", step_type="webhook", config=None, order=0, condition=None):
    return WorkflowStep(
        id=step_id,
        workflow_id="wf1",
        step_type=step_type,
        config=config or {},
        order=order,
        condition=condition,
    )


def _make_repo():
    return InMemoryWorkflowRepository()


def _make_engine():
    return WorkflowEngine(repository=_make_repo())


# ── Engine handler edge cases ───────────────────────────────────────────────


    @pytest.mark.asyncio
    async def test_engine_webhook_no_url():
        engine = _make_engine()
        with pytest.raises(ValueError, match="url"):
            await engine._handle_webhook({"url": ""}, {})


@pytest.mark.asyncio
async def test_engine_webhook_with_url():
    engine = _make_engine()
    result = await engine._handle_webhook({"url": "http://test.com"}, {})
    assert result["called"] is True
    assert result["url"] == "http://test.com"


@pytest.mark.asyncio
async def test_engine_create_task_no_title():
    engine = _make_engine()
    with pytest.raises(ValueError, match="title"):
        await engine._handle_create_task({"title": ""}, {})


@pytest.mark.asyncio
async def test_engine_create_task_with_title():
    engine = _make_engine()
    result = await engine._handle_create_task({"title": "Follow up", "assignee": "ahmed"}, {})
    assert result["created"] is True
    assert result["title"] == "Follow up"


@pytest.mark.asyncio
async def test_engine_update_crm_no_entity():
    engine = _make_engine()
    with pytest.raises(ValueError, match="entity_id"):
        await engine._handle_update_crm({"entity": "deal", "entity_id": ""}, {})


@pytest.mark.asyncio
async def test_engine_update_crm_with_entity():
    engine = _make_engine()
    result = await engine._handle_update_crm(
        {"entity": "deal", "entity_id": "d1", "fields": {"stage": "won"}}, {}
    )
    assert result["updated"] is True
    assert result["entity_id"] == "d1"


@pytest.mark.asyncio
async def test_engine_send_email_no_to():
    engine = _make_engine()
    with pytest.raises(ValueError, match="to"):
        await engine._handle_send_email({"to": ""}, {})


@pytest.mark.asyncio
async def test_engine_send_email_with_to():
    engine = _make_engine()
    result = await engine._handle_send_email(
        {"to": "test@test.com", "subject": "Hello"}, {}
    )
    assert result["sent"] is True


@pytest.mark.asyncio
async def test_engine_nba_recommend():
    engine = _make_engine()
    result = await engine._handle_nba_recommend(
        {"action": "call", "reason": "hot lead"}, {}
    )
    assert result["recommended"] is True


@pytest.mark.asyncio
async def test_engine_execute_full_workflow():
    repo = _make_repo()
    engine = WorkflowEngine(repository=repo)
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Test", trigger_type="manual", status="active",
        steps=[
            _make_step("s1", "create_task", {"title": "Test Task"}, order=0),
            _make_step("s2", "send_email", {"to": "a@b.com", "subject": "Hi"}, order=1),
        ],
    )
    await repo.create(wf)
    execution = await engine.execute(wf, {"tenant_id": "t1"})
    assert execution.status == "completed"
    assert len(execution.step_results) == 2


@pytest.mark.asyncio
async def test_engine_execute_failing_step():
    repo = _make_repo()
    engine = WorkflowEngine(repository=repo)
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Fail", trigger_type="manual", status="active",
        steps=[
            _make_step("s1", "webhook", {"url": ""}, order=0),
        ],
    )
    await repo.create(wf)
    execution = await engine.execute(wf, {})
    assert execution.status == "failed"


@pytest.mark.asyncio
async def test_engine_skips_step_on_condition_false():
    repo = _make_repo()
    engine = WorkflowEngine(repository=repo)
    wf = Workflow(
        id="wf1", tenant_id="t1", name="Cond", trigger_type="manual", status="active",
        steps=[
            _make_step("s1", "send_email", {"to": "a@b.com", "subject": "Hi"}, order=0, condition="context.amount > 10000"),
        ],
    )
    await repo.create(wf)
    execution = await engine.execute(wf, {"amount": 5000})
    assert execution.status == "completed"
    assert execution.step_results[0].status == "skipped"


@pytest.mark.asyncio
async def test_engine_no_handler():
    engine = _make_engine()
    result = await engine._execute_step(
        _make_step("s1", "unknown_type", {}), {}
    )
    assert result.status == "failed"
    assert "No handler" in (result.error or "")


# ── _eval_condition ─────────────────────────────────────────────────────────


def test_eval_condition_equals():
    assert _eval_condition("status == hot", {"status": "hot"}) is True
    assert _eval_condition("status == hot", {"status": "cold"}) is False


def test_eval_condition_not_equals():
    assert _eval_condition("status != cold", {"status": "hot"}) is True


def test_eval_condition_gt():
    assert _eval_condition("score > 50", {"score": 75}) is True
    assert _eval_condition("score > 50", {"score": 30}) is False


def test_eval_condition_lt():
    assert _eval_condition("score < 50", {"score": 30}) is True
    assert _eval_condition("score < 50", {"score": 75}) is False


def test_eval_condition_gte():
    assert _eval_condition("score >= 50", {"score": 50}) is True
    assert _eval_condition("score >= 50", {"score": 49}) is False


def test_eval_condition_lte():
    assert _eval_condition("score <= 50", {"score": 50}) is True
    assert _eval_condition("score <= 50", {"score": 51}) is False


def test_eval_condition_in():
    assert _eval_condition("status in [hot,warm]", {"status": "hot"}) is True
    assert _eval_condition("status in [hot,warm]", {"status": "cold"}) is False


def test_eval_condition_not_in():
    assert _eval_condition("status not in [cold,freezing]", {"status": "hot"}) is True
    assert _eval_condition("status not in [cold,hot]", {"status": "hot"}) is False


def test_eval_condition_empty():
    assert _eval_condition("", {}) is True
    assert _eval_condition(None, {}) is True


def test_eval_condition_dot_notation():
    assert _eval_condition("context.amount > 100", {"amount": 200}) is True


def test_eval_condition_unknown_op():
    result = _eval_condition("x unknown 1", {"x": 1})
    assert result is True


# ── _resolve_config ─────────────────────────────────────────────────────────


def test_resolve_config_string_placeholder():
    result = _resolve_config("{{context.name}}", {"name": "Acme"})
    assert result == "Acme"


def test_resolve_config_missing_key():
    result = _resolve_config("{{context.missing}}", {})
    assert result == "{{context.missing}}"


def test_resolve_config_non_string():
    result = _resolve_config(42, {})
    assert result == 42


def test_resolve_config_multiple_placeholders():
    result = _resolve_config("Hello {{context.name}}, score={{context.score}}", {"name": "Ahmed", "score": 42})
    assert result == "Hello Ahmed, score=42"


# ── Event subscriber ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_event_subscriber_match_workflows():
    from domains.workflow.event_subscriber import WorkflowEventSubscriber

    repo = InMemoryWorkflowRepository()
    svc = AsyncMock(spec=WorkflowService)
    svc.list.return_value = [
        Workflow(id="w1", tenant_id="t1", name="lead_followup", trigger_type="event", status="active"),
    ]
    engine = _make_engine()
    event_bus = MagicMock()
    sub = WorkflowEventSubscriber(svc, event_bus, engine)

    class FakeEvent:
        event_type = "opportunity.created"
        tenant_id = "t1"
        data = {}
        event_id = "e1"

    matching = sub._match_workflows("opportunity.created", [Workflow(
        id="w1", tenant_id="t1", name="lead_followup", trigger_type="event", status="active",
    )])
    assert len(matching) == 1


def test_event_subscriber_no_match_wrong_type():
    from domains.workflow.event_subscriber import WorkflowEventSubscriber

    svc = AsyncMock(spec=WorkflowService)
    event_bus = MagicMock()
    engine = _make_engine()
    sub = WorkflowEventSubscriber(svc, event_bus, engine)
    matching = sub._match_workflows("unknown.event", [Workflow(
        id="w1", tenant_id="t1", name="test", trigger_type="event", status="active",
    )])
    assert len(matching) == 0


def test_event_subscriber_inactive_workflow():
    from domains.workflow.event_subscriber import WorkflowEventSubscriber

    svc = AsyncMock(spec=WorkflowService)
    event_bus = MagicMock()
    engine = _make_engine()
    sub = WorkflowEventSubscriber(svc, event_bus, engine)
    matching = sub._match_workflows("opportunity.created", [Workflow(
        id="w1", tenant_id="t1", name="lead_followup", trigger_type="event", status="inactive",
    )])
    assert len(matching) == 0


def test_event_subscriber_manual_trigger_ignored():
    from domains.workflow.event_subscriber import WorkflowEventSubscriber

    svc = AsyncMock(spec=WorkflowService)
    event_bus = MagicMock()
    engine = _make_engine()
    sub = WorkflowEventSubscriber(svc, event_bus, engine)
    matching = sub._match_workflows("opportunity.created", [Workflow(
        id="w1", tenant_id="t1", name="lead_followup", trigger_type="manual", status="active",
    )])
    assert len(matching) == 0


def test_event_subscriber_lost_deal_match():
    from domains.workflow.event_subscriber import WorkflowEventSubscriber

    svc = AsyncMock(spec=WorkflowService)
    event_bus = MagicMock()
    engine = _make_engine()
    sub = WorkflowEventSubscriber(svc, event_bus, engine)
    matching = sub._match_workflows("opportunity.lost", [Workflow(
        id="w1", tenant_id="t1", name="lost_deal_analysis", trigger_type="event", status="active",
    )])
    assert len(matching) == 1


def test_event_subscriber_meeting_match():
    from domains.workflow.event_subscriber import WorkflowEventSubscriber

    svc = AsyncMock(spec=WorkflowService)
    event_bus = MagicMock()
    engine = _make_engine()
    sub = WorkflowEventSubscriber(svc, event_bus, engine)
    matching = sub._match_workflows("meeting.scheduled", [Workflow(
        id="w1", tenant_id="t1", name="meeting_prep", trigger_type="event", status="active",
    )])
    assert len(matching) == 1


# ── Templates ───────────────────────────────────────────────────────────────


def test_lead_followup_template_structure():
    assert LEAD_FOLLOWUP.name == "Lead Follow-up"
    assert len(LEAD_FOLLOWUP.steps) > 0


def test_lost_deal_template_structure():
    assert LOST_DEAL_ANALYSIS.name == "Lost Deal Analysis"
    assert len(LOST_DEAL_ANALYSIS.steps) > 0


def test_all_templates_are_complete():
    from domains.workflow.templates import WORKFLOW_TEMPLATES
    for key, wf in WORKFLOW_TEMPLATES.items():
        assert wf.name
        assert wf.steps
        assert wf.trigger_type
