# DEC-110 — Category B RLS canonical inventory + execution slices (planning CLOSE)

> **Status:** **Accepted** — planning package **CLOSED**; execution slices **READY** (not shipped)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS / AQLIYA)  
> **Authority:** DEC-044 Option B · DEC-DRAFT-STORY-02-01-RLS-72 (superseded) · `scripts/generate_rls_policies.py` · R-25 / R-09 / R-20 / DB-05 · DEC-085 (`set_config`) · DEC-107 swarm READY  
> **Out of scope this land:** Alembic RLS DDL churn · ENABLE RLS on DB-05 tables · reopening STORY-02-01 / `POLICY_COUNT` 47 · CI-14 / CI-22 / CI-08 · Railway · Production GO

---

## 1. Decision

Close the Sprint 04 **Category B RLS planning** story with a **pinned canonical inventory** and **recommended execution slices**. Do **not** ship join-policy SQL in this land.

| Pin | Value |
|---|---|
| Category A live (governed) | **`ALL_TENANT_TABLES` = 47** — STORY-02-01 CLOSED (DEC-044). **Do not reopen.** |
| Category A deferred | **8** tables with ORM `tenant_id` but **no** governed RLS yet — wait on **DB-05 / R-09 / R-20** |
| Category B (join / parent-FK) | **12** tables — no own `tenant_id`; isolate via parent already under Category A (or identity `users`) |
| Owner / global (not Category B) | Intentionally **excluded** from tenant RLS count (STORY-02-04 / Owner Platform) |
| Historic “72” | **Retired** — evidence-backed program total ≈ **47 + 12 + 8 = 67** tenant-relevant rows (not 72; not a ship gate) |

**Validation label:** **docs / light validated** (ORM scan + migration presence + DEC-044 cross-check). No Docker pytest this land.

---

## 2. Inventory method (light validated)

1. Governed Category A list = `salesos/backend/scripts/generate_rls_policies.py` → `ALL_TENANT_TABLES` (**47**).  
2. ORM scan of `app/`, `domains/`, `runtime/` for `__tablename__` + `tenant_id` (UBOM stubs excluded).  
3. Migration presence via Alembic `create_table` (baseline / domain migrations).  
4. Cross-check DEC-044 / draft: 9 ORM gaps after `company_features` → **8** true Category A deferred + **1** false-positive (`webhook_deliveries` is Category B via `subscription_id`).

---

## 3. Category A — live (unchanged)

**47** policies. Adversarial suites assert `POLICY_COUNT = 47` (S04-01 / S04-05 / S04-06). Generator comment remains: tables without `tenant_id` deferred to Category B.

**Hard stop:** do not edit `get_db()` tenant GUC — must stay `SELECT set_config('app.tenant_id', :tenant_id, true)` (**DEC-085**). Never `SET LOCAL`.

---

## 4. Category A deferred — DB-05 / R-09 (not Category B)

ORM has `tenant_id`; **not** in `ALL_TENANT_TABLES`; CREATE TABLE missing or outside governed RLS path. **No ENABLE RLS until DB-05 lands schema.**

| # | Table | Notes |
|---|---|---|
| 1 | `admin_licenses` | Admin billing |
| 2 | `admin_invoices` | Admin billing |
| 3 | `admin_transactions` | Admin billing |
| 4 | `admin_ai_costs` | Nullable `tenant_id` |
| 5 | `admin_jobs` | Nullable `tenant_id` |
| 6 | `webhook_endpoints` | Workflow domain |
| 7 | `scoring_scorecards` | Scoring |
| 8 | `revenue_analytics_snapshots` | Revenue analytics |

These remain **R-09 / R-20 / DB-05** ownership — **not** Category B execution slices.

---

## 5. Category B — canonical join / parent-FK inventory (**12**)

No `tenant_id` on child; isolation via EXISTS/join to parent that is Category A (or `users` → tenant).

| # | Child table | Parent path | Migration evidence |
|---|---|---|---|
| 1 | `branches` | `companies.id` | `0001_baseline` |
| 2 | `licenses` | `companies.id` | `0001_baseline` (+ indexes `0028`) |
| 3 | `commercial_activities` | `commercial_activity_sessions.id` | `0007_commercial_domain` |
| 4 | `commercial_quote_lines` | `commercial_quotes.id` | `0007_commercial_domain` |
| 5 | `analytics_report_executions` | `analytics_reports.id` (`report_id`) | `0014_analytics` |
| 6 | `analytics_report_shares` | `analytics_reports.id` (`report_id`) | `77214759646c_add_missing_registered_model_tables` |
| 7 | `decision_center_audits` | `decision_center_decisions` (`decision_id`) | `0038_consolidate_init_db_tables` |
| 8 | `decision_center_feedback` | `decision_center_decisions` (`decision_id`) | `0038_consolidate_init_db_tables` |
| 9 | `password_reset_tokens` | `users.id` | `0012_refresh_token_tables` |
| 10 | `refresh_token_families` | `users.id` | `0012_refresh_token_tables` |
| 11 | `webhook_deliveries` | `webhook_subscriptions.id` (`subscription_id`) | `0039_webhook_tables` |
| 12 | `admin_role_permissions` | `admin_roles.id` | `0037_admin_phase16` — **nullable** parent `tenant_id`; design carefully |

