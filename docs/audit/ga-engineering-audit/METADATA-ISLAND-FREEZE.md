# MetaData Island Freeze + KEEP Inventory Pointer

**Date:** 2026-08-08 (Completion Program Stream B M1 remeasure)  
**Finding:** EAB-001-P1-DRIFT-01  
**Disposition:** **Partial (held)** — freeze + ceiling **18** reconfirmed; no further consolidate this wave (pgvector P1 deferred — outside Stream B code lock)  
**Validation:** light validated (host `rg` count=18; fitness FF-09 PASS)

---

## Remeasure (Completion Program Stream B — 2026-08-08)

| Metric | Value | Method |
|--------|------:|--------|
| `MetaData(` matches | **18** | `rg MetaData(` under `salesos/backend` `*.py` |
| Distinct files | **17** | same |
| Delta vs EAB-003 structural | **0** | Freeze held; no island add/remove this wave |

**Prior (EAB-003 structural):** 19→18 via MCP `resources.py` → `table()`/`column()`.

**Honesty ceiling:** Live GA islands remain. **Do not** claim Fixed. **Do not** raise FF-09 ceiling without DEC + this file update. Next measurable drop = P1 `pgvector_migration.py` helper → `table()` (Director unlock / DEC).

**FF-09 ceiling:** **18** (`salesos/scripts/fitness-ci-subset.sh` / `.ps1`).

---

## Freeze rule (effective immediately)

1. **Do not add** new `sqlalchemy.MetaData()` (or private `MetaData()`) islands outside the allowlist below without a DEC that updates this file + FF-09 ceiling.
2. Prefer shared `Base.metadata` (or register stubs via the orphan KEEP path) for live tables.
3. **No DROP** of orphan tables/columns without a dedicated DROP DEC (DEC-130f posture).
4. Benchmark / ephemeral helpers: prefer `sqlalchemy.table()` / `column()` over `MetaData()` so they do not consume the ceiling.

---

## Allowlist (honest inventory — 17 files / 18 matches)

| Path | Notes |
|------|-------|
| `app/db05_orphan_keep.py` | Intentional KEEP private md → copy onto Base |
| `app/application/admin/data_quality.py` | Island |
| `app/tasks.py` | Island |
| `runtime/search_runtime/__init__.py` | Island |
| `runtime/activity_runtime/__init__.py` | Island |
| `runtime/admin_router.py` | Island |
| `runtime/knowledge_graph_runtime/pgvector_migration.py` | Transient `MetaData()` in helper — next safe candidate |
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

**Removed from allowlist (consolidated):** `mcp_server/resources.py` — now uses `table()`/`column()`.

Any **new** file or extra match beyond this list → fail FF-09 until DEC + this doc update.

---

## Migrate plan (ranked backlog — DEC required for Base merges)

| Priority | Candidate | Est. matches saved | Risk | Exit criterion |
|----------|-----------|-------------------:|------|-----------------|
| **Done (EAB-003)** | MCP `resources.py` → `table()` | 1 | Safe | Ceiling 18 |
| P1 | `pgvector_migration.py` helper → `table()` | 1 | Safe–medium | Ceiling 17 + freeze update |
| P2 | Benchmarks share/`table()` | up to 3 | Safe (non-prod) | Ceiling drop; GA islands unchanged |
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
