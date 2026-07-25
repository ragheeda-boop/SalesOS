# SalesOS vNext — Backlog

> **Source**: Code Quality, Performance, Security, Architecture, AI, Design, Testing audits
> **Last Updated**: 2026-07-16

---

## Security

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| SEC-001 | Webhooks router has no authentication — add `Depends(verify_token)` to all webhook routes | P0 | Critical — unauthenticated endpoint, 10/10 posture contradiction | 1 day | None |
| SEC-002 | Admin router uses in-memory stores — migrate to PostgreSQL repositories | P1 | High — state loss on restart, no horizontal scaling | 3 days | Database schema |
| SEC-003 | GraphQL lacks FastAPI-level `Depends(verify_token)` — add global auth dependency | P0 | Critical — GraphQL queries bypass authentication | 1 day | None |
| SEC-004 | JWKS endpoint returns empty symmetric key — remove invalid key, return valid asymmetric keys only | P0 | Critical — token validation effectively disabled | 1 day | None |
| SEC-005 | Grafana default password in `.env.example` — remove default credentials | P1 | High — easy to miss in production, default credential risk | 1 day | None |

## Performance

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| PERF-01 | Middleware body consumption bug — add BodyCache middleware to buffer and restore request body | P0 | Critical — blocks all HTTP load testing, POST endpoints unreliable | 3 days | Middleware chain review |
| PERF-02 | N+1 workspace loop in `commercial.py:470-488` — eager-load or batch-query related data | P0 | Critical — severe degradation on workspace listing, O(N) queries | 3 days | None |
| PERF-03 | N+1 NBA feed in `dashboard/router.py:163-208` — batch-load recommendations | P0 | Critical — severe degradation on NBA feed, O(N) queries | 3 days | None |
| PERF-04 | 12+ endpoints without pagination — add keyset (cursor) pagination to all list endpoints | P0 | Critical — unbounded result sets, memory exhaustion at scale | 2 weeks | Pagination utility library |
| PERF-05 | OFFSET deep pagination causes 3800kB disk spill at 10k rows — replace with keyset pagination | P1 | High — unusable beyond 10k rows, full table scan + sort | 1 week | PERF-04 |
| PERF-06 | 3 separate Redis client pools — consolidate into single connection manager | P1 | Medium — resource waste, connection overhead | 2 days | None |
| PERF-07 | Keyset pagination uses `sorted()`+`slice()` in Python instead of SQL `ORDER BY` | P1 | Medium — sorts full result set in memory, defeats DB optimization | 2 days | None |
| PERF-08 | `search_by_filters` double-query pattern — use `COUNT(*) OVER()` window function | P1 | Medium — doubles database load for every search | 2 days | None |
| PERF-09 | Only 2 endpoints use `@cached` — add caching decorator to all read-heavy low-volatility endpoints | P1 | Medium — repeated identical queries hit database every time | 3 days | Redis pool consolidation (PERF-06) |
| PERF-10 | `print()` in production code (`metrics.py:18`) — replace with proper logging | P2 | Low — debug output pollutes production logs | 0.5 day | None |
| PERF-11 | `console.debug` in production code (`monitoring.ts:126`) — remove or gate behind debug flag | P2 | Low — debug output in browser console | 0.5 day | None |

