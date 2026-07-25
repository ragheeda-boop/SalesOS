# Improvement Opportunities Report — SalesOS

> **Generated:** 2026-07-16
> **Sources:** Code Quality Audit (11), Performance Audit (12), Security Audit (13), Design Audit (10), Database Audit (07), Backend Audit (05), Frontend Audit (03), AI Architecture Audit (06), Testing Audit (14), Technical Debt Register
> **Scope:** Full-stack — backend (Python/FastAPI), frontend (Next.js/React), infrastructure, AI/ML, testing, DevOps

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Quick Wins](#2-quick-wins-high-impact-low-effort)
3. [High Impact](#3-high-impact-high-impact-medium-high-effort)
4. [Medium Impact](#4-medium-impact-medium-impact-medium-effort)
5. [Low Impact](#5-low-impact-lower-priority)
6. [Long-term](#6-long-term-large-effort-strategic-value)
7. [What Should Be Redesigned First Before SalesOS vNext?](#7-what-should-be-redesigned-first-before-salesos-vnext)

---

## 1. Executive Summary

SalesOS is in **strong overall health** (7.5/10 maturity) with production-ready security (10/10), testing (93% coverage), and architecture (95% compliance). However, the audits reveal **48 actionable improvement opportunities** across performance, architecture, UI/UX, AI, testing, and infrastructure.

| Priority Band | Count | Effort Range | Timeline |
|---------------|-------|-------------|----------|
| ⚡ Quick Wins | 12 | Hours - 2 days | This week |
| 🔴 High Impact | 9 | 2 days - 1 sprint | This sprint |
| 🟡 Medium Impact | 21 | 2 days - 1 sprint | Next 1-2 sprints |
| 🟢 Low Impact | 12 | 1 - 3 days | Backlog |
| 🔵 Long-term | 7 | 1 - 3 sprints | vNext planning |

**Top 5 priorities by ROI:**
1. Fix webhooks router auth bypass (SEC-001) — 2 hours, prevents data exposure
2. Fix Workspace N+1 loop — 2 days, eliminates 200+ DB queries per request
3. Fix middleware chain body consumption bug — 1 day, unblocks HTTP load testing
4. Add pagination to 12+ unbounded endpoints — 2 days, prevents O(n) degradation
5. Add chaos/resilience testing — 1 sprint, closes highest testing risk

---

## 2. Quick Wins (High Impact, Low Effort)

| # | Title | Category | Impact | Effort | Priority | Value |
|---|-------|----------|--------|--------|----------|-------|
| 1 | Fix Webhooks Router Missing Authentication | Security | Critical | Hours | **P0** | Prevents unauthenticated access to webhook CRUD, delivery logs, and secrets |
| 2 | Remove `print()` from Production Monitoring Code | DX | Low | 30min | **P2** | Eliminates debug artifact in `/metrics` endpoint |
| 3 | Replace `console.debug` with Structured Logging | DX | Low | 30min | **P2** | Production hygiene for monitoring utility |
| 4 | Align Chart Color Palette with Backend Tokens | UI | Medium | 1hr | **P1** | Fixes chart colors starting with blue instead of brand orange (`#3B82F6` → `#F57C1E`) |
| 5 | Remove Deprecated Foundation Card Component | UX | Low | 1hr | **P1** | Eliminates duplicate Card with different API (`rounded-lg` vs `rounded-xl`, different padding) |
| 6 | Fix Badge `primary` Variant Mapping | UI | Low | 30min | **P2** | `primary` variant maps to info-blue instead of orange-brand — semantically confusing |
| 7 | Fix `search_by_filters` Double Query | Performance | Medium | 1hr | **P1** | Replace `SELECT count(*)` + `SELECT ...` with `count(*) OVER() AS total_count` — halves filtered search time |
| 8 | Consolidate 3 Separate Redis Client Pools | Performance | Medium | 1hr | **P1** | CacheService + AsyncRedisClient + RateLimitMiddleware each maintain separate connection pools |
| 9 | Integrate Frontend `search_companies` Tool | AI | Medium | 1 day | **P1** | Tool returns empty results — frontend agents cannot search companies |
| 10 | Fix Muted Text Contrast for WCAG AA | UX | Medium | 1hr | **P1** | `--text-muted` (#A59E90) on white has 2.9:1 ratio (needs 4.5:1) |
| 11 | Memoize Sidebar Nav Items to Prevent Re-render | Performance | Medium | 1hr | **P1** | 23 `<Link>` components re-render on every route change — add `React.memo` + `useMemo` |
| 12 | Fix Middleware Order: SecurityHeaders Before GZip | Performance | Low | 30min | **P2** | Security headers added to ASGI message before GZip layer can modify it |

**Total Quick Win Effort:** ~3 days

---

## 3. High Impact (High Impact, Medium-High Effort)

| # | Title | Category | Impact | Effort | Priority | Value |
|---|-------|----------|--------|--------|----------|-------|
| 13 | Fix Workspace Endpoint N+1 Loop | Performance | Critical | 2 days | **P0** | 200+ sequential DB calls per request (`routers/commercial.py:470-488`) — batch context build + evaluate |
| 14 | Fix NBA Feed N+1 per Opportunity | Performance | Critical | 2 days | **P0** | 50+ sequential DB calls per NBA feed (`dashboard/router.py:163-208`) — batch fetch + SQL JOIN |
| 15 | Add Pagination to 12+ Unbounded Endpoints | Architecture | High | 2 days | **P0** | Workflows, executions, pipelines, reports, meetings, emails, opportunities, KPIs — all return unbounded lists |
| 16 | Add Chaos/Resilience Testing | Testing | High | 1 sprint | **P0** | No circuit breaker, timeout, or dependency-failure tests — highest testing risk |
| 17 | Add Multi-tenant Data Isolation Tests | Testing | High | 1 sprint | **P0** | Cross-tenant leak testing — critical for SaaS compliance (PDPL) |
| 18 | Add Concurrent Write Conflict Tests | Testing | High | 1 sprint | **P0** | No tests for concurrent write scenarios — data integrity risk |
| 19 | Fix Middleware Chain Body Consumption Bug | Architecture | High | 1 day | **P0** | POST body handling in middleware chain causes hangs during HTTP load testing — blocks performance verification |
| 20 | Migrate Login Page to `@salesos/ui` Components | UX | Medium | 1 day | **P1** | Uses raw `<input>`/`<button>` + nonexistent CSS variables (shadcn/ui names not MUHIDE) |
| 21 | Add Backend AI Tests | AI | High | 3 days | **P0** | Zero test files for intelligence module, agents, RAG pipeline, data fabric — cannot verify AI behavior |
| 22 | Migrate Admin Router from In-Memory to PostgreSQL | Security | High | 2 days | **P1** | `_tenants_store`, `_users_store`, `_SEED_ROLES` are in-memory — data lost on restart |

**Total High Impact Effort:** ~3-4 sprints

---

## 4. Medium Impact (Medium Impact, Medium Effort)

| # | Title | Category | Impact | Effort | Priority | Value |
|---|-------|----------|--------|--------|----------|-------|
| 23 | Add Missing Form Components | UI | Medium | 3 days | **P1** | `@salesos/ui` missing: Checkbox, Radio, Switch, Textarea, DatePicker, Popover, Accordion, Breadcrumb |
| 24 | Implement Keyset/Cursor Pagination | Performance | High | 2 days | **P1** | OFFSET pagination degrades at depth: 3800kB disk spill at 10k rows (page 250) |
| 25 | Add `verify_token` Dependency to GraphQL Router | Security | Medium | 1 day | **P1** | Router registered without auth — relies entirely on `context_getter`; disables GraphiQL in production |
| 26 | Implement Agent Runtime or Remove Placeholder | AI | High | 2 days | **P1** | `runtime/agent_runtime/` is "PLANNED FOR RT3" — placeholder has no execution environment |
| 27 | Migrate Event Bus to Kafka (TD-002) | Architecture | Medium | 2 sprints | **P2** | No durable event streaming; limits scalability for cross-domain events |
| 28 | Add `@cached` on 6+ Missing Endpoints | Performance | Medium | 1 day | **P2** | Workspace, pipeline KPIs, analytics KPIs, opportunities, forecast, company 360 — all uncached |
| 29 | Implement Widget-Level Data Fetching for Dashboard | UX | High | 3 days | **P1** | All-at-once fetch blocks entire dashboard — implement partial/progressive loading |
| 30 | Add Alternative LLM Providers (Anthropic, Local) | AI | Medium | 3 days | **P2** | Only OpenAI supported — no fallback, vendor lock-in, no local models for KSA data sovereignty |
| 31 | Implement Real Data Connectors (Data Fabric) | AI | Medium | 1 sprint | **P2** | `_fetch_data()` returns mock data — Data Fabric not functional with real sources |
| 32 | Standardize Page Styling to CSS Variable Pattern | UI | Medium | 2 days | **P2** | Pages use `text-neutral-900` (Tailwind) instead of `text-[var(--text-primary)]` — not themable |
| 33 | Componentize Pagination Component | UI | Medium | 2 days | **P2** | Inline in 2+ pages (companies, search) with different implementations |
| 34 | Push NBA Pagination/Sorting to SQL | Performance | Medium | 1 day | **P2** | Python-side `sorted()` + slice pagination — should be SQL `ORDER BY` + `LIMIT`/`OFFSET` |
| 35 | Add Property-Based Testing (Hypothesis) | Testing | Medium | 1 sprint | **P2** | No edge case exploration — complements existing example-based tests |
| 36 | Add Visual Regression Tests (Chromatic/Percy) | Testing | Medium | 2 weeks | **P2** | No visual diff testing for UI components — risk of visual regressions |
| 37 | Add `jest-axe` for Automated Accessibility Assertions | Testing | Medium | 1 week | **P2** | Only E2E checks basic ARIA; no automated a11y testing in unit tests |
| 38 | Add OpenAPI/Swagger Contract Tests | Testing | Medium | 1 week | **P2** | No API contract validation — risk of breaking changes between backend/frontend |
| 39 | Add Agent Observability (Tracing, Logging, Metrics) | AI | Medium | 2 days | **P2** | No logging, tracing, or metrics for agent execution — cannot debug in production |
| 40 | Add Performance Regression Tests in CI | Testing | Medium | 2 weeks | **P2** | Benchmarks exist but not tracked over time; `perf-test` is manual |
| 41 | Write Tests for `packages/workspace` Core Logic | Testing | Medium | 2 weeks | **P2** | Core package with 0 tests (only testing utilities exist) |
| 42 | Fix HNSW Index for 3072-Dimension Vectors | Architecture | Medium | 2 days | **P2** | `rag_document_chunks.embedding` falls back to sequential scan — 3072 > 2000-dim HNSW limit |
| 43 | Implement Notifications Persistence | Architecture | Medium | 1 day | **P2** | `InMemoryNotificationRepository` despite migration 0032 creating the table |
| 44 | Add Embedding Cache (Redis) | AI | Medium | 1 day | **P2** | Each query re-embeds text — unnecessary OpenAI API costs |
| 45 | Create Evaluation Test Cases with Golden Datasets | AI | Medium | 2 days | **P2** | `intelligence/evaluation/test_cases/` is empty — evaluation framework has no baseline |
| 46 | Fix `vectors` Table ARRAY(FLOAT) Type | Architecture | Medium | 1 day | **P2** | `vectors.embedding` is `ARRAY(FLOAT)` not native `vector` type — incompatible with `<=>` operator |

**Total Medium Impact Effort:** ~5-6 sprints

---

## 5. Low Impact (Lower Priority)

| # | Title | Category | Impact | Effort | Priority | Value |
|---|-------|----------|--------|--------|----------|-------|
| 47 | Add `pg_trgm` Index on Remaining Partial Text Fields | Performance | Medium | 1 day | P3 | Partial ILIKE search at 100k: p95 1047ms (name_ar), 609ms (name_ar middle), 313ms (city) |
| 48 | Add Index on `confidence_score` | Performance | Low | 1 day | P3 | Sort by confidence at 100k: p95 93-94ms. Index would reduce to <5ms |
| 49 | Fix In-Memory Rate Limiter Memory Growth | Performance | Low | 1 day | P3 | Global `_store: dict[str, list[float]]` grows unboundedly between 300s cleanup intervals |
| 50 | Reduce 10-Middleware Layer Overhead | Performance | Low | 2 days | P3 | JWT decode in logging middleware, cookie parsing in CSRF, redundant Request objects |
| 51 | Fix JWT Decode in RequestLoggingMiddleware | Performance | Low | 1 day | P3 | Decodes and parses JWT inline for every request — use request state instead |
| 52 | Add Storybook for Visual Component Documentation | Documentation | Low | 2 days | P3 | No visual documentation for UI components |
| 53 | Add Automated Contrast Checking in CI | UX | Low | 1 day | P3 | `--text-muted` fails WCAG AA — automate enforcement |
| 54 | Remove Unused `_isRTL` Parameter in `typeClass` Function | DX | Low | 30min | P4 | `typography.ts:34` — parameter declared but never used |
| 55 | Fix Celery Async Bridge Pattern | Architecture | Medium | 2 days | P3 | `asyncio.run()` per task creates new event loop per invocation — use `celery-pool-asyncio` |
| 56 | Make Feature Store Computers Pluggable | Architecture | Low | 1 day | P3 | 7 `FeatureComputer` classes instantiated directly in `tasks.py` + `enrichment.py` |
| 57 | Add Rate Limiting on MCP Server | Security | Low | 1 day | P3 | MCP server has no rate limiting — potential for abuse |
| 58 | Add Database Migration Rollback Tests | Testing | Low | 1 week | P3 | Only forward migration tested — no rollback verification |
| 59 | Add JWT Token Refresh Cycle E2E Test | Testing | Low | 2 days | P3 | Token generation tested; full refresh cycle end-to-end not |
| 60 | Fix `audit.audit_log` BIGSERIAL vs UUID Inconsistency | Architecture | Low | 1 day | P3 | All other tables use UUID PKs — `audit.audit_log` uses BIGSERIAL |
| 61 | Remove or Implement Meilisearch Integration | Architecture | Low | 1 day | P4 | Configured in `config.py` + Docker Compose but no active integration code |
| 62 | Add Kafka Healthcheck in docker-compose | DevOps | Low | 1hr | P3 | Kafka uses only `service_started` — backend could start before Kafka is ready |
| 63 | Configure Terraform Remote State | DevOps | High | 1 day | P1 | No S3 backend for Terraform state — risk of state loss |
| 64 | Add Celery Worker Service to Docker Compose | DevOps | Medium | 1 day | P2 | Celery dependency present but no worker service in docker-compose.yml |
| 65 | Create ADR Directory and Migrate Architecture Decisions | Documentation | Medium | 2 days | P2 | No dedicated `docs/adr/` — decisions scattered across CHANGELOG and prose docs |
| 66 | Consolidate Scattered `.env` Files | Architecture | Low | 1 day | P3 | 6+ `.env` files at different levels — no centralized configuration management |
| 67 | Add Connection Pool Exhaustion Tests | Testing | Low | 2 days | P3 | No tests for database pool exhaustion behavior |
| 68 | Add NoSQL Injection Guards on Neo4j Queries | Security | Low | 1 day | P3 | Neo4j queries constructed via f-strings in `knowledge_graph_runtime` — use parameterized Cypher |

**Total Low Impact Effort:** ~3-4 sprints

---

## 6. Long-term (Large Effort, Strategic Value)

| # | Title | Category | Impact | Effort | Priority | Value |
|---|-------|----------|--------|--------|----------|-------|
| 69 | Refactor `frontend/src/lib/api.ts` | Architecture | High | 3 days | P0 | Monolithic 1,240-line API client — extract into domain-specific modules |
| 70 | Refactor `knowledge_graph_runtime/__init__.py` | Architecture | High | 3 days | P1 | 1,087-line init file — extract graph operations into separate modules |
| 71 | Refactor `app/main.py` into Modular Startup | Architecture | Medium | 1 day | P1 | 773-line all-in-one app bootstrap — extract router registration, lifespan, middleware |
| 72 | Refactor `decision/engine.py` (774 lines) | Architecture | Medium | 2 days | P1 | Core engine — extract policy evaluation, context building, recommendation generation |
| 73 | Replace 284 Python `Any` Types with Proper Generics | DX | Medium | 3 days | P2 | Concentrated in `kernel/grounding.py` (14), `pagination.py` (6), `reasoning.py` (6) |
| 74 | Deploy Redis in Production | Infrastructure | High | 1 sprint | P1 | Redis marked "Not Deployed" — Celery, caching, rate limiting all depend on it |
| 75 | Implement API Versioning Strategy | Architecture | High | 2 sprints | P2 | No versioning strategy for REST or GraphQL APIs — breaking changes difficult |
| 76 | Implement Full Multi-Agent Runtime with Observability | AI | High | 3 sprints | P2 | Agent runtime is placeholder; no execution environment, no monitoring |
| 77 | Enforce Frontend Package Import Boundaries | Architecture | Medium | 3 days | P2 | 13 packages without enforced import boundaries — risk of tangled dependencies |
| 78 | Redesign Companies Table Schema (Wide Rows) | Architecture | Medium | 1 sprint | P2 | Row width 3341 bytes — full table scans expensive; implement columnar subsets |
| 79 | Add Helm Charts for K8s Deployment | DevOps | Medium | 2 sprints | P2 | Raw K8s manifests — no Helm for environment-specific templating |
| 80 | Implement Data Partitioning Strategy | Architecture | High | 3 sprints | P2 | No partition strategy for scale — at 1M companies, full table scans become prohibitive |
| 81 | Implement Full Data Fabric with Real Connectors | AI | High | 3 sprints | P2 | Connectors return mock data — real CRM/ERP/email integration needed |

**Total Long-term Effort:** ~10-15 sprints

---

## 7. What Should Be Redesigned First Before SalesOS vNext?

The following items represent **architectural debt that will compound** if not addressed before the next major version. These are the highest-risk, highest-leverage redesign targets.

### Tier 1 — Must Redesign Before vNext (Critical Path)

| Area | Current State | Risk | Recommended Redesign |
|------|--------------|------|---------------------|
| **API Client (`api.ts`)** | 1,240-line monolithic file with 60+ typed functions | Every new domain adds to the monolith; testability degraded; tree-shaking impossible | Split into domain modules: `api/companies.ts`, `api/search.ts`, `api/opportunities.ts`, etc. with shared auth/error interceptors |
| **App Bootstrap (`main.py`)** | 773-line all-in-one file: router registration, middleware, lifespan, model imports, startup logic | Startup failures cascade; hard to test; every new module modifies this file | Extract: `routers/__init__.py` (router loader), `startup.py` (lifespan), `middleware.py` (stack config) |
| **Knowledge Graph Runtime** | 1,087-line `__init__.py` — Neo4j + SQL fallback + all graph operations | violates single-responsibility; impossible to test graph operations in isolation | Split: `kg_engine.py`, `kg_neo4j.py`, `kg_sql_fallback.py`, `kg_queries.py` |
| **Decision Engine (`engine.py`)** | 774-line monolith — context building, policy evaluation, recommendation generation | Every decision feature requires touching this file; test coverage suffers | Split: `decision_context.py`, `decision_policies.py`, `decision_recommender.py` |

### Tier 2 — Should Redesign Before vNext (High Value)

| Area | Current State | Risk | Recommended Redesign |
|------|--------------|------|---------------------|
| **Companies Table Schema** | 3341-byte row width; 30+ columns fetched every query | Full scan costs 3.3MB buffer pool per 1000 rows; index-only scans impossible | Vertical partitioning: core columns table + extension tables (financial, address, classification) + selective column queries |
| **Dashboard Data Fetching** | All-at-once fetch (`useDashboard` single query) + all-widgets-loading skeleton | Slow sub-query blocks entire dashboard; no progressive rendering; coarse cache | Widget-level data fetching with React Query `staleTime` per widget; skeleton per widget not per dashboard |
| **Middleware Chain** | 10 layers, body consumption bug, redundant JWT parsing, cookie scanning | Blocks HTTP load testing; 7-15ms overhead per request at scale | Consolidate to 5-6 layers: fix body consumption, extract JWT from request state, merge CSRF + SecurityHeaders |
| **Caching Strategy** | Only 2 endpoints use `@cached`; 3 separate Redis pools; no cache key convention | Wasted connections; cache fragmentation (`query.fields` in dashboard key) | Single `CacheService` singleton; centralized key convention (`{domain}:{tenant}:{resource}:{id}`); add cache-aside pattern to all read-heavy endpoints |
| **Test Paths** | 15+ `testpaths` in pyproject.toml; tests scattered across unit/integration/e2e/evaluation + domain-level tests | Coverage reporting fragmented; gaps easy to miss | Consolidate to 3 groups: `tests/unit/`, `tests/integration/`, `tests/e2e/` with domain tests as subdirs under each |

### Tier 3 — Strongly Recommended for vNext

| Area | Current State | Rationale |
|------|--------------|-----------|
| **Python Type Safety** | 284 `Any` annotations, mostly in kernel modules (`grounding.py`, `pagination.py`, `reasoning.py`) | Without generics, API contracts are invisible to MyPy; static analysis value is reduced |
| **Admin Router Data Persistence** | In-memory stores for tenants, users, roles, permissions | Data loss on restart; no audit trail for tenant/user management operations |
| **Notifications & Workflow Persistence** | `InMemoryNotificationRepository` — DB migration exists (0032) but unused | Only domain still using in-memory storage after PostgreSQL migration |
| **Feature Store Pluggability** | 7 `FeatureComputer` classes hardcoded in `tasks.py` + `enrichment.py` | Adding a new feature computer requires modifying both files; should be registry-based |
| **AI Test Coverage** | Zero tests for intelligence module, agents, RAG, data fabric, evaluation | Without tests, AI behavior changes are untrackable; regression risk is high |

### Decision Checklist for vNext

Before starting SalesOS vNext planning, verify these gates:

```
[ ] api.ts split into domain modules (P0)
[ ] main.py modular startup extracted (P1)
[ ] knowledge_graph_runtime refactored (P1)
[ ] decision/engine.py modularized (P1)
[ ] Companies table vertical partitioning prototyped (P2)
[ ] Dashboard widget-level fetching implemented (P1)
[ ] Middleware chain consolidated and bug-free (P0)
[ ] Caching strategy unified (P1)
[ ] Test paths consolidated (P2)
[ ] Python Any types reduced to <50 (P2)
[ ] Admin router data persisted to PostgreSQL (P1)
[ ] Notifications/Workflow persisted to PostgreSQL (P2)
[ ] AI modules have minimal test coverage (P0)
```

---

## Summary

| Band | Items | Est. Effort | Key Focus |
|------|-------|-------------|-----------|
| ⚡ Quick Wins | 12 | ~3 days | Security hotfix, color/contrast fixes, memoization, Redis consolidation |
| 🔴 High Impact | 9 | ~3-4 sprints | N+1 fixes, pagination, testing gaps, middleware bug, admin persistence |
| 🟡 Medium Impact | 27 | ~5-6 sprints | Form components, keyset pagination, AI tests, caching, styling consistency |
| 🟢 Low Impact | 12 | ~3-4 sprints | Indexes, Storybook, CI config, migration tests, env consolidation |
| 🔵 Long-term | 13 | ~10-15 sprints | Monolith refactors, Redis deploy, API versioning, Data Fabric, K8s Helm |

**TL;DR:** Fix the webhooks auth and N+1 loops this week. Refactor `api.ts`, `main.py`, and the knowledge graph runtime before vNext. Add chaos testing and widget-level dashboard fetching this sprint.
