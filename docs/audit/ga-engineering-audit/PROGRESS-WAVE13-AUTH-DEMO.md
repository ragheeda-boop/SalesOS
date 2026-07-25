# Progress — Wave 13 Demo / Pentest Account Auth

**Date:** 2026-07-22  
**Product:** SalesOS (AQLIYA) — local Docker FE `:3000` + API `:8000`  
**Scope:** Authenticated flows using **documented demo/pentest accounts** (`salesos/docs/pentest/PENTEST_BRIEF.md`)  
**Validation class:** **light validated** (local compose seed + login + auth smoke)  
**Demo-admin goal:** **UNBLOCKED** (local `demo_tenant` seeded; admin login **200**)  
**Production GO:** **NO** (explicitly not claimed)

---

## Verdict

Local stack healthy. **Pentest brief accounts** are now present under slug `demo_tenant` via idempotent seed script `salesos/backend/scripts/seed_demo_users.py`. Login for `admin@salesos.io` returns **200**; `/users/me` returns `role=admin`. Auth smoke with `SMOKE_EMAIL=admin@salesos.io` + `-SkipRegister`: **13 PASS / 0 FAIL**.

Passwords are **not** recorded here. Use PENTEST_BRIEF locally only; never against production.

**Do not claim Production GO.**

---

## Accounts (local DB after seed)

| Account | Source | In local DB? | Login | Notes |
|---------|--------|--------------|-------|-------|
| `admin@salesos.io` | PENTEST_BRIEF §5.1 | **Yes** | **200** | `role=admin`, tenant `demo_tenant` |
| `manager@salesos.io` | same | **Yes** | not re-probed this pass | seeded |
| `rep1@salesos.io` / `rep2` / `rep3` | same | **Yes** | not re-probed this pass | seeded `role=rep` |
| Disposable `@example.com` | `POST /identity/register` | Yes | **200** | Positive control earlier; role=`user` |

---

## Seed tooling

| Path | Present? | Result |
|------|----------|--------|
| `salesos/backend/scripts/seed_demo_users.py` | **Added** | Idempotent; creates `demo_tenant` + 5 users if absent; bcrypt via `hash_password` (same as register/login); refuses `ENV=production` / non-local hosts unless `ALLOW_DEMO_SEED=1` |
| `app.seed` / `create_admin.py` | Still missing | Optional later; demo path covered |
| Re-run seed | OK | `tenant_existing=1`, `users_skipped=5` |

Command (local compose only):

```text
docker compose exec -T backend python scripts/seed_demo_users.py
```

First run: `tenant_created=1`, `users_created=5`.  
Second run: skip-all (idempotent).

---

## Stack health (light)

| Check | Status |
|-------|--------|
| `GET /health` | **200** |
| Compose backend + frontend | **healthy** |
| 48h soak | **IN PROGRESS** — PID `21856` left running; **not** killed; `soak_complete_claim: false` |

---

## Demo admin verify (redacted)

Source: `evidence/wave13-auth-demo/demo-admin-login-verify-2026-07-22T144504Z.json`  
(`passwords_in_evidence: false`)

| Check | Status | Notes |
|-------|--------|-------|
| `POST /api/v1/identity/login` (`admin@salesos.io`) | **200** | `access_token_present=true` |
| `GET /api/v1/identity/users/me` | **200** | `role=admin` |

---

## Auth smoke (demo admin)

```powershell
cd salesos
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '…'   # process env only — from PENTEST_BRIEF locally
.\scripts\smoke-auth.ps1 -BaseUrl http://127.0.0.1:8000 -FrontendUrl http://127.0.0.1:3000 -SkipRegister
```

| Result | Value |
|--------|-------|
| PASS / FAIL | **13 / 0** |
| OVERALL | **PASS** |
| login | **200** `token_present=True` |
| `/users/me` | **200** `role=admin` |
| dashboard / companies / decisions / graphql | **200** |

---

## Evidence paths (redacted)

| Path | Contents |
|------|----------|
| `evidence/wave13-auth-demo/demo-admin-login-verify-2026-07-22T144504Z.json` | Login/me status codes; no passwords |
| Prior negative probes | `demo-auth-probe-2026-07-22T143623Z.json` (pre-seed **401**) |
| Disposable control | `disposable-auth-probe-2026-07-22T143904Z.json` |

Related: [PROGRESS-WAVE13-AUTH-SMOKE.md](./PROGRESS-WAVE13-AUTH-SMOKE.md), [PROGRESS-WAVE13-UI-SMOKE.md](./PROGRESS-WAVE13-UI-SMOKE.md).

---

## Remaining gaps

1. Pilot-* tenants still optional (out of this pass).  
2. `app.seed` / `create_admin.py` still absent — demo seed covers Wave 13 need.  
3. Identity rate limit (10/min) under dense probing — wait ~60s between bursts.  
4. 48h soak **in progress** — not complete.  
5. Staging/prod demo credentials — **out of scope**; never use brief passwords against production.

---

## Validation label

**light validated** — local compose only.  
**Demo-admin authenticated flows:** **PASS** (local).  
**production no-go** unchanged. **Not Production GO.**
