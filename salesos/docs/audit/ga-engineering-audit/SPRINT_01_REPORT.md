# Sprint 01 Report — Foundation & Security Hardening

**Date:** 2026-07-30  
**Sprint:** 01 (Phase 0 — GA Foundation)  
**Audit classification:** production no-go (unchanged — sprint addresses P0 blockers only)  

---

## Summary

| Item | Count |
|------|-------|
| Stories planned | 5 |
| Stories completed | 5 |
| Files changed | 10 |
| Tests passed | 1665 |
| Tests failed (pre-existing infrastructure) | 8 |
| Test errors (pre-existing infra) | 46 |
| Frontend TS errors before | 6 |
| Frontend TS errors after | 0 |
| CSRF middleware tests before | 8 |
| CSRF middleware tests after | 8 (all pass) |

---

## Files Changed

| File | Change |
|------|--------|
| `salesos/backend/domains/decision_center/postgres_repo.py` | STORY-01-01: Replace JSONB path `decision_metadata["tenant_id"]` with direct column `DecisionModel.tenant_id` in `list_decisions`, `get_decision`, `get_feedback_by_type` |
| `salesos/backend/domains/workflow/service.py` | STORY-01-02: Add `validate_webhook_url` call in `create_webhook` and `update_webhook` to prevent SSRF |
| `salesos/backend/app/common/middleware.py` | STORY-01-03: Remove `api_key_authenticated` CSRF bypass (Prod-W5-001) |
| `salesos/backend/app/alembic/versions/0052_add_decision_center_tenant_id.py` | STORY-01-01/03-02: New migration adding `tenant_id` to `decision_center_decisions` and `decision_center_templates` |
| `salesos/backend/tests/unit/test_middleware.py` | STORY-01-03: Update CSRF test to assert 403 for API-key-authenticated requests |
| `salesos/frontend/next.config.js` | STORY-03-01: Remove `ignoreDuringBuilds: true` and `ignoreBuildErrors: true` |
| `salesos/frontend/packages/forms/src/index.tsx` | STORY-03-01: Remove `valueAsNumber` option from register call (2-arg → 1-arg) |
| `salesos/frontend/src/features/automation/workspace/automation/AutomationWorkspace.tsx` | STORY-03-01: Add explicit generic to `safeArray<Workflow>` and `safeArray<WorkflowExecution>` |
| `salesos/frontend/src/features/scoring/widgets/company-scoring/CompanyScoringView.tsx` | STORY-03-01: Replace `Recommendation.title`/`Recommendation.description` with `actionLabel`/`reason` |

---

## Story Details

### STORY-01-01: Decision Center Cross-Tenant IDOR

**Root cause:** `DecisionModel` had no `tenant_id` column. Queries in `PostgresRepository` filtered by `decision_metadata["tenant_id"].as_string()`, a JSONB path that does not enforce tenant isolation because `decision_metadata` is user-controlled input.

**Fix:**
1. Added `tenant_id` column to `DecisionModel` (SQLAlchemy ORM)
2. Updated `save_decision` to extract `tenant_id` from metadata
3. Updated `get_decision`, `list_decisions`, `get_feedback_by_type` in `postgres_repo.py` to use `DecisionModel.tenant_id == tenant_id` direct column filter
4. Created Alembic migration `0052` with data backfill from `decision_metadata->>'tenant_id'`

### STORY-01-02: Webhook SSRF

**Root cause:** `domains/workflow/service.py:create_webhook` stored user-supplied URL without validation, enabling SSRF to internal hosts.

**Fix:** Reused existing `validate_webhook_url(url, resolve_dns=True)` from `app/modules/webhooks/url_safety.py` in both `create_webhook` and `update_webhook`. This enforces: HTTPS-only, blocked hostnames (localhost, 169.254.x.x, 10.x.x.x, 172.16-31.x.x, 192.168.x.x, 127.x.x.x), DNS IP resolution check.

### STORY-01-03: CSRF Bypass via X-API-Key

**Root cause:** `CsrfEnforcementMiddleware.__call__` (line 416-418) skipped CSRF validation entirely when `request.state.api_key_authenticated` was `True`, allowing a browser with a stored API key to be used for CSRF attacks.

**Fix:** Removed the 3-line bypass. All state-changing requests must now present a valid `X-CSRF-Token` header matching the `csrf_token` cookie, regardless of authentication method.

### STORY-03-01: Frontend Build Failures

**Root cause:** `next.config.js` had `ignoreDuringBuilds: true` and `ignoreBuildErrors: true`, masking 6 TypeScript errors.

**Fixed errors:**
1. `packages/forms/src/index.tsx`: `register()` called with 2 args instead of 1 (`valueAsNumber` option removed)
2. `AutomationWorkspace.tsx:67`: `safeArray` returned `unknown[]` — added generic `safeArray<Workflow>()`
3. `AutomationWorkspace.tsx:87`: Same — added `safeArray<WorkflowExecution>()`
4. `CompanyScoringView.tsx:103-105`: Used `rec.title`/`rec.description` which don't exist on `Recommendation` type — replaced with `actionLabel`/`reason`

**Result:** `tsc --noEmit` passes clean. Suppression flags removed from `next.config.js`.

### STORY-03-02: Alembic Migration Drift

**Root cause:** Migration chain 0001→0051 was out of sync with models. Comprehensive audit revealed 13 drift items: 
- 12 tables defined in models with NO `create_table` in any migration
- 1 missing column (`tenant_id` on `decision_center_templates`)

**Fix (per scope):** Added `tenant_id` to `decision_center_templates` in migration 0052. Full table reconciliation deferred to Sprint 02 (see ADR-001: schema bootstrap path).

---

## Remaining Drift (deferred to Sprint 02)

These tables exist in models with no migration and must be created before GA:

- `webhook_endpoints`, `scoring_scorecards`, `revenue_analytics_snapshots`
- `analytics_report_shares`, `analytics_scheduled_reports`
- `admin_plans`, `admin_licenses`, `admin_invoices`, `admin_transactions`
- `admin_ai_costs`, `admin_jobs`, `admin_health_snapshots`, `decision_center_templates`

---

## Validation

| Check | Result | Evidence |
|-------|--------|----------|
| Backend unit tests | 1665 passed | `pytest tests/ -q --tb=short --ignore=tests/e2e --ignore=tests/test_integration.py --ignore=tests/integration` |
| CSRF middleware tests | 8 passed | `pytest tests/unit/test_middleware.py::TestCsrfMiddleware -x -q` |
| Frontend typecheck | 0 errors | `tsc --noEmit` (no output) |
| Alembic migration chain | Linear, head at 0052 | Created `0052_add_decision_center_tenant_id.py` → `down_revision = "0051"` |

---

## Risks & Dependencies

- 13 unmigrated tables remain (Sprint 02 scope)
- `salesos_test` database does not exist (pre-existing infra issue, blocks 54 integration tests)
- `Sprint-01.md` mentions CSRF bypass fix at `app/common/middleware.py:350-380` — actual location was `416-418`
- `Sprint-01.md` references `csrf.py` and `csrf_middleware.py` — neither file exists; CSRF logic lives entirely in `app/common/middleware.py`
