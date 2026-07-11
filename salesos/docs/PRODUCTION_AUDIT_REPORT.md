# Production Audit Report — P6

> Date: 2026-07-11
> Auditor: opencode
> Scope: SalesOS v0.6.0 — Full Production Readiness Audit

---

## Executive Summary

| Area | Score | Verdict |
|------|-------|---------|
| Architecture Compliance | 8/10 | 🟡 Pass (minor issues) |
| Security | 6/10 | 🔴 Blocking |
| Dependencies | 8/10 | 🟢 Pass |
| Data Flow | 7/10 | 🟡 Pass (minor issues) |
| Decision Platform Adoption | 5/10 | 🟡 Partial |
| Documentation | 9/10 | 🟢 Pass |
| **Overall** | **7.2/10** | **🟡 Conditional Pass** |

---

## 1. Architecture Compliance

### 1.1 Container/View Pattern

**Finding**: All 37 widgets follow the Container/View pattern correctly.

| Feature Area | Widgets | Pattern Used |
|---|---|---|
| Dashboard | 6 (AIBrief, IntelligenceFeed, RecentActivity, DecisionQueue, MarketPulse, MissionCenter) | `createDashboardWidget` SDK |
| Company Intelligence | 10 (SmartTimeline, SignalsFeed, GoldenRecord, DecisionMakers, BuyingJourney, CompanyDNA, AIRecommendation, RelationshipGraph, DocumentIntelligence, GovernmentIntelligence) | `createWidget` from `@salesos/workspace` |
| Revenue Execution | 19 (NBA, Pipeline, Territory, Churn, Meeting, Email, Forecast, etc.) | `createWidget` from `@salesos/workspace` |
| Analytics | 1 (CommercialAnalytics) | `createWidget` from `@salesos/workspace` |

**Verdict**: ✅ **PASS** — All widgets use SDK, all have Container/View separation.

### 1.2 Cross-Domain Imports

**Finding**: No cross-domain imports detected. All internal imports stay within their own feature directory:
- `dashboard/` imports from `dashboard/_providers`, `dashboard/_registry`, `dashboard/_layout` — same domain
- `company-intelligence/` imports from `company-intelligence/_registry`, `company-intelligence/index` — same domain
- `revenue-execution/` workspace imports widgets from `revenue-execution/widgets/` — same domain

**Verdict**: ✅ **PASS** — No cross-domain violations.

### 1.3 Inline Scoring/Reasoning in Widgets

| Widget | Uses Decision Platform? | Details |
|--------|----------------------|---------|
| NextBestAction (NBA) | ✅ YES | `useDecision()` from DecisionProvider |
| Pipeline Intelligence | ✅ YES | `useDecisionScores()` from `lib/decisionQueries` |
| AIRecommendation | ⚠️ NO | Uses `useCompanyIntelligenceContext` directly |
| SmartTimeline | ⚠️ NO | Uses context directly |
| SignalsFeed | ⚠️ NO | Uses context directly |
| DecisionMakers | ⚠️ NO | Uses context directly |
| CompanyDNA | ⚠️ NO | Uses context directly |
| GoldenRecord | ⚠️ NO | Uses context directly |
| RelationshipGraph | ⚠️ NO | Uses context directly |
| BuyingJourney | ⚠️ NO | Uses context directly |
| DocumentIntelligence | ⚠️ NO | Uses context directly |
| GovernmentIntelligence | ⚠️ NO | Uses context directly |
| All Revenue Execution widgets | ⚠️ NO | Custom `useData` implementations |

**Verdict**: 🟡 **PASS WITH ISSUES** — Only 2/27 display widgets use Decision Platform. AIRecommendation widget displays inline `reasoning` data but it's sourced from context, not Decision Platform.

---

## 2. Security

### 2.1 Secrets in Code

**Finding**: No hardcoded production secrets found.