## Architecture

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| ARC-01 | 1,240-line `api.ts` monolithic router — split into domain-specific API clients | P1 | High — violates DDD isolation, single point of failure for all frontend-backend communication | 1 week | None |
| ARC-02 | 773-line `main.py` monolithic bootstrap — extract into `bootstrap/` module | P1 | High — violates SRP, every new domain adds to this file | 1 week | None |
| ARC-03 | 1,087-line `knowledge_graph_runtime/__init__.py` — decompose into service + repository + router | P1 | High — god object, near-impossible to test or modify safely | 1 week | None |
| ARC-04 | 774-line `decision/engine.py` — split into strategy classes, separate routing and formatting | P1 | Medium — overly coupled, hard to test individual strategies | 3 days | None |
| ARC-05 | 861-line `commercial/postgres_repositories.py` — split into per-entity repository classes | P1 | Medium — bloated repository, difficult maintenance | 2 days | None |
| ARC-06 | 6+ `.env` files, no centralized config — consolidate into pydantic-settings + YAML overlays | P1 | High — configuration scattered, hard to audit, error-prone | 1 week | None |
| ARC-07 | 15+ fragmented testpaths — consolidate into single `tests/pytest.ini` | P1 | Medium — confusing for developers, inconsistent test discovery | 2 days | None |
| ARC-08 | InMemoryNotificationRepository despite DB migration — switch to PostgreSQL-backed repo | P1 | Medium — notification data loss on restart | 2 days | Database schema |
| ARC-09 | Tenant module directory empty — implement tenant provisioning, isolation, quotas | P1 | High — multi-tenancy incomplete, blocking enterprise adoption | 3-4 weeks | Identity domain |
| ARC-10 | 5 runtime engines are stubs (Agent, Execution, Scheduler, Simulation, Workflow) — implement each | P1 | High — placeholder runtimes block automation and AI features | 2-3 weeks per engine | Agent Runtime (AI-02) first |
| ARC-11 | No ADR directory — create ADR directory, migrate architectural decisions | P1 | Medium — governance violation (Constitution Art 3.1), decisions undocumented | 2 days | None |
| ARC-12 | Companies table 3341-byte row width — normalize wide columns, consider vertical partitioning | P2 | Medium — exceeds efficient PostgreSQL page usage, slower scans | 3 days | None |
| ARC-13 | Vectors table uses `ARRAY(FLOAT)` — migrate to native `VECTOR(n)` with HNSW index | P2 | Medium — cannot create vector indexes, similarity search slow | 1 week | Database migration |
| ARC-14 | No API versioning strategy — establish `/api/v2/` convention and breaking change policy | P2 | Medium — breaking changes silently break consumers | 3 days | None |
| ARC-15 | No partition strategy for scale — implement tenant-based partitioning | P2 | Medium — query performance degrades with data growth | 2 weeks | ARC-09 (Tenant domain) |
| ARC-16 | No API versioning strategy — document and enforce URL-based versioning | P2 | Medium — no backward compatibility contract | 3 days | None |

## Frontend

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| FE-01 | Split 1,240-line `api.ts` into domain-specific API clients (identity, company, search, etc.) | P1 | High — single file monolith, cross-domain coupling | 1 week | None |
| FE-02 | Add ESLint rule forbidding Tailwind color classes in page components — enforce CSS variable usage | P1 | Medium — color changes require updating every page | 1 week | None |
| FE-03 | Fix `search_companies` tool returning empty results | P0 | Critical — copilot cannot answer company questions | 2 days | Search API |
| FE-04 | Add Copilot feedback mechanism (thumbs up/down + comment) | P1 | Medium — no feedback loop for AI quality improvement | 1 week | Copilot backend |
| FE-05 | Add copilot tool call observability (success rate, latency, result count) | P1 | Medium — cannot debug tool failures or measure performance | 3 days | Copilot backend |
| FE-06 | Add conversation branching in Copilot | P2 | Low — users cannot explore alternatives without losing context | 1 week | Copilot backend |
| FE-07 | Implement Arabic Copilot support (RTL, Arabic NLP, Saudi context) | P1 | Medium — KSA market requirement | 2 weeks | Arabic NLP module |

