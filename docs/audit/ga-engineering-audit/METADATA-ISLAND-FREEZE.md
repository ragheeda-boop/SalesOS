# MetaData Island Freeze + KEEP Inventory Pointer

**Date:** 2026-08-12 (benchmark + admin COUNT stubs → `table()`)  
**Finding:** EAB-001-P1-DRIFT-01  
**Disposition:** **Partial (narrowed)** — freeze held; ceiling **17→13** via benchmark seed/count + `runtime/admin_router.py` COUNT stubs → `table()`/`column()`  
**Validation:** light validated (host `rg` count; fitness FF-09 ceiling updated)

---

## Remeasure (2026-08-12b)

| Metric | Value | Method |
|--------|------:|--------|
| `MetaData(` matches | **13** | `rg MetaData(` under `salesos/backend` `*.py` |
| Distinct files | **13** | same |
| Delta vs prior 17 | **−4** | admin_router (−1) + benchmark/run (−1) + data_generator (−2) |

**Prior (2026-08-12):** 18→17 via `pgvector_migration.py`.  
**Prior (EAB-003 structural):** 19→18 via MCP `resources.py`.

**Honesty ceiling:** Live GA islands remain. **Do not** claim Fixed. **Do not** raise FF-09 ceiling without DEC + this file update.

**FF-09 ceiling:** **13** (`salesos/scripts/fitness-ci-subset.sh` / `.ps1`).

---

## Freeze rule (effective immediately)

1. **Do not add** new `sqlalchemy.MetaData()` (or private `MetaData()`) islands outside the allowlist below without a DEC that updates this file + FF-09 ceiling.
2. Prefer shared `Base.metadata` (or register stubs via the orphan KEEP path) for live tables.
3. **No DROP** of orphan tables/columns without a dedicated DROP DEC (DEC-130f posture).
4. Benchmark / ephemeral / COUNT stubs: prefer `sqlalchemy.table()` / `column()` over `MetaData()` so they do not consume the ceiling.

---

## Allowlist (honest inventory — 13 files / 13 matches)

| Path | Notes |
|------|-------|
| `app/db05_orphan_keep.py` | Intentional KEEP private md → copy onto Base |
| `app/application/admin/data_quality.py` | Island |
| `app/tasks.py` | Island |
| `runtime/search_runtime/__init__.py` | Island |
| `runtime/activity_runtime/__init__.py` | Island |
| `runtime/knowledge_graph_runtime/repository/sql_repository.py` | Island |
| `domains/search/engine/postgres_repo.py` | Island |
| `domains/search/engine/vector_store.py` | Island |
| `sdk/search.py` | Island |
| `sdk/events/outbox.py` | Island |
| `sdk/events/store.py` | Island |
| `sdk/audit.py` | Island (`schema="audit"`) |
| `intelligence/memory/postgres_store.py` | Island |

**Removed from allowlist (consolidated):**  
- `mcp_server/resources.py` — `table()`/`column()`  
- `runtime/knowledge_graph_runtime/pgvector_migration.py` — `table()`/`column()`  
- `runtime/admin_router.py` — COUNT stubs → `table()`/`column()` (2026-08-12b)  
- `benchmark/run.py`, `benchmark/data_generator.py` — seed/count → `table()`/`column()` (2026-08-12b)

Any **new** file or extra match beyond this list → fail FF-09 until DEC + this doc update.

---

## Migrate plan (ranked backlog — DEC required for Base merges)

| Priority | Candidate | Est. matches saved | Risk | Exit criterion |
|----------|-----------|-------------------:|------|-----------------|
| **Done (EAB-003)** | MCP `resources.py` → `table()` | 1 | Safe | Ceiling 18 |
| **Done (2026-08-12)** | `pgvector_migration.py` helper → `table()` | 1 | Safe | Ceiling 17 |
| **Done (2026-08-12b)** | Benchmarks + admin COUNT stubs → `table()` | 4 | Safe (non-prod / COUNT) | Ceiling 13 |
| Later | Unify search_runtime + domains/search postgres_repo | 1–2 | Risky | DEC + CAPABILITY-DUP |
| Later | Events / audit / activity / kg / memory → Base | many | Risky | DEC-130f follow-on sprint |

**Session rule:** live Base consolidations remain **deferred**. Measurable progress = inventory refresh + ranked plan + ephemeral/COUNT drops.

---

## KEEP inventory pointer (authoritative for orphans)

See `salesos/backend/app/db05_orphan_keep.py` and DEC-130f / orphan KEEP docs under ga-engineering-audit.
