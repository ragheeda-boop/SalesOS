"""Event Runtime — full event lifecycle orchestrator.

Lifecycle for every event:
  publish()
    → Store (PostgresEventStore)
    → Fan-out to ordered subscribers
      → Workflow triggers
      → Notifications
      → AI pipeline
      → Analytics refresh
      → Audit trail
    → Retry with exponential backoff on failure
    → Dead Letter Queue on exhaustion
    → Metrics (latency, throughput, failures)
    → Tracing span per event lifecycle

Implements sdk.events.EventBus interface for drop-in replacement.
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sdk.events.base import DomainEvent
from sdk.events.bus import EventBus
from sdk.events.store import PostgresEventStore
from sdk.telemetry import StructuredLogger, get_tracer, trace_span


class SubscriberPriority(Enum):
    FIRST = 0
    EARLY = 10
    NORMAL = 50
    LATE = 90
    LAST = 100


@dataclass
class SubscriberRegistration:
    handler: Callable[[DomainEvent], Any]
    priority: SubscriberPriority = SubscriberPriority.NORMAL
    name: str = ""
    max_retries: int = 3
    timeout_seconds: float = 30.0


@dataclass
class EventLifecycle:
    event_id: str
    event_type: str
    started_at: datetime
    stored_ms: float = 0.0
    subscriber_results: dict[str, float] = field(default_factory=dict)
    subscriber_errors: dict[str, str] = field(default_factory=dict)
    total_duration_ms: float = 0.0
    dead_lettered: bool = False


class DeadLetterEntry:
    def __init__(
        self,
        event: DomainEvent,
        subscriber_name: str,
        error: str,
        attempts: int,
        failed_at: datetime | None = None,
    ):
        self.event = event
        self.subscriber_name = subscriber_name
        self.error = error
        self.attempts = attempts
        self.failed_at = failed_at or datetime.now(timezone.utc)
        self.id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event.event_id,
            "event_type": self.event.event_type,
            "subscriber": self.subscriber_name,
            "error": self.error,
            "attempts": self.attempts,
            "failed_at": self.failed_at.isoformat(),
            "event_data": self.event.data,
        }


class DeadLetterQueue:
    """Stores events that failed all retry attempts."""

    def __init__(self):
        self._entries: list[DeadLetterEntry] = []

    def add(self, entry: DeadLetterEntry) -> None:
        self._entries.append(entry)

    def get_all(self) -> list[DeadLetterEntry]:
        return list(self._entries)

    def get_by_event(self, event_id: str) -> list[DeadLetterEntry]:
        return [e for e in self._entries if e.event.event_id == event_id]

    def count(self) -> int:
        return len(self._entries)

    def replay(self, entry_id: str) -> DeadLetterEntry | None:
        for entry in self._entries:
            if entry.id == entry_id:
                self._entries.remove(entry)
                return entry
        return None

    def clear(self) -> None:
        self._entries.clear()


class RetryPolicy:
    """Exponential backoff retry with jitter."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    async def execute(
        self,
        handler: Callable,
        event: DomainEvent,
        subscriber_name: str,
        logger: StructuredLogger | None = None,
    ) -> tuple[bool, str | None]:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    result = await asyncio.wait_for(result, timeout=10.0)
                return True, None
            except asyncio.TimeoutError:
                last_error = "timeout"
                if logger:
                    logger.warn(
                        "event_runtime.retry_timeout",
                        subscriber=subscriber_name,
                        event=event.event_type,
                        attempt=attempt,
                    )
            except Exception as e:
                last_error = str(e)
                if logger:
                    logger.warn(
                        "event_runtime.retry_failed",
                        subscriber=subscriber_name,
                        event=event.event_type,
                        attempt=attempt,
                        error=str(e),
                    )

            if attempt < self.max_retries:
                delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
                if self.jitter:
                    import random
                    delay = delay * (0.5 + random.random() * 0.5)
                await asyncio.sleep(delay)

        return False, last_error


