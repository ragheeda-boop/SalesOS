# Progress — Wave 13 Authenticated UI Smoke

**Date:** 2026-07-22  
**Product:** SalesOS — local Docker FE `:3000` + API `:8000`  
**Scope:** Authenticated frontend UI smoke (Playwright chromium)  
**Validation class:** **light validated**  
**Production GO:** **NO** (explicitly not claimed)  
**Overall (script):** **PASS** (Playwright exit `0`) — with documented route gaps below  

---

## Verdict

Disposable user login + key authenticated pages were exercised locally. **Companies**, **Decision Center**, and **AI Copilot** shells opened (`HTTP 200` with expected `h1`). **`/dashboard` was a hard 404** on the original Wave 13 Docker image; after **source fix + FE image rebuild**, Docker `:3000` returns **HTTP 200** (Playwright smoke PASS). Root `/` remains the **public marketing landing**, not an authenticated dashboard home.

This is **not** browser GA evidence and **not** Production GO.

---

## Pass / fail matrix (pages)

| Route | Opened? | Final URL | Status | Notes |
|-------|---------|-----------|--------|-------|
| UI `/login` | Yes | `/login` | **PASS** | Form visible (`Sign In to SalesOS`, Email/Password, Login). Labels are visual-only (no `id`/`htmlFor`) — use `input[type=email\|password]`. |
| Post-login redirect `/dashboard` | Yes (post-rebuild) | `/dashboard` | **PASS** | Was **HTTP 404** on original Wave 13 image; route + Docker rebuild fixed. Residuals **`no_h1` + API 403** closed 2026-07-22 (see residual fix follow-up): probe now `h1=Dashboard`; `GET /api/v1/dashboard` **200** for role=`user`. |
| `/` (home) | Yes | `/` | **PASS*** | Marketing landing (`h1=SalesOS` + login/register CTAs). *Not* the authenticated dashboard. `(dashboard)/page.tsx` does not win this URL over `app/page.tsx`. |
| `/companies` | Yes | `/companies` | **PASS** | `h1=Companies`. Authenticated shell loaded. |
| `/decisions` | Yes | `/decisions` | **PASS** | `h1=Decision Center`. |
| `/copilot` | Yes | `/copilot` | **PASS** | `h1=AI Copilot` **UI shell only** — do not treat as live GA AI (`feature_ai_copilot` honesty; see `AI_HONESTY.md`). |

**Script soft gates:** companies OK + (`/` OR `/dashboard` OK) → overall PASS.  
**Coverage honesty:** `/dashboard` route + visible `h1` + `GET /api/v1/dashboard` under disposable role=`user` are **light validated** on Docker. Deep widget correctness / Production GO not claimed.

---

## Auth path used

1. **API register** (earlier in session): `POST /api/v1/identity/register`  
   - Disposable: `smoke.ui.probe9@example.com` / local-only password  
   - Result: **201** + JWT (register can take ~30–60s under Docker load)  
2. **UI login** via Playwright: fill email/password → Login  
   - Token appeared in `localStorage` (`access_token`)  
   - `afterLoginUrl` observed still on `/login` at probe start (token set before navigation settled; subsequent page probes used the token)  
3. API token seed fallback exists in the smoke spec if UI login does not persist tokens  

UI **Sign Up** (`/register`) is present but was **not** required for this run (API register used).

---

## Console / network observations

Source: `salesos/frontend/test-results/smoke-ui/smoke-auth-ui-report.json`

| Area | Observation |
|------|-------------|
| `/dashboard` | Console: resource **404**; failed request `GET /dashboard` |
| Sidebar prefetch | Repeated **404** RSC fetches to `/dashboard?_rsc=…` while on other pages |
| `/decisions`, `/copilot` | Multiple `net::ERR_ABORTED` on RSC/chunk prefetches during fast navigation (noise); not treated as page-break failures |
| API host mix | Some aborted calls to `http://localhost:8000/api/v1/...` while smoke used `127.0.0.1` (FE rewrite / env host inconsistency under Docker Desktop) |

