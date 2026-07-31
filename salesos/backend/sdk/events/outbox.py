"""Transactional Outbox Pattern for reliable Kafka delivery.

The outbox pattern ensures at-least-once delivery by storing events
in a PostgreSQL table within the same transaction as the business data.
A background relay then publishes outboxed events to Kafka.

Flow:
  1. Business transaction writes data + event to ``event_outbox`` table
  2. ``OutboxRelay`` polls outbox for pending events
  3. Relay publishes each event to Kafka via ``KafkaProducer``
  4. On success: marks event as ``delivered``
  5. On failure: increments ``retry_count``; moves to DLQ after max retries
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sdk.events.base import DomainEvent
from sdk.events.kafka_producer import KafkaProducer
from sdk.events.topic_mapping import event_type_to_topic

logger = logging.getLogger(__name__)

OUTBOX_TABLE = "event_outbox"
MAX_RETRY_COUNT = 3
DEFAULT_RELAY_INTERVAL = 1.0  # seconds
DLQ_TOPIC = "salesos.dlq"
DLQ_ALERT_THRESHOLD = 1000

OUTBOX_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS {OUTBOX_TABLE} (
    id              BIGSERIAL PRIMARY KEY,
    event_id        VARCHAR(64) NOT NULL UNIQUE,
    event_type      VARCHAR(128) NOT NULL,
    topic           VARCHAR(128) NOT NULL,
    key             VARCHAR(128),
    payload         JSONB NOT NULL,
    headers         JSONB NOT NULL DEFAULT '{{}}',
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    retry_count     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outbox_status_created
    ON {OUTBOX_TABLE} (status, created_at);
"""