## Backend

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| BE-01 | Implement Agent Runtime with lifecycle, retry, observability | P0 | Critical — 15 agents registered but cannot execute | 3-4 weeks | None |
| BE-02 | Write backend AI tests — target 85% coverage on `intelligence/` module | P0 | Critical — zero tests, governance violation | 2 weeks | Agent Runtime (BE-01) |
| BE-03 | Implement Anthropic LLM provider | P1 | High — OpenAI vendor lock-in, no fallback | 1 week | Provider protocol |
| BE-04 | Implement multi-provider query router (route by complexity) | P1 | Medium — simple queries routed to cheap providers | 3 days | BE-03 (Anthropic) |
| BE-05 | Implement embedding cache (LRU, keyed by text_hash + model) | P1 | Medium — redundant embedding calls, 40-60% cost reduction potential | 3 days | None |
| BE-06 | Implement hybrid retrieval (vector + BM25, RRF fusion) | P1 | Medium — improves search quality over vector-only | 1 week | ARC-13 (PGVector) |
| BE-07 | Implement multi-agent orchestration (3+ collaboration patterns) | P2 | Medium — enables complex multi-agent workflows | 2 weeks | BE-01 (Agent Runtime) |
| BE-08 | Implement planning engine (plan-execute-observe loop) | P2 | Medium — enables autonomous agent planning | 2 weeks | BE-01 (Agent Runtime) |
| BE-09 | Implement memory system (multi-tier: working, episodic, semantic, procedural) | P2 | Medium — agents lack persistent context | 1 week | BE-01 (Agent Runtime) |
| BE-10 | Implement Data Fabric real connectors (replace mock data) | P2 | Medium — 3+ real connectors: CRM, ERP, market feeds | 2 weeks | None |
| BE-11 | Implement local KSA LLM provider (on-prem, Arabic native) | P2 | Medium — KSA data sovereignty requirement | 2 weeks | BE-03 (provider protocol) |
| BE-12 | Implement guardrails: PII redaction, jailbreak detection, cost anomaly | P1 | Medium — defense-in-depth AI safety | 1 week | None |
| BE-13 | Implement input/output validators for safety layers | P1 | Medium — structured input/output validation for AI | 1 week | BE-12 |
| BE-14 | Implement decision audit trail (persistent decision records) | P1 | Medium — no decision traceability for compliance | 1 week | None |
| BE-15 | Implement decision feedback loop (store user feedback) | P1 | Low — no signal for decision quality improvement | 3 days | BE-14 |
| BE-16 | Implement multi-provider voting for high-stakes decisions | P1 | Medium — single point of failure for critical decisions | 1 week | BE-03, BE-04 |

## AI

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| AI-01 | Zero backend AI tests — write tests for `intelligence/` module | P0 | Critical — governance violation, no regression safety | 2 weeks | None |
| AI-02 | Agent runtime is placeholder — implement full runtime | P0 | Critical — AI-native vision blocked | 3-4 weeks | None |
| AI-03 | Evaluation `test_cases/` directory empty — create 50+ golden test cases | P0 | Critical — cannot measure regression or compare providers | 2 weeks | Domain experts |
| AI-04 | Only OpenAI supported — add Anthropic provider + fallback chain | P1 | High — vendor lock-in, no data sovereignty option | 2-3 weeks | None |
| AI-05 | No embedding cache — implement LRU cache | P1 | Medium — redundant embedding API calls, cost waste | 3 days | None |
| AI-06 | `search_companies` tool returns empty — fix implementation | P1 | High — frontend agent tool broken | 2 days | Search API |
| AI-07 | No agent observability — add tracing, execution logs, Grafana dashboard | P1 | Medium — cannot debug or monitor agent behavior | 1 week | BE-01 (Agent Runtime) |
| AI-08 | Data Fabric connectors return mock data — implement real connectors | P2 | Medium — connectors not usable in production | 2 weeks | None |
| AI-09 | HNSW index issue with 3072-dim vectors — test and tune parameters | P2 | Medium — vector index may not work correctly | 3 days | ARC-13 (PGVector) |
| AI-10 | Vectors table type `ARRAY(FLOAT)` — migrate to `VECTOR(n)` | P2 | Medium — combined issue with AI-09 | 1 week | ARC-13 |

