"""Kafka producer wrapper for domain events.

Provides a dedicated producer that:
- Maps event types to domain-level Kafka topics
- Attaches CloudEvents headers for routing
- Validates events against JSON Schema before sending
- Reports metrics on publish success/failure
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from sdk.config import sdk_settings
from sdk.events.base import DomainEvent
from sdk.events.topic_mapping import event_type_to_topic, TOPIC_PREFIX
from sdk.events.schema_registry import validate_event

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Producer wrapper: publishes DomainEvents to Kafka topics.

    Usage:
        producer = KafkaProducer()
        await producer.start()
        await producer.publish(CompanyCreated(...))
        await producer.close()
    """

    def __init__(
        self,
        bootstrap_servers: str | None = None,
    ):
        self._bootstrap = bootstrap_servers or sdk_settings.kafka_bootstrap_servers
        self._producer: Any = None
        self._started = False
        self._metrics = ProducerMetrics()

    async def start(self) -> bool:
        """Start the Kafka producer connection.

        Returns True if connected, False if unavailable.
        """
        if self._started and self._producer is not None:
            return True

        try:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                acks="all",
            )
            await self._producer.start()
            self._started = True
            logger.info("Kafka producer connected to %s", self._bootstrap)
            return True
        except ImportError:
            logger.warning("aiokafka not installed — producer unavailable")
            return False
        except Exception as exc:
            logger.warning("Kafka producer failed to start: %s", exc)
            return False

    async def publish(self, event: DomainEvent) -> bool:
        """Publish a domain event to the appropriate Kafka topic.

        Returns True if published (or queued), False on failure.
        Validates against schema before sending.
        """
        if not self._started or self._producer is None:
            logger.warning("Producer not started — event %s not sent", event.event_id)
            return False

        # Validate
        errors = validate_event(event)
        if errors:
            logger.error(
                "Schema validation failed for %s (%s): %s",
                event.event_id, event.event_type, errors,
            )
            self._metrics.record_validation_error(event.event_type)
            return False

        topic = event_type_to_topic(event.event_type)
        headers: list[tuple[str, bytes]] = [
            ("event_type", event.event_type.encode("utf-8")),
            ("tenant_id", (event.tenant_id or "").encode("utf-8")),
            ("event_id", event.event_id.encode("utf-8")),
            ("specversion", b"1.0"),
        ]
        if event.metadata:
            uid = event.metadata.get("user_id")
            if uid is not None:
                headers.append(("user_id", str(uid).encode("utf-8")))
            cid = event.metadata.get("correlation_id")
            if cid is not None:
                headers.append(("correlation_id", str(cid).encode("utf-8")))

        try:
            await self._producer.send(
                topic,
                value=event.to_dict(),
                headers=headers,
            )
            self._metrics.record_published(event.event_type)
            logger.debug("Published %s to topic %s", event.event_id, topic)
            return True
        except Exception as exc:
            logger.error("Failed to publish %s to topic %s: %s", event.event_id, topic, exc)
            self._metrics.record_failure(event.event_type)
            return False

    async def flush(self) -> None:
        """Flush pending messages."""
        if self._producer is not None:
            await self._producer.flush()

    async def close(self) -> None:
        """Close the producer connection."""
        if self._producer is not None:
            try:
                await self._producer.stop()
            except Exception:
                logger.exception("Error stopping producer")
            self._producer = None
            self._started = False

    @property
    def metrics(self) -> ProducerMetrics:
        return self._metrics

    @property
    def is_connected(self) -> bool:
        return self._started and self._producer is not None


class ProducerMetrics:
    """Tracks producer publish metrics."""

    def __init__(self):
        self._published: dict[str, int] = {}
        self._failures: dict[str, int] = {}
        self._validation_errors: dict[str, int] = {}

    def record_published(self, event_type: str) -> None:
        self._published[event_type] = self._published.get(event_type, 0) + 1

    def record_failure(self, event_type: str) -> None:
        self._failures[event_type] = self._failures.get(event_type, 0) + 1

    def record_validation_error(self, event_type: str) -> None:
        self._validation_errors[event_type] = self._validation_errors.get(event_type, 0) + 1

    def snapshot(self) -> dict:
        return {
            "total_published": sum(self._published.values()),
            "total_failures": sum(self._failures.values()),
            "total_validation_errors": sum(self._validation_errors.values()),
            "by_type": {
                etype: {
                    "published": self._published.get(etype, 0),
                    "failures": self._failures.get(etype, 0),
                    "validation_errors": self._validation_errors.get(etype, 0),
                }
                for etype in set(
                    list(self._published.keys())
                    + list(self._failures.keys())
                    + list(self._validation_errors.keys())
                )
            },
        }
