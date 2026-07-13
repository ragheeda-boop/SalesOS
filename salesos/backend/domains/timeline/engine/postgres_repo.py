"""PostgresTimelineRepository — production implementation using timeline_entries table."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..contracts.models import (
    ActivityOutcome,
    ActivityType,
    Actor,
    ActorType,
    Target,
    TimelineEvent,
)
from ..contracts.repository import TimelineQuery, TimelineRepository, TimelineResult
from ..models import TimelineEventModel


def _serialize_actor(actor: Actor) -> dict:
    return {"id": actor.id, "type": actor.type.value, "name": actor.name}


def _deserialize_actor(data: dict | None, actor_str: str | None) -> Actor:
    if data and "actor" in data:
        a = data["actor"]
        return Actor(id=a.get("id", ""), type=ActorType(a.get("type", "system")), name=a.get("name", ""))
    return Actor(id=actor_str or "system", type=ActorType.SYSTEM)


def _deserialize_target(data: dict | None, entity_type: str, entity_id: str) -> Target:
    t = (data or {}).get("target", {})
    return Target(
        id=t.get("id", entity_id),
        type=t.get("type", entity_type),
        label=t.get("label", ""),
    )


class PostgresTimelineRepository(TimelineRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def append(self, event: TimelineEvent) -> None:
        payload = {
            "actor": _serialize_actor(event.actor),
            "target": {
                "id": event.target.id,
                "type": event.target.type,
                "label": event.target.label,
            },
            "outcome": event.outcome.value,
            "event_id": event.event_id,
            **event.metadata,
        }
        row = TimelineEventModel(
            entity_type=event.target.type,
            entity_id=event.target.id,
            event_type=event.activity.value,
            data=payload,
            actor=event.actor.id,
            tenant_id=event.tenant_id,
            created_at=event.timestamp,
            importance=_calc_importance(event.activity.value),
        )
        self._session.add(row)
        await self._session.flush()

    async def query(self, query: TimelineQuery) -> TimelineResult:
        q = select(TimelineEventModel)
        count_q = select(func.count()).select_from(TimelineEventModel)

        filters = []
        if query.target_id:
            filters.append(TimelineEventModel.entity_id == query.target_id)
        if query.target_type:
            filters.append(TimelineEventModel.entity_type == query.target_type)
        if query.actor_id:
            filters.append(TimelineEventModel.actor == query.actor_id)
        if query.tenant_id:
            filters.append(TimelineEventModel.tenant_id == query.tenant_id)
        if query.activity_types:
            filters.append(TimelineEventModel.event_type.in_(query.activity_types))
        if query.from_date:
            filters.append(TimelineEventModel.created_at >= query.from_date)
        if query.to_date:
            filters.append(TimelineEventModel.created_at <= query.to_date)

        if filters:
            q = q.where(and_(*filters))
            count_q = count_q.where(and_(*filters))

        sort_col = TimelineEventModel.created_at
        q = q.order_by(sort_col.desc() if query.sort_order == "desc" else sort_col.asc())

        total = await self._session.scalar(count_q) or 0
        q = q.offset((query.page - 1) * query.page_size).limit(query.page_size)
        rows = (await self._session.execute(q)).scalars().all()

        events = [_row_to_event(r) for r in rows]
        return TimelineResult(events=events, total=total, page=query.page, page_size=query.page_size)

    async def get_by_target(self, target_id: str, target_type: str, page: int = 1, page_size: int = 50) -> TimelineResult:
        return await self.query(TimelineQuery(target_id=target_id, target_type=target_type, page=page, page_size=page_size))

    async def get_by_actor(self, actor_id: str, page: int = 1, page_size: int = 50) -> TimelineResult:
        return await self.query(TimelineQuery(actor_id=actor_id, page=page, page_size=page_size))

    async def count(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(TimelineEventModel).where(
                TimelineEventModel.tenant_id == tenant_id
            )
        )
        return result.scalar() or 0

    async def get_summary(
        self, entity_type: str, entity_id: str, tenant_id: str = ""
    ) -> dict:
        from sqlalchemy import and_, func as f

        filters = [
            TimelineEventModel.entity_type == entity_type,
            TimelineEventModel.entity_id == entity_id,
        ]
        if tenant_id:
            filters.append(TimelineEventModel.tenant_id == tenant_id)

        where = and_(*filters)

        total = await self._session.scalar(
            select(f.count()).select_from(TimelineEventModel).where(where)
        ) or 0

        unique_types = await self._session.scalar(
            select(f.count(TimelineEventModel.event_type.distinct())).select_from(TimelineEventModel).where(where)
        ) or 0

        first = await self._session.execute(
            select(TimelineEventModel.created_at).where(where).order_by(TimelineEventModel.created_at.asc()).limit(1)
        )
        first_row = first.scalar_one_or_none()

        last = await self._session.execute(
            select(TimelineEventModel.created_at).where(where).order_by(TimelineEventModel.created_at.desc()).limit(1)
        )
        last_row = last.scalar_one_or_none()

        breakdown_rows = await self._session.execute(
            select(TimelineEventModel.event_type, f.count()).where(where).group_by(TimelineEventModel.event_type)
        )
        event_breakdown = dict(breakdown_rows.all())

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_events": total,
            "unique_event_types": unique_types,
            "first_event": first_row.isoformat() if first_row else None,
            "last_event": last_row.isoformat() if last_row else None,
            "event_breakdown": event_breakdown,
        }


def _row_to_event(row: TimelineEventModel) -> TimelineEvent:
    data = row.data or {}
    actor = _deserialize_actor(data, row.actor)
    target = _deserialize_target(data, row.entity_type, row.entity_id)
    return TimelineEvent(
        event_id=data.get("event_id", str(row.id)),
        actor=actor,
        activity=ActivityType(row.event_type),
        target=target,
        outcome=ActivityOutcome(data.get("outcome", "success")),
        metadata={k: v for k, v in data.items() if k not in ("actor", "target", "outcome", "event_id")},
        timestamp=row.created_at.replace(tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at,
        tenant_id=row.tenant_id or "",
    )


def _calc_importance(event_type: str) -> int:
    high = {"company.created", "company.merged", "decision.created", "golden_record.created",
            "deal.won", "deal.lost", "contract.renewed"}
    medium = {"company.updated", "contact.created", "license.created", "decision.accepted",
              "company.enriched", "funding.received"}
    if event_type in high:
        return 10
    if event_type in medium:
        return 5
    return 1
