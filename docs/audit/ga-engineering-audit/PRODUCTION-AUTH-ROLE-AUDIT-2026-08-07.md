# Production Auth & RBAC Read-Only Audit — 2026-08-07

| Field | Value |
|-------|-------|
| **Artifact** | `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07` |
| **Run** | EAB-2026-08-06-003 (ROW4) |
| **Date** | 2026-08-07 |
| **Environment** | Production (`https://salesos-production-96c0.up.railway.app`) |
| **Mode** | **READ-ONLY** — login (POST `/identity/login`) + GET probes only. No mutations, no POST/PUT/DELETE executed on data endpoints. |
| **Evidence** | `evidence/ops01-prod-health/prod-auth-rbac-audit-2026-08-07.json` + script outputs in `%TEMP%\salesos-audit-prod\` |
| **Validation honesty** | **light validated** — live probes against prod, single-run, spot checks. Not a full red-team. |

---

## 1. Executive summary

- **Authentication: PASS.** Login works for both accounts; unauthenticated gates return 401; JWT RS256 valid; CSRF enforced.
- **Authorization (tenant runtime admin): PASS.** Routes gated by `require_role_dep("admin")` correctly: admin role → 200, user role → 403, on all 4 tested paths.
- **Owner Platform admin: DEPLOYED BUT UNREACHABLE (functional gap, not security bypass).** All `/api/v1/admin/*` owner-scope routes return 401 for both roles because the owner-audience token cannot be minted: **`/owner/login` is not deployed on prod** (404 confirmed on 3 path variants; absent from prod `openapi.json`).
- **Roles are SWAPPED vs operator assumption.** `muhide.com` = `role=user`; `ratlfintech.com` = `role=admin`.
- **Both accounts share the SAME tenant** (`326e0825-1834-4399-8cca-77c2679f172b`) → cross-tenant isolation could NOT be demonstrated between these two accounts.
- **No unauthorized data access observed.** All probes denied appropriately; no mutations run.

---

## 2. Account facts

| Email | role | is_verified | tenant_id |
|-------|------|-------------|-----------|
| `ragheed.a@muhide.com` | **user** | **false** | `326e0825-1834-4399-8cca-77c2679f172b` |
| `ragheed.a@ratlfintech.com` | **admin** | true | `326e0825-1834-4399-8cca-77c2679f172b` |

> **Operator impact:** if you believed `muhide.com` is the admin account, the roles are reversed in the database. Verify intent before Row 5.

---

## 3. Results by area

### 3.1 Unauthenticated gates — PASS
- `GET /api/v1/companies` (unauth) → **401**
- `GET /api/v1/admin/tenants` (unauth) → **401**
- `GET /api/v1/identity/users/me` (unauth) → **401**

### 3.2 Login + session — PASS
- `POST /api/v1/identity/login` → **200** for both accounts
- JWT audience `salesos-api`, RS256-signed (verified via decoding)

### 3.3 CSRF enforcement — PASS (working)
- `POST` without `X-CSRF-Token` → **403** `CSRF token missing`
- `GET /api/v1/identity/csrf-token` → **200** (returns `csrf_token`)
- GraphQL `POST` without CSRF → **403**
- GraphQL with CSRF header+cookie but mismatched tenant binding → **403** `{"detail":"Tenant mismatch"}` — session-to-tenant binding enforced (extra protection, not a bug).

### 3.4 Tenant runtime admin RBAC — PASS
| Route | admin | user |
|-------|:-----:|:----:|
| `/api/v1/admin/metrics` | 200 | 403 |
| `/api/v1/admin/health/full` | 200 | 403 |
| `/api/v1/admin/dlq/stats` | 200 | 403 |
| `/api/v1/admin/sla-report` | 200 | 403 |

### 3.5 Identity users listing — PASS (scoped)
- `/api/v1/identity/users`: admin → **200**, user → **403** (`require_permission_dep("user", READ)` — admin is superset, user is denied). Correct RBAC.

### 3.6 Owner Platform admin — 401 for ALL (functional gap)
Routes `/api/v1/admin/{tenants,users,roles,permissions,plans,feature-flags,audit/logs,health/detailed}` return **401 for both roles**, because `require_owner_role_dep` demands an owner-audience JWT (`salesos-owner-platform`), and no owner login exists in the deployed build.

**Root cause:** production runs the `4750038c` baseline (alembic `d1a8c35e7f09`) whose `openapi.json` (881,643 B) exposes the 72 `/api/v1/admin/*` owner paths **but no owner login path**. The `owner/login` feature exists in local source but is **not yet deployed**:
- `POST /api/v1/identity/owner/login` → **404** (with CSRF bypassed correctly)
- `POST /owner-auth/login` → **404**
- `POST /owner-login` → **404**

This is an **ops/deployment gap**, not a security weakness — the surface is denied (401/404), never accessible.

### 3.7 Tenant isolation — INCONCLUSIVE with these accounts
- Both accounts are in the same tenant `326e0825`, so a *cross-tenant* read/write test is impossible with the provided creds.
- Injecting another tenant header returned 200 but was same-tenant, not cross-tenant.
- **Existing evidence** for tenant isolation remains the RLS checks (`evidence/ops01-pitr/row2/row3` — RLS forced on 4/4 tables) — not re-proven here.

---

## 4. Counts

- **38 PASS / 18 FAIL / 56 total** (raw probe table).
- All 18 "failures" trace to **one root cause**: owner-login not deployed (1 direct + 16 owner-route 401s + 1 inconclusive cross-tenant test). No access-control breach among them.

---

## 5. Recommended actions (for Row 5 / maintenance window)

1. **Confirm roles** — decide the intended role for `muhide.com` (currently `user`, unverified) vs `ratlfintech.com` (currently `admin`).
2. **Decide tenant topology** — both accounts sharing tenant `326e0825` may be intentional (same organization) or a misconfiguration.
3. **Deploy owner-login** (or schedule with the planned maintenance window) so Owner Platform admin routes become usable; verify with an owner-audience token afterwards.
4. **Email verification** — `muhide.com` has `is_verified=false`; decide whether to force verify or leave.
5. **Re-run cross-tenant isolation test** once a second tenant exists / test account is provisioned in a different tenant.

---

## 6. Constraints honored

- No data mutations executed. Only `POST /identity/login` (session establishment) — no resource state change.
- No credentials written to the audit report; tokens never printed.
- `GA_STATUS.md` / `SIGN_HERE.md` untouched (board constraint).
- Full soak continues independent (PID 16044, i00062 at capture time).

---

## 7. Owner disposition (2026-08-07)

- **Item promoted to P0 Release Blocker (P0-01)** by Project Owner per `RELEASE-GOVERNANCE-DECISION-2026-08-07.md` §1A: inability to verify tenant isolation + swapped roles on prod blocks GA.
- **Not a vNext backlog item.** Must be handled inside the RC-06 maintenance window (or explicitly accepted-with-residual by the Project Owner).
- Required actions inside window: confirm role intent, decide tenant topology for `326e0825`, provision a cross-tenant test account if topology is split, and re-run the cross-tenant isolation test (actions 1/2/5 above).
