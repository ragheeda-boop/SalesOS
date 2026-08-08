# Progress — Wave 13 Full UI Crawl

**Date:** 2026-07-22  
**Product:** SalesOS — local primary FE `:3000` + API `:8000`  
**Scope:** Authenticated full-site UI crawl (primary nav + deep routes + visible in-app clicks)  
**Validation class:** **light validated** UI crawl  
**Production GO:** **NO** (explicitly not claimed)  
**Soak:** untouched (read-only browse; PID ~21856 on `:8000`/`:3000` not killed)  
**Overall (script soft gate):** **PASS** (Playwright exit `0`) — **49/49 pages opened**; API/data residuals documented below  

---

## Verdict

Demo admin login + systematic crawl of **all primary sidebar destinations** and **important deep links** completed against the live primary stack. Every catalogued route returned an HTTP 200 shell (no hard page 404 / login redirect / Application error). **136 clicks** attempted on visible main tabs/buttons/links (128 OK / 8 soft fail).

This is **not** “every DOM click in the product,” **not** browser GA, and **not** Production GO. Several pages render empty or partial UI because underlying APIs return **422 / 404 / 500** or are **CORS-blocked** (`127.0.0.1` FE → `localhost` API host mix).

---

## Summary table (pages)

| Route | Cat | Open | Notes |
|-------|-----|------|-------|
| `/login` | auth | PASS | h1=Sign In to SalesOS |
| `/register` | auth | PASS | h1=Create New Account |
| `/dashboard` | nav | PASS | h1=Dashboard |
| `/companies` | nav | PASS | h1=Companies; 1 click timeout (date filter) |
| `/employees` | nav | PASS | h1=Employees; 1 click timeout (Role) |
| `/employees/me` | nav | PASS | no_h1 |
| `/contacts` | nav | PASS | h1=Contacts |
| `/opportunities` | nav | PASS | no_h1 |
| `/activities` | nav | PASS | h1=Activities |
| `/revenue` | nav | PASS | no_h1 |
| `/pipeline` | nav | PASS | h1=Pipeline |
| `/forecast` | nav | PASS | no_h1 |
| `/search` | nav | PASS | h1=Advanced Search |
| `/decisions` | nav | PASS | no_h1 |
| `/meetings` | nav | PASS | no_h1 |
| `/rag` | nav | PASS | h1=المساعد الذكي |
| `/ai` | nav | PASS | h1=AI Prompt Registry; empty-state hint |
| `/graph` | nav | PASS | h1=Knowledge Graph |
| `/copilot` | nav | PASS | h1=AI Copilot (**UI shell** — not GA AI) |
| `/automation` | nav | PASS | h1=Automation; **API 500** workflows |
| `/analytics` | nav | PASS | h1=Analytics Overview; API 422s |
| `/signals` | nav | PASS | h1=Signals; empty-state hint |
| `/rules` | nav | PASS | h1=Business Rules |
| `/monitoring` | nav | PASS | h1=System Monitoring |
| `/customer-success` | nav | PASS | no_h1 |
| `/settings` | nav | PASS | h1=Settings |
| `/admin` | nav | PASS | h1=Admin Panel |
| `/` | deep | PASS | Marketing landing h1=SalesOS |
| `/admin/flags` | deep | PASS | h1=Feature Flags |
| `/admin/config` | deep | PASS | h1=System Config |
| `/admin/audit` | deep | PASS | h1=Audit Log |
| `/admin/tenants` | deep | PASS | h1=Tenant Management |
| `/decisions/templates` | deep | PASS | no_h1 |
| `/revenue/territories` | deep | PASS | h1=Territory Map; click timeouts |
| `/revenue/quotas` | deep | PASS | h1=Quota Management |
| `/pipeline/analytics` | deep | PASS | no_h1; API 422 |
| `/analytics/sales` | deep | PASS | no_h1; API 422 |
| `/analytics/revenue` | deep | PASS | no_h1; API 422 |
| `/analytics/pipeline` | deep | PASS | no_h1; API 422 |
| `/analytics/employees` | deep | PASS | no_h1; API 422 |
| `/analytics/automation` | deep | PASS | no_h1; API 500 workflows |
| `/analytics/reports/builder` | deep | PASS | h1=Report Builder |
| `/automation/workflows/new` | deep | PASS | h1=مُنشئ سير العمل |
| `/automation/analytics` | deep | PASS | no_h1; API 500 |
| `/search/analytics` | deep | PASS | no_h1; **API 404** |
| `/knowledge` | deep | PASS | h1=Knowledge Graph |
| `/knowledge/connectors` | deep | PASS | h1=Data Fabric Connectors |
| `/marketplace` | deep | PASS | h1=Marketplace |
| `/copilot/telemetry` | deep | PASS | no_h1; **API 404** |

