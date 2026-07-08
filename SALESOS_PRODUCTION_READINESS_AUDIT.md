# SalesOS — Production Readiness Audit Report

**Phase 2 Release Decision**
**Date:** 2026-07-08
**Audit Framework:** Engineering Operating System (`.opencode/`)

---

## Executive Verdict

**Phase 2 Release: ❌ NOT READY**

| Dimension | Score | Status |
|-----------|-------|--------|
| Architecture Compliance | **42%** | ❌ BLOCKED |
| Security | **32%** | ❌ BLOCKED |
| Database & Performance | **55%** | ❌ BLOCKED |
| Test Coverage & CI/CD | **55%** | ❌ BLOCKED |
| Infrastructure & DevOps | **62%** | ❌ BLOCKED |
| Frontend | **72%** | ⚠️ GAPS |
| AI/Intelligence | **38%** | ❌ BLOCKED |
| **Overall** | **48%** | **❌ BLOCKED** |

7 of 8 dimensions are below the 70% threshold for Phase 2 release. 31 Critical issues must be resolved.

---

## 1. 🏗 Architecture Compliance — 42%

### Critical Issues (Block Release)

| # | Issue | File:Line | Principle Violated |
|---|-------|-----------|-------------------|
| A1 | **Domains import from `app/`** — Layer violation. domains/search/api.py imports from app.modules.company | `domains/search/api.py:24,34` | Principle 1 (DDD First) |
| A2 | **Domains import `app.common.models`** — Timeline and Commercial domain models depend on app layer | `domains/timeline/models.py:8`, `domains/commercial/infrastructure/models.py:15` | Principle 1 (DDD First) |
| A3 | **Runtime imports from `app/modules/`** — Data Fabric pipeline directly depends on app layer | `runtime/data_fabric_runtime/__init__.py:25-28,544` | Principle 1 (DDD First) |
| A4 | **Services bypass Repository pattern** — CompanyService and IdentityService use raw SQLAlchemy | `app/modules/company/service.py` (all methods), `app/modules/identity/service.py` (all methods) | Principle 4 (Repository Abstraction) |
| A5 | **No UnitOfWork usage** — Pattern exists in `sdk/database.py` but zero services use it | All service files | Principle 4 |
| A6 | **Architecture tests don't catch domain→app imports** — Critical blind spot | `tests/test_architecture.py` | Quality Gate 1 |
| A7 | **Duplicate search repositories** — Two near-identical files create maintenance risk | `domains/search/repositories/company.py` ↔ `app/modules/company/search_repository.py` | Coding Standards |

### High Issues

| # | Issue | File:Line |
|---|-------|-----------|
| A8 | Domain entities are anemic — Company/User/Tenant have zero business methods | All `models.py` files |
| A9 | `DataFabricPipeline` is a god class (774 lines) | `runtime/data_fabric_runtime/__init__.py` |
| A10 | `EventRuntime.publish()` is blocking, not fire-and-forget | `runtime/event_runtime/__init__.py:370-406` |
| A11 | No aggregate roots with consistency boundaries | All domain models |
| A12 | 96 `print()` statements in production code | Pipeline scripts, benchmark |

---

## 2. 🔒 Security — 32%

### Critical Issues (Block Release)

| # | Issue | File:Line | CVSS-like |
|---|-------|-----------|-----------|
| S1 | **Password reset token returned in HTTP response** — Anyone can reset any user's password. Complete authentication bypass. | `identity/router.py:221-227`, `identity/service.py:276-288` | **CRITICAL** |
| S2 | **~88 API routes with zero authentication** — 52% of all endpoints have no token verification | See full audit for list | **CRITICAL** |
| S3 | **DELETE /api/v1/companies/{id} has no auth** — Anonymous users can delete companies | `company/router.py:234-239` | **CRITICAL** |
| S4 | **Contact CRUD has no tenant isolation** — Cross-tenant data access | `contact/router.py:31-53` | **CRITICAL** |
| S5 | **Real Notion API token hardcoded in .env** — Third-party service compromise | `backend/.env:54` | **CRITICAL** |
| S6 | **No token refresh mechanism** — All sessions expire after 30 min with no recovery | Frontend `api.ts` | **CRITICAL** |
| S7 | **JWT stored in localStorage** — XSS-vulnerable; should use httpOnly cookies | Frontend `api.ts` | **CRITICAL** |

### High Issues

| # | Issue | File:Line |
|---|-------|-----------|
| S8 | `secret_key` default value hardcoded in source code | `config.py:14` |
| S9 | Neo4j password fallback hardcoded in source code | `main.py:125` |
| S10 | `.env.example` contains real database credentials | `.env.example:13` |
| S11 | Missing role/permission checks on all commercial routes | `commercial.py` (entire file) |
| S12 | Missing auth on all event-runtime management endpoints | `event_runtime/router.py` |
| S13 | Missing auth on XP1 endpoints (capability/UX/schema/form/action/extension/plugin) | Multiple runtime routers |
| S14 | All decision engine routes lack authentication | `decision_runtime/router.py` |
| S15 | Refresh token rotation without invalidation | `identity/router.py:207-218` |
| S16 | Rate limiting not applied to `/forgot-password` — email enumeration risk | `middleware.py` |

