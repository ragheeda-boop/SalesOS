# 86 — Effectiveness dashboard: per-cohort "avg_time_to_action_hours" reported the wrong column (2026-09-24)

## Summary

`app/modules/effectiveness/__init__.py`'s `EffectivenessService.get_dashboard()`
is genuinely live: mounted via `app/modules/effectiveness/router.py` (boot-
registered) and also called from `app/modules/signal_actions/hitl_router.py`.
Its per-cohort breakdown query selects 12 columns ending
`..., nba_acc, nba_over, avg_tta` (indices 9, 10, 11), but the Python code
building each cohort's response dict read `row[10]` (`nba_over` — a count
of overridden NBA recommendations) for `avg_time_to_action_hours`, instead
of `row[11]` (the actual average-hours figure) — a plain off-by-one
indexing bug.

This produces no error and no crash — both values are plain numbers — so
it silently returned the wrong figure on the live effectiveness dashboard:
a cohort's "average time to first action (hours)" was actually showing
its "number of overridden NBA recommendations" count. Confirmed directly:
seeding one account with `nba_rejected=2, nba_modified=1` (override count
= 3) and a real `time_to_first_action_hours=42.5` showed the dashboard
reporting `avg_time_to_action_hours: 3.0` instead of `42.5`.

The existing unit test file (`tests/unit/test_effectiveness.py`) only
exercises this module's pure helper functions (`assign_cohort`,
`_safe_lift`, `_safe_rate`, `_check_monotonicity`,
`_calibration_readiness`) — never `get_dashboard()`'s real SQL/row-
indexing path — so this had never been caught.

This finding came from a systematic per-column index count of the file's
raw SQL blocks (verifying each `row[N]` access against its SELECT's actual
column order) after several earlier bugs this session revealed how easily
column-count/order mismatches slip through raw positional-index SQL
result access; the rest of the file's row-index usages were checked the
same way and found correct.

## Fix

**`app/modules/effectiveness/__init__.py`**: `row[10]` → `row[11]` for
`avg_time_to_action_hours` in the per-cohort dict construction inside
`get_dashboard()`.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**:
`tests/integration/test_effectiveness_dashboard_cohort_indexing_db.py`
(1 test): seeds one account with deliberately distinct override-count
(3) and real hours (42.5) values, calls `get_dashboard()` end to end, and
asserts the cohort's `avg_time_to_action_hours` is the real hours figure,
not the override count.

**Genuine red→green**: reverted `row[11]` back to `row[10]`, re-ran,
confirmed the exact predicted failure (`assert 3.0 == 42.5`). Restored,
re-confirmed passing.

**Existing unit regression** (`tests/unit/test_effectiveness.py`):
**29/29 PASS**, unaffected (all exercise pure helper functions only).

**Combined session regression** (all integration tests from reports
68/70–86 run together in the same container): **53/53 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

This is a live-bug fix affecting a real, mounted effectiveness dashboard
endpoint's data correctness (not a crash — silently wrong numbers). No
production or `salesos_test` write; only a disposable, ephemeral Postgres
container was used, destroyed after verification. Phase 7 remains
BLOCKED; production remains **NOT APPROVED**.
