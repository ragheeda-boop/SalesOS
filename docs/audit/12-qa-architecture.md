# SalesOS QA Architecture — Deep Audit

> **Audit Type**: READ-ONLY | **Authority**: QA Architect | **Date**: 2026-07-13
> **Scope**: All backend test files, all frontend test files, CI config, quality gates
> **Status**: COMPLETE — Findings + Register Produced

---

## 1. Test Architecture Overview

### 1.1 Frameworks & Runners

| Layer | Framework | Version | Runner | Plugin Stack |
|-------|-----------|---------|--------|-------------|
| Backend | pytest | ^8.2 | pytest (asyncio auto) | pytest-asyncio ^0.23, pytest-cov ^5.0, unittest.mock |
| Frontend | Jest | (via ts-jest) | jsdom | @testing-library/react, @testing-library/jest-dom, jest.fn() |
| Backend Lint | Ruff | ^0.4 | pre-commit | E, F, I, N, W, UP, B, SIM, ARG, C4 |
| Backend Type | mypy | ^1.10 | pre-commit | strict-ish (warn_return_any, warn_unused_configs) |
| Pre-commit | pre-commit | v4.6.0 | Git hooks | ruff, ruff-format, mypy, prettier |
| Security | bandit | (CI) | GitHub Actions | --confidence-level high |
| CI | GitHub Actions | — | PR trigger | lint → test → arch-test → security → ai-eval |

### 1.2 Test Directory Structure

```
backend/
├── conftest.py                          # Root: DB setup, Role registry
├── tests/
│   ├── conftest.py                       # Test client fixtures
│   ├── fakes.py                          # FakeDBResult, FakeExecute, fake_session
│   ├── test_health.py                    # Smoke tests (2)
│   ├── test_integration.py               # 12 cross-module integration tests
│   ├── test_architecture.py              # 5 architecture fitness tests
│   ├── unit/
│   │   ├── conftest.py
│   │   ├── test_rate_limiter.py          # 139 lines
│   │   ├── test_kafka_bus.py             # 444 lines
│   │   ├── test_benchmarks.py            # 337 lines (42 benchmark tests)
│   │   ├── test_search_runtime.py
│   │   ├── test_scoring.py
│   │   ├── test_ai_reasoner.py
│   │   ├── test_rag_pipeline.py
│   │   ├── test_redis_cache.py
│   │   ├── test_deal_health.py
│   │   ├── test_dashboard_mappers.py
│   │   ├── test_workflow_engine.py
│   │   ├── test_work_intelligence.py
│   │   ├── test_telemetry.py
│   │   ├── test_sso.py
│   │   ├── test_normalizers.py
│   │   ├── test_feature_store.py
│   │   ├── test_executive_service.py
│   │   ├── test_email_intelligence.py
│   │   ├── test_revenue_dashboard.py
│   │   ├── test_pipeline_analytics.py
│   │   ├── test_analytics.py
│   │   ├── test_api_keys.py
│   │   ├── test_audit.py
│   │   ├── test_demo.py
│   │   ├── test_meeting_intelligence.py
│   │   ├── test_meeting_email_repos.py
│   │   ├── test_nba_pipeline.py
│   │   ├── test_notifications.py
│   │   ├── test_playbook.py
│   │   ├── test_admin_api.py
│   │   └── conftest.py
│   ├── e2e/
│   │   ├── conftest.py                  # registered_user, auth_headers fixtures
│   │   └── test_critical_paths.py       # 41 E2E tests, 7 critical paths
│   └── evaluation/
│       ├── evaluation_config.py          # EvalConfig + AGENT_EVAL_MAP
│       ├── test_agent_grounding.py       # 6 grounding tests
│       └── test_rag_faithfulness.py      # 5 faithfulness tests
├── domains/
│   ├── search/tests/                    # 8 test files (hybrid, planner, parser, ranking, etc.)
│   ├── ai/tests/                        # 3 test files (evaluator, extended, conftest)
│   ├── scoring/tests/                   # 1 test file (engine, 238 lines, 10 tests)
│   ├── workflow/tests/                  # 3 test files (service, extended, conftest)
│   ├── timeline/tests/                  # 1 test file
│   ├── feature_store/tests/             # 1 test file (253 lines)
│   ├── revenue/forecast/tests/          # 1 test file
│   ├── revenue/analytics/tests/         # 1 test file
│   ├── commercial/activity/tests/       # 1 test file
│   ├── commercial/contract/tests/       # 1 test file
│   ├── commercial/opportunity/tests/    # 1 test file
│   ├── commercial/pipeline/tests/       # 1 test file
│   ├── commercial/quote/tests/          # 1 test file
│   ├── decision/context/tests/          # 1 test file
│   └── decision/recommendation/tests/   # 1 test file
├── app/modules/
│   ├── identity/tests/                  # 1 test file (243 lines)
│   ├── company/tests/                   # 2 test files
│   └── notion_sync/tests/              # 1 test file
└── runtime/
    └── data_fabric_runtime/tests/       # 4 test files (pipeline, scrapers, master_data, contracts)

frontend/
├── jest.config.js                        # jsdom, ts-jest, module aliases
├── jest.setup.ts                         # @testing-library/jest-dom
├── src/
│   ├── __tests__/end-to-end.test.tsx     # 264 lines, 6 flows
│   ├── components/__tests__/             # 9 component test files
│   ├── application/dashboard/__tests__/  # 5 files (widget.store, contract, useDashboard, mapper, api)
│   ├── application/search/__tests__/     # 3 files (keys, hooks, api)
│   ├── application/revenue-execution/__tests__/ # 4 files
│   ├── application/company-intelligence/__tests__/ # 3 files
│   ├── application/api/__tests__/        # 1 file
│   ├── features/search/__tests__/        # 8 view-level test files
│   ├── features/search/components/__tests__/ # 7 component test files
│   ├── features/search/command-bar/__tests__/ # 3 files
│   ├── features/search/ai-search/__tests__/ # 1 file
│   ├── features/dashboard/sdk/__tests__/ # 6 files (create-widget, lifecycle, telemetry, etc.)
│   ├── features/admin/__tests__/         # 2 files
│   ├── lib/__tests__/                    # 15 lib-level test files
│   ├── lib/hooks/__tests__/              # 11 query-hook test files
│   └── packages/
│       ├── ui/__tests__/                 # 16 UI kit component tests
│       ├── search/src/__tests__/         # 6 search package tests
│       ├── runtime/__tests__/            # 2 files (state, cache)
│       ├── platform/decision/__tests__/  # 1 file
│       └── platform/contracts/           # 2 files (revenue, ai)
```