## Infrastructure

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| INFRA-01 | Consolidate 3 Redis client pools into 1 connection manager | P1 | Medium — resource waste, connection overhead | 2 days | None |
| INFRA-02 | Implement centralized config system (pydantic-settings + YAML overlays) | P1 | Medium — 6+ scattered `.env` files, hard to audit | 1 week | None |
| INFRA-03 | Run dependency audit and update all vulnerable packages | P1 | Medium — dependency vulnerabilities | 2 days | None |
| INFRA-04 | Implement database partitioning strategy for tenant scale | P2 | Medium — single table per entity, no partitioning | 2 weeks | ARC-09 (Tenant) |
| INFRA-05 | Set up multi-region deployment capability (KSA + global) | P2 | Low — KSA PDPL data residency requirement | 3-4 weeks | INFRA-02 |
| INFRA-06 | Implement Kafka event bus with outbox pattern (deferred from V1) | P3 | Low — event-driven architecture for scale | 3-4 weeks | None |

## Design

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| DSG-01 | Login page uses shadcn/ui tokens instead of MUHIDE — replace with semantic MUHIDE tokens | P0 | High — brand inconsistency, first impression problem | 2 days | None |
| DSG-02 | Chart colors use `#3B82F6` (blue) instead of brand `#F57C1E` (orange) — implement 12-color chart token palette | P0 | High — brand misalignment, backend token mismatch | 2 days | None |
| DSG-03 | Muted text `#A59E90` fails WCAG AA (2.9:1, needs 4.5:1) — update `--text-muted` to `#8C8374` | P0 | Critical — accessibility violation, legal risk | 1 day | None |
| DSG-04 | Missing Checkbox, Radio, Switch, Textarea, DatePicker — implement all with full ARIA + RTL + error states | P0 | High — cannot build standard forms, blocking all data-entry surfaces | 5 days | None |
| DSG-05 | Pages use Tailwind color classes instead of CSS variables — add ESLint rule + codemod migration | P1 | Medium — no semantic color abstraction, hard to maintain | 1 week | None |
| DSG-06 | Duplicate Card component in `@salesos/ui` — remove deprecated Card, update imports | P0 | Medium — confusion, potential style conflicts | 0.5 day | None |
| DSG-07 | Missing Skeleton and EmptyState components — implement standard loading/empty pattern | P1 | Medium — inconsistent loading and empty states across domains | 3 days | None |
| DSG-08 | Missing toast/notification system — add `useToast()` + `<ToastContainer>` | P1 | Medium — no standardized async feedback | 2 days | None |
| DSG-09 | Missing form validation integration — add React Hook Form + Zod support, `FormField` wrapper | P1 | Medium — ad-hoc form validation, inconsistent error display | 3 days | DSG-04 |
| DSG-10 | Missing DataTable features (sort, select, sticky header) — enhance `<Table>` component | P1 | Medium — core data interaction lacking standard features | 5 days | DSG-04 |
| DSG-11 | Missing Sidebar + Breadcrumbs navigation components — build standard navigation | P1 | Medium — no unified navigation component | 4 days | None |
| DSG-12 | Missing Dark Mode verification pass — verify all surfaces have dark variants | P2 | Low — dark mode may have gaps | 3 days | None |
| DSG-13 | Chart colors missing dark mode variants — add `--chart-*` dark tokens | P2 | Low — charts may not render correctly in dark mode | 1 day | DSG-02 |

