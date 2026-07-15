# SalesOS — Incident Response Plan v2.0

> Effective: 2026-07-14 · Version: 2.0
> Owner: Engineering Lead · Review: Quarterly
> Supersedes: v1.0 (2026-07-13)

---

## Table of Contents

1. [Severity Matrix](#1-severity-matrix)
2. [Incident Response Team](#2-incident-response-team)
3. [Incident Response Process](#3-incident-response-process)
4. [Playbooks](#4-playbooks)
   - [Playbook 1: Application Down](#playbook-1-application-down-s1)
   - [Playbook 2: Database Failure](#playbook-2-database-failure-s1)
   - [Playbook 3: High Error Rate](#playbook-3-high-error-rate-s1-s2)
   - [Playbook 4: Security Incident](#playbook-4-security-incident-s1)
   - [Playbook 5: Performance Degradation](#playbook-5-performance-degradation-s2)
   - [Playbook 6: Data Loss](#playbook-6-data-loss-s1)
   - [Playbook 7: Auth/Access Issues](#playbook-7-authaccess-issues-s2)
   - [Playbook 8: Kafka/Queue Failure](#playbook-8-kafkaqueue-failure-s2-s3)
   - [Playbook 9: Backup Recovery](#playbook-9-backup-recovery-s1)
5. [Communication Templates](#5-communication-templates)
6. [Post-Mortem Process](#6-post-mortem-process)
7. [Tooling](#7-tooling)
8. [Training & Drills](#8-training--drills)

---

## 1. Severity Matrix

### 1.1 Severity Levels

| Level | Name | Description | Response Time | Update Freq | Resolution Target |
|-------|------|-------------|---------------|-------------|-------------------|
| **S1** | Critical | Platform down for all users; data loss risk; security breach; SLA breach | 15 min | Every 30 min | 4 hours |
| **S2** | High | Major feature unavailable; significant user impact; partial outage; >5% error rate | 30 min | Every 1 hour | 8 hours |
| **S3** | Medium | Minor feature degraded; workaround available; limited impact | 2 hours | Every 4 hours | 24 hours |
| **S4** | Low | Cosmetic issue; non-blocking; minor inconvenience | 8 hours | Daily | 1 week |
| **S5** | Info | Observation, improvement suggestion, no user impact | Next business day | Weekly | Next sprint |

### 1.2 Severity Examples

| Level | Scenario | Alert Rule (from alerts.yml) |
|-------|----------|------------------------------|
| S1 | Backend unreachable for >1 min | `BackendServiceDown` / `BackendUnhealthy` |
| S1 | PostgreSQL unreachable | `PostgresDown` |
| S1 | Neo4j unreachable | `Neo4jDown` |
| S1 | Redis unreachable | `RedisDown` |
| S1 | Data breach confirmed | Manual (security incident) |
| S1 | Data loss detected | Manual (data integrity check) |
| S1 | DB connection pool >90% saturated | `DBPoolSaturated` |
| S1 | Critical path P99 >700ms for 5 min | `SLACriticalPathBreach` |
| S1 | Disk space <10% | `DiskSpaceLow` |
| S1 | Auth P99 >800ms for 5 min | `SLAAuthBreach` |
| S2 | HTTP 5xx rate >5% for 5 min | `HighErrorRate` |
| S2 | P99 latency >1s for 5 min | `HighLatency` |
| S3 | P95 latency >500ms for 5 min | `HighLatencyP95` |
| S3 | 5xx errors detected for 10 min | `BackendDegraded` |
| S3 | PostgreSQL connections >50 | `PostgresHighConnections` |
| S3 | Kafka consumer lag >1000 | `QueueDepthHigh` |
| S3 | Memory usage >90% | `MemoryUsageHigh` |
| S3 | No HTTP traffic for 10 min | `NoTraffic` |
| S3 | P95 DB query >1s for 5 min | `SlowDatabaseQueries` |
| S3 | P95 AI inference >10s | `SlowAIInference` |
| S4 | WebSocket connections >80 | `WebSocketConnectionsHigh` |
| S4 | Redis memory >90% | `RedisHighMemory` |
| S5 | Performance optimization opportunity | Manual (monitoring insight) |

### 1.3 Escalation Path

```
S5 (Info)       → Engineering Lead (within 24h)
S4 (Low)        → Engineering Lead (within 8h)
S3 (Medium)     → Engineering Lead (within 2h) → CTO (if unresolved in 12h)
S2 (High)       → Engineering Lead + CTO (within 30min) → CEO (if unresolved in 4h)
S1 (Critical)   → All hands (within 15min) → CEO immediately → External support if needed
```

### 1.4 On-Call Rotation

| Role | Response Time | Contact Method |
|------|---------------|----------------|
| Primary On-Call | 15 min (S1), 30 min (S2) | Phone + WhatsApp + Slack @oncall |
| Secondary On-Call | 30 min (S1), 1 hour (S2) | Phone + WhatsApp |
| Engineering Lead | 1 hour (S3+), Immediate (S1-S2) | Phone + Slack |
| CTO | 2 hours (S2+), Immediate (S1) | Phone |
| CEO | 4 hours (S2 business-critical), Immediate (S1) | Phone |

### 1.5 External Contacts

| Service | Contact | When to Engage |
|---------|---------|---------------|
| AWS Support | TBD | Infrastructure failures |
| Domain Registrar | TBD | DNS issues |
| SSL Provider (Caddy) | N/A (auto-renew) | Certificate issues |
| Security Firm | TBD | S1 security incidents |

---

## 2. Incident Response Team

### 2.1 Roles & Responsibilities

| Role | Primary | Alternate | Responsibilities |
|------|---------|-----------|-----------------|
| **Incident Commander (IC)** | Rotating on-call | Secondary on-call | Owns the incident; coordinates response; makes go/no-go decisions; communicates status |
| **Technical Lead (TL)** | Engineering Lead | Senior Engineer | Leads technical investigation; determines root cause; implements fix |
| **Communications Lead (CL)** | CTO (S1-S2) / Engineering Lead (S3+) | CEO (S1) | Manages internal/external communications; drafts status updates; handles customer comms |
| **Subject Matter Expert (SME)** | Per-domain owner | Domain architect | Provides deep expertise for specific services (DB, Auth, Search, AI, etc.) |

### 2.2 Domain SMEs

| Domain | SME | Backup |
|--------|-----|--------|
| PostgreSQL / Database | Database Engineer | Backend Engineer |
| Neo4j / Graph | AI Engineer | Backend Engineer |
| Authentication / RBAC | Security Engineer | Backend Engineer |
| Search | Search Engineer | Backend Engineer |
| AI / Scoring | AI Engineer | Data Engineer |
| Frontend | Frontend Engineer | DevOps Engineer |
| Infrastructure / K8s | DevOps Engineer | Backend Engineer |
| Network / TLS / Caddy | DevOps Engineer | Frontend Engineer |

### 2.3 Incident Channel Naming

```
Slack: #incident-{YYYY-MM-DD}-{short-desc}
Example: #incident-2026-07-14-postgres-down
```

### 2.4 War Room

For S1 incidents, a Zoom/Google Meet bridge is created automatically:
- Link posted in `#incident-{ID}` channel
- Incident Commander starts the call within 15 minutes
- All stakeholders join; non-essential listeners stay out

---

## 3. Incident Response Process

### 3.1 Process Flow

```
Detection
   │
   ├── Automated: Prometheus alert fires → Alertmanager → Slack #salesos-critical
   │               (see infra/monitoring/alerts.yml for all alert rules)
   │
   └── Manual: User report via support, internal discovery, status page monitor
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │ Triage (5 min)                                    │
  │ 1. Acknowledge alert in Slack / on-call system    │
  │ 2. Assess severity (S1-S5) using matrix above     │
  │ 3. Assign Incident Commander (on-call engineer)   │
  │ 4. Open incident channel: #incident-{ID}          │
  │ 5. Post initial notification (see §5.1)           │
  └──────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │ Contain (target: 15 min for S1)                   │
  │ 1. Stop the bleeding (rollback, isolate, block)   │
  │ 2. Engage SMEs as needed                          │
  │ 3. Apply workaround if full fix not immediate     │
  │ 4. Update status: "Identified - implementing fix" │
  └──────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │ Eradicate (target: varies by severity)            │
  │ 1. Identify root cause                            │
  │ 2. Deploy permanent fix (via CI/CD or hotfix)     │
  │ 3. Verify fix in staging if possible              │
  │ 4. Document fix steps                             │
  └──────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │ Recover                                           │
  │ 1. Restore service (rollout fix, restart, etc.)   │
  │ 2. Verify health checks pass                      │
  │ 3. Run smoke tests (scripts/smoke-test.ps1)       │
  │ 4. Monitor for 15 min (S1) / 5 min (S3+)          │
  │ 5. Update status: "Monitoring"                    │
  └──────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │ Post-Mortem (within 48 hours for S1-S2)           │
  │ 1. Schedule post-mortem meeting                   │
  │ 2. Complete post-mortem template (§6)             │
  │ 3. Create action items with owners & deadlines    │
  │ 4. Update runbook with lessons learned            │
  │ 5. Close incident channel                         │
  └──────────────────────────────────────────────────┘
```

### 3.2 Response Time Targets

| Phase | S1 | S2 | S3 | S4 |
|-------|----|----|----|-----|
| Acknowledge | 5 min | 10 min | 30 min | 2 hours |
| Triage complete | 15 min | 30 min | 2 hours | 8 hours |
| Containment | 30 min | 1 hour | 4 hours | - |
| Resolution | 4 hours | 8 hours | 24 hours | 1 week |
| Post-mortem | 48 hours | 48 hours | 1 week | - |

### 3.3 Status Codes

Used in all communications:

| Status | Meaning |
|--------|---------|
| Investigating | Team is actively diagnosing; cause unknown |
| Identified | Root cause found; working on fix |
| Implementing | Fix in progress (code, config, or infrastructure change) |
| Monitoring | Fix deployed; watching metrics for stability |
| Resolved | Service restored; incident closed |

---

## 4. Playbooks

---

### Playbook 1: Application Down (S1)

**Trigger Conditions:**
- `BackendServiceDown` or `BackendUnhealthy` alert fires (Prometheus)
- `up{job="salesos-backend"} == 0` for 1+ minutes
- Users report "SalesOS is down"
- Health endpoint returns non-200 or unhealthy status

**Immediate Actions (first 15 min):**

```bash
# 1. ACKNOWLEDGE the alert in Slack
# React with :ack: on the alert message in #salesos-critical

# 2. CHECK backend health
curl -sf https://api.salesos.com/health | jq .
curl -sf https://api.salesos.com/health/ready && echo "READY" || echo "NOT READY"
curl -sf https://api.salesos.com/ping | jq .

# 3. CHECK container status
docker compose -f docker-compose.prod.yml ps
docker stats --no-stream | grep backend

# 4. CHECK recent logs for crash reason
docker compose -f docker-compose.prod.yml logs --tail 200 backend | grep -i "error\|exception\|traceback\|fatal\|panic"
docker compose -f docker-compose.prod.yml logs --since 30m backend 2>&1 | tail -100

# 5. POST initial notification in #incident-{ID}
```

**Investigation Steps:**

```bash
# 1. Check if dependency is the root cause
curl -s https://api.salesos.com/health | jq '.database, .neo4j, .redis'

# 2. Check exit code
docker inspect salesos-backend --format '{{.State.ExitCode}} {{.State.Error}}'
# Exit codes: 0=normal, 137=OOM killed, 139=segfault, 1=app error

# 3. If OOM (exit 137), check memory
docker stats --no-stream | grep backend

# 4. Check recent deployments / config changes
git log --oneline -5
docker compose -f docker-compose.prod.yml logs --tail 50 migrations

# 5. Check if ports are occupied
netstat -ano | findstr :8000

# 6. Check PostgreSQL connectivity from backend
docker compose -f docker-compose.prod.yml exec backend curl -sf http://localhost:8000/health/detailed
```

**Resolution Steps:**

```bash
# Option A: Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Option B: If OOM — increase memory limit in docker-compose.prod.yml and restart
#    backend:
#      deploy:
#        resources:
#          limits:
#            memory: 2G  # Increase from 1GB

# Option C: If config/secret issue — fix .env.production, then restart
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml restart backend

# Option D: Full dependency restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d postgres neo4j redis
sleep 30
docker compose -f docker-compose.prod.yml up -d pgbouncer migrations
sleep 15
docker compose -f docker-compose.prod.yml up -d backend
sleep 15
docker compose -f docker-compose.prod.yml up -d frontend caddy

# Option E: Rollback to previous version (if caused by deploy)
# See production_runbook.md §7.3 for full rollback procedure
docker compose -f docker-compose.prod.yml down
export IMAGE_TAG=v1.0.0  # Previous stable version
docker compose -f docker-compose.prod.yml up -d
```

**Verification Steps:**

```bash
# 1. Health endpoint
curl -sf https://api.salesos.com/health | jq .
# Expected: status: "healthy", database: "connected", neo4j: "connected"

# 2. API responds
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/ping
# Expected: 200

# 3. Application startup in logs
docker compose -f docker-compose.prod.yml logs --tail 20 backend | grep "Application startup"

# 4. No errors in last 5 min
docker compose -f docker-compose.prod.yml logs --since 5m backend 2>&1 | grep -ci "error"
# Expected: 0

# 5. Run smoke tests
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
```

**Communication Checklist:**
- [ ] Ack alert in `#salesos-critical`
- [ ] Post initial notification in `#incident-{ID}` (see §5.1)
- [ ] Post status update every 30 min
- [ ] Notify CTO if unresolved after 30 min
- [ ] Notify CEO if unresolved after 2 hours
- [ ] Post resolution notification (see §5.3)
- [ ] Schedule post-mortem

---

### Playbook 2: Database Failure (S1)

**Trigger Conditions:**
- `PostgresDown` alert fires (`pg_up == 0`)
- `Neo4jDown` alert fires (`neo4j_up == 0`)
- `RedisDown` alert fires (`redis_up == 0`)
- Backend health shows `database: "disconnected"` or `neo4j: "disconnected"`
- `DBPoolSaturated` alert (>90% pool utilization)

**Immediate Actions (first 15 min):**

```bash
# 1. ACKNOWLEDGE alert

# 2. CHECK database status
docker compose -f docker-compose.prod.yml ps postgres
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U salesos

# 3. CHECK logs
docker compose -f docker-compose.prod.yml logs --tail 100 postgres | grep -i "fatal\|panic\|shutdown\|corrupt\|disk"
docker compose -f docker-compose.prod.yml logs --tail 100 neo4j | grep -i "error\|fatal\|out of memory"
docker compose -f docker-compose.prod.yml logs --tail 100 redis | grep -i "error\|fatal"

# 4. STOP backend to prevent cascading failures
docker compose -f docker-compose.prod.yml stop backend frontend

# 5. POST notification
```

**Investigation Steps (PostgreSQL):**

```bash
# Check disk space
df -h /var/lib/docker/volumes/salesos_pgdata/_data

# Check database size
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pg_size_pretty(pg_database_size('salesos'));"

# Check active connections before crash
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT count(*) AS total, state FROM pg_stat_activity GROUP BY state;"

# Check for long-running queries
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pid, state, query, query_start, now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC LIMIT 20;"

# Check PgBouncer pool
docker compose -f docker-compose.prod.yml exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"
```

**Resolution Steps (PostgreSQL):**

```bash
# 1. Restart PostgreSQL
docker compose -f docker-compose.prod.yml restart postgres
sleep 15
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U salesos

# 2. Kill long-running queries if pool saturated
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# 3. If disk full — clean old WAL / temp files
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c "VACUUM FULL VERBOSE;"

# 4. If PgBouncer connection exhaustion — restart
docker compose -f docker-compose.prod.yml restart pgbouncer

# 5. If PostgreSQL won't start — restore from backup (see Playbook 9)
```

**Resolution Steps (Neo4j):**

```bash
# 1. Check for OOM
docker stats --no-stream | grep neo4j
# If at limit (4GB), increase NEO4J.memory.heap.max_size

# 2. Restart Neo4j
docker compose -f docker-compose.prod.yml restart neo4j
sleep 20
docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1 AS ok"

# 3. If corrupt — restore from backup (see Playbook 9)
```

**Verification Steps:**

```bash
# PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U salesos

# PgBouncer
docker compose -f docker-compose.prod.yml exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"

# Neo4j
docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1 AS ok"

# Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# API health
curl -s https://api.salesos.com/health | jq .
# Expected: all "connected"

# Smoke tests
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
```

**Communication Checklist:**
- [ ] Ack alert
- [ ] Stop frontend/backend — notify users
- [ ] Post status updates every 30 min
- [ ] Notify CTO if DB restore needed
- [ ] Post resolution notification

---

### Playbook 3: High Error Rate (S1-S2)

**Trigger Conditions:**
- `HighErrorRate` alert: 5xx rate >5% for 5 minutes
- `BackendDegraded` alert: 5xx errors for 10 minutes
- Users report "errors on every page"
- Monitoring shows error rate spike

**Immediate Actions (first 15 min):**

```bash
# 1. ACKNOWLEDGE

# 2. CHECK current error rate
# Grafana dashboard: SalesOS Performance → API Latency
# OR:
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -i "error\|500\|503\|502\|400"

# 3. IDENTIFY which endpoints are failing
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep "HTTP/1.1\" 5[0-9][0-9]" | awk '{print $NF}' | sort | uniq -c | sort -rn

# 4. CHECK if errors are from a specific endpoint or all
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -oP '"GET|POST|PUT|DELETE" \S+' | sort | uniq -c | sort -rn
```

**Investigation Steps:**

```bash
# 1. Check if it's a database issue
curl -s https://api.salesos.com/health | jq .

# 2. Check if it's a specific API change
git diff HEAD~1 --name-only

# 3. Check if it's a dependency timeout
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -i "timeout\|connection.*refused\|connection.*reset"

# 4. Check if it's a rate limiting issue
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -i "rate.*limit\|429"

# 5. Check if it's a CSRF/CORS issue
docker compose -f docker-compose.prod.yml logs --since 10m backend | grep -i "csrf\|cors\|origin"

# 6. Check memory/cpu pressure
docker stats --no-stream | grep backend
```

**Resolution Steps:**

```bash
# Option A: Restart backend (clears transient issues)
docker compose -f docker-compose.prod.yml restart backend

# Option B: If database-related, check connections (see Playbook 2)
# Option C: If rate limiting, adjust in .env.production
#    RATE_LIMIT_AUTHENTICATED=200  # Increase from 100
#    docker compose -f docker-compose.prod.yml restart backend

# Option D: If CSRF-related, verify DOMAIN and CORS settings
#    Check .env.production for DOMAIN, CORS_ORIGINS

# Option E: Rollback if caused by recent deploy (see production_runbook.md §7.3)
```

**Verification Steps:**

```bash
# 1. Check error rate dropped
docker compose -f docker-compose.prod.yml logs --since 5m backend | grep -c "HTTP/1.1\" 5[0-9][0-9]"
# Expected: 0 or very low

# 2. Health check
curl -sf https://api.salesos.com/health | jq .

# 3. Test a few endpoints
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/api/v1/health
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/api/v1/search?q=test

# 4. Smoke tests
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
```

**Communication Checklist:**
- [ ] Ack alert
- [ ] Determine scope (all users vs single feature)
- [ ] Post status update hourly (S2) or every 30 min (S1)
- [ ] Notify if escalating

---

### Playbook 4: Security Incident (S1)

**Trigger Conditions:**
- Unauthorized access detected (auth logs show suspicious patterns)
- Data breach suspected (unusual data export, large API calls from single IP)
- Credential leak (secret pushed to public repo, compromised API key)
- DDoS / abuse (traffic spike from single IP, rate limit bypass)
- Security scan finding (Trivy, Semgrep, Bandit — critical severity)

**Immediate Actions (first 15 min):**

```bash
# 1. ISOLATE — Do NOT restart or change passwords yet (preserve evidence)
# 2. ACKNOWLEDGE — escalate to CTO immediately
# 3. PRESERVE logs
docker compose -f docker-compose.prod.yml logs --since 24h backend > /tmp/incident-logs-$(date +%Y%m%d-%H%M%S).txt
docker compose -f docker-compose.prod.yml logs --since 24h caddy > /tmp/incident-caddy-logs.txt

# 4. CHECK auth logs for suspicious patterns
docker compose -f docker-compose.prod.yml logs --since 6h backend | grep -i "login\|token\|auth\|401\|403" | sort | uniq -c | sort -rn | head -20

# 5. CHECK access logs for unusual IPs
docker compose -f docker-compose.prod.yml logs --since 6h caddy | grep -oP '\d+\.\d+\.\d+\.\d+' | sort | uniq -c | sort -rn | head -20

# 6. OPEN war room with CTO + Security Engineer
```

**Investigation Steps:**

```bash
# 1. Check recent deployments and code changes
git log --oneline -20

# 2. Check if any secrets were exposed
# Check git history for secrets
git log -p --all -S "POSTGRES_PASSWORD\|JWT_SECRET_KEY\|NEO4J_PASSWORD"

# 3. Check for compromised tokens
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT id, user_id, created_at, expires_at FROM identity.tokens
   WHERE expires_at > now() ORDER BY created_at DESC LIMIT 50;"

# 4. Check for unusual data access patterns
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT user_id, count(*) AS requests, MIN(created_at) AS first, MAX(created_at) AS last
   FROM audit.access_log
   WHERE created_at > now() - interval '1 hour'
   GROUP BY user_id
   ORDER BY requests DESC;"

# 5. Rotate all secrets if compromise is confirmed
# See scripts/rotate-secrets.ps1
```

**Resolution Steps:**

```bash
# 1. Block compromised access
# - Rotate all credentials (POSTGRES_PASSWORD, JWT_SECRET_KEY, NEO4J_PASSWORD, etc.)
# - Revoke all active tokens
# - Block suspicious IPs in Caddy/Caddyfile or firewall

# 2. Apply security fix
# - Patch vulnerability
# - Deploy via hotfix

# 3. Verify fix
# - Run security scan
pwsh -File scripts/security-audit.ps1

# 4. Notify affected users if data was exposed
```

**Verification Steps:**

```bash
# 1. Security scan passes
pwsh -File scripts/security-audit.ps1

# 2. All endpoints return 200
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/health

# 3. Auth works end-to-end
# Manual login test

# 4. No residual suspicious activity
docker compose -f docker-compose.prod.yml logs --since 30m backend | grep -ci "401\|403"
```

**Communication Checklist:**
- [ ] Immediately notify CTO + CEO
- [ ] DO NOT disclose details publicly until confirmed and contained
- [ ] Engage external security firm if data breach confirmed
- [ ] Prepare customer notification if required
- [ ] Legal notification if regulated data (KSA PDPL)
- [ ] Document all actions for forensic investigation
- [ ] Post-mortem required within 24 hours

---

### Playbook 5: Performance Degradation (S2)

**Trigger Conditions:**
- `HighLatency` alert: P99 >1s for 5 minutes
- `HighLatencyP95` alert: P95 >500ms for 5 minutes
- `SLACriticalPathBreach` alert: Critical path P99 >700ms
- `SlowDatabaseQueries` alert: P95 DB query >1s
- `SlowAIInference` alert: P95 AI inference >10s
- `MemoryUsageHigh` alert: Memory >90%
- Users report "SalesOS is slow"

**Immediate Actions (first 15 min):**

```bash
# 1. ACKNOWLEDGE alert

# 2. CHECK current latency
# Grafana: SalesOS Performance → API Latency dashboard

# 3. CHECK which endpoints are slow
docker compose -f docker-compose.prod.yml logs --since 10m backend | \
  grep -oP 'HTTP/1.1" \d+ \d+' | awk '{print $NF}' | sort -rn | head -20

# 4. CHECK database query performance
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT query, calls, total_exec_time, mean_exec_time, rows
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;"
```

**Investigation Steps:**

```bash
# 1. Check for long-running queries
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pid, state, query, query_start, now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC
   LIMIT 10;"

# 2. Check connection pool saturation
docker compose -f docker-compose.prod.yml exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"

# 3. Check index usage
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch
   FROM pg_stat_user_tables
   WHERE seq_scan > 1000
   ORDER BY seq_scan DESC
   LIMIT 10;"

# 4. Check for missing indexes (sequential scans on large tables)
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT relname, seq_scan, seq_tup_read, n_live_tup
   FROM pg_stat_user_tables
   WHERE seq_scan > 0 AND n_live_tup > 10000
   ORDER BY n_live_tup DESC;"

# 5. Check dead tuple bloat
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT relname, n_dead_tup, n_live_tup,
          round(n_dead_tup::numeric / greatest(n_live_tup, 1) * 100, 2) AS dead_pct
   FROM pg_stat_user_tables
   WHERE n_dead_tup > 1000
   ORDER BY n_dead_tup DESC;"

# 6. Check container resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 7. Check Neo4j query performance
docker compose -f docker-compose.prod.yml logs --since 30m neo4j | grep -i "query.*slow\|timeout"
```

**Resolution Steps:**

```bash
# Option A: Run VACUUM ANALYZE to update query planner
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c "VACUUM ANALYZE;"

# Option B: Kill long-running queries
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# Option C: Add missing index (if identified)
# Example: CREATE INDEX CONCURRENTLY idx_companies_name ON company.companies USING gin(name gin_trgm_ops);

# Option D: Increase backend workers or memory limits
#    Edit docker-compose.prod.yml:
#    backend:
#      deploy:
#        resources:
#          limits:
#            memory: 2G  # Increase from 1GB

# Option E: Scale backend horizontally
docker compose -f docker-compose.prod.yml up -d --scale backend=3

# Option F: Restart backend to clear caches
docker compose -f docker-compose.prod.yml restart backend
```

**Verification Steps:**

```bash
# 1. Check latency dropped
curl -w "@curl-format.txt" -o /dev/null -s https://api.salesos.com/health

# 2. Check query times
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"

# 3. Check no long-running queries
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '30 seconds';"

# 4. Verify PgBouncer pool health
docker compose -f docker-compose.prod.yml exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"
```

**Communication Checklist:**
- [ ] Ack alert
- [ ] Determine if users are impacted (yes for S2)
- [ ] Post status update hourly
- [ ] Document findings for post-mortem

---

### Playbook 6: Data Loss (S1)

**Trigger Conditions:**
- Accidental DELETE or UPDATE without WHERE clause
- Database corruption (checksum errors, corrupted indexes)
- Application bug causing data deletion
- User reports "my data is missing"
- Backup verification fails

**Immediate Actions (first 15 min):**

```bash
# 1. STOP all writes to the database
docker compose -f docker-compose.prod.yml stop backend

# 2. ASSESS the damage
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT schemaname, tablename, n_live_tup
   FROM pg_stat_user_tables
   ORDER BY n_live_tup DESC;"

# 3. IDENTIFY what was lost and when
# Check recent activity in audit logs
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT * FROM audit.access_log
   WHERE action ILIKE '%delete%' OR action ILIKE '%truncate%' OR action ILIKE '%drop%'
   ORDER BY created_at DESC LIMIT 20;"

# 4. NOTIFY CTO immediately
```

**Investigation Steps:**

```bash
# 1. Check application logs for the deletion event
docker compose -f docker-compose.prod.yml logs --since 2h backend | grep -i "delete\|remove\|drop\|truncate"

# 2. Determine the exact time of data loss
# Check for point-in-time recovery target

# 3. Check for soft-delete / recycle bin
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT count(*) FROM company.companies WHERE deleted_at IS NOT NULL;"

# 4. List available backups
docker compose -f docker-compose.prod.yml exec backup ls -la /backups/postgres/

# 5. Check if WAL archiving is enabled (for point-in-time recovery)
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c "SHOW archive_mode;"
```

**Resolution Steps:**

```bash
# Option A: Restore from backup (see production_runbook.md §3.1)
# 1. Identify the best backup (most recent before data loss)
# 2. Restore to a temporary database
# 3. Export only the lost data
# 4. Import the lost data into production

# Option B: Point-in-time recovery (if WAL archiving enabled)
# See production_runbook.md §4.4 for PTR procedure

# Option C: If soft-deleted, restore from recycle bin
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "UPDATE company.companies SET deleted_at = NULL WHERE deleted_at IS NOT NULL;"
```

**Verification Steps:**

```bash
# 1. Verify data integrity after restore
pwsh -File scripts/verify-backup.ps1

# 2. Check critical table counts match pre-loss expectations
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT 'companies' AS tbl, count(*) FROM company.companies
   UNION ALL
   SELECT 'users', count(*) FROM identity.users
   UNION ALL
   SELECT 'leads', count(*) FROM crm.leads;"

# 3. Check referential integrity
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT count(*) AS orphaned_leads
   FROM crm.leads l
   LEFT JOIN company.companies c ON l.company_id = c.id
   WHERE c.id IS NULL AND l.company_id IS NOT NULL;"

# 4. Smoke tests
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
```

**Communication Checklist:**
- [ ] Immediately notify CTO
- [ ] Determine data loss scope and if customers need to be notified
- [ ] KSA PDPL notification if personal data lost
- [ ] Post-mortem required within 24 hours
- [ ] Document root cause and prevention measures

---

### Playbook 7: Auth/Access Issues (S2)

**Trigger Conditions:**
- `SLAAuthBreach` alert: Auth P99 >800ms
- Users reporting cannot log in
- 401/403 errors increasing
- Token validation failures in logs
- RBAC permission errors

**Immediate Actions (first 15 min):**

```bash
# 1. ACKNOWLEDGE

# 2. CHECK auth endpoint
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/api/v1/identity/login
# Expected: 200 or 422 (for missing body, not 500)

# 3. CHECK recent auth errors
docker compose -f docker-compose.prod.yml logs --since 30m backend | grep -i "401\|403\|token.*invalid\|jwt\|auth.*fail"

# 4. CHECK if JWT secret changed recently
git log --oneline -5 .env.production
```

**Investigation Steps:**

```bash
# 1. Verify JWT secret consistency
docker compose -f docker-compose.prod.yml exec backend env | grep JWT_SECRET_KEY

# 2. Check token expiry configuration
docker compose -f docker-compose.prod.yml exec backend env | grep JWT_ACCESS_TOKEN_EXPIRE

# 3. Check if CSRF is causing issues
docker compose -f docker-compose.prod.yml logs --since 30m backend | grep -i "csrf"

# 4. Check if rate limiting is blocking auth
docker compose -f docker-compose.prod.yml logs --since 30m backend | grep -i "rate.*limit\|429"

# 5. Check database connectivity for user lookup
curl -s https://api.salesos.com/health | jq .database

# 6. Test login end-to-end
curl -s -X POST https://api.salesos.com/api/v1/identity/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}' | jq .
```

**Resolution Steps:**

```bash
# Option A: If JWT secret rotated — all users must re-login
# Notify users via status page

# Option B: Fix CSRF configuration
#    Verify DOMAIN in .env.production matches actual domain
#    Verify CORS_ORIGINS is correct

# Option C: Adjust rate limits for auth endpoints
#    Edit .env.production: RATE_LIMIT_AUTH=50  # Increase from 20

# Option D: Restart backend to apply config changes
docker compose -f docker-compose.prod.yml restart backend

# Option E: If database issue — see Playbook 2
```

**Verification Steps:**

```bash
# 1. Auth endpoint works
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/api/v1/identity/login

# 2. Smoke tests pass (includes auth tests)
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com

# 3. No 401/403 errors in logs
docker compose -f docker-compose.prod.yml logs --since 5m backend | grep -ci "401\|403"
# Expected: 0
```

**Communication Checklist:**
- [ ] Ack alert
- [ ] If users cannot log in — post on status page
- [ ] If JWT rotated — instruct users to re-login
- [ ] Document resolution steps for runbook

---

### Playbook 8: Kafka/Queue Failure (S2-S3)

**Trigger Conditions:**
- `QueueDepthHigh` alert: Kafka consumer lag >1000
- Events not being processed (enrichment, scoring, workflows delayed)
- Backend logs show Kafka connection errors
- Data pipeline stalled

**Immediate Actions (first 15 min):**

```bash
# 1. ACKNOWLEDGE alert

# 2. CHECK Kafka status
docker compose -f docker-compose.prod.yml ps kafka
docker compose -f docker-compose.prod.yml exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 3. CHECK consumer lag
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-consumer-groups --bootstrap-server localhost:9092 --group salesos-group --describe

# 4. CHECK backend logs for Kafka errors
docker compose -f docker-compose.prod.yml logs --since 30m backend | grep -i "kafka\|consumer\|producer\|queue"
```

**Investigation Steps:**

```bash
# 1. Check if Kafka is running
docker compose -f docker-compose.prod.yml exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>&1 | head -5

# 2. Check topic details
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-topics --bootstrap-server localhost:9092 --describe --topic salesos-events

# 3. Check disk space for Kafka logs
df -h /var/lib/docker/volumes/salesos_kafka_data/_data

# 4. Check if consumer is alive
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-consumer-groups --bootstrap-server localhost:9092 --group salesos-group --describe
# Look for any consumer with no active members
```

**Resolution Steps:**

```bash
# Option A: Restart backend (reconnects consumers)
docker compose -f docker-compose.prod.yml restart backend

# Option B: If Kafka is down, restart in dependency order
docker compose -f docker-compose.prod.yml restart kafka
sleep 15
docker compose -f docker-compose.prod.yml restart backend

# Option C: Increase partitions for higher throughput
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-topics --bootstrap-server localhost:9092 --alter --topic salesos-events --partitions 6

# Option D: Reset consumer offset (if lag is unrecoverable)
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-consumer-groups --bootstrap-server localhost:9092 --group salesos-group \
  --topic salesos-events --reset-offsets --to-earliest --execute

# Option E: If data loss acceptable, skip the lagged messages
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-consumer-groups --bootstrap-server localhost:9092 --group salesos-group \
  --topic salesos-events --reset-offsets --to-latest --execute
```

**Verification Steps:**

```bash
# 1. Check consumer lag dropped
docker compose -f docker-compose.prod.yml exec kafka \
  kafka-consumer-groups --bootstrap-server localhost:9092 --group salesos-group --describe
# Expected: LAG = 0 or decreasing

# 2. Check events are being processed
docker compose -f docker-compose.prod.yml logs --since 5m backend | grep -i "processed event\|consumed\|produced"

# 3. Check pipeline health (enrichment, scoring)
curl -s https://api.salesos.com/health | jq .
```

**Communication Checklist:**
- [ ] Ack alert
- [ ] Determine if data loss occurred
- [ ] If enrichment/scoring delayed — inform dependent feature owners
- [ ] Post update if events backlogged (ETA for catch-up)

---

### Playbook 9: Backup Recovery (S1)

**Trigger Conditions:**
- Backup verification script fails
- Backup container logs show errors
- No new backup files in `/backups/postgres/` for >26 hours
- Need to restore from backup (data corruption, disaster recovery)

**Immediate Actions (first 15 min):**

```bash
# 1. CHECK backup logs
docker compose -f docker-compose.prod.yml logs --tail 100 backup
ls -la /opt/salesos/backups/postgres/ | tail -10

# 2. CHECK disk space
df -h /var/lib/docker/volumes/salesos_backup_data/_data
df -h /

# 3. IF restoring from backup (data loss scenario):
#    - Stop application services
docker compose -f docker-compose.prod.yml stop backend frontend

# 4. IDENTIFY the best backup
docker compose -f docker-compose.prod.yml exec backup ls -la /backups/postgres/
```

**Investigation Steps (Backup Failure):**

```bash
# 1. Check if PostgreSQL is accessible from backup container
docker compose -f docker-compose.prod.yml exec backup pg_isready -h postgres -p 5432 -U salesos

# 2. Check backup container status
docker compose -f docker-compose.prod.yml ps backup
docker compose -f docker-compose.prod.yml logs backup

# 3. Check cron job ran
docker compose -f docker-compose.prod.yml logs backup | grep "scheduled backup"

# 4. Check S3 upload if configured
docker compose -f docker-compose.prod.yml logs backup | grep "s3\|upload"
```

**Resolution Steps (Backup Failure):**

```bash
# 1. Trigger manual backup
docker compose -f docker-compose.prod.yml run --rm backup /usr/local/bin/backup-db

# 2. If disk full — clean old backups
docker compose -f docker-compose.prod.yml exec backup rm /backups/postgres/salesos_OLD.dump
# OR: docker compose -f docker-compose.prod.yml exec backup find /backups/postgres/ -name "*.dump" -mtime +7 -delete

# 3. If backup container is broken — restart
docker compose -f docker-compose.prod.yml restart backup

# 4. Run backup verification after fix
pwsh -File scripts/verify-backup.ps1
```

**Resolution Steps (Backup Restore):**

```bash
# Full restore procedure (see production_runbook.md §3.1):
# 1. Terminate all connections
# 2. Drop and recreate database
# 3. Restore from backup
# 4. Re-create extensions and schemas
# 5. Run migrations
# 6. Restart services
# 7. Verify data integrity
```

**Verification Steps:**

```bash
# 1. Verify backup file exists and is non-empty
docker compose -f docker-compose.prod.yml exec backup ls -lah /backups/postgres/ | head -5

# 2. Verify backup integrity
docker compose -f docker-compose.prod.yml run --rm backup pg_restore --list /backups/postgres/salesos_LATEST.dump | head -20

# 3. Run verification script
pwsh -File scripts/verify-backup.ps1

# 4. If restore was needed — run smoke tests
pwsh -File scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com

# 5. Check data integrity
docker compose -f docker-compose.prod.yml exec postgres psql -U salesos -d salesos -c \
  "SELECT schemaname, tablename, n_live_tup
   FROM pg_stat_user_tables
   ORDER BY n_live_tup DESC LIMIT 20;"
```

**Communication Checklist:**
- [ ] Ack alert
- [ ] If backup failed but no data loss — S3, monitor next backup
- [ ] If restoring from backup — S1 with full process
- [ ] Notify CTO if backup failure is persistent
- [ ] Document root cause

---

## 5. Communication Templates

### 5.1 Internal Notification — Incident Opened (S1-S2)

```
🚨 INCIDENT OPENED — S{LEVEL}

Title: {SHORT TITLE}
Service: {service_name}
Impact: {description of user impact}
Started: {UTC timestamp}
On-call: {your_name}
Status: Investigating

Channel: #incident-{YYYY-MM-DD}-{short-desc}
Slack Thread: {link to alert}

Next Update: {UTC timestamp, +30min for S1, +1h for S2}
```

### 5.2 Internal Status Update

```
📋 INCIDENT UPDATE — S{LEVEL}

Title: {SHORT TITLE}
Status: {Investigating | Identified | Implementing | Monitoring | Resolved}
Duration: {time since start}

Finding: {what we found}
Next Step: {what we're doing now}
ETA: {estimated time or "TBD"}

Next Update: {UTC timestamp}
```

### 5.3 Internal Resolution Notification

```
✅ INCIDENT RESOLVED — S{LEVEL}

Title: {SHORT TITLE}
Resolved: {UTC timestamp}
Duration: {total duration}
Root Cause: {one-line summary}
Resolution: {what fixed it}

Post-Mortem: {link to doc} — Scheduled for {date}
```

### 5.4 Customer Communication (S1-S2)

```
Subject: [SalesOS Status] {SERVICE} Disruption

We are currently experiencing {DESCRIPTION} affecting {AFFECTED FEATURES}.

Impact: {USER IMPACT}
Start Time: {UTC TIMESTAMP}
Status: {Investigating | Identified | Implementing | Monitoring | Resolved}

Our team is actively investigating and will provide updates every {FREQUENCY}.

We apologize for the inconvenience and are working to restore service as quickly as possible.

— SalesOS Engineering Team
```

### 5.5 Status Page Updates

| Phase | Message |
|-------|---------|
| Investigating | [Investigating] We are aware of issues with {feature}. Our team is investigating. Updates to follow. |
| Identified | [Identified] The issue has been identified. We are implementing a fix. Expected resolution: {ETA}. |
| Monitoring | [Monitoring] A fix has been deployed. We are monitoring for stability. |
| Resolved | [Resolved] The issue has been resolved. All services are operating normally. |

---

## 6. Post-Mortem Process

### 6.1 When Required

| Severity | Post-Mortem Required | Deadline |
|----------|---------------------|----------|
| S1 | Yes | 48 hours |
| S2 | Yes | 48 hours |
| S3 | Recommended | 1 week |
| S4 | Optional | — |
| S5 | No | — |

### 6.2 Post-Mortem Template

```markdown
# Post-Mortem: {INCIDENT TITLE}

> Date: YYYY-MM-DD
> Severity: S{LEVEL}
> Duration: {HH:MM}
> Author: {NAME}
> Status: Draft / Final

---

## Summary

<1-2 sentence summary of what happened>

## Impact

- **Users affected**: {NUMBER or %}
- **Duration**: {START} to {END} ({DURATION})
- **Revenue impact**: {ESTIMATE or "Unknown"}
- **Data impact**: {NONE / Description}
- **SLA impact**: {YES/NO — credit if applicable}

## Timeline (UTC)

| Time | Event |
|------|-------|
| {TIME} | First alert received |
| {TIME} | Triage complete |
| {TIME} | Root cause identified |
| {TIME} | Fix deployed |
| {TIME} | Service confirmed recovered |
| {TIME} | Incident closed |

## Root Cause (5 Whys)

1. **Why did the incident occur?**
   → [Direct cause]
2. **Why did [direct cause] happen?**
   → [Underlying cause]
3. **Why did [underlying cause] occur?**
   → [Systemic cause]
4. **Why was [systemic cause] not prevented?**
   → [Process/gap cause]
5. **Why did [process/gap cause] exist?**
   → [Root cause]

## Contributing Factors

- {Factor 1}
- {Factor 2}

## What Went Well

- {Positive 1}
- {Positive 2}

## What Went Wrong

- {Issue 1}
- {Issue 2}

## Action Items

| # | Action | Owner | Priority | Due Date | Status |
|---|--------|-------|----------|----------|--------|
| 1 | {ACTION} | {OWNER} | P{0-3} | {DATE} | Open |
| 2 | {ACTION} | {OWNER} | P{0-3} | {DATE} | Open |
| 3 | {ACTION} | {OWNER} | P{0-3} | {DATE} | Open |

## Detection

- **How detected**: {Monitoring alert / User report / Internal discovery}
- **Time to detect**: {DURATION}
- **Detection improvement**: {What could improve detection}

## Response

- **Time to acknowledge**: {DURATION}
- **Time to resolve**: {DURATION}
- **Response improvement**: {What could improve response}

## Lessons Learned

<Key takeaways and how this changes our process>
```

### 6.3 Post-Mortem Process Steps

1. **Schedule** post-mortem meeting within 48 hours (S1-S2)
2. **Invite** all responders and relevant stakeholders
3. **Complete** the template collaboratively
4. **Review** action items and assign owners
5. **Create** GitHub Issues for each action item
6. **Update** runbook/playbook with lessons learned
7. **Share** post-mortem with the team
8. **Track** action items to completion in next sprint

---

## 7. Tooling

### 7.1 Monitoring & Alerting

| Tool | Purpose | URL / Location |
|------|---------|---------------|
| Prometheus | Metrics collection & alert evaluation | `infra/monitoring/prometheus.yml` |
| Alertmanager | Alert routing & notification | `infra/monitoring/alertmanager.yml` |
| Alert Rules | Predefined alert conditions | `infra/monitoring/alerts.yml` |
| Grafana | Dashboards & visualization | `https://monitoring.salesos.com` |
| Slack | Alert notifications | `#salesos-critical` (S1), `#salesos-alerts` (S3+) |

### 7.2 Key Grafana Dashboards

| Dashboard | Purpose |
|-----------|---------|
| SalesOS Overview | High-level service health, request rate, error rate |
| SalesOS Performance | Latency histograms (p50/p95/p99), DB query perf |
| SalesOS Infrastructure | CPU/Memory/Disk per node, cluster health |
| SalesOS Business | API usage by endpoint, tenant activity |
| PostgreSQL | Connections, query time, cache hit ratio |
| Neo4j | Query perf, connection pool, heap usage |

### 7.3 Runbooks & Documentation

| Document | Location | Content |
|----------|----------|---------|
| **Incident Response Plan v2** | `docs/INCIDENT_RESPONSE_PLAN.md` | This document — severity, playbooks, post-mortem |
| **On-Call Runbook** | `docs/ONCALL_RUNBOOK.md` | Quick reference for on-call engineers |
| **Production Runbook** | `docs/production_runbook.md` | Detailed recovery procedures for all services |
| **Deployment Runbook** | `infra/k8s/DEPLOYMENT_RUNBOOK.md` | Deployment, rollback, K8s-specific procedures |
| **SLA Document** | `docs/sla.md` | Service level commitments, credits, reporting |

### 7.4 Recovery Tools

| Tool / Command | Purpose | Reference |
|----------------|---------|-----------|
| `docker compose` | Docker Compose orchestration | `production_runbook.md` §2 |
| `kubectl rollout undo` | K8s rollback | `DEPLOYMENT_RUNBOOK.md` §7 |
| `scripts/backup.ps1` | Manual database backup | `production_runbook.md` §4 |
| `scripts/verify-backup.ps1` | Backup integrity verification | `production_runbook.md` §4.3 |
| `scripts/smoke-test.ps1` | Post-deploy smoke tests | `DEPLOYMENT_RUNBOOK.md` §5 |
| `scripts/security-audit.ps1` | Security posture scan | `scripts/` |
| `scripts/rotate-secrets.ps1` | Secret rotation | `scripts/` |

### 7.5 Alertmanager Configuration Summary

| Route | Severity | Channel | Repeat Interval |
|-------|----------|---------|-----------------|
| default | all | `#salesos-alerts` | 4h |
| critical | critical | `#salesos-critical` | 1h |
| HighErrorRate/BackendDown/PostgresDown/Neo4jDown/RedisDown | critical | `#salesos-critical` | 30min |
| warnings | warning | `#salesos-alerts` | 4h |

### 7.6 Alert Inhibit Rules

- Critical alerts suppress warning alerts with the same `alertname` and `namespace`
- Prevents noise when a critical issue is already being handled

---

## 8. Training & Drills

### 8.1 Quarterly Tabletop Exercises

Every quarter, conduct a 1-hour tabletop exercise covering one scenario:

| Quarter | Scenario | Focus |
|---------|----------|-------|
| Q1 | PostgreSQL failure + backup recovery | Database recovery |
| Q2 | Security incident (credential leak) | Incident containment |
| Q3 | Application down during peak hours | Communication + escalation |
| Q4 | Full disaster recovery (region failover) | DR procedures |

**Tabletop Exercise Format:**
1. Present scenario (15 min)
2. Team walks through response (30 min)
3. Debrief + document gaps (15 min)
4. Update playbooks with findings

### 8.2 Annual Full-Scale Drill

Once per year, conduct a live drill in staging environment:

**Scope:**
- Simulate S1 incident (e.g., database corruption)
- On-call engineer responds (rotated so everyone participates)
- Full incident lifecycle: detection → triage → contain → eradicate → recover → post-mortem
- Measure: time to acknowledge, time to resolve, communication quality

**After-Action Review:**
- Compare actual response times against targets
- Identify gaps in tooling, documentation, or training
- Update playbooks and runbooks
- Report to CTO

### 8.3 New Hire Onboarding

Every new engineer joining the team must complete:

1. **Read**: IRP v2, Production Runbook, On-Call Runbook
2. **Shadow**: Complete 2 on-call shifts with senior engineer
3. **Simulation**: Respond to a simulated alert in staging
4. **Sign-off**: Engineering Lead confirms readiness for solo on-call

### 8.4 Exercise Schedule

| Date | Type | Scenario | Lead |
|------|------|----------|------|
| 2026-10-15 | Tabletop | PostgreSQL failure | Engineering Lead |
| 2027-01-15 | Tabletop | Security incident | Security Engineer |
| 2027-04-15 | Tabletop | Application down | DevOps Engineer |
| 2027-07-01 | Full Drill | Disaster recovery | CTO |

### 8.5 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Time to acknowledge | <5 min S1, <10 min S2 | Alertmanager timestamps |
| Time to respond | <15 min S1 | On-call system |
| Time to contain | <30 min S1 | Incident timeline |
| Time to resolve | <4 hours S1 | Incident timeline |
| Post-mortem completion | Within 48 hours S1 | Calendar |
| Action item closure | Within 1 sprint | Sprint tracking |
| Drill participation | 100% of on-call engineers | Attendance log |

---

## Appendix A: Quick Reference — Alert to Playbook Mapping

| Alert Name | Severity | Playbook |
|------------|----------|----------|
| BackendServiceDown | S1 | Playbook 1 |
| BackendUnhealthy | S1 | Playbook 1 |
| PostgresDown | S1 | Playbook 2 |
| Neo4jDown | S1 | Playbook 2 |
| RedisDown | S1 | Playbook 2 |
| DBPoolSaturated | S1 | Playbook 2 |
| HighErrorRate | S1 | Playbook 3 |
| SLACriticalPathBreach | S1 | Playbook 5 |
| SLAAuthBreach | S1 | Playbook 7 |
| DiskSpaceLow | S1 | Playbook 2 |
| HighLatency | S2 | Playbook 5 |
| BackendDegraded | S3 | Playbook 3 |
| HighLatencyP95 | S3 | Playbook 5 |
| PostgresHighConnections | S3 | Playbook 2 |
| SlowDatabaseQueries | S3 | Playbook 5 |
| SlowAIInference | S3 | Playbook 5 |
| QueueDepthHigh | S3 | Playbook 8 |
| MemoryUsageHigh | S3 | Playbook 5 |
| NoTraffic | S3 | Playbook 1 |
| WebSocketConnectionsHigh | S4 | Playbook 5 |
| RedisHighMemory | S4 | Playbook 2 |

## Appendix B: Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0 | 2026-07-13 | Engineering Lead | Initial incident response plan |
| v2.0 | 2026-07-14 | Documentation Engineer | Full rewrite: 9 playbooks, team roles, process flow, training & drills, alert mapping, on-call runbook |
| v2.0 | 2026-07-14 | Documentation Engineer | Added ONCALL_RUNBOOK.md — quick reference for on-call engineers |

---

*Last Updated: 2026-07-14 · Version: 2.0*
*Owner: Engineering Lead · Review: Quarterly*
*Next Review: 2026-10-14*
