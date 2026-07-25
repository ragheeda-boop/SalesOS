# Progress — Wave 12 LOCAL VIRTUAL Staging (NOT cloud / VPS)

**Date:** 2026-07-22  
**IDs:** PROD-W12-001 / PROD-W12-002 (local stand-in only)  
**Product:** SalesOS (AQLIYA)  
**Verdict:** **DONE** for **local virtual staging tabletop**  
**Cloud / VPS staging:** still **BLOCKED** (no real staging host)  
**Production:** still **NO-GO**  
**Validation class:** **light validated** (local compose on alternate ports)

> This is **local virtual staging**, not cloud/VPS staging.  
> It does **not** close the GA cloud-staging blocker. It documents a practical tabletop path until a real VPS exists.

---

## Honesty summary

| Claim | Status |
|-------|--------|
| Local virtual staging stack (compose project `salesos-staging-local`) | **DONE** |
| Health on virtual ports API `:8001` / FE `:3002` | **PASS** (tabletop day) |
| Deploy + rollback tabletop (digest pin + recreate) | **PASS** (local) |
| Cloud / VPS staging deploy + rollback | **BLOCKED** / **not validated** |
| Production GO | **NO-GO** — do not claim |
| 48h soak (`:8000`/`:3000`, PID ~21856) | **NOT touched** (preserved) |

---

## Ports & project (clash avoidance)

| Role | Primary / soak | Virtual staging |
|------|----------------|-----------------|
| Compose project | `salesos` (default) | `salesos-staging-local` |
| API | `:8000` | `:8001` |
| Frontend | `:3000` | `:3002` (Grafana on primary uses `:3001`) |
| Postgres | `:5432` | `:5433` |
| Redis | `:6379` | `:6380` |

---

## Light profile (resource-constrained host)

Host had **&lt;1 GB free RAM** with soak + primary stack. Virtual staging uses **postgres + redis + backend + frontend only** (no Neo4j / Kafka / monitoring).

To free RAM without killing soak, operators may temporarily stop primary monitoring / Kafka path (`grafana`, `prometheus`, `alertmanager`, exporters, `schema-registry`, `kafka`, `zookeeper`). Documented in evidence; restart those later if needed.

---

## How to start / stop

```powershell
cd salesos

# First time: copy example (gitignored filled file)
Copy-Item .env.staging.local.example .env.staging.local

# Up (stamps alembic_version=0040 on empty virtual DB — see limitations)
.\scripts\staging-virtual-up.ps1
# Optional: also stop primary monitoring first
.\scripts\staging-virtual-up.ps1 -FreeMonitoring

# Deploy / rollback tabletop + evidence
.\scripts\staging-virtual-deploy-rollback.ps1

# Down (keep volumes)
.\scripts\staging-virtual-down.ps1
# Down + wipe virtual DB/redis volumes
.\scripts\staging-virtual-down.ps1 -RemoveVolumes
```

Compose file: `salesos/infra/staging/docker-compose.staging-virtual.yml`  
Env template: `salesos/.env.staging.local.example` (no cloud secrets; local placeholders only)

---

## Tabletop result (2026-07-22)

| Step | Result |
|------|--------|
| Pre image digests recorded | backend `sha256:27ac6fc72b41…99569ed` (`salesos-backend:latest`); frontend `sha256:f3fd7da90c6f…7b40e83` (`salesos-frontend:local`) |
| Rollback pins tagged | `salesos-backend:staging-virtual-prev`, `salesos-frontend:staging-virtual-prev` |
| Deploy analogue (`force-recreate --no-deps`) | API **200**, FE **200** |
| Rollback analogue (pin tags recreate) | API **200**, FE **200** |
| Soak `:8000`/`:3000` after tabletop | **200** / soak PID **21856** alive |
| Historical digests from WAVE12-TABLETOP (`4d7efe7e` / `ed834c95`) | **Not present** on host — new pins recorded |

**Evidence:** `docs/audit/ga-engineering-audit/evidence/wave12-staging-virtual/`

| File | Role |
|------|------|
| `pre-2026-07-22T165405Z.json` | Pre digests + health |
| `deploy-2026-07-22T165405Z.log` | Deploy recreate log |
| `rollback-2026-07-22T165405Z.log` | Rollback recreate log |
| `tabletop-complete-2026-07-22T165405Z.json` | Final PASS record |

---

## Known limitations (honest)

1. **Not cloud staging** — no SSH VPS, no GitHub Environment secrets, no GHCR pull on remote host.  
2. **Schema for auth** — fresh `alembic upgrade head` still fails at `0028` on empty DBs. Virtual up stamps `0040`, then (if `users` missing) applies **schema-only** dump from primary and seeds demo users. See [evidence/wave12-staging-virtual/auth-fix-2026-07-22.md](./evidence/wave12-staging-virtual/auth-fix-2026-07-22.md).  
3. **Backend volume mount** — virtual backend mounts `salesos/backend` (like primary) so `/app/.local` packages resolve; bare image alone hit strawberry/pydantic `ImportError` on this host. **JWKS keys** use isolated volume `staging_local_jwks` (do not share primary `_keys` — different `SECRET_KEY`).  
4. **FE bake-time API URL** — `salesos-frontend:local` was built with `NEXT_PUBLIC_API_URL=http://localhost:8000`. Virtual up patches `.next` to `:8001` at runtime; prefer rebuilding FE with `:8001` for permanence.  
5. **RAM** — double-stack is tight; prefer light profile + optional monitoring stop. Primary backend may flap under memory pressure.  
6. **Cloud staging GA line remains BLOCKED** until real VPS + secrets + workflow publish — see [PROGRESS-WAVE12-STAGING-UNBLOCK.md](./PROGRESS-WAVE12-STAGING-UNBLOCK.md).

---

## Auth on virtual FE (`:3002`) — 2026-07-22 fix

| Check | Result |
|-------|--------|
| API `:8001` login `admin@salesos.io` + CORS for `http://localhost:3002` | **PASS** (API evidence) |
| Virtual schema + demo seed | **DONE** |
| Isolated JWKS volume | **DONE** |
| FE points at `:8001` | **PASS** after runtime patch |
| Browser E2E | **PASS** (Playwright `:3002` → `/dashboard`, API `:8001`) |
| Production GO | **NO-GO** |

Login: open `http://localhost:3002/login` → `admin@salesos.io` → password from `DEMO_ADMIN_PASSWORD` / seed defaults (never commit passwords). Details: [auth-fix-2026-07-22.md](./evidence/wave12-staging-virtual/auth-fix-2026-07-22.md).

---

## What still needs a real VPS for GO

1. Staging host (`STAGING_HOST` / SSH user / key)  
2. GitHub Environment `staging` + secret values  
3. Filled host `.env.staging` (not localhost-only placeholders)  
4. GHCR pull auth on VPS  
5. Published `deploy-staging.yml` on Actions-visible branch  
6. Cloud deploy + rollback tabletop evidence under `evidence/wave12-staging/`  
7. Staging soak / gates against that host  

Until then: **Production NO-GO**; virtual tabletop **DONE** as local path only.
