# Service Matrix — v5.1.0-bootstrap-green

**Baseline:** `salesos/docker-compose.yml` (GA-P2-03 authoritative stack)
**Validation:** light validated (ADR-101 Green Bootstrap Report, 2026-08-05)
**Total services:** 21 (14 default, 7 gated behind profiles)

---

## Default Profile (14 services)

| # | Service | Image/Build | Port Host:Container | Healthcheck | Depends On | Profile | Notes |
|---|---------|-------------|---------------------|-------------|------------|---------|-------|
| 1 | `postgres` | `pgvector/pgvector:pg16` | `5432:5432` | `pg_isready -U $POSTGRES_USER` — int=10s, timeout=5s, retries=5, start=30s | — | default | Vector DB. Init scripts at `infra/docker/postgres/init`. Auth from `POSTGRES_USER`/`POSTGRES_PASSWORD` env (default DB `salesos`). |
| 2 | `pgbouncer` | `edoburu/pgbouncer:latest` | `6432:6432` | none | `postgres` (healthy) | default | Connection pooler. `pool_mode=transaction`, `max_client_conn=100`, `default_pool_size=25`. Not used by backend (direct PG for asyncpg Alembic compatibility). |
| 3 | `neo4j` | `neo4j:5-community` | `7475:7474`<br>`7688:7687` | `wget -q --spider http://localhost:7474` — int=15s, timeout=10s, retries=12, start=45s | — | default | Graph DB. HTTP port mapped 7475→7474, Bolt port mapped 7688→7687. Auth `neo4j/salesos_neo4j_dev` (NEO4J_AUTH). |
| 4 | `redis` | `redis:7-alpine` | `6379:6379` | `redis-cli ping` — int=10s, timeout=3s, retries=5, start=5s | — | default | Cache / session store / Celery broker. OAuth state store (DEC-120). Data volume `redis-data`. |
| 5 | `zookeeper` | `confluentinc/cp-zookeeper:7.7.2` | (internal `2181` only) | none | — | default | Kafka coordinator. No host port published — accessible only on compose network. Data/log volumes: `zoo_data`, `zoo_logs`. |
| 6 | `kafka` | `confluentinc/cp-kafka:7.7.2` | `9092:9092` | `kafka-broker-api-versions --bootstrap-server localhost:9092` — int=15s, timeout=10s, retries=10, start=40s | `zookeeper` | default | Event bus. Internal listener `PLAINTEXT://kafka:9092`, host listener `PLAINTEXT_HOST://localhost:9093`. `auto.create.topics=true`, `num.partitions=3`, retention 168h. |
| 7 | `schema-registry` | `confluentinc/cp-schema-registry:7.7.2` | `8081:8081` | none | `kafka` | default | Avro schema store. Backed by Kafka (`kafkastore`). |
| 8 | `backend` | **Build:** `./backend/Dockerfile`<br>Stage: `python:3.12-slim` + Poetry 1.8.3 | `8000:8000` | `curl -f http://localhost:8000/health` — int=30s, timeout=10s, retries=5, start=180s | `postgres` (healthy)<br>`redis` (healthy)<br>`kafka` (healthy)<br>`neo4j` (healthy) | default | FastAPI 5.1.0-rc1. Uvicorn via tini entrypoint. Direct PG port (5432) not PgBouncer (6432) — asyncpg hangs under transaction pooling during Alembic checks. Event bus `EVENT_BUS_TYPE` defaults `in_memory`. Env from `.env` file + compose overrides. |
| 9 | `frontend` | **Build:** `./frontend/Dockerfile`<br>Stage: `node:22-alpine`<br>**Image tag:** `salesos-frontend:${IMAGE_TAG:-local}` | `3000:3000` | `wget -qO- http://localhost:3000` — int=30s, timeout=5s, retries=3, start=15s | `backend` (healthy) | default | Next.js 15 production (standalone output). SSR rewrites `/api/*` → `API_REWRITE_URL`. Build args: `NEXT_PUBLIC_API_URL`, `API_REWRITE_URL`, `BUILD_ID`. Must be rebuilt when GA routes 404. |
| 10 | `prometheus` | `prom/prometheus:latest` | `9090:9090` | `wget --spider -q http://localhost:9090/-/ready` — int=10s, timeout=5s, retries=3 | `alertmanager` (started) | default | Metrics TSDB. Config: `infra/monitoring/prometheus.yml`, rules: `alerting-rules-production.yml`, Bearer token for backend `/metrics`. `--web.enable-lifecycle`. |
| 11 | `alertmanager` | **Build:** `./infra/docker/monitoring/alertmanager`<br>Base: `alpine:3.20`<br>Binary: `prom/alertmanager:v0.28.1` | `9093:9093` | `wget --spider -q http://localhost:9093/-/healthy` — int=10s, timeout=5s, retries=3 | — | default | Alert routing (Slack, Email, PagerDuty). Config templated via `entrypoint.sh` with `gettext` env subst. Storage path `--storage.path=/alertmanager`. |
| 12 | `grafana` | `grafana/grafana:latest` | `3001:3000` | `wget -qO- http://localhost:3000/api/health` — int=15s, timeout=5s, retries=5 | `prometheus` (healthy) | default | Dashboards. Datasources + dashboards provisioned from `infra/monitoring/grafana/`. Auth: `GF_SECURITY_ADMIN_USER`/`GF_SECURITY_ADMIN_PASSWORD`. |
| 13 | `postgres-exporter` | `prometheuscommunity/postgres-exporter:latest` | `9187:9187` | none | `postgres` (healthy) | default | Prometheus PG metrics. `DATA_SOURCE_NAME` URI constructed from env vars. |
| 14 | `redis-exporter` | `oliver006/redis_exporter:latest` | `9121:9121` | none | `redis` (healthy) | default | Prometheus Redis metrics. Target `redis:6379`. |

