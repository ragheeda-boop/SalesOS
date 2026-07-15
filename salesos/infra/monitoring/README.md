# SalesOS Monitoring Stack

## URLs (Docker Compose)

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |
| Grafana | http://localhost:3001 | admin / admin |
| Backend Health | http://localhost:8000/health | — |
| Backend Metrics | http://localhost:8000/metrics | Bearer token |

## Grafana Dashboards

All dashboards are in the **SalesOS** folder (auto-provisioned):

| Dashboard | UID | Description |
|-----------|-----|-------------|
| SalesOS Overview | `salesos-overview` | HTTP rate, latency percentiles, error rate, DB queries |
| SalesOS API Metrics | `salesos-api-metrics` | Request throughput, latency, error rate, request volume |
| SalesOS Infrastructure | `salesos-infra-metrics` | DB pool, Redis, memory, WebSocket connections |
| SalesOS Pipeline & System | `salesos-pipeline` | DLQ status, pipeline health metrics |
| SalesOS WebSocket Monitoring | `salesos-ws-monitoring` | WebSocket connection health, heartbeat, throughput |

### How to browse dashboards

1. Open http://localhost:3001
2. Login with `admin` / `admin`
3. Go to **Dashboards → SalesOS** folder
4. Click any dashboard to view

## Prometheus

### Alerting Rules (8 production rules)

| Rule | Severity | Description |
|------|----------|-------------|
| ProductionHighErrorRate | critical | HTTP 5xx > 5% for 3m |
| ProductionHighLatencyP95 | warning | P95 latency > 500ms for 5m |
| ProductionDiskHigh | warning | Disk usage > 80% |
| ProductionPodCrashLooping | critical | Pod restarts > 3x in 15m |
| ProductionCertificateExpiring | warning | TLS cert expires in < 30d |
| ProductionKafkaConsumerLag | warning | Consumer lag > 1000 messages |
| ProductionRedisMemoryHigh | warning | Redis memory > 80% |
| ProductionPostgresConnectionsHigh | warning | DB connections > 80 |

Production rules file: `infra/monitoring/alerting-rules-production.yml`

## Alertmanager

### Integrations

| Channel | Receiver | Status |
|---------|----------|--------|
| Slack #salesos-alerts | `default` | 🔴 Needs real webhook URL |
| Slack #salesos-critical | `critical` | 🔴 Needs real webhook URL |
| PagerDuty | `critical` | 🔴 Needs real routing key |
| Email (SMTP) | `critical` | 🔴 Needs real SMTP credentials |

### How to test alerts

```bash
# Send a test alert to Alertmanager
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert"},"startsAt":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"}]'

# Check active alerts
curl http://localhost:9093/api/v2/alerts

# Check Alertmanager status
curl http://localhost:9093/-/ready
```

### Reload config

```bash
curl -XPOST http://localhost:9093/-/reload
```

## K8s Manifests

For production deployment on Kubernetes:

| Component | Manifests |
|-----------|-----------|
| Prometheus | `infra/k8s/prometheus/` (configmap, deployment, service, prometheus-rule) |
| Alertmanager | `infra/k8s/alertmanager/` (deployment with ConfigMap) |
| Grafana | `infra/k8s/grafana/` (configmap, deployment, service) |

## Architecture

```
Backend (:8000) ──► Prometheus (:9090) ──► Alertmanager (:9093) ──► Slack / PagerDuty / Email
                     │
                     └──► Grafana (:3001)
                     │
Postgres (:5432) ──► postgres-exporter (:9187) ──► Prometheus
Redis (:6379)    ──► redis-exporter (:9121)    ──► Prometheus
```
