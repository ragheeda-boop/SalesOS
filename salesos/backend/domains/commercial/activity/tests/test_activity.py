"""Tests for Activity Domain — sessions, outcomes, rule engine, KPIs."""

from datetime import datetime, timezone

import pytest

from domains.commercial.activity.contracts.models import (
    Activity,
    ActivityOutcome,
    ActivitySession,
    ActivityStatus,
    ActivityType,
    OutcomeDefinition,
)
from domains.commercial.activity.contracts.outcome_catalog import OutcomeCatalog
from domains.commercial.activity.contracts.repository import ActivitySessionQuery
from domains.commercial.activity.engine.in_memory_repo import (
    InMemoryActivityRepository,
)
from domains.commercial.activity.engine.rule_engine import ActivityRuleEngine
from domains.commercial.activity.engine.service import ActivityService


# ── Models ──

def test_activity_type_enum():
    assert ActivityType.CALL.value == "call"
    assert ActivityType.MEETING.value == "meeting"


def test_activity_immutable_when_completed():
    a = Activity(id="a1", activity_type=ActivityType.CALL, owner_id="u1", status=ActivityStatus.COMPLETED)
    assert a.is_completed


def test_activity_session_aggregate():
    session = ActivitySession(id="s1", tenant_id="t1", title="Visit", target_id="opp-1")
    assert session.status == ActivityStatus.SCHEDULED
    assert len(session.activities) == 0


# ── Outcome Catalog ──

def test_outcome_catalog_loaded():
    OutcomeCatalog.load_defaults()
    assert OutcomeCatalog.get("call_connected") is not None
    assert OutcomeCatalog.get("nonexistent") is None


def test_outcomes_by_type():
    OutcomeCatalog.load_defaults()
    call_outcomes = OutcomeCatalog.for_type(ActivityType.CALL)
    assert len(call_outcomes) >= 4  # connected, no_answer, qualified, rejected


def test_outcome_with_business_action():
    OutcomeCatalog.load_defaults()
    od = OutcomeCatalog.get("meeting_approved")
    assert od is not None
    assert od.business_action == "advance_stage"


def test_outcome_catalog_actions():
    OutcomeCatalog.load_defaults()
    actions = OutcomeCatalog.all_actions()
    assert "advance_stage" in actions
    assert "update_probability" in actions


# ── Rule Engine ──

@pytest.mark.asyncio
async def test_rule_engine_registers_handlers():
    engine = ActivityRuleEngine()
    triggered = []

    async def handler(outcome):
        triggered.append(outcome.business_action)

    engine.on_outcome("advance_stage", handler)
    assert "advance_stage" in engine.registered_actions


@pytest.mark.asyncio
async def test_rule_engine_triggers_handler():
    engine = ActivityRuleEngine()
    triggered = []

    async def handler(outcome):
        triggered.append(outcome.business_action)

    engine.on_outcome("advance_stage", handler)

    outcome = ActivityOutcome(
        activity_id="a1", session_id="s1", activity_type=ActivityType.MEETING,
        outcome_id="meeting_approved", outcome_label="تمت الموافقة",
        business_action="advance_stage", action_params={},
        target_id="opp-1", target_type="opportunity",
        owner_id="u1", completed_at=datetime.now(timezone.utc),
    )

    actions = await engine.evaluate(outcome)
    assert "advance_stage" in actions
    assert len(triggered) == 1


@pytest.mark.asyncio
async def test_rule_engine_ignores_unregistered():
    engine = ActivityRuleEngine()
    outcome = ActivityOutcome(
        activity_id="a1", session_id="s1", activity_type=ActivityType.CALL,
        outcome_id="call_connected", outcome_label="تم الاتصال",
        business_action="none", action_params={},
        target_id="opp-1", target_type="opportunity",
        owner_id="u1", completed_at=datetime.now(timezone.utc),
    )
    actions = await engine.evaluate(outcome)
    assert actions == []


# ── Service — Session Management ──

@pytest.mark.asyncio
async def test_create_session():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)

    session = await service.create_session("t1", "Customer Visit", "opp-1")
    assert session.title == "Customer Visit"
    assert session.target_id == "opp-1"
    assert session.status == ActivityStatus.SCHEDULED


@pytest.mark.asyncio
async def test_add_activity():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)

    session = await service.create_session("t1", "Visit", "opp-1")
    activity = await service.add_activity(session.id, ActivityType.MEETING, "u1", "User")

    assert activity.activity_type == ActivityType.MEETING
    assert activity.owner_id == "u1"

    # Verify activity is in session
    updated = await service.get_session(session.id)
    assert len(updated.activities) == 1


@pytest.mark.asyncio
async def test_complete_activity_no_business_action():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)

    OutcomeCatalog.load_defaults()

    session = await service.create_session("t1", "Call", "opp-1")
    activity = await service.add_activity(session.id, ActivityType.CALL, "u1")

    outcome = await service.complete_activity(session.id, activity.id, "call_connected")
    assert outcome.business_action == "none"
    assert outcome.outcome_id == "call_connected"

    # Verify activity is completed
    updated = await service.get_session(session.id)
    completed = updated.activities[0]
    assert completed.is_completed
    assert completed.outcome_id == "call_connected"


