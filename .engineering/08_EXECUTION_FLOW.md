---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 08 â€” EXECUTION FLOW

> End-to-end flows as-built. Backend health evidence: `app/main.py` exposes `/ping`, `/health/live`, `/health/detailed`; `app/health.py` drives checks.

## 1. Request lifecycle (as-built)

```
1. Request â†’ nginx/caddy/vercel â†’ FE (Next.js) or BE (FastAPI)
2. FE middleware.ts: check token â†’ refresh if needed â†’ allow/deny route
3. FE api/client.ts: attach Bearer JWT (browser)
4. BE: security middleware (app/boot/security_headers.py) â†’ tenant dep â†’ auth guard
5. Router (app/boot/routers.py registry) â†’ module/domain service
6. Service â†’ runtime engine (if needed) â†’ sdk events â†’ DB via SQLAlchemy
7. Response â†’ client
```

## 2. Auth flow (as-built; identity module)

POST `/api/v1/identity/register` â†’ tenant+user+hashed pw â†’ login `/login` â†’ access+refresh JWT (RS256) â†’ `/refresh` rotates â†’ `/logout` / `/logout-all` â†’ blacklist.
Endpoints (12): POST tenants Â· register Â· login Â· refresh Â· logout Â· logout-all Â· forgot-password Â· reset-password Â· GET users/me Â· users Â· sessions Â· csrf-token Â· `.well-known/jwks.json`.
JWKS served from `app/modules/identity/jwks.py` (RS256, keys in `_keys/` ðŸ”’).
**Refresh-token tables note:** `0012_refresh_token_tables` is in the Alembic chain; whether refresh-token family rotation is actually enabled at runtime is **not verified** (requires `alembic current` on a live DB â€” see `13`, `15`; the v3.0 "NOT enabled" claim was retracted as unverified).

## 3. Search flow (as-built)

`app/routers/search.py` â†’ `domains/search/` â†’ `runtime/search_runtime/` â†’ Postgres (pgvector/pg_trgm) + Meilisearch â†’ results.
Suggested/similar endpoints: `/search/suggest`, `/search/similar/*`.

## 4. Event flow (as-built; default degraded)

Publish â†’ `sdk/events/` â†’ bus (`EVENT_BUS_TYPE`):
- `in_memory` (compose default) â€” events never leave the process.
- `kafka` (K8s configmap) â€” events to Kafka topics â†’ Celery consumers.
**Split-brain risk:** compose and K8s disagree on bus type â†’ event-driven behavior differs per environment. Observed, NOT fixed.

## 5. Async/background (as-built)

Celery `-A app.celery_app`; beat schedule: 9 jobs (e.g., scraping, health, aggregation). Optional Kafka. K8s cron alternative per configmap.

## 6. Capability registry flow (as-built)

`runtime/capability_framework/__init__.py` decorators register capabilities â†’ `router.py` exposes `GET /api/v1/capabilities` (verify_token) â†’ consumers: source_of_truth, ux_runtime, ui_schema_engine, object_viewer, widget_engine (`WidgetRegistry.generate_from_capabilities()`).

## 7. Data pipeline flow (data/ â€” NOT runtime GA path)

`data/scripts/phase4_identity_v4.py` (identity import) etc. â†’ Normalize â†’ Notion/DB. These are import pipelines, not SalesOS runtime path (AGENTS.md Â§2).

## 8. CI/CD flow (as-built; `.github/workflows/`)

```
push/PR â†’ ci.yml (lint+typecheck+unit+integration+build)
       â†’ security-scan.yml (gitleaks BLOCKING, SAST)
       â†’ docker-smoke.yml (docker build+smoke; e2e job has NO services â€” observed)
       â†’ deploy.yml (deploy to env; undeclared outputs slot/image_tag â€” SEC finding)
       â†’ deploy-staging / deploy-production (stage/prod)
```

## 9. When this file changes

- On flow changes (new engine wiring, bus change, auth change, CI step change). Mirror `14` (API), `16` (deploy), `12` (CI).
