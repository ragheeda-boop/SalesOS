# APPENDIX C — Findings Register (P0–P4)

Severity rubric: **P0** blocks GA; **P1** high risk / must-fix before external pilot; **P2** medium; **P3** low; **P4** polish/debt.

---

## P0

### GA-P0-SEC-01 Decision Center cross-tenant IDOR
- **Evidence:** `domains/decision_center/postgres_repo.py` `get_decision` filters `DecisionModel.id` only; router ignores tenant for authorization
- **Root cause:** Missing `(id, tenant_id)` authorization on by-ID reads/writes (audit/feedback similar)
- **Impact:** Authenticated tenant A can read/mutate tenant B decisions if IDs are guessable/leaked
- **Recommendation:** Enforce tenant on all decision/audit/feedback queries; return 404 on mismatch
- **Plan:** 1–2d + tests
- **Source:** [Security backend deep dive](1a2127a4-b90d-4e2d-9f0d-43b1ac342440) (spot-verified)

### GA-P0-SEC-02 Webhook SSRF + InMemory persistence
- **Evidence:** `modules/webhooks/service.py` posts to `sub.url` via httpx; defaults to `InMemoryWebhook*Repository`
- **Root cause:** No URL allowlist / private-IP block; no Postgres wiring in router factory
- **Impact:** SSRF to internal network; subscriptions lost on restart / multi-replica inconsistency
- **Recommendation:** SSRF harden (block RFC1918/metadata); persist to Postgres; require HTTPS + DNS rebinding controls
- **Plan:** 2–3d
- **Source:** security deep-dive (spot-verified)

### GA-P0-01 Frontend ESLint errors block CI/build
- **Evidence:** `npm run lint` / `npm run build` fail; `TenantList.tsx:28` hooks violation
- **Root cause:** Hook called inside event handler
- **Impact:** Stage 1 CI fail; no trustworthy production frontend artifact from source
- **Recommendation:** Move `useUpdateAdminTenant` to component top-level; fix remaining ESLint errors
- **Plan:** 0.5–1d — fix 4 errors, re-run lint+build

### GA-P0-02 TypeScript errors
- **Evidence:** `npx tsc --noEmit` 3 errors (APPENDIX-A)
- **Root cause:** Type misuse in automation + Skeleton props mismatch
- **Recommendation:** Fix types; add CI gate already present — make it green
- **Plan:** 0.5d

### GA-P0-03 Alembic not at head on running environment
- **Evidence:** `alembic current=0033`, `heads=0038`
- **Root cause:** Migrations authored but not applied/deployed to local/runtime DB
- **Impact:** Missing marketplace/admin/employee/decision_center schema → latent runtime failures
- **Recommendation:** `alembic upgrade head` in controlled env; add migrate-on-deploy check; fail health if behind
- **Plan:** 0.5–1d + verification queries

### GA-P0-04 Backend unit tests not green
- **Evidence:** 4 failed + 16 errors (+ MCP collection break)
- **Root cause:** Missing optional dep `mcp`; admin test AttributeError; intelligence test regressions
- **Recommendation:** Fix or quarantine MCP tests; repair admin API tests; restore intelligence tests
- **Plan:** 2–4d

---

### GA-P0-05 Forecast hardcodes demo opportunity
- **Evidence:** `app/routers/commercial.py` — after `DEMO_MODE` check, still `CommercialInput(opportunity_id="demo-1", …)`
- **Impact:** Forecast feature is not production-truthful
- **Recommendation:** Load real opportunities for tenant; gate demo path strictly
- **Plan:** 1d
- **Source:** [Frontend product AI gaps](36b6e408-c9cc-4c91-8623-074166bf9425) (spot-verified)

### GA-P0-SEC-03 Knowledge graph SQL missing tenant filters / DIE memory-primary
- **Evidence (static):** KG `repository.py` SQL fallbacks without `tenant_id`; `decision_runtime` execute from in-memory dict
- **Recommendation:** Disable SQL fallback in prod or add tenant predicates; DIE accept/execute from Postgres by `(id, tenant_id)`
- **Plan:** 3–5d
- **Source:** security deep-dive (**static**; not runtime-exploited in this audit)

---

## P1

### GA-P1-SEC-01 CSRF skip on any non-empty X-API-Key
- **Evidence:** `common/middleware.py:388-391` returns early if header present (no validation)
- **Recommendation:** Skip CSRF only after successful API-key auth into request state
- **Plan:** 0.5d

