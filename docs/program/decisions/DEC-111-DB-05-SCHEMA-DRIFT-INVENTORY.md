# DEC-111 — DB-05 Slice 0: schema drift inventory kickoff (R-20 / R-09)

> **Status:** **Accepted** — Slice 0 inventory **CLOSED**; DB-05 program remains **OPEN** (multi-sprint)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS)  
> **Story / risk:** DB-05 / R-20 / R-09  
> **Authority:** DEC-020 · DEC-021 · DEC-022 (CI-15 local-only; systemic → DB-05) · DEC-044 Option B (8 R-09 tables wait) · DEC-110 Category A deferred pin · DEC-107 swarm READY  
> **Out of scope this land:** production migrate · Prisma · Alembic DDL churn · ENABLE RLS on deferred tables · Category B join SQL · CI-22 / CI-08 / CI-19 reopen · DEC-085 `get_db` / `set_config`

---

## 1. Decision

Kick off **DB-05** with **Slice 0 only**: a prioritized, evidence-backed **schema drift inventory** (Alembic heads vs ORM models vs known CI/prod notes). Do **not** ship reconciliation migrations in this land.

| Pin | Value |
|---|---|
| Alembic graph | **56** revision files; **single head** `065d1d3a466b` (`enable_rls_company_features`; down `07e3ec4084fc`) |
| ORM `__tablename__` scan | **80** tables (`app/` + `domains/` + `runtime/`; tests/alembic excluded) |
| Alembic `create_table` | **89** distinct table names across versions |
| Category A deferred (DEC-110 / R-09) | **8** ORM+`tenant_id` tables with **no** `create_table` — confirmed |
| Extra ORM without `create_table` | **4** (3 global admin + 1 UBOM stub) — not Category A deferred |
| Migration without matching ORM | **21** (legacy / renamed / non-ORM paths) — triage later |
| Historic `alembic check` (CI-15) | **~300** drift lines beyond analytics after `07e3ec4084fc` (DEC-021) — **not re-run** this land (no Docker DB migrate) |

**Validation label:** **docs / light validated** (revision-graph parse + ORM/`create_table` skim + migration/model spot-check). No production migrate. No `alembic upgrade`. **Production GO not claimed. CI GREEN not met.**

---

## 2. Inventory method (light validated)

1. Parse `salesos/backend/app/alembic/versions/*.py` revision / `down_revision` → heads.  
2. Scan `__tablename__` under `app/`, `domains/`, `runtime/`.  
3. Scan `op.create_table("…")` across versions.  
4. Cross-check DEC-110 §4 eight-table list + Sprint 01 deferred list.  
5. Spot-check known R-20 clusters (`emails`/`meetings` UUID vs `String(36)`; DLQ; companies).  
6. **Hard stop:** do not edit `get_db()` — must remain `SELECT set_config('app.tenant_id', :tenant_id, true)` (**DEC-085**).

---

## 3. Prioritized findings

### P0 — Missing CREATE TABLE (blocks RLS / R-09)

ORM defines `tenant_id`; **no** Alembic `create_table`. **No ENABLE RLS** until Slice 1+ lands schema (DEC-044 / DEC-110).

| # | Table | Model path | Priority note |
|---|---|---|---|
| 1 | `webhook_endpoints` | `domains/workflow/db_models.py` | Workflow domain; sibling `webhook_subscriptions` already Category A live |
| 2 | `scoring_scorecards` | `domains/scoring/infrastructure/postgres_repository.py` | Scoring domain |
| 3 | `revenue_analytics_snapshots` | `domains/revenue/analytics/postgres_repo.py` | Revenue analytics |
| 4–6 | `admin_licenses`, `admin_invoices`, `admin_transactions` | `app/modules/admin/db_models.py` | Billing; `tenant_id` UUID NOT NULL |
| 7–8 | `admin_ai_costs`, `admin_jobs` | `app/modules/admin/db_models.py` | Nullable `tenant_id` — design carefully before RLS |

### P1 — Confirmed type / shape drift (migrated tables; ORM≠DDL)

