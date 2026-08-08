# Deployment Package — Enable Owner Platform admin (`owner/login`) on Production

| Field | Value |
|-------|-------|
| **Package ID** | `OPS01-ROW4-OWNER-LOGIN-DEPLOY-2026-08-07` |
| **Author** | Executor (AI), prepared for human execution |
| **Target** | Production `https://salesos-production-96c0.up.railway.app` |
| **Gate** | **DO NOT EXECUTE until soak completes** (2026-08-10T14:10:06Z) **and** project **Owner** approves RC-06 (maintenance window) + RC-08 (owner-login) in `CTO-REQUIRED-HUMAN-DECISIONS.md` |
| **Validation label** | `not validated` for the deploy itself; code is `light validated` (unit asserts 17 passed in Docker; source review below) |
| **Source of truth** | [`PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md`](../../PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md) |

---

## 1. Problem statement

Read-only audit on 2026-08-07 confirmed:

- Owner Platform admin routes (`/api/v1/admin/{tenants,users,roles,permissions,plans,feature-flags,audit/logs,health/detailed}`) **exist** on prod (72 paths in `openapi.json`, 881,643 B) and require an **owner-audience JWT** (`salesos-owner-platform`).
- The only way to mint that JWT is `POST /api/v1/identity/owner/login` — **which is NOT deployed** on prod:
  - `POST /api/v1/identity/owner/login` → **404** (after CSRF correctly bypassed)
  - `POST /owner-auth/login`, `POST /owner-login` → **404**
  - Not present in prod `openapi.json`
- Therefore **all owner-admin routes return 401 for every caller** — the Owner Console is deployed but unreachable. **Functional gap, not a security bypass** (nothing is ever authorized without the owner token).

Root cause: prod is deployed from baseline `4750038c` (Sprint 0.5). The `owner/login` route plus its CSRF / suspension-guard exceptions exist only as **uncommitted working-tree changes** on `master` (HEAD `2538a7d`).

---

## 2. What already exists on prod (no change needed)

Verified present in deployed baseline `4750038c`:

| Component | Evidence |
|-----------|----------|
| `app/owner_auth.py` — `require_owner_role_dep("admin")`, `verify_owner_token` | Present in tree |
| `service.create_owner_access_token / create_owner_refresh_token / decode_owner_*` | Present in tree (`aud=salesos-owner-platform`, RS256) |
| `modules/admin/router.py` wired with `dependencies=[Depends(require_owner_role_dep("admin"))]` | Present in tree |
| `settings.jwt_owner_audience = "salesos-owner-platform"` | `config.py:143` |
| RS256 JWKS + `kid` rotation | Present |
| Frontend `/admin/login` page + `ownerAudience.ts` auth helpers | `salesos/frontend/src/app/(auth)/admin/login/page.tsx` (untracked on disk), `ownerAudience.ts` (modified) |

So the **owner token minting machinery is already on prod**. Only the **login endpoint + exceptions** are missing.

---

## 3. What must be committed + deployed

The owner-login change set = **uncommitted working-tree edits on `master`** (verified by `git status`/`git diff`). Minimal scope required for owner-login to work **and be safe**:

| File | Change (relative to HEAD `2538a7d`) | Why |
|------|--------------------------------------|-----|
| `salesos/backend/app/modules/identity/router.py` | `@router.post("/owner/login")` handler (~62 lines) minting owner-audience access+refresh tokens; gates on active `admin` role (hierarchy check); records `owner_login` audit; sets auth cookies | **The missing endpoint itself** |
| `salesos/backend/app/common/middleware.py` | Add `"/api/v1/identity/owner/login"` to `CsrfEnforcementMiddleware._PUBLIC_PATHS` | owner/login must not require CSRF header (like `/login`) |
| `salesos/backend/app/modules/identity/tenant_lifecycle_guard.py` | Add `"/api/v1/identity/owner/login"` to `SKIP_PATH_PREFIXES` | Login must stay reachable even if a tenant is suspended |

> These 3 files are the **strict minimum**. Everything else in the working tree (EAB-001 security fixups: `boot/middleware.py` TrustedHost/CORS, `config.py` R-14 empty-password guard, `api_keys/middleware.py` fail-closed, `entitlement_middleware.py` / `suspended_tenant_middleware.py` 503 fail-closed, frontend OwnerConsole tweaks) is **out of scope** for this package — see §8.

---

## 4. Release Candidate (RC) — NOT a frozen commit

**No `git commit` is prepared now.** The commit will be created **at execution time from the actual repository state** (after soak review), never from a pre-written draft. Rationale: any change during soak (P0, regression, or minor edit) would make a pre-staged commit stale.

