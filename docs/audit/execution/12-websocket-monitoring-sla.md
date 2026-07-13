# 12 — WebSocket Reliability, Monitoring & SLA Hardening

> Executed: 2026-07-13
> Status: All workstreams complete

---

## 1. WebSocket Reliability

### Files Modified
| File | Change |
|------|--------|
| `backend/intelligence/notifications/websocket.py` | Rewrote `WebSocketManager` |
| `backend/app/routers/notifications.py` | Added tenant-limit enforcement, pong handling, WS metrics endpoint |
| `backend/app/main.py` | Added `asyncio` import, heartbeat + cleanup task startup in lifespan |

### What was done
- **Heartbeat/ping-pong**: Server sends `{"type":"ping","ts":...}` every **30 seconds**. Clients respond with `{"type":"pong"}`. Connections missing 3 heartbeat cycles (90s) are automatically evicted.
- **Connection state management**: Each connection tracks `connected_at`, `last_active`, `last_pong` timestamps. Pong responses update `last_pong`.
- **Max connections per tenant**: **100** hard limit. Exceeding tenants receive `{"type":"error","code":"TENANT_LIMIT"}` and are closed with code `4002`.
- **Connection metrics**: `_ConnectionMetrics` class tracks `total_connections_opened`, `total_connections_closed`, `total_heartbeats_sent/received`, `total_messages_sent`, `rejected_by_limit`.
- **Tenant-scoped counters**: `_tenant_counts` dict tracks per-tenant active connections for limit enforcement.
- **Metrics endpoint**: `GET /notifications/ws/metrics` returns all connection metrics as JSON.
- **Background tasks**: Heartbeat loop and stale-cleanup loop run as `asyncio.create_task()` in the lifespan context; properly cancelled on shutdown.

### Frontend reconnection guidance (for frontend engineer)
```
// Recommended reconnection logic with exponential backoff:
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000]; // max 30s
let attempt = 0;
function connect() {
  const ws = new WebSocket(url);
  ws.onclose = () => {
    const delay = RECONNECT_DELAYS[Math.min(attempt, RECONNECT_DELAYS.length - 1)];
    attempt++;
    setTimeout(connect, delay);
  };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'pong') { /* heartbeat ack */ }
  };
  attempt = 0;
}
```

---

## 2. Monitoring Stack Validation

### Prometheus scrape config — VERIFIED
- `infra/monitoring/prometheus.yml`: Scrapes `backend:8000/metrics` every 15s, plus postgres-exporter, redis-exporter, and self.
- `docker-compose.prod.yml`: All 3 exporters (postgres, redis, caddy) are configured and running.
- **Status**: ✅ No changes needed — config is production-ready.

### New Grafana Dashboards Created
| Dashboard | File | Panels |
|-----------|------|--------|
| **SalesOS API Metrics** | `grafana/dashboards/salesos-api-metrics.json` | Throughput, latency P50/P95/P99, error rates (4xx/5xx), NBA engine timing, DB query duration, AI inference, SLA uptime, top-10 endpoint volume |
| **SalesOS Infrastructure Metrics** | `grafana/dashboards/salesos-infra-metrics.json` | DB pool utilization, overflow, total open; WS connections; cache hit ratio; PostgreSQL backends; Redis memory & hit rate; app uptime |
| **SalesOS WebSocket Monitoring** | `grafana/dashboards/salesos-websocket.json` | Active connections, connection rate, limit gauge, DB pool, cache hit ratio |

### Health Check Aggregation
| Endpoint | Description |
|----------|-------------|
| `GET /health/detailed` | Aggregated health: database (pool stats), cache, graph, kafka, WebSocket metrics, SLA status, uptime, version. Returns `{"status":"healthy"|"degraded","checks":{...}}` |

---

## 3. SLA Monitoring

### Files Created
| File | Purpose |
|------|---------|
| `salesos/SLA_CONFIG.json` | SLA definitions per category with latency/error/uptime thresholds |
| `backend/app/metrics/sla_monitor.py` | Circular-buffer latency tracker + violation evaluator |

### SLA Categories & Thresholds
| Category | p50 | p95 | p99 | Error Budget | Uptime |
|----------|-----|-----|-----|-------------|--------|
| `critical_path` (companies, search, dashboard) | 100ms | 300ms | 700ms | 0.1% | 99.9% |
| `standard` (CRUD, contacts, opportunities) | 200ms | 500ms | 1000ms | 0.5% | 99.5% |
| `enrichment` (enrich, AI, data-fabric) | 2000ms | 8000ms | 15000ms | 1.0% | 99.0% |
| `auth` (login, register, SSO) | 150ms | 400ms | 800ms | 0.1% | 99.95% |
| `health` (health, ping, metrics) | 5ms | 20ms | 50ms | 0.01% | 99.99% |

### SLA Tracking Mechanism
- **Circular buffer**: 100K samples per category, 24h sliding window
- **Evaluation**: `sla_monitor.evaluate()` compares current p50/p95/p99/error_rate against thresholds
- **Violation recording**: Breaches logged with severity (critical for p99/error_budget, warning for p50/p95)
- **Auto-categorization**: `MetricsMiddleware._categorize_path()` maps every incoming request to an SLA category

### SLA Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/admin/sla-report` | Full SLA report: status, breached/healthy counts, per-category metrics and thresholds, recent violations |

---

## 4. Neo4j Backup Automation