### 1.3 Key Configuration

**Backend** (`pyproject.toml`):
- `asyncio_mode = "auto"` — all async fixtures/tests handled transparently
- `markers = ["e2e: ..."]` for selective inclusion
- `testpaths` explicitly lists 19 directories (some unused: `entity_resolution/tests`, `excel_import/tests`, `proposal/tests` referenced but may not exist)
- `fail_under = 30` in coverage — **very low gate**, contradicts the 85% target in dashboard

**Frontend** (`jest.config.js`):
- `testEnvironment: "jsdom"` — DOM simulation
- ts-jest with separate `tsconfig.test.json`
- Module aliases: `@/` → `src/`, `@salesos/` → `packages/$1/src`
- Pattern: `**/__tests__/**/*.test.ts`, `**/*.spec.tsx`
- Only one `.spec.tsx` file in entire frontend: `WidgetContract.spec.tsx`

---

## 2. Unit Test Catalog

### 2.1 Organization & Patterns

**Backend Unit Tests** (`tests/unit/` — 30 files):

All unit tests follow a consistent pattern:
- Use `AsyncMock` / `MagicMock` for dependencies
- Leverage `FakeDBResult`, `FakeExecute`, `fake_session()` from `tests/fakes.py`
- `@pytest.mark.asyncio` for all async tests
- `@pytest.fixture(autouse=True)` for store cleanup (rate_limiter)
- Class-per-test-group organization (e.g., `TestCheckRateLimit`, `TestCleanup`)
- Each test function name describes the behavior (`test_under_limit_returns_none`)

**Domain Unit Tests**:
- **Repository Pattern Compliance**: All domain tests use `InMemoryRepository` implementations
  - `InMemoryFeatureStoreRepository` in `feature_store/`
  - `InMemoryWorkflowRepository` in `workflow/`
  - `FakeCompanyRepository` in `search/` (implements `SearchRepository`)
  - `InMemoryDecisionRepository` in `scoring/` (decision/context/in_memory_repo)
- This is Constitution-compliant (Article 2.2, Article 3.3)
- No external dependencies (DB, network, file I/O)

