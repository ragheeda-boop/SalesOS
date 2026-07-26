# Performance Baseline — Company 360 V3

> **Measured:** 2026-07-26 21:03 UTC  
> **Environment:** Docker Compose (prod), PostgreSQL via PgBouncer, Redis  
> **Method:** curl from inside backend container (`docker exec`)  
> **Status:** Build validated — baseline established  

---

## Backend API Latency (from inside container)

| Endpoint | Metric | TTFB (s) | Total (s) | Notes |
|----------|--------|----------|-----------|-------|
| `GET /api/v1/health` | avg (10 runs) | **0.011** | 0.011 | Consistent, cold start: 0.020 |
| `GET /api/v1/health` | p95 | **0.023** | 0.023 | Worst case |
| `GET /api/v1/health` | p50 | **0.008** | 0.008 | Median |
| `GET /csrf-token` | single | **0.005** | 0.006 | In-memory generation |
| `POST /identity/login` | single | **0.012** | 0.013 | Password verify + JWT sign |
| `GET /.well-known/jwks.json` | single | **0.004** | 0.004 | Cached after first load |
| `GET /companies` | single | **0.093** | 0.093 | PgBouncer query overhead |
| `GET /companies/{id}/360` | single | **0.011** | 0.012 | Not found (empty DB) |
| `GET /companies/{id}/intelligence` | single | **0.004** | 0.005 | Not found (empty DB) |

### Key Observations

- **Health endpoint:** sub-25ms consistently (target: <200ms) ✅
- **Auth flow (CSRF + Login):** ~17ms total (target: <200ms) ✅
- **JWKS:** sub-5ms after cache (target: <50ms) ✅
- **Companies list:** ~93ms — slowest endpoint; likely PgBouncer connection setup on cold query
- **Company 360 / Intelligence:** measured as "not found" (no companies in test DB); **real latency TBD when companies exist**

### Frontend (Next.js SSR)

> ⚠️ Not measurable from inside backend container (different network namespace).  
> Needs host-side measurement or Playwright Lighthouse audit.

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| TTFB (`/v3/companies`) | <200ms | TBD | Not measured |
| TTFB (`/`) | <200ms | TBD | Not measured |
| JS Bundle Size | <500KB gzip | TBD | Not measured |
| LCP | <2.5s | TBD | Not measured |

---

## Targets (Production)

| Metric | Target | Justification |
|--------|--------|---------------|
| Backend Health TTFB | <200ms | Liveness probe SLA |
| Auth Flow (CSRF + Login) | <300ms | User perception |
| Companies List API | <500ms | Paginated query with PgBouncer |
| Company 360 API | <500ms | Multi-table JOIN |
| Intelligence API | <1000ms | Analytics computation |
| JWKS | <50ms | Cached RSA public key |
| Frontend TTFB (SSR) | <500ms | Next.js server-side render |
| Frontend TTFB (CSR) | <200ms | Client-side navigation |
| JS Bundle (initial) | <500KB gzip | Mobile performance |
| LCP | <2.5s | Core Web Vital |
| FID | <100ms | Core Web Vital |
| CLS | <0.1 | Core Web Vital |

---

## Gaps / Next Steps

1. **Frontend TTFB:** Measure from host using Playwright or Lighthouse
2. **Intelligence API real latency:** Seed test company and measure
3. **Companies list optimization:** Investigate 93ms baseline
4. **JS Bundle analysis:** Run `next build && ANALYZE=true next build`
5. **Core Web Vitals:** Lighthouse audit in Playwright

---

## How to Re-measure

```bash
# Backend API (from host)
docker exec salesos-backend-1 curl -s -o /dev/null -w "TTFB: %{time_starttransfer}s\n" http://localhost:8000/api/v1/health

# Full performance script
docker cp perf-baseline.sh salesos-backend-1:/tmp/
docker exec salesos-backend-1 sh /tmp/perf-baseline.sh

# Frontend (from host — requires exposed port or Playwright)
npx playwright test e2e/27-v3-company-intelligence.spec.ts --project=chromium
```
