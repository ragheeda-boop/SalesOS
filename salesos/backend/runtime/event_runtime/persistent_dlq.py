"""Persistent Dead Letter Queue — Postgres-backed DLQ for EventRuntime.

Replaces the in-memory-only DeadLetterQueue so dead-lettered events survive
process restarts and can be queried/replayed via the existing REST endpoints.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import apply_tenant_guc

logger = logging.getLogger(__name__)


class PersistentDeadLetterQueue:
    """Postgres-backed DLQ. Writes dead-lettered events to event_dead_letters table."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def add(
        self,
        entry_id: str,
        tenant_id: str,
        event_id: str,
        event_type: str,
        subscriber_name: str,
        error: str,
        attempts: int,
        event_data: dict | None = None,
        failed_at: datetime | None = None,
    ) -> None:
        now = failed_at or datetime.now(timezone.utc)
        try:
            async with self._session_factory() as session:
                # event_dead_letters has RLS+FORCE RLS; this is the one live
                # caller of this class (EventRuntime._dispatch on exhaustion)
                # — without this pin, every real dead-letter INSERT fails its
                # WITH CHECK and is caught below, silently discarding the
                # persistent-storage guarantee this class exists for (the
                # in-memory DeadLetterQueue still holds it, so nothing is
                # lost until a process restart).
                await apply_tenant_guc(session, tenant_id)
                await session.execute(
                    text("""
                        INSERT INTO event_dead_letters
                            (id, tenant_id, event_id, event_type, subscriber_name,
                             error, attempts, event_data, failed_at)
                        VALUES (:id, :tenant_id, :event_id, :event_type, :subscriber,
                                :error, :attempts, CAST(:event_data AS jsonb), :failed_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": entry_id,
                        "tenant_id": tenant_id,
                        "event_id": event_id,
                        "event_type": event_type,
                        "subscriber": subscriber_name,
                        "error": error[:2000],
                        "attempts": attempts,
                        "event_data": json.dumps(event_data) if event_data else None,
                        "failed_at": now,
                    },
                )
                await session.commit()
        except Exception as e:
            logger.error(
                "dlq_persist_failed",
                extra={"error": str(e), "event_id": event_id, "subscriber": subscriber_name},
            )

    async def list_all(self, tenant_id: str, limit: int = 100) -> list[dict]:
        try:
            async with self._session_factory() as session:
                await apply_tenant_guc(session, tenant_id)
                result = await session.execute(
                    text("""
                        SELECT id, event_id, event_type, subscriber_name, error,
                               attempts, event_data, failed_at, replayed_at
                        FROM event_dead_letters
                        WHERE tenant_id = :tenant_id
                        ORDER BY failed_at DESC
                        LIMIT :limit
                    """),
                    {"tenant_id": tenant_id, "limit": limit},
                )
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error("dlq_list_failed", extra={"error": str(e)})
            return []

    async def count(self, tenant_id: str) -> int:
        try:
            async with self._session_factory() as session:
                await apply_tenant_guc(session, tenant_id)
                result = await session.execute(
                    text("SELECT COUNT(*)::int FROM event_dead_letters WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id},
                )
                row = result.fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0

    async def mark_replayed(self, entry_id: str, tenant_id: str) -> None:
        # tenant_id was missing from this signature entirely — added here
        # since this method (like the rest of this class besides add()) has
        # zero callers anywhere in the codebase today (confirmed via
        # repo-wide grep), so widening the signature is safe.
        try:
            async with self._session_factory() as session:
                await apply_tenant_guc(session, tenant_id)
                await session.execute(
                    text("""
                        UPDATE event_dead_letters
                        SET replayed_at = :now
                        WHERE id = :id AND tenant_id = :tenant_id
                    """),
                    {"id": entry_id, "tenant_id": tenant_id, "now": datetime.now(timezone.utc)},
                )
                await session.commit()
        except Exception as e:
            logger.error("dlq_replay_mark_failed", extra={"error": str(e), "entry_id": entry_id})

    async def purge_old(self, tenant_id: str, older_than_days: int = 30) -> int:
        try:
            async with self._session_factory() as session:
                await apply_tenant_guc(session, tenant_id)
                # make_interval(days => :days), not INTERVAL ':days days' —
                # a bind parameter inside a quoted string literal is not a
                # valid asyncpg positional parameter (confirmed in isolation:
                # "the server expects 0 arguments for this query, 1 was
                # passed"). Every real call raised, was caught by this
                # method's own except, and silently returned 0 — meaning
                # dead-lettered events were never actually purged.
                result = await session.execute(
                    text("""
                        DELETE FROM event_dead_letters
                        WHERE tenant_id = :tenant_id
                          AND failed_at < NOW() - make_interval(days => :days)
                          AND replayed_at IS NOT NULL
                    """),
                    {"tenant_id": tenant_id, "days": older_than_days},
                )
                await session.commit()
                return result.rowcount
        except Exception:
            return 0
