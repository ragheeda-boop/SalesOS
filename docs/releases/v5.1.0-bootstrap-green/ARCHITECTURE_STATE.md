# Architecture State — v5.1.0-bootstrap-green

**Date:** 2026-08-06
**Version:** 5.1.0-rc1
**Validation:** light validated (Docker Compose green, 14/14 services healthy)
**GA classification:** production no-go (per GA Engineering Audit 2026-07-22, Production Readiness 38/100)

---

## 1. Repository Layout

Monorepo at `C:\Users\raghe\Documents\Muhide\`.

| Directory | Purpose |
|-----------|---------|
| `salesos/` | Product monorepo — FastAPI backend + Next.js frontend + infra |
| `salesos/backend/` | Python FastAPI API, domain modules, Alembic migrations, runtime services |
| `salesos/frontend/` | Next.js 15 app + 21 `@salesos/*` workspace packages |
| `docs/` | Audits, ADRs, ops runbooks, vNext plans, release notes |
| `data/` | Notion/identity import pipelines (non-runtime GA path) |
| `engineering-os/` | Governance submodule (if present) |
| `.github/` | CI workflows, Dependabot config (moved from `salesos/.github/` per 2026-07-30 fix) |

---

## 2. Backend Architecture

### Framework & Entry Point

- **FastAPI** application (`salesos/backend/app/main.py`, 424 lines)
- **Lifespan** via `@asynccontextmanager`: 5-phase parallel startup (Phase 0–5), graceful shutdown with task cancellation
- **Phased startup** orchestrated by `app/boot/startup.py` (743 lines):
  - Phase 0: Bootstrap (logging, `init_db`, module registry, telemetry, Sentry)
  - Phase 1: Independent services (cache/Redis, event runtime, knowledge graph, search, feature store, rate limiter, background runners, scrapers, etc.) — 20+ services in `asyncio.gather`
  - Phase 2: Feature + opportunity pipelines
  - Phase 3: Decision pipeline (depends on feature_store from Phase 2)
  - Phase 4: Data fabric, integration hub, employee indexing
  - Phase 5: Background tasks (WebSocket heartbeats)

### Database

- **PostgreSQL 16** via `pgvector/pgvector:pg16` image
- **SQLAlchemy** async engine (`asyncpg` driver) with `QueuePool`
- **Alembic** for migrations (82 migrations, head `e5f9a32b0c08`)
- Connection pooling via **PgBouncer** (port 6432, transaction pooling) — but backend bypasses PgBouncer and connects directly to Postgres (port 5432) due to asyncpg compatibility issues with transaction pooling
- Dual-role pattern: migration/DDL uses owner role (`salesos` superuser); runtime uses `salesos_app` restricted role (R-14 STORY-02-01 remediation), with fallback to owner role when app role not provisioned

### Domain Model

Modular DDD layout with explicit domain/runtime separation:

| Layer | Examples |
|-------|----------|
| **Domains** | `domains/employee/`, `domains/feature_store/`, `domains/decision_center/` |
| **Modules** | `modules/identity/`, `modules/admin/`, `modules/company/`, `modules/contact/`, `modules/audit/`, `modules/integration_hub/`, `modules/communication_hub/`, `modules/employee_360/`, `modules/excel_import/`, `modules/notion_sync/`, `modules/revenue_execution/`, `modules/signal_marketplace/`, `modules/sso/`, `modules/work_intelligence/`, `modules/monitoring/`, `modules/api_keys/`, `modules/cache/`, `modules/entity_resolution/`, `modules/executive/`, `modules/decision/` |
| **Runtime** | `runtime/activity_runtime/`, `runtime/capability_framework/`, `runtime/data_fabric_runtime/`, `runtime/decision_runtime/`, `runtime/event_runtime/`, `runtime/feature_store/`, `runtime/knowledge_graph_runtime/`, `runtime/search_runtime/`, `runtime/timeline_runtime/`, `runtime/ux_runtime/`, `runtime/admin_router/` |
| **Application** | `application/dashboard/` |

### Health Endpoints

- `/ping` — liveness
- `/health` — aggregate (DB, cache, graph, kafka, redis, rate limiter, scrapers)
- `/health/live` — liveness + uptime
- `/health/ready` — readiness (DB + cache required)
- `/health/detailed` — per-component with pool stats, SLA, WebSocket metrics
- `/health/dependencies` — per-dependency status with criticality labels

### Key Config (`salesos/backend/app/config.py`)

- `SERVICE_VERSION`: `5.1.0-rc1`
- `env`: `development` (default)
- `jwt_algorithm`: `RS256` (default), but `HS256` in dev `.env`
- `feature_ai_copilot`: `False` (Wave 6 AI honesty)
- `feature_httponly_access_cookie`: `False`
- `event_bus_type`: `in_memory` (GA-degraded; Kafka available but not default)
- `entitlement_enforcement_enabled`: `True`
- `quota_enforcement_enabled`: `True`
- `kg_allow_sql_fallback`: disabled in production
- Secrets: `SECRET_KEY`, `JWT_SECRET_KEY`, Stripe keys, SSO client secrets, SMTP credentials — all env-only, never defaulted

---

## 3. Frontend Architecture

### Framework

- **Next.js 15** App Router with standalone output
- **SSR rewrites**: `/api/*` → backend (Docker network `http://backend:8000` for SSR, browser uses `NEXT_PUBLIC_API_URL`)
- **Docker build**: multi-stage, `eslint.ignoreDuringBuilds: true` (temporary — ADR-102 pending)

### Workspace Packages (21 packages under `salesos/frontend/packages/`)

| Package | Role |
|---------|------|
| `ui/` | Shared UI component library |
| `platform/` | Decision engine, entity resolution, shared platform logic |
| `widgets/` | Dashboard widget components |
| `widget-sdk/` | Widget SDK for embedding |
| `charts/`, `charts-v3/` | Charting libraries (Recharts-based) |
| `forms/` | Form components and validation |
| `hooks/` | Shared React hooks |
| `providers/` | Context providers (auth, tenant, theme) |
| `search/` | Search interfaces |
| `theme/`, `tokens/`, `design-language/`, `design-system/` | Design system |
| `config/`, `runtime/` | Configuration and runtime utilities |
| `renderer/`, `layouts/`, `icons/` | Rendering, layout primitives, icon sets |
| `workspace/`, `workspace-generator/` | Workspace tooling |

### Key Source Directories (`src/`)

- `src/app/` — Next.js App Router pages
- `src/features/` — Feature-level components (dashboard widgets, morning-brief, employee-360)
- `src/components/` — Shared components
- `src/lib/` — Utilities, API client facade
- `src/middleware.ts` — Next.js edge middleware

### Webpack Optimization

Code splitting with dedicated chunks for framework (React/Next), Radix UI, charting libraries, and common utilities (axios, zod, clsx, tailwind-merge).

---

## 4. Service Topology

14 services in `salesos/docker-compose.yml` (all healthy as of bootstrap-green):

| Service | Image | Port | Depends On |
|---------|-------|------|------------|
| **postgres** | `pgvector/pgvector:pg16` | 5432 | — |
| **pgbouncer** | `edoburu/pgbouncer:latest` | 6432 | postgres (healthy) |
| **neo4j** | `neo4j:5-community` | 7475, 7688 | — |
| **redis** | `redis:7-alpine` | 6379 | — |
| **zookeeper** | `confluentinc/cp-zookeeper:7.7.2` | 2181 | — |
| **kafka** | `confluentinc/cp-kafka:7.7.2` | 9092 | zookeeper |
| **schema-registry** | `confluentinc/cp-schema-registry:7.7.2` | 8081 | kafka |
| **backend** | `salesos-backend` (Dockerfile) | 8000 | postgres, redis, kafka, neo4j (all healthy) |
| **frontend** | `salesos-frontend` (Dockerfile) | 3000 | backend (healthy) |
| **prometheus** | `prom/prometheus:latest` | 9090 | alertmanager |
| **grafana** | `grafana/grafana:latest` | 3001 | prometheus (healthy) |
| **alertmanager** | custom Dockerfile | 9093 | — |
| **postgres-exporter** | `prometheuscommunity/postgres-exporter` | 9187 | postgres (healthy) |
| **redis-exporter** | `oliver006/redis_exporter` | 9121 | redis (healthy) |

### Optional Profiles

- **dev**: `kafdrop` (9100), `redis-commander` (8083)
- **observability**: `loki` (3100), `otel-collector` (4317/4318), `promtail`
- **backup**: nightly `backup` container (DB dumps with S3/MinIO support)
- **objectstore**: `minio` (9000/9001) for S3-compatible backup target

---

## 5. Data Layer

| Component | Technology | GA Status |
|-----------|-----------|-----------|
| **Primary DB** | PostgreSQL 16 with pgvector extension | Connected — critical dependency |
| **Graph DB** | Neo4j 5 Community (bolt) | Connected — non-critical |
| **Cache / Session** | Redis 7 Alpine | Connected — critical for rate limiting |
| **Message Queue** | Kafka 7.7.2 (Confluent) with Schema Registry | Connected but `in_memory` mode default — GA-degraded acceptable per Wave 4 |
| **Search** | Meilisearch | Configured |
| **Feature Store** | In-process runtime | Initialized |
| **Connection Pool** | PgBouncer (transaction pool, 25 default) | Running — bypassed by backend for direct Postgres connections |

---

## 6. Security Model

### Authentication

- **JWT** with `HS256` in dev (RS256 default config), access tokens (30 min) + refresh tokens (7 days)
- **SSO** support: Google, Microsoft, GitHub OAuth (env-configured)
- **API Keys** with expiry (365 days default)
- **Bearer token** required on all `/api/v1/*` routes except identity endpoints

### Middleware Stack (inner → outer, `app/boot/middleware.py`)

1. `GZipMiddleware` (minimum 1024 bytes)
2. `BodyCacheMiddleware` (10 MB max)
3. `RequestIDMiddleware` (X-Request-ID)
4. `RequestLoggingMiddleware`
5. `EntitlementEnforcementMiddleware` (STORY-04-03/06-02)
6. `SuspendedTenantWriteGuardMiddleware`
7. `TenantContextMiddleware` (sets ContextVar `tenant_id`)
8. `SecurityHeadersMiddleware`
9. `CsrfEnforcementMiddleware` (CSRF tokens)
10. `MetricsMiddleware`
11. `RateLimitMiddleware` (configurable per-endpoint tiers)
12. `AuditMiddleware`
13. `ApiKeyMiddleware`
14. `CORSMiddleware` (outermost — whitelist-based)

### Tenant Isolation

- `TenantContextMiddleware` extracts tenant ID from `X-Tenant-Id` header
- RBAC via module-level dependencies
- Entitlement enforcement on gated paths
- Suspended-tenant write guard
- **Known P0**: Cross-tenant IDOR in Decision Center (`domains/decision_center/postgres_repo.py` — loads by ID only, no `tenant_id` filter)
- **Known P1**: CSRF bypass on any non-empty `X-API-Key` header

### Audit

- `AuditMiddleware` logs all requests (excludes `/health`, `/metrics`, `/docs`, `/ping`)
- 90-day retention default

---

## 7. Version

**`5.1.0-rc1`** — service version in `app/config.py:SERVICE_VERSION`.

---

## 8. GA Status

**Classification:** production no-go (per GA Engineering Audit, 2026-07-22).

**Scorecard:** Production Readiness **38/100**, Security **48/100**.

**Bootstrap Green (2026-08-05)** validated that the Docker Compose stack starts cleanly with all 14 services healthy, backend migrations at head, frontend builds and serves, and FE→BE SSR integration passes. This is a **development/infrastructure baseline**, not a production milestone.

| Gate | Bootstrap Green |
|------|:---:|
| Docker Compose up | PASS |
| All services healthy | PASS |
| Backend health | PASS |
| DB migrations current | PASS |
| Frontend builds | PASS |
| FE→BE SSR rewrites | PASS |
| TypeScript typecheck | PASS |

**Remaining P0s** (blocking production): cross-tenant IDOR, webhook SSRF + InMemory, Alembic schema drift resolved (fixed in bootstrap), unit tests not green, forecast hardcodes demo input.

**Pilot eligibility:** Conditional only after listed P0s are closed (pilot-ready with conditions — target, not current).
