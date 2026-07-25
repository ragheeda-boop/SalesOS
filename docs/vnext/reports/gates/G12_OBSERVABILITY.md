# Gate G-12: Observability Validation Report

> **Gate**: G-12 — Observability Validation
> **Date**: 2026-07-17
> **Reviewer**: DevOps Engineer
> **Work Order**: WO-PRC-PRODUCTION-READINESS.md
> **Status**: CONDITIONAL

---

## Executive Summary

| Criterion | Result | Status |
|-----------|--------|--------|
| Prometheus metrics endpoints | `/metrics`, `/metrics/pool`, `/metrics/app` — Prometheus-formatted output | PASS |
| Structured logging | JSON-formatted with request context (request_id, tenant_id, user_id, latency) | PASS |
| Alerting configuration | Prometheus alerting rules + Alertmanager (Slack, Email, PagerDuty) | PASS |
| Health check endpoints | `/health`, `/health/live`, `/health/ready`, `/health/detailed`, `/health/dependencies` | PASS |
| Distributed tracing | OpenTelemetry configured (OTLP HTTP exporter) + Sentry integration | CONDITIONAL |
| Logging level configuration | `LOG_LEVEL` env var, configurable at runtime | PASS |
| Grafana dashboards | 2 provisioned dashboards (API metrics + Infrastructure) | PASS |
| Log aggregation | Loki in docker-compose but no log shipping (promtail not configured) | FAIL |
| OpenTelemetry collector | Referenced but not deployed — OTLP endpoint unreachable | FAIL |

---

## Evidence

### 1. Prometheus Metrics Endpoints

**Endpoint** `GET /metrics` (`app/routers/metrics.py:81`):
- Returns combined Prometheus-formatted output from `common.metrics` + `metrics.collector`
- Authenticated via `Depends(verify_token)` (line 21)
- Uses `PlainTextResponse` for direct Prometheus scraping

**Exposed metrics** (from `app/common/metrics.py`):
```
salesos_http_requests_total{method, path, status}       — counter
salesos_http_request_duration_seconds_bucket{le}        — histogram (buckets: 5ms–10s)
salesos_db_query_duration_seconds{query_name}            — histogram
salesos_ai_inference_duration_seconds{model}             — histogram
salesos_uptime_seconds                                   — gauge
```

**Additional endpoints:**
- `GET /metrics/pool` (`app/routers/metrics.py:89`) — DB connection pool stats (checked_out, checked_in, overflow, total_open)
- `GET /metrics/app` (`app/routers/metrics.py:103`) — WebSocket connections, cache hit ratio, error counts (4xx/5xx)
- `GET /api/v1/admin/sla-report` (`app/routers/metrics.py:122`) — SLA compliance per category (requires admin role)

**Metrics middleware** (`app/routers/metrics.py:24`):
- `MetricsMiddleware` — tracks every HTTP request (method, path, status, duration)
- SLA categorization based on path prefix (health, auth, enrichment, critical_path, standard)
- Uses ASGI `__call__` pattern (not BaseHTTPMiddleware) to avoid body streaming deadlocks

**Prometheus scrape config** (`infra/monitoring/prometheus.yml`):
```yaml
scrape_configs:
  - job_name: "salesos-backend"
    metrics_path: "/metrics"
    authorization:
      type: Bearer
      credentials_file: /etc/prometheus/prometheus-token
    static_configs:
      - targets: ["backend:8000"]
  - job_name: "postgres-exporter"
    static_configs:
      - targets: ["postgres-exporter:9187"]
  - job_name: "redis-exporter"
    static_configs:
      - targets: ["redis-exporter:9121"]
```

**Docker Compose integration** — both dev (`docker-compose.yml`) and prod (`docker-compose.prod.yml`) include:
- Prometheus (dev: `prom/prometheus:latest`, prod: `prom/prometheus:v3.3.0` with 15d retention)
- Grafana (dev: `grafana/grafana:latest`, prod: `grafana/grafana:11.6.0` with auth)
- postgres-exporter
- redis-exporter