**Policy template (execution only — not this land):**

```sql
-- Example: commercial_quote_lines → commercial_quotes
CREATE POLICY tenant_isolation_commercial_quote_lines ON "commercial_quote_lines"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "commercial_quotes" p
      WHERE p.id = commercial_quote_lines.quote_id
        AND p.tenant_id::text = current_setting('app.tenant_id', true)
    )
  )
  WITH CHECK ( /* identical EXISTS */ );
```

FORCE ROW LEVEL SECURITY required (same Category A rationale). Fail-closed if GUC unset.

---

## 6. Explicitly **not** Category B (Owner / global / root)

Do **not** fold into Category B count or Sprint 04 join-policy slices:

| Table | Why excluded |
|---|---|
| `tenants` | Root plane |
| `sso_connections` | Owner Platform (STORY-02-04) |
| `marketplace_plugins` | Owner Platform |
| `marketplace_lifecycle_events` | Owner / plugin lifecycle |
| `feature_definitions` / `feature_values` | Owner Platform |
| `admin_plans` / `admin_permissions` / `admin_feature_flags` / `admin_health_snapshots` | Global / owner admin |
| `sources` | Reference catalog (no tenant) |
| `token_blacklist` | JTI TTL store — no tenant/user FK; separate security design if needed |

---

## 7. Recommended execution slices (post-planning)

| Slice | ID | Scope | Preconditions | Suggested AC |
|---|---|---|---|---|
| **B0** | *(this DEC)* | Inventory + slices pinned | — | **CLOSED** by DEC-110 |
| **B1** | `S04-CATB-01` | Company children: `branches`, `licenses` | Category A `companies` intact; DEC-085 | **CLOSED DEC-112** — `b110c04e7a01`; `POLICY_COUNT` **49** |
| **B2** | `S04-CATB-02` | Commercial children: `commercial_activities`, `commercial_quote_lines` | B1 or parallel if disjoint migration | **CLOSED DEC-114** — `c221d15f8b02`; `POLICY_COUNT` **51** |
| **B3** | `S04-CATB-03` | Analytics children: `analytics_report_executions`, `analytics_report_shares` | Parents in Category A | POLICY_COUNT **+2** |
| **B4** | `S04-CATB-04` | Decision Center children: `decision_center_audits`, `decision_center_feedback` | Parents in Category A | POLICY_COUNT **+2** |
| **B5** | `S04-CATB-05` | Identity join: `password_reset_tokens`, `refresh_token_families` | Parent `users` RLS live | POLICY_COUNT **+2**; careful auth-path tests |
| **B6** | `S04-CATB-06` | Webhooks: `webhook_deliveries` | Parent `webhook_subscriptions` RLS live | POLICY_COUNT **+1** |
| **B7** | `S04-CATB-07` | Admin join: `admin_role_permissions` | Design for nullable `admin_roles.tenant_id` | POLICY_COUNT **+1** or defer if owner-global roles dominate |

**Ordering preference:** B1 → B2 → B6 (high tenant data surface) before B5/B7 (auth/admin edge cases). B3/B4 may interleave if migrations confirmed.

**Out of Category B execution:** all eight §4 tables (DB-05 first).

---

## 8. Honesty / non-goals

- **Production GA / External pilot = NO-GO**
- **CI GREEN not met** (CI-08 GHCR ops-blocked)
- Phase 0 (DEC-008) exit = **GO** already (DEC-016) — this package does **not** change that, and does **not** unlock production GO
- Does **not** claim RLS “complete on 72 tables”
- Does **not** reopen STORY-02-01
- Does **not** churn alembic RLS for Semgrep (DEC-103 / DEC-105 residual)
- Parallel agents own CI-14 / CI-22 residuals — **no overlap**

---

## 9. Program effects

- Mint this Accepted DEC; mark Category B **planning** CLOSED.  
- Update `EXECUTION_DAG.md` / board Progress crumbs.  
- Update R-25 residual next-action → execution slices B1+ (inventory pinned DEC-110).  
- Optional tiny doc-only: generator comment may cite DEC-110 (no SQL churn required this land).
