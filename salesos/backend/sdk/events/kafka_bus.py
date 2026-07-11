"""Kafka-backed event bus with graceful fallback to in-memory.

When Kafka is unavailable (aiokafka not installed, broker down, etc.),
the bus degrades seamlessly to InMemoryEventBus so existing code
continues to work unchanged.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sdk.config import sdk_settings
from sdk.events.base import DomainEvent
from sdk.events.bus import EventBus, InMemoryEventBus

logger = logging.getLogger(__name__)

_TOPIC_PREFIX = "salesos"


class KafkaEventBus(EventBus):
    """Event bus backed by Apache Kafka.

    Uses aiokafka for async producer/consumer.  If aiokafka cannot be
    imported or the broker is unreachable, all operations fall through
    to an in-memory bus so the system remains functional without Kafka.

    Topic naming convention: ``salesos.<domain>.<event_type>``

    Headers carried on every Kafka message:
        - ``tenant_id``
        - ``user_id`` (from event metadata, if present)
        - ``correlation_id`` (from event metadata, if present)
        - ``event_type``
    """

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        group_id: str | None = None,
        auto_offset_reset: str | None = None,
    ):
        self._bootstrap = bootstrap_servers or sdk_settings.kafka_bootstrap_servers
        self._group_id = group_id or sdk_settings.kafka_group_id
        self._offset_reset = auto_offset_reset or sdk_settings.kafka_auto_offset_reset

        self._producer: Any = None
        self._consumer: Any = None
        self._consumer_task: asyncio.Task | None = None
        self._running = False
        self._kafka_available: bool | None = None  # None=untried, True/False

        # Handlers keyed by event_type (same pattern as InMemoryEventBus)
        self._handlers: dict[str, list] = {}
        self._wildcard_handlers: list = []

        # Fallback — always present, used when Kafka is unavailable
        self._fallback = InMemoryEventBus()

    # ── Producer ────────────────────────────────────────────────────────────

    async def _start_producer(self) -> bool:
        """Attempt to create and start the Kafka producer.

        Returns True if the producer started successfully.
        On any failure, sets _kafka_available = False.
        """
        if self._kafka_available is False:
            return False
        if self._producer is not None:
            return True

        try:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            await self._producer.start()
            self._kafka_available = True
            logger.info("Kafka producer connected to %s", self._bootstrap)
            return True
        except ImportError:
            self._kafka_available = False
            logger.warning(
                "aiokafka not installed — falling back to in-memory event bus"
            )
        except Exception as exc:
            self._kafka_available = False
            logger.warning(
                "Kafka unavailable (%s) — falling back to in-memory event bus",
                exc,
            )
        return False

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event.

        Attempts Kafka first; falls back to in-memory on any failure.
        """
        ok = await self._start_producer()
        if not ok:
            await self._fallback.publish(event)
            return

        topic = f"{_TOPIC_PREFIX}.{event.event_type}"
        headers: list[tuple[str, bytes]] = [
            ("tenant_id", (event.tenant_id or "").encode("utf-8")),
            ("event_type", event.event_type.encode("utf-8")),
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
            logger.debug("Published event %s to topic %s", event.event_id, topic)
        except Exception as exc:
            logger.error(
                "Failed to publish event %s to Kafka (%s) — falling back",
                event.event_id,
                exc,
            )
            await self._fallback.publish(event)

    # ── Consumer ────────────────────────────────────────────────────────────

    def _build_handler_list(self, event_type: str) -> list:
        handlers = list(self._handlers.get(event_type, []))
        handlers.extend(self._handlers.get("*", []))
        handlers.extend(self._wildcard_handlers)
        return handlers

    async def _consume_loop(self) -> None:
        """Background task: poll Kafka and dispatch to registered handlers."""
        if self._consumer is None:
            return

        logger.info(
            "Kafka consumer started (group=%s, topics=%s)",
            self._group_id,
            list(self._handlers.keys()),
        )

        while self._running:
            try:
                msg = await self._consumer.getone()
                if msg is None:
                    continue
                event = self._deserialize(msg)
                if event is None:
                    continue

                handlers = self._build_handler_list(event.event_type)
                for handler in handlers:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        logger.exception(
                            "Handler %s failed for event %s",
                            getattr(handler, "__name__", "?"),
                            event.event_type,
                        )
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Kafka consumer error — continuing")
                await asyncio.sleep(1)

    def _deserialize(self, msg: Any) -> DomainEvent | None:
        """Convert a Kafka consumer message back into a DomainEvent."""
        try:
            payload = json.loads(msg.value.decode("utf-8"))
        except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as exc:
            logger.warning("Cannot decode Kafka message: %s", exc)
            return None

        # CloudEvents 1.0 envelope
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

        # Legacy format
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

    def _topics_from_handlers(self) -> list[str]:
        """Derive Kafka topic list from registered handler keys."""
        topics = set()
        for event_type in self._handlers:
            if event_type == "*":
                continue
            topics.add(f"{_TOPIC_PREFIX}.{event_type}")
        return list(topics)

    # ── Subscribe / Unsubscribe ─────────────────────────────────────────────

    def subscribe(self, event_type: str, handler) -> None:
        """Register a handler for a specific event type.

        When a consumer is active the handler receives deserialized
        messages from Kafka.  Otherwise it is forwarded to the
        in-memory fallback.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        # Also register with the in-memory fallback for seamless degradation
        self._fallback.subscribe(event_type, handler)
        logger.debug("Handler subscribed to %s: %s", event_type, handler.__name__)

        # If consumer is running, update its topic subscription
        if self._consumer is not None:
            topics = self._topics_from_handlers()
            if topics:
                self._consumer.subscribe(topics=topics)

    def unsubscribe(self, event_type: str, handler) -> None:
        """Remove a previously registered handler."""
        handlers = self._handlers.get(event_type)
        if handlers:
            try:
                handlers.remove(handler)
                logger.debug(
                    "Handler unsubscribed from %s: %s",
                    event_type,
                    handler.__name__,
                )
            except ValueError:
                pass
            if not handlers:
                del self._handlers[event_type]
        # Also unregister from the in-memory fallback
        self._fallback.unsubscribe(event_type, handler)

    def subscribe_wildcard(self, handler) -> None:
        """Register a handler for ALL event types."""
        self._wildcard_handlers.append(handler)
        self._fallback.subscribe("*", handler)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start_consumer(self) -> None:
        """Start the background Kafka consumer task (if Kafka is available)."""
        if self._consumer is not None or self._kafka_available is False:
            return

        topics = self._topics_from_handlers()
        if not topics:
            logger.debug("No topics to subscribe to — consumer not started")
            return

        try:
            from aiokafka import AIOKafkaConsumer

            self._consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self._bootstrap,
                group_id=self._group_id,
                auto_offset_reset=self._offset_reset,
                value_deserializer=lambda v: v,
            )
            await self._consumer.start()
            self._kafka_available = True
            self._running = True
            self._consumer_task = asyncio.create_task(self._consume_loop())
            logger.info("Kafka consumer started on topics: %s", topics)
        except ImportError:
            self._kafka_available = False
            logger.warning(
                "aiokafka not installed — Kafka consumer unavailable"
            )
        except Exception as exc:
            self._kafka_available = False
            logger.warning(
                "Kafka consumer failed to start (%s) — handlers will use in-memory",
                exc,
            )
            self._consumer = None

    async def stop_consumer(self) -> None:
        """Stop the background consumer task and close the consumer."""
        self._running = False

        if self._consumer_task is not None:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

        if self._consumer is not None:
            try:
                await self._consumer.stop()
            except Exception:
                logger.exception("Error stopping Kafka consumer")
            self._consumer = None

    async def close(self) -> None:
        """Shut down producer and consumer, freeing all resources."""
        await self.stop_consumer()

        if self._producer is not None:
            try:
                await self._producer.stop()
            except Exception:
                logger.exception("Error stopping Kafka producer")
            self._producer = None

    @property
    def is_kafka_available(self) -> bool | None:
        """``True`` when Kafka is connected, ``False`` when in fallback,
        ``None`` when not yet attempted."""
        return self._kafka_available


def _parse_time(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)
