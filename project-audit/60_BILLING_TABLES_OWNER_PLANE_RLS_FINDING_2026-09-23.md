# Owner-Plane Billing Tables — Confirmed Finding, No Action Taken — 2026-09-23

## What this report is

A different track from report 59/DEC-157 (the five live runtime engines).
This investigates the other still-open item from report 57 §3: the 6
owner-plane billing tables (`subscriptions`, `usage_meters`,
`usage_meter_events`, `dunning_cases`, `platform_billing_invoices`,
`stripe_webhook_events`) that carry `tenant_id` but have no RLS. Read-only
investigation only; no code, migration, or database was touched.

Also done this round: removed the stray, untracked
`0afbf3e6ae53_enable_rls_all_tenant_tables.py.bak` file flagged in report 58
("Next code-reachable work" item 3) — pure clutter, not a live revision,
confirmed via git status to have left no tracked diff. A stale
`.git/index.lock` (dated 2026-09-22 10:22, 0 bytes, no running git process)
was also cleared to unblock git commands; this was a leftover lock file, not
a decision.

## What was found

Unlike the 14 tables in report 59 (which turned out to be a real,
un-mitigated gap), these 6 billing tables have a **confirmed, deliberate,
app-layer access-control design** that a blind RLS migration would actively
break, not just risk breaking:

1. **Every non-webhook billing router is owner-role-gated at the
   framework layer**, not tenant-JWT-gated: `usage_meter_router.py`,
   `dunning_router.py`, `proration_router.py`, and `stripe_router.py`'s
   `owner_router` all declare
   `dependencies=[Depends(require_owner_role_dep("admin"))]`. This is a
   distinct authorization plane from every tenant-facing router in this
   codebase.
2. **The owner-admin usage endpoint deliberately supports cross-tenant
   reads**: `usage_meter_router.py` accepts an *optional*
   `tenant_id: uuid.UUID | None = Query(None)` — when omitted, an
   owner-admin can list usage across all tenants. This is not an oversight;
   it is the entire point of a platform billing/usage dashboard.
3. **That cross-tenant read runs through the same restricted DB role as
   ordinary tenant traffic.** `get_db_session` → `get_db()` →
   `async_session()` → `engine = create_async_engine(settings.app_database_url, ...)`
   — the same `salesos_app` role (non-superuser, `NOBYPASSRLS`) used
   everywhere else in this codebase. There is no separate "owner" Postgres
   role today. **Adding the standard `tenant_isolation_<table>` policy
   (`tenant_id::text = current_setting('app.tenant_id', true)`) to these
   tables would make the owner-admin's own cross-tenant listing endpoint
   return zero or wrong rows**, because no single `app.tenant_id` GUC value
   can represent "all tenants."
4. **The one tenant-adjacent read path found** —
   `app/modules/admin/entitlement_resolver.py`'s
   `resolve_entitlements_for_tenant(tenant_id=...)`, which queries
   `SubscriptionModel` filtered by `WHERE tenant_id == tid` — takes its
   `tenant_id` from the caller (the entitlement/quota-enforcement path for
   the *authenticated tenant's own* request), not from unauthenticated or
   cross-tenant-controllable input. No direct exploit path was found in this
   investigation, but this path also has zero database-level backstop today
   — it is exactly as isolated as its Python `WHERE` clause and nothing
   more.
5. **The public exception, `POST /billing/stripe/webhook`, is authenticated
   correctly** — by Stripe signature verification
   (`verify_stripe_signature`), not JWT/owner-role, which is the right
   mechanism for a webhook receiver, not a gap.
6. All 6 tables have normal Declarative ORM classes in
   `app/modules/billing/models.py` (`SubscriptionModel`,
   `UsageMeterModel`, `UsageMeterEventModel`, `DunningCaseModel`,
   `PlatformBillingInvoiceModel`, `StripeWebhookEventModel`) — unlike report
   59's 14 tables, these are not "orphan" raw-SQL tables; they are normal,
   fully-modeled, just RLS-exempt.

## Why the standard fix (report 58's pattern, or report 59/DEC-157's
sequence) does not apply here

Report 58's fix worked because the two tables already had a policy and were
already implicitly GUC-compatible — pure hardening, zero behavior change.
Report 59/DEC-157's proposed fix works because those five runtime engines
have **no legitimate cross-tenant read requirement** — every call site
genuinely should be scoped to one tenant, so pinning the GUC and adding RLS
is a pure correctness fix with no functional trade-off once sequenced
correctly.

**This case is structurally different**: there is a real, intentional,
already-shipped cross-tenant read requirement (the owner-admin billing
dashboard), and it runs through the one Postgres role this whole codebase
uses for everything. A standard per-tenant RLS policy cannot serve both "an
owner admin needs to see every tenant's usage" and "a tenant must never see
another tenant's usage" through the same database role at the same time.
Closing this properly would need one of:

- **(a) A second, distinct Postgres role** for owner-platform database
  access (with its own RLS-exempt or role-scoped policy), separate from the
  `salesos_app` role tenant traffic uses — a real architectural change
  touching connection management, not just these 6 tables.
- **(b) A role-aware RLS predicate** (e.g. `tenant_id::text = current_setting(...) OR is_owner_context()`)
  where `is_owner_context()` is backed by something Postgres can actually
  verify (a second GUC set only by the owner-gated code path, itself needing
  careful review so a tenant-scoped request can never set it) — more
  fragile than (a), and a wrong implementation would be a worse hole than
  today's absence of RLS.
- **(c) Formally accept the current design** — app-layer RBAC
  (`require_owner_role_dep`) as the only gate for owner-plane billing data,
  with no DB-level RLS on these 6 tables, on the basis that this is how the
  codebase already treats "Owner-platform vs Tenant-API JWT audiences" as a
  distinct security plane elsewhere (per `11_CAPABILITY_MATRIX.md` §1.6) —
  and instead invest any further hardening effort in confirming *no*
  tenant-facing route ever reaches these 6 tables (this investigation found
  none, but did not exhaustively trace every code path in the repository).

## Recommendation (not decided — this is the user's call)

Option (c) is the lowest-risk and matches this codebase's existing explicit
two-plane design. Options (a)/(b) are real security improvements but are
each a bigger, separately-scoped piece of architecture work, not a quick
follow-on to report 58/DEC-157. This report does not choose between them.

## Deliberate non-claims

- No code, test, or migration was written or run for this finding. No
  ephemeral database was used (this was pure static/code investigation).
- This is not an exhaustive trace of every code path that could reach these
  6 tables — it covers every router/service file that imports the six ORM
  model classes, found via repository-wide grep, which is a reasonably
  complete but not formally exhaustive method.
- This does not change the capability register total from report 57
  (124/132) — these tables were already listed there as an undecided,
  not-closed finding; this report adds evidence, not a new row or a status
  change.
- Production remains **NOT APPROVED**; Phase 7 remains **BLOCKED**. Neither
  status is affected.

## Housekeeping this round

- Deleted `salesos/backend/app/alembic/versions/0afbf3e6ae53_enable_rls_all_tenant_tables.py.bak`
  (untracked stray file; no git diff results from its removal).
- Cleared a stale `.git/index.lock` (0 bytes, dated 2026-09-22 10:22, no
  running git process at time of removal) that was blocking git commands in
  this session.
