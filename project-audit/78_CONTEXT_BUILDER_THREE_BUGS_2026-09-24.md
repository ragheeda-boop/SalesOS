# 78 — ContextBuilder.build(): 3 independent bugs, never once exercised against a real database (2026-09-24)

## Summary

`runtime/context_runtime/__init__.py`'s `ContextBuilder.build()` assembles a
multi-dimensional `CompanyContext` snapshot (business/sales/marketing/
customer/revenue) for a company, by querying `companies`, `licenses`,
`company_deals`, and `company_intent_visits`. Unlike this session's several
prior dead-code findings (reports 73/74/76/77), **this class is genuinely
live at boot**: `app/boot/startup.py::_init_context_builder` instantiates it
with the real `async_session` factory, and `_init_decision_engine` injects
it into `DecisionEngine`, whose `evaluate()` calls
`self._context_builder.build(company_id, tenant_id)` as its very first step
(`runtime/decision_runtime/__init__.py:243`).

However, `app.state.decision_engine` itself is only ever *assigned* at boot
— confirmed via repo-wide grep that no router, background job, or scheduled
task ever calls `.evaluate()` on it — so end-to-end reachability from a live
HTTP request is currently zero. Every existing test that constructs a
`DecisionEngine` (`test_il2a_save_decision_jsonb.py`, etc.) injects a
`MagicMock()` or fake in place of `context_builder`, so `ContextBuilder`'s
real SQL had never once been executed by any test, ever — confirmed via
grep: zero test files reference `ContextBuilder` directly. Three
independent bugs were found, none previously caught:

1. **No tenant GUC pinning anywhere in `build()`.** `companies`,
   `company_deals`, and `company_intent_visits` all have RLS + FORCE RLS.
   Without `app.tenant_id` pinned, the main company SELECT — which already
   carries its own `WHERE ... AND c.tenant_id = :tid` predicate — still
   returns 0 rows under RLS for a genuinely matching, real company
   (confirmed directly: `count(*) = 0` against real seeded data). `build()`
   then silently hits its `if not r: return ctx` early-exit, producing an
   almost entirely empty context for a company that actually has real
   data — no error, just silently wrong.
2. **The license-expiry query filtered on `licenses.tenant_id`, a column
   that does not exist on `licenses` at all.** Confirmed via `\d licenses`
   and a direct query attempt:
   `ERROR: column "tenant_id" does not exist`. Unlike bug 1, this is a hard
   SQL error with no surrounding try/except in `build()`, so it crashes the
   entire context build outright. Fixed by removing the (nonexistent)
   `tenant_id` filter — `company_id` alone is sufficient scoping, since it
   was already resolved from a tenant-scoped company row.
3. **`licenses.expiry_date` is a plain `date` column; the code subtracted
   an aware `datetime.now(timezone.utc)` from it.** asyncpg returns
   `datetime.date` for a `date` column, and `date - datetime` raises
   `TypeError: unsupported operand type(s) for -: 'datetime.date' and
   'datetime.datetime'` — confirmed directly. This is the same UTC/local
   calendar-date bug class found repeatedly this session (reports 70/73),
   but manifesting as a hard type error here rather than a rollover.
   Fixed by doing calendar-date arithmetic with `date.today()`, consistent
   with this codebase's dominant existing convention.

Correction of an earlier misreading during investigation: `company_deals`
and `company_intent_visits` (referenced by the sales/marketing queries) DO
exist with matching column names — an initial `to_regclass()` probe result
was misread as "table not found" when it actually confirmed both tables
exist. No bug there; only bugs 1–3 above are real.

## Fixes

**`runtime/context_runtime/__init__.py`**:
- Added `from app.database import apply_tenant_guc`; changed
  `from datetime import datetime, timezone` → `from datetime import date, datetime`.
- `build()`: pin `app.tenant_id` once, immediately inside the
  `async with self._session_factory() as session:` block.
- License-expiry query: removed the nonexistent `tenant_id` filter.
- Expiry calculation: normalize `exp` to a `date` (via `date.fromisoformat()`
  for a string, `.date()` for a `datetime`, or pass through if already a
  `date`) and subtract from `date.today()`.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app` restricted
role (non-superuser, `NOBYPASSRLS`).

**New file**: `tests/integration/test_context_builder_db.py` (2 tests):
- `test_build_returns_real_context_for_a_genuinely_matching_company` — seeds
  a company with a real license (45-day-out expiry), an open deal, and a
  recent website visit; asserts every dimension of `CompanyContext` is
  genuinely populated (industry, city, size band, deal counts/value, visit
  count, license count, revenue growth, days-to-renewal).
- `test_build_returns_empty_context_for_a_nonexistent_company` — confirms
  the honest-empty path still works for a company that truly doesn't exist.

**Genuine red→green, all 3 bugs isolated independently**:
1. Removed the GUC pin: re-ran the "genuinely matching company" test,
   confirmed `ctx.business.industry` was `None` instead of `"Tech"` — the
   exact predicted silent-empty-context failure. Restored, re-confirmed.
2. Reverted the license-expiry query to include `tenant_id`: re-ran, got the
   exact predicted `UndefinedColumnError: column "tenant_id" does not
   exist`. Restored, re-confirmed.
3. Reverted the expiry calculation to the original `datetime.now(...)`
   subtraction: re-ran, got the exact predicted
   `TypeError: unsupported operand type(s) for -: 'datetime.date' and
   'datetime.datetime'`. Restored, re-confirmed.

All three restored together: **2/2 PASS**.

**Combined session regression** (all integration tests from reports
68/70–78 run together in the same container): **37/37 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

`ContextBuilder` is instantiated at boot with a real DB session factory and
has one real internal caller (`DecisionEngine.evaluate()`), but that
entry point itself has zero external callers today (no router/job reaches
`app.state.decision_engine`) — so this fix closes a bug that would surface
the instant that wiring is added, without itself changing any currently
reachable behavior. No production or `salesos_test` write; only a
disposable, ephemeral Postgres container was used, destroyed after
verification. Phase 7 remains BLOCKED; production remains **NOT APPROVED**.
