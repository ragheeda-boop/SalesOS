# 92 — NBAEngine: 3 independent, live-breaking bugs; a 4th finding documented, not fixed (2026-09-24)

> Note on numbering: report 89 (`89_BOOKKEEPING_RECONCILIATION_2026-09-24.md`)
> was a bookkeeping/reconciliation pass that stated "no CODE-CLOSABLE rows
> remain" and "next code-reachable work: None." This report was produced by
> a continuation of the same sweep after that bookkeeping pass, and found 3
> new, genuinely live, previously-undiscovered bugs in `runtime/nba_engine/
> __init__.py` (the entire NBA feature was completely inoperable) — so that
> bookkeeping report's stop condition, while accurate for the register
> at the time, was not the end of the line for this class of investigation.
> Numbered 92: reports 90 (`90_HUMAN_GATE_INDEX`) and 91 (`91_PO_PHASE_A_DECISION_RECORD`) were authored concurrently by a parallel session.

## Summary

Continuing the session-wide sweep, investigated `runtime/nba_engine/__init__.py`
(613 lines) after noticing zero `apply_tenant_guc`/`set_config` calls anywhere
in the file despite it being the backing engine for a real, boot-mounted
REST router. This is the most severe live finding of the entire session: the
**entire Next Best Action feature was completely non-functional** — every
real call to any of its 3 endpoints either 404'd unconditionally or crashed
with a hard SQL error, regardless of whether the target opportunity
genuinely existed with real data.

## Reachability — confirmed live, not dead code

`runtime/nba_engine/api/router.py` is mounted at boot
(`app/boot/routers.py:576`). Its 3 endpoints call straight into `NBAEngine`:

- `GET /opportunities/{id}/nba` → `engine.get_or_compute()`
- `POST /opportunities/{id}/nba/refresh` → `engine.recompute()`
- `POST /opportunities/{id}/nba/feedback` → `engine.record_feedback()`

(A separate event-driven wiring path, `runtime/nba_engine/subscribers/
__init__.py::register_subscribers()`, is confirmed dead — never called from
`app/boot/*.py` — but the REST router above is real and live regardless.)

## Bug 1: no tenant GUC pinning anywhere — every real call always failed

None of `_load_cached`, `_normalize`, `_cache_result`, `_batch_load_cached`,
or `_batch_normalize` ever pinned `app.tenant_id`. `commercial_opportunities`,
`company_features`, and `activity_records` all carry FORCE RLS with the
canonical `tenant_id::text = current_setting('app.tenant_id', true)` policy
— confirmed via `\d` on all three. Without the GUC pinned, the USING clause
evaluates to NULL/false for every row **regardless of the query's own
`WHERE ... AND tenant_id = :tid` predicate**, so every SELECT under the
restricted `salesos_app` role silently returned zero rows.

Effect: `recompute()`'s very first step, `_normalize()`, always found the
opportunity's own SELECT returning nothing → early-returns `None` → the
router treats this as "Opportunity not found" (404) for every real
opportunity, every time. `GET .../nba` and `POST .../nba/refresh` were both
permanently broken this way.

### Fix

`from app.database import apply_tenant_guc` + `await apply_tenant_guc(session,
tenant_id)` immediately after opening each session, in all 5 methods —
matching this session's established DEC-085 pattern (reports 68, 75, 77, 78,
83, 84, etc.).

## Bug 2 (masked by bug 1, exposed only after fixing it): nonexistent `description` column

With the GUC pin in place, `_normalize()`'s activities query
(`SELECT id, action, timestamp, description FROM activity_records ...`) now
actually executes for real — and immediately fails:
`asyncpg.exceptions.UndefinedColumnError: column "description" does not
exist`. Confirmed via `\d activity_records`: the real columns are `id`,
`actor`, `action`, `entity_type`, `entity_id`, `target_type`, `target_id`,
`metadata` (JSONB), `tenant_id`, `timestamp` — no `description` column at
all. `_batch_normalize()` has the identical bug in its own activities query.

This is a textbook example of one bug fully masking a second: before fixing
bug 1, execution never reached this line (the early `None` return happened
first), so this hard SQL error was completely dormant.

### Fix

Established convention for this exact table (confirmed via
`app/application/dashboard/mappers/timeline_mapper.py:32`:
`meta.get("description") or r["action"]`) is that descriptive text lives
inside the `metadata` JSONB column, not a dedicated column. Neither consumer
of `recent_activities` in this file reads a `description` key (only
`.get("timestamp")` and `len(activities)` are read — confirmed by grep), so
the minimal correct fix is simply selecting the real `metadata` column
instead of the nonexistent `description` column, in both queries.