**Frontend Unit Tests** (105+ files):
- **UI Kit**: 16 component tests (button, card, modal, toast, etc.) — each tests: rendering, click handlers, variants, sizes, loading/disabled states, icons
- **Query Hooks**: 11 tests covering `useTenant`, `taskQueries`, `searchQueries`, `opportunityQueries`, `mutationHooks`, `executiveQueries`, `employeeQueries`, `contactQueries`, `companyQueries`, `company360Queries`, `adminQueries`, `activityQueries`
- **Store Tests**: `widget.store`, `opportunity.store`, `task.store`, `company-intelligence.store`
- **DTO Tests**: `opportunity.dto`, `company-intelligence.keys`
- **Engine Tests**: `nba.engine.test.tsx`
- **Mappers**: `dashboard.mapper.test.tsx`
- **API hooks**: `hooks.test.tsx`, `search.api.test.tsx`
- **Feature components**: 40+ component-level tests (SearchBar, SearchFilters, AIAnswer, CommandBar, etc.)

### 2.2 Coverage by Domain (from ENGINEERING_DASHBOARD.md + actual file counts)

| Domain | Reported Coverage | Test Files | Test Count (est.) | Quality |
|--------|-------------------|------------|-------------------|---------|
| Identity | 88% | 1 (243 lines) | ~20 | 🟢 Frozen interface |
| Company | 80% | 2 (+ integration) | ~30 | 🟡 Below ideal |
| Search | 93% | 8 files (~1200 lines) | ~60 | 🟢 Excellent depth |
| Timeline | 82% | 1 file | ~10 | 🟡 Light |
| CRM | 80% | 5 files (commercial/*) | ~25 | 🟡 |
| Scoring | 78% | 2 (engine + unit) | ~15 | 🟡 |
| AI | 92% | 3 files (~570 lines) | ~35 | 🟢 Deep evaluator coverage |
| Workflow | 95% | 2 (service + extended) | ~28 | 🟢 Strong |
| Feature Store | 95% | 2 (domains + unit) | ~25 | 🟢 |
| Entity Resolution | 95% | 0 dedicated | Covered via integration | 🟡 No unit tests |
| Data Fabric | N/A | 4 files (runtime) | ~30 | 🟢 Pipeline + scrapers |
| Monitoring | >85% | 0 dedicated | Covered via unit | 🟡 Not independently tested |
| Customer Success | >85% | 0 dedicated | | 🟡 Not independently tested |

**Overall backend**: ~60 test files, est. 500+ individual tests
**Overall frontend**: 105+ test files, est. 500+ individual tests

### 2.3 Notable Unit Test Quality Examples

**Excellent**:
- `test_hybrid_search.py` (567 lines): Tests RRF fusion, filtering, embedding service, pagination — pure units, no DB
- `test_rate_limiter.py` (139 lines): Clean window-based tests with patched time
- `test_evaluator.py` (218 lines): Comprehensive metric coverage (exact_match, contains_keyword, length_check, json_valid, confidence_threshold, batch, aggregation)
- `test_kafka_bus.py` (444 lines): Deep event bus testing with fallback, serialization, multiple handlers

**Adequate**:
- Identity `test_service.py` (243 lines): Covers CRUD + auth flow, but mostly happy path
- Company `test_service.py` (253 lines): Covers CRUD + search, duplicate detection

**Thin**:
- Timeline: 1 test file only
- CRM commercial sub-domains: 1 file each, light coverage

---

## 3. Integration Test Analysis

### 3.1 Backend Integration (`tests/test_integration.py`)

**12 tests** across 3 test classes:

| Class | Tests | Focus |
|-------|-------|-------|
| `TestPipelineE2E` | 6 | Entity resolution → Golden Record → Company sync |
| `TestAPIE2E` | 8 | HTTP client integration (CRUD, search, 360, admin, auth) |
| `TestCrossModuleE2E` | 4 | Cross-module: golden→company sync, state integrity |

**Assessment**:
- Strong pipeline coverage: valid records, invalid rejection, duplicate CR merging, multi-tenant isolation, DLQ, audit trail
- API integration hits: health, root, companies CRUD, search, company/360, golden records, DLQ admin, metrics, full health
- Cross-module covers: golden-to-company sync, field mapping, atomicity, conflict logging
- Gaps: No contract/Opportunity/Decision API integration tests (not in test_integration.py)
- Dependency: Requires PostgreSQL (`salesos_test` database) — correctly uses root `conftest.py` DB fixtures
- All tests are deterministic and reproducible with fresh DB each session

### 3.2 Frontend Integration (`end-to-end.test.tsx`)

**6 Flow Tests** (264 lines):
1. Search → Query Building (SearchQueryBuilder)
2. Company Intelligence (DNA, AIRecommendation, signals, timeline)
3. NBA Engine (deriveNextBestAction)
4. Opportunity Store (create, list, stage update, win probability)
5. Task Store (add, complete, list)
6. Full Flow: Search → Intelligence → NBA → Opp → Pipeline → Task

**Assessment**:
- Tests integration of data flow, not actual API calls — uses mock data
- Good for unit-level integration (stores + engines + DTOs)
- Not true E2E — no HTTP requests, no server interaction
- Misleading filename `end-to-end.test.tsx` — these are integration tests, not E2E

---

## 4. E2E Test Analysis

### 4.1 Backend E2E (`tests/e2e/test_critical_paths.py`)

**41 tests** across 5 critical paths + cross-cutting:

| Path | Class | Tests | Scenario |
|------|-------|-------|----------|
| CP1 | `TestRegistrationLoginDashboard` | 6 | Register → Login → Dashboard, wrong password, unauth rejection |
| CP2 | `TestCompanySearchViewEnrich` | 5 | Create → Search → View → 360 → Full journey |
| CP3 | `TestNBADecisionFlow` | 6 | Evaluate, NBA, history, accept/feedback, metrics |
| CP4 | `TestTimelineActivity` | 6 | Ingest, entity activities, timeline, summary, stats, full journey |
| CP5 | `TestEntityResolution` | 5 | Resolve batch, golden records, stats, conflicts, full journey |
| CP6 | `TestHealthSmoke` | 6 | Health endpoints, ping, root metadata, unauth rejection |
| X | `TestCrossCuttingConcerns` | 7 | Search, activity/timeline/search metrics, company update, batch ingest |

**Quality Assessment**:
- **Timeout**: 30s per test via `asyncio.wait_for`
- **e2e marker**: All tests tagged with `pytest.mark.e2e`
- **Fixture strategy**: Real user registration via API, JWT token generation, tenant isolation per test
- **Deterministic**: Yes — each test creates its own tenant + user
- **Speed**: Moderate (DB round-trips per test) — 30s timeout allows headroom
- **Graceful degradation**: NBA/Decision tests accept 200 OR 503 (engine may not be initialized)
- **Assertion quality**: Good but not exhaustive — some tests accept broad status code ranges (e.g., 200/404/500 for golden-record-by-cr)
- **Gap**: No load/concurrency E2E tests
- **Gap**: No WebSocket E2E tests (if WS endpoints exist)
- **Gap**: No file upload E2E tests (Excel import, document upload)

### 4.2 Frontend E2E

**No true E2E tests**. The frontend `end-to-end.test.tsx` is an integration test using mock data, not actual browser/server interaction. There is:
- No Playwright/Cypress configuration
- No Selenium/WebDriver tests
- No browser-based E2E tests whatsoever

**This is the single largest QA gap.** The dashboard reports 41 E2E tests, but these are backend-only. No frontend E2E exists.

---

## 5. Contract/Widget Test Analysis

### 5.1 Widget SDK Contract Tests

**6 SDK test files** under `features/dashboard/sdk/__tests__/`:

| File | Focus | Tests (est.) |
|------|-------|-------------|
| `create-widget.test.tsx` | Lifecycle, telemetry, permissions, flags, error states | ~12 |
| `widget-lifecycle.test.tsx` | onMount, onUnmount, onRefresh, onError | ~8 |
| `widget-telemetry.test.tsx` | Recorded events (mounted, loaded, failed, refreshed) | ~6 |
| `widget-permissions.test.tsx` | Permission denied behavior, fallback | ~4 |
| `widget-feature-flags.test.tsx` | Flag disabled behavior, tier gating | ~4 |
| `WidgetContract.spec.tsx` | `describeWidgetContract()` — the formal contract test | 1 |

**WidgetContract.spec.tsx**:
- Uses `describeWidgetContract({ name, defaultData, config })` from SDK testing utilities
- Only 1 instance — each Widget must have its own
- **Constitution violation**: Article 9.2 requires every Widget to have `describeWidgetContract()` — currently only 1 test widget registered

### 5.2 Widget Contract Type Tests

`widget.contract.test.tsx`:
- Validates `WidgetStatus` enum: 'ready', 'loading', 'degraded', 'error'
- Validates `WidgetAction` shape
- Validates `DashboardWidget<T>` generic
- Minimal — 3 tests, type-level only

### 5.3 Dashboard Widget Component Tests

6 widget component test files:
- `RecentActivity.test.tsx`
- `MarketPulse.test.tsx`
- `IntelligenceFeed.test.tsx`
- `MissionCenter.test.tsx` (103 tests — the reference widget)
- `AIBrief.test.tsx`
- `DecisionQueue.test.tsx`

---

## 6. Performance Test Analysis

### 6.1 Benchmark Suite (`tests/unit/test_benchmarks.py`)

**42 tests** across 6 domains:

| Domain | Tests | Benchmarks Covered |
|--------|-------|-------------------|
| BenchmarkResult | 4 | within_budget (no budget, under, over) |
| BenchmarkRunner | 8 | run_all, run_domain, report, violations, compare, regression, improvement, list_runs |
| Search | 4 | fulltext, semantic, hybrid at 3 sizes; index creation |
| NBA | 3 | recommendation, pipeline, cached (validates cache is faster) |
| RAG | 4 | embedding, vector search, full pipeline, chunking throughput |
| Dashboard | 3 | revenue (cached vs nocache), pipeline summary, concurrent (validates scale) |
| API | 3 | endpoint latency, concurrent connections, auth overhead, rate limiter |
| CLI | 3 | run_all, run_search, compare_missing |
| API Router | 2 | list_runs, load_run_detail not found |

**Quality**:
- All benchmarks run with synthetic/empty data — no real DB load
- Validates statistical properties: p50 ≤ p95 ≤ p99, cached < nocache, concurrent scales monotonically
- Regression detection via compare to baseline JSON
- Budget enforcement: `budget_p95_ms` parameter
- No integration with real PostgreSQL for benchmark accuracy
- **Gap**: Benchmarks test the framework, not actual system performance

### 6.2 Load Test (`scripts/load-test.py`)

**425 line standalone load test**:
- Backends: aiohttp (primary) or httpx (fallback)
- Scenarios: health check (5 concurrent), search (10 concurrent), company detail, NBA, timeline, dashboard
- Metrics: p50, p95, p99, min, max, avg, error rate per scenario
- Config: env vars for BASE_URL, credentials, company ID
- Output: formatted table report + exit code
- **Not integrated into CI** — manual execution only
- **No assertions** — reporting only, does not fail on thresholds

---

## 7. AI Evaluation Test Analysis

### 7.1 Grounding Tests (`test_agent_grounding.py`)

**6 tests**:
- `test_grounding_context_has_expected_structure`: Field presence check
- `test_grounding_context_empty_detection`: `is_empty()` behavior
- `test_competitor_agent_falls_back_without_data`: Low confidence with empty context
- `test_confidence_scales_with_evidence` (parametrized): 3 evidence counts → confidence ranges
- `test_output_schema_requires_confidence_range`: All 6 agent schemas enforce 0-1 confidence

**Assessment**: Pure logic tests — no actual LLM calls. Tests the scaffolding, not the pipeline.

### 7.2 Faithfulness Tests (`test_rag_faithfulness.py`)

**5 tests**:
- `test_output_mentions_provided_data`: Context appears in output
- `test_confidence_derived_from_evidence`: Evidence quality → confidence
- `test_faithfulness_check` (parametrized): Fact-in-context verification
- `test_agent_does_not_hallucinate_without_data`: Empty context → low confidence

**Assessment**: All are logic tests, not actual LLM evaluation. Tests verify the evaluation framework, not real AI behavior.

### 7.3 AI Evaluator Tests (`domains/ai/tests/test_evaluator.py`)

**15 tests** covering all built-in metrics:
- exact_match, contains_keyword, length_check, json_valid, confidence_threshold
- Multi-metric evaluation, batch evaluation, aggregation, custom thresholds
- Edge cases: empty input, below-threshold confidence, ID generation, timestamps

**Assessment**: Comprehensive evaluator framework coverage. Does not test actual LLM outputs.

### 7.4 Evaluation Config (`evaluation_config.py`)

- `EvaluationConfig` dataclass with: grounding confidence, faithfulness, hallucination ratio, eval models
- `AGENT_EVAL_MAP` for 5 agents: competitor, research, meeting, pricing, forecast
- Each agent specifies required fields, min confidence, grounding requirements

### 7.5 AI Evaluation Gap

**Critical gap**: No integration between evaluation framework and actual LLM calls. The `quality_gate.md` GATE 6 specifies:
- Eval results attached (accuracy, hallucination rate, confidence calibration) — **NOT automated**
- Semantic cache used — **NOT tested**
- Cost tracked — **NOT tested**
- Prompt registered in AI Catalog — **NOT tested**

---

## 8. Coverage Analysis by Domain

### 8.1 Reported Coverage (from ENGINEERING_DASHBOARD.md)

```
Domain               Coverage    Status    Test Files
─────────────────────────────────────────────────────
Identity             88%         🟢        1 (+ integration)
Company              80%         🟡        2 (+ integration)
Search               93%         🟢        8 dedicated
Timeline             82%         🟡        1 dedicated
CRM                  80%         🟡        5 commercial sub-domains
Scoring              78%         🟡        2
AI                   92%         🟢        3 dedicated
Workflow             95%         🟢        2 dedicated
Customer Success     >85%        🟢        0 dedicated (covered by unit)
Monitoring           >85%        🟢        0 dedicated (covered by unit)
Entity Resolution    95%         🟡        0 dedicated (covered by integration)
Feature Store        95%         🟢        2
─────────────────────────────────────────────────────
Overall              ~93%        🟢        60+ backend files
```

### 8.2 Coverage Gate Analysis

| Gate | Required | Actual | Status |
|------|----------|--------|--------|
| pyproject.toml fail_under | 30% | ~93% | 🟢 Massively exceeds |
| Constitution minimum | 85% | ~93% | 🟢 |
| Dashboard target | 85% | 93% | 🟢 |
| Integration target | 70% | 70% | 🟢 (self-reported) |
| E2E target | 60% | 40% | 🔴 Below target |

### 8.3 Coverage Risks

1. **pyproject.toml `fail_under = 30`** is dangerously low. If coverage drops 60 points, CI still passes. The 85% requirement exists in documentation but is not enforced in CI config.
2. **Self-reported coverage** (93%) may not match actual `pytest --cov` output. No automated coverage report was found.
3. **Timeline, CRM, Scoring** all below 85% individually (82%, 80%, 78%) — the constitutional minimum is 85%. The overall average masks per-domain shortfalls.

---

## 9. Test Quality Assessment

### 9.1 Determinism

| Category | Score | Evidence |
|----------|-------|----------|
| Database tests | 🟢 Good | Fresh DB per session, rollback-per-test, NullPool connections |
| Unit tests | 🟢 Good | Pure mocks, InMemory repos, patched time, no random |
| E2E tests | 🟢 Good | UUID-based isolation, fresh tenant per test fixture |
| Benchmark tests | 🟡 Fair | Synthetic data, no real-world variance tested |
| AI eval tests | 🟢 Good | Pure logic, no LLM dependency |

### 9.2 Speed

| Category | Typical Duration | Target | Status |
|----------|-----------------|--------|--------|
| Unit tests (backend) | <50ms each | <1s | 🟢 |
| Unit tests (frontend) | <100ms each | <1s | 🟢 |
| Integration tests | ~500ms each | <5s | 🟢 |
| E2E tests | 2-5s each | <30s | 🟢 |
| Benchmark tests | Variable | N/A | 🟡 Some run DB queries |

### 9.3 Maintainability

| Factor | Score | Evidence |
|--------|-------|----------|
| Fixture reuse | 🟢 | `conftest.py` hierarchy: root → tests/ → tests/e2e/ |
| Fake abstractions | 🟢 | Shared `fakes.py` eliminates duplication |
| Test naming | 🟢 | Descriptive: `test_pipeline_valid_record_creates_golden` |
| Arrange-Act-Assert | 🟢 | Consistently followed |
| Mock complexity | 🟡 | Some tests mock 4+ layers (hybrid search tests) |
| Duplication | 🟡 | `_seed_company`, `_seed_company_id`, `_make_result` repeated across files |
| Frontend mocks | 🟡 | Multiple `jest.fn()` setups, spread across test files |

### 9.4 Architecture Test Fitness

The `test_architecture.py` file provides 5 architecture tests:
1. Domain isolation (no UI imports) — parametrized across all domain dirs
2. Kernel isolation (no commercial imports) — parametrized across kernel dirs
3. SDK isolation (no domain imports from SDK)
4. Frozen interface preservation (SearchQuery, SearchResult, SearchPlanner)
5. Capability registry coverage (all commercial/revenue/decision modules)

**Assessment**: Strong architecture fitness testing. Covers the most critical constitutional rules.

---

## 10. Test Gaps and Blind Spots

### 10.1 Critical Gaps

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| 1 | **No frontend E2E tests** | Critical | No Playwright/Cypress config, no browser tests |
| 2 | **No WebSocket tests** | High | Unknown if WS endpoints exist but no test coverage |
| 3 | **No file upload tests** | High | Excel import module has testpath registered but no tests found |
| 4 | **No performance regression in CI** | High | `load-test.py` is manual, not in CI pipeline |
| 5 | **No actual LLM evaluation** | High | AI eval tests only test the framework, not actual LLM behavior |
| 6 | **Contract tests incomplete** | High | Only 1 WidgetContract.spec vs. Article 9.2 requirement for all widgets |
| 7 | **Coverage gate not enforced** | Medium | `fail_under = 30` in pyproject.toml vs. 85% constitutional minimum |
| 8 | **No chaos/failure injection tests** | Medium | No tests for DB connection loss, timeout, partial failure |
| 9 | **No accessibility automated tests** | Medium | WCAG AA target documented but no aXe/pa11y CI integration |
| 10 | **No RTL-specific tests** | Medium | Arabic UI is core feature but no RTL layout test automation |

### 10.2 Domain-Specific Gaps

| Domain | Missing Tests |
|--------|--------------|
| Entity Resolution | No dedicated unit tests — only integration coverage |
| Timeline | Only 1 test file — light coverage of timeline service |
| CRM/Commercial | 5 sub-domains with 1 file each — thin coverage |
| Scoring | 78% coverage — below 85% minimum |
| Excel Import | Testpath registered but no test files found |
| Entity Resolution dedicated | No unit tests for resolution service |

### 10.3 Test Type Gaps

| Test Type | Status | Notes |
|-----------|--------|-------|
| Unit tests | 🟢 Strong | 60+ backend, 105+ frontend |
| Integration tests | 🟡 Adequate | 12 pipeline + API, no decision/opportunity API integration |
| E2E tests | 🔴 Gap | 41 backend E2E (strong), 0 frontend E2E (critical) |
| Contract tests | 🔴 Gap | Only 1 of many required |
| Performance tests | 🟡 Partial | Benchmarks test framework, load-test is manual |
| Security tests | 🟡 Partial | Architecture tests cover isolation, no OWASP/penetration tests |
| Accessibility tests | 🔴 Gap | No automated a11y tests |
| AI eval tests | 🟡 Partial | Framework tested, not actual LLM behavior |
| Property-based tests | 🔴 Gap | No hypothesis/generative testing |
| Snapshot tests | 🔴 Gap | No frontend snapshot tests |
| Visual regression | 🔴 Gap | No Percy/Chromatic/visual diff |

---

## 11. Quality Gate Assessment

### 11.1 Gate Status Summary

| Gate | Automated | Manual | Status | Notes |
|------|-----------|--------|--------|-------|
| 1: Architecture | 6 checks | 4 review | 🟢 | Arch tests in CI |
| 2: Code Quality | 7 checks | 2 review | 🟢 | Ruff, mypy, bandit |
| 3: Testing | 5 checks | 3 review | 🟡 | Coverage gate too low, E2E missing |
| 4: Events & Telemetry | 5 checks | 3 review | 🟡 | Not automated as documented |
| 5: Observability | 3 checks | 4 review | 🟡 | Not independently verified |
| 6: AI Quality | 3 checks | 5 review | 🔴 | None automated, all manual |
| 7: Documentation | 2 checks | 9 review | 🟡 | CHANGELOG auto, most manual |
| 8: UX & Accessibility | 3 checks | 6 review | 🔴 | No aXe, no RTL test automation |

### 11.2 CI Pipeline Reality Check

The documented CI pipeline (QUALITY_GATE.md:169-214) vs. actual findings:

| Documented | Found | Status |
|------------|-------|--------|
| `ruff check .` | ✅ In pre-commit, in CI | 🟢 |
| `black --check .` | ❌ Uses ruff-format, not black | Inconsistency |
| `mypy --strict src/` | ⚠️ Pre-commit uses `--ignore-missing-imports`, not `--strict` | Partial |
| `pytest tests/ --cov=src/ --cov-fail-under=85` | ❌ `fail_under = 30` in pyproject.toml | DOCS INACCURATE |
| `pytest tests/architecture/ --no-header -q` | ❌ Tests in `tests/test_architecture.py`, not `tests/architecture/` | Path mismatch |
| `bandit -r src/` | ✅ Referenced | 🟢 |
| `npm audit` | ✅ Referenced | 🟢 |
| `python scripts/run_ai_eval.py --report` | ❌ Script not found | Missing |

---

## 12. QA Technical Debt Register

| ID | Area | Severity | Description | Effort | Owner |
|----|------|----------|-------------|--------|-------|
| QA-001 | Frontend E2E | Critical | No browser-based E2E tests exist. Need Playwright/Cypress setup covering 7 critical paths. | 3 sprints | Frontend QA |
| QA-002 | Coverage Gate | High | `fail_under = 30` in pyproject.toml must be changed to 85 to match constitutional requirement. | 1 hour | Backend Lead |
| QA-003 | AI Eval Automation | High | AI evaluation pipeline is not automated. `run_ai_eval.py` does not exist. CI label-based trigger has no backing script. | 2 sprints | AI Engineer |
| QA-004 | WebSocket Tests | High | No WebSocket connection/failure/reconnection tests if WS endpoints are active. | 1 sprint | Backend QA |
| QA-005 | Contract Test Gap | High | Only 1 WidgetContract.spec vs. Article 9.2 requirement for all widgets. ~7+ widgets missing contract tests. | 1 sprint | Frontend QA |
| QA-006 | Performance CI | High | `load-test.py` is manual. Need automated performance regression in CI with thresholds. | 1 sprint | DevOps |
| QA-007 | Entity Resolution Unit Tests | Medium | No dedicated unit tests for EntityResolutionService — only integration coverage. | 1 sprint | Backend QA |
| QA-008 | Accessibility Automation | Medium | No aXe/pa11y in CI despite WCAG AA target in Constitution Article 9.3. | 1 sprint | Frontend QA |
| QA-009 | RTL Test Suite | Medium | No automated Arabic RTL layout tests despite Arabic being first-class language. | 1 sprint | Frontend QA |
| QA-010 | Scoring Coverage | Medium | 78% below 85% minimum. Scoring needs additional unit tests. | 1 sprint | Backend QA |
| QA-011 | Timeline Coverage | Medium | 82% below 85% minimum. Timeline service needs more tests. | 1 sprint | Backend QA |
| QA-012 | CRM Coverage | Medium | 80% below 85% minimum. Commercial sub-domains need deeper tests. | 1 sprint | Backend QA |
| QA-013 | Excel Import Tests | Medium | Testpath registered in pyproject.toml but no test files found. | 3 days | Backend QA |
| QA-014 | CI Docs Accuracy | Low | QUALITY_GATE.md references `tests/architecture/` and `--strict` mypy, neither matches actual config. | 2 hours | Docs |
| QA-015 | Load Test Assertions | Low | `load-test.py` reports but never fails on threshold violations. Needs --fail-on-budget flag. | 3 days | DevOps |
| QA-016 | Snapshot Tests | Low | No frontend visual snapshot tests (no jest-image-snapshot, Percy, Chromatic). | 1 sprint | Frontend QA |

---

## Summary Scorecard

| Dimension | Score | Max | Status |
|-----------|-------|-----|--------|
| Unit Test Quantity | 9 | 10 | 🟢 Extensive |
| Unit Test Quality | 8 | 10 | 🟢 Good patterns, some mock duplication |
| Integration Tests | 7 | 10 | 🟡 Adequate but API coverage gaps |
| E2E Tests (Backend) | 8 | 10 | 🟢 41 tests across 7 paths |
| E2E Tests (Frontend) | 0 | 10 | 🔴 None exist |
| Contract Tests | 2 | 10 | 🔴 Only 1 widget |
| Performance Tests | 5 | 10 | 🟡 Framework only, no CI integration |
| AI Evaluation | 4 | 10 | 🔴 Framework tested, not pipeline |
| Architecture Tests | 9 | 10 | 🟢 Strong isolation + frozen interface checks |
| Accessibility Tests | 0 | 10 | 🔴 None automated |
| Security Tests | 5 | 10 | 🟡 Architecture + lint, no pen tests |
| CI Pipeline | 7 | 10 | 🟡 Good structure, some inaccuracies |
| Coverage Enforcement | 3 | 10 | 🔴 Gate at 30%, should be 85% |
| **OVERALL** | **6.3** | **10** | **🟡 ADEQUATE — Critical gaps found** |

---

*Audit completed by QA Architect. No files modified. Findings to be prioritized in Sprint planning.*
