# ADR-0112: Agent State Machine + Fencing + Execution Identity

**Status:** ACCEPTED
**Date:** 2026-08-09

---

## Context

The Agent Runtime needs a clear state machine for task lifecycle, a fencing mechanism
to prevent stale workers from performing writes after losing ownership, and a consistent
model for execution identity across retries and approval cycles.

## Decision

### State Machine (Phase 1 — no WAITING state)

```
PENDING  →  CLAIMED  →  RUNNING  →  COMPLETED
                          │
                          └─────── →  FAILED
                                       │
                                  ┌────┴────┐
                             attempts<     attempts>=
                             max           max
                                  │            │
                              PENDING     EXHAUSTED
```

**Phase 3 adds:** `RUNNING → REQUIRES_APPROVAL → PENDING → CLAIMED → RUNNING`

### Valid Transitions

| From | To | Trigger | Fencing |
|------|----|---------|---------|
| PENDING | CLAIMED | `claimDue()` — CTE + SKIP LOCKED | `lease_generation++` |
| CLAIMED | RUNNING | `startSession()` | `WHERE lease_generation = :gen` |
| RUNNING | COMPLETED | `completeTask()` | `WHERE lease_generation = :gen` |
| RUNNING | FAILED | `failTask()` — also handles retry/exhaust | `WHERE lease_generation = :gen` |
| FAILED | PENDING | `failTask()` itself (attempts < max) | Atomic with fail |
| FAILED | EXHAUSTED | `failTask()` itself (attempts >= max) | Atomic with fail |
| CLAIMED | PENDING | `recoverExpiredLeases()` | System (no worker) |
| RUNNING | PENDING | `recoverExpiredLeases()` | System (no worker) |
| PENDING | EXHAUSTED | `retireExhausted()` | System |

### Fencing (lease_generation)

Every worker-originated state transition and every budget spend MUST verify
`lease_generation` atomically in the same transaction:

```sql
UPDATE agent_tasks
SET status = 'COMPLETED', finished_at = :now, outcome = :outcome
WHERE id = :task_id
  AND lease_generation = :my_generation
  AND status = 'RUNNING';
-- 0 affected rows → STALE_WORKER
```

### Execution Identity Model

| Scenario | `agent_task.id` | `agent_run.id` | `lease_generation` |
|----------|:---:|:---:|:---:|
| Retry after failure | SAME | **NEW** | NEW |
| Approval resume | SAME | **SAME** | NEW |
| Worker crash recovery | SAME | Depends on phase | NEW |
| Normal completion | SAME | SAME | Constant |

### failTask() — Atomic Retry or Exhaust

```sql
UPDATE agent_tasks
SET status = CASE
        WHEN attempts < max_attempts THEN 'PENDING'
        ELSE 'EXHAUSTED'
    END,
    outcome = :error,
    leased_until = NULL,
    leased_by = NULL,
    finished_at = CASE
        WHEN attempts >= max_attempts THEN :now
        ELSE finished_at
    END
WHERE id = :task_id
  AND lease_generation = :my_generation
  AND status = 'RUNNING';
```

## Consequences

- Clear ownership boundaries: `agent_run.id` = execution identity, `lease_generation` = worker identity.
- Fencing prevents stale workers from mutating state after losing ownership.
- Worker crash recovery is automatic via `recoverExpiredLeases`.
- No in-memory-only states — every transition is a database write.

## Related

- ADR-0110: Agent Runtime re-scope
- ADR-0111: Task Queue strategy