## Bug 3 (masked by bugs 1+2, exposed only after fixing both): dict bound as raw jsonb parameter

With bugs 1 and 2 fixed, execution now reaches `_cache_result()`'s INSERT —
and fails again: `asyncpg.exceptions.DataError: invalid input for query
argument $4: {...} ('dict' object has no attribute 'encode')`. The `signals`
column is `jsonb`, but the code bound a raw Python `dict`
(`{"action": nba.action, "reason": nba.reason}`) directly as a query
parameter with no serialization — the same bug class as reports 74/75/82/83
this session (`:name::type` scanner quirk / raw-dict-into-jsonb).

### Fix

`json.dumps(...)` the dict before binding, and `CAST(:signals AS jsonb)` in
both the INSERT and the `ON CONFLICT DO UPDATE` clause (matching the
established `CAST(... AS type)` pattern rather than the broken `::type`
suffix form).

## Finding 4: `record_feedback()` — a genuine architecture gap, NOT fixed

While reviewing `record_feedback()`, found it has **no `tenant_id` parameter
at all** (its signature is `(opportunity_id, nba_id, user_id, action,
reason=None)`), and its own caller,
`runtime/nba_engine/api/router.py::record_nba_feedback()`, never passes one
either. Separately, its INSERT targets `nba_feedback` columns (`nba_id`,
`opportunity_id`, `user_id`, `action`) that **do not exist on the real
table at all** — confirmed via migration `m8n9o0p1q2r3`, whose real schema
requires NOT NULL `tenant_id`, `company_name`, `action_id` (UUID FK),
`recommendation_id` (UUID FK), `seller_id`, `decision`,
`original_action_type`. `_build_recommendation()` confirms `nba.id` is a
throwaway `str(uuid.uuid4())` never persisted anywhere queryable — there is
no way to resolve a real `recommendation_id`/`action_id` from the inputs
`record_feedback()` currently receives.

This is not a naming typo fixable by renaming columns — it needs a real
product/architecture decision (what does "feedback on an NBA" mean against
a schema built for a different, richer HITL seller-operating-model concept
with FK linkage to `agent_sales_actions`?). Matching this session's
established practice for genuine architecture gaps (reports 59, 60, 84,
87, 88), this is **documented directly in the source** (a dated comment at
the call site) and in this report, not patched with invented data.
`POST /opportunities/{id}/nba/feedback` remains broken until that decision
is made.

## Verification

Fresh `pgvector/pgvector:pg16`-based ephemeral container (`loop4h-pg` +
`loop4h-runner`, recreated this session with the correct owner-vs-restricted
role env split established in report 82), `salesos_app` restricted role.

**New file**: `tests/integration/test_nba_engine_rls_db.py` (3 tests):
1. `recompute()` finds and returns a genuinely-seeded, real opportunity.
2. `recompute()` correctly returns `None` for a real opportunity under a
   *different* tenant (proving isolation is real, not just "broken open").
3. A cached result written by `_cache_result()` is correctly read back by
   `_load_cached()` on a second `get_or_compute()` call for the same tenant.

**Genuine red→green, all 3 bugs independently reproduced and re-fixed in
sequence**:
- Reverted only the 5 `apply_tenant_guc` calls → both data-bearing tests
  failed with the exact predicted symptom (`assert None is not None` — RLS
  filtered everything out). Restored, re-confirmed green.
- Reverted only the `metadata`→`description` fix → reproduced the exact
  predicted `UndefinedColumnError: column "description" does not exist`.
  Restored, re-confirmed green.
- Reverted only the `json.dumps`/`CAST(... AS jsonb)` fix → reproduced the
  exact predicted `DataError: ... 'dict' object has no attribute 'encode'`.
  Restored, re-confirmed green.

**Existing regression, unaffected**: `tests/unit/test_nba_pipeline.py`,
`test_ai_reasoner.py`, `test_il1c_runtime_proof.py`, `test_deal_health.py` —
**114/114 PASS** (none of these mock the session away entirely for the
DB-touching methods, but none previously exercised a real Postgres
connection either — confirmed they still pass unchanged).

**Combined session regression** (every integration test from reports
68/70–89 run together in the same container): **57/57 PASS**, no
cross-fix regressions.

## Production / Phase 7

This closes the single most severe functional gap found in this entire
session: the NBA feature was not degraded or partially working — it was
**completely inoperable** for every real tenant, on every endpoint, with
the "get" and "refresh" paths silently masquerading as a 404 (misleadingly
suggesting the opportunity didn't exist) and the "feedback" path still
broken pending a real product decision. No production or `salesos_test`
write; only a disposable, ephemeral Postgres container was used, to be torn
down after verification. Phase 7 remains BLOCKED; production remains **NOT
APPROVED**.