### 2. Structured Logging

**JSON formatter** — `app/common/logging_config.py`:
```python
class JSONFormatter(logging.Formatter):
    def format(self, record) -> str:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Optional fields when present on record:
        # request_id, tenant_id, user_id, resource, latency_ms
```

**Request logging** — `app/common/middleware.py` (RequestLoggingMiddleware, line 251):
- Logs every request with: http_method, path, status, duration_ms, latency_ms, client_ip, resource
- Enriches with: request_id, tenant_id, user_id (decoded from JWT)
- Adaptive log level: `warning` if duration > 1s, `error` if status >= 500, `info` otherwise

**Configuration** — called in app startup (`main.py:57`):
```python
from app.common.logging_config import configure_logging
configure_logging(settings.log_level)
```

**Quiet loggers**: `httpx`, `httpcore`, `urllib3`, `neo4j` set to WARNING.

**StructuredLogger SDK** — `sdk/telemetry.py` (StructuredLogger, line 47):
- Binds extra context via `.bind(**kwargs)`
- Supports `info`, `error`, `warn`, `debug`, `exception`
- Thread-safe, forwards to Python logging with extra fields

### 3. Alerting Configuration

**Prometheus alerting rules** — `infra/monitoring/alerts.yml` (17 rules):

| Alert | Condition | Severity | Description |
|-------|-----------|----------|-------------|
| HighErrorRate | 5xx rate > 5% over 5m | critical | HTTP server errors |
| HighLatency | P99 > 1s over 5m | critical | 99th percentile latency |
| HighLatencyP95 | P95 > 500ms over 5m | warning | 95th percentile latency |
| BackendServiceDown | up == 0 for 1m | critical | Backend unreachable |
| BackendUnhealthy | up == 0 for 5m | critical | Sustained outage |
| BackendDegraded | 5xx rate > 0 for 10m | warning | Intermittent errors |
| PostgresDown | pg_up == 0 for 1m | critical | Database unreachable |
| PostgresHighConnections | backends > 50 for 5m | warning | Connection spike |
| DBPoolSaturated | utilization > 90% for 5m | critical | Pool exhaustion |
| RedisDown | redis_up == 0 for 1m | critical | Cache unreachable |
| RedisHighMemory | memory > 90% for 5m | warning | Memory pressure |
| Neo4jDown | neo4j_up == 0 for 1m | critical | Graph DB unreachable |
| SlowDatabaseQueries | P95 > 1s for 5m | warning | Slow queries |
| SlowAIInference | P95 > 10s for 5m | warning | Slow AI |
| WebSocketConnectionsHigh | active > 80 for 5m | warning | WS limit approach |
| NoTraffic | 0 req/5m for 10m | warning | Possible routing issue |
| SLACriticalPathBreach | P99 > 700ms for 5m | critical | SLA violation |
| SLAAuthBreach | P99 > 800ms for 5m | critical | Auth SLA violation |

**Production-specific rules** — `infra/monitoring/alerting-rules-production.yml` (9 rules):
- Tiered (S1=critical, S2=warning) with runbook URLs
- Includes: PodCrashLooping, CertificateExpiring, KafkaConsumerLag, ProductionRedisMemoryHigh, ProductionPostgresConnectionsHigh

**Staging-specific rules** — `infra/monitoring/alerting-rules-staging.yml` (7 rules):
- Lower thresholds, same alert categories

**Alertmanager** — `infra/monitoring/alertmanager.yml`:
- Routes: critical → Slack + Email + PagerDuty; warnings → Slack only
- Group by: alertname, severity, namespace
- Repeat intervals: 30m (critical infra), 1h (critical), 4h (warnings)
- Inhibit rules: critical suppresses warning
- Placeholder variables: `${SLACK_WEBHOOK_URL}`, `${PAGERDUTY_ROUTING_KEY}`, etc.

### 4. Health Check Endpoints

