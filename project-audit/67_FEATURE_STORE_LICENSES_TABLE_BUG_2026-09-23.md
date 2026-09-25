# Feature Store: Wrong Table/Column Names Broke Expansion & Revenue Scores — 2026-09-23

## What this is

Found while investigating DEC-157's semantics questions (checking every
caller of `runtime/feature_store/features.py`'s raw-SQL queries against the
14-table orphan-keep audit). This is unrelated to DEC-157 itself but is a
significant, previously-undiscovered, live bug — documented and fixed on
its own.

## The bug

`ExpansionScoreComputer.compute()` and `RevenueScoreComputer.compute()`
(both in `runtime/feature_store/features.py`) queried a table that **does
not exist anywhere in the schema**:

```sql
SELECT expires_at FROM public.company_licenses
WHERE company_id = :cid AND tenant_id = :tid AND status = 'active'
ORDER BY expires_at ASC LIMIT 1
```

The real table, created in `0001_baseline.py`, is named **`licenses`** (not
`company_licenses`), has **no `tenant_id` column** (it is a Category-B1
join-scoped child of `companies` per `app/alembic/lib/rls.py`'s
`CATEGORY_B1_JOIN_TABLES`), and its expiry column is **`expiry_date`** (a
plain `DATE`), not `expires_at`.

Confirmed by direct, ephemeral-database reproduction (not inferred): every
call to either computer with a real `company_id`/`tenant_id` raised

```
sqlalchemy.exc.ProgrammingError: ... UndefinedTableError:
relation "public.company_licenses" does not exist
```

**Why this was never visibly reported:** `runtime/feature_store/__init__.py`'s
orchestration loop wraps every computer's `compute()` call in a bare
`try/except Exception`, logs the error, and records the feature as failed
(`None`) — a deliberate resilience pattern for the *orchestrator*, but it
meant this specific, 100%-reproducible bug has been silently swallowed on
every single invocation since these two computers were written, with zero
test coverage to ever catch it (`grep` found no test file referencing
either class at all).

**A second, compounding bug in the same code path:** even after fixing the
table/column names, the original date-arithmetic line
(`(renewal_dt - datetime.now(timezone.utc)).days`) would have raised
`TypeError: unsupported operand type(s) for -: 'datetime.date' and
'datetime.datetime'` — `expiry_date` is a plain `DATE`, so asyncpg returns a
`date`, not a `datetime`, and a naive `date` cannot be subtracted from a
timezone-aware `datetime`. This line had never been exercised either, since
the query above it always raised first.

## Fix

- `ExpansionScoreComputer`: query `public.licenses`, `expiry_date` instead
  of `expires_at`; drop the non-existent `tenant_id` filter (the query is
  already scoped by `company_id`, and RLS on `licenses` — via its
  Category-B1 join policy — enforces the caller's pinned tenant GUC as
  defense-in-depth once GUC pinning is added for this call path, see
  DEC-157 report 68).
- `RevenueScoreComputer`: same table/column fix for its `active_licenses`
  count query.
- Date handling: normalize `expiry_date` to a plain `date` before
  subtracting from `datetime.now(timezone.utc).date()` (also `date()`),
  handling the `str`/`datetime`/`date` cases explicitly instead of assuming
  a `datetime`.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16`, migrated to the current head,
`salesos_app` restricted role. New
`tests/integration/test_feature_store_licenses_table_db.py`:

- Seeds a real tenant, company, and one active `licenses` row via raw SQL
  matching the actual schema.
- `test_expansion_score_computer_reads_real_licenses_table`: asserts
  `days_to_renewal` is correctly computed from the real row (proving both
  the table-name fix and the date-arithmetic fix).
- `test_revenue_score_computer_reads_real_licenses_table`: asserts
  `deal_equity == 50000` (`0` total deal value `+ 1` active license
  `× 50000`) — only possible if the query found exactly the one seeded
  license row, not a coincidental pass.

**Genuine red→green, not asserted:** reverted both fixes (table/column
names back to the broken originals) with `sed`, re-ran — both tests failed,
one with the exact `UndefinedTableError` predicted above. Restored the
fix, re-ran — both passed again.

Regression: `tests/unit/test_feature_store.py` + `test_feature_store_cache.py`
**32/32 PASS** (these are orchestration-level tests using fakes; unaffected
by this fix, confirming no behavior change to the parts they cover).
`python -m py_compile` clean. Pre-existing unrelated Ruff findings (unused
imports predating this change) left untouched. Ephemeral database,
network, and image removed after verification.

## Deliberate non-claims

- Does not add GUC pinning for these two computers (or the other Feature
  Store computers reading the 9 `company_*` orphan-keep tables) — that is
  DEC-157's job, tracked and executed separately (report 68). This fix is
  purely the table/column-name and date-arithmetic correction.
- Does not audit the other Feature Store computers (`IcpComputer`,
  `FundingScoreComputer`, `HiringScoreComputer`, `GrowthScoreComputer`,
  `IntentScoreComputer`) for similar table/column mismatches — a targeted
  check found none (their table names all match the DEC-130f orphan-keep
  register), but a full line-by-line re-verification of every raw query in
  this file was not performed.
- No database, migration, deployment, commit, or push occurred (beyond the
  ephemeral verification database, destroyed after use).
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**. This
  fix restores a previously-always-failing GTM/lead-scoring feature; it
  does not touch Master Data or production-readiness gates.