### 4.1 Release Candidate manifest

| File | Reason | Isolation reason |
|------|--------|------------------|
| `salesos/backend/app/modules/identity/router.py` | Add `POST /owner/login` endpoint (mint owner-audience JWT) | Only auth-route change in scope |
| `salesos/backend/app/common/middleware.py` | Allow owner login through CSRF (add path to `_PUBLIC_PATHS`) | CSRF exemption, auth-path only |
| `salesos/backend/app/modules/identity/tenant_lifecycle_guard.py` | Skip owner login in suspension guard | Guard exception, auth-path only |

### 4.2 Release flow (owner-login ships as its own release)

```text
Release RC (owner-login only)
        ↓
Commit A  — "feat(identity): owner/login mint"  (3 files, nothing else)
        ↓
Verify    — build + unit route-gate tests + post-deploy probe matrix (§5 Step 3)
        ↓
Tag       — e.g. v5.1.0-owner-login.1 (after green verify)
        ↓
Deploy    — Railway deploy from the tagged commit
```

No mixing with: security fixes, EAB fixes, refactoring, documentation, dependency upgrades, schema changes, or feature work.

### 4.3 Acceptance criteria (RC gates)

- [ ] `git status` shows **exactly the 3 files** staged, nothing else
- [ ] Backend boots; route-gate unit asserts pass (owner_login, CSRF exemption, suspension-guard skip)
- [ ] `openapi.json` gains `/api/v1/identity/owner/login` and nothing else changes
- [ ] Post-deploy probes (§5 Step 3) all green: 200 mint / 403 non-admin / 200 owner route / 401 tenant token on owner route / 401 no-regression / CSRF still enforced
- [ ] Probe matrix from `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` shows no authz drift

### 4.4 Verification prerequisites (before execution)

- [ ] Soak completed: staging `loop-*.json` shows PASS through end (PID 16044 exited cleanly), no FAIL entries
- [ ] **Owner approval**: **RC-06** (Maintenance Window) and **RC-08** (owner-login deploy) in `CTO-REQUIRED-HUMAN-DECISIONS.md` = **APPROVED** by project Owner
- [ ] Owner account confirmed: which email is the intended owner admin (`muhide.com` currently `role=user`; `ratlfintech.com` currently `role=admin` — **roles are swapped vs assumption**, decide before enabling owner login)
- [ ] `is_verified` policy decided for owner account (owner_login does not gate on `is_verified`, only `is_active` + role)
- [ ] Backend + frontend build validated locally (`npx tsc --noEmit`, backend unit route-gate tests) against the **actual** working-tree state at window time

---

## 5. Execution steps (maintenance window, non-peak)

### Step 1 — Create the commit FROM ACTUAL REPO STATE (in repo root `C:\Users\raghe\Documents\Muhide`)
```powershell
# First: re-review the working tree at window time. Stage EXACTLY the 3 RC files:
git status --short
git diff salesos/backend/app/modules/identity/router.py
git diff salesos/backend/app/common/middleware.py
git diff salesos/backend/app/modules/identity/tenant_lifecycle_guard.py

# Then stage only those three:
git add salesos/backend/app/modules/identity/router.py
git add salesos/backend/app/common/middleware.py
git add salesos/backend/app/modules/identity/tenant_lifecycle_guard.py
git diff --cached --stat   # MUST show only 3 files
git commit -m "feat(identity): deploy owner/login mint endpoint (DEC-093)"
```
> **EAB-001 security fixups and everything else must remain UNSTAGED.** If the working tree moved during soak, re-review the diff and adapt — the RC manifest (§4.1) is the contract, not the diff hash.

### Step 2 — Push + deploy via Railway (CI path)
```powershell
git push origin master
# Railway auto-deploy (or manual via dashboard). Confirm deploy is from the new commit hash.
```

### Step 3 — Post-deploy verification (READ-ONLY probes only)
```powershell
# 1. OpenAPI must now expose the path
curl -s https://salesos-production-96c0.up.railway.app/openapi.json | Select-String "owner/login"

# 2. Owner login mints owner-audience token (owner admin account only)
curl -s -X POST https://salesos-production-96c0.up.railway.app/api/v1/identity/owner/login `
  -H "Content-Type: application/json" -d '{"email":"<OWNER_ADMIN>","password":"<...>"}'
# → expect 200 with access_token (decoded aud must be salesos-owner-platform)

# 3. Non-admin owner login must 403
curl -s -X POST .../api/v1/identity/owner/login -d '{"email":"<user-role>","password":"<...>"}' -w "%{http_code}"
# → expect 403 "Owner Platform requires admin role"