No claim that API payloads were fully correct — only that the **pages rendered** with auth context.

---

## What was not covered

- Full e2e suite (`e2e/*.spec.ts` beyond smoke)  
- Firefox / WebKit / mobile projects  
- Deep CRUD on companies, decision accept/reject, copilot chat quality  
- Authenticated dashboard widgets (blocked by `/dashboard` 404 + `/` marketing)  
- Browser MCP automation (tab create failed in this environment; Playwright used instead)  
- Production / staging  
- Load, accessibility, visual regression  

---

## Artifacts / commands

| Path | Role |
|------|------|
| `salesos/frontend/e2e/smoke-auth-ui.spec.ts` | Minimal authenticated UI smoke |
| `salesos/frontend/playwright.smoke.config.ts` | Chromium-only; **no** `webServer` (reuses Docker FE) |
| `salesos/scripts/smoke-ui.ps1` | Register (optional) + run smoke; prefers `127.0.0.1` |
| `salesos/frontend/test-results/smoke-ui/smoke-auth-ui-report.json` | Page probe evidence |

```powershell
cd salesos
# Prefer 127.0.0.1 — Docker Desktop localhost resets were observed during this wave
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-ui.ps1

# Or reuse an existing disposable user:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-ui.ps1 `
  -Email 'smoke.ui.probe9@example.com' -Password '***' -SkipRegister
```

**Commands run (this wave):**

- API/FE health checks (`curl` / Docker `ps`)  
- `POST /api/v1/identity/register` (disposable `@example.com`)  
- `npx playwright install chromium` (browsers missing in agent cache)  
- `.\scripts\smoke-ui.ps1 -SkipRegister ...` → **OVERALL: PASS**

Related API precursor: `docs/audit/ga-engineering-audit/PROGRESS-WAVE13-AUTH-SMOKE.md`.

---

## Blockers / findings (honest)

1. **P0/P1 UX:** `/dashboard` **404** on the original Wave 13 Docker smoke — **source fixed** and **Docker FE image rebuilt** (2026-07-22); residuals `no_h1` + API **403** closed same day (see follow-up).  
2. **Routing:** Authenticated home is `app/(dashboard)/dashboard/page.tsx`. Root `/` remains marketing.  
3. **A11y/test debt:** Login `Input` labels lack `id`/`htmlFor` — `getByLabel` (existing e2e helpers) does not work against current UI.  
4. **Infra flakiness:** Host → Docker port forwarding intermittently timed out / `ERR_CONNECTION_RESET` on `localhost`; `127.0.0.1` was more reliable.  
5. **AI honesty:** Copilot page title rendered; treat as **shell**, not production AI capability.

---

## Validation label

**light validated** — local Playwright chromium smoke only.  
**production no-go** unchanged.

---

## Follow-up — `/dashboard` 404 fix (2026-07-22, verification)

**Source fix (parent):**
- Added `salesos/frontend/src/app/(dashboard)/dashboard/page.tsx` → renders `DashboardPage`
- Removed conflicting `salesos/frontend/src/app/(dashboard)/page.tsx` (route group `/` competed with marketing `app/page.tsx`)

**Verification (this note):**

| Check | Result |
|-------|--------|
| Conflicting `(dashboard)/page.tsx` | **Gone** (`Test-Path` false; no import refs to that file) |
| New `/dashboard` App Router page | **Present** |
| Broken imports of `(dashboard)/page` | **None found** |
| `next.config.js` rewrites | **API only** (`/api/:path*` → backend). **No** `/dashboard` rewrite |
| Next.js `middleware` | **None** in FE tree (no middleware rewrite/redirect for `/dashboard`) |
| Docker FE mounts | **Image-only** (`docker inspect` Mounts `[]`; compose has no source volume) |
| Docker FE `:3000` `/dashboard` | Still **HTTP 404** (`salesos-frontend:local`, up ~9h — image predates fix) |
| `npx next dev -p 3010` `/dashboard` | **HTTP 200** (Next log: `Compiling /dashboard` → `GET /dashboard 200`) |
| Marketing `/` | Still **HTTP 200** on both Docker and dev |
| Playwright `smoke-auth-ui` vs `next dev :3010` | **Not completed** — `POST …/identity/login` → `ECONNREFUSED 127.0.0.1:8000` during run (auth seed blocked). Route existence already proven by Next `GET /dashboard 200`. |

**Docker image rebuild still required** for Docker/UI smoke on `:3000`:

```powershell
cd salesos
docker compose build frontend
docker compose up -d frontend
# then re-run: .\scripts\smoke-ui.ps1 -SkipRegister ...
```

Do **not** treat Docker `:3000` as fixed until rebuild/recreate. Source-level route is fixed and **light validated** via local `next dev` HTTP 200 (not Production GO).

---

## Follow-up — Docker FE rebuild live on `:3000` (2026-07-22)

**Goal:** Ship the `/dashboard` App Router page into the image-only FE container so Wave 13 smoke no longer 404s.

**Commands (frontend-only; `--no-deps` to avoid backend rebuild conflict):**

```powershell
cd salesos
docker compose build frontend          # exit 0 (~398s)
docker compose up -d --force-recreate --no-deps frontend   # exit 0
```

**Image / container:**

| Item | Value |
|------|-------|
| Image | `salesos-frontend:local` |
| Image ID | `sha256:84ef1507c89e…` (built ~2026-07-22T09:15Z) |
| Container | `salesos-frontend-1` — **healthy** |
| Prior image | `ed834c955d44` (~9h old) — still had `/dashboard` 404 |

**HTTP curl (`http://127.0.0.1:3000`, no redirect follow):**

