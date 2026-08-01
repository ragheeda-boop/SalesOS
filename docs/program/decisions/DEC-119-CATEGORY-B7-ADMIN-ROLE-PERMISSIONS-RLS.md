# DEC-119 — Category B Slice B7: admin_role_permissions join RLS

> **Status:** **Accepted** — Slice B7 **CLOSED** (execution); Category B execution track **COMPLETE** (B1–B7)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS / AQLIYA)  
> **Story:** `S04-CATB-07` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-118 B6 · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DB-05 deferred-8 ENABLE RLS (incl. admin billing tables) · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO · permissive NULL-tenant bypass

---

## 1. Decision

Ship **additive** Category B join RLS for admin role-permissions only:

| Table | Parent path | Policy |
|---|---|---|
| `admin_role_permissions` | `admin_roles.id` via `role_id` | `tenant_isolation_admin_role_permissions` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **59** (47 + B1 + B2 + B3 + B4 + B5 + B6 + B7) |
| Alembic | `b7e2f65a3f07` → down `a6d1e54f2e06` |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql()` + `CATEGORY_B7_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

Parent FK confirmed against ORM (`RolePermissionModel.role_id` → `RoleModel.id`) and migration `0037_admin_phase16`. Both columns are `String(100)` — no cast.

### Nullable-tenant / global-admin note (careful; do not weaken)

- Parent `admin_roles.tenant_id` is **nullable**. Seeded / owner-created roles often omit `tenant_id` (global catalog).
- Category A already fail-closes those rows under a tenant GUC (`tenant_id::text = current_setting(...)` — NULL never matches).
- B7 join uses the **same** equality via EXISTS — fail-closed for NULL-tenant parents.
- **Rejected:** `OR p.tenant_id IS NULL` (or similar) — would leak global/owner role permission maps to every tenant session.
- Owner / BYPASSRLS paths remain out of band (same class as other FORCE policies). Not a permissive app-session bypass.

DEC-110 AC alternative (“defer if owner-global roles dominate”) was considered; deferred would leave the child unprotected while the parent is already Category A. Shipping the matching fail-closed join closes the Category B inventory without inventing a bypass.

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_admin_role_permissions ON "admin_role_permissions"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "admin_roles" p
      WHERE p.id = "admin_role_permissions".role_id
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
| Docker `python -m pytest` B7 + POLICY_COUNT + DEC-085 | **5 passed** in 16.84s |
| Live `pg_policies` count after apply | **59** (`admin_role_permissions` policy present; deferred-8 admin billing still 0) |
| Alembic revision | `b7e2f65a3f07` (down `a6d1e54f2e06`); local DB upgraded via `alembic upgrade head` |
| Validation label | **build validated** (Docker python pytest + policy count evidence) |

---

## 4. Remaining (not this land)

- **Category B execution B1–B7 COMPLETE** — no further Cat B join slices.  
- **DB-05** Slice 1 CREATE landed DEC-113 — do **not** ENABLE RLS on those 8 from Category B agents.  
- Semgrep alembic `text()` residual expected (DEC-103/105) — do not churn for Semgrep.

---

## 5. Honesty

- **Production GA / External pilot = NO-GO**  
- **CI GREEN not met** (CI-08)  
- Does **not** claim historic “72” or DB-05 RLS complete  
- Does **not** reopen STORY-02-01
