# SalesOS On-Call Runbook

> **Audience**: On-call engineer (primary & secondary responder)
> **Version**: 1.0 — 2026-07-14
> **Purpose**: Quick reference — 1 page. For detailed steps, see the playbooks.

---

## Quick Links

| Resource | Location |
|----------|----------|
| **Incident Response Plan v2** | `docs/INCIDENT_RESPONSE_PLAN.md` |
| **Production Runbook** | `docs/production_runbook.md` |
| **Deployment Runbook** | `infra/k8s/DEPLOYMENT_RUNBOOK.md` |
| **Alert Rules** | `infra/monitoring/alerts.yml` |
| **Grafana** | `https://monitoring.salesos.com` |
| **Prometheus** | `https://monitoring.salesos.com/prometheus` |
| **Alertmanager** | `https://monitoring.salesos.com/alertmanager` |
| **Status Page** | `https://status.salesos.example.com` |

### Slack Channels

| Channel | Purpose |
|---------|---------|
| `#salesos-critical` | S1-S2 alert notifications |
| `#salesos-alerts` | S3+ alert notifications |
| `#incident-{YYYY-MM-DD}-{desc}` | Active incident coordination |
| `#salesos-deployments` | Deployment notifications |

---

## Severity Quick Reference

| Sev | Response | When | Alert Examples |
|-----|----------|------|----------------|
| **S1** | 15 min | Platform down, data loss, security breach | BackendDown, PostgresDown, HighErrorRate, DBPoolSaturated |
| **S2** | 30 min | Major feature down, degraded | HighLatency, SLAAuthBreach |
| **S3** | 2 hours | Minor issue, workaround exists | HighLatencyP95, SlowDatabaseQueries, QueueDepthHigh |
| **S4** | 8 hours | Cosmetic | WebSocketConnectionsHigh, RedisHighMemory |
| **S5** | Next day | Info | — |

### First 5 Minutes — Always

```
1. ACK the alert in Slack (react with :ack:)
2. CHECK health: curl -sf https://api.salesos.com/health | jq .
3. CHECK status: docker compose -f docker-compose.prod.yml ps
4. OPEN incident channel: #incident-{YYYY-MM-DD}-{short-desc}
5. POST initial notification (see IRP §5.1)
```

---

## Common Commands

### Status & Health

```bash
# Full health check
curl -sf https://api.salesos.com/health | jq .

# Service status
docker compose -f docker-compose.prod.yml ps

# Resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Quick version check
curl -s https://api.salesos.com/health | jq -r .version
```

### Logs

```bash
# Backend logs (last 100 lines, follow)
docker compose -f docker-compose.prod.yml logs -f --tail 100 backend

# Errors only
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -i "error\|exception\|traceback\|fatal"

# HTTP error codes
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep "HTTP/1.1\" 5[0-9][0-9]"

# Specific service logs
docker compose -f docker-compose.prod.yml logs --tail 50 postgres neo4j redis caddy
```

### Restart

```bash
# Single service
docker compose -f docker-compose.prod.yml restart backend

# All services (in dependency order — see production_runbook §8.3)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d postgres neo4j redis
sleep 30
docker compose -f docker-compose.prod.yml up -d pgbouncer migrations
sleep 15
docker compose -f docker-compose.prod.yml up -d backend
sleep 15
docker compose -f docker-compose.prod.yml up -d frontend caddy
```

### Database

```bash
# PostgreSQL connection
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos

# PostgreSQL status
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U salesos

# PgBouncer pool status
docker compose -f docker-compose.prod.yml exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"

# Long-running queries
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pid, state, query, now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC LIMIT 10;"

# Kill hanging queries
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# Neo4j status
docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1 AS ok"

# Redis status
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Rollback (if caused by deploy)

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml down
export IMAGE_TAG=v1.0.0  # Previous stable version
docker compose -f docker-compose.prod.yml up -d

# K8s
kubectl rollout undo deployment/backend -n salesos
kubectl rollout undo deployment/frontend -n salesos
```

### Backup

```bash
# Manual backup
docker compose -f docker-compose.prod.yml run --rm backup /usr/local/bin/backup-db

# List backups
docker compose -f docker-compose.prod.yml exec backup ls -la /backups/postgres/

# Verify backup
pwsh -File scripts/verify-backup.ps1
```

### Smoke Tests

```bash
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
```

---

## Alert → Playbook Mapping

