# Gate G-14: Release Candidate (RC) Validation

> **Issued by**: Release Manager
> **Date**: 2026-07-17
> **Release Candidate**: v3.0.0-RC
> **Commit**: e08a190a02ceb38891e4c523cd286144836f582a (+12 commits ahead)
> **Status**: 🟡 CONDITIONAL

---

## Verdict

| Area | Status | Details |
|------|--------|---------|
| Overall | 🟡 **CONDITIONAL** | 7/8 checks pass. One non-blocking documentation gap: CHANGELOG.md lacks a v3.0.0-RC entry. Fix before GA. |

**Prerequisite**: Update CHANGELOG.md with `[v3.0.0-RC]` release notes before the GA release.

---

## RC Readiness Checklist

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Version tag exists | ✅ PASS | `v3.0.0-RC` tagged at `e08a190` — semver-compliant with RC suffix |
| 2 | CHANGELOG release notes complete | ❌ FAIL | No `v3.0.0-RC` or `v3.0.0` entry in `salesos/CHANGELOG.md`. Latest entries: `v2.0.0` and `@salesos/design-language@2.0.0-alpha.1`. |
| 3 | All migrations reversible | ✅ PASS | 37 Alembic versions (`0001`–`0037`) all implement `downgrade()`. Verified on 0037 and 0025. |
| 4 | Docker build configured | ✅ PASS | Multi-stage Dockerfiles for backend (`python:3.12-slim`) and frontend (`node:22-alpine`). Both use non-root users and HEALTHCHECK. |
| 5 | Production env template complete | ✅ PASS | `backend/.env.production.template` covers all sections: DB, Neo4j, Redis, Kafka, JWT, OpenAI, SMTP, SSO, scrapers, rate limits, observability. |
| 6 | Rollback plan documented | ✅ PASS | Rollback detailed in `GA_LAUNCH_PLAN.md` §4 (trigger criteria, 6-step process, 3 modes, <10min ETA), `deployment_guide.md` §7.3, `production_runbook.md` §7.3. |
| 7 | Smoke test script exists | ✅ PASS | `scripts/smoke-test.ps1` (404 lines) — tests health, auth, search, frontend, DB, Neo4j, Redis, Kafka. Previous run results at `reports/smoke_test.md` and `reports/smoke_test.json`. |
| 8 | CI/CD pipeline configured | ✅ PASS | `salesos/.github/workflows/ci.yml` (597 lines) — 7 stages: Lint → TypeCheck → Unit Tests (85% coverage gate) → Integration → Security (pip-audit, npm audit, Bandit, secrets scan, Trivy, arch compliance) → Build (Docker push to ghcr.io) → E2E (Playwright). |

---

## Migration Status

| Metric | Value |
|--------|-------|
| Total migrations | 37 (0001–0037) |
| Latest migration | `0037_admin_phase16` |
| Framework | Alembic with asyncpg |
| Reversible | ✅ All 37 migrations have `downgrade()` |
| Downgrade verified | ✅ — 0037 drops tables/columns in reverse order; 0025 drops triggers/functions/indexes |
| Migration execution | ✅ CI runs `alembic upgrade head` in test and integration stages |

### Latest Migration (0037) — Phase 16 Admin

- Creates: `admin_roles`, `admin_permissions`, `admin_role_permissions`, `tenant_configs`
- Alters: `admin_feature_flags` (adds `rollout_percentage`, `is_ci_test`)
- Alters: `audit_logs` (adds `outcome`)
- Downgrade: Fully reverses all operations — drops columns, drops tables, drops index

---

## Deployment Verification

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Backend Dockerfile | `salesos/backend/Dockerfile` | ✅ PASS | Multi-stage (builder+production), python 3.12-slim, non-root user, HEALTHCHECK on `/health` |
| Frontend Dockerfile | `salesos/frontend/Dockerfile` | ✅ PASS | Multi-stage, node 22-alpine, standalone Next.js output, non-root user, HEALTHCHECK |
| Production Compose | `salesos/docker-compose.prod.yml` | ✅ PASS | 11 services: postgres+pgvector, pgbouncer, backend, frontend, neo4j, redis, prometheus, grafana, alertmanager, exporter. Resource limits, healthchecks, logging, backups volume. |
| K8s Deployments | `salesos/infra/k8s/` | ✅ PASS | Deployments for backend, frontend, redis, prometheus, grafana, alertmanager |
| Deploy Script | `salesos/infra/scripts/deploy.sh` | ✅ PASS | Exists for automated deployment |
| Deployment Guide | `salesos/docs/deployment_guide.md` | ✅ PASS | Comprehensive (1623 lines) covering Docker Compose, K8s, blue-green, migrations, monitoring |

---

## Rollback Plan Status

| Aspect | Status | Details |
|--------|--------|---------|
| Trigger criteria | ✅ Documented | Error rate >5%, API p99 >2000ms, DB CPU >90%, critical bug, security incident (GA_LAUNCH_PLAN.md §4) |
| Rollback process | ✅ Documented | 6-step process: DETECT → DECIDE → EXECUTE → DB → VERIFY → NOTIFY, total ETA < 10 min |
| Rollback modes | ✅ Documented | K8s Rollback (code-only, `kubectl rollout undo`), Full Rollback (DB + code), Feature Flag Toggle |
| Docker Compose rollback | ✅ Documented | `docker compose down` → `restore-db.sh` → set previous `IMAGE_TAG` → `up -d` (deployment_guide.md §7.3) |
| K8s rollback | ✅ Documented | `kubectl rollout undo deployment/salesos-backend` and `deployment/salesos-frontend` (deployment_guide.md §7.3) |
| DB rollback | ✅ Documented | `alembic downgrade -1` + pre-deploy backup restore (GA_LAUNCH_PLAN.md, production_runbook.md) |
| Rollback drill | ✅ Completed | GA_LAUNCH_PLAN.md §8.5: "Rollback drill passed" |

---

## Issues Requiring Remediation

| # | Severity | Issue | Owner | Remediation |
|---|----------|-------|-------|-------------|
| 1 | 🟡 Medium | CHANGELOG.md missing `v3.0.0-RC` entry. Tag exists (e08a190) but no release notes written. | Release Manager | Add `[v3.0.0-RC] - 2026-07-16` section with Added/Changed/Fixed. Blocking for GA but not for RC validation. |

---

## Summary

7/8 checks pass. The sole gap is a missing CHANGELOG entry for the RC tag — a documentation completeness issue that does not block the RC but **must be resolved before the GA release**.

**Recommendation**: CONDITIONAL PASS — proceed to G-15 (Executive Go/No-Go) with the CHANGELOG remediation tracked as a pre-GA requirement.
