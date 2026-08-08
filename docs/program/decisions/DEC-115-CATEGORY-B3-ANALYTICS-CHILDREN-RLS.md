# DEC-115 — Category B Slice B3: analytics-children join RLS

> **Status:** **Accepted** — Slice B3 **CLOSED** (execution)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS)  
> **Story:** `S04-CATB-03` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-114 B2 · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** B4–B7 · DB-05 deferred-8 ENABLE RLS · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO

---

## 1. Decision

Ship **additive** Category B join RLS for analytics children only:

| Table | Parent path | Policy |
|---|---|---|
| `analytics_report_executions` | `analytics_reports.id` via `report_id` | `tenant_isolation_analytics_report_executions` |
| `analytics_report_shares` | `analytics_reports.id` via `report_id` | `tenant_isolation_analytics_report_shares` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **53** (47 + B1 + B2 + B3) |
| Alembic | `d3f8a21c9b03` → down `c221d15f8b02` |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql` + `CATEGORY_B3_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

Parent FKs confirmed against ORM (`domains/analytics/infrastructure/models.py`) and migrations `0014_analytics` / `77214759646c_add_missing_registered_model_tables`.

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_analytics_report_executions ON "analytics_report_executions"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "analytics_reports" p
      WHERE p.id = "analytics_report_executions".report_id
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
| Docker `python -m pytest` B3 + POLICY_COUNT + DEC-085 | **7 passed** in 9.78s |
| Live `pg_policies` count after apply | **53** (`analytics_report_executions` + `analytics_report_shares` policies present) |
| Alembic revision | `d3f8a21c9b03` (down `c221d15f8b02`); local DB upgraded via `alembic upgrade head` |
| Validation label | **build validated** (Docker python pytest + policy count evidence) |

---

## 4. Remaining (not this land)

- **B5–B7** READY per DEC-110 (identity / webhooks / admin).  
- **DB-05** Slice 1 CREATE landed DEC-113 — do **not** ENABLE RLS on those 8 from Category B agents.  
- Semgrep alembic `text()` residual expected (DEC-103/105) — do not churn for Semgrep.

---

## 5. Honesty

- **Production GA / External pilot = NO-GO**  
- **CI GREEN not met** (CI-08)  
- Does **not** claim Category B complete or historic “72”  
- Does **not** reopen STORY-02-01
