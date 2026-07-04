"""Universal Timeline Runtime — every object gets a typed, queryable timeline.

Timeline entries capture any event related to an entity:
  - Entity type + Entity ID identifies the timeline owner
  - Event type categorizes what happened
  - Data stores the event payload
  - Actor records who/what caused the event

Supports any entity type: Company, Person, Deal, License, etc.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class TimelineEntry:
    entity_type: str
    entity_id: str
    event_type: str
    data: dict[str, Any]
    actor: Optional[str] = None
    tenant_id: Optional[str] = None
    importance: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "event_type": self.event_type,
            "data": self.data,
            "actor": self.actor,
            "tenant_id": self.tenant_id,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TimelineMetrics:
    entries_recorded: int = 0
    queries_executed: int = 0
    total_query_ms: float = 0.0

    def snapshot(self) -> dict:
        return {
            "entries_recorded": self.entries_recorded,
            "queries_executed": self.queries_executed,
            "total_query_ms": round(self.total_query_ms, 2),
        }


class TimelineRuntime:
    """Universal timeline — records all events for all entity types.

    Integrates with EventRuntime by subscribing to wildcard `*` events
    and recording every domain event as a timeline entry.
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._logger = logger
        self.metrics = TimelineMetrics()
        self._entries: list[TimelineEntry] = []

    async def record(
        self,
        entity_type: str,
        entity_id: str,
        event_type: str,
        data: dict,
        actor: Optional[str] = None,
        tenant_id: Optional[str] = None,
        importance: int = 0,
    ) -> TimelineEntry:
        entry = TimelineEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            data=data,
            actor=actor,
            tenant_id=tenant_id,
            importance=importance,
        )
        self._entries.append(entry)
        self.metrics.entries_recorded += 1

        async with self._session_factory() as session:
            await session.execute(
                sa_text("""
                    INSERT INTO timeline_entries
                        (entity_type, entity_id, event_type, data, actor, tenant_id, importance, created_at)
                    VALUES (:et, :eid, :evt, :data, :actor, :tid, :imp, :ca)
                """),
                {
                    "et": entity_type,
                    "eid": entity_id,
                    "evt": event_type,
                    "data": data,
                    "actor": actor,
                    "tid": tenant_id,
                    "imp": importance,
                    "ca": entry.created_at,
                },
            )
            await session.commit()

        return entry

    async def get_timeline(
        self,
        entity_type: str,
        entity_id: str,
        event_types: Optional[list[str]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        t0 = time.monotonic()
        self.metrics.queries_executed += 1

        query = """
            SELECT * FROM timeline_entries
            WHERE entity_type = :et AND entity_id = :eid
        """
        params: dict = {"et": entity_type, "eid": entity_id}

        if event_types:
            query += " AND event_type = ANY(:evts)"
            params["evts"] = event_types
        if since:
            query += " AND created_at >= :since"
            params["since"] = since
        if until:
            query += " AND created_at <= :until"
            params["until"] = until

        query += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        params["lim"] = limit
        params["off"] = offset

        async with self._session_factory() as session:
            rows = await session.execute(sa_text(query), params)
            results = [dict(r) for r in rows.mappings().all()]

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return results

    async def get_entity_timelines(self, tenant_id: str, entity_type: str, limit: int = 20) -> list[dict]:
        """Get most recent timelines across all entities of a type."""
        t0 = time.monotonic()
        self.metrics.queries_executed += 1
        async with self._session_factory() as session:
            rows = await session.execute(
                sa_text("""
                    SELECT DISTINCT ON (entity_id) *
                    FROM timeline_entries
                    WHERE tenant_id = :tid AND entity_type = :et
                    ORDER BY entity_id, created_at DESC
                    LIMIT :lim
                """),
                {"tid": tenant_id, "et": entity_type, "lim": limit},
            )
            results = [dict(r) for r in rows.mappings().all()]
        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return results

    async def get_timeline_summary(self, entity_type: str, entity_id: str) -> dict:
        """Return summary stats for an entity's timeline."""
        t0 = time.monotonic()
        self.metrics.queries_executed += 1
        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT event_type) as unique_event_types,
                        MIN(created_at) as first_event,
                        MAX(created_at) as last_event
                    FROM timeline_entries
                    WHERE entity_type = :et AND entity_id = :eid
                """),
                {"et": entity_type, "eid": entity_id},
            )
            stats = dict(row.mappings().one())

            # Event type breakdown
            breakdown = await session.execute(
                sa_text("""
                    SELECT event_type, COUNT(*) as cnt
                    FROM timeline_entries
                    WHERE entity_type = :et AND entity_id = :eid
                    GROUP BY event_type
                    ORDER BY cnt DESC
                """),
                {"et": entity_type, "eid": entity_id},
            )
            event_breakdown = {r["event_type"]: r["cnt"] for r in breakdown.mappings().all()}

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_events": stats["total_events"] or 0,
            "unique_event_types": stats["unique_event_types"] or 0,
            "first_event": str(stats["first_event"]) if stats["first_event"] else None,
            "last_event": str(stats["last_event"]) if stats["last_event"] else None,
            "event_breakdown": event_breakdown,
        }

    def get_all_entries(self, entity_type: str, entity_id: str) -> list[dict]:
        """Return in-memory entries (for testing / hot path)."""
        return [
            e.to_dict() for e in self._entries
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]

    # ── Event Runtime integration ─────────────────────────────

    async def on_domain_event(self, event_data: dict) -> None:
        """Called by EventRuntime subscriber — records any domain event as timeline entry."""
        await self.record(
            entity_type=event_data.get("aggregate_type", "unknown"),
            entity_id=event_data.get("aggregate_id", ""),
            event_type=event_data.get("event_type", "unknown"),
            data=event_data.get("data", {}),
            actor=event_data.get("metadata", {}).get("actor"),
            tenant_id=event_data.get("tenant_id"),
            importance=self._calc_importance(event_data.get("event_type", "")),
        )

    def _calc_importance(self, event_type: str) -> int:
        high = {"company.created", "company.merged", "decision.created", "golden_record.created",
                "deal.won", "deal.lost", "contract.renewed"}
        medium = {"company.updated", "contact.created", "license.created", "decision.accepted",
                  "company.enriched", "funding.received"}
        if event_type in high:
            return 10
        if event_type in medium:
            return 5
        return 1
