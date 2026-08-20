# B03 MIGRATION TARGET RECONCILIATION

**Date:** 2026-08-09
**Method:** READ-ONLY analysis only
**Production modified:** NO

---

## Repository

- **Current HEAD:** `f4aee055fd6e` (untracked — never committed to git)
- **Previous authorized target:** `f7a1b82c3d09`
- **New revision:** `f4aee055fd6e`

## New Migration

| Field | Value |
|-------|-------|
| **Revision** | `f4aee055fd6e` |
| **Down revision** | `f7a1b82c3d09` |
| **Created** | 2026-08-09 01:43:48.016061 |
| **Purpose** | Agent Runtime Phase 1: core tables for durable agent execution |
| **Tables** | `agent_tasks`, `agent_runs`, `agent_actions` |
| **RLS** | ENABLE + FORCE ROW LEVEL SECURITY + `tenant_isolation` policy on all 3 tables |
| **Indexes** | 6 indexes (3 partial, 2 unique partial, 1 standard) |
| **Foreign keys** | `agent_runs.task_id → agent_tasks.id`, `agent_actions.run_id → agent_runs.id`, `agent_actions.task_id → agent_tasks.id`, all `tenant_id → tenants.id` |
| **Data mutations** | None (pure DDL) |
| **Destructive operations** | None (CREATE TABLE only) |
| **Rollback** | Full downgrade: DROP tables in reverse order |
| **Git status** | **UNTRACKED** — never committed to master |

### Tables Created

1. **agent_tasks** — lease-based work queue with fencing token, budget/attempts, idempotency
2. **agent_runs** — execution sessions with budget/cost/token tracking
3. **agent_actions** — side-effect ledger with idempotency, PDP/approval fields

### Classification

- DDL: YES (3 CREATE TABLE, 6 CREATE INDEX)
- INSERT: NO
- UPDATE: NO
- DELETE: NO
- Data migration: NO
- RLS: YES (3 policies)
- Destructive: NO
- Non-destructive: YES

## Application Dependency

### Code references to agent tables

| Module | Reference | Nature |
|--------|-----------|--------|
| `runtime/agent_runtime/models.py` | `AgentTask`, `AgentRun`, `AgentAction` ORM models | Database models |
| `runtime/agent_runtime/__init__.py` | `AgentRuntime` class, raw SQL on `agent_tasks`, `agent_runs` | Runtime orchestrator |
| `runtime/agent_runtime/queue.py` | Raw SQL on `agent_tasks` | Queue management |
| `runtime/agent_runtime/budget.py` | Raw SQL on `agent_runs` | Budget tracking |
| `runtime/agent_runtime/dispatcher.py` | `AgentRuntime` instantiation | Dispatcher |
| `runtime/agent_runtime/preamble.py` | `AgentTask` model import | Preamble builder |
| `app/boot/startup.py` | `_init_agent_runtime()` | Startup init |
| `app/routers/copilot.py` | `AgentTask` from `intelligence.agents` (dataclass, NOT ORM) | Copilot endpoint |
| `intelligence/agents/base.py` | `AgentTask` dataclass | Agent base class |

### Critical distinction

There are **two different `AgentTask` classes**:

1. **`intelligence.agents.base.AgentTask`** — Python `@dataclass`, used by copilot and all agent implementations. **Does NOT require database tables.**
2. **`runtime.agent_runtime.models.AgentTask`** — SQLAlchemy ORM model mapped to `agent_tasks` table. **Requires database tables.**

### Will the application fail without these tables?

**NO.** The `AgentRuntime.__init__()` only stores the session factory — no database queries at construction time. Database queries happen at runtime when tasks are dispatched/claimed. The application will start and all existing endpoints will function. Only the agent runtime dispatch/claim operations would fail if invoked.

## Migration Chain

