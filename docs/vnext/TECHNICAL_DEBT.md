# SalesOS vNext — Technical Debt Register

> **Audit Basis**: Code Quality, Performance, Security, Architecture, AI, Design, Testing audits
> **Status**: Active
> **Last Updated**: 2026-07-16

---

## P0 — Critical (Must fix before next sprint)

| ID | Description | Impact | Affected Files | Recommendation | Effort |
|----|-------------|--------|---------------|----------------|--------|
| SEC-001 | Webhooks router has no authentication | Unauthenticated webhook endpoint — attacker can trigger arbitrary webhook calls. Critical security gap despite 10/10 posture score. | `app/routers/webhooks.py` | Add `Depends(verify_token)` to all webhook routes | 1 day |
| SEC-003 | GraphQL lacks FastAPI-level `Depends(verify_token)` | GraphQL endpoint can be queried without authentication — data exposure risk | GraphQL router(s) | Add global `Depends(verify_token)` dependency to GraphQL router | 1 day |
| SEC-004 | JWKS endpoint uses empty symmetric key | JWKS endpoint returns an empty symmetric key — token validation is effectively disabled | `app/routers/auth.py` (JWKS endpoint) | Remove empty key; ensure JWKS returns valid asymmetric public keys only | 1 day |
| PERF-01 | Middleware body consumption bug | Request body is consumed by middleware chain before reaching route handler. POST requests arrive with empty body. Blocks all HTTP load testing. | `app/middleware/` chain (10 layers) | Add BodyCache middleware that buffers request body once; all downstream consumers read cached copy | 3 days |
| PERF-02 | N+1 workspace loop | Workspace listing performs N+1 queries — one query per workspace for related data | `app/routers/commercial.py:470-488` | Eager-load related data or use batch query pattern | 3 days |
| PERF-03 | N+1 NBA feed | NBA (Next Best Action) recommendation feed performs N+1 queries per user | `dashboard/router.py:163-208` | Batch-load NBA recommendations with single query | 3 days |
| PERF-04 | 12+ endpoints without pagination | List endpoints return unbounded result sets — will cause memory exhaustion and timeouts as tenant data grows | Multiple router files | Add keyset (cursor) pagination to all list endpoints | 2 weeks |
| AI-01 | Zero backend AI tests | No tests for `intelligence/` module — agents, RAG, reasoning, guardrails, grounding all untested. Governance violation (Engineering Constitution Art 2.2). | `intelligence/` (agents/, reasoning.py, guardrails.py, rag/, grounding.py) | Write contract + unit tests; target 85% coverage | 2 weeks |
| AI-02 | Agent runtime is placeholder string | 15 registered agents cannot execute — runtime is marked "PLANNED FOR RT3". Blocks entire AI-native vision. | `runtime/agent_runtime/` | Implement full Agent Runtime with lifecycle, retry, observability | 3-4 weeks |
| AI-03 | Evaluation `test_cases/` directory empty | No golden test cases for AI evaluation. Cannot measure regression, compare providers, or gate releases on AI quality. | `intelligence/evaluation/test_cases/` | Create 50+ golden test cases across all agents and RAG | 2 weeks |

## P1 — High (Must fix within vNext)