---

## Dev Profile

| # | Service | Image/Build | Port Host:Container | Healthcheck | Depends On | Profile | Notes |
|---|---------|-------------|---------------------|-------------|------------|---------|-------|
| 15 | `kafdrop` | `obsidiandynamics/kafdrop:latest` | `9100:9000` | none | `kafka` | `dev` | Kafka browser UI. `JVM_OPTS=-Xms32M -Xmx64M`. Connects to `kafka:9092` + `schema-registry:8081`. |
| 16 | `redis-commander` | `rediscommander/redis-commander:latest` | `8083:8081` | none | `redis` (healthy) | `dev` | Redis browser UI. Port 8083→8081 (remapped from 8081 to avoid schema-registry conflict — GA-P2-03 fix). |

---

## Backup Profile

| # | Service | Image/Build | Port Host:Container | Healthcheck | Depends On | Profile | Notes |
|---|---------|-------------|---------------------|-------------|------------|---------|-------|
| 17 | `backup` | **Build:** `./infra/docker/backup/Dockerfile`<br>Base: `postgres:16-alpine` | none | none | `postgres` (healthy) | `backup` | Scheduled PG dump. Default cron: daily 02:00. Scripts: `backup-db`, `restore-db`. Retention: 7 days. Optional S3 offload via `S3_BUCKET` env. Trigger manually: `docker compose run --rm backup backup-db`. |

---

## Objectstore Profile

| # | Service | Image/Build | Port Host:Container | Healthcheck | Depends On | Profile | Notes |
|---|---------|-------------|---------------------|-------------|------------|---------|-------|
| 18 | `minio` | `minio/minio:RELEASE.2024-09-22T00-33-43Z` | `9000:9000`<br>`9001:9001` | none | — | `objectstore` | S3-compatible local object store. Console on `:9001`. Auth: `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` (default `minioadmin`). For offsite backup drills only. |

---

## Observability Profile

| # | Service | Image/Build | Port Host:Container | Healthcheck | Depends On | Profile | Notes |
|---|---------|-------------|---------------------|-------------|------------|---------|-------|
| 19 | `loki` | `grafana/loki:3.1.1` | `3100:3100` | none | — | `observability` | Log aggregation. Config: `local-config.yaml` (built-in). |
| 20 | `otel-collector` | `otel/opentelemetry-collector-contrib:0.111.0` | `4317:4317` (gRPC)<br>`4318:4318` (HTTP)<br>`8889:8889` (metrics) | none | `loki` | `observability` | OTel pipeline. Config: `infra/monitoring/otel-collector-config.local.yaml`. Exports traces/logs → Loki, metrics → Prometheus. Env: `ENVIRONMENT`, `SERVICE_VERSION=5.1.0`. |
| 21 | `promtail` | `grafana/promtail:3.1.1` | none | none | `loki` | `observability` | Log shipper. Mounts Docker socket (ro) for container log discovery. Config: `infra/monitoring/promtail-config.yml`. Ships to `loki:3100`. |

---

## Named Volumes

| Volume | Used By |
|--------|---------|
| `pgdata` | postgres |
| `neo4j_data` | neo4j |
| `neo4j_logs` | neo4j |
| `redis-data` | redis |
| `zoo_data` | zookeeper |
| `zoo_logs` | zookeeper |
| `kafka_data` | kafka |
| `prometheus_data` | prometheus |
| `grafana_data` | grafana |
| `backup_data` | backup |
| `minio_data` | minio |

---

## Dependency Graph (Startup Order)

```
Level 0 (no dependencies, default profile)
  postgres ───────────────────────────────────┐
  neo4j ──────────────────────────────────────┤
  redis ──────────────────────────────────────┤
  zookeeper ──────────────────────────────────┤
  alertmanager ───────────────────────────────┤
                                              │
Level 1                                      │
  pgbouncer ← postgres (healthy)             │
  kafka ← zookeeper                          │
  postgres-exporter ← postgres (healthy)     │
  redis-exporter ← redis (healthy)           │
                                              │
Level 2                                      │
  schema-registry ← kafka                    │
                                              │
Level 3 (gate: all core datastores healthy)  │
  backend ← postgres (healthy)               │
          ← redis (healthy)                  │
          ← kafka (healthy)                  │
          ← neo4j (healthy)                  │
                                              │
Level 4                                      │
  frontend ← backend (healthy)               │
  prometheus ← alertmanager (started)         │
                                              │
Level 5                                      │
  grafana ← prometheus (healthy)             │
```

```
Profile-gated services:

  [dev]           kafdrop ← kafka
  [dev]           redis-commander ← redis (healthy)
  [backup]        backup ← postgres (healthy)
  [objectstore]   minio (standalone)
  [observability] loki (standalone)
  [observability] otel-collector ← loki
  [observability] promtail ← loki
```

### Full dependency chain (default services)

```
alertmanager ──┐
               ├──→ prometheus ──→ grafana
postgres ──────┤
  ├─→ pgbouncer
  ├─→ postgres-exporter
  └─→ ┐
neo4j ──→ ┤
redis ──→ ├──→ backend ──→ frontend
  ├─→ redis-exporter
kafka ──→ ┘
  ├─→ schema-registry
  └─→ [kafdrop] (dev)
zookeeper ──→ kafka
```
