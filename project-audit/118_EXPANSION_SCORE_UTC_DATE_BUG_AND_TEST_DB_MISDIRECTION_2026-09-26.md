# 118 — ExpansionScoreComputer UTC/local date bug (5th occurrence) + a real test-invocation safety gap found and closed

**Read-only in scope of production/salesos_test.** All reproduction and verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container migrated to the current Alembic head, torn down after use. No write to `salesos_test` or production. No provider call.

## 1. The bug

`runtime/feature_store/features.py`'s `ExpansionScoreComputer.compute()` (already partially fixed in report 113 for wrong table/column names) had one remaining defect:

```python
days_to_renewal = (renewal_date - datetime.now(timezone.utc).date()).days
```

`renewal_date` comes from `licenses.expiry_date`, a plain `DATE` column with no time-of-day or timezone component. Comparing it against `datetime.now(timezone.utc).date()` — the UTC calendar date — rather than `date.today()` — the host's local calendar date — is the same bug class this codebase has now found and fixed **five** times (reports 70, 73, 78, and now here; a related instance was fixed proactively in `company/repositories.py` in report 70 without ever having a live caller). On a positive-UTC-offset host (this one included — Saudi Arabia is UTC+3), the UTC calendar date lags the local one for part of every day, silently shifting `days_to_renewal` by one and potentially flipping which of `ExpansionScoreComputer`'s renewal-proximity scoring tiers a license lands in.

### Fix

```python
days_to_renewal = (renewal_date - date.today()).days
```

`from datetime import date, datetime, timezone` (added `date` to the existing import). Repo-wide grep confirms `date.today()` is used exactly once in this file (the fixed line) and every other `datetime.now(timezone.utc)` call in the file is a legitimate elapsed-time comparison against a full timestamp column, not a date-only comparison — none of those needed to change.

### Live reproduction, then permanent regression test

First reproduced live against the host's actual current UTC/local offset (this session, 2026-09-26 local / 2026-09-25 UTC): reverted the fix, confirmed `days_to_renewal` was off by exactly one day from the correct value, restored the fix, reconfirmed correct.

That live reproduction depends on a coincidence (the host currently sitting in the lagging window) that won't hold on every future run, so a **deterministic** regression test was added instead: `tests/integration/test_feature_store_licenses_table_db.py::test_expansion_score_computer_uses_local_calendar_date_not_utc` monkeypatches the module's `date` name to a fake with `.today()` returning a fixed, arbitrary date (`2020-01-01`) far from the real UTC date, seeds a license expiring exactly 30 days after that fixed date, and asserts `days_to_renewal == 30`. Only an implementation that genuinely calls `date.today()` can land on exactly 30; a regression to the UTC-based line lands ~2,400 days off (confirmed below), not a subtle off-by-one that could be mistaken for coincidence.

**Genuine red→green, reproduced twice:**
- Fix in place: `days_to_renewal == 30` — PASS.
- Line reverted to `datetime.now(timezone.utc).date()`: `assert -2429 == 30` — FAILED exactly as predicted (the real UTC date is ~6.6 years after the fixed 2020-01-01 reference, so the wrong "today" produces a wildly negative days-to-renewal rather than a subtle off-by-one — a stronger, more discriminating proof than relying on a live 1-day timezone coincidence).
- Fix restored: PASS again.

## 2. A real test-invocation safety gap, found while setting up the reproduction

The first attempt at this reproduction (`export DATABASE_URL=... && python -m pytest tests/integration/test_feature_store_licenses_table_db.py`) did **not** fail safely — it connected somewhere unexpected and threw a `NotNullViolationError` on `companies.cr_number` that made no sense given the ephemeral container's real schema (that column has been nullable there since migration `p7q8r9s0t1u2`, 2026-09-11).

Root cause: `tests/integration/test_feature_store_licenses_table_db.py` (like every other `_db.py` integration test that imports `from app.database import async_session, engine` rather than opening its own `asyncpg.connect(...)`) is built from `settings.app_database_url` (`app/config.py`), **not** `settings.resolved_database_url`. `app_database_url`'s resolution order is:

1. `APP_DATABASE_URL_OVERRIDE` if set.
2. Otherwise, if `APP_POSTGRES_PASSWORD` is non-empty: build a URL from `APP_POSTGRES_USER`/`APP_POSTGRES_PASSWORD`/`POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB` — **ignoring `DATABASE_URL` entirely.**
3. Otherwise: fall back to `resolved_database_url` (which does honor `DATABASE_URL`).

This repo's checked-in `salesos/backend/.env` sets `APP_POSTGRES_PASSWORD=salesos_app_dev_password`, `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432`, `POSTGRES_DB=salesos` — so exporting only `DATABASE_URL` in the shell (a natural, and previously-used, pattern for pointing a one-off `pytest` run at a disposable container) is **silently ignored** for any test that goes through `app.database.engine`; it connects instead to `localhost:5432/salesos`, a **persistent local dev Postgres** (container `salesos-postgres-1`, running since 2026-08-22) — not `salesos_test`, not a disposable container.

