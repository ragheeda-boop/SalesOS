# SalesOS Degraded Mode Matrix

> **GA scope:** Kafka in_memory is accepted degraded mode for GA launch.
> Neo4j/Redis are required; SQL fallback disabled in production.

| Component | Required for GA | Degraded Behavior | User Impact | SLI Adjustment |
|-----------|----------------|-------------------|-------------|----------------|
| PostgreSQL | YES | Full outage | 503 all requests | N/A — blocks GA |
| Redis | YES | Cache misses | +50-200ms latency per uncached query | Standard→Enrichment tier |
| Neo4j | YES | Graph queries fail | Knowledge Graph 503; search falls to fulltext | graph endpoints degraded |
| Kafka | NO (in_memory) | InMemoryEventBus | Event bus local-only; no multi-pod events | Accepted degraded |
| Celery | NO | No background tasks | Async jobs (email, enrichment) not processed | Accepted degraded |
| Loki/OTel | NO | No distributed traces | Debugging harder; metrics still work | Accepted degraded |

## Health Check Status Codes

| Endpoint | All Healthy | Redis Down | Neo4j Down | Kafka Down (Expected) |
|----------|-------------|------------|------------|----------------------|
| /health | healthy | healthy | healthy | healthy |
| /health/detailed | healthy | degraded | degraded | healthy |
| /health/dependencies | healthy | degraded | healthy | healthy |
| /health/ready | ready | not_ready | not_ready | ready |

## Alert Severity Matrix

| Condition | Severity | Response Time | Playbook |
|-----------|----------|---------------|----------|
| Postgres down | S1 | 5 min | DR_RUNBOOK.md §4.1 |
| Redis down | S2 | 15 min | Restart Redis; fallback to cache-miss mode |
| Neo4j down | S2 | 15 min | Restart Neo4j; graph endpoints return 503 |
| DB pool > 80% | S3 | 30 min | Scale backend or increase pool |
| P99 latency > 2x SLA | S2 | 15 min | Check DB/Redis health, recent deploys |
| Error rate > 5% | S1 | 5 min | ONCALL_RUNBOOK.md §first-5-min |