@dataclass
class OutboxEntry:
    id: int = 0
    event_id: str = ""
    event_type: str = ""
    topic: str = ""
    key: str = ""
    payload: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    status: str = "pending"
    retry_count: int = 0
    last_error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventOutbox:
    """Transactional outbox — stores domain events temporarily before Kafka delivery.

    Use ``write()`` inside the same DB session as your business transaction.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def ensure_table(self) -> None:
        """Create the outbox table if it does not exist."""
        await self._session.execute(text(OUTBOX_CREATE_SQL))
        await self._session.commit()

    async def write(self, event: DomainEvent) -> int:
        """Write an event to the outbox within the current transaction.

        Returns the outbox row ID.
        """
        topic = event_type_to_topic(event.event_type)
        payload = event.to_dict()
        headers = {
            "event_type": event.event_type,
            "tenant_id": event.tenant_id or "",
            "event_id": event.event_id,
            "specversion": "1.0",
        }
        if event.metadata:
            uid = event.metadata.get("user_id")
            if uid is not None:
                headers["user_id"] = str(uid)
            cid = event.metadata.get("correlation_id")
            if cid is not None:
                headers["correlation_id"] = str(cid)

        stmt = text(f"""
            INSERT INTO {OUTBOX_TABLE}
                (event_id, event_type, topic, key, payload, headers)
            VALUES
                (:event_id, :event_type, :topic, :key, :payload::jsonb, :headers::jsonb)
            RETURNING id
        """)
        result = await self._session.execute(
            stmt,
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "topic": topic,
                "key": event.aggregate_id or event.event_id,
                "payload": json.dumps(payload),
                "headers": json.dumps(headers),
            },
        )
        row = result.fetchone()
        outbox_id = row[0] if row else 0
        logger.debug(
            "Outbox entry %d for event %s (%s)", outbox_id, event.event_id, event.event_type
        )
        return outbox_id

    async def mark_delivered(self, outbox_id: int) -> None:
        """Mark an outbox entry as delivered to Kafka."""
        stmt = text(f"""
            UPDATE {OUTBOX_TABLE}
            SET status = 'delivered', updated_at = NOW()
            WHERE id = :id
        """)
        await self._session.execute(stmt, {"id": outbox_id})

    async def mark_failed(self, outbox_id: int, error: str) -> None:
        """Increment retry count; mark as failed if max retries exceeded."""
        stmt = text(f"""
            UPDATE {OUTBOX_TABLE}
            SET status = CASE
                    WHEN retry_count + 1 >= :max_retry THEN 'failed'
                    ELSE 'pending'
                END,
                retry_count = retry_count + 1,
                last_error = :error,
                updated_at = NOW()
            WHERE id = :id
        """)
        await self._session.execute(
            stmt,
            {"id": outbox_id, "max_retry": MAX_RETRY_COUNT, "error": error},
        )

    async def mark_dlq(self, outbox_id: int, error: str) -> None:
        """Mark an entry as dead-lettered after exhausting retries."""
        stmt = text(f"""
            UPDATE {OUTBOX_TABLE}
            SET status = 'dlq', last_error = :error, updated_at = NOW()
            WHERE id = :id
        """)
        await self._session.execute(stmt, {"id": outbox_id, "error": error})

    async def fetch_pending(self, batch_size: int = 50) -> list[OutboxEntry]:
        """Fetch pending outbox entries ordered by creation time."""
        stmt = text(f"""
            SELECT id, event_id, event_type, topic, key, payload, headers,
                   status, retry_count, last_error, created_at, updated_at
            FROM {OUTBOX_TABLE}
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        """)
        result = await self._session.execute(stmt, {"limit": batch_size})
        return [self._row_to_entry(row) for row in result.fetchall()]

    async def fetch_dlq_count(self) -> int:
        """Count entries in dead letter queue."""
        stmt = text(f"SELECT COUNT(*) FROM {OUTBOX_TABLE} WHERE status = 'dlq'")
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def cleanup_delivered(self, older_than_hours: int = 24) -> int:
        """Delete delivered entries older than the given threshold."""
        stmt = text(f"""
            DELETE FROM {OUTBOX_TABLE}
            WHERE status = 'delivered'
              AND updated_at < NOW() - (:hours || ' hours')::interval
        """)
        result = await self._session.execute(stmt, {"hours": str(older_than_hours)})
        deleted = result.rowcount
        if deleted:
            logger.info("Cleaned up %d delivered outbox entries", deleted)
        return deleted

    def _row_to_entry(self, row) -> OutboxEntry:
        return OutboxEntry(
            id=row[0],
            event_id=row[1],
            event_type=row[2],
            topic=row[3],
            key=row[4] or "",
            payload=row[5] if isinstance(row[5], dict) else json.loads(row[5]),
            headers=row[6] if isinstance(row[6], dict) else json.loads(row[6]),
            status=row[7],
            retry_count=row[8],
            last_error=row[9] or "",
            created_at=row[10],
            updated_at=row[11],
        )


class OutboxRelay:
    """Background relay that polls the outbox and publishes to Kafka.

    Usage::

        relay = OutboxRelay(session_factory)
        await relay.start()      # runs in background task
        # ...
        await relay.stop()
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        producer: KafkaProducer | None = None,
        relay_interval: float = DEFAULT_RELAY_INTERVAL,
        batch_size: int = 50,
    ):
        self._session_factory = session_factory
        self._producer = producer or KafkaProducer()
        self._interval = relay_interval
        self._batch_size = batch_size
        self._running = False
        self._task: asyncio.Task | None = None
        self._total_relayed: int = 0
        self._total_failed: int = 0
        self._dlq_count: int = 0

    async def start(self) -> bool:
        """Start the relay background task."""
        if self._running:
            return True
        self._running = True
        ok = await self._producer.start()
        if not ok:
            logger.warning("OutboxRelay: Kafka producer unavailable — relay in standby")
        self._task = asyncio.create_task(self._relay_loop())
        logger.info(
            "OutboxRelay started (interval=%ss, batch=%d)", self._interval, self._batch_size
        )
        return True

    async def stop(self) -> None:
        """Stop the relay gracefully."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        await self._producer.close()
        logger.info(
            "OutboxRelay stopped (relayed=%d, failed=%d)", self._total_relayed, self._total_failed
        )

    async def _relay_loop(self) -> None:
        """Main loop: poll outbox → publish to Kafka."""
        while self._running:
            try:
                await self._relay_batch()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("OutboxRelay: error in relay cycle")
            await asyncio.sleep(self._interval)

    async def _relay_batch(self) -> None:
        """Fetch one batch of pending events and publish them."""
        async with self._session_factory() as session:
            outbox = EventOutbox(session)
            entries = await outbox.fetch_pending(self._batch_size)
            if not entries:
                return

            for entry in entries:
                await self._deliver_one(session, outbox, entry)

            await session.commit()

    async def _deliver_one(
        self, session: AsyncSession, outbox: EventOutbox, entry: OutboxEntry
    ) -> None:
        """Publish a single outbox entry to Kafka."""
        if not self._producer.is_connected:
            logger.warning("OutboxRelay: producer not connected, deferring entry %d", entry.id)
            return

        try:
            payload = entry.payload
            topic = entry.topic

            if entry.headers:
                event_type = entry.headers.get("event_type", entry.event_type)
            else:
                event_type = entry.event_type

            headers: list[tuple[str, bytes]] = [
                ("event_type", event_type.encode("utf-8")),
                ("tenant_id", (entry.headers.get("tenant_id", "")).encode("utf-8")),
                ("event_id", entry.event_id.encode("utf-8")),
                ("specversion", b"1.0"),
            ]
            uid = entry.headers.get("user_id")
            if uid:
                headers.append(("user_id", str(uid).encode("utf-8")))
            cid = entry.headers.get("correlation_id")
            if cid:
                headers.append(("correlation_id", str(cid).encode("utf-8")))

            await self._producer._producer.send(
                topic,
                value=json.dumps(payload, default=str).encode("utf-8"),
                headers=headers,
                key=entry.key.encode("utf-8") if entry.key else None,
            )

            await outbox.mark_delivered(entry.id)
            self._total_relayed += 1

        except Exception as exc:
            error = str(exc)
            logger.warning("OutboxRelay: failed to deliver entry %d: %s", entry.id, error)
            self._total_failed += 1

            if entry.retry_count + 1 >= MAX_RETRY_COUNT:
                await outbox.mark_dlq(entry.id, error)
                logger.error(
                    "OutboxRelay: entry %d moved to DLQ after %d retries", entry.id, MAX_RETRY_COUNT
                )
            else:
                await outbox.mark_failed(entry.id, error)

    async def check_dlq_alert(self) -> int:
        """Check DLQ size and log a warning if above threshold.

        Returns the current DLQ count.
        """
        async with self._session_factory() as session:
            outbox = EventOutbox(session)
            count = await outbox.fetch_dlq_count()
            self._dlq_count = count
            if count >= DLQ_ALERT_THRESHOLD:
                logger.warning(
                    "DLQ ALERT: %d messages in dead letter queue (threshold=%d)",
                    count,
                    DLQ_ALERT_THRESHOLD,
                )
            return count

    @property
    def stats(self) -> dict:
        return {
            "running": self._running,
            "total_relayed": self._total_relayed,
            "total_failed": self._total_failed,
            "dlq_count": self._dlq_count,
        }
