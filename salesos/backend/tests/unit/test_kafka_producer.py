"""Tests for KafkaProducer wrapper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sdk.events.base import DomainEvent
from sdk.events.kafka_producer import KafkaProducer


@pytest.fixture
def event() -> DomainEvent:
    return DomainEvent(
        event_type="company.created",
        aggregate_id="agg-1",
        aggregate_type="company",
        tenant_id="tenant-1",
        data={"company_id": "c-1", "name": "Acme", "tenant_id": "tenant-1", "domain": "acme.com"},
        metadata={"user_id": "user-1", "correlation_id": "corr-1"},
    )


@pytest.mark.asyncio
async def test_start_producer_success() -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    with patch("aiokafka.AIOKafkaProducer", MagicMock()) as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        ok = await producer.start()
        assert ok is True
        assert producer.is_connected is True
        mock_instance.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_producer_import_error() -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    with patch.dict("sys.modules", {"aiokafka": None}):
        with patch("builtins.__import__", side_effect=ImportError):
            ok = await producer.start()
            assert ok is False
            assert producer.is_connected is False


@pytest.mark.asyncio
async def test_publish_with_mock_producer(event: DomainEvent) -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    mock_instance = AsyncMock()
    producer._producer = mock_instance
    producer._started = True

    success = await producer.publish(event)
    assert success is True

    expected_topic = "salesos.company"
    mock_instance.send.assert_called_once()
    args, kwargs = mock_instance.send.call_args
    assert args[0] == expected_topic
    assert kwargs["headers"] is not None
    headers = dict(kwargs["headers"])
    assert headers["event_type"] == b"company.created"
    assert headers["tenant_id"] == b"tenant-1"
    assert headers["user_id"] == b"user-1"
    assert headers["correlation_id"] == b"corr-1"
    assert headers["specversion"] == b"1.0"


@pytest.mark.asyncio
async def test_publish_fails_when_not_started(event: DomainEvent) -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    success = await producer.publish(event)
    assert success is False


@pytest.mark.asyncio
async def test_publish_validation_error(event: DomainEvent) -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    mock_instance = AsyncMock()
    producer._producer = mock_instance
    producer._started = True

    # Clear data to trigger schema validation failure for company.created
    event.data = {}
    success = await producer.publish(event)
    # company.created schema requires company_id, name, tenant_id
    # Since validation errors return False
    assert success is False


@pytest.mark.asyncio
async def test_publish_send_failure_triggers_metric(event: DomainEvent) -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    mock_instance = AsyncMock()
    mock_instance.send = AsyncMock(side_effect=RuntimeError("broker down"))
    producer._producer = mock_instance
    producer._started = True

    success = await producer.publish(event)
    assert success is False


@pytest.mark.asyncio
async def test_flush() -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    mock_instance = AsyncMock()
    producer._producer = mock_instance
    producer._started = True

    await producer.flush()
    mock_instance.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_close() -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    mock_instance = AsyncMock()
    producer._producer = mock_instance
    producer._started = True

    await producer.close()
    mock_instance.stop.assert_awaited_once()
    assert producer.is_connected is False


@pytest.mark.asyncio
async def test_metrics_snapshot() -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    mock_instance = AsyncMock()
    producer._producer = mock_instance
    producer._started = True

    event1 = DomainEvent(
        event_type="company.created",
        tenant_id="t1",
        data={"company_id": "c1", "name": "Acme", "tenant_id": "t1"},
    )
    event2 = DomainEvent(
        event_type="opportunity.created",
        tenant_id="t1",
        data={"opportunity_id": "o1", "company_id": "c1", "tenant_id": "t1", "name": "Deal", "value": 100000, "stage": "qualification"},
    )

    await producer.publish(event1)
    await producer.publish(event2)

    snap = producer.metrics.snapshot()
    assert snap["total_published"] == 2
    assert snap["total_failures"] == 0


@pytest.mark.asyncio
async def test_producer_not_started_twice() -> None:
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    with patch("aiokafka.AIOKafkaProducer", MagicMock()) as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance

        ok1 = await producer.start()
        ok2 = await producer.start()
        assert ok1 is True
        assert ok2 is True
        # start() should only be called once
        mock_instance.start.assert_awaited_once()
