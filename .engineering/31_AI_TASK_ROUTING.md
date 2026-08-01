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

# 31 â€” AI TASK ROUTING

> Task â†’ (read first Â· modify Â· tests Â· owner). Primary dispatch reference for parallel agents.

## 1. Routing matrix

| Task | Read first | Modify | Tests | Owner |
|---|---|---|---|---|
| Fix API endpoint | 14, 28, 08 | `app/routers/` + module | contract + integration | Backend/Cursor |
| Add DB migration | 13, 02, 28 | `app/alembic/versions/` (gated) | migration test + `alembic upgrade head` (Docker, approved) | Backend/Cursor |
| Implement feature store | 29, 07 | `domains/feature_store/`, `runtime/feature_store/` | feature_store tests | Backend/Cursor |
| Implement workflow engine | 29, 07, 28 (ADR-031) | `runtime/workflow_runtime/` (stub) | workflow/webhook tests | Backend/Cursor |
| Replace decision STUB | 29 (CAP-016), 02, 18 | `frontend/packages/platform/decision/` + Decision Center APIs | decision_center tenant-isolation tests + FE | Shared |
| Close SQLi sinks | 15, 02, 00 | `app/application/admin/data_quality.py`, `app/modules/revenue_execution/service.py` | SEC regression tests | Backend/Cursor |
| Align capability registries | 29, 06, 28 | sync/validate scripts + runtime registry | registry tests + `/api/v1/capabilities` | Shared |
| Fix event-bus split-brain | 06, 08, 13 | compose + k8s configmap (gated) | smoke + integration | Ops |
| Deploy GHCR fix (CI-08) | 12, 16, 21 | `.github/workflows/` + GHCR secrets | CI run evidence | Ops |
| VPS secrets (CI-09) | 12, 16, 21 | deploy workflows + vault | CI run evidence | Ops |
| FE page/feature | 05 Â§8-10, 14, 17 | `src/app/`, `src/features/` | jest + playwright | Claude |
| FE auth/middleware | 05, 08, 15 | `src/middleware.ts`, `src/lib/auth/` | e2e auth | Claude |
| ADR index cleanup | 27, 28, 00 | `27`/`28` only (ADRs are Human-owned) | consistency check | Shared (report only) |
| Update capability catalog | 29, 00 | `29` only (catalog Human-owned) | registry drift check | Shared (report only) |
| Add RLS policy | 13, 02 | `scripts/generate_rls_policies.py` + migrations (gated) | RLS verification | Backend/Cursor |
| Refactor domain | 07, 18, 09 | `domains/*` | unit + contract + arch-compliance | Backend/Cursor |
| Write new test pillar | 17, 12 | `tests/` | run narrow suite (approved) | Backend/Cursor |
| Simulate/nba work | 29 (CAP-021) | `runtime/nba_engine/` | nba_engine tests | Backend/Cursor |
| Terraform/K8s change | 16, 09 | `salesos/infra/` (gated) | plan/apply dry-run (approved) | Ops |

## 2. Parallel-safe clusters (no path overlap)

- C1: Backend domain work (`domains/*`) vs FE feature work (`src/features/*`) vs Ops CI (`ci.yml`).
- C2: Decision Center (backend `modules/decision`) vs capability registry sync (`runtime/capability_framework`) â€” different paths.
- C3: Workflow engine (`runtime/workflow_runtime`) vs entity resolution (`modules/entity_resolution`).

## 3. Conflict rules

- Shared paths (capability catalog, registry, platform packages) â†’ serialized via `26` locks.
- Any change touching `app/boot/routers.py` or `app/database.py` is high blast-radius â†’ single agent at a time.
- Docs/ADRs/capability catalog = Human-owned; agents may only draft findings into `18`/`27`/`28`.

## 4. When this file changes

- When task mapping changes. Mirror `09` (owners), `26` (coordination), `30` (parallel matrix).
