# DEC-112 — Category B Slice B1: company-children join RLS (`branches`, `licenses`)

> **Status:** **Accepted** — Slice B1 **CLOSED** (execution)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS / AQLIYA)  
> **Story:** `S04-CATB-01` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** B2–B7 · DB-05 deferred-8 ENABLE RLS · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO

---

## 1. Decision

Ship **additive** Category B join RLS for company children only:

| Table | Parent path | Policy |
|---|---|---|
| `branches` | `companies.id` via `company_id` | `tenant_isolation_branches` |
| `licenses` | `companies.id` via `company_id` | `tenant_isolation_licenses` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **49** (47 + B1) |
| Alembic | `b110c04e7a01` → down `b8d4f02a1c06` (rebased after DEC-113 Slice 1) |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql` + `CATEGORY_B1_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

`commercial_activities` remains **B2** (parent `commercial_activity_sessions`) — not this slice.

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_branches ON "branches"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "companies" p
      WHERE p.id = "branches".company_id
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
| Docker one-off `pytest` B1 + POLICY_COUNT + DEC-085 | **7 passed** in 6.34s |
| Live `pg_policies` count after apply | **49** (`branches` + `licenses` policies present) |
| Alembic revision | `b110c04e7a01` (down `b8d4f02a1c06` after DEC-113 rebase); local DB stamped after SQL apply (same DDL as migration) |
| Validation label | **build validated** (Docker poetry/python pytest + policy count evidence) |

---

## 4. Remaining (not this land)

- **B2–B7** READY per DEC-110 (commercial / analytics / decision / identity / webhooks / admin).  
- **DB-05** Slice 1 CREATE landed DEC-113 — do **not** ENABLE RLS on those 8 from Category B agents.  
- Semgrep alembic `text()` residual expected (DEC-103/105) — do not churn for Semgrep.

---

## 5. Honesty

- **Production GA / External pilot = NO-GO**  
- **CI GREEN not met** (CI-08)  
- Does **not** claim Category B complete or historic “72”  
- Does **not** reopen STORY-02-01