| Cluster | Evidence | Risk |
|---|---|---|
| `emails` / `meetings` | Migration `0013_meetings_emails.py`: `id`/`tenant_id`/`opportunity_id` as `sa.UUID()`; ORM `String(36)` in `domains/commercial/infrastructure/models.py` | Autogenerate + runtime cast friction; RLS policies cast `::text` (mitigates some) |
| `companies` ORM-removed columns | R-20 / CI-15: DB may still hold `branch_count`, `revenue_prev_year`, `tsv`, `search_vector`, `parent_company_id`, … not on current `Company` model | Dead columns / autogenerate noise |
| Index rename class | R-20: `ix_rev_*` → `ix_*` on opportunities/tasks/contacts/webhooks | Autogenerate churn; low runtime risk if names only |
| Nullable / type deltas | R-20: workflow, notifications, scheduled_jobs, feature tables | Needs per-table Slice triage |

**Note:** `dead_letter_queue.id` — tip model + `0011_dead_letter_queue.py` both **Integer** PK (aligned). Historic R-20 “INTEGER vs UUID” line treated as **stale unless `alembic check` re-proves** against a live head DB.

### P2 — Adjacent inventory (not Category A deferred)

| Item | Tables | Disposition |
|---|---|---|
| Global admin (no `tenant_id`) | `admin_plans`, `admin_feature_flags`, `admin_health_snapshots` | Still **no** `create_table`; Owner/global path — **not** DEC-110 deferred-8; optional later CREATE |
| UBOM stub | `deals` (`domains/ubom/__init__.py`) | Exclude from GA schema reconciliation until product path exists |
| CREATE without ORM | **21** tables (e.g. `activity_records`, `rag_*`, `graph_*`, `company_intent_*`, …) | Likely renamed/legacy; classify in Slice 2+ — do not drop blindly |

### P3 — Process / CI notes

| Note | Source |
|---|---|
| Analytics local drift **CLOSED** (CI-15 / R-19) | `07e3ec4084fc`; systemic remains R-20 |
| CI-15 migration file left **10 Ruff style** residuals on lint backlog | DEC-022 — not DB-05 Slice 0 |
| Semgrep alembic residual **11** accepted | DEC-103 / DEC-105 — **do not churn** RLS migrations for Semgrep |
| Prod migrate | **Forbidden** this land; Railway/image promote out of scope |

---

## 4. Recommended next slices (not this land)

| Slice | Scope | Exit |
|---|---|---|
| **0** | *(this DEC)* Inventory + priorities | **CLOSED** |
| **1** | Additive **CREATE TABLE** for P0 eight (R-09) — one domain cluster per PR preferred (e.g. webhook → scoring → revenue → admin billing) | upgrade/downgrade PASS on non-prod; models match DDL; **still no RLS** |
| **2** | Type reconciliation for `emails`/`meetings` (choose ORM→UUID **or** DDL→String(36); document authority) | `alembic check` cluster clear; adversarial suites still green |
| **3** | Index rename + nullable/type triage (batch, low-risk) | Drift line count ↓; no silent data loss |
| **4+** | After CREATE exists: hand off **ENABLE RLS** for the eight to governed RLS path (separate from Category B B1–B7) | POLICY_COUNT growth only with explicit AC |

**Principle (unchanged):** Local stories fix local drift. Systemic drift stays **DB-05**. Category B execution (DEC-110 B1–B7) must **not** ENABLE RLS on these eight.

---

## 5. Non-goals / honesty

- No Production GO / External pilot / pilot-ready claim.  
- No whole-pipeline CI GREEN claim (CI-08 GHCR still BLOCKED).  
- No Prisma. No production `alembic upgrade`.  
- Do not reopen STORY-02-01 (`POLICY_COUNT` **47**).  
- Do not conflict with Category B SQL lands or CI-22 residual work.

---

## 6. Records to update

- Board: DB-05 → **IN PROGRESS** (Slice 0 COMPLETE; program OPEN).  
- `EXECUTION_DAG.md`: DB-05 Slice 0 CLOSED; next = Slice 1 CREATE.  
- `RISK_REGISTER.md` R-20 / R-09 next-action → inventory pinned DEC-111.  
- `DECISION_LOG.md` entry DEC-111.
