"""Event bus: publish and subscribe to domain events."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

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

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a previously registered handler (optional override)."""


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

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type)
        if handlers:
            try:
                handlers.remove(handler)
            except ValueError:
                pass

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



