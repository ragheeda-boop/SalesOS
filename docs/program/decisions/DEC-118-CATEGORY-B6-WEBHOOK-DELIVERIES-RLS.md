# DEC-118 — Category B Slice B6: webhook-deliveries join RLS

> **Status:** **Accepted** — Slice B6 **CLOSED** (execution)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS)  
> **Story:** `S04-CATB-06` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-117 B5 · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** B7 · DB-05 deferred-8 ENABLE RLS (incl. `webhook_endpoints`) · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO

---

## 1. Decision

Ship **additive** Category B join RLS for webhook deliveries only:

| Table | Parent path | Policy |
|---|---|---|
| `webhook_deliveries` | `webhook_subscriptions.id` via `subscription_id` | `tenant_isolation_webhook_deliveries` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **58** (47 + B1 + B2 + B3 + B4 + B5 + B6) |
| Alembic | `a6d1e54f2e06` → down `f5c0d43e1d05` |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql()` + `CATEGORY_B6_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

Parent FK confirmed against ORM (`WebhookDeliveryModel.subscription_id` → `WebhookSubscriptionModel.id`) and migration `0039_webhook_tables`. Both columns are `String(36)` — no cast.

**Not the parent:** deferred-8 `webhook_endpoints` (DB-05 Slice 1 CREATE, DEC-113) remains without ENABLE RLS. B6 join path is exclusively via Category A `webhook_subscriptions`.

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_webhook_deliveries ON "webhook_deliveries"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "webhook_subscriptions" p
      WHERE p.id = "webhook_deliveries".subscription_id
        AND p.tenant_id::text = current_setting('app.tenant_id', true)
    )
  )
  WITH CHECK ( /* identical EXISTS */ );
```

FORCE ROW LEVEL SECURITY required. Fail-closed if GUC unset.

---

## 3. Validation

| Check | Result |
|---|---|
| Docker `python -m pytest` B6 + POLICY_COUNT + DEC-085 | **5 passed** in 2.98s |
| Live `pg_policies` count after apply | **58** (`webhook_deliveries` policy present; `webhook_endpoints` still 0) |
| Alembic revision | `a6d1e54f2e06` (down `f5c0d43e1d05`); local DB upgraded via `alembic upgrade head` |
| Validation label | **build validated** (Docker python pytest + policy count evidence) |

---

## 4. Remaining (not this land)

- **B7** READY per DEC-110 (`admin_role_permissions`; nullable parent design).  
- **DB-05** Slice 1 CREATE landed DEC-113 — do **not** ENABLE RLS on those 8 from Category B agents.  
- Semgrep alembic `text()` residual expected (DEC-103/105) — do not churn for Semgrep.

---

## 5. Honesty

- **Production GA / External pilot = NO-GO**  
- **CI GREEN not met** (CI-08)  
- Does **not** claim Category B complete or historic “72”  
- Does **not** reopen STORY-02-01
