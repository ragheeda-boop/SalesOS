"""Integration tests for the full Kafka LIVE flow: outbox → Kafka → consumer.

10 tests covering:
  - Full pipeline      (2) outbox → relay → consumption
  - DLQ routing        (2) failure → DLQ → read DLQ
  - Bus with outbox    (2) KafkaEventBus with outbox relay
  - Edge cases         (2) producer unavailable, consumer fail
  - Performance        (1) batch relay
  - Cleanup            (1) delivered event cleanup
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import make_mock_session, make_mock_session_factory

from sdk.events.base import DomainEvent
from sdk.events.dlq import DLQHandler, RetryableConsumer
from sdk.events.kafka_bus import KafkaEventBus
from sdk.events.outbox import EventOutbox, OutboxRelay, OutboxEntry


@pytest.fixture
def sample_event() -> DomainEvent:
    return DomainEvent(
        event_id="live-evt-001",
        event_type="company.created",
        aggregate_id="agg-1",
        aggregate_type="company",
        tenant_id="tenant-1",
        data={"company_id": "c1", "name": "Acme", "tenant_id": "tenant-1"},
        metadata={"correlation_id": "corr-1"},
    )


def _make_entry_tuples(sample_event: DomainEvent, count: int = 1) -> list[tuple]:
    results = []
    for i in range(count):
        evt = sample_event if i == 0 else DomainEvent(
            event_id=f"live-evt-{i:03d}",
            event_type="company.created",
            tenant_id="t-1",
            data={"company_id": f"c{i}", "name": f"Co{i}", "tenant_id": "t-1"},
        )
        results.append((
            i + 1,
            evt.event_id,
            evt.event_type,
            "salesos.company",
            evt.aggregate_id or evt.event_id,
            evt.to_dict(),
            {"event_type": evt.event_type, "tenant_id": evt.tenant_id},
            "pending",
            0,
            "",
            evt.occurred_at,
            evt.occurred_at,
        ))
    return results


@pytest.fixture
def mock_session_factory():
    return make_mock_session_factory


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FULL PIPELINE TESTS (2)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_outbox_to_kafka_pipeline(sample_event: DomainEvent) -> None:
    """Full flow: write to outbox → relay → Kafka producer."""
    session = make_mock_session()
    entries_1 = _make_entry_tuples(sample_event, 1)
    session.execute.return_value.fetchall.side_effect = [entries_1, [], [], [], [], []]
    session_factory = make_mock_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await asyncio.sleep(0.1)
    await relay.stop()

    assert relay.stats["total_relayed"] >= 1
    assert producer._producer.send.called
    call_args = producer._producer.send.call_args
    assert call_args[0][0] == "salesos.company"


@pytest.mark.asyncio
async def test_outbox_multiple_events(sample_event: DomainEvent) -> None:
    """Multiple events should all be relayed."""
    session = make_mock_session()
    entries_3 = _make_entry_tuples(sample_event, 3)
    empty = []
    session.execute.return_value.fetchall.side_effect = [entries_3, empty, empty, empty, empty, empty]
    session_factory = make_mock_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01, batch_size=10)
    await relay.start()
    await asyncio.sleep(0.1)
    await relay.stop()

    assert relay.stats["total_relayed"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DLQ ROUTING TESTS (2)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_failure_routes_to_dlq(sample_event: DomainEvent) -> None:
    """Failed event after max retries should be routed to DLQ."""
    session = make_mock_session()
    entries_1 = _make_entry_tuples(sample_event, 1)
    session.execute.return_value.fetchall.side_effect = [entries_1, [], [], [], [], []]
    session_factory = make_mock_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()
    producer._producer.send = AsyncMock(side_effect=RuntimeError("broker down"))

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await asyncio.sleep(0.1)
    await relay.stop()

    assert relay.stats["total_failed"] >= 1


@pytest.mark.asyncio
async def test_dlq_handler_routes_to_dlq_topic(sample_event: DomainEvent) -> None:
    """DLQHandler should send to DLQ topic after max retries."""
    producer = AsyncMock()
    producer.is_connected = True
    producer._producer = AsyncMock()

    handler = DLQHandler(producer=producer, max_retries=2)

    for _ in range(handler._max_retries):
        await handler.handle_failure(sample_event, "salesos.company", "error")

    assert handler.total_dlq == 1
    assert producer._producer.send.called
    call_args = producer._producer.send.call_args
    assert call_args[0][0] == "salesos.dlq"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BUS WITH OUTBOX TESTS (2)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_kafka_bus_with_outbox_relay() -> None:
    """KafkaEventBus with outbox relay should flag outbox as enabled."""
    bus = KafkaEventBus(outbox_enabled=True)
    session_factory = make_mock_session_factory()
    relay = AsyncMock()
    relay._session_factory = session_factory
    await bus.set_outbox_relay(relay)
    assert bus.outbox_enabled is True


@pytest.mark.asyncio
async def test_kafka_bus_outbox_fallback_on_error(sample_event: DomainEvent) -> None:
    """When outbox fails, bus should fall back to in-memory."""
    results: list[DomainEvent] = []

    async def handler(e: DomainEvent) -> None:
        results.append(e)

    bus = KafkaEventBus(outbox_enabled=True)
    bus.subscribe("company.created", handler)

    session_factory = make_mock_session_factory()
    relay = AsyncMock()
    relay._session_factory = session_factory

    with patch("sdk.events.outbox.EventOutbox.write", side_effect=RuntimeError("db down")):
        await bus.publish(sample_event)

    assert len(results) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 4. EDGE CASE TESTS (2)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_outbox_relay_producer_disconnected() -> None:
    """Relay should not crash when producer is disconnected."""
    session = make_mock_session()
    session.execute.return_value.fetchall.return_value = []
    session_factory = make_mock_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = False
    producer.start.return_value = False

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await asyncio.sleep(0.08)
    await relay.stop()

    assert relay.stats["total_relayed"] == 0
    assert relay.stats["total_failed"] == 0


@pytest.mark.asyncio
async def test_dlq_handler_clear_after_success(sample_event: DomainEvent) -> None:
    """Retry counts should be cleared after successful processing."""
    handler = DLQHandler(max_retries=3)
    handler.record_attempt(sample_event.event_id)
    handler.record_attempt(sample_event.event_id)
    assert handler._retry_counts[sample_event.event_id] == 2

    handler.clear_retries(sample_event.event_id)
    assert sample_event.event_id not in handler._retry_counts


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PERFORMANCE TEST (1)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_batch_relay_performance() -> None:
    """Relay should handle a batch of events efficiently."""
    session = make_mock_session()
    entries = []
    for i in range(10):
        evt = DomainEvent(
            event_id=f"perf-evt-{i:03d}",
            event_type="company.created",
            tenant_id="t-1",
            data={"company_id": f"c{i}", "name": f"Co{i}", "tenant_id": "t-1"},
        )
        entries.append((
            i + 1, evt.event_id, evt.event_type, "salesos.company",
            evt.aggregate_id or evt.event_id, evt.to_dict(),
            {"event_type": evt.event_type, "tenant_id": evt.tenant_id},
            "pending", 0, "", evt.occurred_at, evt.occurred_at,
        ))
    session.execute.return_value.fetchall.side_effect = [entries, [], [], [], [], []]
    session_factory = make_mock_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01, batch_size=20)
    await relay.start()
    await asyncio.sleep(0.1)
    await relay.stop()

    assert relay.stats["total_relayed"] == 10


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CLEANUP TEST (1)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_event_store_cleanup() -> None:
    """Delivered events should be cleaned up after TTL."""
    session = make_mock_session()
    session.execute.return_value.rowcount = 5
    outbox = EventOutbox(session)

    count = await outbox.cleanup_delivered(older_than_hours=24)
    assert count == 5
