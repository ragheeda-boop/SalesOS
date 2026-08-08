# Production Verification — SalesOS (Railway `production`)

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-06 · **Mode:** VERIFY FIRST (read-only)
**Method:** live HTTP probes, GraphQL, `railway logs`, redacted variable comparison, plus prior machine-verified rows 1–3 (offsite + WAL + PITR) in `evidence/ops01-*`.
**Validation label:** **machine verified** (live) — no changes made.

---

## 1. Reachability & health (live, 2026-08-06)

- `GET https://salesos-production-96c0.up.railway.app/health` → **200**
- Payload: `{"status":"ok","version":"5.1.0-rc1","database":"connected","cache":"connected","graph":"unavailable","kafka":"in_memory","redis":"connected","rate_limiter":"active","uptime_seconds":83961.2}`
- `GET /ready` → **404** (no such route)
- `GET /openapi.json` → 200 (881,643 B)

## 2. Deployment provenance

| Field | Value |
|-------|-------|
| Last deploy | `bdce3450-53d4-4bc4-90d8-4c940e0e1002`, 2026-08-05T21:29:24Z, status SUCCESS |
| Image digest | `sha256:11b14ac58b85…` |
| Deploy origin | CI `deploy.yml` (`railway up --ci`, push to `master`) — canonical path |
| Source commit | `4750038c96fe5d95656aade7257ed134d5df5194` — "Sprint 0.5: Baseline Freeze — v5.1.0-bootstrap-green" (2026-08-06 00:26 +0300) |
| vs local HEAD | local `2538a7d` is 3 commits ahead (unreleased) |

## 3. Database (machine verified — this run + rows 1–3 evidence)

| Check | Production value |
|-------|------------------|
| `alembic_version` | `d1a8c35e7f09` (matches alembic head check in logs) |
| `companies` count | 141,221 |
| `tenants` count | 57 |
| `audit_logs` count | 683 (max created_at 2026-08-06T17:54:01Z) |
| WAL archive | ON — pgBackRest base `20260806-192926F`, archived_count=6/failed=0 → `salesos-pitr-w-857q3fjjrr` (row 2) |
| Offsite | pg_dump → `salesos-backups-iwrweogrr`, SHA256-verified disposable restore (row 1) |
| PITR | pgBackRest 2.59.0 restore to 2026-08-06T19:29:50Z, promote timeline 2, exact match vs live (row 3) |
| `DATABASE_URL` | hash `971975109E` == prod Postgres var (wired correctly) |

## 4. Runtime config (redacted hashes only)

- `ENV=production`, `DEBUG=false`.
- Google SSO configured: `SSO_GOOGLE_CLIENT_ID`, `SSO_GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI=https://salesos-production-96c0.up.railway.app/api/v1/integrations/google/callback`.
- `FRONTEND_URL` set; `FEATURE_HTTPONLY_ACCESS_COOKIE=false`; `FEATURE_AI_COPILOT=false`.
- `JWT_SECRET_KEY` `sha256=06823858C2`; `SECRET_KEY` `sha256=73534985DF` — **identical to staging** (cross-env secret reuse — see DIFF).
- `NEXT_PUBLIC_API_URL=https://sales-os-jet.vercel.app/` (frontend build-time).

## 5. CI/CD

- Active: `deploy.yml` — push `master` → `railway up --ci` (backend) + Vercel Git (frontend). Deploy-time health gate included.
- `deploy-production.yml` (K8s) **QUARANTINED** (DEC-149) — not the live path.
- Repo secrets present for prod Railway (token/project/service/env/health URL). Rollback: Railway UI/CLI redeploy of prior deployment.

## 6. Stability (logs)

- 455-line window (deploy 2026-08-05T21:29 → now, uptime ≈ 23.3h). No restart.
- Warnings only: "Alembic head check failed (No module named 'scripts') — running migrations" (migration ran OK), scraper auth config MISSING → mock mode (`BALADY_API_KEY`/`REGA_API_KEY`/`TAQEEM_API_KEY`/`NAJIZ_API_KEY` absent), FastAPI duplicate Operation IDs.
- **No ERROR / Traceback / CRITICAL in window.**

## 7. Known gaps (must not be hidden)

1. **Neo4j graph is OFFLINE** — `neo4j-prod` service has no active deployment, `/health` reports `"graph":"unavailable"`. Graph-dependent features are down in production while working in staging.
2. Scrapers run in **mock mode** (no provider API keys configured).
3. GA audit classification remains **production no-go** (Security 48 / Production Readiness 38, per ga-engineering-audit) — environment health does not change the overall GO/NO-GO.

## 8. Verdict

| Criterion | Result |
|-----------|--------|
| Serving `/health`, DB/cache/redis connected | PASS |
| Canonical CI deploy path | PASS |
| WAL + offsite + PITR verified (rows 1–3) | PASS |
| Log stability (no errors in window) | PASS |
| Graph/Neo4j availability | **FAIL — neo4j-prod OFFLINE** |
| GA readiness (audit) | **NO-GO (unchanged)** |
