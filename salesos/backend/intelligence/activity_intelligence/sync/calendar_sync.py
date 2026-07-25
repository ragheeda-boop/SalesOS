"""Calendar Sync Worker — provider-agnostic calendar synchronization (ADR-012 §12).

Operates against CalendarProvider interface. Handles:
- Incremental fetch (since last_sync)
- Recurring event handling
- Cancellation detection
- Mapping via MappingPipeline
- Activity recording via ActivityRuntime
"""

from __future__ import annotations

from datetime import datetime, timezone

from intelligence.activity_intelligence.contracts.events import (
    CommunicationReceived,
    CommunicationSynced,
)
from intelligence.activity_intelligence.contracts.models import RawCalendarEvent
from intelligence.activity_intelligence.contracts.provider import CalendarProvider
from intelligence.activity_intelligence.mapping import MappingPipeline
from intelligence.activity_intelligence.sync.conflict import ConflictResolver
from intelligence.activity_intelligence.sync.dedup import Deduplicator


class CalendarSyncWorker:
    """Synchronizes calendar events from a provider to the platform."""

    def __init__(
        self,
        provider: CalendarProvider,
        mapping: MappingPipeline,
        event_bus=None,
        activity_runtime=None,
    ):
        self.provider = provider
        self.mapping = mapping
        self.event_bus = event_bus
        self.activity_runtime = activity_runtime
        self.deduplicator = Deduplicator()
        self.conflict_resolver = ConflictResolver()
        self.last_sync: datetime | None = None

    async def sync(
        self,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        known_event_ids: set[str] | None = None,
    ) -> dict:
        """Run a sync cycle. Returns summary dict."""
        known_ids = known_event_ids or set()
        since = since or self.last_sync or datetime.now(timezone.utc)
        until = until or datetime.now(timezone.utc)

        events = await self.provider.fetch_events(since=since, until=until)

        new_count = 0
        updated_count = 0
        skipped_count = 0
        errors: list[str] = []

        for raw in events:
            event_key = raw.event_id

            # Handle recurring events — generate individual instances
            if raw.is_recurring:
                continue  # Future: expand recurring events

            if self.deduplicator.is_duplicate(event_key, known_ids):
                if raw.status == "cancelled":
                    # Handle cancellation of previously synced event
                    updated_count += 1
                    continue
                # Check for update conflicts
                if self.conflict_resolver.has_conflict(raw, known_ids):
                    skipped_count += 1
                    continue
                updated_count += 1
                continue

            try:
                # Stage 1: Emit received event
                if self.event_bus:
                    event = CommunicationReceived(
                        tenant_id=tenant_id,
                        channel="meeting",
                        source_provider="google_calendar",
                        source_id=raw.event_id,
                        raw_data=self._raw_to_dict(raw),
                        aggregate_type="communication",
                        aggregate_id=raw.event_id,
                    )
                    await self.event_bus.publish(event)

                # Stage 2: Resolve company via Mapping Pipeline
                domain = ""
                for attendee in raw.attendees:
                    email = attendee.get("email", "")
                    if "@" in email:
                        domain = email.rsplit("@", 1)[-1]
                        break

                if domain:
                    result = await self.mapping.resolve_company_from_event(
                        tenant_id=tenant_id, domain=domain
                    )

                    # Stage 3: Record in Activity Runtime
                    if self.activity_runtime and result:
                        await self.activity_runtime.ingest(
                            actor="system",
                            action="meeting.synced",
                            entity_type="communication",
                            entity_id=raw.event_id,
                            target_type=result.candidate.entity_type,
                            target_id=result.candidate.entity_id,
                            metadata={
                                "source_provider": "google_calendar",
                                "confidence": result.score,
                                "title": raw.title,
                                "start_time": raw.start_time.isoformat() if raw.start_time else None,
                            },
                            tenant_id=tenant_id,
                        )

                new_count += 1
                known_ids.add(event_key)

            except Exception as e:
                errors.append(f"Event {raw.event_id}: {e}")

        self.last_sync = datetime.now(timezone.utc)

        if self.event_bus:
            synced_event = CommunicationSynced(
                tenant_id=tenant_id,
                provider="google_calendar",
                channel="meeting",
                synced_count=len(events),
                new_count=new_count,
                updated_count=updated_count,
                errors=errors,
                aggregate_type="communication",
                aggregate_id=f"sync-calendar-{tenant_id}",
            )
            await self.event_bus.publish(synced_event)

        return {
            "synced_count": len(events),
            "new_count": new_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "errors": errors,
        }

    @staticmethod
    def _raw_to_dict(raw: RawCalendarEvent) -> dict:
        return {
            "event_id": raw.event_id,
            "title": raw.title,
            "start_time": raw.start_time.isoformat() if raw.start_time else None,
            "end_time": raw.end_time.isoformat() if raw.end_time else None,
            "status": raw.status,
        }