**Verified this was a near-miss, not an incident:** `salesos-postgres-1`'s `salesos` database has `tenants=33`, `companies=5` (matching the long-standing local-dev baseline first documented in report 19, unrelated to this session) and an **empty** `alembic_version` table (never stamped to any migration — an old/unmanaged schema, which is exactly why the stale pre-`p7q8r9s0t1u2` NOT NULL constraint was still there and caused the INSERT to fail loudly). The failing INSERT rolled back before any `commit()` — confirmed via the SQL echo log ending in `ROLLBACK` with no prior `COMMIT` — so **zero rows were written** to this database by this session.

Checked whether this exposure is specific to this one file: grepped every `_db.py` integration test added or touched earlier in this session (`test_dec157_orphan_keep_rls_db.py`, `test_persistent_dlq_rls_and_interval_db.py`, `test_attribution_engine_injection_and_isolation_db.py`, and others) for a `current_database()` safety assertion — **none of them have one**. Many *older* integration tests in this repo (`test_account_evidence_persistence_db.py`, `test_fact_proposal_service_db.py`, `test_hitl_authenticated_seller_db.py`, etc.) do assert `current_database() == "salesos_test"` as their first line — but that literal check doesn't fit files designed to run against an arbitrarily-named disposable/ephemeral database rather than `salesos_test` specifically. This is a genuine, generalizable gap: **any `_db.py` integration test built on `app.database.engine`/`async_session`, run bare from a host shell with only `DATABASE_URL` exported, silently targets the persistent local dev database instead of the caller's intended target.**

### Fix applied here (scoped, not a blanket fix)

Added a `current_database() != "salesos"` refusal to this file's existing `autouse` `_dispose_engine_after_test` fixture, so this specific file can never again silently repeat the mistake:

```python
async with engine.connect() as conn:
    db_name = await conn.scalar(text("SELECT current_database()"))
assert db_name != "salesos", (
    f"REFUSING: connected to {db_name!r} — this is the persistent "
    "local dev database, not a disposable/test one. Set "
    'APP_POSTGRES_PASSWORD="" (or APP_DATABASE_URL_OVERRIDE) to point '
    "app.database.engine at an ephemeral container before running "
    "this file."
)
```

The correct invocation (used for every verification in this report) additionally exports `APP_POSTGRES_PASSWORD=""`, which forces `app_database_url` to fall through to `resolved_database_url` (honoring `DATABASE_URL`):

```bash
export DATABASE_URL="postgresql+asyncpg://salesos:pw@localhost:15433/scratch" \
       APP_POSTGRES_PASSWORD="" SECRET_KEY=... JWT_SECRET_KEY=... SALESOS_TESTING=1
```

**Not fixed here, documented instead:** rolling the same `current_database()` refusal out to every other `_db.py` file that shares this exposure is a separate, wider change that deserves its own deliberate pass (each file's "what's the right expected database name/shape" isn't uniform — some legitimately target `salesos_test` by literal name, others any freshly-migrated scratch DB) rather than a blanket, unreviewed mass-edit. Flagged as a candidate for a dedicated follow-up, consistent with this session's established practice of documenting genuinely ambiguous or wide-blast-radius gaps rather than unilaterally resolving them all at once (reports 59, 60, 84, 87).

## 3. Verification summary

- New test genuine red→green (see above): reverted → `assert -2429 == 30` (exact predicted failure mode) → restored → PASS.
- Full file: `3 passed` (2 pre-existing report-113 tests unaffected, 1 new).
- Regression: `tests/unit/test_feature_store.py` + `tests/unit/test_feature_store_cache.py` + this integration file: **35/35 PASS**.
- `ruff check --select E4,E7,E9,F,I` on both touched files: clean (3 pre-existing unrelated unused-import findings in `features.py` confirmed via `git diff` to predate this change — not touched).
- `python -m compileall`: clean on both files.
- `git diff --check`: clean (no trailing-whitespace/conflict-marker issues).

## 4. Scope and safety

- Files changed: `salesos/backend/runtime/feature_store/features.py` (2 lines), `salesos/backend/tests/integration/test_feature_store_licenses_table_db.py` (+78/-2, new deterministic test + safety fixture).
- Committed as `0618e473` on `fix/login-and-keys` with explicit paths (no `git add -A`).
- `salesos_test` and production: untouched. Only the disposable `sweep-pg` container (destroyed after use) and, transiently and without any write, the persistent local dev `salesos` database (read-only `current_database()` probe plus one rolled-back INSERT) were touched.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 5. Loop status

Continuing the standing "5 hours, all approvals" authorization from report 116/§157/§158. Next: continue the systematic sweep for further genuine, code-level defects (recurring bug classes, SQL correctness, GUC/RLS pinning, reachability of dead vs. live code), each with red→green proof, before considering any Phase 7 human-gate work (which remains explicitly human/PO-bound, not something this loop can close).
