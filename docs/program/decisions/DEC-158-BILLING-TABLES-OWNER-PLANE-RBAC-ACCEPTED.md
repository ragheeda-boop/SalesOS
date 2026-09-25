# DEC-158 — Owner-plane billing tables: accept app-layer RBAC as the isolation boundary, no RLS (Accepted — CLOSED)

> **Status:** **Accepted — CLOSED 2026-09-23.**
> **Date:** 2026-09-23
> **Board:** Backend Platform / Database (SalesOS)
> **Finding:** `project-audit/60_BILLING_TABLES_OWNER_PLANE_RLS_FINDING_2026-09-23.md`
> **Authority:** DEC-085 (canonical tenant-isolation RLS pattern — this DEC is a deliberate, ruled-on exception to it, not a violation) · `11_CAPABILITY_MATRIX.md` §1.6 (existing "Owner-platform vs Tenant-API JWT audiences" two-plane design)
> **Out of scope:** DROP or reshape any table · any RLS migration on these 6 tables · a second Postgres role or connection pool · `feature_ai_copilot` or any unrelated flag

---

## 1. Decision

**Accept option (c) from report 60: formally treat app-layer RBAC
(`require_owner_role_dep("admin")`) as the sole, sufficient isolation
boundary for the 6 owner-plane billing tables** (`subscriptions`,
`usage_meters`, `usage_meter_events`, `dunning_cases`,
`platform_billing_invoices`, `stripe_webhook_events`). **No RLS is added to
these tables.** This is a permanent architectural position, not a temporary
hold pending further work — it is the intended design, now written down.

## 2. Why (the structural reason RLS does not fit here)

Every other tenant table in this codebase is scoped to exactly one tenant
per request, so pinning `app.tenant_id` and adding a
`tenant_id::text = current_setting(...)` policy is a pure correctness
tightening with no functional trade-off (this is exactly DEC-157's
reasoning). These 6 tables are structurally different: the owner-admin
billing/usage dashboard has a **real, already-shipped, intentional**
requirement to read **across all tenants in one query**
(`usage_meter_router.py`'s `tenant_id: uuid.UUID | None = Query(None)`), and
that cross-tenant read runs through the same `salesos_app` Postgres role
(non-superuser, `NOBYPASSRLS`) as every tenant-scoped request. A single
`app.tenant_id` GUC value cannot mean both "this one tenant" and "every
tenant" at the same time — a standard RLS policy would make the owner
dashboard's own cross-tenant listing silently return zero or wrong rows.
Options (a) (a second Postgres role for owner-plane access) and (b) (a
role-aware `OR is_owner_context()` predicate) would both close this
properly, but each is a materially larger, separately-scoped piece of
architecture work — (a) touches connection management and pooling
repo-wide, (b) was already flagged in report 60 as "a wrong implementation
would be a worse hole than today's absence of RLS." Neither is a quick
follow-on to DEC-157; both remain available as future work if the owner
surface's risk profile changes (see §5).

## 3. Confirmation performed before Accept (this session, read-only)

Report 60's original grep (every router/service file importing the 6 ORM
model classes) was re-run and extended to trace two additional import sites
found this session:

- `app/modules/admin/routers/billing.py` and
  `app/modules/admin/routers/tenants.py` (both import
  `SubscriptionService`) — both routers declare
  `dependencies=[Depends(require_owner_role_dep("admin"))]` at the
  `APIRouter(...)` level, same owner-plane gate as every other billing
  router. No new tenant-facing exposure.
- `app/modules/admin/services.py:449` (a lazy `from
  app.modules.billing.service import SubscriptionService` inside a
  tenant-provisioning method) — part of the admin/platform onboarding flow,
  not a tenant-JWT-reachable path.
- Two apparent matches on `SubscriptionModel`/`UsageMeterModel`-adjacent
  names (`app/modules/signal_marketplace/db_models.py`'s
  `SignalSubscriptionModel`, `app/modules/webhooks/repository.py`'s
  `WebhookSubscriptionModel`) were checked and are **unrelated classes** —
  substring false positives from the grep pattern, not references to the
  billing models.

This is, as report 60 already stated, "a reasonably complete but not
formally exhaustive method" (every router/service file that imports the six
ORM model classes) — not a full manual trace of every code path in the
repository. It is sufficient confirmation for this DEC's Accept; it is not
a claim of exhaustive proof.

## 4. What this DEC does and does not authorize

| | |
|---|---|
| Authorizes | Closing report 57/60's open finding as **Accepted, no code change** |
| Authorizes | Citing this DEC as the reason these 6 tables intentionally have no `tenant_isolation_<table>` policy, in any future audit or capability-register pass |
| Does NOT authorize | Any RLS migration on these 6 tables |
| Does NOT authorize | A second Postgres role, connection pool, or GUC convention for owner-plane access |
| Does NOT change | The capability register total (these tables were never a counted capability row; this closes an audit finding, not a product row) |
| Does NOT change | Production approval status (**NOT APPROVED**) or Phase 7 status (**BLOCKED**) — unrelated |

## 5. Residual risk (accepted, not eliminated)

- The one tenant-adjacent read path (`entitlement_resolver.py`'s
  `resolve_entitlements_for_tenant`) has zero database-level backstop — it
  is exactly as isolated as its Python `WHERE tenant_id == tid` clause and
  nothing more. This DEC accepts that as consistent with the rest of this
  finding's scope; it is not a new gap introduced by this decision.
- If a future feature ever adds a **tenant-JWT-gated** (not owner-role-gated)
  route that reads any of these 6 tables, this DEC's acceptance no longer
  holds for that route and must be re-reviewed before shipping it — this
  DEC's safety argument is entirely conditional on every current and future
  read path being owner-role-gated.
- If the owner/admin surface's threat model changes (e.g., a compromised
  owner-admin session becoming a higher-stakes concern than it is today),
  options (a)/(b) from report 60 remain the two available upgrades and
  should be re-evaluated then, not now.

## 6. Records

- Finding: `project-audit/60_BILLING_TABLES_OWNER_PLANE_RLS_FINDING_2026-09-23.md`
- `DECISION_LOG.md` entry: this DEC, filed above DEC-157
- **Not claimed:** any code change, any test written, production readiness,
  or Phase 7 progress