| Endpoint | File | Purpose | Response |
|----------|------|---------|----------|
| `GET /health` | `main.py:636` | General health (DB, Redis, rate_limiter, Neo4j, Kafka, scrapers) | `{"status": "ok"|"degraded", ...}` |
| `GET /health/live` | `main.py:410` | K8s liveness — simple process health | `{"status": "alive", "uptime_seconds": N}` |
| `GET /health/ready` | `main.py:565` | K8s readiness — checks critical deps (DB, Cache, Kafka, Neo4j, rate_limiter, scrapers) | `{"status": "ready"|"not_ready", "checks": {...}}` |
| `GET /health/detailed` | `main.py:415` | Full subsystem health (DB pool, cache, Neo4j, Kafka, WS, SLA, uptime, version) | `{"status": "healthy"|"degraded", "checks": {...}}` |
| `GET /health/dependencies` | `main.py:491` | Individual dependency status (postgresql, redis, kafka, neo4j, feature_store) | `{"status": "healthy", "dependencies": {...}, "summary": {...}}` |
| `GET /ping` | `main.py:406` | Simple reachability check | `{"ping": "pong"}` |

**K8s integration**: Backend service in `docker-compose.prod.yml` (lines 259-264) has healthcheck:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  start_period: 30s
  retries: 3
```

### 5. Distributed Tracing

**OpenTelemetry** — `sdk/telemetry.py`:
```python
def setup_telemetry(service_name: str = "salesos"):
    resource = Resource.create({
        "service.name": service_name,
        "service.version": sdk_settings.service_version,
        "deployment.environment": sdk_settings.environment,
    })
    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=sdk_settings.otlp_endpoint)
    )
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
```

**OTLP endpoint** configured in `sdk/config.py`: `http://otel-collector:4318/v1/traces`

**Called at startup** in `main.py:61`: `setup_telemetry("salesos")`

**Span context manager** — `sdk/telemetry.py:82`:
```python
@asynccontextmanager
async def trace_span(name: str, attributes: dict | None = None):
    tracer = get_tracer("salesos")
    with tracer.start_as_current_span(name) as span:
        ...
        yield span
```

**Sentry integration** — `main.py:63-71`:
```python
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
```

**Gap**: The OTel collector (`otel-collector:4318`) is not deployed in any docker-compose configuration. Tracing is configured and initialized, but spans are dropped because the OTLP endpoint is unreachable. No tracing data reaches any backend.

### 6. Logging Level Configuration

**Setting**: `app/config.py:76`: `log_level: str = "DEBUG"`

**Runtime configuration**: `.env.production.template` sets `LOG_LEVEL=INFO`. Dev docker-compose sets `LOG_LEVEL=DEBUG`.

**Initialization**: `main.py:57`: `configure_logging(settings.log_level)` — called before any other initialization.

**Implementation**: `app/common/logging_config.py:42`:
```python
def configure_logging(level: str = "DEBUG"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.DEBUG))
```

### 7. Grafana Dashboards

**SalesOS API Metrics** — `infra/monitoring/grafana/dashboards/salesos-api-metrics.json`:
- Panels: Request Throughput (req/s), Latency Percentiles (P50/P95/P99), Error Rate (%), Error Total by Status, SLA Status, NBA Engine Processing (P95), DB Query Duration (P95), AI Inference Duration (P95), Request Volume (Top 10 paths)

**SalesOS Infrastructure Metrics** — `infra/monitoring/grafana/dashboards/salesos-infra-metrics.json`:
- Panels: DB Connection Pool, DB Pool Utilization (%), DB Total Open Connections, Active WebSocket Connections, WebSocket Connections Total, Cache Hit Ratio, PostgreSQL Active Backends, Redis Memory Usage, Redis Hit Rate, Application Uptime

### 8. Log Aggregation (Loki)

**Deployed** — `docker-compose.yml` (lines 168-174):
```yaml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  command: -config.file=/etc/loki/local-config.yaml
```