## Testing

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| TST-01 | Workspace core package has 0 tests — write unit tests for all service and repository classes | P1 | High — core workspace functionality completely untested | 1 week | None |
| TST-02 | No chaos testing — add failure injection tests for DB, Redis, provider outages | P2 | Medium — resilience under partial failures unknown | 2 weeks | Test infrastructure |
| TST-03 | No concurrent write tests — add race condition and deadlock tests | P2 | Medium — data corruption under concurrent writes unknown | 1 week | None |
| TST-04 | No multi-tenant isolation tests — verify tenant A cannot access tenant B data | P2 | Critical — cross-tenant data leakage risk not tested | 1 week | None |
| TST-05 | No visual regression tests — add Playwright screenshot comparison | P2 | Medium — UI breaks not caught in CI | 1 week | None |
| TST-06 | No a11y unit tests — add axe-core automated accessibility tests for all components and pages | P2 | Medium — WCAG compliance degrades without automated checks | 1 week | None |
| TST-07 | No API contract tests — add provider contract tests for each endpoint, consumer contract tests for each frontend API client | P1 | High — API changes can break frontend without detection | 2 weeks | None |
| TST-08 | No migration rollback tests — verify each migration can be rolled back | P2 | Medium — production rollback failures cause extended downtime | 3 days | Migration infra |
| TST-09 | No performance/load test suite — add k6 or locust-based tests integrated with CI | P3 | Low — no automated performance regression detection | 3 weeks | PERF-01 (middleware fix) |
| TST-10 | E2E test gaps in admin, settings, employee intelligence — expand coverage | P3 | Low — 269 E2E tests exist but key paths missing | Ongoing | None |

## Developer Experience

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| DX-01 | 284 Python `Any` annotations degrade type safety — replace with specific types progressively | P3 | Medium — type safety degraded, mypy cannot catch type errors in 284 locations | 2 weeks (incremental) | None |
| DX-02 | 4 TODO comments in production — resolve or convert to tracked Technical Debt | P3 | Low — incomplete features embedded in code with no ownership | 2 days | None |
| DX-03 | 18 files exceed 500 lines — decompose following SRP | P3 | Medium — large files harder to understand, test, maintain | Ongoing per file | None |
| DX-04 | 15+ fragmented testpaths — consolidate into single `tests/pytest.ini` | P1 | Medium — confusing test discovery, inconsistent config | 2 days | None |
| DX-05 | No ADR directory — create docs/adr/ and migrate architecture decisions | P1 | Medium — governance violation, decisions undocumented | 2 days | None |
| DX-06 | 6+ `.env` files — consolidate into centralized config | P1 | Medium — scattered config, hard to audit, error-prone | 1 week | None |
| DX-07 | No API versioning documented — establish and document versioning convention | P2 | Low — breaking changes handled ad-hoc | 3 days | None |

## Documentation

| ID | Description | Priority | Impact | Effort | Dependencies |
|----|-------------|----------|--------|--------|-------------|
| DOC-01 | Create ADR directory and migrate all architecture decisions to ADR format | P1 | Medium — governance requirement (Constitution Art 3.1) | 2 days | None |
| DOC-02 | Document API versioning strategy and breaking change policy | P2 | Low — no documented contract for API consumers | 2 days | ARC-14 |
| DOC-03 | Document chart color sequence for backend team reference | P2 | Low — backend chart tokens misaligned with frontend | 1 day | DSG-02 |
| DOC-04 | Update runbook with new middleware chain, config system, redis pool | P1 | Medium — operational docs outdated after Phase 0 changes | 3 days | Phase 0 |
| DOC-05 | Document Agent Runtime API for agent developers | P1 | Medium — agent developers need API reference | 3 days | BE-01 |

---

## Summary

| Category | P0 | P1 | P2 | P3 | Total |
|----------|----|----|----|----|-------|
| Security | 3 | 2 | 0 | 0 | 5 |
| Performance | 5 | 4 | 2 | 0 | 11 |
| Architecture | 0 | 11 | 5 | 0 | 16 |
| Frontend | 1 | 4 | 1 | 0 | 6 |
| Backend | 2 | 8 | 6 | 0 | 16 |
| AI | 3 | 4 | 3 | 0 | 10 |
| Infrastructure | 0 | 3 | 2 | 1 | 6 |
| Design | 5 | 5 | 2 | 0 | 12 |
| Testing | 0 | 2 | 6 | 2 | 10 |
| Developer Experience | 0 | 3 | 1 | 3 | 7 |
| Documentation | 0 | 3 | 2 | 0 | 5 |
| **Total** | **19** | **49** | **30** | **6** | **104** |