**Page open:** **49 PASS / 0 FAIL**  
**Clicks:** **136 attempted** (128 OK / **8 fail** — mostly filter/date control timeouts + one marketing “Sign in” auth_redirect)  

Full auto table: `evidence/wave13-full-ui-crawl/full-ui-crawl-summary.md`  
Machine JSON: `evidence/wave13-full-ui-crawl/full-ui-crawl-report.json`  
(No passwords in evidence; email redacted to domain + local prefix only.)

---

## Critical / notable bugs (honest)

Page shells passed; these are **data / API / interaction** residuals that block “fully working” product surfaces:

| Severity | Finding | Evidence |
|----------|---------|----------|
| **P1** | `GET /api/v1/workflows` → **HTTP 500** (and `/workflows/analytics` **500**) | `/automation`, `/automation/analytics`, `/analytics/automation`, report builder |
| **P1** | `GET /api/v1/search/analytics` → **HTTP 404** | `/search/analytics` |
| **P1** | `GET /api/v1/copilot/telemetry` → **HTTP 404** | `/copilot/telemetry` |
| **P2** | Widespread **HTTP 422** on analytics/revenue surfaces | `pipeline/analytics`, `revenue/dashboard`, `forecast`, `workspace`, `employees?limit=100` |
| **P2** | Browser **CORS** when FE origin is `http://127.0.0.1:3000` calling `http://localhost:8000` | Many console “blocked by CORS policy” on pipeline/settings/admin/rag/signals/decisions |
| **P3** | **no_h1** on 17 routes | a11y / landmark residual (page still rendered) |
| **P3** | Soft click timeouts on date/filter controls | `/companies` From date; `/employees` Role; territories/quotas/builder |
| **Info** | Empty-state hints | `/ai`, `/signals` |
| **Info** | `/copilot` opens as UI shell | Do not market as live GA AI (`AI_HONESTY.md`) |

No hard auth failure for demo admin after login. No page-level Application error / Next 404 on catalogued routes in this run.

---

## Coverage honesty

| Layer | Estimate | Meaning |
|-------|----------|---------|
| Catalogued routes (nav + deep + auth) | **~100%** of listed set (49 unique paths) | Sidebar `NAV_KEYS` + important app-router deep links |
| “Every click” literal | **~25–40%** of interactive surface | Cap **8 clicks/page** on visible `main` tabs/buttons/links; destructive / logout / file I/O / external skipped |
| Entity deep links (`/companies/[id]`, `/employees/[id]`, `/opportunities/[id]`, marketplace plugin config) | **Not crawled** (no seeded ID discovery this run) | Note as skipped |
| Modals / infinite scroll / drag-drop / CRUD submit | **Skipped** by design | Dismiss-only if dialog opened |
| Browser MCP | **Not used** | Playwright automation preferred |
| Firefox / WebKit / mobile | **Not run** | Chromium only |
| Production / staging cloud | **Not run** | Local primary only |

Script reported `coverageEstimatePct=104` because auth routes were counted separately from the deep catalog denominator — treat route coverage as **~100% of the crawl catalog**, not >100% of the product.

---

## Auth path

1. Credentials via env only (`SMOKE_EMAIL` / `SMOKE_PASSWORD` → mapped to `E2E_USER_*`); **not** written into evidence JSON.  
2. UI login on `/login` (email/password inputs; labels visual-only).  
3. API token seed fallback exists if UI login does not persist `access_token`.  
4. Demo admin domain recorded as `salesos.io` only.

---

## Artifacts / how to re-run

| Path | Role |
|------|------|
| `salesos/frontend/e2e/full-ui-crawl.spec.ts` | Reusable full crawl (env credentials) |
| `salesos/frontend/playwright.full-crawl.config.ts` | Chromium-only; **no** `webServer` (reuses soak FE) |
| `salesos/scripts/full-ui-crawl.ps1` | Preflight + run + print matrix |
| `docs/audit/ga-engineering-audit/evidence/wave13-full-ui-crawl/` | Reports + screenshots dir |

```powershell
cd salesos
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '<from vault / local only>'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\full-ui-crawl.ps1

# Optional knobs:
# -MaxClicks 8
# -FrontendUrl http://127.0.0.1:3000
# -BaseUrl http://127.0.0.1:8000
# Prefer 127.0.0.1 for FE; if API CORS noise dominates, align API host with FE origin.
```

**Commands run (this wave):**

- API `/health` + FE `/login` preflight (**200**)  
- `npx playwright test --config playwright.full-crawl.config.ts` (~5.5 min)  
- Evidence written under `evidence/wave13-full-ui-crawl/`  