| Path | Code |
|------|------|
| `/dashboard` | **200** |
| `/companies` | **200** |
| `/login` | **200** |
| `/` | **200** |

**Optional `smoke-ui.ps1` re-run (backend `:8000` healthy):**

```powershell
.\scripts\smoke-ui.ps1 -Email 'smoke.ui.probe9@example.com' -Password '***' -SkipRegister `
  -FrontendUrl 'http://127.0.0.1:3000' -BaseUrl 'http://127.0.0.1:8000'
```

| Result | Value |
|--------|-------|
| Playwright | **1 passed** (~31.5s), exit **0** |
| Soft gate | **OVERALL: PASS** — pages PASS=5 FAIL=0 |
| `/dashboard` | **PASS** `http=200` (notes: `no_h1`) |
| `/`, `/companies`, `/decisions`, `/copilot` | **PASS** with expected `h1` |

**Residual issues (not blockers for route existence) — closed in residual fix follow-up:**

1. Dashboard page probe: `no_h1` → fixed with always-visible page `h1` (`h1=Dashboard` in smoke).  
2. Authenticated smoke: `HTTP 403 GET …/api/v1/dashboard` → fixed by gating sales home on `company.READ` (executive surface still 403 for role=`user`).  
3. **production no-go** / **light validated** unchanged — not Production GO.

**Validation:** **light validated** (Docker curl + Playwright chromium smoke). **not** browser GA; **not** Production GO.

---

## Verification re-run (2026-07-22, continuation agent)

Confirmed stack + evidence after FE image already on `:3000`:

| Check | Result |
|-------|--------|
| FE image | `salesos-frontend:local` `sha256:84ef1507c89e…` — container **healthy** (~47m up at verify) |
| `GET http://127.0.0.1:3000/dashboard` | **200** (also `/login`, `/`, `/companies` → 200) |
| API `/health` | **200** `status=ok` (cache/redis connected; graph unavailable; kafka in_memory) |
| `.\scripts\smoke-ui.ps1 -SkipRegister …` | **OVERALL: PASS** — Playwright 1 passed (~21s), pages PASS=5 FAIL=0 |
| Report | `salesos/frontend/test-results/smoke-ui/smoke-auth-ui-report.json` |

