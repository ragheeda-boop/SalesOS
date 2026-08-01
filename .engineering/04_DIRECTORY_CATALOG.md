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

# 04 â€” DIRECTORY CATALOG

> Machine- and agent-readable catalog of every significant directory. Purpose (business + technical), owner, criticality, safe-to-modify policy. Locked (read-only) paths marked **ðŸ”’** (see `22_FILE_LOCKS.json`).

## 1. Backend (`salesos/backend/`)

| Path | Purpose (business) | Purpose (technical) | Owner | Criticality | Safe to modify |
|---|---|---|---|---|---|
| `app/` | Product core | FastAPI application package | Backend/Cursor | CRITICAL | Yes, gated |
| `app/main.py` | â€” | App factory, middleware, startup, health routes (`/ping`, `/health/live`, `/health/detailed`) | Backend/Cursor | CRITICAL | Yes, gated |
| `app/boot/` | â€” | Router registry (67 include_router), startup hooks | Backend/Cursor | CRITICAL | Yes, gated |
| `app/config.py` | â€” | Pydantic settings; `feature_ai_copilot=False` default | Backend/Cursor | CRITICAL | Yes, gated |
| `app/database.py` | â€” | SQLAlchemy session/engine; create_app_db/check_backend_db helpers | Backend/Cursor | CRITICAL | Yes, gated |
| `app/dependencies.py` | â€” | Shared FastAPI deps (tenant, auth guards) | Backend/Cursor | HIGH | Yes, gated |
| `app/modules/` | Business modules | 23 feature modules (identity, company, contact, opportunity, revenue_execution, entity_resolution, decision, ...) â€” no `crm` module exists | Backend/Cursor | HIGH | Yes, gated |
| `app/modules/identity/` | IAM | auth flows, JWKS (`jwks.py`), `_keys/` (ðŸ”’) | Backend/Cursor | CRITICAL | Yes, gated; `_keys/` NEVER |
| `app/modules/identity/_keys/` | â€” | RSA private/public keypair (ðŸ”’) | Ops | CRITICAL | NEVER |
| `app/routers/` | API surface | One file per endpoint group (companies, opportunities, search, workflows, analytics, ai, copilot, ...) | Backend/Cursor | HIGH | Yes, gated |
| `app/graphql/` | â€” | GraphQL schema (read-only /graphql) | Backend/Cursor | MEDIUM | Yes |
| `app/alembic/` | â€” | DB migration tooling | Backend/Cursor | CRITICAL | Yes, gated |
| `app/alembic/versions/` | â€” | 69 migrations, head `a4f7c29e1b80` (DB-05 slice 5d). RLS B1â€“B7 + deferred-8 landed | Backend/Cursor | CRITICAL | Yes, gated (record-not-fix) |
| `domains/` | DDD domains | 17 domains under domains/ (search, commercial, revenue, analytics, decision, feature_store, ai, scoring, timeline, ...) + app/domains/customer_success | Backend/Cursor | HIGH | Yes, gated |
| `runtime/` | Runtime engines | 27 engine dirs (search, timeline, knowledge_graph, data_fabric, feature_store, decision, workflow, agent, simulation, nba, pipeline_analytics, capability_framework, ...) â€” 10 single-file dirs | Backend/Cursor | HIGH | Yes, gated |
| `runtime/capability_framework/` | â€” | Decorator registry (14 built-ins), `router.py` | Backend/Cursor | HIGH | Yes, gated |
| `sdk/` | â€” | capability_registry.py (~25), events (AuditEvent etc.), telemetry | Backend/Cursor | HIGH | Yes, gated |
| `intelligence/` | AI | providers, data_fabric, activity_intelligence | Backend/Cursor | MEDIUM | Yes |
| `tests/` | â€” | unit/contract/integration/e2e/evaluation/support (220 files via git ls-files method) | Backend/Cursor | HIGH | Yes |
| `tests/support/` | â€” | fixtures (mock keypair!) | Backend/Cursor | MEDIUM | Yes |
| `scripts/` | â€” | arch-compliance.py, check-coverage.py, generate_rls_policies.py, lint.sh, update_env_template.sh, generate_api_docs.sh, sync/validate_capability_registries.py | Backend/Cursor | MEDIUM | Yes |
| `pyproject.toml` | â€” | Poetry manifest (Python 3.12) | Backend/Cursor | CRITICAL | Yes, gated |
| `alembic.ini` | â€” | Alembic config | Backend/Cursor | CRITICAL | Yes, gated |
| `Dockerfile`, `Dockerfile.backend`, `docker-entrypoint.sh` | â€” | Container build/entry | Backend/Cursor | HIGH | Yes, gated |
| `.env` | â€” | **ðŸ”’ SECRETS** | Ops | CRITICAL | NEVER |
| `.env.production.template` | â€” | Template (safe to read) | Backend/Cursor | MEDIUM | Yes |

## 2. Frontend (`salesos/frontend/`)

