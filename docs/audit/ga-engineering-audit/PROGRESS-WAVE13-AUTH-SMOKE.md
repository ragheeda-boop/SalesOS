# Progress — Wave 13 Auth Smoke Precursor

**Date:** 2026-07-22  
**Product:** SalesOS — local Docker  
**Scope:** Authenticated API smoke (GO-live precursor; not production T-0)  
**Validation class:** **light validated** (local compose runtime evidence)  
**Overall:** **PASS** (13/13)

---

## Summary

Disposable local registration via `POST /api/v1/identity/register` works; JWT unlocks companies + decision-center list; unauthenticated calls correctly return **401**; GraphQL requires CSRF (**403** without, **200** with cookie+header); `/metrics` and `/health` are reachable without user JWT.

No production secrets used. No auth weakening. Seed credentials were **not** required — register creates a local tenant+user.

---

## Pass / fail matrix

| Check | Expected | Actual | Status | Notes |
|-------|----------|--------|--------|-------|
| `GET /api/v1/companies` (no token) | 401 | 401 | **PASS** | Auth gate |
| `GET /api/v1/decisions` (no token) | 401 | 401 | **PASS** | Decision Center gate |
| `POST /graphql` (no CSRF) | 403 | 403 | **PASS** | CSRF enforced |
| `POST /api/v1/identity/register` | 201 | 201 | **PASS** | Disposable `@example.com` user |
| `POST /api/v1/identity/login` | 200 | 200 | **PASS** | JWT issued (`token_present=True`) |
| `GET /api/v1/identity/csrf-token` | 200 | 200 | **PASS** | Sets `csrf_token` cookie |
| `GET /api/v1/identity/users/me` | 200 | 200 | **PASS** | Bearer + `X-Tenant-Id` |
| `GET /api/v1/companies` (auth) | 200 | 200 | **PASS** | Empty list `items=0` (new tenant) |
| `GET /api/v1/decisions` (auth) | 200 | 200 | **PASS** | Empty/list JSON OK |
| `POST /graphql` (auth+CSRF) | 200 | 200 | **PASS** | `{ __typename }` |
| `GET /health` | 200 | 200 | **PASS** | DB/cache/graph connected |
| `GET /metrics` (unauth) | 200 | 200 | **PASS** | Prometheus scrape OK |
| `GET frontend :3000/` | 200 | 200 | **PASS** | Container healthy; FE login UI not exercised |

**Script exit code:** `0` (`OVERALL: PASS`)

---

## Commands run

```powershell
# Stack was already up (backend :8000 healthy, frontend :3000 healthy)
cd salesos
docker compose ps

# Repeatable smoke (never prints JWT)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-auth.ps1
```

Optional bash twin (Unix/CI):

```bash
bash salesos/scripts/smoke-auth.sh
```

Identity contract used by the script:

- Register: `POST /api/v1/identity/register`  
  Body: `{ "email", "password" (>=12 + complexity), "full_name" }`  
  Creates tenant when `tenant_id` omitted.
- Login: `POST /api/v1/identity/login`
- Me: `GET /api/v1/identity/users/me`
- CSRF: `GET /api/v1/identity/csrf-token` then `X-CSRF-Token` + cookie on GraphQL POST

Password complexity: min 12, upper, lower, digit, special (see `identity/schemas.py`).  
Use a real TLD for EmailStr (e.g. `@example.com`). `.local` emails return **422**.

---

## Script path

| Path | Role |
|------|------|
| `salesos/scripts/smoke-auth.ps1` | Primary (Windows / local Docker) |
| `salesos/scripts/smoke-auth.sh` | Bash twin for Linux/macOS CI hosts |

Related (broader, older): `salesos/scripts/smoke-test.ps1` — still notes historical identity middleware issues; prefer `smoke-auth.ps1` for this Wave 13 precursor.

---

## Blockers / caveats

| Item | Severity | Detail |
|------|----------|--------|
| Shared per-IP rate limit + identity tier **10/min** | Medium (local DX) | `RateLimitMiddleware` uses key `ratelimit:{ip}` for **all** paths; identity paths apply tier=10. Dense probing before `/api/v1/identity/*` yields **429**. Script orders identity/CSRF early. If 429: wait ~60s and re-run. |
| No documented local seed admin | Low | Register-on-the-fly is sufficient for smoke; no committed prod secrets. |
| Empty companies list | Expected | New disposable tenant has zero companies — **200 + empty** is correct. |
| FE login E2E | Skipped | Prefer API evidence; Playwright not run. Frontend root **200** only. |
| Production GO | **NO-GO** | This is local smoke evidence only; GA audit remains production no-go. |

---

## Auth honesty notes

- CSRF on state-changing GraphQL: **working** (403 without token).
- JWT gate on companies/decisions: **working** (401 without token).
- Metrics scrape path remains unauthenticated by design (PROD-W5-004).
- Did **not** disable middleware, CSRF, RBAC, or rate limits.

---

## Files touched

- `salesos/scripts/smoke-auth.ps1` (new)
- `salesos/scripts/smoke-auth.sh` (new)
- `docs/audit/ga-engineering-audit/PROGRESS-WAVE13-AUTH-SMOKE.md` (this file)

**Validation status:** light validated — local Docker API smoke **PASS** 13/13 on 2026-07-22.

---

## Follow-up — env credentials + dashboard probe (2026-07-22)

- `smoke-auth.ps1` now accepts `SMOKE_EMAIL` / `SMOKE_PASSWORD` and `-SkipRegister` (login-only for existing accounts).
- Script also probes `GET /api/v1/dashboard` after `/me`.
- Demo `@salesos.io` accounts: **BLOCKED** on this local DB — see [PROGRESS-WAVE13-AUTH-DEMO.md](./PROGRESS-WAVE13-AUTH-DEMO.md).
- Disposable positive control after rate-limit cooldown: login/me/dashboard/companies all **200** (evidence under `evidence/wave13-auth-demo/`).

**production no-go** unchanged.
