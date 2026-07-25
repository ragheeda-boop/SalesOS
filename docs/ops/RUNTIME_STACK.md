# Runtime stack enablement — SalesOS / AQLIYA (PROD-W4 / W8)

**Status:** config & documentation (2026-07-22)  
**Canonical stacks:**

| Environment | Compose entry | Observability |
|-------------|---------------|---------------|
| Local (repo root) | `docker-compose.yml` | Prometheus, Grafana, Loki, OTel, Promtail, Alertmanager **included by default** |
| Local / staging app | `salesos/docker-compose.yml` | Prometheus/Grafana/Alertmanager default; Loki/OTel/Promtail via `--profile observability` |
| Staging host | `salesos/infra/staging/docker-compose.staging.yml` | Prometheus/Grafana (see staging file) |
| Production | K8s (`salesos/infra/k8s`) + `docker-compose.prod.yml` patterns | See `salesos/infra/monitoring/README.md` |

## Dependency health matrix (GA)

| Component | Required for SalesOS GA? | Local default | Health signal |
|-----------|--------------------------|---------------|---------------|
| PostgreSQL | **Yes** | Always on | `/health` → `database=connected` |
| Redis / cache | **Yes** (readiness) | Always on + `REDIS_URL` | `/health` → `cache` / `redis` |
| Neo4j | Preferred; SQL fallback exists | Always on; API waits `service_healthy` | `/health/dependencies` → `neo4j` |
| Kafka | **Optional** (degraded OK) | Root: profile `kafka`; App: always present but `EVENT_BUS_TYPE=in_memory` | `/health` → `kafka=in_memory` or `connected` |
| Meilisearch | Optional (search) | Root compose only | Search paths |

### Enable Kafka (when product requires it)

```bash
# Root stack
docker compose --profile kafka up -d
# then set in .env / shell:
# EVENT_BUS_TYPE=kafka
# KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# salesos stack — Kafka already in compose; set:
# EVENT_BUS_TYPE=kafka
```

Signed degraded mode for GA: **Kafka not required** if `EVENT_BUS_TYPE=in_memory` is accepted by Product/CTO.

## Neo4j healthcheck

Compose uses HTTP probe `wget … http://localhost:7474` instead of `cypher-shell -p $PASSWORD` in CMD arrays (host-side env substitution caused flaky / false unhealthy).

API/worker/backend `depends_on: neo4j: condition: service_healthy` so drivers are not created against a half-started graph.

## Frontend image ≠ source (PROD-W4-001)

Stale FE images return **404** for routes that exist as `page.tsx` in source (`/copilot`, `/analytics`, `/marketplace`, …).

```bash
# Root (profile frontend)
docker compose --profile frontend build frontend
docker compose --profile frontend up -d frontend

# salesos
cd salesos
docker compose build frontend
# optional: IMAGE_TAG=$(git rev-parse --short HEAD) docker compose up -d frontend
docker compose up -d frontend
```

Compose tags: `salesos-frontend:${IMAGE_TAG:-local}` + build arg `BUILD_ID=${GIT_SHA:-local}`.

**Do not** treat a long-running full rebuild as done in this wave unless explicitly approved — document + fix service definitions first (this doc + compose args).

## Postgres health flapping (PROD-W4-004)

Healthchecks now use `start_period` (20s) and longer intervals. Residual Docker Desktop flapping remains **needs verify** on Linux staging.

## Observability enablement (PROD-W4-003 / W8)

```bash
# Root — already includes Loki/OTel
docker compose up -d prometheus grafana loki otel-collector alertmanager

# salesos app compose
docker compose --profile observability up -d loki otel-collector promtail
```

SLO / alert skeleton: [`docs/ops/SLO_ALERTS.md`](./SLO_ALERTS.md)  
Secrets hygiene: [`docs/ops/SECRETS_HYGIENE.md`](./SECRETS_HYGIENE.md)
