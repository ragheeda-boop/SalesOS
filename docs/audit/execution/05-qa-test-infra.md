# QA & Test Infrastructure Fixes — Execution Summary

> **Date**: 2026-07-13
> **Phase**: Sprint 8 GA Production Launch — QA Hardening
> **Executor**: QA Engineering Agent

---

## 1. Playwright E2E Setup

**File**: `salesos/frontend/playwright.config.ts`

Created comprehensive Playwright configuration for frontend E2E testing:

| Configuration | Value |
|---------------|-------|
| Test directory | `e2e/` |
| Base URL | `http://localhost:3000` |
| Browsers | Chromium, Firefox, WebKit, Mobile Safari |
| Parallelism | Fully parallel (sequential in CI) |
| Retries | 2 in CI, 0 locally |
| Screenshot on failure | Enabled |
| Trace on failure | Enabled (first retry) |
| Video on failure | Retained |
| Web server | Auto-starts `npm run dev` |

**Package.json updates**:
- Added `@playwright/test: ^1.49` as devDependency
- Added npm scripts: `test:e2e`, `test:e2e:ui`, `test:e2e:chromium`

**Global setup/teardown**: `e2e/global-setup.ts` and `e2e/global-teardown.ts`

---

## 2. Critical Path E2E Tests

Created 10 E2E test suites in `salesos/frontend/e2e/` covering all critical user journeys:

| # | File | Critical Path | Tests |
|---|------|--------------|-------|
| 1 | `01-login.spec.ts` | Login flow (success + failure) | 5 |
| 2 | `02-dashboard.spec.ts` | Dashboard loads with widgets | 4 |
| 3 | `03-search.spec.ts` | Search company flow | 4 |
| 4 | `04-company-detail.spec.ts` | Company detail page | 4 |
| 5 | `05-create-opportunity.spec.ts` | Create opportunity | 4 |
| 6 | `06-pipeline-kanban.spec.ts` | Pipeline kanban drag-drop | 4 |
| 7 | `07-revenue-dashboard.spec.ts` | Revenue dashboard | 4 |
| 8 | `08-admin-panel.spec.ts` | Admin panel navigation | 4 |
| 9 | `09-rtl-layout.spec.ts` | RTL layout rendering (dir="rtl") | 5 |
| 10 | `10-mobile-responsive.spec.ts` | Mobile responsive (375px viewport) | 5 |

**Total**: 43 E2E tests across 10 critical paths

### Key patterns used:
- `beforeEach` login flow with env-configurable credentials (`E2E_USER_EMAIL`, `E2E_USER_PASSWORD`)
- Resilient selectors using `getByRole`, `getByLabel`, `getByText` with regex fallbacks for bilingual UI
- RTL validation via `html[dir="rtl"]` attribute check
- Mobile viewport at 375x812 (iPhone 14)
- Touch target accessibility checks (minimum bounding box height)

---

## 3. Coverage Enforcement

### pyproject.toml

Added per-domain coverage minimums documentation:

| Domain | Minimum Coverage |
|--------|-----------------|
| Identity | 88% |
| Company | 80% |
| Search | 93% |
| Timeline | 82% |
| CRM | 80% |
| Scoring | 78% |
| AI | 92% |
| Workflow | 95% |

### check-coverage.ps1

**File**: `salesos/scripts/check-coverage.ps1`

CI-friendly PowerShell script that:
- Runs `pytest --cov` per domain against each threshold
- Supports `-Domain identity,search` for targeted checks
- Supports `-SkipE2E` to exclude E2E tests in CI
- Supports `-Json` for machine-readable output
- Returns non-zero exit code on failure
- Color-coded pass/fail output

Usage:
```powershell
.\scripts\check-coverage.ps1
.\scripts\check-coverage.ps1 -Domain identity,search
.\scripts\check-coverage.ps1 -SkipE2E -Json
```

---

## 4. Search Benchmarks — Real PostgreSQL Queries

**File**: `salesos/backend/benchmarks/search_benchmark.py`

