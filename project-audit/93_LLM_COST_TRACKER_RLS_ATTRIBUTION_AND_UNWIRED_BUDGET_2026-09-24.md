# 93 — LLM cost tracking / budget enforcement (AI Foundation F2): two bugs fixed, one wiring gap documented (2026-09-24)

## Summary

AI Foundation F2 (commit `4e1592f`, AGENTS.md §11) is described as
"DB-backed cost tracking with pre-call budget enforcement." Reviewing
`intelligence/providers/cost_tracker.py` and its only caller
`intelligence/agents/llm.py` found that per-tenant LLM budget enforcement
**cannot work in the running application** for three independent reasons.
Two are code bugs, now fixed and proven. The third is a wiring gap. I
documented it and did not change it, because turning it on changes live
LLM-call behavior.

## Bug 1: no tenant GUC pinning (FIXED)

`CostTracker` opens its own sessions from `self._db_session_factory()` and
never pinned `app.tenant_id`. Both tables it uses have FORCE row-level
security with the canonical policy (confirmed on a fresh migrated database):

| table | RLS | FORCE |
|---|---|---|
| `tenant_llm_budgets` | t | t |
| `llm_cost_entries` | t | t |

Under the restricted `salesos_app` role, `set_budget()` fails with
`new row violates row-level security policy for table "tenant_llm_budgets"`.
Every budget read also returns zero rows, which `check_budget()` treats as
"no budget, allow."

**Fix:** a local `_pin_tenant(session, tenant_id)` helper (`set_config('app.tenant_id', …, true)`)
is called at all 8 session sites. For the two `session.begin()` blocks it is
called inside the transaction. It is a local helper, not
`app.database.apply_tenant_guc`, to avoid an `intelligence → app` import
cycle. This follows the same precedent as `sdk/events/store.py` (report 68).

## Bug 2: spend never recorded for default-bound tenants (FIXED)

`LLMService.chat()` computes `effective_tenant = tenant_id or self._default_tenant_id`.
The pre-call budget check uses `effective_tenant`, but the post-call
`track()` + `deduct_budget()` block was gated on the **explicit** `tenant_id`
argument. Agents never pass it. They rely on the per-request default
binding (`app/routers/copilot.py` constructs `LLMService(default_tenant_id=…)`).
So spend was never recorded or deducted, and a budget could never be
exhausted.

**Fix:** `intelligence/agents/llm.py:212` now gates on `effective_tenant`.

## Also fixed: December billing-period end

`get_period_summary()` computed December's `period_end` as `Dec 28` instead
of `Jan 1` of the next year. Fixed with `date(today.year + 1, 1, 1)`.

## Wiring gap — documented, NOT fixed

`init_cost_tracker()` is never called anywhere in `app/` or `runtime/`, and
none of the three production `LLMService(...)` constructions passes a
`cost_tracker`:

- `app/routers/copilot.py:146`
- `intelligence/rag/service.py:28`
- `runtime/agent_runtime/__init__.py:208`

So in the running application `self._cost_tracker is None`, and the whole F2
block is skipped. Central `ai_tokens` quota metering (`usage_meter_factory`,
AGENTS.md §19) is a separate path and still works.

**Why I did not wire it:** `check_budget()` is not wrapped in `try`. Wiring
it at boot adds a synchronous database round-trip before every LLM call, and
a database error there would fail the call. Choosing fail-open versus
fail-closed on a budget-store error, and enabling spend enforcement on live
calls, are product and ops decisions. With Bugs 1 and 2 fixed, wiring is now
one line (`init_cost_tracker(async_session)` in `app/boot/startup.py`) once
that decision is made.

## Verification

Fresh-migrated ephemeral `pgvector/pgvector:pg16` database, restricted
`salesos_app` role (non-superuser, no `BYPASSRLS`).

**New file:** `tests/integration/test_llm_cost_tracker_rls_db.py` (2 tests):
1. The budget persists and reads back for its own tenant, and is invisible
   to another tenant.
2. An `LLMService` with only a default-bound tenant and a real `CostTracker`
   records the first call's spend (1 row, 2 cents deducted). The second call
   is then rejected with `Budget exceeded`. The other tenant sees no records
   and zero spend.

**Genuine red→green, each bug isolated** (reverted in the container copy only):
- Pins removed → `InsufficientPrivilegeError: new row violates row-level security policy for table "tenant_llm_budgets"`.
- `llm.py:212` reverted to `tenant_id` → `assert 0 == 1` (no cost record written).
- Both restored → 2/2 PASS.

**Regression:**
- `tests/unit/test_ai_foundation_f2.py` 27/27 PASS.
- Combined session integration regression (reports 68/70–92 plus this file)
  **59/59 PASS**.

## Register effect

None. The 132-row register (report 57 §2) has no dedicated row for LLM
budget enforcement. Row 126 ("Provider Spend Budget ledger") is a different
system (report 30).

## Deliberate non-claims

- Budget enforcement is **not live**. Bugs 1 and 2 are fixed, but nothing
  instantiates the tracker at runtime (see the wiring gap above).
- `chat_stream()` and `embed()` still resolve tenant only from the explicit
  argument (they have no default-tenant fallback). This is consistent within
  those methods and was not changed.
- No production or `salesos_test` write; only the disposable `loop4h-pg`
  container. Phase 7 row 40 is unchanged. Production is **NOT APPROVED**.