# 4. Owner-admin route with owner token → 200
curl -s .../api/v1/admin/tenants -H "Authorization: Bearer <owner_token>" -w "%{http_code}"

# 5. Tenant token still rejected on owner routes → 401 (no regression)
# 6. Tenant login unchanged → 200; tenant admin routes unchanged (admin 200 / user 403)
# 7. CSRF still enforced on other POSTs → 403 without X-CSRF-Token
```

### Step 4 — Regression sweep
Re-run the read-only probe matrix from `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` (38 PASS rows) to confirm no authz drift. Confirm `openapi.json` size changes ONLY by the new `owner/login` path (+`csrf` unaffected).

---

## 6. Rollback

| Trigger | Action |
|---------|--------|
| owner/login returns 5xx, or owner routes mis-authorize, or CSRF breaks on tenant login | **Revert the 3-file commit** and redeploy `4750038c`-equivalent baseline (Railway redeploy of previous release / `git revert <sha>`) |
| Tenant RBAC regressions (admin→403/user→200 flipped) | Same revert; re-verify with probe matrix |
| No migrations in this change set | No DB rollback required |

Rollback window: up to 30 minutes post-deploy; soak metrics (`/health`) monitored.

---

## 7. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Non-RC files (EAB-001 security fixups etc.) get swept into the owner-login commit | Medium | High (unreviewed surface ships together) | §8 Out of Scope is contract; stage EXACTLY the 3 RC files and confirm `git diff --cached --stat` (§5 Step 1) before commit |
| R2 | Owner roles swapped (`muhide.com`=user) → owner login with wrong account fails or grants wrong scope | High | Medium | Decide owner account first (§4.4); owner_login only grants on `role=admin`, so a user-role owner account simply 403s — fail-safe |
| R3 | `owner/login` CSRF exemption widens attack surface | Low | Low | Matches existing `/login` exemption; POST to owner/login requires valid credentials; no data mutation |
| R4 | `SALESOS_TESTING=true` CSRF bypass in prod (EAB-001-P2-SEC-04) | Low (already present) | High | Do NOT ship the EAB-001 middleware changes in this window (out of scope §8); startup logs ERROR if env prod + flag set |
| R5 | Frontend `/admin/login` (untracked) not deployed → console unusable from UI | High | Medium | Include frontend admin login in a follow-up UI release; backend owner/login is usable via curl/Postman regardless |
| R6 | Working tree drifts during soak → RC commit built from stale review | Medium | Medium | Create commit at window time from actual repo state (§4/§5 Step 1); re-review diffs before staging; RC manifest is the contract, not a frozen patch |

---

## 8. Out of Scope — hard boundary (prevents scope creep)

**This deployment SHALL NOT include:**

- EAB-001 security fixups (`boot/middleware.py` TrustedHost/CORS, `config.py` R-14 password guard, `api_keys/middleware.py` fail-closed, `entitlement_middleware.py`, `suspended_tenant_middleware.py`) — own release, later
- Refactoring / reformatting (e.g. Prettier, imports) of any file outside the 3 RC files
- ADR / documentation updates (`PROJECT_BIBLE.md`, ADRs, ops docs)
- Dependency upgrades (Python, Node, image bumps)
- Schema changes / Alembic migrations
- Feature work (frontend Owner Console shell, OwnerOpsPageHonesty, integrations page)
- Tenant topology / role corrections for `muhide.com` vs `ratlfintech.com` (business decision, RC-01/RC-02)
- Neo4j persistent volume (RC-04)
- Any GA claims or status-file edits (`GA_STATUS.md`, `SIGN_HERE.md`)

> If any of the above is needed, it is a **new package** requiring its own approval — it does not ride into this window.

---

## 9. Owner login endpoint behavior (for reviewers)

```
POST /api/v1/identity/owner/login
Body: {"email","password"}
Flow:
  1. IdentityService.authenticate (same password verification as tenant /login)
  2. reject if not is_active        → 403
  3. reject if role < "admin" (hierarchy admin=3, manager=2, user=1, api=1, auditor=0) → 403
  4. mint owner ACCESS + REFRESH tokens (aud=salesos-owner-platform, RS256, kid from JWKS)
  5. set auth cookies (access + refresh)
  6. record audit "owner_login" (tenant_id from user, email, audience, ip)
  7. return TokenResponse (tenant_id=None — owner scope is tenant-less)
```
No `is_verified` gate. No tenant token minted. Tenant `/login` untouched.

---

*Prepared by executor (AI) — **Owner** approval and human execution required. All commands above are guidance; run only within the approved maintenance window after RC-06 + RC-08 approval. The final commit is created at window time from the actual repo state — never from a pre-staged draft.*
