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

# 06 â€” ARCHITECTURE MAP

> The architecture as-built and as-governed. **This file describes what exists; it does not license changes.** Change authority lives in `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` + `engineering-os/`.

## 1. System context (as-built)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  FE: Next.js 15 App       â”‚  HTTPS  â”‚  BE: FastAPI (Python 3.12)   â”‚
â”‚  src/app (72 pages)       â”‚â—„â”€â”€â”€â”€â”€â”€â–ºâ”‚  app/main.py factory          â”‚
â”‚  src/lib/api/client.ts    â”‚  Bearer â”‚  app/boot/routers.py (67)    â”‚
â”‚  src/middleware.ts (auth) â”‚  JWT    â”‚  modules/ domains/ runtime/  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚                                        â”‚
           â–¼                                        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Postgres 16       â”‚      â”‚ Redis        â”‚  â”‚ Meilisearch  â”‚  â”‚ Neo4j (opt)  â”‚
â”‚ (66 migrations,   â”‚      â”‚ (cache/rate) â”‚  â”‚ (search)     â”‚  â”‚ (graph)      â”‚
â”‚  RLS A + B1..B7)  â”‚      â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚ optional / degraded per compose
        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Kafka (opt)  â”‚  â”‚ Celery worker â”‚  â”‚ Celery beat (9 jobs)  â”‚
â”‚ default      â”‚  â”‚ (in_memory   â”‚  â”‚ â”€ or Kubernetes cron   â”‚
â”‚ in_memory    â”‚  â”‚ event bus =  â”‚  â”‚  per configmap)        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## 2. Layering (as governed â€” kernel rule, enforced in `tests/test_architecture.py`)

| Layer | Location | May import |
|---|---|---|
| Presentation/API | `app/routers/`, `app/modules/*/routes.py`, `app/graphql/` | application, domain, runtime, sdk |
| Application | `app/modules/`, `app/application/` | domain, runtime, sdk |
| Domain (DDD) | `domains/` | runtime, sdk |
| Runtime engines | `runtime/` | sdk |
| Kernel | `sdk/` | stdlib/3rd-party ONLY (no app imports â€” Rule 3) |
| Commercial (LEGACY boundary) | anything importing `domains/` or `app/` from `data/`, root, `sales-os/` | **FORBIDDEN** (arch Rule 5) |

Architecture rules (`salesos/backend/tests/test_architecture.py`): (1) SDK-import rule â€” kernel must not import app; (2) kernelâ†’commercial forbiddance â€” commercial layers must not be imported into kernel; (3) no `app` import inside `sdk`; (4) â€¦; (5) commercial-modules-forbidden. Full text: `25_CHANGE_PROTOCOL` Â§Rules.

## 3. Backend composition (as-built)

- **Router registry:** `app/boot/routers.py` â€” 67 `include_router` registrations; every route in the app must be registered here (boot contract).
- **Modules:** `app/modules/` â€” 23 feature modules (identity, company, contact, opportunity, revenue_execution, entity_resolution, decision, source_of_truth, ...). **No `crm` module exists** (v3.0 invented it; corrected).
- **Domains:** `domains/` â€” 17 DDD domains (+ `app/domains/customer_success`).
- **Runtimes:** `runtime/` â€” 27 engine dirs; 10 single-file dirs (agent_runtime, simulation_runtime, workflow_runtime, context_runtime, execution_runtime, memory_runtime, policy_runtime, recommendation_runtime, scheduler_runtime, widget_engine). Stub status heuristic, not individually proven (see `23`).
- **SDK kernel:** `sdk/` â€” capability registry (~25), event system, telemetry.
- **Event bus:** default `EVENT_BUS_TYPE=in_memory` (degraded); Kafka optional. **Split-brain:** compose runs in_memory, K8s configmap expects kafka â†’ events diverge per environment (observed; `02`).
- **Async:** Celery `-A app.celery_app`; beat has 9 jobs.

## 4. Frontend composition (as-built)

- **App Router pages:** `src/app` â€” 72 `page.tsx`; route groups `auth`, `dashboard`, `v3`, `(google) callback`.
- **Middleware:** `src/middleware.ts` â€” route protection + token refresh on browser side.
- **API client:** `src/lib/api/client.ts` â€” injects Bearer token (browser); server-side direct calls.
- **Features:** `src/features/` â€” 13 feature modules.
- **Packages:** `packages/` â€” 21 workspace packages; 13 with `src`, 8 without (incl. `@salesos/decision-platform` = STUB).
- **Workspace generator:** `@salesos/workspace-generator` generates workspaces from capability registry (empty stub).
- **Apps:** `apps/` â€” 4 EMPTY shells.

## 5. Data layer (as-built)

- **Postgres 16**, Alembic-managed, 69 migrations; head `a4f7c29e1b80` (DB-05 slice 5d; DEC-142). RLS Category A (47 tables) + B1â€“B7 + deferred-8 join RLS landed. `0012_refresh_token_tables` in chain; live enabled-state not re-asserted this pass.
- **RLS:** 47 Category-A tables (DEC-044) + B1â€“B7 join policies; policy count 59 per DEC-120 Slice C staging (not re-computed).
- **Search:** pgvector + pg_trgm fulltext + Meilisearch.
- **Graph:** Neo4j configured for knowledge graph.
- **Cache:** Redis.

## 6. Governance overlay (as-governed â€” not code)

| Dimension | Authority |
|---|---|
| GO/NO-GO | `docs/audit/ga-engineering-audit/` â€” **NO-GO** (Production 38, Security 48; `security-audit-report-latest.json` 51.6/100, 30 critical failures) |
| Waves | `PRODUCTION_PLAN.md` Waves 0â€“14 |
| ADRs | `docs/adr/` (6 tracked) + `engineering-os/adr/` (6) + `docs/ADR-Data-001` â€” see `27` |
| Capability governance | `docs/CAPABILITY_CATALOG.md` + `engineering-os/kernel/capability-registry.yaml` |
| Decisions | `docs/program/decisions/DEC-*`, `docs/vnext/DECISIONS.md` D-* |

## 7. Known architectural defects (observe only)

1. Event bus split-brain (in_memory vs kafka) â†’ event guarantees differ per env.
2. Capability registry 4-way drift (see `29` Â§4).
3. Dual capability registry requires sync scripts to align (EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30 #9/#17; DEBT-ARC-003, E-21).
4. SQLi sinks: `app/application/admin/data_quality.py`, `app/modules/revenue_execution/service.py` (SEC critical).
5. ADR index vs file status conflicts (see `27`).

## 8. When this file changes

- On architectural change, engine add/removal, layer rule change, or data-layer change. Must mirror `07` (dependency graph), `24` (manifest), `29` (capabilities).