| File | Finding | Severity |
|------|---------|----------|
| `backend/app/config.py` | `openai_api_key: str = ""` (empty default, configured via env) | ✅ OK |
| `backend/app/tasks.py` | Uses `settings.openai_api_key`, `settings.meili_master_key` from env | ✅ OK |
| `backend/app/routers/copilot.py` | Uses `settings.openai_api_key` from env | ✅ OK |
| `backend/sdk/vector.py` | `api_key=self._api_key` — passed from settings | ✅ OK |
| `frontend/src/lib/api.ts` | Uses `process.env.NEXT_PUBLIC_API_URL` — proper | ✅ OK |
| Test files | Test passwords like `TestP@ss123` in identity tests | ⚠️ Low (test data) |

**Verdict**: ✅ **PASS**

### 2.2 Auth on All API Endpoints — **CRITICAL FAILURE**

**Finding**: 7 runtime routers are missing `Depends(get_current_tenant_id)` or any auth dependency entirely.

| Router | Endpoints | Missing Auth? |
|--------|-----------|---------------|
| `runtime/ux_runtime/router.py` | `/nav/sidebar`, `/nav/breadcrumbs`, `/layout/*`, `/commands/*`, `/notifications/*`, `/theme`, `/viewer/*` | ❌ **ALL endpoints unauthenticated** |
| `runtime/capability_framework/router.py` | `/capabilities`, `/capabilities/{id}`, `/capabilities/{id}/health`, `/capabilities/{id}/tabs`, `/nav/sidebar`, `/search/*` | ❌ **ALL endpoints unauthenticated** |
| `runtime/action_engine/router.py` | `/actions`, `/actions/{id}`, `/actions/execute`, `/actions/executions/{id}` | ❌ **ALL endpoints unauthenticated** (execute action included!) |
| `runtime/extension_api/router.py` | `/hooks`, `/hooks/{hook_name}` | ❌ **ALL endpoints unauthenticated** |
| `runtime/form_engine/router.py` | `/generate`, `/{form_id}/validate`, `/{form_id}` | ❌ **ALL endpoints unauthenticated** |
| `runtime/plugin_sandbox/router.py` | `/plugins`, `/plugins/{id}`, `/plugins/install`, `/{id}/enable`, `/{id}/disable`, `/{id}` delete | ❌ **ALL endpoints unauthenticated** |
| `runtime/ui_schema_engine/router.py` | `/viewer/{entity_type}/{entity_id}` | ❌ **Unauthenticated** |

**Verdict**: ❌ **FAIL** — **7 routers with no auth whatsoever. Release blocked.**

### 2.3 Hardcoded Configs

**Finding**: The codebase was previously remediated for hardcoded configs (TD-005 resolved in v0.5). Current state:

- `backend/app/config.py` uses `pydantic-settings` — ✅ Proper
- `frontend/src/lib/api.ts` uses `NEXT_PUBLIC_API_URL` env — ✅ Proper
- `backend/app/main.py` has `os.environ.get("SALESOS_TESTING")` — ⚠️ Low (testing flag)

**Verdict**: ✅ **PASS**

---

## 3. Dependencies

### 3.1 console.log / debugger / print

| Area | Finding | Severity |
|------|---------|----------|
| Frontend `src/` | No `console.log` or `debugger` found | ✅ Clean |
| Backend `app/` | No `print()` in production code | ✅ Clean |
| Backend scripts (`benchmark/`, `demo/`, `pipeline/`) | Multiple `print()` statements in CLI tools | ⚠️ Low (scripts only) |

**Verdict**: ✅ **PASS**

### 3.2 Outdated Dependencies

| File | Notable Versions | Status |
|------|-----------------|--------|
| `frontend/package.json` | Next.js 15, React 19, TanStack Query 5.60, Axios 1.7 | ✅ Current |
| `backend/pyproject.toml` | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2.7 | ✅ Current |

**Verdict**: ✅ **PASS**

---

## 4. Data Flow

### 4.1 localStorage Usage

| File | Usage | Severity |
|------|-------|----------|
| `lib/api.ts` | Stores `access_token`, `refresh_token` for auth | ⚠️ Standard pattern (acceptable) |
| `lib/hooks/mutationHooks.ts` | Stores tokens after login/register | ⚠️ Standard pattern |
| `lib/hooks/useTenant.ts` | Reads `tenant_id`, `access_token` | ⚠️ Standard pattern |
| `application/revenue-execution/opportunity.store.ts` | Stores/reads opportunities in localStorage | ❌ **Not ideal — production data in localStorage** |
| `application/revenue-execution/task.store.ts` | Stores/reads tasks in localStorage | ❌ **Not ideal — production data in localStorage** |

