"""Kafka-backed event bus with domain-level topics and graceful fallback.

Uses the dedicated KafkaProducer and KafkaConsumerBase for sending and
receiving events.  When Kafka is unavailable (aiokafka not installed,
broker down, etc.), the bus degrades seamlessly to InMemoryEventBus
so existing code continues to work unchanged.

Outbox integration: when ``sdk_settings.kafka_outbox_enabled`` is True,
``publish()`` writes to the transactional outbox first.  The outbox relay
then publishes to Kafka asynchronously.

Topic naming follows the domain-level convention ``salesos.<domain>``
(e.g. ``salesos.company``, ``salesos.crm``) instead of per-event-type
topics.  Event types are mapped to domain topics via
``sdk.events.topic_mapping``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sdk.config import sdk_settings
from sdk.events.base import DomainEvent
from sdk.events.bus import EventBus, InMemoryEventBus
from sdk.events.kafka_producer import KafkaProducer
from sdk.events.kafka_consumer import KafkaConsumerBase
from sdk.events.topic_mapping import event_type_to_topic, topics_for_event_types

logger = logging.getLogger(__name__)


class KafkaEventBus(EventBus):
    """Event bus backed by Apache Kafka with domain-level topics.

    Uses KafkaProducer for publishing and KafkaConsumerBase for consuming.
    Falls back to InMemoryEventBus when Kafka is unavailable.

    When ``outbox_enabled=True``, publish() writes to the transactional
    outbox instead of directly to Kafka.  An ``OutboxRelay`` background
    task publishes outboxed events asynchronously.

    Topic naming: ``salesos.<domain>`` (e.g. ``salesos.company``).
    """

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        group_id: str | None = None,
        auto_offset_reset: str | None = None,
        outbox_enabled: bool | None = None,
    ):
        self._bootstrap = bootstrap_servers or sdk_settings.kafka_bootstrap_servers
        self._group_id = group_id or sdk_settings.kafka_group_id
        self._offset_reset = auto_offset_reset or sdk_settings.kafka_auto_offset_reset
        self._outbox_enabled = (
            outbox_enabled
            if outbox_enabled is not None
            else sdk_settings.kafka_outbox_enabled
        )

        self._producer = KafkaProducer(bootstrap_servers=self._bootstrap)
        self._consumer: _BusConsumer | None = None
        self._consumer_task: asyncio.Task | None = None
        self._kafka_available: bool | None = None
        self._relay: Any = None

        # Handlers keyed by event_type (same pattern as InMemoryEventBus)
        self._handlers: dict[str, list] = {}
        self._wildcard_handlers: list = []

        # Fallback — always present
        self._fallback = InMemoryEventBus()

    # ── Outbox integration ──────────────────────────────────────────────────

    async def set_outbox_relay(self, relay: Any) -> None:
        """Attach an OutboxRelay for transactional outbox mode."""
        self._relay = relay
        if relay is not None:
            self._outbox_enabled = True
            logger.info("KafkaEventBus: outbox relay attached")

    # ── Producer ────────────────────────────────────────────────────────────

    async def _ensure_producer(self) -> bool:
        """Ensure producer is started.

        Returns True if Kafka is available for publishing.
        """
        if self._kafka_available is False:
            return False

        ok = await self._producer.start()
        if ok:
            self._kafka_available = True
        else:
            self._kafka_available = False
        return ok

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event.

        If outbox is enabled, writes to the transactional outbox first.
        Otherwise, attempts Kafka first; falls back to in-memory on any failure.
        """
        if self._outbox_enabled and self._relay is not None:
            await self._publish_outbox(event)
            return

        ok = await self._ensure_producer()
        if not ok:
            await self._fallback.publish(event)
            return

        success = await self._producer.publish(event)
        if not success:
            logger.warning(
                "Kafka publish failed for %s — falling back to in-memory",
                event.event_id,
            )
            await self._fallback.publish(event)

    async def _publish_outbox(self, event: DomainEvent) -> None:
        """Write event to the outbox for transactional delivery."""
        try:
            from sdk.events.outbox import EventOutbox

            outbox = EventOutbox(self._relay._session_factory)
            async with self._relay._session_factory() as session:
                event_outbox = EventOutbox(session)
                await event_outbox.ensure_table()
                await event_outbox.write(event)
                await session.commit()
            logger.debug("Event %s written to outbox", event.event_id)
        except Exception as exc:
            logger.error("Failed to write event %s to outbox: %s", event.event_id, exc)
            await self._fallback.publish(event)

    # ── Consumer ────────────────────────────────────────────────────────────

    async def start_consumer(self) -> None:
        """Start the background Kafka consumer task (if Kafka is available)."""
        if self._consumer is not None or self._kafka_available is False:
            return

        topics = self._topics_from_handlers()
        if not topics:
            logger.debug("No topics to subscribe to — consumer not started")
            return

        self._consumer = _BusConsumer(
            topics=topics,
            bootstrap_servers=self._bootstrap,
            group_id=self._group_id,
            auto_offset_reset=self._offset_reset,
        )

        ok = await self._consumer.start()
        if ok:
            self._kafka_available = True
            self._consumer.set_dispatcher(self._dispatch_to_handlers)
            logger.info("Kafka consumer started on topics: %s", topics)
        else:
            self._kafka_available = False
            logger.warning("Kafka consumer failed to start — using in-memory")

    def _dispatch_to_handlers(self, event: DomainEvent) -> None:
        """Dispatch a consumed event to all registered handlers."""
        handlers = list(self._handlers.get(event.event_type, []))
        handlers.extend(self._handlers.get("*", []))
        handlers.extend(self._wildcard_handlers)

        if not handlers:
            logger.debug("No handlers for event: %s", event.event_type)
            return

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                logger.exception(
                    "Handler %s failed for event %s",
                    getattr(handler, "__name__", "?"),
                    event.event_type,
                )

    def _topics_from_handlers(self) -> list[str]:
        """Derive Kafka topic list from registered handler keys."""
        if self._handlers:
            event_types = [et for et in self._handlers if et != "*"]
            return topics_for_event_types(event_types)
        return list(self._handlers.keys())

    # ── Subscribe / Unsubscribe ─────────────────────────────────────────────

    def subscribe(self, event_type: str, handler) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self._fallback.subscribe(event_type, handler)
        logger.debug("Handler subscribed to %s: %s", event_type, handler.__name__)

    def unsubscribe(self, event_type: str, handler) -> None:
        """Remove a previously registered handler."""
        handlers = self._handlers.get(event_type)
        if handlers:
            try:
                handlers.remove(handler)
            except ValueError:
                pass
            if not handlers:
                del self._handlers[event_type]
        self._fallback.unsubscribe(event_type, handler)

    def subscribe_wildcard(self, handler) -> None:
        """Register a handler for ALL event types."""
        self._wildcard_handlers.append(handler)
        self._fallback.subscribe("*", handler)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def stop_consumer(self) -> None:
        """Stop the background consumer."""
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

    async def close(self) -> None:
        """Shut down producer and consumer, freeing all resources."""
        await self.stop_consumer()
        await self._producer.close()
        if self._relay is not None:
            await self._relay.stop()

    @property
    def is_kafka_available(self) -> bool | None:
        return self._kafka_available

    @property
    def producer(self) -> KafkaProducer:
        return self._producer

    @property
    def outbox_enabled(self) -> bool:
        return self._outbox_enabled


class _BusConsumer(KafkaConsumerBase):
    """Internal consumer used by KafkaEventBus.

    Dispatches deserialized events to the bus's handler registry.
    """

    def __init__(
        self,
        topics: list[str],
        bootstrap_servers: str,
        group_id: str,
        auto_offset_reset: str,
    ):
        super().__init__(
            topics=topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            validate_schemas=False,
        )
        self._dispatcher = None

    def set_dispatcher(self, dispatcher) -> None:
        self._dispatcher = dispatcher

    async def handle_event(self, event: DomainEvent) -> None:
        if self._dispatcher:
            self._dispatcher(event)
