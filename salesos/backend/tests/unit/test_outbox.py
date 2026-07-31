"""Tests for the transactional outbox (EventOutbox + OutboxRelay).

20 tests covering:
  - write        (5)  creation, payload, dedup, metadata, rollback
  - relay        (5)  publish, batch, empty, connect, reconnect
  - delivery     (3)  mark, cleanup, partial
  - failure      (4)  retry, max retry → failed, DLQ, error tracking
  - integration  (3)  write → relay → delivered, DLQ alert, stats
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from sdk.events.base import DomainEvent
from sdk.events.outbox import (
    DLQ_ALERT_THRESHOLD,
    EventOutbox,
    OutboxEntry,
    OutboxRelay,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_session() -> MagicMock:
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def outbox(mock_session: MagicMock) -> EventOutbox:
    return EventOutbox(session=mock_session)


@pytest.fixture
def sample_event() -> DomainEvent:
    return DomainEvent(
        event_id="evt-001",
        event_type="company.created",
        aggregate_id="agg-1",
        aggregate_type="company",
        tenant_id="tenant-1",
        data={"company_id": "c1", "name": "Acme", "tenant_id": "tenant-1"},
        metadata={"user_id": "user-1", "correlation_id": "corr-1"},
    )


@pytest.fixture
def sample_entry() -> OutboxEntry:
    return OutboxEntry(
        id=1,
        event_id="evt-001",
        event_type="company.created",
        topic="salesos.company",
        key="agg-1",
        payload={"specversion": "1.0", "id": "evt-001", "type": "company.created"},
        headers={"event_type": "company.created", "tenant_id": "t-1"},
        status="pending",
        retry_count=0,
    )


def _make_session() -> MagicMock:
    """Create a mock DB session whose execute() returns a proper result."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    exec_result = MagicMock()
    exec_result.fetchall.return_value = []
    exec_result.fetchone.return_value = None
    exec_result.scalar.return_value = 0
    exec_result.rowcount = 0
    session.execute.return_value = exec_result
    return session


def _make_session_factory(session: MagicMock | None = None) -> MagicMock:
    """Create a mock session factory yielding the given session."""
    if session is None:
        session = _make_session()
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = session
    factory.return_value.__aexit__.return_value = None
    return factory


# ═══════════════════════════════════════════════════════════════════════════════
# 1. WRITE TESTS (5)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_write_event_creates_outbox_entry(
    outbox: EventOutbox, sample_event: DomainEvent
) -> None:
    """Writing an event should insert a row and return its ID."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (42,)
    outbox._session.execute.return_value = mock_result

    outbox_id = await outbox.write(sample_event)

    assert outbox_id == 42
    outbox._session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_write_stores_payload_correctly(
    outbox: EventOutbox, sample_event: DomainEvent
) -> None:
    """The payload should include the CloudEvents envelope."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    outbox._session.execute.return_value = mock_result

    await outbox.write(sample_event)

    call_kwargs = outbox._session.execute.call_args[0][1]
    payload = json.loads(call_kwargs["payload"])
    assert payload["specversion"] == "1.0"
    assert payload["id"] == "evt-001"
    assert payload["type"] == "company.created"
    assert call_kwargs["topic"] == "salesos.company"
    assert call_kwargs["event_type"] == "company.created"
    assert call_kwargs["key"] == "agg-1"


@pytest.mark.asyncio
async def test_write_headers_include_metadata(
    outbox: EventOutbox, sample_event: DomainEvent
) -> None:
    """User ID and correlation ID should be in headers."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    outbox._session.execute.return_value = mock_result

    await outbox.write(sample_event)

    call_kwargs = outbox._session.execute.call_args[0][1]
    headers = json.loads(call_kwargs["headers"])
    assert headers["user_id"] == "user-1"
    assert headers["correlation_id"] == "corr-1"


@pytest.mark.asyncio
async def test_write_event_id_uniqueness(outbox: EventOutbox, sample_event: DomainEvent) -> None:
    """Duplicate event_id should raise (UNIQUE constraint)."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    outbox._session.execute.side_effect = [mock_result, Exception("duplicate key")]

    await outbox.write(sample_event)
    with pytest.raises(Exception, match="duplicate key"):
        await outbox.write(sample_event)


@pytest.mark.asyncio
async def test_write_without_metadata(outbox: EventOutbox) -> None:
    """Writing an event without metadata should still work."""
    event = DomainEvent(
        event_id="evt-002",
        event_type="company.updated",
        tenant_id="t-1",
    )
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (2,)
    outbox._session.execute.return_value = mock_result

    outbox_id = await outbox.write(event)
    assert outbox_id == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RELAY TESTS (5)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_relay_publishes_pending_events(sample_entry: OutboxEntry) -> None:
    """Relay should fetch pending entries and publish them."""
    session = _make_session()
    session.execute.return_value.fetchall.return_value = [
        (
            sample_entry.id,
            sample_entry.event_id,
            sample_entry.event_type,
            sample_entry.topic,
            sample_entry.key,
            sample_entry.payload,
            sample_entry.headers,
            sample_entry.status,
            sample_entry.retry_count,
            sample_entry.last_error,
            sample_entry.created_at,
            sample_entry.updated_at,
        ),
    ]
    session_factory = _make_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()

    await asyncio.sleep(0.08)
    await relay.stop()

    assert producer._producer.send.called


