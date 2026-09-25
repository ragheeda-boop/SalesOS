# 70 — Stale `ALL_TENANT_TABLES` Count Fix + Real UTC/Local Date-Boundary Bug (2026-09-24)

> **Scope:** Closes the last known pre-existing, unrelated unit-test failure
> flagged across reports 68/69 (a stale hardcoded count assertion), and — in
> the course of that work, when the session's date rolled over live — finds
> and fixes a genuine, previously-undetected UTC/local calendar-date
> boundary bug affecting NBA task due-dates and license-expiry lookups.
> Verified on fresh ephemeral Postgres containers; `salesos_test` was never
> touched.

## 1. Stale count assertion (mechanical, zero risk)

`tests/unit/test_db05_slice4_deferred_8_rls_authority.py::test_deferred_8_not_folded_into_category_a_47`
asserted `len(ALL_TENANT_TABLES) == 55`. Confirmed the real, current count is
**66** — 11 more Category A tables were added across many sessions after the
last legitimate bump (51→55, the "four governed fact-ledger tables"), and
this one assertion was never updated. Verified before touching anything:

- `scripts/generate_rls_policies.py` and `app/alembic/lib/rls.py`'s
  duplicated `ALL_TENANT_TABLES` lists are identical (66 entries, no drift
  between the two canonical/duplicate copies).
- No duplicate table names in the list (66 unique).
- On a fresh ephemeral `pgvector/pgvector:pg16` migrated to head
  (`e1d1c1225d00`), **all 66** tables resolved to a real table with
  `relrowsecurity=true`, `relforcerowsecurity=true`, and exactly 1
  `tenant_isolation_<table>` policy — zero anomalies.

Fixed the assertion to `66`, with a comment naming the concrete tables added
since the last bump instead of leaving a vague "still 55" note that would
just go stale again. All 4 tests in the file now pass.

## 2. Real bug found: UTC-vs-local calendar-date boundary

While running the full local `tests/unit/` suite to confirm the fix above
was the only failure, the session's tracked date rolled over
(2026-09-23 → 2026-09-24) mid-run and a **different**, previously-passing
test failed live:
`tests/unit/test_signal_action_execution.py::test_execute_creates_tenant_linked_crm_task_and_is_idempotent`,
with `task["due_date"] == date.today()` failing:
`datetime.date(2026, 9, 23) == datetime.date(2026, 9, 24)`.

Root cause: `app/modules/signal_actions/actions.py`'s `ActionExecutor.execute()`
computed an NBA-derived CRM task's `due_date` via
`datetime.now(UTC).date() + timedelta(days=due_days)`. For `due_days=0`
("immediate"/"today" urgency — exactly the case that maps to `priority="high"`
and is meant to mean "due today"), this reduces to the raw UTC calendar
date. On a host in a positive-UTC-offset timezone, the real local wall clock
was consistently a day ahead of the process's UTC-computed date at the
moment of the run (confirmed by two consecutive re-runs a minute apart both
showing the identical UTC-vs-local mismatch — not a race, a real,
reproducible offset) — this is precisely the class of bug that manifests
every night during the local-midnight-to-UTC-offset window (e.g., roughly
00:00–03:00 in a UTC+3 deployment like Saudi Arabia): a task genuinely
created "due today" from the seller's perspective gets silently persisted
with **yesterday's** date, which any downstream "is this overdue" check
would then treat as already late.

Grep confirmed the rest of the codebase's dominant convention for
date-only "today" is `date.today()` (10 occurrences: contract/quote expiry,
deal close dates, cost-tracker billing periods) — `datetime.now(UTC).date()`
was a 2-call-site outlier, not the established pattern.

### Fix

- `app/modules/signal_actions/actions.py`: `due_date` now computed via
  `date.today() + timedelta(days=due_days)`; import simplified from
  `from datetime import UTC, datetime, timedelta` to
  `from datetime import date, timedelta` (both were the only usages in the
  file).
- `app/modules/company/repositories.py`'s `LicenseRepository.find_expiring()`:
  same bug, same fix (`date.today()` instead of `datetime.now(UTC).date()`
  for both the lower and upper bound of the expiry window). Removed the
  now-unused module-level `from datetime import UTC` import. This method has
  **zero production callers** today (confirmed via repo-wide grep) — fixed
  proactively before any caller is added, since it shares the exact same
  bug shape as the signal_actions case and was otherwise going to reproduce
  the identical class of defect the moment something calls it.

### Verification

- **Genuine red→green, live-reproduced**: reverted `actions.py`'s fix,
  re-ran `test_signal_action_execution.py` — failed with the exact same
  `2026-09-23 == 2026-09-24` mismatch (this machine's real timezone offset
  reproducing the bug on demand, not a synthetic scenario). Restored the
  fix, re-ran — 4/4 PASS.
- `tests/unit/test_signal_actions.py`, `test_signal_nba.py`,
  `test_signal_priority.py`, `test_signal_qualification.py`,
  `test_signal_action_execution.py`, `test_hitl_authenticated_seller.py`:
  **117/117 PASS** (no regression from the `actions.py` change).
- New `tests/integration/test_license_find_expiring_date_boundary_db.py`
  (3 tests, no prior coverage existed for `find_expiring()` at all): seeds a
  license expiring exactly today, one that expired yesterday, and one
  outside the 30-day window, on a fresh ephemeral Postgres migrated to
  head, through the restricted `salesos_app` role — **3/3 PASS**. Re-ran
  alongside the adjacent `test_feature_store_licenses_table_db.py`
  (which also reads the `licenses` table) — **5/5 PASS**, no interference.
  (This container's own clock is UTC, so it does not itself reproduce the
  offset — the fix's correctness there rests on the identical code shape
  already proven red→green in `actions.py`, plus the logic-correctness
  proof this new test provides.)
- Repo-wide grep after both fixes: **zero** remaining occurrences of
  `datetime.now(UTC).date()` anywhere in `app/`, `runtime/`, `domains/`,
  `intelligence/`, `sdk/` (only this report's and the code's own explanatory
  comments mention the string).
- **Full local `tests/unit/` suite: 3766 passed, 0 failed** (4 skipped, 7
  xfailed, 3 xpassed) — the first fully clean run this session, closing out
  the "1 pre-existing unrelated failure" carried forward across reports
  68 and 69.

## 3. What this does not claim

- No production/staging migration; only ephemeral, disposable Postgres
  containers were written to for verification — `salesos_test` and any
  shared database were never touched. All ephemeral Docker resources
  (containers, network, image) removed after use.
- Does not add a tenant-timezone concept — the fix aligns this codebase's
  two outlier call sites to its own already-dominant `date.today()`
  convention; it does not introduce per-tenant business-day localization,
  which would be new product scope.
- Does not claim the capability register moved — both are correctness bug
  fixes to already-existing, already-counted code paths, not new
  capabilities.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**.

## 4. Files changed this session

- `tests/unit/test_db05_slice4_deferred_8_rls_authority.py`
- `app/modules/signal_actions/actions.py`
- `app/modules/company/repositories.py`
- `tests/integration/test_license_find_expiring_date_boundary_db.py` (new)
