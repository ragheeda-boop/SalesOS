# 88 — WorkQueueService.get_my_day(): live cross-seller pending-action leak; a second, undecided analytics-visibility question (2026-09-24)

## Summary

Continuing the review of `app/modules/signal_actions/hitl_service.py`
(started in report 87), found a genuinely live, currently-active
cross-seller data leak in `WorkQueueService.get_my_day()` — the backing
service for the real, mounted `GET /work-queue/my-day` endpoint
(`get_my_day_for_current_user`, called with the caller's own authenticated
user id as `seller_id`).

## Bug found and fixed: pending actions leaked across sellers

`get_my_day()`'s own docstring describes it as a **"My Day read model:
actions + follow-ups + scores, mine-only."** Its three data sections
(pending actions, pending follow-ups, recent outcomes) are each supposed
to show only the calling seller's own items. The follow-ups and outcomes
queries correctly filter `AND seller_id = :s` — but the **pending actions**
query filtered only on `tenant_id` and `status`, never on the seller.

`agent_sales_actions.user_id` is the seller-owner column (populated at
INSERT time in `app/modules/signal_actions/actions.py`) — confirmed via
grep of the one INSERT call site. Confirmed directly: seeding two
sellers' pending actions in the same tenant and calling `get_my_day()` for
seller A returned **seller B's pending action too** — every seller's "My
Day" page showed every other seller's pending sales actions in the same
tenant, not just their own.

### Fix

**`app/modules/signal_actions/hitl_service.py`**: added
`AND user_id = :s` to the pending-actions query, matching the pattern
already correctly used by the sibling follow-ups/outcomes queries in the
same method.

### Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**:
`tests/integration/test_work_queue_my_day_seller_scoping_db.py` (1 test):
seeds one pending action each for two different sellers in the same
tenant, calls `get_my_day()` for seller A, asserts only seller A's
company appears.

**Genuine red→green**: reverted the `AND user_id = :s` filter, re-ran,
confirmed the exact predicted leak (`{'Seller A Co', 'Seller B Co'} ==
{'Seller A Co'}` failed — both companies visible). Restored, re-confirmed
passing. Existing `tests/unit/test_hitl_authenticated_seller.py` (which
mocks `get_my_day()` entirely, never exercising the real SQL — why this
was never caught before) 3/3 PASS, unaffected.

**Combined session regression** (all integration tests from reports
68/70–88 run together in the same container): **54/54 PASS**, no
cross-fix regressions.

**Full local unit suite**: **3766 passed, 0 failed** (4 skipped, 7
xfailed, 3 xpassed — all pre-existing categories) — clean baseline
reconfirmed.

## Second finding, documented only: seller-productivity leaderboard visibility

While reviewing the adjacent `FeedbackAnalyticsService.get_dashboard()`
(the `GET /analytics` endpoint), found its "Seller productivity" section
(a named, per-seller top-10 leaderboard: `seller_id`, `total_outcomes`,
`converted`, `conversion_rate`) is **unconditionally tenant-wide** —
it ignores the endpoint's own optional `seller_id` query parameter
entirely, always returning every seller's individually-identifiable
performance data.

Unlike `get_my_day()`, this is **not** treated as a bug fix here, because:

1. `get_dashboard()`'s docstring never promises "mine-only" — it's
   described as an analytics dashboard with an *optional* seller filter,
   and the other 4 sections correctly honor that filter (aggregate
   rollups, correctly scoped when `seller_id` is supplied).
2. The real open question is **authorization policy, not scoping
   mechanics**: `GET /analytics` is gated only by a generic
   `signal_actions:READ` permission (not a manager/admin-only role) —
   confirmed via the router. Whether ordinary sellers should be able to
   see a named cross-seller leaderboard at all is a genuine product
   decision (some sales orgs intentionally show team leaderboards for
   gamification; others keep individual performance manager-only), not
   something this session should decide unilaterally.

Matching the established practice for genuinely ambiguous
product/authorization questions (reports 59/60/84/87), this is documented
for a deliberate decision rather than silently gated or left as-is without
comment.

## Production / Phase 7

The `get_my_day()` fix closes a live, currently-active information leak
between sellers within the same tenant. No production or `salesos_test`
write; only a disposable, ephemeral Postgres container was used, destroyed
after verification. Phase 7 remains BLOCKED; production remains **NOT
APPROVED**.