Converted all 4 benchmark functions from simulated latency to real PostgreSQL queries:

### Before (simulated):
- Used `_simulate_search_latency()` with logarithmic scaling
- No database connection
- Zero test data seeding

### After (real):
- **Full-text search**: Uses `PostgresSearchRepository.search_raw()` with `plainto_tsquery('arabic', :q)` against `companies.search_vector`
- **Semantic search**: Combines full-text + embedding overhead (reserved for pgvector integration)
- **Hybrid search**: Runs multi-term tsquery against real data
- **Index creation**: Seeds test data and measures actual insertion time

### Architecture:
- Graceful fallback: if no database is available, simulates latency with documented overheads
- Connection probing via `SELECT 1` on startup
- Test data seeding via `_seed_test_data()` — creates companies with `to_tsvector('arabic', ...)` 
- All results tagged with `real_db: true/false` in metadata
- Reports actual p50/p95/p99 from `time.perf_counter()` measurements (not simulation)

### Budget thresholds (unchanged):
| Benchmark | Records | p95 Budget |
|-----------|---------|-----------|
| fulltext_search | 100/1000/10000 | 200ms / 200ms / 500ms |
| semantic_search | 100/1000/10000 | 500ms / 500ms / 1000ms |
| hybrid_search | 100/1000/10000 | 800ms / 800ms / 2000ms |
| index_creation | 100/1000/10000 | 5s / 5s / 30s |

---

## 5. Widget Contract Test Template

**File**: `salesos/frontend/src/features/dashboard/sdk/contract-test-utils.ts`

Reusable contract test generator that other widgets can use.

### What it provides:
```typescript
import { createWidgetContractTest } from '../sdk/contract-test-utils'

createWidgetContractTest<MyWidgetData>({
  name: 'MyWidget',
  metadata: { id: 'my-widget', title: 'My Widget', ... },
  render: ({ data }) => <MyWidgetView {...data} />,
  defaultData: myDefaultData,
  customTests: ({ mock, renderWidget, screen, fireEvent }) => {
    // Widget-specific tests here
  },
})
```

### Built-in contract tests (automatic):
1. **Rendering** — title, children in ready state, fallback on permission denied, feature flag disabled
2. **Widget States** — loading/ready/degraded/error states, degraded overlay behavior
3. **Permissions** — renders when granted, hides when denied
4. **Feature Flags** — renders when enabled, hides when disabled
5. **Accessibility** — refresh button aria-label, loading role="status", error role="alert", retry button
6. **Interaction** — retry calls refetch, refresh calls refetch

### Re-exports all SDK testing utilities:
- `describeWidgetContract` — for alternative usage
- `renderWidget` — test renderer with mocked useData
- `createMockWidget` — factory for loading/ready/degraded/error states
- `mockPermissionsAll/mockPermissionsNone` — permission mocks
- `mockFeatureFlagsAll/mockFeatureFlagsNone` — feature flag mocks

---

## Changes Summary

| Task | Files Created | Files Modified | Status |
|------|-------------|---------------|--------|
| 1. Playwright E2E Setup | `playwright.config.ts`, `e2e/global-setup.ts`, `e2e/global-teardown.ts` | `package.json` | Done |
| 2. Critical Path E2E Tests | `e2e/01-login.spec.ts` through `e2e/10-mobile-responsive.spec.ts` (10 files) | — | Done |
| 3. Coverage Enforcement | `scripts/check-coverage.ps1` | `pyproject.toml` | Done |
| 4. Search Benchmarks | — | `benchmarks/search_benchmark.py` (rewritten) | Done |
| 5. Widget Contract Test Template | `sdk/contract-test-utils.ts` | — | Done |

---

## Next Steps

1. Run `npx playwright install` to install browser binaries
2. Run `npm run test:e2e` to verify E2E tests against a running dev server
3. Run `.\scripts\check-coverage.ps1` to validate per-domain coverage
4. Verify benchmarks with `python -m benchmarks.search_benchmark` against a running PostgreSQL
5. Use `createWidgetContractTest()` in new widget test files
