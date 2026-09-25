# STAGING READINESS — 2026-08-24

**Status: BLOCKED — EXTERNAL ACCESS**

---

## Current State

| Property | Value |
|----------|-------|
| Staging environment | NOT CREATED |
| Staging database | NOT PROVISIONED |
| Staging OAuth client | NOT CONFIGURED |
| Staging frontend URL | NOT DEPLOYED |
| Staging backend URL | NOT DEPLOYED |

## What Exists

| Component | Production | Staging | Isolated? |
|-----------|:----------:|:-------:|:---------:|
| Railway service | YES | NO | N/A |
| PostgreSQL | YES | NO | N/A |
| Redis | YES | NO | N/A |
| Google OAuth client | Shared | Shared | **NO** |
| Frontend (Vercel) | YES | NO | N/A |
| Environment variables | YES | NO | N/A |

## Blocking Dependencies

| Dependency | Owner | Status | Action Required |
|------------|-------|--------|-----------------|
| Railway project | Platform | Production only | Create staging environment |
| PostgreSQL | Platform | Production only | Provision staging database |
| Redis | Platform | Production only | Provision staging Redis |
| Google Cloud Console | DevOps | NOT AVAILABLE | Create staging OAuth client |
| Vercel project | DevOps | Production only | Create staging frontend project |
| DNS / URLs | DevOps | NOT CONFIGURED | Configure staging subdomain |

## Required Configuration (When Available)

| Property | Production | Staging (Target) |
|----------|------------|------------------|
| Backend URL | `salesos.up.railway.app` | `salesos-staging.up.railway.app` |
| Frontend URL | `salesos.vercel.app` | `salesos-staging.vercel.app` |
| Database | `salesos-prod-db` | `salesos-staging-db` |
| Redis | `salesos-prod-redis` | `salesos-staging-redis` |
| OAuth client | `salesos-prod` (Google) | `salesos-staging` (Google) |
| JWT secret | Production secret | Separate staging secret |
| `ENV` | `production` | `staging` |
| `SALESOS_TESTING` | (empty) | (empty) |
| `OPENAI_API_KEY` | Provider key | Same or separate key |

## Migration Compatibility

| Check | Status |
|-------|:------:|
| Same migration head as production | ✅ (when deployed) |
| Same schema version | ✅ (when deployed) |
| `alembic upgrade head` runs clean | ✅ (verified in CI) |

## Acceptance Criteria

| Criterion | Status |
|-----------|:------:|
| Staging environment exists | ❌ NOT MET |
| Staging is isolated from production | ❌ NOT MET |
| Deployment succeeds | ❌ NOT MET |
| Health checks pass | ❌ NOT MET |
| Authentication works | ❌ NOT MET |
| No production secrets exposed | ❌ NOT MET |

## Recommendation

Staging environment creation requires:
1. Railway Owner/Admin to create staging service
2. DevOps to provision separate database + Redis
3. DevOps to create staging Google OAuth client
4. DevOps to configure staging frontend on Vercel

**This condition CANNOT be closed without external access.**
