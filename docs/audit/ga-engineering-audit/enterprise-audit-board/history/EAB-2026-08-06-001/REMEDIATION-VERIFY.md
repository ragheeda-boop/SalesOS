# Remediation Verify Note — EAB-2026-08-06-001

**Date:** 2026-08-06  
**Scope:** Light runtime verify for SEC-01 / SEC-02 after Waves 1–2  
**Validation:** **light validated** (Docker probe; no full pytest/npm)  
**Production GA:** **NO-GO** unchanged · No commit

---

## Environment

| Item | Value |
|------|-------|
| Compose SoT | `salesos/docker-compose.yml` |
| Backend | `salesos-backend-1` (host bind `./backend:/app`) |
| Method | AST parse → recreate/restart → HTTP probes + boot logs |

---

## Evidence

### Static (in-container files)

| Check | Result |
|-------|--------|
| `db_session_factory = async_session` | present |
| `FactoryBoundRepository` inits (timeline/FS/DC/opportunity/workflow) | present |
| `_timeline_session = sess` | **0** matches |
| Decision Runtime prefix `/api/v1/decision-runtime` | present |
| ContextVar `reset_current_tenant_id` in finally | present |
| AST parse `database.py` / `startup.py` / `middleware.py` / `routers.py` | **AST_OK** |

### Boot (after RS256 pin + TrustedHost hostname fix)

| Log / signal | Result |
|--------------|--------|
| JWT_ALGORITHM in container | **RS256** (compose override; `.env` had HS256 leftover) |
| `timeline recorder: ok` / `decision center: ok` / `feature store domain: ok` | ok (factory path) |
| `db_session_factory: wired (async_session)` | expected at Phase complete |
| `SalesOS startup complete` | **~23.7s** |
| `Application startup complete` / Uvicorn running | yes |

### HTTP probes (post-fix)

| Probe | Result | Reading |
|-------|--------|---------|
| `GET /health` | **200** | Process live |
| `GET /api/v1/decisions` | **401** | Auth gate (not middleware fail-open 200/skip) |
| `GET /api/v1/decisions` + `X-API-Key: probe-invalid` | **401** (or gated) | API-key path exercises factory-backed middleware |
| `GET /docs` | **200** | (prior probe) |

### Incident during verify (honest)

1. **First restart** failed: `.env` `JWT_ALGORITHM=HS256` vs ADR-102 RS256-only Settings validator.  
   **Mitigation:** compose `JWT_ALGORITHM: RS256` override (does not weaken auth).  
   **Human follow-up:** set host `.env` to `JWT_ALGORITHM=RS256` for consistency.
2. **Boot succeeded but `/health` → 400 Invalid host header:** `TrustedHostMiddleware` was given CORS *origins* (`http://localhost:3000`) instead of hostnames. Exposed by restart of long-lived process.  
   **Fix:** derive trusted hostnames (`localhost`, `127.0.0.1`, `backend`, `testserver` + hosts parsed from origins) in `boot/middleware.py`. CORS origins unchanged.

---

## Not validated

- Full pytest / adversarial entitlement suite  
- npm lint/build / browser SSR paint  
- Staging soak / WAL restore  
- Live tenant GUC SQL assertion under load  

---

## Conclusion

SEC-01 factory wiring + fail-closed middleware and SEC-02 factory-session boot path are **light validated** in local Docker after corrective pins. Does **not** authorize Production GO.

---

*Verify — EAB-2026-08-06-001 — light validated — production no-go — no commit*