**Gap**: No promtail or any log shipping agent configured. Loki runs with default local config but receives no logs. No docker log driver configured to ship to Loki (JSON file driver used in production compose, not Loki).

---

## Findings

### Critical (P0)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| OBS-01 | **OpenTelemetry collector not deployed** — `setup_telemetry()` initializes OTLP exporter pointing to `otel-collector:4318` which does not exist in any compose or K8s config. Tracing spans are silently dropped | High | OPEN |

### High (P1)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| OBS-02 | **No log aggregation pipeline** — Loki is deployed in docker-compose but no promtail/shipper sends logs to it. `docker-compose.prod.yml` uses `json-file` log driver, not Loki | Medium | OPEN |
| OBS-03 | **No tracing dashboard** — Grafana has API and infra dashboards but no dashboard for tracing data (Jaeger/Tempo/Zipkin) | Low | OPEN |

### Low (P3)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| OBS-04 | SLA report is in-memory only — lost on restart, no persistence | Low | OPEN |
| OBS-05 | Audit logging excluded for /health and /metrics paths (config.py:154) — expected but no warning when health checks are failing | Low | OPEN |
| OBS-06 | No `auto_explain` or `pg_stat_statements` configured for slow query detection (noted in PERF-10) | Low | OPEN |

---

## Verdict: CONDITIONAL

| Criterion | Requirement | Actual | Status |
|-----------|-------------|--------|--------|
| Prometheus metrics | Scrape endpoint with key application metrics | `/metrics`, `/metrics/pool`, `/metrics/app` — HTTP, DB, AI, WebSocket, cache, pool metrics | PASS |
| Structured logging | JSON-format logs with request context | JSONFormatter with request_id, tenant_id, user_id, latency_ms | PASS |
| Alerting | Prometheus rules + alert notification | 17 alert rules + Alertmanager (Slack, Email, PagerDuty) + production-specific tiered alerting | PASS |
| Health checks | Liveness + Readiness + Detailed checks | 6 health endpoints (live, ready, health, detailed, dependencies, ping) | PASS |
| Distributed tracing | End-to-end trace capture and export | OTel configured with OTLP exporter, but collector not deployed — spans dropped | CONDITIONAL |
| Logging level | Configurable without code change | LOG_LEVEL env var, runtime configurable | PASS |
| Log aggregation | Centralized log collection and search | Loki deployed but no log shipping — logs remain on container stdout | FAIL |
| Grafana dashboards | Operational dashboards for monitoring | 2 provisioned dashboards (API + Infrastructure) | PASS |

**Verdict: CONDITIONAL PASS**

**Conditions for upgrade to PASS:**
1. Deploy OpenTelemetry collector (otel-collector) in production docker-compose / K8s config and verify spans reach the collector (OBS-01)
2. Configure log shipping — either promtail sidecar, Docker Loki driver, or fluent-bit to ship logs to Loki (OBS-02)

**Remediation Plan:**
- P0 (OBS-01): Sprint 14 — Add otel-collector service to `docker-compose.prod.yml`, verify trace export with sample end-to-end trace
- P1 (OBS-02): Sprint 14 — Add promtail or Docker Loki log driver, validate log ingestion in Grafana Explore
- P3 (OBS-06): Backlog — Add `auto_explain` module for automatic slow query plan capture

---

*Report generated by SalesOS DevOps Engineer — 2026-07-17*
*Data sources: app/main.py, app/common/logging_config.py, app/common/metrics.py, app/routers/metrics.py, app/common/middleware.py (RequestLoggingMiddleware, RequestIDMiddleware), sdk/telemetry.py, app/config.py, infra/monitoring/prometheus.yml, infra/monitoring/alerts.yml, infra/monitoring/alerting-rules-production.yml, infra/monitoring/alerting-rules-staging.yml, infra/monitoring/alertmanager.yml, infra/monitoring/grafana/dashboards/salesos-api-metrics.json, infra/monitoring/grafana/dashboards/salesos-infra-metrics.json, docker-compose.yml, docker-compose.prod.yml, .env.production.template*