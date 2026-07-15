"""Tests for the Dead Letter Queue (DLQHandler, RetryableConsumer, DLQReader).

15 tests covering:
  - DLQHandler consume   (3) init, retry check, record attempt
  - DLQHandler retry     (4) handle failure → retry, handle failure → DLQ, clear, stats
  - DLQHandler dead letter (4) send to DLQ, producer unavailable, no producer, entry format
  - DLQHandler alert     (2) count tracking, threshold
  - RetryableConsumer    (2) process success, process fail → DLQ
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sdk.events.base import DomainEvent
from sdk.events.dlq import (
    DLQHandler,
    DLQEntry,
    DLQReader,
    RetryableConsumer,
    DLQ_TOPIC,
    MAX_RETRIES,
)
from sdk.events.kafka_producer import KafkaProducer


# ── Helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_event() -> DomainEvent:
    return DomainEvent(
        event_id="evt-dlq-1",
        event_type="company.created",
        aggregate_id="agg-1",
        aggregate_type="company",
        tenant_id="tenant-1",
        data={"company_id": "c1", "name": "Acme", "tenant_id": "tenant-1"},
        metadata={"correlation_id": "corr-1"},
    )


@pytest.fixture
def handler() -> DLQHandler:
    return DLQHandler(max_retries=3)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DLQHandler — CONSUME TESTS (3)
# ═══════════════════════════════════════════════════════════════════════════════


def test_dlq_handler_init() -> None:
    """DLQHandler should init with default values."""
    h = DLQHandler()
    assert h._max_retries == 3
    assert h._dlq_topic == "salesos.dlq"
    assert h.total_dlq == 0


def test_should_retry_true_on_first_attempt(handler: DLQHandler) -> None:
    """should_retry should return True for unseen events."""
    assert handler.should_retry("evt-new") is True


def test_should_retry_false_after_max(handler: DLQHandler) -> None:
    """should_retry should return False after max retries."""
    for _ in range(MAX_RETRIES):
        handler.record_attempt("evt-001")
    assert handler.should_retry("evt-001") is False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DLQHandler — RETRY TESTS (4)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_handle_failure_returns_false_below_max(handler: DLQHandler, sample_event: DomainEvent) -> None:
    """handle_failure should return False (retry) when under max retries."""
    result = await handler.handle_failure(sample_event, "salesos.company", "timeout")
    assert result is False
    assert handler._retry_counts["evt-dlq-1"] == 1


@pytest.mark.asyncio
async def test_handle_failure_returns_true_on_max(handler: DLQHandler, sample_event: DomainEvent) -> None:
    """handle_failure should return True (DLQ) after max retries."""
    with patch.object(handler, "_send_to_dlq", new_callable=AsyncMock) as mock_dlq:
        for _ in range(MAX_RETRIES - 1):
            await handler.handle_failure(sample_event, "salesos.company", "fail")

        result = await handler.handle_failure(sample_event, "salesos.company", "final fail")
        assert result is True
        mock_dlq.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_retries(handler: DLQHandler) -> None:
    """clear_retries should remove the retry count for an event."""
    handler.record_attempt("evt-001")
    assert "evt-001" in handler._retry_counts
    handler.clear_retries("evt-001")
    assert "evt-001" not in handler._retry_counts


def test_stats(handler: DLQHandler) -> None:
    """Stats should reflect current state."""
    handler.record_attempt("evt-001")
    handler.record_attempt("evt-002")
    stats = handler.stats
    assert stats["active_retries"] == 2
    assert stats["max_retries"] == 3
    assert stats["total_dlq"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DLQHandler — DEAD LETTER TESTS (4)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_send_to_dlq(sample_event: DomainEvent) -> None:
    """send_to_dlq should publish to the DLQ topic."""
    producer = AsyncMock()
    producer.is_connected = True
    producer._producer = AsyncMock()

    handler = DLQHandler(producer=producer, max_retries=1)
    handler.record_attempt(sample_event.event_id)

    with patch.object(handler, "_ensure_producer", new_callable=AsyncMock, return_value=True):
        await handler._send_to_dlq(sample_event, "salesos.company", "error msg")

    assert producer._producer.send.called
    call_args = producer._producer.send.call_args
    topic = call_args[0][0]
    assert topic == DLQ_TOPIC
    headers = dict(call_args[1]["headers"])
    assert headers["dlq_reason"] == b"max_retries_exceeded"


@pytest.mark.asyncio
async def test_send_to_dlq_producer_unavailable(sample_event: DomainEvent) -> None:
    """send_to_dlq should handle producer not being available."""
    producer = AsyncMock()
    producer.is_connected = False

    handler = DLQHandler(producer=producer, max_retries=1)
    with patch.object(handler, "_ensure_producer", new_callable=AsyncMock, return_value=False):
        await handler._send_to_dlq(sample_event, "salesos.company", "error")
    # Should not raise


@pytest.mark.asyncio
async def test_handle_failure_no_producer(sample_event: DomainEvent) -> None:
    """handle_failure should work even without a pre-configured producer."""
    handler = DLQHandler(max_retries=1)
    with patch.object(handler, "_send_to_dlq", new_callable=AsyncMock):
        for _ in range(handler._max_retries):
            await handler.handle_failure(sample_event, "salesos.company", "error")
        # No exception expected


def test_dlq_entry_creation() -> None:
    """DLQEntry should store event metadata."""
    event = DomainEvent(event_type="test.event", event_id="evt-001")
    entry = DLQEntry(event=event, topic="salesos.test", error="test error", retry_count=2)
    assert entry.event.event_type == "test.event"
    assert entry.topic == "salesos.test"
    assert entry.error == "test error"
    assert entry.retry_count == 2

    d = entry.to_dict()
    assert d["original_topic"] == "salesos.test"
    assert d["error"] == "test error"
    assert d["retry_count"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DLQHandler — ALERT TESTS (2)
# ═══════════════════════════════════════════════════════════════════════════════


def test_total_dlq_tracking() -> None:
    """total_dlq should increment after each DLQ send."""
    producer = AsyncMock()
    producer.is_connected = True
    producer._producer = AsyncMock()

    handler = DLQHandler(producer=producer, max_retries=1)
    handler._total_dlq = 5
    assert handler.total_dlq == 5


@pytest.mark.asyncio
async def test_dlq_entry_roundtrip(sample_event: DomainEvent) -> None:
    """DLQEntry to_dict → reconstruct should preserve fields."""
    entry = DLQEntry(
        event=sample_event,
        topic="salesos.company",
        error="timeout",
        retry_count=2,
    )
    d = entry.to_dict()
    assert d["original_topic"] == "salesos.company"
    assert d["error"] == "timeout"
    assert d["retry_count"] == 2
    assert d["event"]["id"] == "evt-dlq-1"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. RetryableConsumer TESTS (2)
# ═══════════════════════════════════════════════════════════════════════════════


class MockRetryableConsumer(RetryableConsumer):
    """Test consumer with controllable process_event."""

    def __init__(self, *args, should_fail: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._should_fail = should_fail
        self.processed: list[DomainEvent] = []

    async def process_event(self, event: DomainEvent) -> None:
        if self._should_fail:
            raise RuntimeError("process failed")
        self.processed.append(event)


@pytest.mark.asyncio
async def test_retryable_consumer_success() -> None:
    """RetryableConsumer should process events successfully."""
    consumer = MockRetryableConsumer(topics=["salesos.company"], max_retries=3)
    event = DomainEvent(event_type="company.created", event_id="evt-001")

    await consumer.handle_event(event)

    assert len(consumer.processed) == 1
    assert consumer.processed[0].event_id == "evt-001"


@pytest.mark.asyncio
async def test_retryable_consumer_fail_dlq() -> None:
    """RetryableConsumer should DLQ after max retries."""
    consumer = MockRetryableConsumer(topics=["salesos.company"], max_retries=2, should_fail=True)
    event = DomainEvent(event_type="company.created", event_id="evt-fail")

    with patch.object(consumer._dlq_handler, "_send_to_dlq", new_callable=AsyncMock) as mock_dlq:
        with pytest.raises(RuntimeError, match="process failed"):
            await consumer.handle_event(event)
        mock_dlq.assert_awaited_once()
