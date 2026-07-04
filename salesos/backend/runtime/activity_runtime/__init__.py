"""Activity Runtime — unified activity spine for SalesOS.

Every business action (email, meeting, task, contract, proposal,
comment, approval, file upload, note) becomes one ActivityRecord.

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

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


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
            await session.execute(
                sa_text("""
                    INSERT INTO activity_records
                        (id, actor, action, entity_type, entity_id,
                         target_type, target_id, metadata, tenant_id, timestamp)
                    VALUES
                        (:id, :actor, :action, :et, :eid,
                         :tt, :tid, :meta, :ten, :ts)
                """),
                {
                    "id": record.id,
                    "actor": record.actor,
                    "action": record.action,
                    "et": record.entity_type,
                    "eid": record.entity_id,
                    "tt": record.target_type,
                    "tid": record.target_id,
                    "meta": record.metadata or {},
                    "ten": record.tenant_id,
                    "ts": record.timestamp,
                },
            )
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
                await session.execute(
                    sa_text("""
                        INSERT INTO activity_records
                            (id, actor, action, entity_type, entity_id,
                             target_type, target_id, metadata, tenant_id, timestamp)
                        VALUES
                            (:id, :actor, :action, :et, :eid,
                             :tt, :tid, :meta, :ten, :ts)
                    """),
                    {
                        "id": a.id,
                        "actor": a.actor,
                        "action": a.action,
                        "et": a.entity_type,
                        "eid": a.entity_id,
                        "tt": a.target_type,
                        "tid": a.target_id,
                        "meta": a.metadata or {},
                        "ten": a.tenant_id,
                        "ts": a.timestamp,
                    },
                )
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

        conditions = []
        params: dict = {}
        idx = 0

        def _add(field: str, param: str, value: Any) -> None:
            nonlocal idx
            if value is not None:
                conditions.append(f"{field} = :{param}")
                params[param] = value

        _add("tenant_id", "ten", tenant_id)
        _add("actor", "actor", actor)
        _add("action", "action", action)
        _add("entity_type", "et", entity_type)
        _add("entity_id", "eid", entity_id)
        _add("target_type", "tt", target_type)
        _add("target_id", "tid", target_id)

        if since:
            conditions.append("timestamp >= :since")
            params["since"] = since
        if until:
            conditions.append("timestamp <= :until")
            params["until"] = until

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        count_sql = f"SELECT COUNT(*) FROM activity_records WHERE {where_clause}"
        query_sql = f"""
            SELECT * FROM activity_records
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT :lim OFFSET :off
        """
        params["lim"] = limit
        params["off"] = offset

        async with self._session_factory() as session:
            count_row = await session.execute(sa_text(count_sql), params)
            total = count_row.scalar() or 0

            rows = await session.execute(sa_text(query_sql), params)
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

        conditions = []
        params: dict = {}
        if tenant_id:
            conditions.append("tenant_id = :ten")
            params["ten"] = tenant_id
        if since:
            conditions.append("timestamp >= :since")
            params["since"] = since
        if until:
            conditions.append("timestamp <= :until")
            params["until"] = until
        where = " AND ".join(conditions) if conditions else "TRUE"

        async with self._session_factory() as session:
            # Total count
            row = await session.execute(
                sa_text(f"SELECT COUNT(*) FROM activity_records WHERE {where}"), params
            )
            total = row.scalar() or 0

            # By action
            breakdown = await session.execute(
                sa_text(f"""
                    SELECT action, COUNT(*) as cnt
                    FROM activity_records WHERE {where}
                    GROUP BY action ORDER BY cnt DESC
                """),
                params,
            )
            by_action = {r["action"]: r["cnt"] for r in breakdown.mappings().all()}

            # By entity type
            et_breakdown = await session.execute(
                sa_text(f"""
                    SELECT entity_type, COUNT(*) as cnt
                    FROM activity_records WHERE {where}
                    GROUP BY entity_type ORDER BY cnt DESC
                """),
                params,
            )
            by_entity_type = {r["entity_type"]: r["cnt"] for r in et_breakdown.mappings().all()}

            # Time range
            time_range = await session.execute(
                sa_text(f"""
                    SELECT
                        MIN(timestamp) as first_ts,
                        MAX(timestamp) as last_ts
                    FROM activity_records WHERE {where}
                """),
                params,
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
