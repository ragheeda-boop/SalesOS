"""
Agent Queue Service — PostgreSQL-backed lease-based work queue.

Adapted from Comp AI CRM (apps/agent/agent/lib/tasks.ts).
Implements FOR UPDATE SKIP LOCKED claim, lease recovery, retry/exhaust,
and idempotent task scheduling.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.agent_runtime.models import AgentTask, AgentRun

LEASE_MS_FAST = 2 * 60_000
LEASE_MS_RESEARCH = 30 * 60_000

# asyncpg adapts Python lists as PG arrays when the bind is typed ARRAY(String).
# Do not use inline CAST(:kinds AS text[]) / ::text[] — IL-2B.1 showed inline
# type casts on bound params break the asyncpg binary protocol.
_KIND_TEXT_ARRAY = ARRAY(String)


def _claim_kind_clause(
    kinds_include: list[str] | None,
    kinds_exclude: list[str] | None,
) -> tuple[str, dict]:
    """SQL fragment + params for claim_due kind filtering.

    Qualifies ``agent_tasks.kind`` — the candidates CTE has no ``t2`` alias.
    Live dispatcher always passes kinds; a dangling ``t2`` makes claim SQL invalid.
    """
    if kinds_include is not None:
        return "agent_tasks.kind = ANY(:kinds)", {"kinds": list(kinds_include)}
    if kinds_exclude is not None:
        return "agent_tasks.kind != ALL(:kinds)", {"kinds": list(kinds_exclude)}
    return "TRUE", {}


async def claim_due(
    session: AsyncSession,
    tenant_id: str,
    limit: int = 12,
    kinds_include: list[str] | None = None,
    kinds_exclude: list[str] | None = None,
    lease_ms: int = LEASE_MS_RESEARCH,
) -> list[AgentTask]:
    now = datetime.now(timezone.utc)
    lease_until = now + timedelta(milliseconds=lease_ms)
    worker_id = f"celery@{uuid.uuid4().hex[:8]}"

    kind_clause, kind_params = _claim_kind_clause(kinds_include, kinds_exclude)

    query = text(f"""
        WITH candidates AS (
            SELECT id
            FROM agent_tasks
            WHERE tenant_id = :tenant_id
              AND status = 'PENDING'
              AND due_at <= :now
              AND (leased_until IS NULL OR leased_until < :now)
              AND attempts < max_attempts
              AND {kind_clause}
            ORDER BY priority DESC, due_at ASC
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        )
        UPDATE agent_tasks t
        SET status = 'CLAIMED',
            leased_until = :lease_until,
            leased_by = :worker_id,
            lease_generation = COALESCE(t.lease_generation, 0) + 1,
            attempts = t.attempts + 1,
            started_at = COALESCE(t.started_at, :now),
            updated_at = :now
        FROM candidates c
        WHERE t.id = c.id
        RETURNING t.*
    """)
    if "kinds" in kind_params:
        query = query.bindparams(bindparam("kinds", type_=_KIND_TEXT_ARRAY))

    result = await session.execute(query, {
        "tenant_id": tenant_id,
        "now": now,
        "lease_until": lease_until,
        "worker_id": worker_id,
        "limit": limit,
        **kind_params,
    })
    return list(result.fetchall())


async def recover_expired_leases(
    session: AsyncSession,
    tenant_id: str,
) -> int:
    now = datetime.now(timezone.utc)

    query = text("""
        UPDATE agent_tasks
        SET status = 'PENDING',
            leased_until = NULL,
            leased_by = NULL,
            updated_at = :now
        WHERE tenant_id = :tenant_id
          AND status IN ('CLAIMED', 'RUNNING')
          AND leased_until IS NOT NULL
          AND leased_until < :now
          AND attempts < max_attempts
    """)

    result = await session.execute(query, {
        "tenant_id": tenant_id,
        "now": now,
    })
    return result.rowcount


async def retire_exhausted(
    session: AsyncSession,
    tenant_id: str,
) -> int:
    now = datetime.now(timezone.utc)

    query = text("""
        UPDATE agent_tasks
        SET status = 'EXHAUSTED',
            finished_at = :now,
            leased_until = NULL,
            leased_by = NULL,
            updated_at = :now
        WHERE tenant_id = :tenant_id
          AND status IN ('PENDING', 'FAILED')
          AND attempts >= max_attempts
          AND (leased_until IS NULL OR leased_until < :now)
    """)

    result = await session.execute(query, {
        "tenant_id": tenant_id,
        "now": now,
    })
    return result.rowcount


async def complete_task(
    session: AsyncSession,
    task_id: str,
    outcome: str,
    completion_reason: str = "SUCCESS",
    lease_generation: int | None = None,
) -> bool:
    now = datetime.now(timezone.utc)

    if lease_generation is not None:
        query = text("""
            UPDATE agent_tasks
            SET status = 'COMPLETED',
                finished_at = :now,
                outcome = :outcome,
                completion_reason = :reason,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = :now
            WHERE id = :task_id
              AND lease_generation = :gen
              AND status = 'RUNNING'
        """)
        params = {
            "task_id": task_id, "now": now, "outcome": outcome[:1000],
            "reason": completion_reason, "gen": lease_generation,
        }
    else:
        query = text("""
            UPDATE agent_tasks
            SET status = 'COMPLETED',
                finished_at = :now,
                outcome = :outcome,
                completion_reason = :reason,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = :now
            WHERE id = :task_id
              AND status = 'RUNNING'
        """)
        params = {
            "task_id": task_id, "now": now, "outcome": outcome[:1000],
            "reason": completion_reason,
        }

    result = await session.execute(query, params)
    return result.rowcount > 0


async def fail_task(
    session: AsyncSession,
    task_id: str,
    error: str,
    lease_generation: int | None = None,
) -> bool:
    now = datetime.now(timezone.utc)

    if lease_generation is not None:
        query = text("""
            UPDATE agent_tasks
            SET status = CASE
                    WHEN attempts < max_attempts THEN 'PENDING'
                    ELSE 'EXHAUSTED'
                END,
                outcome = :error,
                finished_at = CASE
                    WHEN attempts >= max_attempts THEN :now
                    ELSE finished_at
                END,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = :now
            WHERE id = :task_id
              AND lease_generation = :gen
              AND status IN ('CLAIMED', 'RUNNING')
        """)
        params = {"task_id": task_id, "now": now, "error": error[:1000], "gen": lease_generation}
    else:
        query = text("""
            UPDATE agent_tasks
            SET status = CASE
                    WHEN attempts < max_attempts THEN 'PENDING'
                    ELSE 'EXHAUSTED'
                END,
                outcome = :error,
                finished_at = CASE
                    WHEN attempts >= max_attempts THEN :now
                    ELSE finished_at
                END,
                leased_until = NULL,
                leased_by = NULL,
                updated_at = :now
            WHERE id = :task_id
              AND status IN ('CLAIMED', 'RUNNING')
        """)
        params = {"task_id": task_id, "now": now, "error": error[:1000]}

    result = await session.execute(query, params)
    return result.rowcount > 0


async def schedule_task(
    session: AsyncSession,
    tenant_id: str,
    kind: str,
    reason: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    due_at: datetime | None = None,
    priority: int = 0,
    budget: int = 4,
    idempotency_key: str | None = None,
) -> AgentTask:
    """Schedule a task, merging unfinished work and honoring idempotency_key.

    Idempotency: unfinished (tenant, kind, entity) bumps ``due_at``. If an
    ``idempotency_key`` already exists (including COMPLETED tasks), return that
    row — do not raise UniqueViolation. Concurrent insert races use a savepoint
    and fall back to key lookup.
    """
    from sqlalchemy.exc import IntegrityError

    now = datetime.now(timezone.utc)
    due = due_at or now

    existing = await session.execute(
        text("""
            SELECT id FROM agent_tasks
            WHERE tenant_id = :tid AND kind = :kind
              AND finished_at IS NULL
              AND (entity_type IS NOT DISTINCT FROM :etype)
              AND (entity_id IS NOT DISTINCT FROM :eid)
            LIMIT 1
        """),
        {"tid": tenant_id, "kind": kind, "etype": entity_type, "eid": entity_id},
    )
    row = existing.fetchone()
    if row:
        await session.execute(
            text("UPDATE agent_tasks SET due_at = :due, updated_at = :now WHERE id = :id"),
            {"due": due, "now": now, "id": row.id},
        )
        return await session.get(AgentTask, row.id)

    # COMPLETED (or any prior) row with same key — IL-2A residual UniqueViolation path.
    if idempotency_key:
        by_key = await session.execute(
            text("""
                SELECT id FROM agent_tasks
                WHERE tenant_id = :tid AND idempotency_key = :idem
                LIMIT 1
            """),
            {"tid": tenant_id, "idem": idempotency_key},
        )
        key_row = by_key.fetchone()
        if key_row:
            return await session.get(AgentTask, key_row.id)

    try:
        async with session.begin_nested():
            result = await session.execute(
                text("""
                    INSERT INTO agent_tasks (tenant_id, kind, entity_type, entity_id,
                        priority, due_at, budget, input_data, idempotency_key)
                    VALUES (:tid, :kind, :etype, :eid, :pri, :due, :budget,
                        CAST(:data AS jsonb), :idem)
                    RETURNING *
                """),
                {
                    "tid": tenant_id, "kind": kind, "etype": entity_type, "eid": entity_id,
                    "pri": priority, "due": due, "budget": budget,
                    "data": json.dumps({"reason": reason}), "idem": idempotency_key,
                },
            )
            row = result.fetchone()
            return AgentTask(**dict(row._mapping)) if row else None
    except IntegrityError:
        if not idempotency_key:
            raise
        by_key = await session.execute(
            text("""
                SELECT id FROM agent_tasks
                WHERE tenant_id = :tid AND idempotency_key = :idem
                LIMIT 1
            """),
            {"tid": tenant_id, "idem": idempotency_key},
        )
        key_row = by_key.fetchone()
        if key_row:
            return await session.get(AgentTask, key_row.id)
        raise