Residual (then): `/dashboard` probe `no_h1`; `HTTP 403 GET …/api/v1/dashboard` under smoke auth; aborted Next chunk fetches during fast nav.  
**Superseded** by residual fix follow-up below (`h1=Dashboard`; dashboard API **200** for role=`user`).

**Validation label:** **light validated**. **production no-go** — not Production GO.

---

## Follow-up — residual fix `no_h1` + API 403 (2026-07-22)

### Root cause of `/api/v1/dashboard` 403

| Fact | Detail |
|------|--------|
| Gate | `require_permission_dep("executive", PermissionAction.READ)` on sales home `GET /api/v1/dashboard` (+ nba-feed) |
| Smoke user | `POST /api/v1/identity/register` → `create_user` → default **`role=user`** |
| Role matrix | `user` has `company`/`contact`/`opportunity` only — **no** `executive.*` |
| Admin-only | `executive.*` is on the **admin** role; `/api/v1/executive/dashboard` correctly keeps that gate |
| Misconfiguration | Sales home dashboard was conflated with the executive module permission |

Not CSRF, not wrong path, not missing tenant header. **Expected for role=`user` under the old gate; incorrect product gate for the SalesOS home surface.**

### Code changes (minimal; did not weaken executive)

| File | Change |
|------|--------|
| `salesos/backend/app/application/dashboard/router.py` | `/dashboard` + `/dashboard/nba-feed` → `company.READ` (user+manager+admin). `/executive/dashboard` unchanged (`executive.READ`). |
| `salesos/frontend/src/features/dashboard/_layout/dashboard-page.tsx` | Always-visible page-level `<h1>` (loading / error / success). |
| `salesos/frontend/src/features/dashboard/_layout/dashboard-metrics-header.tsx` | Dropped duplicate title `h1`; QuickActions + metrics only. |

### API evidence (role=`user`, after backend volume restart)

```text
register=201
me=200 role=user
dashboard=200
executive_dashboard=403   # still enforced — RBAC not weakened
```

### FE rebuild + smoke

```powershell
cd salesos
docker compose build frontend          # exit 0 (~16m)
docker compose up -d --force-recreate --no-deps frontend
.\scripts\smoke-ui.ps1 -BaseUrl http://127.0.0.1:8000 -FrontendUrl http://127.0.0.1:3000
```

| Item | Result |
|------|--------|
| Image | `salesos-frontend:local` `sha256:f3fd7da90c6f…` |
| `GET :3000/dashboard` | **200** |
| Playwright | **1 passed** (~23s), exit **0** |
| Soft gate | **OVERALL: PASS** — pages PASS=5 FAIL=0 |
| `/dashboard` notes | `http=200; h1=Dashboard` (no `no_h1`) |
| Report | `salesos/frontend/test-results/smoke-ui/smoke-auth-ui-report.json` — **no** `HTTP 403 …/api/v1/dashboard` |

Nav noise remains (`net::ERR_ABORTED` on RSC/chunks during fast navigation) — not treated as page failure.

**Validation:** **light validated**. **production no-go** — not Production GO. No commit in this follow-up.

---

## Follow-up — demo-admin + `SMOKE_*` env (2026-07-22)

Pentest brief accounts (`admin@salesos.io` / manager / rep) are **absent** in local DB → login **401**. Full write-up: [PROGRESS-WAVE13-AUTH-DEMO.md](./PROGRESS-WAVE13-AUTH-DEMO.md).

Script change (minimal): `smoke-ui.ps1` now reads `SMOKE_EMAIL` / `SMOKE_PASSWORD` from process env (no secrets in repo).

Re-run with env disposable user:

| Result | Value |
|--------|-------|
| Playwright | **1 passed** (~51s), exit **0** |
| Soft gate | **OVERALL: PASS** — pages PASS=5 FAIL=0 |
| Email | `smoke.ui.env.9e2f1e9a@example.com` (disposable) |
| Report | `salesos/frontend/test-results/smoke-ui/smoke-auth-ui-report.json` |

**Validation:** **light validated**. Demo-admin UI path **BLOCKED**. **production no-go** — not Production GO.