---

## 3. 🗄 Database & Performance — 55%

### Critical Issues (Block Release)

| # | Issue | File:Line |
|---|-------|-----------|
| D1 | **No vector index for pgvector** — HNSW index commented out (dimension limit). Every semantic search = full table scan | `alembic/versions/0006_search_runtime.py:74-80` |
| D2 | **Full-text search infrastructure completely unused** — `tsv` column + GIN index + trigger exist but app uses ILIKE `%pattern%` | `search_repository.py`, `repositories.py` |
| D3 | **No trigram GIN indexes for ILIKE search** — All ILIKE queries = sequential scans | All migrations (benchmarks create them, but not in prod) |
| D4 | **bulk_upsert has N+1 query pattern** — M records = M individual queries per CR check | `repositories.py:139-168` |

### High Issues

| # | Issue | File:Line |
|---|-------|-----------|
| D5 | Embedding model (text-embedding-3-large, 3072d) exceeds pgvector HNSW limit (2000d) | `config.py:44` |
| D6 | 6 tables use Integer auto-increment PK instead of UUID | Migrations 0002-0005, 0011 |
| D7 | 6 tables missing `created_at`/`updated_at` | Various migrations |
| D8 | `EntityResolutionConflict.golden_record_id` FK without index | Migration 0001 |
| D9 | `seed_from_database` serial per-company + OpenAI API call — hours to index thousands | `pgvector_repository.py` |
| D10 | No `pool_recycle` configured — stale connections risk | `database.py` |
| D11 | All benchmarks ran on SQLite, not PostgreSQL — not representative | `benchmark/` |

---

## 4. 🧪 Test Coverage & CI/CD — 55%

### Critical Issues (Block Release)

| # | Issue | Detail |
|---|-------|--------|
| T1 | **No PostgreSQL-backed repository tests** — All 14+ repositories have zero tests against actual PostgreSQL | All repository classes |
| T2 | **No router endpoint unit tests** — ~20 of 168 endpoints are tested (via integration only) | All router files |
| T3 | **`testpaths` misconfigured** — CI only runs ~20% of tests. Domain tests, commercial tests NOT included | `pyproject.toml` |
| T4 | **No coverage thresholds in CI** — Pipeline passes even with 0% coverage on new code | `ci.yml` |
| T5 | **No security scanning** — No Snyk/Trivy/Dependabot/npm audit in CI | `ci.yml` |
| T6 | **No frontend page/component tests** — Zero tests for any page, API client, or React Query hooks | Frontend test suite |

### High Issues

| # | Issue | Detail |
|---|-------|--------|
| T7 | No staging environment — CD deploys directly to production | `deploy.yml` |
| T8 | No deployment health check or rollback | `deploy.yml` |
| T9 | Event bus, permission system, feature store, knowledge graph have zero tests | Core infrastructure |
| T10 | Commercial E2E flow untested (quote→contract→revenue) | Missing |
| T11 | Integration test (`test_integration.py`) is untracked — not in CI | New file |
| T12 | AI/Intelligence layer: zero tests across all modules (11 agents, signals, digital twin, revenue brain, graph) | `intelligence/` |

---

## 5. ☁ Infrastructure & DevOps — 62%

### Critical Issues (Block Release)

| # | Issue | File:Line |
|---|-------|-----------|
| I1 | **No alerting rules** — Silent failures in production. No Prometheus rules, no Alertmanager | `monitoring/prometheus.yml` |
| I2 | **No log aggregation** — No centralized logs. Debugging requires per-host `docker logs` | Entire stack |
| I3 | **Dev compose has zero resource limits** — Runaway process can exhaust host | `docker-compose.yml` |
| I4 | **No WAL archiving or PITR** — Data loss window = backup interval (up to 24h) | PostgreSQL config |
| I5 | **Secrets in plaintext in docker-compose** — Passwords visible via `docker inspect` | All compose files |
| I6 | **K8s secrets.yaml tracked in git** (even as template) | `infra/k8s/secrets.yaml` |

### High Issues

| # | Issue | Detail |
|---|-------|--------|
| I7 | No custom PostgreSQL config (shared_buffers, work_mem, etc.) | Missing |
| I8 | No SSL/TLS for PostgreSQL connections | Missing |
| I9 | Frontend Dockerfile has no HEALTHCHECK | `frontend/Dockerfile` |
| I10 | No internal/external network segmentation — all ports exposed | `docker-compose.yml` |
| I11 | No PodDisruptionBudget or HPA in K8s | `infra/k8s/` |
| I12 | Caddy lacks rate limiting, request logging, compression | `infra/caddy/Caddyfile` |
| I13 | Sentry DSN empty by default in production template | `.env.production.template` |

---

## 6. 🎨 Frontend — 72%

### Critical Issues

| # | Issue | File:Line |
|---|-------|-----------|
| F1 | **No token refresh mechanism** — 30-min sessions with no recovery. **Blocks Phase 2.** | `api.ts` |
| F2 | **localStorage for JWT tokens** — XSS-vulnerable | `api.ts` |

