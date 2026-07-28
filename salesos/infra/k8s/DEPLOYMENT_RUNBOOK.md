# SalesOS Production Deployment Runbook

> **Version:** 5.1.0-rc1  
> **Last Updated:** 2026-07-29  
> **Owner:** DevOps Team  
> **SLA:** 99.9% uptime | RTO: 1 hour | RPO: 15 minutes

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Deployment Methods](#3-deployment-methods)
   - [A. CI/CD Pipeline (Recommended)](#a-cicd-pipeline-recommended)
   - [B. Docker Compose](#b-docker-compose)
   - [C. Manual K8s](#c-manual-k8s)
4. [Deployment Procedure](#4-deployment-procedure)
5. [Post-Deployment Verification](#5-post-deployment-verification)
6. [Monitoring Dashboards](#6-monitoring-dashboards)
7. [Rollback Procedure](#7-rollback-procedure)
8. [Backup & Recovery](#8-backup--recovery)
9. [Common Issues & Fixes](#9-common-issues--fixes)
10. [Incident Response](#10-incident-response)
11. [Security Checklist](#11-security-checklist)

---

## 1. Prerequisites

### Tooling

| Tool | Version | Required | Purpose |
|------|---------|----------|---------|
| kubectl | >= 1.28 | K8s deploy | Cluster management |
| kustomize | >= 5.0 | K8s deploy | Manifest templating |
| docker | >= 24.0 | Docker deploy | Container runtime |
| docker compose | >= 2.24 | Docker deploy | Service orchestration |
| helm | >= 3.12 | K8s deploy | Operator installation |
| gh | >= 2.50 | CI/CD | GitHub CLI |

### Access

- [ ] GitHub PAT with `packages:write`, `contents:read` scopes
- [ ] Kubeconfig with `cluster-admin` or `salesos-admin` context
- [ ] GHCR access (ghcr.io/ragheeda-boop/salesos)
- [ ] Slack webhook URL for alerts (#salesos-deployments)
- [ ] PagerDuty or OpsGenie API key (optional)

### Secrets (must be set before deployment)

| Secret | Source | Rotation |
|--------|--------|----------|
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` | 90 days |
| `NEO4J_PASSWORD` | `openssl rand -hex 32` | 90 days |
| `REDIS_PASSWORD` | `openssl rand -hex 32` | 90 days |
| `JWT_SECRET_KEY` | `openssl rand -hex 64` | 180 days |
| `OPENAI_API_KEY` | OpenAI dashboard | As needed |
| `SLACK_WEBHOOK_URL` | Slack Apps | As needed |
| `GRAFANA_ADMIN_PASSWORD` | `openssl rand -hex 32` | 90 days |
| `SMTP_PASSWORD` | Email provider | As needed |

### Environment Verification

```bash
# Check cluster health
kubectl cluster-info
kubectl get nodes -o wide

# Check namespace exists
kubectl get ns salesos

# Verify storage class
kubectl get storageclass

# Check ingress controller
kubectl get pods -n ingress-nginx

# Check cert-manager
kubectl get pods -n cert-manager
```

---

## 2. Architecture Overview

```
                         ┌──────────────┐
                         │   Caddy/LB   │
                         │  :443/:80    │
                         └──────┬───────┘
                                │
                  ┌─────────────┴─────────────┐
                  ▼                            ▼
          ┌──────────────┐           ┌──────────────────┐
          │   Frontend   │           │    Backend API   │
          │  :3000 (3x)  │◄──────────│  :8000 (3-10x)   │
          └──────────────┘           └────────┬─────────┘
                                              │
                    ┌────────────┬─────────────┼─────────────┬──────────────┐
                    ▼            ▼             ▼             ▼              ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
             │PostgreSQL│ │  Neo4j   │ │  Redis   │ │  Kafka   │ │   Prometheus │
             │  :5432   │ │  :7687   │ │  :6379   │ │  :9092   │ │   + Grafana  │
             │  Stateful│ │  Stateful│ │  Deploy  │ │  Stateful│ │   Monitoring │
             └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

### Key Design Decisions

- **No single point of failure**: Backend/Frontend run 3+ replicas with HPA
- **Database statefulsets**: PostgreSQL + Neo4j + Kafka with persistent volumes
- **Rolling updates**: maxUnavailable=0, maxSurge=1
- **Pod Disruption Budgets**: minAvailable=2 for API, 1 for databases
- **Network Policies**: Default-deny, allow-listed service-to-service
- **Backup**: Daily at 0300 UTC, 7-day local retention + S3

---

## 3. Deployment Methods

### A. CI/CD Pipeline (Recommended)

Triggered automatically by pushing a git tag:

```bash
git tag v1.2.3
git push origin v1.2.3
```

Or manually via GitHub Actions:
1. Go to Actions → Deploy to Production
2. Click "Run workflow"
3. Enter version (e.g., `v1.2.3`)
4. Select environment

Pipeline stages:
```
Gate Check → Build & Push → Security Scan → Deploy → Smoke Tests → Notify
                                                                       ↓
                                                              Rollback (on failure)
```

### B. Docker Compose

For single-server production or staging:

```bash
# Set environment
set POSTGRES_PASSWORD=<secure-password>
set NEO4J_PASSWORD=<secure-password>
set GRAFANA_ADMIN_PASSWORD=<secure-password>
set DOMAIN=salesos.com

# Deploy
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d migrations
docker compose -f docker-compose.prod.yml up -d

# Verify
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=50
```

### C. Manual K8s

```bash
# Preview
kubectl kustomize infra/k8s/

# Deploy
kubectl apply -k infra/k8s/

# Monitor rollout
kubectl rollout status deployment/backend -n salesos --timeout=300s
kubectl rollout status deployment/frontend -n salesos --timeout=300s

# Check all pods
kubectl get pods -n salesos -w
```

---

## 4. Deployment Procedure

### Phase 1: Pre-Deployment Checks

```bash
# Run this checklist before every deployment
./scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com

# Check current version
kubectl get deployment backend -n salesos -o jsonpath='{.spec.template.spec.containers[0].image}'

# Verify disk space on all nodes
kubectl top nodes

# Check database connections
kubectl exec deploy/backend -n salesos -- curl -sf http://localhost:8000/health/detailed

# Verify backup ran recently
ls -la /backups/postgres-*.sql.gz
```

### Phase 2: Image Build

```bash
# Build locally (for testing)
docker compose build

# Or let CI/CD handle it via tag push
git tag v1.2.3
git push origin v1.2.3
```

### Phase 3: Database Migrations

Migrations run automatically as an init container. To run manually:

```bash
# Via Docker Compose
docker compose -f docker-compose.prod.yml run --rm migrations

# Via K8s job
kubectl create job --from=cronjob/migrations migrate-manual -n salesos
kubectl logs job/migrate-manual -n salesos -f
```

### Phase 4: Deploy New Version

```bash
# CI/CD handles this automatically
# For manual deploy:
kubectl set image deployment/backend \
  backend=ghcr.io/ragheeda-boop/salesos/backend:v1.2.3 \
  -n salesos

kubectl set image deployment/frontend \
  frontend=ghcr.io/ragheeda-boop/salesos/frontend:v1.2.3 \
  -n salesos
```

### Phase 5: Monitor Rollout

```bash
# Watch rollout status
kubectl rollout status deployment/backend -n salesos --timeout=300s
kubectl rollout status deployment/frontend -n salesos --timeout=300s

# Check new pods
kubectl get pods -n salesos -l app=backend
kubectl get pods -n salesos -l app=frontend

# Verify HPA
kubectl get hpa -n salesos
```

---

## 5. Post-Deployment Verification

### Smoke Tests

```powershell
# Comprehensive smoke tests
.\scripts\smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com

# Quick health check
.\scripts\smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com -MaxRetries 5
```

Expected results:
```
Step 1/8: Wait for Backend Health        ✅ PASS
Step 2/8: Detailed Health                ✅ PASS
Step 3/8: Authentication Tests           ✅ PASS
Step 4/8: Search Tests                   ✅ PASS
Step 5/8: Frontend Tests                 ✅ PASS
Step 6/8: Database Connection Tests      ✅ PASS
Step 7/8: Neo4j Connection Tests         ✅ PASS
Step 8/8: Business Logic Tests           ✅ PASS
```

### Performance Verification

```bash
# Run load test (if NOT during peak hours)
python scripts/load-test.py --endpoint https://api.salesos.com --concurrent 20 --duration 30

# Check p95 latency in Grafana
# Dashboard: "SalesOS Performance" → API Latency panel
```

### Data Integrity

```bash
# Verify database connectivity
kubectl exec deploy/backend -n salesos -- python -c "
import httpx
r = httpx.get('http://localhost:8000/health/detailed')
print(r.json())
"
```

---

## 6. Monitoring Dashboards

| Dashboard | URL | Access |
|-----------|-----|--------|
| Grafana | `https://monitoring.salesos.com` | Admin credentials |
| Prometheus | `https://monitoring.salesos.com/prometheus` | Internal only |
| Alertmanager | `https://monitoring.salesos.com/alertmanager` | Internal only |
| Kafdrop | `http://localhost:9000` | Dev tunnel only |

### Key Grafana Dashboards

1. **SalesOS Overview** — High-level service health, request rate, error rate
2. **SalesOS Performance** — Latency histograms (p50/p95/p99), DB query perf
3. **SalesOS Infrastructure** — CPU/Memory/Disk per node, cluster health
4. **SalesOS Business** — API usage by endpoint, tenant activity
5. **PostgreSQL** — Connections, query time, cache hit ratio
6. **Neo4j** — Query perf, connection pool, heap usage

### Critical Alerts

| Alert | Threshold | Severity | Response Time |
|-------|-----------|----------|---------------|
| BackendDown | Healthcheck fails | CRITICAL | 5 minutes |
| HighErrorRate | 5xx > 5% for 5m | CRITICAL | 5 minutes |
| HighLatencyP99 | > 1s for 5m | CRITICAL | 10 minutes |
| PostgresDown | pg_up == 0 | CRITICAL | 5 minutes |
| Neo4jDown | neo4j_up == 0 | CRITICAL | 5 minutes |
| RedisDown | redis_up == 0 | CRITICAL | 5 minutes |
| DiskSpaceLow | < 10% free | CRITICAL | 15 minutes |
| SLACriticalPathBreach | P99 > 700ms | CRITICAL | 5 minutes |

---

## 7. Rollback Procedure

### Automatic Rollback

The CI/CD pipeline triggers automatic rollback if smoke tests fail:

```bash
# CI/CD does this automatically:
kubectl rollout undo deployment/backend -n salesos
kubectl rollout undo deployment/frontend -n salesos
```

### Manual Rollback

```bash
# Step 1: Rollback to previous revision
kubectl rollout undo deployment/backend -n salesos
kubectl rollout undo deployment/frontend -n salesos

# Step 2: Wait for stability
kubectl rollout status deployment/backend -n salesos --timeout=300s
kubectl rollout status deployment/frontend -n salesos --timeout=300s

# Step 3: Verify
./scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com

# Step 4: Pin to specific version
kubectl set image deployment/backend \
  backend=ghcr.io/ragheeda-boop/salesos/backend:v1.2.2 \
  -n salesos

# Step 5: Document incident
# Create incident report in Notion: /incidents
```

### Rollback Specific Version

```bash
# List revision history
kubectl rollout history deployment/backend -n salesos

# Rollback to specific revision
kubectl rollout undo deployment/backend -n salesos --to-revision=3
```

### Database Rollback

```bash
# If migration caused issues:
# 1. Restore from backup
zcat /backups/postgres-20260714-030002.sql.gz | kubectl exec -i deploy/postgres -n salesos -- psql -U salesos -d salesos

# 2. Mark migration as applied
kubectl exec deploy/backend -n salesos -- alembic stamp <previous-revision>

# 3. Restart backend
kubectl rollout restart deployment/backend -n salesos
```

---

## 8. Backup & Recovery

### Automated Backups

Scheduled daily at **03:00 UTC** via CronJob:

| Component | Method | Retention | Destination |
|-----------|--------|-----------|-------------|
| PostgreSQL | pg_dump (compressed) | 7 days local + 30 days S3 | /backups + s3://salesos-backups/ |
| Neo4j | neo4j-admin dump / APOC export | 7 days local + 30 days S3 | /backups + s3://salesos-backups/ |
| Redis | SAVE + RDB copy | 7 days local | /backups |
| K8s manifests | git (immutable) | Forever | GitHub |

### Manual Backup

```bash
# Run backup immediately
pwsh -File ./scripts/backup.ps1 -Upload -SlackWebhook $env:SLACK_WEBHOOK_URL

# Verify backup
ls -la /backups/
```

### Disaster Recovery

#### Full Recovery (RTO: 1 hour)

```bash
# Step 1: Deploy infrastructure
kubectl apply -k infra/k8s/

# Step 2: Restore PostgreSQL
gunzip -c /backups/postgres-20260714-030002.sql.gz | \
  kubectl exec -i deploy/postgres -n salesos -- psql -U salesos -d salesos

# Step 3: Restore Neo4j
kubectl cp /backups/neo4j-20260714-030002.dump deploy/neo4j:/data/ -n salesos
kubectl exec deploy/neo4j -n salesos -- neo4j-admin load --from=/data/neo4j-20260714-030002.dump

# Step 4: Restore Redis
kubectl cp /backups/redis-20260714-030002.rdb deploy/redis:/data/dump.rdb -n salesos
kubectl rollout restart deployment/redis -n salesos

# Step 5: Verify
./scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
```

#### Point-in-Time Recovery (PostgreSQL)

```bash
# Requires WAL archiving to be enabled
# Restore to specific timestamp
kubectl exec deploy/postgres -n salesos -- pg_ctl stop
# Configure recovery.conf with restore_command and recovery_target_time
kubectl exec deploy/postgres -n salesos -- pg_ctl start
```

---

## 9. Common Issues & Fixes

### Issue: Backend pods crash-looping

```bash
# Check logs
kubectl logs -f deployment/backend -n salesos --tail=100

# Common causes:
# 1. Database connection — check POSTGRES_PASSWORD in secrets
# 2. Migration not run — check migrations pod
# 3. OOM — increase memory limits

# Fix:
kubectl rollout restart deployment/backend -n salesos
```

### Issue: Frontend shows blank page

```bash
# Check frontend logs
kubectl logs -f deployment/frontend -n salesos --tail=50

# Common causes:
# 1. NEXT_PUBLIC_API_URL incorrectly set
# 2. Backend not reachable
# 3. Build failure — check .next/standalone

# Fix:
kubectl rollout restart deployment/frontend -n salesos
```

### Issue: Database connection pool exhausted

```bash
# Check pool status
kubectl exec deploy/backend -n salesos -- curl -sf http://localhost:8000/health/detailed

# Check PgBouncer stats
kubectl exec deploy/pgbouncer -n salesos -- psql -h postgres -U salesos -d pgbouncer -c "SHOW STATS;"

# Fix:
# 1. Increase pool size in configmap
# 2. Restart PgBouncer
kubectl rollout restart deployment/pgbouncer -n salesos
```

### Issue: Kafka consumer lag

```bash
# Check lag
kubectl exec deploy/kafka -n salesos -- kafka-consumer-groups --bootstrap-server localhost:9092 --group salesos-group --describe

# Fix:
# 1. Restart backend consumers
kubectl rollout restart deployment/backend -n salesos
# 2. Increase partitions if needed
kubectl exec deploy/kafka -n salesos -- kafka-topics --bootstrap-server localhost:9092 --alter --topic salesos-events --partitions 6
```

### Issue: Cert-manager certificate expiry

```bash
# Check certificates
kubectl get certificates -n salesos

# Renew
kubectl delete certificate salesos-api-tls -n salesos
kubectl delete certificate salesos-app-tls -n salesos
# Ingress controller will re-request certificates
```

### Issue: Prometheus disk full

```bash
# Check retention
kubectl exec deploy/prometheus -n salesos -- ls -la /prometheus/

# Fix: Reduce retention period
kubectl edit configmap prometheus-config -n salesos
# Change --storage.tsdb.retention.time=15d to 7d
kubectl rollout restart deployment/prometheus -n salesos
```

### Issue: Backup CronJob not running

```bash
# Check CronJob
kubectl get cronjobs -n salesos

# Check recent jobs
kubectl get jobs -n salesos -l app.kubernetes.io/name=salesos-backup

# Check logs:
kubectl logs job/salesos-backup-<id> -n salesos

# Fix: Restart CronJob
kubectl delete job -n salesos -l app.kubernetes.io/name=salesos-backup
```

---

## 10. Incident Response

### Severity Levels

| Level | Definition | Response Time | Escalation |
|-------|------------|---------------|------------|
| SEV1 | Complete outage or data loss | 15 min | DevOps → CTO |
| SEV2 | Partial degradation, core feature broken | 30 min | DevOps |
| SEV3 | Non-critical feature broken | 4 hours | DevOps |
| SEV4 | Cosmetic or low-priority | Next sprint | Team |

### Incident Flow

```
1. Alert fires (Slack/PagerDuty)
2. DevOps acknowledges (15 min SLA)
3. Assess severity (1-4)
4. Open incident in Notion: /incidents
5. Apply fix or rollback
6. Verify resolution
7. Post-mortem within 48 hours
8. Update runbook
```

### Communication

- **Slack Channel**: #salesos-incidents
- **Status Page**: status.salesos.com
- **Escalation**: DevOps → CTO (for SEV1)

### Post-Incident Checklist

- [ ] Root cause identified
- [ ] Incident documented in Notion
- [ ] Monitoring improved to detect similar issue
- [ ] Runbook updated with new findings
- [ ] If SEV1: post-mortem scheduled

---

## 11. Security Checklist

### Pre-Deployment

- [ ] All secrets in Sealed Secrets / External Secrets (never plaintext)
- [ ] `.env.production` in .gitignore
- [ ] No hardcoded credentials in code
- [ ] Docker images scanned (Trivy in CI)
- [ ] Dependency audit clean (`npm audit`, `safety check`)

### Post-Deployment

- [ ] TLS 1.3 enforced on all ingress endpoints
- [ ] RBAC: service accounts have minimal permissions
- [ ] Network policies applied (default-deny)
- [ ] Audit logging enabled
- [ ] Rate limiting active (100/min authed, 20/min anonymous)
- [ ] CORS configured for production domain only

### Regular

- [ ] Secrets rotated every 90 days (database) / 180 days (JWT)
- [ ] SSL certificate renewal automated (cert-manager)
- [ ] Security scan runs weekly (Trivy + Bandit + Semgrep)
- [ ] Penetration test every 6 months
- [ ] Dependency updates reviewed monthly

---

## Quick Reference

```bash
# 📊 Health check
kubectl get all -n salesos
kubectl top pods -n salesos
kubectl logs -f deployment/backend -n salesos --tail=50

# 🔄 Restart service
kubectl rollout restart deployment/backend -n salesos

# ⏪ Rollback
kubectl rollout undo deployment/backend -n salesos

# 📦 Scale
kubectl scale deployment/backend --replicas=5 -n salesos

# 📋 View config
kubectl get configmap salesos-config -n salesos -o yaml

# 🔐 View secrets (names only)
kubectl get secret salesos-secrets -n salesos -o name

# 💾 Manual backup
pwsh -File scripts/backup.ps1 -Upload

# 🧪 Smoke tests
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com

# 🐳 Docker logs
docker compose -f docker-compose.prod.yml logs -f backend
```

---

*This runbook is maintained by the DevOps team. Update after any infrastructure change.*