**Not run:** full e2e suite, npm build/lint, migrate, commit, soak kill.

---

## Skipped (explicit)

- Virtual staging `:3002` (primary `:3000` healthy)  
- Logout / delete / export / upload controls  
- External links / mailto  
- Dynamic entity detail URLs without ID discovery  
- Infinite list pagination beyond first link budget  
- Claiming Production GO or 48h soak complete  

---

## Follow-up — API residual fixes (2026-07-22 evening)

**Validation class:** **light validated** (demo-admin API probe after backend restart)  
**Production GO:** **NO**  
**Soak:** untouched  

### Root causes (before)

| Symptom | Root cause |
|---------|------------|
| `GET /workflows` **500** | ORM selected missing `workflow_definitions.timeout_seconds`; swallowed as 500. `/workflows/analytics` missing (hit `{id}`). |
| `GET /search/analytics`, `/copilot/telemetry` **404** | FE called aggregate routes that were never registered (only `/copilot/telemetry/stats` etc. existed). |
| Analytics **422** storm | Many FE pages called `api.get` without `X-Tenant-Id` while backend required `Header(...)`. |
| CORS `127.0.0.1:3000` → `localhost:8000` | CORSMiddleware was **innermost**; preflight/error paths lacked ACAO. `Accept` missing from allow_headers. |
| `revenue/dashboard` / `pipeline/analytics` **500** (after 422 fixed) | Schema drift: `asyncio.gather` on one asyncpg conn; `stage_name`/`health`/`company_features`/`pipeline_stage_entries` mismatches; wrong import path for `PipelineHistoricalPeriod`. |

### After (demo `admin@salesos.io` probe — no passwords in evidence)

Evidence: `evidence/wave13-api-residual-fix/probe-2026-07-22T180624Z.json` (+ later full matrix `probe-2026-07-22T18…` from `salesos/scripts/probe-wave13-api-residuals.ps1`).

| Endpoint | Before | After |
|----------|--------|-------|
| `GET /api/v1/workflows` | 500 | **200** |
| `GET /api/v1/workflows/analytics` | 500/404 | **200** |
| `GET /api/v1/search/analytics?days=30` | 404 | **200** |
| `GET /api/v1/copilot/telemetry?days=30` | 404 | **200** |
| `GET /api/v1/pipeline/analytics` | 422→500 | **200** |
| `GET /api/v1/revenue/dashboard` | 422→500 | **200** |
| `GET /api/v1/forecast` | 422 | **200** |
| `GET /api/v1/workspace` | 422 | **200** |
| `GET /api/v1/employees?limit=100` | 422 | **200** |
| Auth-only (no `X-Tenant-Id`, JWT has tenant) | 422 | **200** |
| CORS OPTIONS `http://localhost:3000` | flaky | **200** + ACAO |
| CORS OPTIONS `http://127.0.0.1:3000` | blocked | **200** + ACAO |

### Files changed (minimal)

- `salesos/backend/app/dependencies.py` — tenant from JWT if header omitted  
- `salesos/backend/app/boot/middleware.py` + `middleware_setup.py` — CORS outermost  
- `salesos/backend/app/config.py` — allow `Accept`/`Accept-Language`  
- `salesos/docker-compose.yml` — explicit `ALLOWED_HOSTS` both origins  
- `salesos/backend/app/routers/workflows.py` — harden list + add `/workflows/analytics`  
- `salesos/backend/app/routers/search.py` — add `/search/analytics`  
- `salesos/backend/app/routers/copilot.py` — add aggregate `/copilot/telemetry`  
- `salesos/backend/app/routers/revenue.py` — sequential queries; tolerate missing `company_signals`  
- `salesos/backend/runtime/pipeline_analytics/*` — schema-aligned SQL; sequential summary; fix import  
- `salesos/frontend/src/lib/api/client.ts` — inject `X-Tenant-Id` (needs FE image rebuild to ship in Docker FE)  
- Local DB: `ALTER TABLE workflow_definitions ADD COLUMN IF NOT EXISTS timeout_seconds`  

### Remaining OPEN

- FE Docker image still built with old `client.ts` until rebuild (backend JWT tenant fallback covers 422 for now).  
- `company_signals` / `company_features` tables still absent locally (signals empty; health uses probability proxy).  
- Search analytics log is process-memory only until search callers record events.  
- Copilot telemetry empty unless tools log (feature_ai_copilot still default False — honesty intact).  
- Full UI re-crawl **not** re-run this follow-up.  

**Not claimed:** Production GO, browser GA, soak complete, commit.

---

*Evidence governs. Light validated UI crawl + light validated API residual probe.*
