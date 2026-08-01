# DEC-122 — DB-05 Slice 3: index rename + nullable/type triage

> **Status:** **Accepted** — Slice 3 **CLOSED** (safe additive index fixes); DB-05 program remains **OPEN**  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20  
> **Authority:** DEC-111 Slice 0 P1 clusters · DEC-121 Slice 2 · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** ENABLE RLS on deferred-8 · production / Railway migrate · Prisma · DROP companies dead columns · SET NOT NULL with unknown prod nulls · DEC-085 edits

---

## 1. Decision

Ship **additive / rename-only** Alembic `c9f4a21b6e08` (down `b7e2f65a3f07`) plus a small ORM cleanup on `Opportunity` indexes. **Do not** DROP companies ORM-removed columns this land (**STOP**).

| Pin | Value |
|---|---|
| Alembic head | **`c9f4a21b6e08`** (single head) |
| Authority | Live Docker `pg_indexes` @ tip `0156121` + ORM `__table_args__` / `index=True` |
| RLS | Unchanged — no ENABLE on deferred-8 |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

### Fixed this land

| Cluster | Action |
|---|---|
| `commercial_opportunities` | Free colliding `ix_opportunities_tenant_{stage,status}` → `ix_commercial_opps_*` (0007 names vs commercial ORM); additive `ix_commercial_opps_owner` |
| `opportunities` / `tasks` | `ALTER INDEX` rename `ix_rev_*` → `ix_*` (6; stage rename after commercial free) |
| `webhook_subscriptions` / `webhook_deliveries` | Rename short names → ORM `index=True` defaults (`…_tenant_id`, `…_subscription_id`) |
| `scheduled_jobs` | Rename `ix_scheduled_jobs_next_run` → `ix_scheduled_jobs_next_run_at` |
| `workflow_*` | Drop redundant short-name twins when `*_id` indexes already exist (3) |
| `notifications` | Additive CREATE `ix_notifications_user_read`, `ix_notifications_tenant_type` |
| `tasks` | Additive CREATE `ix_tasks_company_id` |
| ORM `Opportunity` | Remove bogus `ix_opportunities_tenant_status` (same cols as stage; no `status` column); drop `index=True` on `company_id` so only `ix_opportunities_company` remains |

### Deferred / STOP (documented)

| Item | Why STOP |
|---|---|
| DROP `companies.branch_count`, `revenue_prev_year`, `tsv`, `parent_company_id`, `search_vector` | **Destructive.** `search_vector` is **live-used** by search runtime/domain FTS (not dead). `parent_company_id` still referenced in company service SQL. Local Docker row counts 0 ≠ prod safety. Needs dedicated DEC + data inventory before DROP. |
| Contacts composite vs single-column index naming | DB has `ix_contacts_tenant_email` / `tenant_company`; ORM `index=True` wants per-column names. Adding singles is optional noise; leave for Slice 4+ naming pass. |
| Broad nullable SET NOT NULL (workflow / notifications / scheduled_jobs defaults) | ORM already allows null on defaulted columns matching local DDL; tightening NOT NULL needs prod null inventory — defer. |
| Commercial `opportunity_id` UUID vs VARCHAR FK | Residual from DEC-121 — not index work. |

---

## 2. Validation

| Check | Result |
|---|---|
| Docker `alembic heads` | `c9f4a21b6e08` single head |
| Docker `alembic upgrade head` (local compose only) | PASS (rename/create/drop) |
| Narrow unit tests | Docker `pytest` Slice 3 + DEC-085 guard (see land commit) |
| Production / Railway migrate | **Not run** |
| Full `alembic check` | **Not re-run** this land |
| Label | **build validated** (narrow Docker pytest + local upgrade) |

**Production GO not claimed. CI GREEN not met. R-14 GO not claimed.**

---

## 3. Records

- Board DB-05 → Slice 3 COMPLETE; next Slice 4+ (companies dead-column DEC / contacts index naming / governed RLS for deferred-8).  
- `EXECUTION_DAG.md` / `RISK_REGISTER.md` R-20 next-action.  
- `DECISION_LOG.md` DEC-122.