| ID | Description | Impact | Affected Files | Recommendation | Effort |
|----|-------------|--------|---------------|----------------|--------|
| SEC-002 | Admin router uses in-memory stores | Admin state lost on restart. Cannot scale to multiple instances. | `app/routers/admin.py` | Replace in-memory stores with PostgreSQL-backed repositories | 3 days |
| SEC-005 | Grafana password default in `.env.example` | Default credentials shipped in version control — easy to miss in production deployment | `.env.example` | Remove default credentials; add placeholder with required-field validation | 1 day |
| PERF-05 | OFFSET deep pagination — 3800kB disk spill at 10k rows | Offset pagination degrades to full table scan + sort + disk spill for deep pages. Unusable beyond 10k rows. | Multiple query files | Replace OFFSET with keyset (cursor) pagination in all queries | 1 week |
| PERF-06 | 3 separate Redis client pools | Cache, session, and rate limiting each have their own pool. Resource waste, connection overhead, no unified management. | `app/infrastructure/redis/` (3 files) | Consolidate into single Redis connection manager with namespace prefix | 2 days |
| PERF-07 | Keyset pagination uses `sorted()`+`slice()` instead of SQL `ORDER BY` | Keyset pagination implemented in Python — sorts entire result set in memory instead of pushing to database | Pagination utility file | Rewrite keyset pagination to use SQL `WHERE` + `ORDER BY` + `LIMIT` | 2 days |
| PERF-08 | `search_by_filters` double-query pattern | Search executes same query twice — once for count, once for results. Doubles database load. | Search query file | Use SQL `COUNT(*) OVER()` window function for single-query count + results | 2 days |
| PERF-09 | Only 2 endpoints use `@cached` | Almost no endpoint caching — repeated identical queries hit database every time | Multiple router files | Add `@cached` decorator to all read-heavy, low-volatility endpoints | 3 days |
| ARC-01 | 1,240-line `api.ts` monolithic router | Single file handles all domains. Violates DDD bounded context isolation. Every change risks breaking unrelated domains. | `src/api.ts` | Split into domain-specific API clients (identity, company, search, etc.) | 1 week |
| ARC-02 | 773-line `main.py` monolithic bootstrap | Startup logic, middleware, router registration all in one file. Every new domain adds to this file. | `app/main.py` | Extract into `bootstrap/` module with separate app factory, settings, middleware, routers | 1 week |
| ARC-03 | 1,087-line `knowledge_graph_runtime/__init__.py` | God object file — violates Single Responsibility Principle. Near-impossible to test or modify safely. | `knowledge_graph_runtime/__init__.py` | Decompose into service, repository, and router modules | 1 week |
| ARC-04 | 774-line `decision/engine.py` | Overly large engine file — couples decision logic, provider routing, result formatting in one module | `decision/engine.py` | Split into strategy classes, separate provider routing, extract formatters | 3 days |
| ARC-05 | 861-line `commercial/postgres_repositories.py` | Bloated repository file — makes testing and maintenance difficult | `commercial/postgres_repositories.py` | Split into per-entity repository classes | 2 days |
| ARC-06 | 6+ `.env` files, no centralized config | Configuration scattered across multiple `.env` files. No single source of truth. Hard to audit. | Multiple `.env.*` files | Consolidate into single config system with pydantic-settings + YAML overlays | 1 week |
| ARC-07 | 15+ fragmented testpaths | Test discovery configuration scattered across multiple `pytest.ini`/`pyproject.toml` files. Confusing for developers. | Multiple test config files | Consolidate test configuration into single `tests/pytest.ini` | 2 days |
| ARC-08 | InMemoryNotificationRepository despite DB migration | Notifications use in-memory store even though database migration exists. Data loss on restart. | Notification repository file | Switch to PostgreSQL-backed notification repository | 2 days |
| ARC-09 | Tenant module directory empty | Multi-tenancy domain declared but not implemented. No tenant provisioning, isolation, or quota management. | `domains/tenant/` | Implement tenant domain with provisioning, isolation, quotas | 3-4 weeks |
| ARC-10 | 5 runtime engines are stubs | Agent, Execution, Scheduler, Simulation, Workflow engines exist as stubs only. Cannot execute. | `runtime/` stub files | Implement each runtime with production logic (see SPRINT_PLAN) | 2-3 weeks per engine |
| ARC-11 | No ADR directory | Architecture decisions not documented. Violates Engineering Constitution Art 3.1. | Missing `docs/adr/` | Create ADR directory; migrate architecture decisions to ADR format | 2 days |
| AI-04 | Only OpenAI supported for AI features | Vendor lock-in — no fallback for OpenAI outages. Cannot meet KSA PDPL data sovereignty requirements. | `intelligence/providers/` | Add Anthropic provider, create fallback chain, implement query routing | 2-3 weeks |
| AI-05 | No embedding cache | Every RAG query re-embeds text — redundant API calls, increased latency, higher costs. | `intelligence/rag/embeddings.py` | Implement LRU embedding cache keyed by (text_hash, model) | 3 days |
| AI-06 | `search_companies` frontend tool returns empty | Frontend agent tool broken — companies search returns no results. Copilot cannot answer company questions. | Frontend agent tool file | Fix tool implementation to properly call search API and return results | 2 days |
| AI-07 | No agent observability | Impossible to debug agent behavior. No tracing, no execution logs, no performance metrics. | `runtime/agent_runtime/` (missing) | Add tracing spans, execution logs, and Grafana dashboard for agents | 1 week |
| DSG-01 | Login page uses shadcn/ui tokens instead of MUHIDE tokens | Brand inconsistency — login page looks different from rest of application. First impression problem. | Login page CSS/components | Replace `--background`, `--card` (shadcn/css) with MUHIDE `--bg-primary`, `--surface-card` | 2 days |
| DSG-02 | Chart colors mismatch — hardcoded blue `#3B82F6` instead of brand orange `#F57C1E` | Charts don't match brand identity. Backend chart colors also misaligned. | `@salesos/charts` | Implement 12-color chart palette starting with orange; export as `--chart-*` CSS tokens | 2 days |
| DSG-03 | Muted text `#A59E90` on white — 2.9:1 contrast ratio, fails WCAG AA (needs 4.5:1) | Accessibility violation — legal risk under accessibility regulations. Users with visual impairments cannot read muted text. | Global `--text-muted` token | Update `--text-muted` to minimum `#8C8374` (4.56:1); verify all downstream uses | 1 day |
| DSG-04 | Missing Checkbox, Radio, Switch, Textarea, DatePicker components | Cannot build standard forms. Login page, settings, and all data-entry surfaces use raw HTML elements. | `@salesos/ui` | Implement 5 missing form components with full ARIA, RTL, error states | 5 days |
| DSG-05 | Pages use Tailwind utility classes directly instead of CSS variables | Color changes require updating every page. No semantic abstraction. Inconsistent theme application. | Multiple page files | Add ESLint rule forbidding Tailwind color classes; codemod migration to CSS vars | 1 week |
| DSG-06 | Duplicate Card component in `@salesos/ui` | Two Card components — confusion about which to use. Potential styling conflicts. | `@salesos/ui` | Remove deprecated Card, update imports across codebase | 0.5 day |
| TST-01 | Workspace core package has 0 tests | Core workspace functionality completely untested. No regression safety. | Workspace core package | Write unit tests for all workspace service and repository classes | 1 week |
| TST-07 | No API contract tests | No provider or consumer contract tests. API changes can break frontend without detection. | Missing `tests/contract/` | Add provider contract tests for every backend endpoint; add consumer contract tests for every frontend API client | 2 weeks |