| Alert | Playbook |
|-------|----------|
| BackendDown / BackendUnhealthy | [Playbook 1: App Down](INCIDENT_RESPONSE_PLAN.md#playbook-1-application-down-s1) |
| PostgresDown / Neo4jDown / RedisDown / DBPoolSaturated | [Playbook 2: DB Failure](INCIDENT_RESPONSE_PLAN.md#playbook-2-database-failure-s1) |
| HighErrorRate / BackendDegraded | [Playbook 3: High Error Rate](INCIDENT_RESPONSE_PLAN.md#playbook-3-high-error-rate-s1-s2) |
| Security Incident (manual) | [Playbook 4: Security](INCIDENT_RESPONSE_PLAN.md#playbook-4-security-incident-s1) |
| HighLatency / SLACriticalPathBreach / SlowDB / MemoryUsageHigh | [Playbook 5: Performance](INCIDENT_RESPONSE_PLAN.md#playbook-5-performance-degradation-s2) |
| Data Loss (manual) | [Playbook 6: Data Loss](INCIDENT_RESPONSE_PLAN.md#playbook-6-data-loss-s1) |
| SLAAuthBreach / Auth errors | [Playbook 7: Auth Issues](INCIDENT_RESPONSE_PLAN.md#playbook-7-authaccess-issues-s2) |
| QueueDepthHigh / Kafka errors | [Playbook 8: Kafka Failure](INCIDENT_RESPONSE_PLAN.md#playbook-8-kafkaqueue-failure-s2-s3) |
| Backup failure / restore needed | [Playbook 9: Backup Recovery](INCIDENT_RESPONSE_PLAN.md#playbook-9-backup-recovery-s1) |

---

## Daily Health Check (beginning of shift)

```powershell
# Run these commands at shift start:

Write-Host "=== Service Status ==="
docker compose -f docker-compose.prod.yml ps

Write-Host "=== Backend Health ==="
curl -sf https://api.salesos.com/health | jq .

Write-Host "=== Frontend Status ==="
curl -sf -o /dev/null -w "HTTP %{http_code}\n" https://salesos.com

Write-Host "=== PostgreSQL Connections ==="
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -t -c \
  "SELECT count(*) FROM pg_stat_activity;"

Write-Host "=== PgBouncer Pool ==="
docker compose -f docker-compose.prod.yml exec pgbouncer psql -h localhost -p 6432 pgbouncer -t -c "SHOW POOLS;"

Write-Host "=== Disk Usage ==="
df -h / | Select-Object -Last 1

Write-Host "=== Container Resources ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

Write-Host "=== Recent Errors (1h) ==="
docker compose -f docker-compose.prod.yml logs --since 1h backend 2>&1 | Select-String -Pattern "error|exception|traceback" | Measure-Object | Select-Object Count

Write-Host "=== Backup Status ==="
Get-ChildItem -Path C:\opt\salesos\backups\postgres\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1

Write-Host "=== SSL Certificate ==="
# Check at: https://www.sslshopper.com/ssl-checker.html#hostname=salesos.com
```

### Warning Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk usage | >80% | >90% |
| Error rate (1h) | >10 | >50 |
| PG connections | >60 | >80 |
| Backend memory | >800MB | >950MB |
| Neo4j memory | >3GB | >3.8GB |
| Backup age | >26h | >48h |

---

## Shift Handover Checklist

```
ON-CALL SHIFT HANDOVER — Date: ____________

[ ] Current system status: GREEN / YELLOW / RED

[ ] Active incidents:
    - Incident #___: Status: ___

[ ] Recent changes (last 24h):
    - Deployments: ___
    - Config changes: ___
    - Manual interventions: ___

[ ] Pending alerts to watch:
    - ___

[ ] Backup status:
    - Last successful PostgreSQL backup: ___
    - Last successful Neo4j backup: ___
    - Disk usage: ___%

[ ] Notes for next shift:
    ___

Handover from: ____________ to: ____________
```

---

## Incident Communication Templates

### Open

```
🚨 INCIDENT OPENED — S{LEVEL}
Service: {service}
Impact: {impact}
Started: {UTC}
On-call: {name}
Status: Investigating
Channel: #incident-{ID}
```

### Update

```
📋 INCIDENT UPDATE — S{LEVEL}
Status: {Investigating | Identified | Implementing | Monitoring | Resolved}
Finding: {what we found}
Next: {what we're doing}
ETA: {time or TBD}
```

### Resolved

```
✅ INCIDENT RESOLVED — S{LEVEL}
Duration: {total}
Root Cause: {summary}
Resolution: {what fixed it}
Post-mortem: {link}
```

---

*Last Updated: 2026-07-14 · Maintained by: Engineering Lead*
