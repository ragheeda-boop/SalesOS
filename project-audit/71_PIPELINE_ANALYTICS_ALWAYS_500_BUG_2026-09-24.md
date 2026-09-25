# 71 — Pipeline Deal-Scoring Endpoints Always 500'd (Wrong Table/Columns), Found via Systematic Sweep (2026-09-24)

> **Scope:** Found and fixed a real, always-broken production bug (same class
> as report 67's Feature Store `licenses` bug) via a systematic, repo-wide
> raw-SQL table-reference audit, not a one-off. Also documents one related,
> lower-severity finding left unfixed because the correct table cannot be
> confidently determined without product input. Verified on a fresh ephemeral
> Postgres container; `salesos_test` was never touched.

## 1. Method: systematic raw-SQL table-reference sweep

Report 67's Feature Store bug (querying a nonexistent `company_licenses`
table) was found by chance while working on an unrelated task. This session
generalized that into a repeatable check: extracted every `FROM`/`INSERT
INTO`/`UPDATE`/`JOIN <name>` token from raw SQL across `app/`, `runtime/`,
`domains/`, `intelligence/`, `sdk/` (111 unique tokens), diffed it against
the real 211-table `public` schema on a fresh ephemeral Postgres migrated to
head, and manually triaged every token not in that list. Most were false
positives (CTE aliases like `stage_counts`/`candidates`/`recovered`/`existing`,
PL/pgSQL function parameters like `p_tenant_id`, function calls like
`reserve_provider_spend(...)`, Postgres system catalogs). Two were real:

## 2. Real bug found + fixed: `/pipeline/score-deal` and `/pipeline/score-batch`

`runtime/pipeline_analytics/router.py` (3 occurrences across both endpoints)
queried `public.pipeline_stage_entries` — a table that does not exist
anywhere in the schema — using columns `stage_name` and `exit_reason`,
neither of which exist either. The real table, created in
`0007_commercial_domain.py`, is `commercial_stage_entries`, with columns
`from_stage`/`to_stage`/`entered_at`/`exited_at` (confirmed by the sibling
file `runtime/pipeline_analytics/__init__.py`'s `PipelineAnalyticsEngine`,
which already queries this table correctly — clear proof the two files
diverged, not that the concept itself was undefined).

Both endpoints wrap their entire body in `except Exception: raise
HTTPException(500)`, so every real call to either endpoint has always
returned a 500 — a Decision Platform deal-scoring feature that has likely
**never worked**, with **zero** prior test coverage (the only existing suite
in this package, `tests/unit/test_pipeline_analytics.py`, exercises the
different, correctly-written `PipelineAnalyticsEngine` class, not this
router).

### Fix

- `days_in_stage` query: `pipeline_stage_entries` → `commercial_stage_entries`,
  `stage_name` → `to_stage`; added `ORDER BY entered_at DESC LIMIT 1` (a deal
  that re-entered the same stage more than once must use its most recent
  entry, not an arbitrary/unordered row) — applied to both `score_deal` and
  `score_batch`.
