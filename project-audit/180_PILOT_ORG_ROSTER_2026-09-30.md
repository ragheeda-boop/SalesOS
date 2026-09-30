# 180 — Pilot org roster: recorded, not applied (no matching accounts)

**Date:** 2026-09-30
**Scope:** Record the real org roster. Apply it only to existing accounts that clearly match.
**Outcome:** No roster person and no `muhide` tenant exists in any allowed database. **No database was written.**
Production `salesos` was not connected to.

---

## 1. Roster (as given by the owner)

| Person | Role | Tenant | Reports to |
|---|---|---|---|
| ragheed | Platform owner (`users.is_platform_owner = true`), the only one | — | — |
| muhide | Tenant company | — | — |
| sultan | Tenant `admin` of muhide only; **not** platform owner | muhide | — |
| ibrahem | `user` | muhide | sultan |
| feras | `user` | muhide | sultan |
| shaher | `user` | muhide | sultan |
| maria | `user` | muhide | shaher |
| nojood | `user` | muhide | shaher |

## 2. Identity model (inspected, not changed)

- The role is stored as a single string, `users.role` (default `user`). There is no roles or user_roles table. `IdentityService.update_user_role` sets it.
- Platform owner is `users.is_platform_owner` (migration `b2c3d4e5f6a8`, default false). No API sets it; an operator must set it directly.
- **There is no manager or reports-to field on `users`.** `relationships/models.py` has a `reports_to` edge, but it links commercial contacts, not users.
- Reporting lines are therefore recorded **in this report only**. No migration was added. No org-chart schema was invented.

## 3. Search (read-only, `BEGIN READ ONLY … ROLLBACK`, `current_database()` asserted)

| Database | Users | `muhide` tenant | Roster matches | Notes |
|---|---:|---|---:|---|
| `salesos_test` | 0 (20 tenants) | none | 0 | Alembic `a1b2c3d4e5f7`: behind `b2c3d4e5f6a8`, so no `is_platform_owner` column |
| `b03_test_a_fresh` | 0 | none | 0 | |
| `b03_test_b_prod_state` | 0 | none | 0 | |
| `salesos_restore_drill_eab003` | 17 | none | 0 | Restore-drill copy; not a live target anyway |
| `salesos_restore_drill_offsite` | no `users` table | — | — | |
| `salesos_test_er_pipeline` | no `users` table | — | — | |
| `salesos` | **not connected** | — | — | Production; forbidden |

Matching was case-insensitive on email and full name for all 7 names, and on tenant name, slug and domain for `muhide`.

## 4. What was applied

**Nothing.** No match was unique and clear, because nobody matched at all. The following were not done:

- set `is_platform_owner`;
- changed any role;
- created any user or tenant.

No email or password was guessed.

## 5. Gaps (for the owner or operator)

1. **The accounts do not exist.** Each person must be created through real self-registration or invite:
   - sultan registers or is invited as tenant `admin` of muhide;
   - sultan then invites ibrahem, feras and shaher as `user`;
   - maria and nojood are invited as `user`, since shaher is a `user` and holds no `user:CREATE`.
2. **The `muhide` tenant does not exist locally.** It is created when sultan self-registers; the first registrant of a new tenant becomes its `admin`.
3. **ragheed's platform-owner flag** must be set by an operator in the target environment, after migration `b2c3d4e5f6a8` is applied there and after ragheed's account exists. Until then, owner login works for nobody (report 179).
4. **The local test databases are behind `b2c3d4e5f6a8`.** Migrate them first if the flag must be proven locally.
5. **Reporting lines are not enforced anywhere in the product.** They exist only in this report. Adding a real field is a separate product decision.

## 6. Unchanged

- G2–G16 and G8 are unchanged.
- `feature_ai_copilot` was not touched.
- **Production is NOT APPROVED.**
- No migration and no production write were made.
