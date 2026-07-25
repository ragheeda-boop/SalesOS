# SalesOS Monitoring Stack

> Canonical enablement: [`docs/ops/RUNTIME_STACK.md`](../../../docs/ops/RUNTIME_STACK.md)  
> SLOs / alerts: [`docs/ops/SLO_ALERTS.md`](../../../docs/ops/SLO_ALERTS.md)

## URLs (Docker Compose)

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |
| Grafana | http://localhost:3001 | admin / set via `GRAFANA_PASSWORD` |
| Loki | http://localhost:3100 | — (root compose or `--profile observability`) |
| OTel Collector | localhost:4317 (gRPC) / 4318 (HTTP) | — |
| Backend Health | http://localhost:8000/health | — |
| Backend Metrics | http://localhost:8000/metrics | Bearer scrape token (Wave 5) |

## Stack selection

| Compose | Prometheus config | Loki / OTel |
|---------|-------------------|-------------|
| Repo root `docker-compose.yml` | `prometheus.compose-root.yml` (target `api:8000`) | Included |
| `salesos/docker-compose.yml` | `prometheus.yml` + token example | `--profile observability` |

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
2. Login with admin / your `GRAFANA_PASSWORD`
3. Go to **Dashboards → SalesOS** folder
4. Click any dashboard to view

## Prometheus

### Alerting Rules

Production rules: `infra/monitoring/alerting-rules-production.yml`  
Local/dev rules: `infra/monitoring/alerts.yml`

### Scrape token

Do **not** commit real JWTs. Use `prometheus-token.example`. See `docs/ops/SECRETS_HYGIENE.md`.

## Alertmanager

Integrations (Slack / PagerDuty / SMTP) are env-driven — leave empty locally. No cloud vendor required for the local stack.

### How to test alerts

```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert"},"startsAt":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"}]'
curl http://localhost:9093/-/ready
```

## Architecture

```
Backend (:8000) ──► Prometheus (:9090) ──► Alertmanager (:9093)
                     │
                     └──► Grafana (:3001)
App / OTel ──► OTel Collector ──► Loki (:3100) ──► Grafana
Postgres ──► postgres-exporter ──► Prometheus
Redis    ──► redis-exporter    ──► Prometheus
```
