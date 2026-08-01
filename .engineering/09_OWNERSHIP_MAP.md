---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 09 â€” OWNERSHIP MAP

> Code ownership for agent dispatch and change review. Owners are **teams/agent-types** as evidenced in the repo (project conventions), not individuals. Single-owner paths avoid conflicts; shared paths require the coordination protocol (`26`).

## 1. Owner legend

| Owner | Meaning | Evidence |
|---|---|---|
| Backend/Cursor | FastAPI backend, domains, runtime, migrations, tests | `salesos/backend/` |
| Claude | Frontend (Next.js), features, packages, e2e | `salesos/frontend/` |
| Ops | CI, infra, compose, secrets, deploy | `.github/`, `salesos/infra/`, compose files |
| Shared | Capability registry, platform packages, cross-cutting | overlap in map |
| Data team | Import pipelines, scrapers | `data/`, root scrapers |
| Human | Governance, ADRs, constitution, GA posture | `docs/**`, `engineering-os/`, `AGENTS.md` |

## 2. Ownership matrix

| Path / area | Owner | Notes |
|---|---|---|
| `salesos/backend/app/` core | Backend/Cursor | main.py, boot/, config, database, dependencies |
| `salesos/backend/app/modules/identity/` | Backend/Cursor | auth + `_keys/` ðŸ”’ |
| `salesos/backend/app/modules/*` (other 22) | Backend/Cursor | feature modules |
| `salesos/backend/app/routers/` | Backend/Cursor | API surface |
| `salesos/backend/domains/` (19) | Backend/Cursor | DDD domains |
| `salesos/backend/runtime/` (27) | Backend/Cursor | engines; 10 single-file dirs (stub status heuristic) |
| `salesos/backend/sdk/` | Backend/Cursor | kernel â€” gated (Rule 3) |
| `salesos/backend/app/alembic/versions/` | Backend/Cursor | migrations â€” gated (record-not-fix) |
| `salesos/backend/tests/` | Backend/Cursor | test pillars |
| `salesos/frontend/src/app/` | Claude | pages |
| `salesos/frontend/src/features/` | Claude | feature modules |
| `salesos/frontend/src/lib/` | Claude | client, auth, hooks |
| `salesos/frontend/src/middleware.ts` | Claude | gated (auth) |
| `salesos/frontend/src/components`, `application` | Claude | shared UI |
| `salesos/frontend/packages/platform/` | Shared | package shell |
| `salesos/frontend/packages/*` production | Shared | widget-sdk, workspace, search, renderer |
| `salesos/frontend/packages/*` stub | Shared | decision-platform stub, empty pkgs |
| `salesos/frontend/e2e/`, `tests/visual/` | Claude | Playwright |
| `salesos/frontend/server/server.js` | Shared | mock server (review before prod) |
| `.github/workflows/` | Ops | CI/CD |
| `salesos/docker-compose*.yml` | Ops | compose |
| `salesos/infra/` | Ops | k8s, terraform, monitoring, staging |
| `salesos/scripts/` | Ops | deploy/smoke/backup |
| `docs/audit/ga-engineering-audit/` | Human | CANONICAL â€” ðŸ”’ read-only |
| `docs/adr/`, `docs/ADR-Data-001` | Human | ðŸ”’ read-only |
| `docs/CAPABILITY_CATALOG.md` | Human | ðŸ”’ read-only |
| `docs/vnext/`, `docs/program/`, `docs/ops/` | Human | ðŸ”’ read-only |
| `AGENTS.md` | Human | ðŸ”’ read-only |
| `engineering-os/` | Human | submodule â€” ðŸ”’ read-only |
| `data/scripts/`, scrapers | Data team | import pipelines |
| `sales-os/` | â€” | LEGACY â€” avoid |
| `.engineering/` | Bootstrap | owned by bootstrap workflow (this suite) |

## 3. Parallelization guidance

Two tasks are parallel-safe when their owner paths do not overlap AND neither path is Shared. For shared paths use `26` (locks) + `21` (runtime state). Priority conflicts: `docs/**` changes require Human sign-off (frozen); never parallel-edit identity keys, `.env*`, capability catalog, or ADR index.

## 4. When this file changes

- On ownership changes. Mirror `04`, `05`, `29` (owner columns).
