# SLI / SLO / Alert skeleton — SalesOS (PROD-W8-002)

**Classification:** proposed thresholds — **not** production-measured.  
**Rule files:** `salesos/infra/monitoring/alerts.yml`, `alerting-rules-production.yml`, `alerting-rules-staging.yml`  
**No cloud vendor account required** for local Prometheus + Alertmanager.

## Proposed SLOs (review after staging soak)

| SLI | Measurement | Proposed SLO | Alert sketch |
|-----|-------------|--------------|--------------|
| Availability | success of `/ping` or blackbox | ≥ 99.5% / 30d | `< 99%` over 15m → S1 |
| Error ratio | 5xx / requests | < 1% | `> 2%` 5m → S2; `> 5%` → S1 |
| Live latency | p95 `/health/live` | < 200ms | sustained breach → S2 |
| List APIs | p95 companies list (staging data) | < 1s | `> 2s` sustained → S2 |
| DB up | `pg_up` | 100% critical path | `PostgresDown` → S1 |
| Cache | Redis `redis_up` | if in GA matrix | `RedisDown` → S1/S2 |
| Graph | Neo4j health if in GA | degraded allowed with SQL fallback | `Neo4jDown` → S2 |
| Queue | Kafka lag (if `EVENT_BUS_TYPE=kafka`) | baseline after soak | `QueueDepthHigh` → S2 |
| Schema drift | alembic current vs head (job) | 0 in prod | any drift → S1 |

## Alert severity mapping (on-call)

| Sev | Meaning | Example rules already in `alerts.yml` |
|-----|---------|----------------------------------------|
| S1 | wake / page | `BackendServiceDown`, `PostgresDown`, `HighErrorRate` |
| S2 | business hours | `HighLatencyP95`, `RedisHighMemory`, `Neo4jDown` |

Wire receivers in `alertmanager.yml` via env (`SLACK_WEBHOOK_URL`, etc.) — leave empty locally.

## Local verification (config-only OK)

```bash
# From repo root
docker compose up -d prometheus alertmanager grafana
curl -s http://localhost:9090/-/ready
curl -s http://localhost:9093/-/ready

# Reload rules after edit
curl -X POST http://localhost:9090/-/reload
```

Live SLIs on staging ≥ 72h remain **needs verify** (Wave 11 soak).
