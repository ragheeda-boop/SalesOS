# MetaData Island Freeze + KEEP Inventory Pointer

**Date:** 2026-08-13 (`table()` query/DML stubs; ceiling **13→6**)  
**Finding:** EAB-001-P1-DRIFT-01  
**Disposition:** **Partial (narrowed)** — freeze held; ceiling **13→6** via seven query/DML stubs → `table()`/`column()`. Live Base merges still **blocked** on [DEC-156](../../program/decisions/DEC-156-METADATA-BASE-MERGE-RESIDUAL.md) (**Proposal — not Accepted**).  
**Validation:** light validated (host `rg` count; fitness FF-09 ceiling updated)

---

## Remeasure (2026-08-13)

| Metric | Value | Method |
|--------|------:|--------|
| `MetaData(` matches | **6** | `rg MetaData(` under `salesos/backend` `*.py` |
| Distinct files | **6** | same |
| Delta vs prior 13 | **−7** | data_quality, tasks, search_runtime, postgres_repo, sdk/search, sdk/audit, intelligence/memory |

**Prior (2026-08-12b):** 17→13 via benchmark + admin COUNT stubs.  
**Prior (2026-08-12):** 18→17 via `pgvector_migration.py`.  
**Prior (EAB-003 structural):** 19→18 via MCP `resources.py`.

**Honesty ceiling:** Live GA islands remain. **Do not** claim Fixed. **Do not** raise FF-09 ceiling without DEC + this file update.

**FF-09 ceiling:** **6** (`salesos/scripts/fitness-ci-subset.sh` / `.ps1`).

---

## Freeze rule (effective immediately)

1. **Do not add** new `sqlalchemy.MetaData()` (or private `MetaData()`) islands outside the allowlist below without a DEC that updates this file + FF-09 ceiling.
2. Prefer shared `Base.metadata` (or register stubs via the orphan KEEP path) for live tables.
3. **No DROP** of orphan tables/columns without a dedicated DROP DEC (DEC-130f posture).
4. Benchmark / ephemeral / COUNT / query-DML stubs: prefer `sqlalchemy.table()` / `column()` over `MetaData()` so they do not consume the ceiling.
5. **Do not** merge remaining live Bases without **Accepted** DEC-156 (proposal only as of 2026-08-13).

---

## Allowlist (honest inventory — 6 files / 6 matches)

| Path | Notes |
|------|-------|
| `app/db05_orphan_keep.py` | Intentional KEEP private md → copy onto Base |
| `runtime/activity_runtime/__init__.py` | Island — `Index()` KEEP; `to_metadata(Base)` |
| `runtime/knowledge_graph_runtime/repository/sql_repository.py` | Island — `graph_edges` Index KEEP; `to_metadata(Base)` |
| `domains/search/engine/vector_store.py` | Island — `_PgVector` + Index KEEP; `vectors` copied to Base |
| `sdk/events/outbox.py` | Island — `Index()` + runtime `create_all()` |
| `sdk/events/store.py` | Island — `domain_events` Index KEEP; `to_metadata(Base)` |

**Removed from allowlist (consolidated):**  
- `mcp_server/resources.py` — `table()`/`column()`  
- `runtime/knowledge_graph_runtime/pgvector_migration.py` — `table()`/`column()`  
- `runtime/admin_router.py` — COUNT stubs → `table()`/`column()` (2026-08-12b)  
- `benchmark/run.py`, `benchmark/data_generator.py` — seed/count → `table()`/`column()` (2026-08-12b)  
- `app/application/admin/data_quality.py` — companies query stub → `table()`/`column()` (2026-08-13)  
- `app/tasks.py` — companies/contacts Celery stubs → `table()`/`column()` (2026-08-13)  
- `runtime/search_runtime/__init__.py` — companies query stub → `table()`/`column()` (2026-08-13)  
- `domains/search/engine/postgres_repo.py` — companies query stub → `table()`/`column()` (2026-08-13)  
- `sdk/search.py` — embedding collection stubs → `table()`/`column()` (2026-08-13)  
- `sdk/audit.py` — `audit.audit_log` DML stub → `table()`/`column()` (2026-08-13)  
- `intelligence/memory/postgres_store.py` — episodic_memory DML stub → `table()`/`column()` (2026-08-13)

Any **new** file or extra match beyond this list → fail FF-09 until DEC + this doc update.

---

## Migrate plan (ranked backlog — DEC required for Base merges)

| Priority | Candidate | Est. matches saved | Risk | Exit criterion |
|----------|-----------|-------------------:|------|-----------------|
| **Done (EAB-003)** | MCP `resources.py` → `table()` | 1 | Safe | Ceiling 18 |
| **Done (2026-08-12)** | `pgvector_migration.py` helper → `table()` | 1 | Safe | Ceiling 17 |
| **Done (2026-08-12b)** | Benchmarks + admin COUNT stubs → `table()` | 4 | Safe (non-prod / COUNT) | Ceiling 13 |
| **Done (2026-08-13)** | DQ / tasks / search stubs / sdk search / audit / memory → `table()` | 7 | Safe (query/DML; not KEEP/`create_all`) | Ceiling 6 |
| **Blocked** | Residual six → `Base.metadata` | 6 | Risky | **DEC-156 Accepted** (proposal only) |

**Session rule:** live Base consolidations remain **deferred** until DEC-156 is Accepted. Measurable progress this land = `table()` stubs + freeze/FF-09 ceiling **6** + DEC-156 proposal.

---

## KEEP inventory pointer (authoritative for orphans)

See `salesos/backend/app/db05_orphan_keep.py` and DEC-130f / orphan KEEP docs under ga-engineering-audit.
