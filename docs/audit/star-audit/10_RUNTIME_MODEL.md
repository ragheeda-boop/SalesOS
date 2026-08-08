# 10 — RUNTIME: Docker, Compose, Workers, Health

> Source: Source code analysis (Phase 10)
> Classification: IMPLEMENTATION ONLY

---

## 1. Docker Architecture

### 1.1 Backend Dockerfile (Production)

```dockerfile
# Multi-stage build
FROM python:3.12-slim AS builder
# Installs Poetry 2.4.1, dependencies, app sources

FROM python:3.12-slim AS production
# Installs curl + tini, creates non-root salesos user
# HEALTHCHECK: curl -f http://localhost:8000/health
# ENTRYPOINT: tini -- (PID 1 init)
# CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 1.2 Frontend Dockerfile

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
# npm install, npm run build

FROM node:20-alpine AS production
# Copies standalone output
# CMD: node server.js
```

---

## 2. Docker Compose Services

### 2.1 Local Development (`docker-compose.yml`)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| backend | Custom build | 8000 | FastAPI API server |
| frontend | Custom build | 3000 | Next.js frontend |
| postgres | postgres:16 | 5432 | Primary database |
| redis | redis:7 | 6379 | Cache + rate limiting + session |
| neo4j | neo4j:5 | 7474/7687 | Knowledge graph |
| kafka | confluentinc/cp-kafka | 9092 | Event bus |
| zookeeper | confluentinc/cp-zookeeper | 2181 | Kafka dependency |
| meilisearch | getmeili/meilisearch | 7700 | Full-text search |
| celery-worker | Custom build | — | Background tasks |
| celery-beat | Custom build | — | Scheduled tasks |
| celery-flower | Custom build | 5555 | Worker monitoring |
| nginx | nginx:alpine | 80/443 | Reverse proxy |
| minio | minio/minio | 9000/9001 | Object storage |

**Total: 14 services**

### 2.2 Production (`docker-compose.prod.yml`)

- Railway-managed deployment
- Backend + Frontend + Celery worker + Celery beat
- PostgreSQL (Railway managed)
- Redis (Railway managed)

### 2.3 Test (`docker-compose.test.yml`)

- CI test environment
- Isolated services for testing

---

## 3. Celery Workers

### 3.1 Worker Configuration

| Setting | Value |
|---------|-------|
| Broker | Redis |
| Serialization | JSON |
| Timezone | UTC |
| ACKs Late | Yes |
| Includes | app.tasks, domains.employee.tasks, app.modules.communication_hub.tasks |

### 3.2 Celery Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| `calendar_sync_all` | Every 15 min | Google calendar sync |
| `email_sync_all` | Every 15 min | Google email sync |
| `hub_gmail_sync_all` | Every 15 min | Hub Gmail sync |
| `hub_calendar_sync_all` | Every 15 min | Hub calendar sync |
| `webhook_renewal_all` | Hourly | Webhook renewal |
| `score_rebuild_all_employees` | Daily 3:00 AM | Employee score rebuild |
| `signal_retention_cleanup` | Daily 2:00 AM | Signal cleanup |
| `gdpr_purge_expired_users` | Daily 4:00 AM | GDPR purge |
| `worker_health_ping` | Every 5 min | Worker health heartbeat |
| `calendar_event_cleanup` | Daily 2:30 AM | Calendar cleanup |

### 3.3 On-Demand Tasks

| Task | Purpose |
|------|---------|
| `process_entity` | Background entity processing |
| `index_for_search` | Meilisearch indexing |
| `enrich_company` | Full company enrichment pipeline |
| `enrich_company_task` | Async enrichment with Redis caching |
| `sync_notion_database` | Notion database import |

---

## 4. Health Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ping` | GET | Process liveness |
| `/health` | GET | Full health check |
| `/health/live` | GET | Kubernetes liveness probe |
| `/health/ready` | GET | Readiness probe (DB+cache required) |
| `/health/detailed` | GET | Detailed subsystem health |
| `/health/dependencies` | GET | Dependency health (PG, Redis, Kafka, Neo4j) |

### 4.1 Health Check Details

| Check | Tests |
|-------|-------|
| PostgreSQL | `SELECT 1` via async session |
| Redis | `PING` via aioredis |
| Kafka | Producer metadata check |
| Neo4j | Driver connectivity check |
| WebSocket | Connection test |
| Scrapers | Scraper availability |
| Rate Limiter | Limiter status |
| Feature Store | Store availability |
| SLA | SLA monitor status |

---

## 5. Railway Deployment

| Component | Status |
|-----------|--------|
| Backend | ✅ Live (HTTP 200) |
| Frontend | ✅ Live (HTTP 200) |
| Celery Worker | ✅ Running |
| Celery Beat | ✅ Running |
| PostgreSQL | ✅ Managed |
| Redis | ✅ Managed |
| Neo4j | ❌ Offline (graph unavailable) |

---

## 6. Monitoring

| Component | Status |
|-----------|--------|
| Prometheus metrics | ✅ `/metrics` endpoint |
| SLA monitor | ✅ `app/metrics/sla_monitor.py` |
| Client-side monitoring | ✅ `src/lib/monitoring.ts` (sendBeacon) |
| Structured logging | ✅ `app/common/logging_config.py` |
| Request logging | ✅ `RequestLoggingMiddleware` |
| Sentry | ✅ Configured (optional) |

---

## 7. Startup Sequence

```
Phase 0 (Sequential):
  ├── DB init (extensions, Alembic, schema verify)
  ├── Module registry
  ├── Telemetry init
  └── Sentry init

Phase 1 (Parallel):
  ├── Cache, EventRuntime, Activity, TimelineRecorder
  ├── VectorStore, SDKCache, FeatureStoreDomain
  ├── KnowledgeGraph, DecisionCenter, DecisionPlatform
  ├── Widgets/UX, UIEngines, PluginSandbox, Scraper

Phase 2 (Parallel):
  ├── Opportunity, FeatureStore

Phase 3 (Parallel):
  ├── PolicyEngine, RecommendationEngine, ContextBuilder
  ├── BackendSDK → DecisionEngine + DecisionFeedback

Phase 4 (Parallel):
  ├── EmbeddingService → DataFabric
  ├── SearchRuntime, TimelineRuntime → Subscribers

Phase 5:
  └── WebSocket heartbeat + cleanup background tasks
```

**Fault isolation:** `asyncio.gather(return_exceptions=True)` — each phase degrades gracefully.

---

## 8. Infrastructure Health Summary

| Component | Local | Production |
|-----------|-------|------------|
| Backend | ✅ | ✅ |
| Frontend | ✅ | ✅ |
| PostgreSQL | ✅ | ✅ |
| Redis | ✅ | ✅ |
| Neo4j | ✅ | ❌ Offline |
| Kafka | ✅ | ⚠️ In-memory fallback |
| Meilisearch | ✅ | ⚠️ Not confirmed |
| Celery | ✅ | ✅ |
| Nginx | ✅ | ⚠️ Not confirmed |

---

*This document describes the runtime reality. Security details are in 07_SECURITY_COMPARISON.md.*
