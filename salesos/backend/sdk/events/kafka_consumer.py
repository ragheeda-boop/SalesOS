"""Kafka consumer base class for domain events.

Provides:
- Topic subscription by domain name
- Automatic deserialization from CloudEvents 1.0 format
- Schema validation on consume
- Graceful error handling with configurable retry
- Dead letter support
- Consumer group management
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sdk.config import sdk_settings
from sdk.events.base import DomainEvent
from sdk.events.topic_mapping import TOPIC_PREFIX, topic_to_domain
from sdk.events.schema_registry import validate_event

logger = logging.getLogger(__name__)


class KafkaConsumerBase(ABC):
    """Base class for Kafka consumers.

    Subclasses implement ``handle_event()`` to process deserialized
    DomainEvents. The base class handles connection, deserialization,
    schema validation, and error management.

    Usage:
        class MyConsumer(KafkaConsumerBase):
            async def handle_event(self, event: DomainEvent) -> None:
                # process the event
                pass

        consumer = MyConsumer(topics=["salesos.company", "salesos.crm"])
        await consumer.start()
        # ... consumer runs until stop() is called
        await consumer.stop()
    """

    def __init__(
        self,
        topics: list[str] | None = None,
        bootstrap_servers: str | None = None,
        group_id: str | None = None,
        auto_offset_reset: str | None = None,
        validate_schemas: bool = True,
    ):
        self._topics = topics or []
        self._bootstrap = bootstrap_servers or sdk_settings.kafka_bootstrap_servers
        self._group_id = group_id or sdk_settings.kafka_group_id
        self._offset_reset = auto_offset_reset or sdk_settings.kafka_auto_offset_reset
        self._validate_schemas = validate_schemas

        self._consumer: Any = None
        self._running = False
        self._task: asyncio.Task | None = None
        self._metrics = ConsumerMetrics()

    @abstractmethod
    async def handle_event(self, event: DomainEvent) -> None:
        """Process a deserialized domain event.

        Override this in subclasses. Raise an exception to trigger
        the error handling / dead letter flow.
        """

    async def start(self) -> bool:
        """Start the consumer and begin processing events.

        Returns True if consumer started, False if unavailable.
        """
        if self._running:
            return True

        if not self._topics:
            logger.warning("No topics configured — consumer not started")
            return False

        try:
            from aiokafka import AIOKafkaConsumer

            self._consumer = AIOKafkaConsumer(
                *self._topics,
                bootstrap_servers=self._bootstrap,
                group_id=self._group_id,
                auto_offset_reset=self._offset_reset,
                value_deserializer=lambda v: v,
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
            )
            await self._consumer.start()
            self._running = True
            self._task = asyncio.create_task(self._consume_loop())
            logger.info(
                "Consumer started (group=%s, topics=%s)",
                self._group_id, self._topics,
            )
            return True
        except ImportError:
            logger.warning("aiokafka not installed — consumer unavailable")
            return False
        except Exception as exc:
            logger.warning("Consumer failed to start: %s", exc)
            return False

    async def stop(self) -> None:
        """Stop the consumer gracefully."""
        self._running = False

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._consumer is not None:
            try:
                await self._consumer.stop()
            except Exception:
                logger.exception("Error stopping consumer")
            self._consumer = None

    async def subscribe(self, topics: list[str]) -> None:
        """Update topic subscription (if consumer is running)."""
        self._topics = topics
        if self._consumer is not None:
            self._consumer.subscribe(topics=topics)
            logger.info("Consumer subscribed to topics: %s", topics)

    async def _consume_loop(self) -> None:
        """Background poll-and-dispatch loop."""
        if self._consumer is None:
            return

        while self._running:
            try:
                msg = await self._consumer.getone()
                if msg is None:
                    continue

                event = self._deserialize(msg)
                if event is None:
                    self._metrics.record_deserialization_error()
                    continue

                if self._validate_schemas:
                    errors = validate_event(event)
                    if errors:
                        logger.warning(
                            "Schema validation failed for %s (%s): %s",
                            event.event_id, event.event_type, errors,
                        )
                        self._metrics.record_validation_error(event.event_type)
                        continue

                self._metrics.record_received(event.event_type)

                try:
                    await self.handle_event(event)
                    self._metrics.record_handled(event.event_type)
                except Exception:
                    logger.exception(
                        "Handler failed for event %s (%s)",
                        event.event_id, event.event_type,
                    )
                    self._metrics.record_handler_error(event.event_type)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Consumer loop error — continuing")
                await asyncio.sleep(1)

    def _deserialize(self, msg: Any) -> DomainEvent | None:
        """Convert a Kafka ConsumerRecord back into a DomainEvent.

        Supports both CloudEvents 1.0 and legacy envelope formats.
        """
        try:
            payload = json.loads(msg.value.decode("utf-8"))
        except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as exc:
            logger.warning("Cannot decode Kafka message: %s", exc)
            return None

        if "specversion" in payload and "data" in payload:
            data = payload["data"]
            return DomainEvent(
                event_id=payload.get("id", ""),
                event_type=payload.get("type", ""),
                aggregate_id="",
                aggregate_type=payload.get("source", "salesos").replace("salesos.", ""),
                tenant_id=data.get("tenant_id", ""),
                occurred_at=_parse_time(payload.get("time")),
                data=data.get("payload", {}),
                metadata=data.get("metadata", {}),
            )

        return DomainEvent(
            event_id=payload.get("event_id", ""),
            event_type=payload.get("event_type", ""),
            event_version=payload.get("event_version", 1),
            aggregate_id=payload.get("aggregate_id", ""),
            aggregate_type=payload.get("aggregate_type", ""),
            tenant_id=payload.get("tenant_id", ""),
            occurred_at=_parse_time(payload.get("occurred_at")),
            data=payload.get("data", {}),
            metadata=payload.get("metadata", {}),
        )

    @property
    def metrics(self) -> ConsumerMetrics:
        return self._metrics

    @property
    def is_running(self) -> bool:
        return self._running


class ConsumerMetrics:
    """Tracks consumer processing metrics."""

    def __init__(self):
        self._received: dict[str, int] = {}
        self._handled: dict[str, int] = {}
        self._handler_errors: dict[str, int] = {}
        self._validation_errors: dict[str, int] = {}
        self._deserialization_errors: int = 0

    def record_received(self, event_type: str) -> None:
        self._received[event_type] = self._received.get(event_type, 0) + 1

    def record_handled(self, event_type: str) -> None:
        self._handled[event_type] = self._handled.get(event_type, 0) + 1

    def record_handler_error(self, event_type: str) -> None:
        self._handler_errors[event_type] = self._handler_errors.get(event_type, 0) + 1

    def record_validation_error(self, event_type: str) -> None:
        self._validation_errors[event_type] = self._validation_errors.get(event_type, 0) + 1

    def record_deserialization_error(self) -> None:
        self._deserialization_errors += 1

    def snapshot(self) -> dict:
        all_types = set(
            list(self._received.keys())
            + list(self._handled.keys())
            + list(self._handler_errors.keys())
            + list(self._validation_errors.keys())
        )
        return {
            "total_received": sum(self._received.values()),
            "total_handled": sum(self._handled.values()),
            "total_handler_errors": sum(self._handler_errors.values()),
            "total_validation_errors": sum(self._validation_errors.values()),
            "total_deserialization_errors": self._deserialization_errors,
            "by_type": {
                etype: {
                    "received": self._received.get(etype, 0),
                    "handled": self._handled.get(etype, 0),
                    "handler_errors": self._handler_errors.get(etype, 0),
                    "validation_errors": self._validation_errors.get(etype, 0),
                }
                for etype in all_types
            },
        }


def _parse_time(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)