## P2 — Medium (Plan for next sprint)

| ID | Description | Impact | Affected Files | Recommendation | Effort |
|----|-------------|--------|---------------|----------------|--------|
| ARC-12 | Companies table 3341-byte row width | Wide table — exceeds PostgreSQL efficient page usage. Slows full scans, increases I/O. | Migration file for companies table | Normalize wide columns into related tables; consider vertical partitioning | 3 days |
| ARC-13 | Vectors table uses `ARRAY(FLOAT)` instead of native `VECTOR(n)` type | Cannot create IVFFlat or HNSW indexes. Similarity search is slow and unsupported. | Migration file for vectors table | Migrate to native `VECTOR(n)` type; create HNSW index | 1 week |
| ARC-14 | No API versioning strategy | No `/api/v2/` vs `/api/v3/` convention. Breaking changes silently break consumers. | All routers | Establish versioning convention (`/api/v2/` URL prefix); document breaking change policy | 3 days |
| ARC-15 | No partition strategy for scale | Single table for all tenants — no partitioning by tenant_id or date range. Query performance degrades with data growth. | Database schema | Implement tenant-based partitioning strategy; add partition management tooling | 2 weeks |
| AI-08 | Data Fabric connectors return mock data | Connectors for external data sources return fake data — cannot be used in production. | `intelligence/data_fabric/` connectors | Implement real connectors for CRM, ERP, market data feeds following DataSource protocol | 2 weeks |
| AI-09 | HNSW index issue with 3072-dim vectors | 3072-dimensional vectors exceed typical HNSW parameter ranges — index may not work correctly. | Vector index configuration | Test and tune HNSW index parameters for 3072-dim; consider dimensionality reduction | 3 days |
| AI-10 | Vectors table type issue (duplicate of ARC-13) | Combined with `ARRAY(FLOAT)` issue — vectors can't leverage pgvector's optimized storage and indexes | Migration + query files | Same as ARC-13 — migrate to `VECTOR(n)` type | 1 week |
| TST-02 | No chaos testing | System resilience under partial failures (DB down, Redis down, provider outage) never tested. | Missing test infrastructure | Add chaos testing with failure injection for all external dependencies | 2 weeks |
| TST-03 | No concurrent write tests | Race conditions, deadlocks, and data corruption under concurrent writes never tested. | Missing test cases | Add concurrent write tests for all write-heavy endpoints | 1 week |
| TST-04 | No multi-tenant isolation tests | Tenant data isolation never verified under load. Risk of cross-tenant data leakage. | Missing test cases | Add multi-tenant isolation tests that verify tenant A cannot access tenant B data | 1 week |
| TST-05 | No visual regression tests | UI changes can break layouts, colors, spacing without detection. Manual visual QA is slow and inconsistent. | Missing test infrastructure | Add visual regression testing with Playwright screenshot comparison | 1 week |
| TST-06 | No a11y unit tests | Accessibility regressions not caught in CI. WCAG compliance degrades over time. | Missing test infrastructure | Add axe-core automated accessibility tests for all components and pages | 1 week |
| TST-08 | No migration rollback tests | Database migrations may not be reversible — production rollback failures cause extended downtime. | Missing test cases | Add migration rollback tests that verify each migration can be rolled back | 3 days |
| PERF-10 | 1 `print()` in production (`metrics.py:18`) | Debug output in production — pollutes logs, may leak internal state | `metrics.py:18` | Replace with proper logging call | 0.5 day |
| PERF-11 | 1 `console.debug` in production (`monitoring.ts:126`) | Debug output in production browser console — pollutes browser console | `monitoring.ts:126` | Remove or gate behind debug flag | 0.5 day |