### GA-P1-SEC-02 Rate-limit treats any Bearer as authenticated tier
- **Evidence:** `common/middleware.py` checks `Authorization: Bearer ` prefix only
- **Plan:** 0.5d

### GA-P1-PROD-01 Frontend Decision Engine stubs
- **Evidence:** `frontend/packages/platform/decision/index.ts` — six `Not implemented` throws
- **Plan:** Wire to Decision Center API or remove from GA surface

### GA-P1-01 Stale frontend Docker image vs source routes
- **Evidence:** HTTP 404 for `/copilot`, `/analytics`, `/marketplace`, `/employees`, `/knowledge`, `/signals`, `/rules`, `/activities` while source `page.tsx` exists
- **Recommendation:** Rebuild/redeploy frontend image from current source after build green
- **Plan:** 1d (blocked by P0-01/02)

### GA-P1-02 Runtime deps reported not_configured
- **Evidence:** `/health/detailed` cache/graph/kafka not_configured; Neo4j unhealthy
- **Recommendation:** Fix Neo4j health; verify Redis URL/init; decide Kafka vs in_memory for GA; alert on degraded
- **Plan:** 2–3d

### GA-P1-03 Release docs conflict / overclaim GO
- **Evidence:** APPENDIX-B
- **Recommendation:** Mark GO docs as superseded; require evidence-backed re-certification
- **Plan:** 1d docs governance

### GA-P1-04 Missing AGENTS.md / .cursor/rules
- **Evidence:** Glob 0
- **Recommendation:** Add platform AGENTS.md reflecting AQLIYA boundaries + SalesOS as first product
- **Plan:** 1d

### GA-P1-05 AQLIYA multi-product gap
- **Evidence:** No AuditOS/DecisionOS/LocalContentOS code
- **Recommendation:** Either scope GA as **SalesOS GA** only, or schedule platform product shells
- **Plan:** Product decision + 0–many sprints

### GA-P1-06 Stub AI/runtime engines
- **Evidence:** agent/workflow/scheduler/execution/simulation ~1 LOC; `feature_ai_copilot=False`
- **Recommendation:** Do not market AI-native GA; gate features; implement or remove stubs
- **Plan:** weeks (product-dependent)

### GA-P1-07 Auth failure returns 422 not 401
- **Evidence:** Missing `authorization` header → FastAPI validation 422
- **Recommendation:** Custom dependency / exception handler mapping to 401/403
- **Plan:** 1d

### GA-P1-08 Host developer experience broken for backend
- **Evidence:** Poetry/asyncpg Windows build failure; Python version skew vs CI 3.12
- **Recommendation:** Document Docker-only backend; pin poetry env to 3.12; provide WSL path
- **Plan:** 1–2d docs/tooling

### GA-P1-09 `/metrics` requires Authorization (ops friction)
- **Evidence:** `/metrics` → 422 missing authorization
- **Recommendation:** Separate Prometheus scrape path with network policy / bearer, not app JWT
- **Plan:** 1d

---

## P2

### GA-P2-01 Tailwind color classes vs design tokens (many warnings)
### GA-P2-02 service_version still `0.1.0` while CHANGELOG claims v2/v3
### GA-P2-03 Observability split across root vs salesos compose
### GA-P2-04 Postgres healthcheck flapping (was unhealthy then healthy)
### GA-P2-05 Duplicate admin router registration patterns (`runtime.admin_router` + `modules.admin`)
### GA-P2-06 Large `modules/admin/router.py` (~1100+ lines) — maintainability
### GA-P2-07 Knowledge graph / data fabric large modules — complexity risk
### GA-P2-08 Rate limit hit during CSRF probe — confirm identity limiter not locking out legit traffic incorrectly

---

## P3

### GA-P3-01 `utcnow()` deprecation warnings in intelligence agent_base
### GA-P3-02 Next `<img>` vs `next/image` in TourOverlay
### GA-P3-03 React hook exhaustive-deps warnings
### GA-P3-04 Missing Arabic docs (DOC-04 historical)

---

## P4

### GA-P4-01 Legacy scrapers / root Python scripts clutter monorepo
### GA-P4-02 `sales-os/` legacy vs `salesos/` primary naming confusion
### GA-P4-03 Zip design assets at repo root