class EventMetrics:
    """Event runtime metrics counters."""

    def __init__(self):
        self._events_published: dict[str, int] = {}
        self._events_succeeded: dict[str, int] = {}
        self._events_failed: dict[str, int] = {}
        self._events_dead_lettered: dict[str, int] = {}
        self._latencies: dict[str, list[float]] = {}
        self._subscriber_durations: dict[str, list[float]] = {}

    def record_published(self, event_type: str) -> None:
        self._events_published[event_type] = self._events_published.get(event_type, 0) + 1

    def record_succeeded(self, event_type: str) -> None:
        self._events_succeeded[event_type] = self._events_succeeded.get(event_type, 0) + 1

    def record_failed(self, event_type: str) -> None:
        self._events_failed[event_type] = self._events_failed.get(event_type, 0) + 1

    def record_dead_lettered(self, event_type: str) -> None:
        self._events_dead_lettered[event_type] = self._events_dead_lettered.get(event_type, 0) + 1

    def record_latency(self, event_type: str, duration_ms: float) -> None:
        if event_type not in self._latencies:
            self._latencies[event_type] = []
        self._latencies[event_type].append(duration_ms)

    def record_subscriber_duration(self, subscriber_name: str, duration_ms: float) -> None:
        if subscriber_name not in self._subscriber_durations:
            self._subscriber_durations[subscriber_name] = []
        self._subscriber_durations[subscriber_name].append(duration_ms)

    def snapshot(self) -> dict:
        return {
            "total_published": sum(self._events_published.values()),
            "total_succeeded": sum(self._events_succeeded.values()),
            "total_failed": sum(self._events_failed.values()),
            "total_dead_lettered": sum(self._events_dead_lettered.values()),
            "by_type": {
                etype: {
                    "published": self._events_published.get(etype, 0),
                    "succeeded": self._events_succeeded.get(etype, 0),
                    "failed": self._events_failed.get(etype, 0),
                    "dead_lettered": self._events_dead_lettered.get(etype, 0),
                }
                for etype in set(list(self._events_published.keys()))
            },
            "subscribers": {
                name: {
                    "avg_duration_ms": round(
                        sum(durs) / len(durs), 2
                    ) if durs else 0,
                    "total_calls": len(durs),
                }
                for name, durs in self._subscriber_durations.items()
            },
        }


