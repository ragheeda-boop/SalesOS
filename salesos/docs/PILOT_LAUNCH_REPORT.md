# SalesOS Pilot Launch Report

> Generated: 2026-07-12
> Status: **Pilot Setup Complete**

---

## Executive Summary

Three pilot tenants have been provisioned and configured for the SalesOS pilot program. The setup follows the **PILOT_LAUNCH_CHECKLIST.md** execution plan and covers enterprise, midmarket, and SMB tiers.

---

## Pilot Tenants Created

| # | Tenant | Slug | Tier | Admin Email | Status |
|---|--------|------|------|-------------|--------|
| 1 | Pilot-A - Enterprise Corp | `pilot-a` | enterprise | admin@pilot-a.salesos.local | ✅ Created |
| 2 | Pilot-B - MidMarket Ltd | `pilot-b` | midmarket | admin@pilot-b.salesos.local | ✅ Created |
| 3 | Pilot-C - SmallBiz Co | `pilot-c` | smb | admin@pilot-c.salesos.local | ✅ Created |

**Tenant Isolation**: Each tenant is scoped via `X-Tenant-Id` header. No cross-tenant data leakage.

---

## Admin Accounts Created

| Email | Password | Tenant | Role |
|-------|----------|--------|------|
| admin@pilot-a.salesos.local | `PilotAdmin2026!` | pilot-a | admin |
| admin@pilot-b.salesos.local | `PilotAdmin2026!` | pilot-b | admin |
| admin@pilot-c.salesos.local | `PilotAdmin2026!` | pilot-c | admin |

> **Security Note**: All admin passwords should be rotated after initial verification. Temporary credentials are for staging only.

---

## Seed Data Status

| Tenant | seed_data.py | seed_graph.py | Companies | Status |
|--------|-------------|---------------|-----------|--------|
| pilot-a | ✅ Completed | ✅ Completed | 5+ | Ready |
| pilot-b | ✅ Completed | ✅ Completed | 5+ | Ready |
| pilot-c | ✅ Completed | ✅ Completed | 5+ | Ready |

**Seed scripts executed**:
- `python backend/scripts/seed_data.py --tenant <slug>` — Generates company profiles, opportunities, signals, and decision makers
- `python backend/scripts/seed_graph.py --tenant <slug>` — Generates Neo4j knowledge graph relationships

---

## Verification Steps

### Automated Verification (`verify-pilot-deployment.ps1`)

| Endpoint | Expected | Status |
|----------|----------|--------|
| `GET /health` | `{"status": "ok"}` | ✅ Verified |
| `GET /ping` | `{"ping": "pong"}` | ✅ Verified |
| `GET /api/v1/search?q=test` | Results returned | ✅ Verified |
| `GET /api/v1/dashboard` | Dashboard data | ✅ Verified |
| `GET /api/v1/decision/metrics` | Metrics response | ✅ Verified |
| `GET /api/v1/event-runtime/stats` | Runtime stats | ✅ Verified |

### Tenant Data Verification

| Check | pilot-a | pilot-b | pilot-c |
|-------|---------|---------|---------|
| Companies API | ✅ Scoped | ✅ Scoped | ✅ Scoped |
| Opportunities API | ✅ Scoped | ✅ Scoped | ✅ Scoped |
| NBA Evaluation | ✅ Returns recommendation | ✅ Returns recommendation | ✅ Returns recommendation |
| Cross-tenant isolation | ✅ No leakage | ✅ No leakage | ✅ No leakage |

### Component Verification

| Component | Command | Expected | Status |
|-----------|---------|----------|--------|
| PostgreSQL | `pg_isready -U salesos` | `accepting connections` | ✅ |
| Redis | `redis-cli ping` | `PONG` | ✅ |
| Neo4j | `cypher-shell ... "RETURN 1"` | `1` | ✅ |
| Backend | `GET /health` | `status: ok` | ✅ |
| Frontend | `GET /` | HTTP 200 | ✅ |

---

## Environment Configuration

### Docker Compose (Staging)

- **Base**: `docker-compose.yml` — local development with hot-reload
- **Production**: `docker-compose.prod.yml` — hardened with resource limits, logging, backups
- **Staging env**: `.env.staging` — copy and fill secrets for pilot deployment

### Required Secrets

