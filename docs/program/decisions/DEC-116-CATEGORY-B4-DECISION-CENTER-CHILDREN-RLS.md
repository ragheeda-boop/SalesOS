# DEC-116 — Category B Slice B4: decision-center-children join RLS

> **Status:** **Accepted** — Slice B4 **CLOSED** (execution)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS / AQLIYA)  
> **Story:** `S04-CATB-04` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-115 B3 · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** B5–B7 · DB-05 deferred-8 ENABLE RLS · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO

---

## 1. Decision

Ship **additive** Category B join RLS for decision-center children only:

| Table | Parent path | Policy |
|---|---|---|
| `decision_center_audits` | `decision_center_decisions.id` via `decision_id` | `tenant_isolation_decision_center_audits` |
| `decision_center_feedback` | `decision_center_decisions.id` via `decision_id` | `tenant_isolation_decision_center_feedback` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **55** (47 + B1 + B2 + B3 + B4) |
| Alembic | `e4b9c32d0c04` → down `d3f8a21c9b03` |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql(..., cast_parent_pk_to_text=True)` + `CATEGORY_B4_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

Parent FKs confirmed against ORM (`domains/decision_center/postgres_repo.py`) and migration `0038_consolidate_init_db_tables`. Parent PK is UUID (`BaseModel`); child `decision_id` is String(64) — join uses `p.id::text` (same cast as repo feedback join).

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_decision_center_audits ON "decision_center_audits"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "decision_center_decisions" p
      WHERE p.id::text = "decision_center_audits".decision_id
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
| Docker `python -m pytest` B4 + POLICY_COUNT + DEC-085 | **9 passed** in 8.89s |
| Live `pg_policies` count after apply | **55** (`decision_center_audits` + `decision_center_feedback` policies present) |
| Alembic revision | `e4b9c32d0c04` (down `d3f8a21c9b03`); local DB upgraded via `alembic upgrade head` |
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
