# 164 — `domains/approval` and `domains/revenue/router.py` fully clean; `QuotaService.take_snapshot()`'s auto-generated period label used a non-existent strftime directive

**Read-only in scope of production/salesos_test.** One disposable `pgvector/pgvector:pg16` container migrated to head and destroyed after verification for the regression check; no production/`salesos_test` write.

## 1. Scope

Continuing the `domains/` subdirectory sweep (per report 155's plan): `domains/approval` (freshly proven live by report 189's app.state wiring fix, but its own Postgres repository's field-mapping correctness had not yet been separately verified) and `domains/revenue` (the largest unreviewed directory, 2,523 lines).

## 2. `domains/approval` — fully clean

Read `contracts/models.py`, `infrastructure/models.py`, `infrastructure/postgres_repository.py`, and the relevant parts of `engine/service.py` in full.

- `ApprovalRequestModel`'s 14 columns (including the `extra_metadata` Python-attribute / `"metadata"` column-name alias, matching the established convention seen elsewhere in this session — reports 169/184) match `ApprovalRequest`'s dataclass fields exactly.
- `_to_domain()`/`_from_domain()` round-trip every field correctly, including nested `ApprovalDecision` JSON serialization (`decided_at.isoformat()` ↔ `datetime.fromisoformat()`) and all 3 enum types (`ApprovalTargetType`/`ApprovalLevel`/`ApprovalStatus`).
- `save()`'s upsert loop correctly excludes `id` from the update; verified `created_at` is never touched by any of `approve()`/`reject()`/`escalate()`/`cancel()` (only `updated_at` is bumped), so the upsert's blanket column copy can't corrupt the original creation timestamp.
- `id` generation uses `uuid.uuid4()`, which fits the `String(36)` primary key column exactly.
- GUC pinning is delegated correctly: this repository never opens its own session (it's always constructed with an injected one), and report 148's fix already wires it through the established, previously-verified-correct `FactoryBoundRepository` → `tenant_scoped_session()` → `apply_tenant_guc()` pattern.

**No bug found.**

## 3. `domains/revenue/router.py` — fully clean, including a defensive pattern that could easily have been mistaken for a bug

Read all 550 lines. Every endpoint delegates to `ForecastService`/`QuotaService`/`TerritoryService` with request/response Pydantic schemas that match the underlying dataclasses field-for-field (`CommercialInputSchema` ↔ `CommercialInput`, `TimeSeriesPointSchema` ↔ `TimeSeriesDataPoint`, confirmed by direct comparison). No raw SQL, no direct `AsyncSession` manipulation, no date arithmetic of its own anywhere in the file.

Initial concern, resolved: the three service-factory functions (`_forecast_svc`/`_quota_svc`/`_territory_svc`) import `InMemoryForecastRepository`/`InMemoryQuotaRepository`/`InMemoryTerritoryRepository` at module scope, which looked at first glance like the router might be using ephemeral, per-process storage for a mounted, live feature (`/api/v1/revenue-planning/*`, confirmed mounted at `app/boot/routers.py:634-639`). Reading the full factory functions resolved this: each wraps a `try: from domains.commercial.infrastructure.postgres_repositories import Postgres<X>Repository ... except ImportError: return <X>Service(InMemory<X>Repository())` — since those Postgres repository classes genuinely exist (and were already verified field-mapping-clean for `Quota`/`Territory`/`Forecast` in report 169), the `ImportError` branch is unreachable in practice; the in-memory repos are a defensive fallback, not the live path. `get_db_session` (used throughout via `Depends`) delegates to `get_db`, the codebase's standard auto-tenant-GUC-pinning dependency — confirmed via direct read of `app/dependencies.py` — so by-ID lookups without an explicit `tenant_id` argument (`get_territory(territory_id)`, `get_quota(quota_id)`, etc.) are correctly tenant-isolated by RLS, not a missing-tenant-check gap.

**No bug found in the router itself.**

## 4. The bug — `QuotaService.take_snapshot()`

`period_label=period_label or datetime.now(timezone.utc).strftime("%Y-Q%q")` — Python's `strftime` has no `%q` (quarter) directive at all; there is no such format code in CPython's table. Confirmed the actual behavior differs by platform rather than being silently ignored everywhere:

- **Linux** (this application's deployment platform, confirmed via a fresh `python:3.12-slim` container): the invalid directive is **not substituted** — it's emitted **literally**, producing e.g. `"2026-Q%q"` instead of the intended `"2026-Q1"`. No exception, no warning — just wrong data silently persisted as the quota snapshot's `period_label`.
- **Windows** (this dev machine): raises `ValueError: Invalid format string` immediately — an unhandled crash.

Either way, `POST /api/v1/revenue-planning/quotas/snapshot` (`take_quota_snapshot`, whose `period_label` query parameter defaults to `""`) hits this exact path on every real call that doesn't explicitly supply a label — the normal/expected usage for an "auto-label the current quarter" feature.

## 5. Why existing tests never caught it

The only test referencing `take_snapshot()` (`tests/integration/test_quota_snapshots_rls.py`) always supplies an explicit `period_label` (`"2026-Q3"`), so the auto-generation fallback branch containing the bug was never exercised.

## 6. Fix

Computes the calendar quarter directly (`(now.month - 1) // 3 + 1`) instead of relying on a non-existent strftime directive, matching this file's existing `datetime.now(timezone.utc)` convention for timestamps (the label is a descriptive tag, not a business-logic-driving date field like a license expiry, so no UTC-vs-local calendar-boundary concern applies here, unlike reports 70/73/78/116/159's date-boundary bug class).

## 7. Verification — genuine red→green

New `tests/unit/test_revenue_quota_snapshot_period_label.py` (9 tests): parametrized over one representative month from each of the 4 quarters, monkeypatching `datetime.now()` to a fixed value and asserting the resulting label is a well-formed `YYYY-QN` string containing no literal `%q`; plus a regression guard that an explicitly-supplied label is still respected unchanged.

Scoped `git stash push -- salesos/backend/domains/revenue/quota/service.py` (reverting only the fix): all 8 auto-generation tests failed with the exact predicted `ValueError: Invalid format string` (this platform's failure mode); the explicit-label test correctly still passed, since that branch was never buggy. `git stash pop` restored the fix; all 9 re-confirmed PASS.

## 8. Regression

New test file: 9/9 PASS. Existing `tests/integration/test_quota_snapshots_rls.py` (the only pre-existing test touching this method): 1/1 PASS against a fresh, fully-migrated, restricted-role disposable container — no regression. Ruff (`--select E4,E7,E9,F,I`): the changed service file has exactly 1 finding (`I001`, an unrelated pre-existing import-sort issue, confirmed identical before/after via scoped stash), the new test file has 0. `python -m py_compile` and `git diff --check`: clean.

## 9. Scope and safety

- Two files touched: `salesos/backend/domains/revenue/quota/service.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_revenue_quota_snapshot_period_label.py` (new).
- Only a disposable, ephemeral `pgvector/pgvector:pg16` container was used for the regression check, migrated to head via Alembic and destroyed (`docker rm -f`) after. No production/`salesos_test` write.
- No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 10. Loop status

Continuing the standing 24-hour continuous-loop authorization. `domains/approval` and `domains/revenue` are now both accounted for in the `domains/` sweep (per report 155's plan — decision_center/feature_store/workflow/timeline/employee/notifications/commercial/search/analytics/scoring were already checked in reports 139-190; approval and revenue close out this list). Remaining `domains/` subdirectories not yet individually reviewed: `domains/ai`, `domains/copilot`, `domains/decision`, `domains/marketplace`, `domains/rag`, `domains/ubom` (the last explicitly marked DEPRECATED per this session's own header history — lower priority).
