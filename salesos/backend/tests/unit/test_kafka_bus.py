"""Tests for KafkaEventBus with fallback to in-memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
        data={"name": "Acme"},
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
    assert results[0].data == {"name": "Acme"}


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


# ── Topic naming ───────────────────────────────────────────────────────────


def test_topic_naming() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    # The topic derivation is internal — verify it matches the convention
    event = DomainEvent(event_type="opportunity.created")
    # Publish through fallback (no kafka), just confirm no crash
    with patch.object(bus, "_fallback") as mock_fb:
        mock_fb.publish = AsyncMock()
        bus.subscribe("opportunity.created", lambda e: None)

        import asyncio
        asyncio.run(bus.publish(event))
        mock_fb.publish.assert_called_once()


# ── Kafka producer with mock ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_with_mock_producer(event: DomainEvent) -> None:
    """When aiokafka IS available, the producer should be called."""
    mock_producer = AsyncMock()
    mock_producer.send = AsyncMock()

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus._producer = mock_producer  # inject directly, skip _start_producer
    bus._kafka_available = True

    await bus.publish(event)

    expected_topic = "salesos.company.created"
    expected_value = event.to_dict()
    expected_headers = [
        ("tenant_id", b"tenant-1"),
        ("event_type", b"company.created"),
        ("user_id", b"user-1"),
        ("correlation_id", b"corr-1"),
    ]

    mock_producer.send.assert_called_once_with(
        expected_topic,
        value=expected_value,
        headers=expected_headers,
    )


@pytest.mark.asyncio
async def test_producer_failure_triggers_fallback(event: DomainEvent) -> None:
    """When the producer raises, the bus should fall to in-memory."""
    mock_producer = AsyncMock()
    mock_producer.send = AsyncMock(side_effect=RuntimeError("broker down"))

    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus._producer = mock_producer
    bus._kafka_available = True
    bus.subscribe("company.created", handler)

    await bus.publish(event)

    assert len(results) == 1  # delivered via fallback


# ── Deserialization (handling incoming Kafka messages) ─────────────────────


def test_deserialize_cloudevents() -> None:
    """Should parse CloudEvents 1.0 format."""
    payload = {
        "specversion": "1.0",
        "id": "evt-1",
        "source": "salesos.company",
        "type": "company.created",
        "time": "2026-07-11T12:00:00+00:00",
        "data": {
            "tenant_id": "t-1",
            "payload": {"name": "Acme"},
            "metadata": {"correlation_id": "c-1"},
        },
    }

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    msg = MagicMock()
    msg.value = json.dumps(payload).encode("utf-8")

    event = bus._deserialize(msg)
    assert event is not None
    assert event.event_id == "evt-1"
    assert event.event_type == "company.created"
    assert event.data == {"name": "Acme"}
    assert event.metadata == {"correlation_id": "c-1"}
    assert event.tenant_id == "t-1"


def test_deserialize_legacy() -> None:
    """Should parse the legacy (non-CloudEvents) format."""
    payload = {
        "event_id": "evt-2",
        "event_type": "company.updated",
        "aggregate_id": "agg-1",
        "aggregate_type": "company",
        "tenant_id": "t-1",
        "occurred_at": "2026-07-11T12:00:00+00:00",
        "data": {"field": "name"},
        "metadata": {},
    }

    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    msg = MagicMock()
    msg.value = json.dumps(payload).encode("utf-8")

    event = bus._deserialize(msg)
    assert event is not None
    assert event.event_id == "evt-2"
    assert event.event_type == "company.updated"
    assert event.data == {"field": "name"}


def test_deserialize_invalid_json() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    msg = MagicMock()
    msg.value = b"not-json"

    assert bus._deserialize(msg) is None


def test_deserialize_no_value() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    msg = MagicMock()
    msg.value = None

    assert bus._deserialize(msg) is None


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
async def test_is_kafka_available_false_on_fallback() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    await bus.publish(DomainEvent(event_type="test.event"))
    assert bus.is_kafka_available is False


@pytest.mark.asyncio
async def test_is_kafka_available_true_with_mock(event: DomainEvent) -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    bus._producer = AsyncMock()
    bus._kafka_available = True
    assert bus.is_kafka_available is True


# ── Lifecycle: close ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_graceful() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    # Should not raise even without a producer
    await bus.close()


@pytest.mark.asyncio
async def test_close_stops_producer() -> None:
    bus = KafkaEventBus(bootstrap_servers="localhost:9092")
    mock_producer = AsyncMock()
    bus._producer = mock_producer
    await bus.close()
    mock_producer.stop.assert_awaited_once()


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