- Conversion-rate query: same table rename; `exit_reason LIKE 'advanced_to_%'`
  (a column that never existed) replaced with `exited_at IS NOT NULL` (a
  stage-entries row's `exited_at` being set is exactly what "this deal moved
  on from this stage" means in the real schema).
- No explicit `tenant_id` filter was added to the conversion query — checked
  first that this is not a cross-tenant leak: `commercial_stage_entries` has
  its own RLS + FORCE RLS + `tenant_isolation_commercial_stage_entries`
  policy (Category A, direct `tenant_id` column), and the router's
  `db: AsyncSession = Depends(get_db_session)` sessions are GUC-pinned
  automatically per DEC-085 (`app/database.py::get_db()`, via the
  `_current_tenant_id` ContextVar set by request middleware) — so RLS
  already scopes every query to the caller's tenant regardless of the SQL's
  own WHERE clause, the same way every other tenant-scoped raw-SQL query in
  this codebase relies on it.

### Verification

New `tests/integration/test_pipeline_analytics_score_deal_db.py` (2 tests),
run through the actual HTTP router (not just the query in isolation) on a
fresh ephemeral Postgres migrated to head:

- Seeds a tenant, company, opportunity, an already-exited prior stage entry,
  and a **currently open** stage entry backdated 60 days (well beyond the
  scorer's ~11-day default average per-stage cycle time) — a deal
  deliberately "stuck."
- `POST /pipeline/score-deal`: asserts HTTP 200 (was always 500) and that
  the `stage_velocity` scoring factor lands at its worst tier (`<=0.3`).
  This specifically distinguishes "the query found the real 60-day
  duration" from "the query silently found nothing and `days_in_stage`
  defaulted to 0" — a broken-but-non-crashing version of this query would
  incorrectly score `stage_velocity=1.0` (a "moving fast" deal) for every
  deal regardless of real data, so a passing assertion here only holds if
  the fix genuinely reads the seeded duration.
- `POST /pipeline/score-batch`: same seed, asserts 200 + `total_scored == 1`.
- A genuine engineering obstacle surfaced and was resolved along the way:
  Starlette's `TestClient` drives the ASGI app from its own background
  event loop (an anyio blocking portal), a different loop than the one used
  to seed the database beforehand — combining `TestClient` with this
  codebase's process-global async engine for the first time in this
  session's test suite raised `RuntimeError: ... attached to a different
  loop`. Fixed by making the seed phase run via `asyncio.run()` in its own
  loop, explicitly disposing the shared `engine` immediately after (so its
  connection pool is empty and will bind fresh connections to whichever
  loop touches it next), then only entering `TestClient(...)` afterward.
  Also required overriding `verify_token` (not just the permission-check
  dependency) — `require_permission_dep`'s closure resolves `Depends(verify_token)`
  as an independent sub-dependency regardless of any monkeypatch to the
  `require_permission` function it calls internally, so a synthetic Bearer
  token without a `verify_token` override would otherwise still hit real
  JWKS key loading.
- Regression: `tests/unit/test_pipeline_analytics.py` +
  `tests/unit/test_revenue_dashboard.py` — **40/40 PASS**, no change in
  `PipelineAnalyticsEngine`'s already-correct behavior.
- Repo-wide grep after the fix: zero remaining references to
  `pipeline_stage_entries` anywhere except this report and the new test
  file's own explanatory docstring.
- Full local `tests/unit/` suite: **3766 passed, 0 failed** (unchanged from
  before this fix — this bug lived entirely in a previously-uncovered
  integration path).

## 3. Related finding, NOT fixed: `intelligence/grounding.py`

`GroundingService._get_signals()` and `_get_recent_activity()` (used live by
`runtime/agent_runtime/__init__.py`, not dead code) query
`public.buying_signals` and `public.timeline_events` — neither exists
anywhere in the schema. Unlike the pipeline-analytics bug, this one is
**not** confidently fixable right now:

- Both methods are wrapped in a bare `except Exception: return []` with no
  logging at all, so the failure is currently silent (agent grounding
  quietly loses real signal/activity context rather than crashing) — lower
  severity than a 500, but still a real product gap.
- The queried columns (`intensity`, `priority`, `detected_at` for signals;
  `description`, `occurred_at` for activity) do not cleanly match any
  candidate table found: `company_signals` (the real "buying signal"
  table) has `severity`/`status`/`confidence_score`/`first_seen_at`
  instead; `timeline_entries` (a real table) has `importance`/`created_at`/
  a JSONB `data` blob instead of a `description` column, and — per this
  same project's own report 19 finding, in a different file — was
  previously determined to be **"the wrong store"** for an analogous
  timeline need, with `audit.audit_log` via `AuditTrail.query` being the
  correct source there instead.
- Guessing a mapping here risks the same trap report 19 already
  documented once; this needs the same kind of explicit product
  verification that finding got, not a second silent guess. Flagged, not
  fixed, this session.

## 4. What this does not claim

- No production/staging migration; only an ephemeral, disposable Postgres
  container was used for verification, torn down after. `salesos_test` was
  never touched.
- Does not fix `intelligence/grounding.py` (§3) — that finding is
  documented, not resolved.
- Does not claim the capability register moved — this is a correctness fix
  to an already-existing, already-counted feature, not a new capability.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**.

## 5. Files changed this session

- `runtime/pipeline_analytics/router.py`
- `tests/integration/test_pipeline_analytics_score_deal_db.py` (new)
