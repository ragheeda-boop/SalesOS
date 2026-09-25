# 69 — DEC-158 + DEC-159 Closure: Billing-Tables RBAC Acceptance + Cache-Router Admin Gate (2026-09-23)

> **Scope:** Closes the remaining 2 of the 3 pending decisions carried
> forward from reports 60 and 63 (DEC-157/report 68 closed the first, the
> orphan-keep RLS remediation, separately). Both closures here are
> low-risk: one is a documentation-only architectural acceptance with no
> code change (DEC-158), the other is a single-file permission tightening
> with full test coverage (DEC-159). No production/staging access, no
> shared database write.

## DEC-158 — Owner-plane billing tables: accept app-layer RBAC, no RLS

Report 60 found 6 owner-plane billing tables (`subscriptions`,
`usage_meters`, `usage_meter_events`, `dunning_cases`,
`platform_billing_invoices`, `stripe_webhook_events`) with `tenant_id` but
no RLS, and presented 3 options without deciding: (a) a second Postgres
role for owner-plane access, (b) a role-aware RLS predicate, (c) formally
accept the existing app-layer RBAC (`require_owner_role_dep("admin")`)
design as sufficient.

**Decision: (c), accepted.** These 6 tables have a real, already-shipped
requirement for the owner-admin billing dashboard to read across all
tenants in one query, through the same restricted `salesos_app` Postgres
role every tenant request uses. A single `app.tenant_id` GUC cannot mean
both "this tenant" and "every tenant" — a standard RLS policy would break
the owner dashboard's own cross-tenant listing. Options (a)/(b) are real
upgrades but are separately-scoped architecture work (new connection
management, or a more fragile predicate already flagged in report 60 as
riskier than doing nothing), not a quick follow-on. Full ruling:
`docs/program/decisions/DEC-158-BILLING-TABLES-OWNER-PLANE-RBAC-ACCEPTED.md`.

**Confirmation performed before accepting** (read-only, this session):
re-ran and extended report 60's grep of every file importing the 6 billing
ORM model classes. Found 2 additional import sites beyond report 60's
original list — `app/modules/admin/routers/billing.py` and
`app/modules/admin/routers/tenants.py` — both confirmed owner-role-gated
(`require_owner_role_dep("admin")`) at the router level, same as every
other billing router. Two apparent name matches
(`SignalSubscriptionModel`, `WebhookSubscriptionModel`) were checked and
are unrelated classes (substring false positives, not the billing models).
No tenant-JWT-gated route was found reaching any of the 6 tables. This
remains, as report 60 stated, a reasonably complete but not formally
exhaustive method — not a claim of full repository-wide proof.

**No code changed for DEC-158.** This is a documentation-only closure: the
finding is now a ruled-on, written architectural decision instead of an
open question.

## DEC-159 — Gate /api/v1/cache/* behind the "admin" role

Report 63 ("Next code-reachable work" item 1) flagged that
`app/modules/cache/router.py` required only `verify_token` (any
authenticated user, any role, any tenant) for raw caller-supplied-key
`get`/`set`/`delete` plus a wildcard `flush(pattern="*")` — a wider blast
radius than most per-tenant endpoints, since there is no per-key
tenant-prefix check anywhere in this router.

**Decision: tighten to `require_role_dep("admin")`, accepted and
implemented this session.** This is the same mechanism already used for
other infra/ops-level routers in this codebase (`app/routers/metrics.py`,
`benchmarks.py`), and simpler than inventing a new
`PermissionAction`/resource pair for a router that is not a specific
business resource.

### Code change

`app/modules/cache/router.py`: `Depends(verify_token)` →
`Depends(require_role_dep("admin"))` at the `APIRouter(...)` level (covers
all 5 endpoints — `/health`, `GET /{key}`, `POST /set`, `DELETE /{key}`,
`POST /flush`). `require_role_dep("admin")` already depends on
`verify_token` transitively via `get_current_user_role`, so removing the
separate `verify_token` dependency loses no coverage.

### Test change and verification

`tests/unit/test_cache_admin_router.py` updated: overrides
`get_current_user_role` directly rather than `verify_token`, since
`require_role_dep(...)` is a factory that produces a fresh closure per
call and cannot be matched by identity from a second call in test code —
overriding the stable, importable sub-dependency it delegates to is the
correct FastAPI pattern. Added 2 new tests:
`test_non_admin_role_is_rejected_on_every_endpoint` (role="user" → 403 on
all 5 endpoints) and `test_manager_role_is_also_rejected_admin_only`
(role="manager" → 403, confirming the cutoff is genuinely "admin only",
not just "not user").

**Genuine red→green**: reverted the router to its pre-DEC-159 state
(`verify_token` only), re-ran the 6 tests — all 6 failed (the 4
originally-passing tests now got `401` since the reverted setup no longer
overrides `verify_token`; the 2 new role-check tests failed with
`assert 401 == 403`, exactly as predicted). Restored the fix, re-ran — 6/6
PASS.

Full local `tests/unit/` regression after the fix: **3765 passed** (up
from 3763 — the 2 new tests), 4 skipped, 7 xfailed, 3 xpassed, and the same
**1 pre-existing, unrelated failure** already flagged in report 68
(`test_db05_slice4_deferred_8_rls_authority.py`'s stale `ALL_TENANT_TABLES`
count assertion, predating this session, unaffected by either of today's
two closures).

No other test file references this router or depends on its previous
permissive behavior (confirmed via grep across `tests/`).

### What this does not close

This closes the *access* gap (who may call these endpoints at all), not a
*tenant-key-isolation* gap within the shared cache itself. A caller who
legitimately holds "admin" for their own tenant could, in principle, still
reach another tenant's cache key if they can guess its naming scheme
(e.g. `company:<tenant>:<id>`) — that would require key-namespace
enforcement inside `CacheService`/the router, a separate and larger
finding not addressed here. The repeated-failure circuit-breaker
performance item noted alongside this in report 63 is also untouched.

## Deliberate non-claims (both decisions)

- No production/staging access, no write to `salesos_test` or any shared
  database, for either decision.
- Does not change the capability register total from report 57 (these
  items were never counted capability rows — they are audit findings, not
  product capabilities).
- Production remains **NOT APPROVED**; Phase 7 remains **BLOCKED**. Neither
  status is affected by either decision.
- All 3 of this session's originally-pending decisions (DEC-157, DEC-158,
  DEC-159) are now **Accepted — CLOSED**. See report 68 for DEC-157.

## Files changed this session (DEC-158 + DEC-159 scope only)

- `app/modules/cache/router.py`
- `tests/unit/test_cache_admin_router.py`
- `docs/program/decisions/DEC-158-BILLING-TABLES-OWNER-PLANE-RBAC-ACCEPTED.md` (new)
- `docs/program/decisions/DEC-159-CACHE-ROUTER-ADMIN-ROLE-GATE.md` (new)
- `docs/program/DECISION_LOG.md`