class EventRuntime(EventBus):
    """Orchestrates the complete event lifecycle.

    Implements EventBus interface — drop-in replacement for InMemoryEventBus.

    Usage:
        runtime = EventRuntime(async_session)
        runtime.subscribe("company.created", my_handler)
        await runtime.publish(CompanyCreated(...))
    """

    def __init__(
        self,
        session_factory=None,
        logger: StructuredLogger | None = None,
    ):
        super().__init__()
        self._session_factory = session_factory
        self._logger = logger
        self._subscribers: dict[str, list[SubscriberRegistration]] = {}
        self._wildcard_subscribers: list[SubscriberRegistration] = []
        self._dlq = DeadLetterQueue()
        self._retry = RetryPolicy()
        self.metrics = EventMetrics()
        self._tracer = get_tracer("event_runtime")

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        """EventBus interface: subscribe a handler to an event type."""
        self.register(event_type, handler)

    def register(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Any],
        priority: SubscriberPriority = SubscriberPriority.NORMAL,
        name: str | None = None,
        max_retries: int = 3,
    ) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        reg = SubscriberRegistration(
            handler=handler,
            priority=priority,
            name=name or getattr(handler, "__name__", "unknown"),
            max_retries=max_retries,
        )
        self._subscribers[event_type].append(reg)
        self._subscribers[event_type].sort(key=lambda r: r.priority.value)
        if self._logger:
            self._logger.debug(
                "event_runtime.subscriber_registered",
                event_type=event_type,
                subscriber=reg.name,
            )

    def register_wildcard(
        self,
        handler: Callable[[DomainEvent], Any],
        priority: SubscriberPriority = SubscriberPriority.LAST,
        name: str | None = None,
    ) -> None:
        """Register a handler for ALL event types."""
        reg = SubscriberRegistration(
            handler=handler,
            priority=priority,
            name=name or getattr(handler, "__name__", "unknown"),
        )
        self._wildcard_subscribers.append(reg)
        self._wildcard_subscribers.sort(key=lambda r: r.priority.value)

    async def publish(self, event: DomainEvent) -> EventLifecycle:
        """Publish an event through the full lifecycle.

        Lifecycle:
        1. Store the event (PostgresEventStore via session factory)
        2. Fan-out to matched subscribers (ordered by priority)
        3. Trace each subscriber execution
        4. Retry on failure with backoff
        5. Dead letter on exhaustion
        6. Emit metrics
        """
        lifecycle = EventLifecycle(
            event_id=event.event_id,
            event_type=event.event_type,
            started_at=datetime.now(timezone.utc),
        )

        with self._tracer.start_as_current_span("event_runtime.publish") as span:
            span.set_attribute("event.type", event.event_type)
            span.set_attribute("event.id", event.event_id)

            # 1. Store the event (create session per-publish)
            store_start = time.monotonic()
            if self._session_factory:
                try:
                    async with self._session_factory() as store_session:
                        event_store = PostgresEventStore(store_session)
                        await event_store.append(event)
                        await store_session.commit()
                        lifecycle.stored_ms = (time.monotonic() - store_start) * 1000
                        span.set_attribute("event.stored_ms", lifecycle.stored_ms)
                except Exception as e:
                    if self._logger:
                        self._logger.error(
                            "event_runtime.store_failed",
                            event_type=event.event_type,
                            event_id=event.event_id,
                            error=str(e),
                        )
                    return lifecycle

            # 2. Collect subscribers
            handlers = list(self._subscribers.get(event.event_type, []))
            handlers.extend(self._subscribers.get("*", []))
            handlers.extend(self._wildcard_subscribers)
            handlers.sort(key=lambda r: r.priority.value)

            if not handlers:
                self.metrics.record_published(event.event_type)
                self.metrics.record_succeeded(event.event_type)
                lifecycle.total_duration_ms = (time.monotonic() - time.monotonic()) + 0.001
                return lifecycle

            # 3. Fan-out to subscribers
            for reg in handlers:
                sub_start = time.monotonic()
                retry_policy = RetryPolicy(max_retries=reg.max_retries)
                success, error = await retry_policy.execute(
                    reg.handler, event, reg.name, self._logger
                )
                sub_duration = (time.monotonic() - sub_start) * 1000

                if success:
                    lifecycle.subscriber_results[reg.name] = sub_duration
                    self.metrics.record_subscriber_duration(reg.name, sub_duration)
                    if self._logger:
                        self._logger.debug(
                            "event_runtime.subscriber_succeeded",
                            subscriber=reg.name,
                            event_type=event.event_type,
                            duration_ms=round(sub_duration, 2),
                        )
                else:
                    lifecycle.subscriber_errors[reg.name] = error or "unknown"
                    # 4. Dead letter on exhaustion
                    dl_entry = DeadLetterEntry(
                        event=event,
                        subscriber_name=reg.name,
                        error=error or "unknown",
                        attempts=reg.max_retries,
                    )
                    self._dlq.add(dl_entry)
                    lifecycle.dead_lettered = True
                    self.metrics.record_dead_lettered(event.event_type)
                    if self._logger:
                        self._logger.error(
                            "event_runtime.subscriber_dead_lettered",
                            subscriber=reg.name,
                            event_type=event.event_type,
                            error=error,
                        )

            # 5. Finalize lifecycle
            lifecycle.total_duration_ms = (time.monotonic() - store_start) * 1000
            span.set_attribute("event.total_duration_ms", lifecycle.total_duration_ms)
            span.set_attribute("event.subscriber_count", len(handlers))
            span.set_attribute("event.dead_lettered", str(lifecycle.dead_lettered))

            self.metrics.record_published(event.event_type)
            if lifecycle.dead_lettered:
                self.metrics.record_failed(event.event_type)
            else:
                self.metrics.record_succeeded(event.event_type)
            self.metrics.record_latency(event.event_type, lifecycle.total_duration_ms)

        return lifecycle

    @property
    def dead_letter_queue(self) -> DeadLetterQueue:
        return self._dlq

    async def replay_dead_letter(self, entry_id: str) -> bool:
        """Replay a dead lettered event through the full lifecycle."""
        entry = self._dlq.replay(entry_id)
        if not entry:
            return False
        await self.publish(entry.event)
        return True

    async def replay_all_dead_letters(self) -> int:
        """Replay all dead lettered events."""
        entries = list(self._dlq.get_all())
        count = 0
        for entry in entries:
            success = await self.replay_dead_letter(entry.id)
            if success:
                count += 1
        return count
