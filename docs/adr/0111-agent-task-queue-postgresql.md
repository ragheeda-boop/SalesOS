# ADR-0111: Agent Task Queue — PostgreSQL CTE + FOR UPDATE SKIP LOCKED

**Status:** ACCEPTED
**Date:** 2026-08-09

---

## Context

The Agent Runtime requires a durable task queue that supports concurrent workers,
lease-based claim, retry, and crash recovery. Three options were evaluated:

| Option | Technology | Trade-off |
|--------|-----------|-----------|
| A | PostgreSQL (CTE + FOR UPDATE SKIP LOCKED) | Proven by Comp AI. Zero new infra. Same DB as tasks+results. |
| B | Redis + Celery | Celery is already deployed for background jobs. No lease mechanism in CeleryTaskQueue. |
| C | Kafka | Provisioned but idle (ADR-0109). Overkill for agent dispatch volume (~0 tasks/min). |

## Decision

**PostgreSQL is the agent task queue.** Celery Beat (60s cron) triggers the dispatcher.
Celery workers execute agent sessions. PostgreSQL holds task state and handles leasing.

The queue is NOT Redis-backed and NOT Celery's internal task queue. Celery is the
scheduler and executor; PostgreSQL is the durable queue.

## Claim Query (Corrected CTE Pattern)

```sql
-- claimDue: atomic claim with lease and fencing token
WITH candidates AS (
    SELECT id
    FROM agent_tasks
    WHERE tenant_id = :tenant_id
      AND status = 'PENDING'
      AND due_at <= :now
      AND (leased_until IS NULL OR leased_until < :now)
      AND attempts < max_attempts
    ORDER BY priority DESC, due_at ASC
    LIMIT :batch_size
    FOR UPDATE SKIP LOCKED
)
UPDATE agent_tasks t
SET status = 'CLAIMED',
    leased_until = :now + :lease_duration,
    leased_by = :worker_id,
    lease_generation = COALESCE(t.lease_generation, 0) + 1,
    attempts = t.attempts + 1,
    started_at = COALESCE(t.started_at, :now)
FROM candidates c
WHERE t.id = c.id
RETURNING t.*;
```

## Lease Recovery

```sql
-- recoverExpiredLeases: return orphaned tasks to PENDING
UPDATE agent_tasks
SET status = 'PENDING',
    leased_until = NULL,
    leased_by = NULL
WHERE status IN ('CLAIMED', 'RUNNING')
  AND leased_until IS NOT NULL
  AND leased_until < :now
  AND attempts < max_attempts;
```

## Dispatch Cycle (every 60s via Celery Beat)

```
recoverExpiredLeases()   →  CLAIMED/RUNNING + expired → PENDING
retireExhausted()        →  attempts >= max → EXHAUSTED
claimDue()               →  PENDING → CLAIMED
dispatch                 →  fast lane (non-LLM) + research lane (LLM)
```

## Lease Durations

| Lane | Tasks | Lease | Batch | Concurrency |
|------|-------|------:|------:|------------:|
| Fast | brand, portrait, simple lookups | 2 min | 60 | 6 |
| Research | research, enrichment, scoring | 30 min | 12 | 12 |

## Idempotency

`agent_tasks` has a partial unique index `UNIQUE (tenant_id, idempotency_key) WHERE
idempotency_key IS NOT NULL`. This prevents duplicate task creation at the queue level,
independent of the `agent_actions` idempotency guard which protects side effects.

## Consequences

- **No new infrastructure** — PostgreSQL is the existing system of record.
- **FOR UPDATE SKIP LOCKED** guarantees disjoint claims across concurrent dispatchers.
- **lease_generation** provides fencing tokens (see ADR-0112).
- Graceful degradation: if PostgreSQL is down, everything is down anyway.
- Scale ceiling: ~10K tasks/min on PostgreSQL. Sufficient for years.

## Related

- ADR-0110: Agent Runtime re-scope
- ADR-0112: Agent State Machine
- ADR-0109: Kafka event bus posture
