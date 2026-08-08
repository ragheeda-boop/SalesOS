# DEC-117 — Category B Slice B5: identity-token-children join RLS

> **Status:** **Accepted** — Slice B5 **CLOSED** (execution)  
> **Date:** 2026-08-01  
> **Board:** Architecture / Database (SalesOS)  
> **Story:** `S04-CATB-05` (DEC-110 §7)  
> **Authority:** DEC-110 inventory · DEC-116 B4 · DEC-044 Category A 47 intact · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** B6–B7 · DB-05 deferred-8 ENABLE RLS · reopening STORY-02-01 / `ALL_TENANT_TABLES` · CI-08 · Production GO · auth-path bypass policies

---

## 1. Decision

Ship **additive** Category B join RLS for identity token children only:

| Table | Parent path | Policy |
|---|---|---|
| `password_reset_tokens` | `users.id` via `user_id` | `tenant_isolation_password_reset_tokens` |
| `refresh_token_families` | `users.id` via `user_id` | `tenant_isolation_refresh_token_families` |

| Pin | Value |
|---|---|
| Category A `ALL_TENANT_TABLES` | **47** unchanged (DEC-044) |
| Live `tenant_isolation_%` policies | **57** (47 + B1 + B2 + B3 + B4 + B5) |
| Alembic | `f5c0d43e1d05` → down `e4b9c32d0c04` |
| Helper | `scripts/generate_rls_policies.generate_join_policy_sql()` + `CATEGORY_B5_JOIN_TABLES` |
| DEC-085 | **Intact** — `get_db()` still `SELECT set_config('app.tenant_id', :tenant_id, true)` |

Parent FKs confirmed against ORM (`app/modules/identity/models.py`) and migration `0012_refresh_token_tables` (`020cfcbab7b4`). Both child `user_id` columns and `users.id` are UUID — no cast.

### Auth-path note (careful; do not weaken)

- JWT refresh rotation supplies `tenant_id` → middleware sets ContextVar → `get_db` `set_config` → own-tenant family rows visible.
- Unset `app.tenant_id` remains **fail-closed** (including `token_hash` lookup). No permissive “auth bypass” policy added — that would weaken tenant isolation.
- Unauthenticated password-reset by hash alone shares the same fail-closed class as Category A `users` email lookup without tenant GUC; fixing that login/bootstrap path is **out of scope** for B5 (would be a separate auth design, not RLS weaken).

---

## 2. Policy shape

```sql
CREATE POLICY tenant_isolation_password_reset_tokens ON "password_reset_tokens"
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM "users" p
      WHERE p.id = "password_reset_tokens".user_id
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
| Docker `python -m pytest` B5 + POLICY_COUNT + DEC-085 | **10 passed** in 5.47s |
| Live `pg_policies` count after apply | **57** (`password_reset_tokens` + `refresh_token_families` policies present) |
| Alembic revision | `f5c0d43e1d05` (down `e4b9c32d0c04`); local DB upgraded via `alembic upgrade head` |
| Validation label | **build validated** (Docker python pytest + policy count evidence) |

---

## 4. Remaining (not this land)

- **B6–B7** READY per DEC-110 (webhooks / admin).  
- **DB-05** Slice 1 CREATE landed DEC-113 — do **not** ENABLE RLS on those 8 from Category B agents.  
- Semgrep alembic `text()` residual expected (DEC-103/105) — do not churn for Semgrep.

---

## 5. Honesty

- **Production GA / External pilot = NO-GO**  
- **CI GREEN not met** (CI-08)  
- Does **not** claim Category B complete or historic “72”  
- Does **not** reopen STORY-02-01
