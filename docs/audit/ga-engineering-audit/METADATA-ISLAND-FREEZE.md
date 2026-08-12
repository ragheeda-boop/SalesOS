# MetaData Island Freeze + KEEP Inventory Pointer

**Date:** 2026-08-12 (pgvector helper consolidate)  
**Finding:** EAB-001-P1-DRIFT-01  
**Disposition:** **Partial (narrowed)** — freeze held; ceiling **18→17** via `pgvector_migration.py` `_embedding_table` → `table()`/`column()`  
**Validation:** light validated (host `rg` count=17; fitness FF-09 ceiling updated)

---

## Remeasure (2026-08-12)

| Metric | Value | Method |
|--------|------:|--------|
| `MetaData(` matches | **17** | `rg MetaData(` under `salesos/backend` `*.py` |
| Distinct files | **16** | same (pgvector_migration removed from inventory) |
| Delta vs 2026-08-08 | **−1** | `pgvector_migration.py` helper → `table()` |

**Prior (EAB-003 structural):** 19→18 via MCP `resources.py` → `table()`/`column()`.  
**Prior (Stream B 2026-08-08):** 18 held.

**Honesty ceiling:** Live GA islands remain. **Do not** claim Fixed. **Do not** raise FF-09 ceiling without DEC + this file update. Next measurable drop = benchmarks share/`table()` (non-prod) or `admin_router.py` COUNT stubs.

**FF-09 ceiling:** **17** (`salesos/scripts/fitness-ci-subset.sh` / `.ps1`).

---

## Freeze rule (effective immediately)

1. **Do not add** new `sqlalchemy.MetaData()` (or private `MetaData()`) islands outside the allowlist below without a DEC that updates this file + FF-09 ceiling.
2. Prefer shared `Base.metadata` (or register stubs via the orphan KEEP path) for live tables.
3. **No DROP** of orphan tables/columns without a dedicated DROP DEC (DEC-130f posture).
4. Benchmark / ephemeral helpers: prefer `sqlalchemy.table()` / `column()` over `MetaData()` so they do not consume the ceiling.

---

## Allowlist (honest inventory — 16 files / 17 matches)

| Path | Notes |
|------|-------|
| `app/db05_orphan_keep.py` | Intentional KEEP private md → copy onto Base |
| `app/application/admin/data_quality.py` | Island |
| `app/tasks.py` | Island |
| `runtime/search_runtime/__init__.py` | Island |
| `runtime/activity_runtime/__init__.py` | Island |
| `runtime/admin_router.py` | Island |
| `runtime/knowledge_graph_runtime/repository/sql_repository.py` | Island |
| `domains/search/engine/postgres_repo.py` | Island |
| `domains/search/engine/vector_store.py` | Island |
| `sdk/search.py` | Island |
| `sdk/events/outbox.py` | Island |
| `sdk/events/store.py` | Island |
| `sdk/audit.py` | Island (`schema="audit"`) |
| `intelligence/memory/postgres_store.py` | Island |
| `benchmark/run.py` | Non-prod benchmark |
| `benchmark/data_generator.py` | **2** matches — non-prod benchmark |

**Removed from allowlist (consolidated):** `mcp_server/resources.py` — `table()`/`column()`.  
**Removed 2026-08-12:** `runtime/knowledge_graph_runtime/pgvector_migration.py` — `_embedding_table` → `table()`/`column()`.

Any **new** file or extra match beyond this list → fail FF-09 until DEC + this doc update.

---

## Migrate plan (ranked backlog — DEC required for Base merges)

| Priority | Candidate | Est. matches saved | Risk | Exit criterion |
|----------|-----------|-------------------:|------|-----------------|
| **Done (EAB-003)** | MCP `resources.py` → `table()` | 1 | Safe | Ceiling 18 |
| **Done (2026-08-12)** | `pgvector_migration.py` helper → `table()` | 1 | Safe | Ceiling 17 + freeze update |
| P1 | Benchmarks share/`table()` | up to 3 | Safe (non-prod) | Ceiling drop; GA islands unchanged |
| P3 | `admin_router.py` COUNT stubs | 1 | Medium | Shared Table or `table()` |
| Later | Unify search_runtime + domains/search postgres_repo | 1–2 | Risky | DEC + CAPABILITY-DUP |
| Later | Events / audit / activity / kg / memory → Base | many | Risky | DEC-130f follow-on sprint |

**Session rule:** live Base consolidations remain **deferred**. Measurable progress = inventory refresh + ranked plan + optional ephemeral −1 (done).

---

## KEEP inventory pointer (authoritative for orphans)

| Artifact | Role |
|----------|------|
| [`salesos/backend/app/db05_orphan_keep.py`](../../../salesos/backend/app/db05_orphan_keep.py) | Orphan KEEP table stubs + `ORPHAN_KEEP_TABLES` |
| [`docs/program/decisions/DEC-130f-DB-05-SLICE-5F-ORPHAN-KEEP-REGISTER.md`](../../program/decisions/DEC-130f-DB-05-SLICE-5F-ORPHAN-KEEP-REGISTER.md) | Slice 5f decision — metadata KEEP register |
| DEC-130 … DEC-130h | Criterion 7.6 phased program |

---

## Related EAB

- DM-06 MetaData count (Axis 41 / DRIFT.md)
- Fitness FF-09 — [FITNESS-CI-SUBSET-PLAN.md](./FITNESS-CI-SUBSET-PLAN.md)
- [EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md](./enterprise-audit-board/history/EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md)
