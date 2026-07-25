# Sprint 1 — Production Infrastructure Deployment Verification

**Sprint:** 1 — Production Infrastructure  
**Date:** 2026-07-25  
**Status:** CODE COMPLETE — Ready for DevOps execution  

---

## Deliverables Created

| # | File | Purpose |
|---|------|---------|
| 1 | `scripts/deploy-production.sh` | Unified deployment script (8 phases: pre-flight → migrations → services → workers → monitoring → health wait → celery test → API verify) |
| 2 | `scripts/generate-secrets.sh` | K8s secrets generation (loads .env + auto-generates strong secrets, produces ConfigMap + Secret YAML) |
| 3 | `scripts/verify-deployment.sh` | Automated verification (7 categories: health, metrics, API, Docker, Celery, DB, migrations → JSON report) |
| 4 | `docker-compose.prod.yml` | Updated with `worker` + `beat` services |
| 5 | `infra/k8s/celery-worker/deployment.yaml` | K8s: 2 Celery worker replicas with liveness probes |
| 6 | `infra/k8s/celery-worker/migration-job.yaml` | K8s: Pre-install migration Job |
| 7 | `celery_schedule.py` | 7 scheduled Beat jobs |
| 8 | `celery_app.py` | Updated `include` + `beat_schedule` registration |
| 9 | `domains/employee/tasks.py` | 6 @shared_task wrappers + worker_health_ping |

---

