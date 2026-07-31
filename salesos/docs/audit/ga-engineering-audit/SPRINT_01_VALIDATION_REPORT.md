# Sprint 01 Validation Report

Date: 2026-07-30  
Scope: Sprint 01 only. Sprint 02 was not started.

## Independent Validation Findings Addressed

| Finding | Status | Resolution |
|---|---:|---|
| Workflow webhook tests used HTTP fixtures | Fixed | Updated service/router webhook fixtures to resolvable HTTPS URLs using `https://example.com/...` |
| `domains/workflow/tests` not discovered by CI | Fixed | Added `domains/workflow/tests` to `tool.pytest.ini_options.testpaths` |
| `domains/decision_center/tests` not evaluated | Fixed | Added `domains/decision_center/tests` to `testpaths`, ran tests, fixed Sprint 01 template tenant signature drift |
| Missing IDOR adversarial regression | Fixed | Expanded `test_cross_tenant_idor_blocked` to cover direct access, audit, feedback, listing, and aggregation isolation |
| Missing SSRF adversarial regression | Fixed | Added create/update webhook SSRF tests for HTTP, localhost, private IPs, loopback hostnames, and valid HTTPS pass-through |
| Workflow router tests failed auth in CI unit context | Fixed | Router test fixture now overrides generated RBAC dependency closures, avoiding real JWT/DB auth in unit tests |

## Files Updated In This Validation Pass

| File | Change |
|---|---|
| `salesos/backend/pyproject.toml` | Added `domains/decision_center/tests` and `domains/workflow/tests` to pytest `testpaths` |
| `salesos/backend/domains/workflow/tests/test_router.py` | Updated webhook fixtures to HTTPS and bypassed generated RBAC closures in the unit app fixture |
| `salesos/backend/domains/workflow/tests/test_phase13.py` | Updated webhook service fixtures to HTTPS and added SSRF adversarial tests for `create_webhook` and `update_webhook` |
| `salesos/backend/domains/decision_center/tests/test_decision_center.py` | Fixed template tests for required tenant context and expanded IDOR regression coverage |

## Executed Test Counts

| Command | Result |
|---|---|
| `docker compose exec backend python -m pytest domains/decision_center/tests/ -x -q --tb=short` | 50 passed |
| `docker compose exec backend python -m pytest domains/workflow/tests/ -x -q --tb=short` | 143 passed |
| `docker compose exec backend python -m pytest tests/unit/test_middleware.py::TestCsrfMiddleware -x -q --tb=short` | 8 passed |
| `npm.cmd run typecheck` in `salesos/frontend` | 0 TypeScript errors |
| `docker compose exec backend python -m pytest tests/ domains/decision_center/tests/ domains/workflow/tests/ -q --tb=short --ignore=tests/e2e --ignore=tests/test_integration.py --ignore=tests/integration` | 1817 passed, 7 failed, 4 skipped, 2 errors |
| `docker compose exec backend python -m pytest tests/ domains/decision_center/tests/ domains/workflow/tests/ -q --tb=short --ignore=tests/e2e` | 1856 passed, 8 failed, 4 skipped, 66 errors |

## Coverage Delta

Test discovery now includes two previously undiscovered Sprint 01-relevant domain suites:

| Directory | Newly Discovered Tests | Current Result |
|---|---:|---|
| `domains/decision_center/tests` | 50 | 50 passed |
| `domains/workflow/tests` | 143 | 143 passed |
| Total | 193 | 193 passed |

Security regression coverage added or expanded:

| Risk | Coverage |
|---|---|
| Decision Center IDOR | Cross-tenant direct read, audit read, feedback read/write, audit write, listing, and aggregation all denied |
| Workflow webhook SSRF | `create_webhook` rejects HTTP, localhost, private IPs, loopback DNS; `update_webhook` rejects HTTP and localhost; valid HTTPS passes |
| CSRF API key bypass | Authenticated API-key requests still require CSRF token |

## Remaining Failures

The complete suite still has failures. They are not caused by Sprint 01 changes and were classified as pre-existing or infrastructure-bound.

### Non-Integration Failures

| Test | Failure | Classification |
|---|---|---|
| `tests/test_architecture.py::test_domain_does_not_import_ui[domain_dir6]` | `domains/employee/*` imports FastAPI | Pre-existing architecture boundary issue unrelated to Sprint 01 |
| `tests/unit/test_authorization.py::TestRoleHierarchy::test_user_permissions_correct` | User role currently has `company:create` | Pre-existing authorization policy/test mismatch unrelated to Sprint 01 |
| `tests/unit/test_authorization.py::TestPermissionEnforcer::test_user_cannot_create_company` | Expected deny, policy allows | Pre-existing authorization policy/test mismatch unrelated to Sprint 01 |
| `tests/unit/test_contact_service.py::TestContactCreate::test_create_contact_basic` | `company_id` is required | Pre-existing contact model/test mismatch unrelated to Sprint 01 |
| `tests/unit/test_contact_service.py::TestContactCreate::test_create_contact_optional_fields_none` | `company_id` is required | Pre-existing contact model/test mismatch unrelated to Sprint 01 |
| `tests/unit/test_employee_360_service.py::TestGenerateCoachActions::test_healthy_pipeline_generates_on_track` | Expected `on_track`, got `low_activity` | Pre-existing employee 360 logic/test mismatch unrelated to Sprint 01 |
| `tests/unit/test_employee_360_service.py::TestGetProfile::test_get_profile_found` | MagicMock `department` fails Pydantic string validation | Pre-existing test fixture issue unrelated to Sprint 01 |

### Integration/Infrastructure Failures

| Area | Failure | Classification |
|---|---|---|
| `tests/integration/test_kafka_live.py::test_kafka_bus_outbox_fallback_on_error` | Expected one outbox fallback event, got zero | Pre-existing live Kafka integration behavior issue unrelated to Sprint 01 |
| `tests/integration/*`, `tests/test_integration.py`, `tests/test_health.py` | `asyncpg.exceptions.InvalidCatalogNameError: database "salesos_test" does not exist` and related DB setup failures | Pre-existing test database infrastructure issue |

## Sprint 01 Acceptance Status

| Acceptance Item | Status |
|---|---:|
| Workflow webhook tests use HTTPS fixtures | Satisfied |
| Workflow tests execute in CI discovery | Satisfied |
| Decision Center tests evaluated | Satisfied |
| Sprint 01-introduced Decision Center failures fixed | Satisfied |
| IDOR adversarial regression exists and passes | Satisfied |
| SSRF adversarial regressions for create/update exist and pass | Satisfied |
| Frontend typecheck clean with suppressions removed | Satisfied |
| Complete suite re-run with new directories | Satisfied, with unrelated/pre-existing failures documented |

## Final Recommendation

Sprint 01 acceptance criteria are satisfied for the Sprint 01 scope.

Recommendation: do not start Sprint 02 until the owner accepts the documented unrelated failures as out of Sprint 01 scope or separately assigns them. Current status remains production no-go per GA audit; this validation only closes Sprint 01 security/build acceptance criteria.
