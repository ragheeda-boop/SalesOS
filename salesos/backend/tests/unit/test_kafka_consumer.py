"""Tests for KafkaConsumerBase."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sdk.events.base import DomainEvent
from sdk.events.kafka_consumer import KafkaConsumerBase


class CollectingConsumer(KafkaConsumerBase):
    """Test consumer that collects received events."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events: list[DomainEvent] = []

    async def handle_event(self, event: DomainEvent) -> None:
        self.events.append(event)


class FailingConsumer(KafkaConsumerBase):
    """Test consumer that raises on every event."""

    async def handle_event(self, event: DomainEvent) -> None:
        msg = f"failed on {event.event_type}"
        raise RuntimeError(msg)


@pytest.fixture
def cloud_event_payload() -> dict:
    return {
        "specversion": "1.0",
        "id": "evt-001",
        "source": "salesos.company",
        "type": "company.created",
        "time": "2026-07-14T12:00:00+00:00",
        "datacontenttype": "application/json",
        "data": {
            "event_version": 1,
            "tenant_id": "t-1",
            "payload": {"company_id": "c-1", "name": "Acme", "tenant_id": "t-1"},
            "metadata": {"correlation_id": "corr-1"},
        },
    }


@pytest.fixture
def legacy_payload() -> dict:
    return {
        "event_id": "evt-002",
        "event_type": "company.updated",
        "event_version": 1,
        "aggregate_id": "agg-1",
        "aggregate_type": "company",
        "tenant_id": "t-1",
        "occurred_at": "2026-07-14T12:00:00+00:00",
        "data": {"company_id": "c-1", "name": "Acme Corp"},
        "metadata": {},
    }


def _make_msg(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.value = json.dumps(payload).encode("utf-8")
    return msg


# ── Deserialization ────────────────────────────────────────────────────────


def test_deserialize_cloud_events(cloud_event_payload: dict) -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    msg = _make_msg(cloud_event_payload)
    event = consumer._deserialize(msg)

    assert event is not None
    assert event.event_id == "evt-001"
    assert event.event_type == "company.created"
    assert event.tenant_id == "t-1"
    assert event.data == {"company_id": "c-1", "name": "Acme", "tenant_id": "t-1"}


def test_deserialize_legacy(legacy_payload: dict) -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    msg = _make_msg(legacy_payload)
    event = consumer._deserialize(msg)

    assert event is not None
    assert event.event_id == "evt-002"
    assert event.event_type == "company.updated"


def test_deserialize_invalid_json() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    msg = MagicMock()
    msg.value = b"not-json"

    assert consumer._deserialize(msg) is None


def test_deserialize_no_value() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    msg = MagicMock()
    msg.value = None

    assert consumer._deserialize(msg) is None


# ── Consumer lifecycle ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_no_topics() -> None:
    consumer = CollectingConsumer(topics=[])
    ok = await consumer.start()
    assert ok is False


@pytest.mark.asyncio
async def test_start_success() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    with patch("aiokafka.AIOKafkaConsumer", MagicMock()) as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        ok = await consumer.start()
        assert ok is True
        assert consumer.is_running is True
        mock_instance.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_import_error() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    with (
        patch.dict("sys.modules", {"aiokafka": None}),
        patch("builtins.__import__", side_effect=ImportError),
    ):  # noqa: E501
        ok = await consumer.start()
        assert ok is False
        assert consumer.is_running is False


@pytest.mark.asyncio
async def test_stop() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    with patch("aiokafka.AIOKafkaConsumer", MagicMock()) as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        await consumer.start()
        await consumer.stop()
        assert consumer.is_running is False
        mock_instance.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_without_start() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    await consumer.stop()  # should not raise


# ── Event handling ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_event_called(cloud_event_payload: dict) -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    msg = _make_msg(cloud_event_payload)
    event = consumer._deserialize(msg)
    assert event is not None

    await consumer.handle_event(event)
    assert len(consumer.events) == 1
    assert consumer.events[0].event_type == "company.created"


@pytest.mark.asyncio
async def test_consumer_metrics_recorded(cloud_event_payload: dict) -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    msg = _make_msg(cloud_event_payload)
    event = consumer._deserialize(msg)
    assert event is not None

    consumer._metrics.record_received(event.event_type)
    await consumer.handle_event(event)
    consumer._metrics.record_handled(event.event_type)

    snap = consumer.metrics.snapshot()
    assert snap["total_received"] == 1
    assert snap["total_handled"] == 1


@pytest.mark.asyncio
async def test_failing_consumer_records_error(cloud_event_payload: dict) -> None:
    consumer = FailingConsumer(topics=["salesos.company"])
    msg = _make_msg(cloud_event_payload)
    event = consumer._deserialize(msg)
    assert event is not None

    with pytest.raises(RuntimeError):
        await consumer.handle_event(event)

    consumer._metrics.record_received(event.event_type)
    consumer._metrics.record_handler_error(event.event_type)

    snap = consumer.metrics.snapshot()
    assert snap["by_type"]["company.created"]["handler_errors"] == 1


def test_metrics_empty_snapshot() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    snap = consumer.metrics.snapshot()
    assert snap["total_received"] == 0
    assert snap["total_handled"] == 0
    assert snap["total_handler_errors"] == 0
    assert snap["total_deserialization_errors"] == 0


# ── Subscribe ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_subscribe_updates_topics() -> None:
    consumer = CollectingConsumer(topics=["salesos.company"])
    with patch("aiokafka.AIOKafkaConsumer", MagicMock()) as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        await consumer.start()
        await consumer.subscribe(["salesos.company", "salesos.crm"])
        mock_instance.subscribe.assert_called_with(topics=["salesos.company", "salesos.crm"])
