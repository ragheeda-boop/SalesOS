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
| Decision evaluate | `salesos_decision_evaluate_duration_seconds` on `GET /metrics` | p95 < 2s; p99 < 5s | `DecisionEvaluateHighLatency` / `Critical` |
| Event fan-out | `salesos_event_fanout_failures_total` | 0 sustained failures | `EventFanoutFailures` → S2 |
| Agent schedule | `salesos_agent_dispatch_errors_total` (API IL-2A path) | 0 sustained | `AgentDispatchErrors` → S2 |

## IL-2A closed-loop metrics (landed — Wave 8 residual)

Exported on `GET /metrics` via `app.metrics.collector`:

| Metric | Type | Source |
|--------|------|--------|
| `salesos_decision_evaluate_duration_seconds` | histogram | `DecisionEngine.evaluate` |
| `salesos_decision_evaluate_total{outcome}` | counter | `ok` / `blocked` / `error` |
| `salesos_event_fanout_failures_total{event_type,reason}` | counter | EventRuntime store timeout/fail + subscriber DLQ |
| `salesos_agent_dispatch_errors_total{reason}` | counter | IL-2A triggers (+ Celery worker process if scraped) |
| `salesos_nba_processing_duration_seconds` | histogram | kept in sync with evaluate |

**Residual:** Celery `agent_dispatch_all` counters live in the worker process memory — API `/metrics` scrape does **not** see them unless a worker scrape or log-based alert is added. Prefer IL-2A API-path reasons (`il2a_*`) for closed-loop alerting until worker scrape exists.

## Alert severity mapping (on-call)

| Sev | Meaning | Example rules already in `alerts.yml` |
|-----|---------|----------------------------------------|
| S1 | wake / page | `BackendServiceDown`, `PostgresDown`, `HighErrorRate`, `DecisionEvaluateCriticalLatency` |
| S2 | business hours | `HighLatencyP95`, `EventFanoutFailures`, `AgentDispatchErrors`, `Neo4jDown` |

Wire receivers in `alertmanager.yml` via env (`SLACK_WEBHOOK_URL`, etc.) — leave empty locally.

## Local verification (config-only OK)

```bash
# From repo root
docker compose up -d prometheus alertmanager grafana
curl -s http://localhost:9090/-/ready
curl -s http://localhost:9093/-/ready

# Reload rules after edit
curl -X POST http://localhost:9090/-/reload

# Confirm metric names on backend scrape
curl -s http://localhost:8000/metrics | rg "salesos_decision_evaluate|salesos_event_fanout|salesos_agent_dispatch"
```

Live SLIs on staging ≥ 72h remain **needs verify** (Wave 11 soak).
Alert scrape on staging/prod Prometheus still **UNVERIFIED** unless evidence is attached under `evidence/wave8-obs/`.
