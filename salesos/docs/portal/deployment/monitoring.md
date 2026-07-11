# Monitoring Setup Guide

> **المراقبة — Prometheus و Grafana و التنبيهات**

---

## Architecture

```
Application Metrics (Prometheus endpoints)
      │
      ▼
Prometheus Server
      │
      ├── Grafana Dashboards
      ├── Alertmanager → Slack / PagerDuty / Email
      └── Long-term storage (Thanos, optional)
```

---

## Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'salesos-api'
    metrics_path: '/api/v1/metrics'
    static_configs:
      - targets: ['api:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9308']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

---

## Key Metrics

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| `api_request_duration_ms` | Histogram | p95 > 500ms |
| `api_error_rate` | Counter | > 5% for 5 min |
| `db_connections_active` | Gauge | > 80% pool |
| `kafka_consumer_lag` | Gauge | > 10,000 |
| `nba_evaluation_latency_ms` | Histogram | p95 > 3s |
| `rag_retrieval_duration_ms` | Histogram | p95 > 2s |
| `workflow_success_rate` | Gauge | < 90% for 15 min |

---

## Grafana Dashboards

### API Dashboard

```
┌─────────────────────────────────────────────────────────┐
│ Request Rate    │ Error Rate     │ p95 Latency          │
│ 245 req/min     │ 1.2%           │ 187ms                │
├─────────────────────────────────────────────────────────┤
│ Top Endpoints (by latency)                              │
│ /api/v1/search        │ 320ms      │ 🟡                  │
│ /api/v1/rag/query     │ 1045ms     │ 🔴 (over budget)    │
│ /api/v1/revenue/nba   │ 245ms      │ 🟢                  │
└─────────────────────────────────────────────────────────┘
```

### NBA Dashboard

| Panel | Description |
|-------|-------------|
| NBA evaluations/min | Throughput |
| AI vs rule-only split | Source distribution |
| Acceptance rate | Feedback quality |
| Top recommendations | Most common actions |
| Pipeline trace breakdown | rules_ms, scoring_ms, ai_ms |

### Kafka Dashboard

| Panel | Description |
|-------|-------------|
| Consumer lag per group | NBA, Workflow, Analytics |
| Produce/Consume rate | Messages/sec |
| Under-replicated partitions | Cluster health |
| DLQ count | Error rate per hour |

---

## Alerting Rules

```yaml
groups:
  - name: salesos-critical
    rules:
      - alert: HighErrorRate
        expr: rate(api_error_total[5m]) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "API error rate above 5%"

      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(api_request_duration_ms[5m])) > 500
        for: 5m
        labels: { severity: warning }

      - alert: KafkaConsumerLag
        expr: kafka_consumer_lag > 10000
        for: 5m
        labels: { severity: critical }

      - alert: NBALowAcceptance
        expr: nba_acceptance_rate < 0.4
        for: 15m
        labels: { severity: warning }
```

---

## Log Aggregation

```yaml
# docker-compose: add to logging section
logging:
  driver: "loki"
  options:
    loki-url: "http://loki:3100/loki/api/v1/push"
```

Or use ELK stack (Elasticsearch + Logstash + Kibana).

---

## Uptime Monitoring

| Tool | Checks |
|------|--------|
| Health endpoint | `GET /api/v1/health` every 30s |
| Synthetic transactions | Search → Get Company → Create Opp |
| SSL certificate expiry | Alert 30 days before expiry |
| Database connectivity | Connection pool health |