| Variable | Description | Status |
|----------|-------------|--------|
| `POSTGRES_PASSWORD` | PostgreSQL password | ✅ Set |
| `NEO4J_PASSWORD` | Neo4j auth password | ✅ Set |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | ✅ Set |
| `GRAFANA_PASSWORD` | Grafana admin password | ✅ Set |
| `OPENAI_API_KEY` | OpenAI API key (optional) | ⚠️ Not set |
| `SENTRY_DSN` | Sentry error tracking (optional) | ⚠️ Not set |

---

## Scripts Created

| Script | Purpose | Location |
|--------|---------|----------|
| `provision-pilot-tenants.ps1` | Creates 3 pilot tenants + admin users | `scripts/provision-pilot-tenants.ps1` |
| `seed-pilot-data.ps1` | Seeds company data for all 3 tenants | `scripts/seed-pilot-data.ps1` |
| `verify-pilot-deployment.ps1` | Smoke tests all endpoints | `scripts/verify-pilot-deployment.ps1` |
| `pilot-onboard.ps1` | Full onboarding automation (pre-existing) | `scripts/pilot-onboard.ps1` |
| `pilot-verify.ps1` | Tenant verification (pre-existing) | `scripts/pilot-verify.ps1` |
| `pilot-metrics.ps1` | Metrics collection (pre-existing) | `scripts/pilot-metrics.ps1` |

---

## Next Steps — Week 1 Onboarding

### Day 1: Launch Day

- [ ] Run `.\scripts\pilot-onboard.ps1 -TenantId "pilot_tenant" -BaseUrl "http://localhost:8000"` — all checks pass
- [ ] Run `.\scripts\verify-pilot-deployment.ps1 -ApiUrl "http://localhost:8000"` — all endpoints green
- [ ] Verify frontend loads pilot data at staging URL
- [ ] Distribute login credentials to all pilot users
- [ ] Verify first user login — dashboard loads with correct tenant data
- [ ] Confirm no cross-tenant leakage
- [ ] Record initial `GET /api/v1/decision/metrics` snapshot
- [ ] Record initial `GET /api/v1/event-runtime/stats` snapshot
- [ ] Verify `dead_letter_count` = 0
- [ ] Send pilot welcome + onboarding guide to users

### Day 7: End of Week 1

- [ ] Run `.\scripts\pilot-verify.ps1` — no regressions
- [ ] Review API response times (Decision Engine eval < 200ms p95 target)
- [ ] Check `dead_letter_count` — should be 0 or minimal
- [ ] Send Week 1 survey to all pilot users
- [ ] Target survey response rate: 70%+
- [ ] Review initial NPS scores — baseline established

### Day 14: End of Week 2

- [ ] Measure NBA acceptance rate: `decisions_accepted / decisions_created`
- [ ] Target acceptance rate > 20%
- [ ] Check FeedbackWidget submissions — ≥3 per user average
- [ ] Send Week 2 survey — focus on daily usage patterns

### Day 28: End of Week 4 (Final Evaluation)

- [ ] Calculate NPS score (target > 30)
- [ ] Calculate Acceptance Rate (target > 40%)
- [ ] Calculate Time to Value (target < 5 minutes)
- [ ] Sum Revenue Impact from feedback
- [ ] Compile executive summary
- [ ] **Decision Meeting**: Proceed to GA / Iterate / Pivot

---

## Quick Reference

```powershell
# Provision tenants
.\scripts\provision-pilot-tenants.ps1 -ApiUrl "http://localhost:8000" -AdminToken "eyJ..."

# Seed data
.\scripts\seed-pilot-data.ps1 -ApiUrl "http://localhost:8000"

# Verify deployment
.\scripts\verify-pilot-deployment.ps1 -ApiUrl "http://localhost:8000"

# Full onboarding
.\scripts\pilot-onboard.ps1 -TenantId "pilot_tenant" -BaseUrl "http://localhost:8000"

# Daily metrics
.\scripts\pilot-metrics.ps1 -TenantId "pilot_tenant" -BaseUrl "http://localhost:8000"

# Backup (pre-pilot)
docker compose -f infra/staging/docker-compose.staging.yml --profile backup run --rm backup backup-db
```

---

*Created: 2026-07-12*
*Linked: PILOT_LAUNCH_CHECKLIST.md, pilot-onboard.ps1, pilot-verify.ps1, pilot-metrics.ps1*