## Deployment Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Pre-flight Checks                                         │
│    ├── Docker daemon running                                  │
│    ├── Docker Compose v2 installed                            │
│    ├── .env.production exists (with real secrets)             │
│    ├── GOOGLE_CLIENT_ID/SECRET configured                     │
│    └── MICROSOFT_CLIENT_ID/SECRET configured                  │
├──────────────────────────────────────────────────────────────┤
│ 2. Database                                                   │
│    └── alembic upgrade head (migrations 0041-0045)            │
├──────────────────────────────────────────────────────────────┤
│ 3. Core Services                                              │
│    ├── postgres (pgvector:pg16)                               │
│    ├── redis (redis:7-alpine)                                 │
│    ├── backend (GHCR image, 4 uvicorn workers)                │
│    └── frontend (GHCR image, Next.js standalone)              │
├──────────────────────────────────────────────────────────────┤
│ 4. Background Workers                                         │
│    ├── worker (Celery, concurrency=2, max-tasks-per-child=1000│
│    └── beat (Celery Beat, 7 scheduled jobs)                   │
├──────────────────────────────────────────────────────────────┤
│ 5. Monitoring                                                 │
│    ├── prometheus (v3.3.0, 15d retention)                     │
│    ├── grafana (11.6.0, 6 dashboards auto-provisioned)        │
│    ├── postgres-exporter                                      │
│    └── redis-exporter                                         │
├──────────────────────────────────────────────────────────────┤
│ 6. Health Wait (max 120s)                                     │
│    └── curl -f http://localhost:8000/health                   │
├──────────────────────────────────────────────────────────────┤
│ 7. Celery Test                                                │
│    └── celery -A app.celery_app inspect ping                  │
├──────────────────────────────────────────────────────────────┤
│ 8. API Verification                                           │
│    ├── /health → 200                                           │
│    ├── /health/employee-360 → 200                              │
│    ├── /health/employee-360/ready → 200                        │
│    ├── /health/employee-360/live → 200                         │
│    ├── /metrics → 200                                          │
│    └── /api/v1/executive/summary → 200                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Celery Beat Schedule (Active after deployment)

| Schedule | Task Name | Job |
|----------|-----------|-----|
| Every 15 min | `calendar_sync_all` | Sync all employee calendars via Google/Microsoft |
| Every 15 min | `email_sync_all` | Sync all employee emails via Gmail/Outlook |
| Every 60 min | `webhook_renewal_all` | Renew expiring webhook subscriptions |
| Daily 02:00 UTC | `signal_retention_cleanup` | Remove orphaned signals |
| Daily 03:00 UTC | `score_rebuild_all_employees` | Recalculate scores for all active employees |
| Daily 04:00 UTC | `gdpr_purge_expired_users` | Hard-delete users past retention period |
| Every 5 min | `worker_health_ping` | Verify worker → DB connectivity |

---

## Sprint 1 Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | جميع الخدمات تعمل | READY | Deployment script verified service dependency chain |
| 2 | لا توجد أخطاء Startup | READY | Migration runs first, backend depends on migration success |
| 3 | جميع الحاويات Healthy | READY | Health checks on all 14+ services, 120s wait with retry |
| 4 | Celery يعالج Job تجريبي بنجاح | READY | `celery_app.py` registers beat_schedule + tasks.py has @shared_task wrappers |
| 5 | Google OAuth variables configured | REQUIRES ENV | Set GOOGLE_CLIENT_ID/SECRET in .env.production |
| 6 | Microsoft OAuth variables configured | REQUIRES ENV | Set MICROSOFT_CLIENT_ID/SECRET in .env.production |
| 7 | K8s secrets generated (not CHANGE_ME) | REQUIRES ENV | Run `scripts/generate-secrets.sh` then encrypt with `kubeseal` |
| 8 | Deployment verification passes | READY | `scripts/verify-deployment.sh` produces JSON report |

---

## DevOps Execution Checklist (Sprint 1)

```bash
# Step 1: Set environment variables
cp .env.production.template .env.production
# EDIT .env.production — set ALL secrets including:
#   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
#   MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET
#   POSTGRES_PASSWORD, NEO4J_PASSWORD
#   SECRET_KEY (>32 chars), JWT_SECRET_KEY (>32 chars)
#   DOMAIN (your production domain)

# Step 2: Generate K8s secrets
bash scripts/generate-secrets.sh
kubeseal < infra/k8s/secrets-generated.yaml > infra/k8s/sealed-secrets.yaml

# Step 3: Deploy to K8s
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap-generated.yaml
kubectl apply -f infra/k8s/sealed-secrets.yaml
kubectl apply -k infra/k8s/

# Step 4: Run migrations (K8s Job will do this automatically)
kubectl wait --for=condition=complete job/db-migrations -n salesos --timeout=300s

# Step 5: Verify deployment
bash scripts/verify-deployment.sh
# Check output: ALL CHECKS PASSED

# Step 6: Monitor Celery
kubectl logs -n salesos deployment/celery-worker --tail=50
kubectl logs -n salesos deployment/celery-beat --tail=20

# OR for Docker Compose:
bash scripts/deploy-production.sh
# Follow the interactive prompts
```

---

## Risk: External Dependencies

| Dependency | Blocked By | Resolution |
|------------|-----------|------------|
| Google Cloud OAuth | Needs Google Cloud Console project | Register project → enable Calendar API + Gmail API → create OAuth consent screen → set GOOGLE_CLIENT_ID/SECRET |
| Azure AD OAuth | Needs Azure Portal app | Register app → add Microsoft Graph permissions (Calendars.Read, Mail.Read) → set MICROSOFT_CLIENT_ID/SECRET |
| K8s secrets (CHANGE_ME) | Needs actual secret values | Run generate-secrets.sh script |
| DNS + TLS | Needs domain + Let's Encrypt | Set DOMAIN env var → Caddy auto-provisions TLS |

---

## Sprint 1 Status: READY FOR DEVOPS EXECUTION

All code, configs, scripts, and documentation are complete. Sprint 1 can be executed by a DevOps engineer with:
- Access to Google Cloud Console
- Access to Azure Portal
- Access to Kubernetes cluster (or Docker host for Compose)
- Domain name configured for the cluster

**Estimated execution time:** 4-6 hours (including OAuth app registration)
