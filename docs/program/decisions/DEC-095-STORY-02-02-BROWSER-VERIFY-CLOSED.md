# DEC-095 — STORY-02-02 browser redirect verify CLOSED

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** STORY-02-02 (`middleware.ts` server-side auth / cookie gate)  
> **Code land:** `3f4b3c8` (already on master; no middleware code change in this DEC)  
> **Supersedes:** DEC-088 PARTIAL (browser not executed)  
> **Validation label:** **browser-validated** (unauthenticated live Next redirect probe) — **not** Production GO

---

## Decision

Close STORY-02-02. Server-side unauthenticated redirect is verified against a live Next.js process.

| Evidence | Result |
|---|---|
| Middleware land `3f4b3c8` | Present — unchanged this DEC |
| Jest unit helpers (DEC-088) | **14/14 PASS** — **light validated** (prior) |
| Live FE restore | Host `next@15.5.22` restored (manual tarball after Windows `npm install` EPERM / corrupt `node_modules`); `next dev` on `127.0.0.1:3000` |
| `GET /dashboard` (no cookies) | **307** → `http://localhost:3000/login?callbackUrl=%2Fdashboard` |
| `GET /login` | **200** (after first compile) |
| `GET /` | **200** (after first compile) |
| Authenticated `smoke-ui.ps1` / Playwright | **Not run** — compose backend unhealthy / optional Wave 13 path |

**Story status:** **DONE** (server-side redirect browser-validated).

---

## Probe transcript (curl, tip at run)

```text
# Unauthenticated protected route
curl -sS -D - -o NUL --max-time 60 http://127.0.0.1:3000/dashboard
→ HTTP/1.1 307 Temporary Redirect
→ location: http://localhost:3000/login?callbackUrl=%2Fdashboard

# Public routes (retry after compile)
curl … /login → http_code=200
curl … /      → http_code=200

# Recheck
curl … /dashboard → http_code=307 redirect=…/login?callbackUrl=%2Fdashboard
```

Raw notes also under `salesos/frontend/test-results/story-02-02-browser/redirect-probe.txt` (local; may be gitignored by environment).

---

## Honesty

- Label **browser-validated** applies to the **unauthenticated middleware redirect AC** only (live HTTP against `next dev`).
- Does **not** claim Playwright authenticated smoke, Production GO, External pilot, or whole-pipeline **CI GREEN**.
- No edits to `app/database.py` / `get_db()` (DEC-085 parallel critical).
- Compose `salesos-frontend` image build was attempted but Docker Desktop bake/context issues blocked; host `next dev` used instead.