**Verdict**: 🟡 **PASS WITH ISSUES** — Auth token storage is standard, but opportunity and task stores persist business data to localStorage.

### 4.2 API Client Usage

**Finding**: All API calls in the frontend go through the centralized `api` instance from `lib/api.ts`. No direct `fetch()` or alternate axios instances found in feature code.

**Verdict**: ✅ **PASS**

### 4.3 React Query Patterns

**Finding**: React Query hooks are defined in `lib/hooks/*` (opportunityQueries, companyQueries, searchQueries, etc.) but **features/widgets sometimes bypass them**:

| Widget | Data Fetching Method |
|--------|---------------------|
| PipelineIntelligence | `useOpportunities()` + `useDecisionScores()` — ✅ React Query |
| Dashboard widgets | Custom `useData()` with direct API calls — ⚠️ Mixed |
| NBA Container | Uses `decision.evaluate()` directly with `useState` + `useEffect` — ⚠️ No React Query caching |
| Company Intelligence widgets | Use context provider — ⚠️ No React Query |

**Verdict**: 🟡 **PASS WITH ISSUES** — React Query exists but is inconsistently adopted across widgets.

---

## 5. Decision Platform Adoption

### 5.1 Decision Platform Usage Count

| Widget Category | Total Widgets | Using Decision Platform | Adoption Rate |
|----------------|--------------|----------------------|---------------|
| Dashboard | 6 | 0 | 0% |
| Company Intelligence | 10 | 0 | 0% |
| Revenue Execution | 19 | 2 (NBA, Pipeline) | 10.5% |
| Analytics | 1 | 0 | 0% |
| **Total** | **36** | **2** | **5.6%** |

**Finding**: Decision Platform (`@salesos/decision-platform`) is imported only in `DecisionProvider.tsx`. The `useDecision()` hook is only available within the `DecisionProvider` context which is scoped to `revenue-execution` feature. Other features (dashboard, company-intelligence) do not have access to it.

### 5.2 DecisionProvider Availability

| Context | DecisionProvider Available? |
|---------|---------------------------|
| Dashboard | ❌ Not wrapped |
| Company Intelligence | ❌ Not wrapped |
| Revenue Execution | ✅ Available |

**Verdict**: 🟡 **PASS WITH ISSUES** — Decision Platform is functional in revenue-execution but not extended to other features. Adoption is at 5.6%.

---

## 6. Documentation Completeness

| Document | Status | Notes |
|----------|--------|-------|
| `README.md` | ✅ Complete | Updated for v0.6, covers architecture, quick start, tech stack |
| `CHANGELOG.md` | ✅ Complete | v0.6.0 changelog with detailed Wave 2 entries |
| `RELEASE_GATES.md` | ✅ Complete | 8 gates defined with automation spec |
| `PERFORMANCE_BASELINE.md` | ✅ Complete | Latency baselines, infrastructure metrics |
| `docs/wave-2/*` | ✅ Complete | 11 architectural documents for Wave 2 |
| API Reference | ✅ Available at `docs/wave-2/11-API_REFERENCE.md` and FastAPI `/docs` |

**Verdict**: ✅ **PASS** — Documentation is comprehensive and up to date.

---

## 7. Release Gate Assessment

| Gate | Status | Reason |
|------|--------|--------|
| **Gate 1 — Security** | **❌ FAIL** | 7 runtime routers have no authentication (critical) |
| **Gate 2 — Architecture** | ✅ PASS | No cross-domain imports, clean Container/View pattern |
| **Gate 3 — Performance** | ✅ PASS | Baselines within budget (see PERFORMANCE_BASELINE.md) |
| **Gate 4 — Testing** | ❌ FAIL | Coverage: 58% unit (target 85%), 45% integration (target 70%) |
| **Gate 5 — CI/CD** | ✅ PASS | Docker builds, migrations, ruff/mypy/pytest configured |
| **Gate 6 — Infrastructure** | ⚠️ Conditional | Health endpoints exist, resource limits not verified |
| **Gate 7 — Documentation** | ✅ PASS | README, CHANGELOG, API docs all updated |
| **Gate 8 — Final Decision** | **❌ BLOCKED** | Gates 1 and 4 must pass first |