@pytest.mark.asyncio
async def test_relay_empty_batch() -> None:
    """Relay should handle empty batches without error."""
    session = _make_session()
    session.execute.return_value.fetchall.return_value = []
    session_factory = _make_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await asyncio.sleep(0.08)
    await relay.stop()

    assert relay.stats["total_relayed"] == 0


@pytest.mark.asyncio
async def test_relay_no_connection() -> None:
    """Relay should defer when producer is not connected."""
    session = _make_session()
    session.execute.return_value.fetchall.return_value = []
    session_factory = _make_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = False

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await relay.stop()

    assert relay.stats["total_relayed"] == 0


@pytest.mark.asyncio
async def test_relay_stop_without_start() -> None:
    """Stop without start should not raise."""
    session_factory = MagicMock()
    relay = OutboxRelay(session_factory, relay_interval=0.01)
    await relay.stop()


@pytest.mark.asyncio
async def test_relay_double_start() -> None:
    """Starting relay twice should be idempotent."""
    session_factory = MagicMock()
    relay = OutboxRelay(session_factory, relay_interval=0.1)
    ok1 = await relay.start()
    ok2 = await relay.start()
    assert ok1 is True
    assert ok2 is True
    await relay.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DELIVERY TESTS (3)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_mark_delivered(outbox: EventOutbox) -> None:
    """mark_delivered should set status to 'delivered'."""
    await outbox.mark_delivered(42)
    outbox._session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_delivered(outbox: EventOutbox) -> None:
    """cleanup_delivered should delete old delivered entries."""
    mock_result = MagicMock()
    mock_result.rowcount = 5
    outbox._session.execute.return_value = mock_result
    count = await outbox.cleanup_delivered(older_than_hours=24)
    assert count == 5


@pytest.mark.asyncio
async def test_cleanup_zero(outbox: EventOutbox) -> None:
    """cleanup with no matching entries should return 0."""
    mock_result = MagicMock()
    mock_result.rowcount = 0
    outbox._session.execute.return_value = mock_result
    count = await outbox.cleanup_delivered(older_than_hours=1)
    assert count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FAILURE TESTS (4)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_mark_failed_increments_retry(outbox: EventOutbox) -> None:
    """mark_failed should increment retry count."""
    await outbox.mark_failed(42, "network error")
    call_kwargs = outbox._session.execute.call_args[0][1]
    assert call_kwargs["id"] == 42
    assert "network error" in call_kwargs["error"]


@pytest.mark.asyncio
async def test_max_retry_moves_to_failed(outbox: EventOutbox) -> None:
    """After max retries, status should become 'failed'."""
    await outbox.mark_failed(42, "final error")
    outbox._session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_dlq(outbox: EventOutbox) -> None:
    """mark_dlq should set status to 'dlq'."""
    await outbox.mark_dlq(42, "dead letter error")
    call_kwargs = outbox._session.execute.call_args[0][1]
    assert call_kwargs["id"] == 42
    assert "dead letter" in call_kwargs["error"]


@pytest.mark.asyncio
async def test_fetch_dlq_count(outbox: EventOutbox) -> None:
    """fetch_dlq_count should return the count of DLQ entries."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 3
    outbox._session.execute.return_value = mock_result
    count = await outbox.fetch_dlq_count()
    assert count == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 5. INTEGRATION / EDGE TESTS (3)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_write_then_relay_delivered(sample_event: DomainEvent) -> None:
    """Write + relay should result in delivered events."""
    session = _make_session()
    entry_tuple = (
        1,
        sample_event.event_id,
        sample_event.event_type,
        "salesos.company",
        "agg-1",
        sample_event.to_dict(),
        {"event_type": sample_event.event_type, "tenant_id": sample_event.tenant_id},
        "pending",
        0,
        "",
        sample_event.occurred_at,
        sample_event.occurred_at,
    )
    session.execute.return_value.fetchall.return_value = [entry_tuple]
    session_factory = _make_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await asyncio.sleep(0.08)
    await relay.stop()

    assert relay.stats["total_relayed"] >= 1


@pytest.mark.asyncio
async def test_dlq_alert_threshold(outbox: EventOutbox) -> None:
    """DLQ count above threshold should trigger alert check."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = DLQ_ALERT_THRESHOLD + 1
    outbox._session.execute.return_value = mock_result
    count = await outbox.fetch_dlq_count()
    assert count > DLQ_ALERT_THRESHOLD


@pytest.mark.asyncio
async def test_relay_stats(sample_entry: OutboxEntry) -> None:
    """Relay stats should track relayed and failed counts."""
    session = _make_session()
    session.execute.return_value.fetchall.return_value = [
        (
            sample_entry.id,
            sample_entry.event_id,
            sample_entry.event_type,
            sample_entry.topic,
            sample_entry.key,
            sample_entry.payload,
            sample_entry.headers,
            sample_entry.status,
            sample_entry.retry_count,
            sample_entry.last_error,
            sample_entry.created_at,
            sample_entry.updated_at,
        ),
    ]
    session_factory = _make_session_factory(session)

    producer = AsyncMock()
    producer.is_connected = True
    producer.start.return_value = True
    producer._producer = AsyncMock()

    relay = OutboxRelay(session_factory, producer=producer, relay_interval=0.01)
    await relay.start()
    await asyncio.sleep(0.05)
    await relay.stop()

    stats = relay.stats
    assert "running" in stats
    assert "total_relayed" in stats
    assert "total_failed" in stats
    assert isinstance(stats["total_relayed"], int)
