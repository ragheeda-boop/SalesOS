# DEC-088 — STORY-02-02 browser/E2E verify attempt; status remains PARTIAL

> **Status:** **Accepted** (records only)  
> **Date:** 2026-08-01  
> **Story:** STORY-02-02 (`middleware.ts` server-side auth / cookie gate)  
> **Code land:** `3f4b3c8` (already on master)  
> **Validation label:** **light validated** (unit helpers only) — **not** browser pass

---

## Decision

Do **not** close STORY-02-02. Do **not** claim browser pass or Phase 0 GO.

Record Frontend/QA verify attempt against tip `f2c7587` (post Jest-debt R-23 CLOSED `d0fc0e2`):

| Evidence | Result |
|---|---|
| Middleware land `3f4b3c8` | Present — `middleware.ts` + `middleware-auth.ts` + cookie session sync (`AuthSessionSync` / `session.ts`) |
| Jest unit helpers | **14/14 PASS** — `middleware-auth.test.ts` + `session.test.ts` via `node node_modules/jest/bin/jest.js` (**light validated**) |
| Playwright harness | Present — `playwright.config.ts`, `playwright.smoke.config.ts`, `e2e/smoke-auth-ui.spec.ts`, `scripts/smoke-ui.ps1` |
| Browser / E2E redirect | **Not executed** — blocked (see below) |

**Story status:** remains **PARTIAL** (server-side middleware landed; redirect **not** browser-validated).

---

## Blockers (browser pass remains open)

1. **Local FE tooling broken:** `salesos/frontend/node_modules` incomplete — no `.bin`; `next` missing `dist/server/require-hook`; `npm run dev` / `npx playwright` fail. Full `npm install` **not** run (low-load; not authorized as install).
2. **Compose FE/BE not serving:** `:3000` / `:8000` down. `docker compose up -d --build` hit Docker Desktop API **500** mid-pull; partial infra containers (postgres/kafka/neo4j) up without backend/frontend. No `salesos-frontend` image locally; `salesos-backend:latest` present but FE image build did not complete.
3. **No unauthenticated redirect E2E assertion executed** (would need live Next middleware — curl `Location` or Playwright goto `/dashboard` without cookies → `/login?callbackUrl=…`).

---

## What remains for browser pass

1. Restore FE install (`npm ci` / `npm install` in `salesos/frontend`) **or** healthy `docker compose` frontend image on `:3000`.
2. Unauthenticated redirect probe (minimum AC):
   - `GET /dashboard` (no `access_token` cookie) → **3xx** to `/login` with `callbackUrl`
   - Public `/` and `/login` remain reachable
3. Optional authenticated path: `salesos/scripts/smoke-ui.ps1` (Wave 13) once API `/health` + FE `/` return 200.
4. Re-record evidence; only then move STORY-02-02 **PARTIAL → DONE** and claim browser-validated redirect.

---

## Honesty

- **CI GREEN not met.**
- Phase 0 / Railway posture unchanged by this DEC (Ops may land DEC-016 separately).
- No auth/CSRF/RBAC/middleware code changes in this records land.
