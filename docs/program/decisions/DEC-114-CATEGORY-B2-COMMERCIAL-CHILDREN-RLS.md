# DEC-114 — Category B Slice B2: commercial-children join RLS

> **Status:** **Accepted** — Slice B2 **CLOSED** (execution)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS / AQLIYA)  
> **Story:** `S04-CATB-02` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-112 B1 · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** B3–B7 · DB-05 deferred-8 ENABLE RLS · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO

---

## 1. Decision

Ship **additive** Category B join RLS for commercial children only:

| Table | Parent path | Policy |
|---|---|---|
| `commercial_activities` | `commercial_activity_sessions.id` via `session_id` | `tenant_isolation_commercial_activities` |
| `commercial_quote_lines` | `commercial_quotes.id` via `quote_id` | `tenant_isolation_commercial_quote_lines` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **51** (47 + B1 + B2) |
| Alembic | `c221d15f8b02` → down `b110c04e7a01` |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql` + `CATEGORY_B2_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

Parent FKs confirmed against ORM (`domains/commercial/infrastructure/models.py`) and migration `0007_commercial_domain`.

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_commercial_activities ON "commercial_activities"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "commercial_activity_sessions" p
      WHERE p.id = "commercial_activities".session_id
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
| Docker `pytest` B2 + B1 + POLICY_COUNT + DEC-085 | **10 passed** (`test_adversarial_rls_category_b{1,2}`, S04-01/06 intact, `test_dec085_set_config_guard`) |
| Live `pg_policies` count after apply | **51** |
| Alembic revision | `c221d15f8b02` (down `b110c04e7a01`) |
| Validation label | **build validated** (Docker python pytest + policy count evidence) |

---

## 4. Remaining (not this land)

- **B3–B7** READY per DEC-110 (analytics / decision / identity / webhooks / admin).  
- **DB-05** Slice 1 CREATE landed DEC-113 — do **not** ENABLE RLS on those 8 from Category B agents.  
- Semgrep alembic `text()` residual expected (DEC-103/105) — do not churn for Semgrep.

---

## 5. Honesty

- **Production GA / External pilot = NO-GO**  
- **CI GREEN not met** (CI-08)  
- Does **not** claim Category B complete or historic “72”  
- Does **not** reopen STORY-02-01