---

## 8. Detailed Findings

### 🔴 Critical

| ID | Area | Finding | Location |
|----|------|---------|----------|
| P6-C01 | Security | 7 runtime routers have zero authentication: UX Runtime, Capability Framework, Action Engine, Extension API, Form Engine, Plugin Sandbox, UI Schema Engine | `backend/runtime/*/router.py` |
| P6-C02 | Security | Action Engine `/execute` endpoint is unauthenticated — allows arbitrary action execution | `backend/runtime/action_engine/router.py:37` |
| P6-C03 | Testing | Unit test coverage at 58% (target 85%) | Dashboard |
| P6-C04 | Testing | Integration test coverage at 45% (target 70%) | Dashboard |

### 🟡 High

| ID | Area | Finding | Location |
|----|------|---------|----------|
| P6-H01 | Data Flow | Business data persisted to localStorage (opportunities, tasks) | `application/revenue-execution/*.store.ts` |
| P6-H02 | Decision Platform | Only 5.6% of widgets (2/36) use Decision Platform | Various widgets |
| P6-H03 | Decision Platform | DecisionProvider not available in Dashboard or Company Intelligence contexts | `features/revenue-execution/_providers/` |
| P6-H04 | Architecture | Company Intelligence widgets use context directly instead of Decision Platform | `features/company-intelligence/widgets/*` |

### ⚠️ Medium

| ID | Area | Finding | Location |
|----|------|---------|----------|
| P6-M01 | Data Flow | NBA Container uses `useState`+`useEffect` instead of React Query for data fetching | `NBAContainer.tsx:71-99` |
| P6-M02 | Security | CSRF protection status not verified | Cross-cutting |
| P6-M03 | Security | Rate limiting not verified on all endpoints | Cross-cutting |
| P6-M04 | Infrastructure | No memory limits defined in dev docker-compose | `docker-compose.yml` |
| P6-M05 | Data Flow | AIRecommendation view displays `reasoning` inline without Decision Platform | `AIRecommendationView.tsx:24` |

### ✅ Low

| ID | Area | Finding | Location |
|----|------|---------|----------|
| P6-L01 | Dependencies | Test files contain test passwords | `backend/app/modules/identity/tests/` |
| P6-L02 | Dependencies | `print()` statements in CLI/script files | `backend/benchmark/`, `demo/`, `pipeline/` |
| P6-L03 | Config | `os.environ.get("SALESOS_TESTING")` in production startup | `backend/app/main.py:48` |

---

## 9. Recommendations

### Must Fix Before Release

1. **Add authentication to all runtime routers** — Every `@router.*` in `runtime/` must include `Depends(get_current_tenant_id)` at minimum. Focus on: UX Runtime, Capability Framework, Action Engine, Extension API, Form Engine, Plugin Sandbox, UI Schema Engine.
2. **Fix Action Engine `/execute`** — This endpoint can execute arbitrary actions without auth. Critical security hole.
3. **Improve test coverage** — Unit tests at 58% need to reach 85%; integration at 45% needs 70%.

### Should Fix This Sprint

4. **Extend DecisionProvider** to Dashboard and Company Intelligence contexts so all widgets can use Decision Platform.
5. **Replace localStorage stores** with API-backed persistence for opportunities and tasks.
6. **Migrate widget data fetching** to React Query patterns consistently across all widgets.

### Technical Debt to Track

7. CSRF protection verification (not audited)
8. Rate limiting completeness audit
9. Infrastructure resource limits
10. Docker Desktop → production Linux deployment validation

---

## Appendix: Files Audited

- 37 widget Container files
- 36 widget View files
- 17 API router files (backend)
- 7 runtime router files (backend)
- 14 query hook files (frontend)
- 12 feature provider/registry files
- All configuration files (package.json, pyproject.toml)
- Documentation files (README, CHANGELOG, RELEASE_GATES, PERFORMANCE_BASELINE)
