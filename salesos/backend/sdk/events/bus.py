"""Event bus: publish and subscribe to domain events."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from sdk.config import sdk_settings
from sdk.events.base import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Any]


class EventBus(ABC):
    """Abstract event bus for publishing domain events."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribed handlers."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""


class InMemoryEventBus(EventBus):
    """In-memory event bus for development and testing.

    Handlers are called synchronously within the same process.
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Handler subscribed to %s: %s", event_type, handler.__name__)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        wildcard_handlers = self._handlers.get("*", [])
        all_handlers = handlers + wildcard_handlers

        if not all_handlers:
            logger.debug("No handlers for event: %s", event.event_type)
            return

        for handler in all_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
                logger.debug("Event %s handled by %s", event.event_type, handler.__name__)
            except Exception:
                logger.exception(
                    "Handler %s failed for event %s", handler.__name__, event.event_type
                )


class KafkaEventBus(EventBus):
    """Kafka-backed event bus for production use.

    Requires aiokafka client. Handlers run in separate consumer processes.
    """

    def __init__(self, bootstrap_servers: str | None = None):
        self._bootstrap_servers = bootstrap_servers or sdk_settings.kafka_bootstrap_servers
        self._producer = None

    async def _get_producer(self):
        if self._producer is None:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode(),
            )
            await self._producer.start()
        return self._producer

    async def publish(self, event: DomainEvent) -> None:
        producer = await self._get_producer()
        topic = f"salesos.{event.event_type}"
        await producer.send(topic, value=event.to_dict())
        logger.info("Published event %s to topic %s", event.event_id, topic)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        logger.warning(
            "KafkaEventBus.subscribe() is a no-op. "
            "Use a separate consumer process instead."
        )

    async def close(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None
