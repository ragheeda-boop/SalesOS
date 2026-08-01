"""Universal Timeline Runtime - every object gets a typed, queryable timeline.

CI-19 Wave 2 Core (no sqlalchemy.text)

Timeline entries capture any event related to an entity:
  - Entity type + Entity ID identifies the timeline owner
  - Event type categorizes what happened
  - Data stores the event payload
  - Actor records who/what caused the event

Supports any entity type: Company, Person, Deal, License, etc.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import and_, func, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from domains.timeline.models import TimelineEventModel


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


def _domain_filter(domain: str):
    return TimelineEventModel.data["domain"].astext == domain


def _timeline_filters(
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    tenant_id: str | None = None,
    event_types: list[str] | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    domain: str | None = None,
) -> list[Any]:
    filters: list[Any] = []
    if entity_type is not None:
        filters.append(TimelineEventModel.entity_type == entity_type)
    if entity_id is not None:
        filters.append(TimelineEventModel.entity_id == entity_id)
    if tenant_id is not None:
        filters.append(TimelineEventModel.tenant_id == tenant_id)
    if event_types:
        filters.append(TimelineEventModel.event_type.in_(event_types))
    if since is not None:
        filters.append(TimelineEventModel.created_at >= since)
    if until is not None:
        filters.append(TimelineEventModel.created_at <= until)
    if domain:
        filters.append(_domain_filter(domain))
    return filters


class TimelineRuntime:
    """Universal timeline - records all events for all entity types."""

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
            stmt = insert(TimelineEventModel).values(
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=event_type,
                data=data,
                actor=actor,
                tenant_id=tenant_id,
                importance=importance,
                created_at=entry.created_at,
            )
            await session.execute(stmt)
            await session.commit()

        return entry

    async def get_timeline(
        self,
        entity_type: str,
        entity_id: str,
        event_types: Optional[list[str]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        domain: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        t0 = time.monotonic()
        self.metrics.queries_executed += 1

        filters = _timeline_filters(
            entity_type=entity_type,
            entity_id=entity_id,
            event_types=event_types,
            since=since,
            until=until,
            domain=domain,
        )
        where_clause = and_(*filters) if filters else True

        async with self._session_factory() as session:
            count_stmt = (
                select(func.count())
                .select_from(TimelineEventModel)
                .where(where_clause)
            )
            total = (await session.execute(count_stmt)).scalar() or 0

            query_filters = list(filters)
            if cursor:
                try:
                    cursor_data = json.loads(cursor)
                    cursor_created = cursor_data.get("created_at")
                    cursor_id = cursor_data.get("id")
                    if cursor_created:
                        query_filters.append(
                            or_(
                                TimelineEventModel.created_at < cursor_created,
                                and_(
                                    TimelineEventModel.created_at == cursor_created,
                                    TimelineEventModel.id < cursor_id,
                                ),
                            )
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

            query_where = and_(*query_filters) if query_filters else True
            stmt = (
                select(TimelineEventModel)
                .where(query_where)
                .order_by(
                    TimelineEventModel.created_at.desc(),
                    TimelineEventModel.id.desc(),
                )
                .limit(limit)
            )
            if not cursor:
                stmt = stmt.offset(offset)

            rows = await session.execute(stmt)
            results = [dict(r) for r in rows.mappings().all()]

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return results, total

    async def get_entity_timelines(
        self,
        tenant_id: str,
        entity_type: str,
        limit: int = 20,
        domain: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[dict]:
        t0 = time.monotonic()
        self.metrics.queries_executed += 1

        filters = _timeline_filters(
            tenant_id=tenant_id,
            entity_type=entity_type,
            since=since,
            until=until,
            domain=domain,
        )
        where_clause = and_(*filters)

        async with self._session_factory() as session:
            stmt = (
                select(TimelineEventModel)
                .distinct(TimelineEventModel.entity_id)
                .where(where_clause)
                .order_by(
                    TimelineEventModel.entity_id,
                    TimelineEventModel.created_at.desc(),
                )
                .limit(limit)
            )
            rows = await session.execute(stmt)
            results = [dict(r) for r in rows.mappings().all()]

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return results

    async def get_timeline_summary(
        self,
        entity_type: str,
        entity_id: str,
        domain: Optional[str] = None,
    ) -> dict:
        t0 = time.monotonic()
        self.metrics.queries_executed += 1

        filters = _timeline_filters(
            entity_type=entity_type,
            entity_id=entity_id,
            domain=domain,
        )
        where_clause = and_(*filters)

        async with self._session_factory() as session:
            stats_stmt = select(
                func.count().label("total_events"),
                func.count(func.distinct(TimelineEventModel.event_type)).label(
                    "unique_event_types"
                ),
                func.min(TimelineEventModel.created_at).label("first_event"),
                func.max(TimelineEventModel.created_at).label("last_event"),
            ).where(where_clause)
            stats = dict((await session.execute(stats_stmt)).mappings().one())

            breakdown_stmt = (
                select(
                    TimelineEventModel.event_type,
                    func.count().label("cnt"),
                )
                .where(where_clause)
                .group_by(TimelineEventModel.event_type)
                .order_by(func.count().desc())
            )
            breakdown = await session.execute(breakdown_stmt)
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
        return [
            e.to_dict()
            for e in self._entries
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]

    async def on_domain_event(self, event_data: dict) -> None:
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
        high = {
            "company.created",
            "company.merged",
            "decision.created",
            "golden_record.created",
            "deal.won",
            "deal.lost",
            "contract.renewed",
        }
        medium = {
            "company.updated",
            "contact.created",
            "license.created",
            "decision.accepted",
            "company.enriched",
            "funding.received",
        }
        if event_type in high:
            return 10
        if event_type in medium:
            return 5
        return 1