### Files Created
| File | Purpose |
|------|---------|
| `scripts/neo4j-backup.ps1` | Windows: offline backup via neo4j-admin dump + online fallback via cypher-shell |
| `scripts/neo4j-recover.ps1` | Windows: recovery from dump file (confirm → stop → clear data → load → restart → verify) |
| `infra/scripts/backup-neo4j.sh` | Linux/Docker: scheduled backup script for the backup container |
| `docker-compose.prod.yml` | Updated backup service to include Neo4j backup at 04:00 daily |

### Backup Procedure
1. Stop Neo4j container for offline dump
2. Run `neo4j-admin database dump neo4j` inside container
3. Copy dump file out via `docker cp`
4. Restart Neo4j
5. Verify dump file exists and is non-empty
6. Rotate old backups (7-day retention)

### Recovery Procedure (documented in neo4j-recover.ps1)
1. Confirm operation (interactive prompt)
2. Stop Neo4j
3. Remove `neo4j_data` volume
4. Start Neo4j, copy dump file in
5. Run `neo4j-admin database load neo4j --overwrite-destination`
6. Restart Neo4j
7. Verify node/relationship counts via `cypher-shell`

### Backup Verification
- `scripts/verify-backup.ps1` updated to include Neo4j connectivity check and node/relationship count verification

---

## 5. Application Metrics

### Files Created
| File | Purpose |
|------|---------|
| `backend/app/metrics/__init__.py` | Module init — exports `collector` and `sla_monitor` singletons |
| `backend/app/metrics/collector.py` | `ApplicationMetricsCollector` — Prometheus-format metrics |
| `backend/app/metrics/sla_monitor.py` | `SLAMonitor` — circular-buffer SLA tracking |

### Metrics Collected (Prometheus format)
| Metric | Type | Labels |
|--------|------|--------|
| `salesos_http_requests_total` | counter | method, path, status |
| `salesos_http_request_duration_seconds` | histogram | method, path |
| `salesos_errors_total` | counter | type (http_5xx, http_4xx) |
| `salesos_websocket_active` | gauge | — |
| `salesos_websocket_connections_total` | counter | — |
| `salesos_websocket_disconnections_total` | counter | — |
| `salesos_db_pool_checkedout` | gauge | — |
| `salesos_db_pool_checkedin` | gauge | — |
| `salesos_db_pool_overflow` | gauge | — |
| `salesos_db_pool_total` | gauge | — |
| `salesos_cache_hits_total` | counter | — |
| `salesos_cache_misses_total` | counter | — |
| `salesos_cache_hit_ratio` | gauge | — |
| `salesos_nba_processing_duration_seconds` | histogram | — |
| `salesos_app_uptime_seconds` | gauge | — |

### Metrics Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /metrics` | Combined Prometheus scrape target (common + new collector) |
| `GET /metrics/pool` | Database connection pool stats (JSON) |
| `GET /metrics/app` | Application-level: WS, cache, errors (JSON) |

---

## New Prometheus Alerts Added

| Alert | Condition | Severity |
|-------|-----------|----------|
| `DBPoolSaturated` | Pool > 90% utilized for 5m | critical |
| `RedisHighMemory` | Memory > 90% of max for 5m | warning |
| `WebSocketConnectionsHigh` | > 80 active for 5m | warning |
| `SLACriticalPathBreach` | Critical path P99 > 700ms for 5m | critical |
| `SLAAuthBreach` | Auth path P99 > 800ms for 5m | critical |

---

## Files Changed/Created Summary

| # | File | Action |
|---|------|--------|
| 1 | `backend/intelligence/notifications/websocket.py` | Modified — heartbeat, limits, metrics |
| 2 | `backend/app/routers/notifications.py` | Modified — tenant limit, pong, metrics endpoint |
| 3 | `backend/app/main.py` | Modified — heartbeat tasks, health/detailed, imports |
| 4 | `backend/app/metrics/__init__.py` | Created |
| 5 | `backend/app/metrics/collector.py` | Created |
| 6 | `backend/app/metrics/sla_monitor.py` | Created |
| 7 | `backend/app/routers/metrics.py` | Modified — collector integration, SLA, metrics/app |
| 8 | `SLA_CONFIG.json` | Created |
| 9 | `infra/monitoring/alerts.yml` | Modified — 5 new alerts |
| 10 | `infra/monitoring/grafana/dashboards/salesos-api-metrics.json` | Created |
| 11 | `infra/monitoring/grafana/dashboards/salesos-infra-metrics.json` | Created |
| 12 | `infra/monitoring/grafana/dashboards/salesos-websocket.json` | Created |
| 13 | `scripts/neo4j-backup.ps1` | Created |
| 14 | `scripts/neo4j-recover.ps1` | Created |
| 15 | `scripts/verify-backup.ps1` | Modified — Neo4j verification added |
| 16 | `infra/scripts/backup-neo4j.sh` | Created |
| 17 | `docker-compose.prod.yml` | Modified — Neo4j backup service |

---

## Validation Commands

```bash
# Python syntax check
python -m py_compile backend/app/metrics/collector.py
python -m py_compile backend/app/metrics/sla_monitor.py
python -m py_compile backend/app/routers/metrics.py
python -m py_compile backend/app/routers/notifications.py
python -m py_compile backend/app/main.py

# JSON validation
python -c "import json; json.load(open('SLA_CONFIG.json'))"
python -c "import json; json.load(open('infra/monitoring/grafana/dashboards/salesos-api-metrics.json'))"

# PowerShell syntax check
powershell -Command "Get-Content scripts/neo4j-backup.ps1 | Out-Null; Write-Host 'OK'"

# Prometheus config check (if docker available)
docker run --rm -v ./infra/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus:v3.3.0 checkconfig /etc/prometheus/prometheus.yml
```
