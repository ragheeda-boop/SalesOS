# DEC-113 - DB-05 Slice 1: additive CREATE TABLE for 8 P0 R-09 tables

> **Status:** **Accepted** - Slice 1 **CLOSED** (CREATE TABLE); DB-05 program remains **OPEN**
> **Date:** 2026-08-01
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)
> **Story / risk:** DB-05 / R-20 / R-09
> **Authority:** DEC-111 Slice 0 inventory · DEC-110 deferred-8 pin · DEC-044 Option B · DEC-085 `set_config` · DEC-107 swarm READY
> **Out of scope this land:** ENABLE RLS on deferred-8 · production migrate · Prisma · Category B B1-B7 · DEC-085 `get_db` edits · emails/meetings type Slice 2

---

## 1. Decision

Ship **additive** Alembic `CREATE TABLE` for all **8** Category A deferred P0 tables (R-09), in two domain clusters:

| Cluster | Revision | Tables |
|---|---|---|
| Admin billing / jobs | `a7c3e91f0b05` (down `065d1d3a466b`) | `admin_licenses`, `admin_invoices`, `admin_transactions`, `admin_ai_costs`, `admin_jobs` |
| Workflow / scoring / revenue | `b8d4f02a1c06` (down `a7c3e91f0b05`) | `webhook_endpoints`, `scoring_scorecards`, `revenue_analytics_snapshots` |

| Pin | Value |
|---|---|
| Alembic head (this land) | **`b8d4f02a1c06`** (single head with B1 WIP aside) |
| Parent at authorize | committed tip `065d1d3a466b` @ `630bd77` |
| RLS | **None** - no `ENABLE ROW LEVEL SECURITY` / no policies |
| DEC-085 | **Intact** - `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |
| Remaining P0 CREATE | **0** |

ORM column/index shapes matched from:
- `app/modules/admin/db_models.py`
- `domains/workflow/db_models.py`
- `domains/scoring/infrastructure/postgres_repository.py`
- `domains/revenue/analytics/postgres_repo.py`

Migrations are **idempotent** (inspector skip-if-exists) for init_db / `create_all` drift.

---

## 2. Concurrent B1 note

Category B agent had **untracked** local revision `b110c04e7a01` also revising `065d1d3a466b` (DEC-112 WIP). After wait/pull, B1 was **not** on `origin/master`. Slice 1 landed on committed parent to avoid idle STOP. **B1 must rebase** `b110c04e7a01` -> down_revision **`b8d4f02a1c06`** (do not force-split heads).

---

## 3. Validation

| Check | Result |
|---|---|
| `alembic heads` (Docker poetry; B1 WIP renamed aside) | `b8d4f02a1c06` single head |
| Production `alembic upgrade` | **Not run** |
| `alembic check` full drift | **Not re-run** (no head DB migrate this land) |
| DEC-085 `get_db` | Untouched (execute path uses `set_config`; comments mention SET LOCAL as forbidden) |
| Label | **light validated** |

**Production GO not claimed. CI GREEN not met.**

---

## 4. Next

| Slice | Scope |
|---|---|
| **2** | `emails` / `meetings` UUID vs String(36) authority |
| **3** | Index rename + nullable triage |
| **4+** | Governed ENABLE RLS handoff for the eight (separate from Cat B B1-B7) |
