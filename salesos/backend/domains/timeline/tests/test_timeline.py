"""Tests for Timeline Domain — models, repository, recorder."""

from datetime import datetime, timezone

import pytest

from domains.timeline.contracts.models import (
    ActivityOutcome,
    ActivityType,
    Actor,
    ActorType,
    Target,
    TimelineEvent,
)
from domains.timeline.contracts.repository import TimelineQuery, TimelineResult
from domains.timeline.engine.in_memory_repo import InMemoryTimelineRepository
from domains.timeline.engine.recorder import TimelineRecorder


# ── Tests ──


def test_create_actor():
    actor = Actor.user(user_id="user-1", name="أحمد")
    assert actor.id == "user-1"
    assert actor.type == ActorType.USER
    assert actor.name == "أحمد"


def test_create_actor_helpers():
    assert Actor.system().type == ActorType.SYSTEM
    assert Actor.ai_agent("agent-1").type == ActorType.AI_AGENT
    assert Actor.workflow("wf-1").type == ActorType.WORKFLOW
    assert Actor.integration("int-1").type == ActorType.INTEGRATION


def test_create_target():
    target = Target(id="company-1", type="company", label="شركة الأمل")
    assert target.id == "company-1"
    assert target.type == "company"
    assert target.label == "شركة الأمل"


def test_create_timeline_event():
    event = TimelineEvent(
        event_id="evt-1",
        actor=Actor.user("user-1"),
        activity=ActivityType.COMPANY_CREATED,
        target=Target(id="company-1", type="company"),
        metadata={"cr_number": "1234567890"},
        tenant_id="tenant-1",
    )
    assert event.event_id == "evt-1"
    assert event.activity == ActivityType.COMPANY_CREATED
    assert event.outcome == ActivityOutcome.SUCCESS
    assert event.metadata["cr_number"] == "1234567890"


@pytest.mark.asyncio
async def test_append_event():
    repo = InMemoryTimelineRepository()
    event = TimelineEvent(
        event_id="evt-1",
        actor=Actor.system(),
        activity=ActivityType.COMPANY_CREATED,
        target=Target(id="company-1", type="company"),
        tenant_id="tenant-1",
    )
    await repo.append(event)
    assert await repo.count("tenant-1") == 1


@pytest.mark.asyncio
async def test_query_by_target():
    repo = InMemoryTimelineRepository()

    for i in range(3):
        await repo.append(TimelineEvent(
            event_id=f"evt-{i}",
            actor=Actor.system(),
            activity=ActivityType.COMPANY_CREATED,
            target=Target(id=f"company-{i}", type="company"),
            tenant_id="tenant-1",
        ))

    result = await repo.get_by_target("company-0", "company")
    assert result.total == 1
    assert result.events[0].target.id == "company-0"


@pytest.mark.asyncio
async def test_query_by_actor():
    repo = InMemoryTimelineRepository()

    await repo.append(TimelineEvent(
        event_id="evt-1", actor=Actor.user("user-1"),
        activity=ActivityType.COMPANY_CREATED,
        target=Target(id="company-1", type="company"),
        tenant_id="tenant-1",
    ))
    await repo.append(TimelineEvent(
        event_id="evt-2", actor=Actor.user("user-2"),
        activity=ActivityType.COMPANY_CREATED,
        target=Target(id="company-2", type="company"),
        tenant_id="tenant-1",
    ))

    result = await repo.get_by_actor("user-1")
    assert result.total == 1


@pytest.mark.asyncio
async def test_query_with_filters():
    repo = InMemoryTimelineRepository()

    for i in range(5):
        await repo.append(TimelineEvent(
            event_id=f"evt-{i}",
            actor=Actor.system(),
            activity=ActivityType.COMPANY_CREATED if i < 3 else ActivityType.COMPANY_UPDATED,
            target=Target(id="company-1", type="company"),
            tenant_id="tenant-1",
        ))

    result = await repo.query(TimelineQuery(
        target_id="company-1",
        activity_types=["company.created"],
    ))
    assert result.total == 3
    assert len(result.events) == 3


@pytest.mark.asyncio
async def test_pagination():
    repo = InMemoryTimelineRepository()

    for i in range(10):
        await repo.append(TimelineEvent(
            event_id=f"evt-{i}",
            actor=Actor.system(),
            activity=ActivityType.COMPANY_CREATED,
            target=Target(id="company-1", type="company"),
            tenant_id="tenant-1",
        ))

    result = await repo.query(TimelineQuery(target_id="company-1", page=1, page_size=3))
    assert result.total == 10
    assert len(result.events) == 3


@pytest.mark.asyncio
async def test_timeline_recorder():
    repo = InMemoryTimelineRepository()
    recorder = TimelineRecorder(repo)

    event = await recorder.append(
        actor=Actor.user("user-1", name="أحمد"),
        activity=ActivityType.COMPANY_CREATED,
        target=Target(id="company-1", type="company", label="شركة الأمل"),
        metadata={"cr_number": "1234567890"},
        tenant_id="tenant-1",
    )

    assert event.event_id is not None
    assert event.actor.name == "أحمد"
    assert event.target.label == "شركة الأمل"

    count = await repo.count("tenant-1")
    assert count == 1


@pytest.mark.asyncio
async def test_recorder_handles_domain_event():
    repo = InMemoryTimelineRepository()
    recorder = TimelineRecorder(repo)

    await recorder.on_domain_event({
        "type": "company.created",
        "source": "salesos/company",
        "data": {
            "aggregate_id": "company-1",
            "aggregate_type": "company",
            "tenant_id": "tenant-1",
            "data": {"name_ar": "شركة الأمل", "cr_number": "1234567890"},
        },
    })

    count = await repo.count("tenant-1")
    assert count == 1

    result = await repo.get_by_target("company-1", "company")
    assert result.total == 1
    assert result.events[0].activity == ActivityType.COMPANY_CREATED


@pytest.mark.asyncio
async def test_immutability():
    """Timeline events should never be modified after creation."""
    repo = InMemoryTimelineRepository()
    recorder = TimelineRecorder(repo)

    event = await recorder.append(
        actor=Actor.system(),
        activity=ActivityType.COMPANY_CREATED,
        target=Target(id="company-1", type="company"),
        tenant_id="tenant-1",
    )

    # The event's timestamp should not change
    original_ts = event.timestamp

    # Simulate time passing
    import asyncio
    await asyncio.sleep(0.01)

    result = await repo.get_by_target("company-1", "company")
    assert result.events[0].timestamp == original_ts
