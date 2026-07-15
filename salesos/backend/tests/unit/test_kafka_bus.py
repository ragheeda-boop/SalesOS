"""Tests for KafkaEventBus with fallback to in-memory."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sdk.events.base import DomainEvent
from sdk.events.bus import EventBus, InMemoryEventBus
from sdk.events.kafka_bus import KafkaEventBus


@pytest.fixture
def event() -> DomainEvent:
    return DomainEvent(
        event_type="company.created",
        aggregate_id="agg-1",
        aggregate_type="company",
        tenant_id="tenant-1",
        data={"company_id": "c1", "name": "Acme", "tenant_id": "tenant-1"},
        metadata={"user_id": "user-1", "correlation_id": "corr-1"},
    )


# ── Fallback behaviour ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fallback_when_aiokafka_not_installed(event: DomainEvent) -> None:
    """When aiokafka is absent, the bus should publish via in-memory fallback."""

    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus.subscribe("company.created", handler)
    await bus.publish(event)

    assert len(results) == 1
    assert results[0].event_type == "company.created"


@pytest.mark.asyncio
async def test_fallback_is_idempotent(event: DomainEvent) -> None:
    """Calling publish multiple times via fallback should work."""
    count = 0

    async def handler(e: DomainEvent) -> None:
        nonlocal count
        count += 1

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus.subscribe("company.created", handler)

    for _ in range(3):
        await bus.publish(event)

    assert count == 3


@pytest.mark.asyncio
async def test_fallback_with_unsubscribe(event: DomainEvent) -> None:
    """unsubscribe should remove the handler from the in-memory fallback."""
    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus.subscribe("company.created", handler)
    await bus.publish(event)
    assert len(results) == 1

    bus.unsubscribe("company.created", handler)
    await bus.publish(event)
    assert len(results) == 1  # no second delivery


# ── EventBus interface compliance ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_implements_eventbus_interface() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    assert isinstance(bus, EventBus)


def test_subscribe_and_unsubscribe_arity() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")

    def handler(_e: DomainEvent) -> None:
        pass

    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)


# ── Wildcard subscription ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wildcard_subscription(event: DomainEvent) -> None:
    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus.subscribe("*", handler)
    await bus.publish(event)
    assert len(results) == 1


# ── Kafka producer integration ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_goes_through_kafka_producer(event: DomainEvent) -> None:
    """When Kafka is available, the bus should use the KafkaProducer."""
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus._kafka_available = True

    with patch.object(bus._producer, "publish", new_callable=AsyncMock, return_value=True) as mock_pub:
        with patch.object(bus, "_ensure_producer", new_callable=AsyncMock, return_value=True):
            await bus.publish(event)
            mock_pub.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_producer_failure_triggers_fallback(event: DomainEvent) -> None:
    """When the producer fails, the bus should fall to in-memory."""
    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus._kafka_available = True
    bus.subscribe("company.created", handler)

    with patch.object(bus._producer, "publish", new_callable=AsyncMock, return_value=False):
        await bus.publish(event)

    assert len(results) == 1  # delivered via fallback


# ── Schema validation for Wave 2 events ────────────────────────────────────


def test_opportunity_created_schema() -> None:
    from sdk.events.schemas import OpportunityCreated

    evt = OpportunityCreated(
        aggregate_id="opp-1",
        aggregate_type="opportunity",
        tenant_id="t-1",
        data={"name": "Big Deal", "value": 100000},
    )
    assert evt.event_type == "opportunity.created"
    assert evt.data["name"] == "Big Deal"


def test_opportunity_updated_schema() -> None:
    from sdk.events.schemas import OpportunityUpdated

    evt = OpportunityUpdated(
        aggregate_id="opp-1",
        aggregate_type="opportunity",
        tenant_id="t-1",
        data={"name": "Bigger Deal"},
    )
    assert evt.event_type == "opportunity.updated"


def test_opportunity_deleted_schema() -> None:
    from sdk.events.schemas import OpportunityDeleted

    evt = OpportunityDeleted(
        aggregate_id="opp-1",
        aggregate_type="opportunity",
        tenant_id="t-1",
    )
    assert evt.event_type == "opportunity.deleted"


def test_nba_generated_schema() -> None:
    from sdk.events.schemas import NBAGenerated

    evt = NBAGenerated(
        aggregate_id="opp-1",
        aggregate_type="opportunity",
        tenant_id="t-1",
        data={"action": "send_email", "priority": "high"},
    )
    assert evt.event_type == "nba.generated"


def test_nba_action_taken_schema() -> None:
    from sdk.events.schemas import NBAActionTaken

    evt = NBAActionTaken(
        aggregate_id="opp-1",
        aggregate_type="opportunity",
        tenant_id="t-1",
        data={"action": "send_email", "result": "completed"},
    )
    assert evt.event_type == "nba.action_taken"


def test_meeting_brief_generated_schema() -> None:
    from sdk.events.schemas import MeetingBriefGenerated

    evt = MeetingBriefGenerated(
        aggregate_id="m-1",
        aggregate_type="meeting",
        tenant_id="t-1",
        data={"summary": "..."},
    )
    assert evt.event_type == "meeting.brief_generated"


def test_meeting_completed_schema() -> None:
    from sdk.events.schemas import MeetingCompleted

    evt = MeetingCompleted(
        aggregate_id="m-1",
        aggregate_type="meeting",
        tenant_id="t-1",
        data={"duration_minutes": 45},
    )
    assert evt.event_type == "meeting.completed"


def test_email_analyzed_schema() -> None:
    from sdk.events.schemas import EmailAnalyzed

    evt = EmailAnalyzed(
        aggregate_id="e-1",
        aggregate_type="email",
        tenant_id="t-1",
        data={"sentiment": "positive"},
    )
    assert evt.event_type == "email.analyzed"


def test_pipeline_stage_changed_schema() -> None:
    from sdk.events.schemas import PipelineStageChanged

    evt = PipelineStageChanged(
        aggregate_id="pipeline-1",
        aggregate_type="pipeline",
        tenant_id="t-1",
        data={"from_stage": "lead", "to_stage": "qualified"},
    )
    assert evt.event_type == "pipeline.stage_changed"


# ── is_kafka_available property ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_is_kafka_available_untried() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    assert bus.is_kafka_available is None


@pytest.mark.asyncio
async def test_is_kafka_available_false_on_fallback(event: DomainEvent) -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    with patch.object(bus._producer, "start", new_callable=AsyncMock, return_value=False):
        await bus.publish(event)
    assert bus.is_kafka_available is False


@pytest.mark.asyncio
async def test_is_kafka_available_true_after_start(event: DomainEvent) -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus._kafka_available = True
    with patch.object(bus._producer, "publish", new_callable=AsyncMock, return_value=True):
        with patch.object(bus, "_ensure_producer", new_callable=AsyncMock, return_value=True):
            await bus.publish(event)
    assert bus.is_kafka_available is True


# ── Lifecycle: close ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_graceful() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    await bus.close()


@pytest.mark.asyncio
async def test_close_stops_producer() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    with patch.object(bus._producer, "close", new_callable=AsyncMock) as mock_close:
        await bus.close()
        mock_close.assert_awaited_once()


# ── InMemoryEventBus compliance ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_in_memory_unsubscribe() -> None:
    """InMemoryEventBus.unsubscribe should work correctly."""
    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = InMemoryEventBus()
    bus.subscribe("test.event", handler)
    await bus.publish(DomainEvent(event_type="test.event"))
    assert len(results) == 1

    bus.unsubscribe("test.event", handler)
    await bus.publish(DomainEvent(event_type="test.event"))
    assert len(results) == 1  # not incremented


@pytest.mark.asyncio
async def test_in_memory_unsubscribe_nonexistent() -> None:
    """unsubscribe on a handler that was never registered should not raise."""
    bus = InMemoryEventBus()

    async def handler(e: DomainEvent) -> None:
        pass

    bus.unsubscribe("test.event", handler)  # should not raise
    bus.unsubscribe("nonexistent", handler)  # should not raise
