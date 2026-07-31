"""Dead Letter Queue for Kafka event consumers.

Provides:
- ``DLQHandler`` — tracks per-event retries and routes to DLQ topic after max attempts
- ``DLQConsumerBase`` — consumer base with automatic retry + DLQ routing
- ``DLQReader`` — reads/replays events from the DLQ topic
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sdk.events.base import DomainEvent
from sdk.events.kafka_consumer import KafkaConsumerBase
from sdk.events.kafka_producer import KafkaProducer
from sdk.events.topic_mapping import event_type_to_topic

logger = logging.getLogger(__name__)

DLQ_TOPIC = "salesos.dlq"
MAX_RETRIES = 3


class DLQEntry:
    """Represents a dead-lettered event with metadata."""

    def __init__(
        self,
        event: DomainEvent,
        topic: str,
        error: str,
        retry_count: int = 0,
        failed_at: datetime | None = None,
    ):
        self.event = event
        self.topic = topic
        self.error = error
        self.retry_count = retry_count
        self.failed_at = failed_at or datetime.now(UTC)

    def to_dict(self) -> dict:
        return {
            "event": self.event.to_dict(),
            "original_topic": self.topic,
            "error": self.error,
            "retry_count": self.retry_count,
            "failed_at": self.failed_at.isoformat(),
        }


class DLQHandler:
    """Handles retry logic and DLQ routing for failed event processing.

    Usage in a consumer::

        handler = DLQHandler(producer)
        # when processing fails:
        await handler.handle_failure(event, topic, error)
    """

    def __init__(
        self,
        producer: KafkaProducer | None = None,
        max_retries: int = MAX_RETRIES,
        dlq_topic: str = DLQ_TOPIC,
    ):
        self._producer = producer or KafkaProducer()
        self._max_retries = max_retries
        self._dlq_topic = dlq_topic
        self._retry_counts: dict[str, int] = {}
        self._total_dlq: int = 0
        self._producer_started = False

    async def _ensure_producer(self) -> bool:
        if not self._producer_started:
            ok = await self._producer.start()
            if ok:
                self._producer_started = True
            return ok
        return self._producer.is_connected

    def should_retry(self, event_id: str) -> bool:
        """Check if the event should be retried."""
        count = self._retry_counts.get(event_id, 0)
        return count < self._max_retries

    def record_attempt(self, event_id: str) -> int:
        """Record a retry attempt. Returns the attempt number (1-based)."""
        self._retry_counts[event_id] = self._retry_counts.get(event_id, 0) + 1
        return self._retry_counts[event_id]

    async def handle_failure(self, event: DomainEvent, original_topic: str, error: str) -> bool:
        """Handle a failed event.

        If under max retries, records the attempt (consumer should retry).
        If max retries exceeded, sends to DLQ topic.

        Returns True if sent to DLQ, False if retry is still possible.
        """
        attempt = self.record_attempt(event.event_id)

        if attempt < self._max_retries:
            logger.warning(
                "Event %s (%s) failed (attempt %d/%d): %s — will retry",
                event.event_id,
                event.event_type,
                attempt,
                self._max_retries,
                error,
            )
            return False

        logger.error(
            "Event %s (%s) failed after %d attempts — sending to DLQ: %s",
            event.event_id,
            event.event_type,
            self._max_retries,
            error,
        )

        await self._send_to_dlq(event, original_topic, error)
        return True

    async def _send_to_dlq(self, event: DomainEvent, original_topic: str, error: str) -> None:
        """Publish the failed event to the DLQ topic."""
        ok = await self._ensure_producer()
        if not ok:
            logger.warning("DLQHandler: producer unavailable — cannot send to DLQ")
            return

        entry = DLQEntry(
            event=event,
            topic=original_topic,
            error=error,
            retry_count=self._retry_counts.get(event.event_id, 0),
        )

        headers: list[tuple[str, bytes]] = [
            ("event_type", event.event_type.encode("utf-8")),
            ("event_id", event.event_id.encode("utf-8")),
            ("original_topic", original_topic.encode("utf-8")),
            ("error", error.encode("utf-8")),
            ("specversion", b"1.0"),
            ("dlq_reason", b"max_retries_exceeded"),
        ]

        try:
            await self._producer._producer.send(
                self._dlq_topic,
                value=json.dumps(entry.to_dict(), default=str).encode("utf-8"),
                headers=headers,
                key=event.aggregate_id.encode("utf-8") if event.aggregate_id else None,
            )
            self._total_dlq += 1
            logger.info("Event %s sent to DLQ topic %s", event.event_id, self._dlq_topic)
        except Exception as exc:
            logger.exception("DLQHandler: failed to send event %s to DLQ: %s", event.event_id, exc)

    def clear_retries(self, event_id: str) -> None:
        """Clear retry count for a successfully processed event."""
        self._retry_counts.pop(event_id, None)

    @property
    def total_dlq(self) -> int:
        return self._total_dlq

    @property
    def stats(self) -> dict:
        return {
            "total_dlq": self._total_dlq,
            "active_retries": len(self._retry_counts),
            "max_retries": self._max_retries,
        }


class RetryableConsumer(KafkaConsumerBase, ABC):
    """Consumer base class with automatic retry and DLQ routing.

    Subclasses implement ``process_event()``. If it raises, the consumer
    retries up to ``max_retries`` times, then routes the event to the DLQ topic.

    Usage::

        class MyConsumer(RetryableConsumer):
            async def process_event(self, event: DomainEvent) -> None:
                # this will auto-retry on failure
                ...
    """

    def __init__(
        self,
        *args,
        max_retries: int = MAX_RETRIES,
        dlq_topic: str = DLQ_TOPIC,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._dlq_handler = DLQHandler(
            producer=KafkaProducer(bootstrap_servers=kwargs.get("bootstrap_servers")),
            max_retries=max_retries,
            dlq_topic=dlq_topic,
        )

    @abstractmethod
    async def process_event(self, event: DomainEvent) -> None:
        """Process a domain event. Raise on failure to trigger retry/DLQ."""

    async def handle_event(self, event: DomainEvent) -> None:
        """Wrap process_event with retry + DLQ logic."""
        topic = event_type_to_topic(event.event_type)
        for attempt in range(1, self._dlq_handler._max_retries + 1):
            try:
                await self.process_event(event)
                self._dlq_handler.clear_retries(event.event_id)
                return
            except Exception as exc:
                error = str(exc)
                if attempt < self._dlq_handler._max_retries:
                    logger.warning(
                        "RetryableConsumer: attempt %d/%d failed for %s: %s",
                        attempt,
                        self._dlq_handler._max_retries,
                        event.event_id,
                        error,
                    )
                else:
                    logger.error(
                        "RetryableConsumer: all %d attempts failed for %s — DLQ",
                        self._dlq_handler._max_retries,
                        event.event_id,
                    )
                    await self._dlq_handler._send_to_dlq(event, topic, error)
                    raise

    async def close(self) -> None:
        await super().stop()
        if self._dlq_handler._producer:
            await self._dlq_handler._producer.close()


class DLQReader:
    """Reads and replays events from the DLQ topic.

    Usage::

        reader = DLQReader(bootstrap_servers="kafka:9092")
        entries = await reader.read_dlq(limit=10)
        for entry in entries:
            # inspect or replay
            ...
        await reader.close()
    """

    def __init__(self, bootstrap_servers: str = "kafka:9092", group_id: str = "dlq-reader"):
        self._bootstrap = bootstrap_servers
        self._group_id = group_id

    async def read_dlq(self, limit: int = 10) -> list[DLQEntry]:
        """Read entries from the DLQ topic without committing.

        Uses an isolated consumer with ``auto_offset_reset='earliest'``.
        """
        try:
            from aiokafka import AIOKafkaConsumer

            consumer = AIOKafkaConsumer(
                DLQ_TOPIC,
                bootstrap_servers=self._bootstrap,
                group_id=f"{self._group_id}-{datetime.now(UTC).timestamp()}",
                auto_offset_reset="earliest",
                enable_auto_commit=False,
            )
            await consumer.start()

            entries: list[DLQEntry] = []
            timeout_ms = 3000
            try:
                while len(entries) < limit:
                    msg = await consumer.getone(timeout_ms=timeout_ms)
                    if msg is None:
                        break
                    payload = json.loads(msg.value.decode("utf-8"))
                    event_dict = payload.get("event", {})
                    event = DomainEvent(
                        event_id=event_dict.get("id", ""),
                        event_type=event_dict.get("type", ""),
                        aggregate_id=event_dict.get("subject", "").split("/")[-1]
                        if "/" in (event_dict.get("subject", ""))
                        else "",
                        aggregate_type=event_dict.get("source", "").replace("salesos.", ""),
                        tenant_id=event_dict.get("data", {}).get("tenant_id", ""),
                        occurred_at=datetime.fromisoformat(
                            event_dict.get("time", datetime.now(UTC).isoformat())
                        ),
                        data=event_dict.get("data", {}).get("payload", {}),
                        metadata=event_dict.get("data", {}).get("metadata", {}),
                    )
                    entry = DLQEntry(
                        event=event,
                        topic=payload.get("original_topic", ""),
                        error=payload.get("error", ""),
                        retry_count=payload.get("retry_count", 0),
                        failed_at=datetime.fromisoformat(
                            payload.get("failed_at", datetime.now(UTC).isoformat())
                        ),
                    )
                    entries.append(entry)
            except TimeoutError:
                pass

            await consumer.stop()
            return entries

        except ImportError:
            logger.warning("aiokafka not installed — cannot read DLQ")
            return []
        except Exception as exc:
            logger.warning("DLQReader: failed to read DLQ: %s", exc)
            return []
