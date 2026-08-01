---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 07 â€” DEPENDENCY GRAPH

> Who depends on what. Read-before-edit: changing a node below risks its consumers. Enforced at build by `tests/test_architecture.py` (5 rules) and `scripts/arch-compliance.py`.

## 1. Runtime dependency graph (back-end)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ identity     â”‚  â”‚ company      â”‚  â”‚ contact      â”‚  â”‚ (no crm mod) â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚                 â”‚                 â”‚                 â”‚
       â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
               â–¼                 â–¼                 â–¼
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚ opportunity  â”‚  â”‚ revenue_exec â”‚  â”‚ entity_resol â”‚
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
              â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                      â–¼                 â–¼
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚ analytics    â”‚  â”‚ decision_centâ”‚
              â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚                 â”‚
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
   â–¼                        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ search     â”‚        â”‚ timeline   â”‚        â”‚ workflows  â”‚
â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
      â”‚                     â”‚                     â”‚
      â–¼                     â–¼                     â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚             runtime engines (27)                   â”‚
â”‚  search_runtime Â· timeline_runtime Â· workflow_rt  â”‚
â”‚  data_fabric Â· feature_store Â· decision Â· nba Â·   â”‚
â”‚  capability_framework Â· widget_engine Â· ux Â· ...  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚             KERNEL: sdk/                           â”‚
â”‚  capability_registry Â· events Â· telemetry         â”‚
â”‚  (MUST NOT import app/domains/runtime â€” Rule 3)   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚             DATASERVICES                          â”‚
â”‚  Postgres 16 (56 mig) Â· Redis Â· Meilisearch Â·     â”‚
â”‚  Neo4j Â· Kafka(opt) Â· Celery(beat 9)              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## 2. Frontend dependency graph

```
src/app (72 pages) â”€â”€â–º src/features (13) â”€â”€â–º src/lib/api/client.ts â”€â”€â–º BE /api/v1/*
        â”‚                    â”‚
        â””â”€â”€â”€â”€â–º src/components â”€â”€â–º src/application â”€â”€â–º src/lib/hooksÂ·queries
        â””â”€â”€â”€â”€â–º packages/ (21)  â”€â”€ @salesos/widget-sdk, workspace, search, renderer (production)
                               â””â”€ @salesos/decision-platform (STUB), platform (shell), 8 without `src`
```

## 3. Enforced rules (arch-compliance, `tests/test_architecture.py`)

| # | Rule | Check |
|---|---|---|
| 1 | SDK-import | `sdk/` must not import `app/` |
| 2 | Kernelâ†’commercial forbiddance | commercial layers not importable from kernel |
| 3 | No `app` in `sdk` | import graph walker |
| 4 | (SDK consumers) | FE must go through SDK/API, not DB |
| 5 | Commercial-modules-forbidden | `data/`, root, `sales-os/` must not import `app/`/`domains/` |

## 4. Module â†’ runtime mapping (registry-level)

`runtime/capability_framework/` decorators (14): identity, company, data-fabric, search, timeline, feature-store, event-runtime, activity-intelligence, capability-framework (STABLE) Â· knowledge-graph, decision-engine, workflow (BETA) Â· marketplace (DRAFT).
Consumers: `app/routers/source_of_truth.py`, `runtime/ux_runtime/router.py`, `runtime/ui_schema_engine/router.py`, `runtime/object_viewer.py`, `runtime/widget_engine/__init__.py`.

## 5. Database dependency chain

`app/database.py` â†’ Alembic (69 versions, head `a4f7c29e1b80` = DB-05 slice 5d) â†’ Postgres 16. RLS Category A (47 tables, DEC-044) + B1â€“B7 + deferred-8 join RLS landed; policy count 67 per DEC-123a tip-align (not re-probed). `0012_refresh_token_tables` in chain; live enabled-state not re-asserted this pass.

## 6. Test dependency graph

`tests/` â† fixtures (`conftest.py`, `tests/support/` incl. mock keypair) â†’ test pillars: unit / contract / integration / e2e / evaluation. Frontend: `jest.config.js` + `playwright.config.ts` (31 e2e specs) + `tests/visual/`.

## 7. Change blast-radius guide (top consumers)

| Node changed | Likely impacted |
|---|---|
| `sdk/capability_registry.py` | all runtime decorators, FE workspace-gen, `/api/v1/capabilities` |
| `app/boot/routers.py` | every endpoint contract (boot contract) |
| `app/modules/identity/routes.py` | FE auth flows, middleware, all gated routes |
| `app/database.py` | every repository/model |
| `runtime/capability_framework/` | 6 consumers above |
| `frontend/src/middleware.ts` | route protection across all pages |

## 8. When this file changes

- On dependency changes. Re-run `python scripts/arch-compliance.py` (approved) to verify the graph holds.