@pytest.mark.asyncio
async def test_complete_activity_with_rule_trigger():
    repo = InMemoryActivityRepository()
    engine = ActivityRuleEngine()
    service = ActivityService(repo, rule_engine=engine)

    OutcomeCatalog.load_defaults()

    # Track what the rule engine triggers
    triggered = []

    async def advance_handler(outcome):
        triggered.append({
            "action": outcome.business_action,
            "target_id": outcome.target_id,
        })

    engine.on_outcome("advance_stage", advance_handler)

    session = await service.create_session("t1", "Meeting", "opp-1")
    activity = await service.add_activity(session.id, ActivityType.MEETING, "u1")

    outcome = await service.complete_activity(session.id, activity.id, "meeting_approved")
    assert outcome.business_action == "advance_stage"
    assert len(triggered) == 1
    assert triggered[0]["target_id"] == "opp-1"


@pytest.mark.asyncio
async def test_cannot_complete_twice():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)
    OutcomeCatalog.load_defaults()

    session = await service.create_session("t1", "Call", "opp-1")
    activity = await service.add_activity(session.id, ActivityType.CALL, "u1")
    await service.complete_activity(session.id, activity.id, "call_connected")

    with pytest.raises(ValueError, match="already completed"):
        await service.complete_activity(session.id, activity.id, "call_connected")


@pytest.mark.asyncio
async def test_invalid_outcome():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)
    OutcomeCatalog.load_defaults()

    session = await service.create_session("t1", "Call", "opp-1")
    activity = await service.add_activity(session.id, ActivityType.CALL, "u1")

    with pytest.raises(ValueError, match="not found in catalog"):
        await service.complete_activity(session.id, activity.id, "nonexistent")


# ── Queries ──

@pytest.mark.asyncio
async def test_query_sessions_by_target():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)

    await service.create_session("t1", "Visit", "opp-1")
    await service.create_session("t1", "Follow-up", "opp-2")
    await service.create_session("t1", "Call", "opp-1")

    sessions = await service.query_sessions(ActivitySessionQuery(target_id="opp-1"))
    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_get_activities_by_target():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)
    OutcomeCatalog.load_defaults()

    s1 = await service.create_session("t1", "Visit", "opp-1")
    await service.add_activity(s1.id, ActivityType.MEETING, "u1")
    await service.add_activity(s1.id, ActivityType.DEMO, "u1")

    s2 = await service.create_session("t1", "Call", "opp-2")
    await service.add_activity(s2.id, ActivityType.CALL, "u1")

    activities = await service.get_activities_by_target("opp-1", "opportunity")
    assert len(activities) == 2


# ── KPIs ──

@pytest.mark.asyncio
async def test_kpi_summary():
    repo = InMemoryActivityRepository()
    service = ActivityService(repo)
    OutcomeCatalog.load_defaults()

    # Create sessions with activities
    s1 = await service.create_session("t1", "Visit", "opp-1")
    a1 = await service.add_activity(s1.id, ActivityType.MEETING, "u1")
    await service.complete_activity(s1.id, a1.id, "meeting_completed")

    s2 = await service.create_session("t1", "Call", "opp-2")
    a2 = await service.add_activity(s2.id, ActivityType.CALL, "u1")
    await service.complete_activity(s2.id, a2.id, "call_qualified")

    kpis = await service.kpi_summary("t1")
    assert kpis["total_sessions"] == 2
    assert kpis["total_activities"] == 2
    assert kpis["completed_activities"] == 2
    assert kpis["activities_per_rep"] == 2.0


# ── Full Scenario: Meeting → Rule → Pipeline ──

@pytest.mark.asyncio
async def test_meeting_to_pipeline_scenario():
    """Simulate: Meeting → Outcome → Rule Engine → Pipeline progression."""
    repo = InMemoryActivityRepository()
    engine = ActivityRuleEngine()
    service = ActivityService(repo, rule_engine=engine)
    OutcomeCatalog.load_defaults()

    # Track pipeline actions
    pipeline_actions = []

    async def advance_stage_handler(outcome):
        pipeline_actions.append({
            "target": outcome.target_id,
            "action": "advance_stage",
            "source": outcome.activity_type.value,
            "outcome": outcome.outcome_label,
        })

    async def update_probability_handler(outcome):
        pipeline_actions.append({
            "target": outcome.target_id,
            "action": "update_probability",
            "delta": outcome.action_params.get("delta", 0),
            "source": outcome.activity_type.value,
        })

    engine.on_outcome("advance_stage", advance_stage_handler)
    engine.on_outcome("update_probability", update_probability_handler)

    # Scenario: Call → Qualified (probability +0.15)
    session = await service.create_session("t1", "Qualification Call", "opp-1")

    call = await service.add_activity(session.id, ActivityType.CALL, "u1")
    await service.complete_activity(session.id, call.id, "call_qualified")

    # Scenario: Meeting → Approved (advance stage)
    meeting = await service.add_activity(session.id, ActivityType.MEETING, "u1")
    await service.complete_activity(session.id, meeting.id, "meeting_approved")

    # Scenario: Demo → Interested (probability +0.1)
    demo = await service.add_activity(session.id, ActivityType.DEMO, "u1")
    await service.complete_activity(session.id, demo.id, "demo_interested")

    assert len(pipeline_actions) == 3
    assert pipeline_actions[0]["action"] == "update_probability"
    assert pipeline_actions[1]["action"] == "advance_stage"
    assert pipeline_actions[2]["action"] == "update_probability"