```
d1a8c35e7f09 (production current)
    ↓ e2b9d46f8a10
    ↓ a4f7c29e1b80
    ↓ f6b2e84c1a90
    ↓ c3a9f12d4e80
    ↓ d4b0e23f5a91
    ↓ e5c1f34a6b02
    ↓ f6d2a45b7c03
    ↓ a7e3b56c8d04
    ↓ b8f4c67d9e15
    ↓ c9e5d78a0f26
    ↓ d0f6e89b1a37
    ↓ e1a7b68c2d05
    ↓ f2b8c79d3e06
    ↓ c4d8e21a9f07
    ↓ e5f9a32b0c08
    ↓ f7a1b82c3d09 (previously authorized target)
    ↓ f4aee055fd6e (UNTRACKED — new, never committed)
```

- **No additional revisions after `f4aee055fd6e`** — confirmed via grep
- **True repository HEAD:** `f4aee055fd6e`

## Validation Status

| Target | Validated | PG18 Tested | Notes |
|--------|-----------|-------------|-------|
| `f7a1b82c3d09` | **YES** | **YES** | 16 revisions, 137 tables, 73 RLS, 72 FORCE RLS |
| `f4aee055fd6e` | **NO** | **NO** | Not included in any isolated validation |

## Production

- **Current revision:** `d1a8c35e7f09`
- **Production modified:** NO
- **Migration executed:** NO
- **Deployment:** NO

## Target Decision

### OPTION A: `f7a1b82c3d09`

| Aspect | Assessment |
|--------|------------|
| **Schema impact** | 137 tables, 73 RLS, 72 FORCE RLS |
| **Application compatibility** | All existing endpoints functional. Agent runtime dispatch/claim would fail (tables missing) but app starts fine. |
| **Validation status** | FULLY VALIDATED — PG16 + PG18 isolated testing |
| **RLS impact** | 6 new policies, all tenant isolation |
| **Data impact** | 3 backfill migrations (idempotent, 0 rows in isolated test) |
| **Rollback implications** | All 16 migrations have downgrade functions |
| **Additional validation needed** | NO |
| **Additional human authorization needed** | Already authorized |

### OPTION B: `f4aee055fd6e`

| Aspect | Assessment |
|--------|------------|
| **Schema impact** | 140 tables, 76 RLS, 75 FORCE RLS (+3 tables, +3 RLS from Option A) |
| **Application compatibility** | Same as Option A. Agent runtime would fully function. |
| **Validation status** | **NOT VALIDATED** — never tested on PG16 or PG18 |
| **RLS impact** | 3 additional `tenant_isolation` policies (consistent pattern) |
| **Data impact** | No additional data mutations beyond Option A |
| **Rolldown implications** | Downgrade exists (DROP tables in reverse order) |
| **Additional validation needed** | **YES** — requires PG18 isolated validation before production |
| **Additional human authorization needed** | **YES** — not covered by previous authorization |
| **Git status** | **UNTRACKED** — file was never committed |

## RECOMMENDATION

**RECOMMENDED TARGET: `f7a1b82c3d09`**

Rationale:

1. **`f4aee055fd6e` has NOT been validated on PG18.** The isolated PG18 testing only covered up to `f7a1b82c3d09`. Migrating to `f4aee055fd6e` without validation violates the established validation protocol.

2. **`f4aee055fd6e` is UNTRACKED in git.** The file was never committed. This suggests it is work-in-progress that was not intended for production deployment at this time.

3. **The current application does NOT require `f4aee055fd6e`.** The app starts and functions without the agent tables. The agent runtime gracefully handles missing tables (init catches exceptions, sets `agent_runtime = None`).

4. **Option A is fully validated and authorized.** 16 revisions, PG16 + PG18 testing, production preflight READY.

5. **Option B can be validated and authorized separately** after Option A is successfully applied to production.

If `f4aee055fd6e` is desired for production, the correct sequence is:
1. Commit the file to git
2. Validate on PG18 (fresh + production-state)
3. Obtain explicit human authorization
4. Apply as a separate migration step after Option A

## Gate

- **B03 Production Reconciliation:** BLOCKED — TARGET RECONCILIATION
- **B05:** BLOCKED

STOP.
