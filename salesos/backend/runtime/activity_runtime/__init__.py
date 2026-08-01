"""Activity Runtime — unified activity spine for SalesOS.

Every business action (email, meeting, task, contract, proposal,
comment, approval, file upload, note) becomes one ActivityRecord.

CI-19 Wave 2 Core (no sqlalchemy.text)

Schema:
  actor       — who performed the action
  action      — what was done (e.g. "email.sent", "meeting.completed")
  entity_type — primary entity type
  entity_id   — primary entity ID
  target_type — secondary entity type (optional)
  target_id   — secondary entity ID (optional)
  metadata    — flexible JSON payload
  tenant_id   — multi-tenancy
  timestamp   — when it happened
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    and_,
    func,
    insert,
    select,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

_activity_metadata = MetaData()

activity_records = Table(
    "activity_records",
    _activity_metadata,
    Column("id", String(64), primary_key=True),
    Column("actor", String(255), nullable=False),
    Column("action", String(100), nullable=False),
    Column("entity_type", String(50), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("target_type", String(50), nullable=True),
    Column("target_id", String(64), nullable=True),
    Column("metadata", JSONB, nullable=True),
    Column("tenant_id", String(36), nullable=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    # Live indexes — metadata register only (DEC-130d); do not DROP
    Index("ix_activity_action", "action", text("timestamp DESC")),
    Index("ix_activity_actor", "actor", text("timestamp DESC")),
    Index("ix_activity_entity", "entity_type", "entity_id", text("timestamp DESC")),
    Index("ix_activity_records_action", "action"),
    Index("ix_activity_records_actor", "actor"),
    Index("ix_activity_records_entity_id", "entity_id"),
    Index("ix_activity_records_tenant_id", "tenant_id"),
    Index("ix_activity_records_timestamp", "timestamp"),
    Index("ix_activity_tenant_action", "tenant_id", "action", text("timestamp DESC")),
)


@dataclass
class ActivityRecord:
    actor: str
    action: str
    entity_type: str
    entity_id: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    tenant_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "metadata": self.metadata or {},
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ActivityMetrics:
    ingested: int = 0
    queries: int = 0
    total_query_ms: float = 0.0

    def snapshot(self) -> dict:
        return {
            "ingested": self.ingested,
            "queries": self.queries,
            "total_query_ms": round(self.total_query_ms, 2),
        }


def _insert_values(record: ActivityRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "actor": record.actor,
        "action": record.action,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "target_type": record.target_type,
        "target_id": record.target_id,
        "metadata": record.metadata or {},
        "tenant_id": record.tenant_id,
        "timestamp": record.timestamp,
    }


def _filter_where(
    *,
    tenant_id: Optional[str] = None,
    actor: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    """Build allowlisted Core WHERE from optional equality / range filters."""
    conditions = []
    if tenant_id is not None:
        conditions.append(activity_records.c.tenant_id == tenant_id)
    if actor is not None:
        conditions.append(activity_records.c.actor == actor)
    if action is not None:
        conditions.append(activity_records.c.action == action)
    if entity_type is not None:
        conditions.append(activity_records.c.entity_type == entity_type)
    if entity_id is not None:
        conditions.append(activity_records.c.entity_id == entity_id)
    if target_type is not None:
        conditions.append(activity_records.c.target_type == target_type)
    if target_id is not None:
        conditions.append(activity_records.c.target_id == target_id)
    if since is not None:
        conditions.append(activity_records.c.timestamp >= since)
    if until is not None:
        conditions.append(activity_records.c.timestamp <= until)
    return and_(*conditions) if conditions else true()


class ActivityRuntime:
    """Unified activity spine — every business action becomes an ActivityRecord.

    Integrates with EventRuntime to auto-record domain events.
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._logger = logger
        self.metrics = ActivityMetrics()

    async def ingest(
        self,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        tenant_id: Optional[str] = None,
    ) -> ActivityRecord:
        record = ActivityRecord(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        self.metrics.ingested += 1

        async with self._session_factory() as session:
            await session.execute(insert(activity_records).values(**_insert_values(record)))
            await session.commit()

        return record

    async def ingest_batch(
        self, records: list[dict]
    ) -> list[ActivityRecord]:
        """Ingest multiple activities in a single transaction."""
        activities = []
        for r in records:
            activities.append(ActivityRecord(
                actor=r["actor"],
                action=r["action"],
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                target_type=r.get("target_type"),
                target_id=r.get("target_id"),
                metadata=r.get("metadata"),
                tenant_id=r.get("tenant_id"),
            ))

        self.metrics.ingested += len(activities)

        async with self._session_factory() as session:
            for a in activities:
                await session.execute(insert(activity_records).values(**_insert_values(a)))
            await session.commit()

        return activities

    async def query(
        self,
        tenant_id: Optional[str] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        import time
        t0 = time.monotonic()
        self.metrics.queries += 1

        where = _filter_where(
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            target_type=target_type,
            target_id=target_id,
            since=since,
            until=until,
        )

        async with self._session_factory() as session:
            total = (
                await session.scalar(
                    select(func.count()).select_from(activity_records).where(where)
                )
            ) or 0

            rows = await session.execute(
                select(activity_records)
                .where(where)
                .order_by(activity_records.c.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            results = [dict(r) for r in rows.mappings().all()]

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return results, total

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return await self.query(
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def get_by_actor(
        self,
        actor: str,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return await self.query(
            actor=actor,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def get_by_action(
        self,
        action: str,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return await self.query(
            action=action,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def get_stats(
        self,
        tenant_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> dict:
        import time
        t0 = time.monotonic()
        self.metrics.queries += 1

        where = _filter_where(tenant_id=tenant_id, since=since, until=until)
        action_col = activity_records.c.action
        entity_type_col = activity_records.c.entity_type
        cnt = func.count().label("cnt")

        async with self._session_factory() as session:
            total = (
                await session.scalar(
                    select(func.count()).select_from(activity_records).where(where)
                )
            ) or 0

            breakdown = await session.execute(
                select(action_col, cnt)
                .where(where)
                .group_by(action_col)
                .order_by(cnt.desc())
            )
            by_action = {r["action"]: r["cnt"] for r in breakdown.mappings().all()}

            et_breakdown = await session.execute(
                select(entity_type_col, cnt)
                .where(where)
                .group_by(entity_type_col)
                .order_by(cnt.desc())
            )
            by_entity_type = {
                r["entity_type"]: r["cnt"] for r in et_breakdown.mappings().all()
            }

            time_range = await session.execute(
                select(
                    func.min(activity_records.c.timestamp).label("first_ts"),
                    func.max(activity_records.c.timestamp).label("last_ts"),
                ).where(where)
            )
            tr = dict(time_range.mappings().one())

        elapsed = (time.monotonic() - t0) * 1000
        self.metrics.total_query_ms += elapsed
        return {
            "total": total,
            "by_action": by_action,
            "by_entity_type": by_entity_type,
            "first_activity": str(tr["first_ts"]) if tr["first_ts"] else None,
            "last_activity": str(tr["last_ts"]) if tr["last_ts"] else None,
        }

    # ── Event Runtime integration ──

    async def on_domain_event(self, event_data: dict) -> None:
        """Called by EventRuntime subscriber — records domain events as activities."""
        await self.ingest(
            actor=event_data.get("metadata", {}).get("actor", "system"),
            action=event_data.get("event_type", "unknown"),
            entity_type=event_data.get("aggregate_type", "unknown"),
            entity_id=event_data.get("aggregate_id", ""),
            metadata=event_data.get("data"),
            tenant_id=event_data.get("tenant_id"),
        )