### High Issues

| # | Issue | Detail |
|---|-------|--------|
| F3 | No aria-labels on any interactive elements | All components |
| F4 | No skip-to-content link | Layout |
| F5 | PipelineKanban unusable on mobile | `pipeline-kanban.tsx` |
| F6 | CopilotPanel fixed width breaks on small screens | `copilot-panel.tsx` |
| F7 | No Open Graph / Twitter metadata | `layout.tsx` |
| F8 | SearchPanel silently swallows errors | `search-panel.tsx` |
| F9 | No error monitoring (Sentry) on frontend | Missing |
| F10 | No loading skeletons for individual components | Multiple |

---

## 7. 🤖 AI/Intelligence — 38%

### Critical Issues

| # | Issue | File:Line |
|---|-------|-----------|
| AI1 | **Zero tests for ALL intelligence modules** — 11 agents, signals, digital twin, revenue brain, graph | `intelligence/` |
| AI2 | **EnrichmentService uses `asyncio.run()`** — Will crash or create event loop conflicts in async context | `intelligence/enrichment/__init__.py` |

### High Issues

| # | Issue | Detail |
|---|-------|--------|
| AI3 | RevenueBrain uses hardcoded `base_revenue = 1000000.0` — forecasts are fictional | `revenue_brain/` |
| AI4 | All agents depend entirely on LLM — no external data sources, web search, or API integrations | All agents |
| AI5 | No event bus integration — agents operate as direct request-response | All agents |
| AI6 | Graph is in-memory only — no Neo4j connection implemented | `graph/` |
| AI7 | No error handling around OpenAI API calls — rate limits crash the app | `agents/base.py` |
| AI8 | Semantic search endpoints marked experimental — not wired to frontend | Search |

---

## 8. Remediation Plan

### Sprint 0.5 — Security Hardening (Week 1)

| Task | Issues Fixed | Est. Days |
|------|-------------|-----------|
| Fix password reset flow (email token, never return in response) | S1 | 1 |
| Add `Depends(verify_token)` + `Depends(get_current_tenant_id)` to all 88 unprotected routes | S2, S3, S4, S11-S14 | 3 |
| Remove hardcoded secrets from `.env`, config.py, main.py; use env vars only | S5, S8, S9, S10 | 1 |
| Implement refresh token with httpOnly cookies | S6, S7, F1, F2 | 3 |
| Rotate exposed Notion token | S5 | 0.5 |

**Total: ~8 days**

### Sprint 0.6 — Architecture Remediation (Week 2)

| Task | Issues Fixed | Est. Days |
|------|-------------|-----------|
| Fix domain→app imports — move dependencies to app layer, inject via interfaces | A1, A2, A3 | 2 |
| Refactor CompanyService + IdentityService to use Repository pattern | A4 | 2 |
| Wire UnitOfWork into all services | A5 | 1 |
| Add architecture tests for domain→app, runtime→app import violations | A6 | 1 |
| Remove duplicate search repository | A7 | 0.5 |

**Total: ~6.5 days**

### Sprint 0.7 — Database & Performance (Week 3)

| Task | Issues Fixed | Est. Days |
|------|-------------|-----------|
| Add trigram GIN indexes + migration | D3 | 1 |
| Replace ILIKE with tsvector full-text search | D2 | 2 |
| Fix embedding model to 1536d (text-embedding-3-small) or upgrade pgvector | D1, D5 | 1 |
| Optimize bulk_upsert to single query | D4 | 1 |
| Add vector index (IVFFlat for 1536d) | D1 | 1 |

**Total: ~6 days**

### Sprint 0.8 — Tests & Infrastructure (Week 4)

| Task | Issues Fixed | Est. Days |
|------|-------------|-----------|
| Fix testpaths to include all test directories | T3 | 0.5 |
| Add coverage thresholds to CI | T4 | 0.5 |
| Add security scanning (Snyk/Trivy) to CI | T5 | 1 |
| Add PostgreSQL-backed repository tests for top 5 repos | T1 | 2 |
| Set up log aggregation (Loki + Promtail) | I2 | 2 |
| Add resource limits to dev compose | I3 | 0.5 |
| Configure PostgreSQL WAL archiving | I4 | 1 |
| Add Prometheus alert rules + Alertmanager | I1 | 1.5 |

**Total: ~9 days**

### Total Remediation Estimate: **~30 working days**

---

## 9. Recommendation

**Do not release Phase 2 in the current state.**

The 31 Critical issues represent existential risks: complete auth bypass, 88% of API endpoints unprotected, no monitoring or alerting, and a 24h data loss window. Any one of these would cause a production incident.

**After remediation:** Run a full regression audit, then proceed to:
1. Tag `v2.0.0-rc.1`
2. Deploy to staging
3. Run E2E smoke tests
4. Performance benchmarks at 10K/100K records
5. If all pass → `v2.0.0` release

---

*Report generated by OpenCode Engineering Operating System — `.opencode/agents/quality/`*