| Path | Purpose | Purpose (technical) | Owner | Criticality | Safe to modify |
|---|---|---|---|---|---|
| `src/app/` | Product UI | 89 App Router `.tsx` pages + `layout.tsx` + `route.ts` | Claude | HIGH | Yes |
| `src/app/auth/` | Auth UI | login/register/reset | Claude | HIGH | Yes |
| `src/app/dashboard/` | Dashboard UI | main shell | Claude | HIGH | Yes |
| `src/app/v3/` | v3 UI | newer pages | Claude | HIGH | Yes |
| `src/features/` | Feature modules | 13 features (company-intelligence, customer-success, ai-copilot-v3, decision, ...) | Claude | HIGH | Yes |
| `src/lib/` | Core client | `api/client.ts`, auth, hooks, queries | Claude | HIGH | Yes |
| `src/components/` | UI | shared components | Claude | MEDIUM | Yes |
| `src/application/` | App state | state/DI wiring | Claude | MEDIUM | Yes |
| `src/middleware.ts` | â€” | route protection, token refresh | Claude | CRITICAL | Yes, gated |
| `packages/` | Workspace packages | 21 packages (13 with `src`, 8 without) | Shared | MEDIUM | Yes |
| `packages/platform/` | â€” | `@salesos/*` packages | Shared | HIGH | Yes |
| `packages/platform/decision/` | â€” | **STUB** (throws) â€” AI honesty | Shared | LOW | Yes (implement later) |
| `e2e/` | â€” | 31 Playwright specs | Claude | MEDIUM | Yes |
| `tests/visual/` | â€” | Playwright visual tests | Claude | MEDIUM | Yes |
| `apps/` | â€” | 4 EMPTY app shells (no src/) | Shared | LOW | Yes |
| `.storybook/` | â€” | Storybook config | Claude | LOW | Yes |
| `server/server.js` | â€” | Mock server, permissive CORS (ðŸ”’ review before prod) | Shared | LOW | Yes (with approval) |
| `playwright*.config.ts`, `jest.config.js` | â€” | test config | Claude | MEDIUM | Yes |
| `next.config.js`, `tailwind.config.ts`, `tsconfig.json` | â€” | build config | Claude | HIGH | Yes, gated |
| `.env.local` | â€” | **ðŸ”’ SECRETS** | Ops | CRITICAL | NEVER |

## 3. Infra (`salesos/infra/`)

| Path | Purpose | Owner | Criticality | Safe to modify |
|---|---|---|---|---|
| `k8s/` (37 files) | K8s manifests (backend, frontend, kafka, redis, monitoring) | Ops | HIGH | Gated |
| `terraform/` (3 files) | IaC | Ops | HIGH | Gated |
| `monitoring/` (21 files) | Prometheus/Grafana config; `prometheus-token` (ðŸ”’) | Ops | MEDIUM | Gated |
| `staging/` | staging stack manifests | Ops | MEDIUM | Gated |
| `docker/` | compose fragments | Ops | MEDIUM | Gated |
| `caddy/` | reverse-proxy config | Ops | MEDIUM | Gated |

## 4. CI/CD & config (repo root + `salesos/`)

| Path | Purpose | Owner | Criticality | Safe to modify |
|---|---|---|---|---|
| `.github/workflows/` (6) | CI, security-scan, docker-smoke, deploy, deploy-staging, deploy-production | Ops | HIGH | Gated |
| `.github/dependabot.yml` | dep updates | Ops | MEDIUM | Yes |
| `salesos/docker-compose*.yml` (7) | compose stacks | Ops | HIGH | Gated |
| `salesos/.env`, `.env.production`, `.env.staging.local` | **ðŸ”’ SECRETS** | Ops | CRITICAL | NEVER |
| `salesos/Makefile` | task shortcuts | Ops | MEDIUM | Yes |

## 5. Governance & docs (repo root)

| Path | Purpose | Owner | Criticality | Safe to modify |
|---|---|---|---|---|
| `docs/audit/ga-engineering-audit/` | **Canonical GA truth (ðŸ”’)** | Human | CRITICAL | READ-ONLY |
| `docs/adr/` | ADR-030..035 + index (ðŸ”’) | Human | HIGH | READ-ONLY |
| `docs/ADR-Data-001-identity-resolution-v3.md` | identity ADR (ðŸ”’) | Human | HIGH | READ-ONLY |
| `docs/CAPABILITY_CATALOG.md` | capability cards (ðŸ”’) | Human | HIGH | READ-ONLY |
| `docs/vnext/` | roadmaps, WO-*, TECHNICAL_DEBT, DECISIONS (D-001..016) | Human | HIGH | READ-ONLY |
| `docs/program/` | DEC-* swarm decisions | Human | MEDIUM | READ-ONLY |
| `docs/ops/` | runbooks | Human | MEDIUM | READ-ONLY |
| `AGENTS.md` | agent instructions (ðŸ”’) | Human | CRITICAL | READ-ONLY |
| `engineering-os/` | **Governance SUBMODULE (ðŸ”’)** â€” dirty | Human | CRITICAL | READ-ONLY (submodule) |
| `data/scripts/` | identity import pipeline | Data team | LOW | Yes |

## 6. Legacy / adjacent (repo root)

| Path | Purpose | Owner | Criticality | Safe to modify |
|---|---|---|---|---|
| `sales-os/` | LEGACY tree | â€” | LOW | Prefer salesos/ |
| `balady_scraper/`, `taqeem_scraper/`, `najiz_scraper/`, `rega_scraper/` | scrapers (data side) | Data team | LOW | Yes |
| `scripts/backup.sh` | root backup | Ops | LOW | Yes |
| root `*.py` | data pipelines | Data team | LOW | Yes |

## 7. Where agents are FORBIDDEN to write (always)

`salesos/backend/.env`, `.env.production.template` (leave as-is unless approved), `app/modules/identity/_keys/*`, `salesos/frontend/.env.local`, `salesos/.env*`, `salesos/infra/monitoring/prometheus-token`, `docs/**` (governance), `engineering-os/**`, `AGENTS.md`, `.engineering/**` (bootstrap-owned).

## 8. When this file changes

- On directory add/remove/relocation. Must mirror `03`, `05`, `24`.
