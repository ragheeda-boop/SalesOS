"""OutboxRelay._deliver_one() double-serialized every message's value.

The real AIOKafkaProducer (constructed in kafka_producer.py) is configured
with `value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8")`.
aiokafka's own Producer._serialize() applies that serializer UNCONDITIONALLY
to whatever is passed as `value=` inside send() -- confirmed directly against
the installed aiokafka source (producer/producer.py:350-357).

_deliver_one() pre-encoded the payload itself
(`json.dumps(payload, default=str).encode("utf-8")`) before passing it as
`value=` -- so the configured serializer ran a SECOND time, on an already-bytes
object. `json.dumps(some_bytes, default=str)` cannot serialize bytes directly,
so its `default=str` fallback fires and serializes `str(some_bytes)` (the
Python repr of the bytes object) as a quoted JSON string. The bytes that
actually land on the Kafka topic are a JSON string containing the escaped
repr of the intended payload, not the payload itself -- any real consumer's
`json.loads()` would get back a bare string, not the original dict.

Reproduced directly with the exact aiokafka-installed serializer lambda,
without needing a live broker or the real aiokafka package at runtime for
this test -- the serializer function is the same one kafka_producer.py
constructs AIOKafkaProducer with.

Existing tests/unit/test_outbox.py::test_relay_publishes_pending_events only
asserted `producer._producer.send.called` -- it mocks `_producer` as an
AsyncMock, so no real serializer ever ran and the corruption was invisible.
This test inspects what would actually reach the wire.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from sdk.events.outbox import EventOutbox, OutboxEntry, OutboxRelay

# The exact value_serializer kafka_producer.py configures AIOKafkaProducer with.
REAL_VALUE_SERIALIZER = lambda v: json.dumps(v, default=str).encode("utf-8")  # noqa: E731


def _make_session_factory(session: MagicMock) -> MagicMock:
    factory = MagicMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    factory.return_value = ctx
    return factory


@pytest.fixture
def sample_entry() -> OutboxEntry:
    return OutboxEntry(
        id=7,
        event_id="evt-777",
        event_type="company.created",
        topic="salesos.company",
        key="agg-777",
        payload={"company_id": "c-777", "name": "Acme Corp", "amount": 12345},
        headers={"event_type": "company.created", "tenant_id": "t-1"},
        status="pending",
        retry_count=0,
    )


@pytest.mark.asyncio
async def test_deliver_one_value_survives_the_real_kafka_serializer(
    sample_entry: OutboxEntry,
) -> None:
    """The value _deliver_one() hands to send() must round-trip through the
    REAL configured value_serializer back to the original payload dict --
    proving no double-encoding happened."""
    session = MagicMock()
    outbox = EventOutbox(session=session)
    outbox.mark_delivered = AsyncMock()

    captured: dict = {}

    async def _fake_send(topic, value=None, headers=None, key=None):
        captured["topic"] = topic
        captured["value"] = value
        captured["headers"] = headers
        captured["key"] = key

    producer = AsyncMock()
    producer.is_connected = True
    producer._producer = AsyncMock()
    producer._producer.send = AsyncMock(side_effect=_fake_send)

    relay = OutboxRelay(_make_session_factory(session), producer=producer)

    await relay._deliver_one(session, outbox, sample_entry)

    assert outbox.mark_delivered.called, "delivery should have succeeded, not raised"

    # Simulate exactly what aiokafka's Producer._serialize() does: apply the
    # configured value_serializer UNCONDITIONALLY to whatever was passed.
    on_the_wire = REAL_VALUE_SERIALIZER(captured["value"])
    recovered = json.loads(on_the_wire)

    assert recovered == sample_entry.payload, (
        f"value was corrupted by double-serialization: expected the payload "
        f"dict to round-trip through the real Kafka value_serializer, got "
        f"{recovered!r} (type {type(recovered).__name__}) instead"
    )