## P3 — Low (Address opportunistically)

| ID | Description | Impact | Affected Files | Recommendation | Effort |
|----|-------------|--------|---------------|----------------|--------|
| CQ-01 | 284 Python `Any` annotations | Type safety degraded — mypy cannot catch type errors in 284 locations. Testing and refactoring become harder. | `kernel/grounding.py:14`, `pagination.py:6`, `reasoning.py:6` + 268 other locations | Replace `Any` with specific types; progressively increase mypy strictness | 2 weeks (incremental) |
| CQ-02 | 4 TODO comments in production | Incomplete features or known issues embedded in code — no ownership or tracking | Various files | Resolve each TODO or convert to tracked Technical Debt item | 2 days |
| CQ-03 | 18 files exceed 500 lines | Large files are harder to understand, test, and maintain. Increases cognitive load and merge conflict risk. | api.ts (1240), knowledge_graph_runtime (1087), commercial/postgres_repositories.py (861), main.py (773), decision/engine.py (774), + 13 more | Decompose all files >500 lines following Single Responsibility Principle | 1 week per file |
| DSG-07 | Missing Skeleton and EmptyState components | Loading states use spinners instead of layout-appropriate skeletons. Empty states inconsistent across domains. | `@salesos/ui` (missing) | Add Skeleton and EmptyState components with standard pattern | 3 days |
| DSG-08 | Missing form validation integration | No React Hook Form or Zod integration. Form validation is ad-hoc and inconsistent. | `@salesos/ui` (missing) | Add `FormField` wrapper, error state pattern, React Hook Form + Zod integration | 3 days |
| ARC-16 | `api.ts` has 284 Python `Any` annotations (see CQ-01) | Overlaps with CQ-01 — type safety in API layer is particularly important for contract enforcement | `api.ts` | Prioritize `Any` removal in API layer files | 3 days |

## P4 — Deferred (Post-vNext or long-term)

| ID | Description | Impact | Affected Files | Recommendation | Effort |
|----|-------------|--------|---------------|----------------|--------|
| ARC-17 | No partition strategy implemented | Long-term scaling risk — deferred until multi-tenancy v2 | Database schema (deferred) | Revisit when tenant count exceeds 100 | TBD |
| TST-09 | Missing performance/load test suite | No automated performance regression detection. Relying on manual benchmarks. | Missing test infrastructure | Add k6 or locust-based load test suite integrated with CI | 3 weeks |
| TST-10 | Missing E2E test coverage for key user journeys | 269 E2E tests exist but gaps in admin, settings, employee intelligence paths | Missing E2E scenarios | Expand E2E coverage to all critical user journeys | Ongoing |

---

## Summary

| Priority | Count | Total Effort |
|----------|-------|-------------|
| P0 | 12 | ~14 weeks combined (parallelizable across teams) |
| P1 | 29 | ~26 weeks combined (parallelizable across teams) |
| P2 | 17 | ~16 weeks combined |
| P3 | 7 | ~5 weeks combined |
| P4 | 3 | TBD |
| **Total** | **68** | **~61 weeks (parallelizable to ~12-16 weeks calendar)** |
