# Performance Architecture Audit — SalesOS

> **Auditor**: Performance Architect (READ-ONLY)  
> **Date**: 2026-07-13  
> **Scope**: Full-stack — Backend API, Database, Caching, Background Jobs, Frontend, Infrastructure, Search  
> **Sources**: PERFORMANCE_BASELINE.md, ENGINEERING_DASHBOARD.md, PERFORMANCE_OPTIMIZATION_REPORT.md, load-test.py, benchmarks/, benchmark/, 20+ source files

---

## 1. Performance Architecture Overview

### 1.1 Request Lifecycle

```
Client → Nginx (port 80) → Next.js SSR (port 3000) ──rewrites──→ FastAPI (port 8000)
                                      │                                  │
                                      ├─ Dynamic imports (SSR:false)     ├─ Redis cache (optional)
                                      ├─ Skeleton loaders               ├─ PostgreSQL (async pool)
                                      └─ API proxy to backend            ├─ Neo4j (knowledge graph)
                                                                         ├─ Celery worker (Redis broker)
                                                                         ├─ OpenAI (embeddings, async)
                                                                         ├─ Meilisearch (indexing)
                                                                         └─ Prometheus metrics endpoint
```

### 1.2 Stack Summary

| Layer | Technology | Async | Notes |
|-------|-----------|-------|-------|
| Web Server | Nginx | — | Basic proxy, no gzip/caching |
| Frontend | Next.js 14 (standalone) | Partial | SSR:false for 17 widgets |
| API | FastAPI + Uvicorn | Full | Async throughout |
| ORM | SQLAlchemy 2.0 async | Full | async_sessionmaker |
| Cache | Redis (optional) | Full | Graceful degradation |
| Queue | Celery + Redis | Sync tasks wrapping async | asyncio.run() per task |
| Vector DB | pgvector | Full | Cosine via `<=>` operator |
| Search | PostgreSQL tsvector/GIN + pg_trgm | Full | 5s statement timeout |
| Graph | Neo4j | Sync | context managers |
| Monitoring | Prometheus + AlertManager | — | In-memory metrics tracker |

### 1.3 Concurrency Model

- **FastAPI**: Native async throughout — no thread pool, no `run_in_executor` for DB calls
- **Load test**: asyncio + aiohttp/httpx clients, semaphore-gated at 5–30 concurrent per scenario
- **Celery workers**: `worker_prefetch_multiplier` configurable, `task_acks_late=True`
- **Key gap**: Decision Platform engines run **synchronously within API request paths** (CPU-bound, blocking the event loop)

---

## 2. API Latency Analysis

### 2.1 Documented Baselines (from `PERFORMANCE_BASELINE.md`)

| Endpoint | p50 | p95 | p99 | Budget | Status |
|----------|-----|-----|-----|--------|--------|
| `/ping` (no deps) | < 0.1ms | < 0.2ms | < 1ms | — | 🟢 |
| `/health` (DB check) | < 1ms | < 10ms | < 15ms | — | 🟢 |
| `/register` | < 200ms | < 500ms | — | — | 🟢 |
| `/login` | < 100ms | < 300ms | — | — | 🟢 |

### 2.2 Production Budgets (from `ENGINEERING_DASHBOARD.md`)

| Endpoint | p50 | p95 | p99 | Budget | Status |
|----------|-----|-----|-----|--------|--------|
| `GET /companies/{id}` | 45ms | 120ms | 250ms | 200ms | 🟢 p95 ok, p99 exceeds |
| `POST /search` | 180ms | 450ms | 900ms | 500ms | 🟡 p99 nearly 2x budget |
| `GET /timeline` | 90ms | 300ms | 600ms | 300ms | 🟡 p99 2x budget |
| `POST /enrich` | 2.5s | 8s | 15s | 5s | 🔴 all percentiles exceed |

### 2.3 Load Test Design (`scripts/load-test.py`)

The load test covers **5 scenarios** as a GA readiness check:

| Scenario | Endpoint | Semaphore | Default Iters | Notes |
|----------|----------|-----------|---------------|-------|
| Health check | `/health` | 5 | 20 | No auth, fast path |
| Login | `/api/v1/identity/login` | 10 | 10 | Auth flow |
| Dashboard | `/api/v1/dashboard` | 30 | 30 | Highest concurrency |
| Search | `/api/v1/search` | 30 | 20 | POST with JSON body |
| Company detail | `/api/v1/companies/{id}` | 25 | 20 | Single entity lookup |

**Key observations**:

- Semaphore limits are conservative (5–30) — not testing true saturation
- Total max requests per run: 100 (not 100 concurrent users as documented)
- Only 5 critical paths covered — no timeline, enrichment, or write-path testing
- No ramp-up phase, no steady-state measurement
- Timeout: 30s (aiohttp) — too generous for fast endpoints, too short for /enrich
- Error threshold: 5% error rate before FAIL

**File**: `salesos/scripts/load-test.py`

### 2.4 Docker Desktop Overhead

Per `PERFORMANCE_BASELINE.md`:

> Docker Desktop adds **4–7 seconds overhead per request** via port forwarding on Windows/WSL2.

This makes local latency measurements meaningless. The documented baselines were measured "inside Docker network (no Docker Desktop overhead)" via `docker exec`. Production latency should be measured from within the cluster.

---

## 3. Database Performance

### 3.1 Connection Pool (`backend/app/database.py`)

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=20,           # 20 persistent connections
    max_overflow=10,        # +10 overflow (30 max)
    pool_pre_ping=True,     # Verify connection before use
    pool_recycle=3600,      # Recycle every hour
)
```

- **Pool size**: Adequate for single-instance API. At 30 max connections and 100 req/s with 50ms avg, pool is sufficient.
- **`pool_pre_ping=True`**: Adds ~1ms per connection check. Good for reliability, minor latency cost.
- **`pool_recycle=3600`**: Appropriate for PostgreSQL (default idle timeout is usually higher).
- **No connection timeout** configured: `pool_timeout` defaults to 30s — connections may wait long under saturation.

### 3.2 Index Strategy (`backend/benchmark/queries.py` + `domains/search/engine/strategy_matrix.py`)

The strategy matrix maps 8 search intents to specific PostgreSQL index strategies:

| Intent | Pattern | Strategy | Expected p95 (100k) |
|--------|---------|----------|---------------------|
| EXACT_CR | Numeric CR match | B-Tree composite (tenant_id, cr_number) | < 1ms |
| EXACT_NAME | Full name match | B-Tree (tenant_id, name_ar) | < 1ms |
| PARTIAL_NAME | Middle substring | Trigram GIN (name_ar_trgm) | 78ms |
| PARTIAL_HIGH_SELECTIVITY | Common prefix (55% match) | Seq Scan | ~500ms |
| MULTI_FILTER | 2+ field filters | Composite + Trigram | 15–250ms |
| SEMANTIC | Natural language | pgvector HNSW | TBD |
| FULL_TEXT | Arabic full-text | tsvector GIN | TBD |
| SIMILAR | "Like this company" | pgvector HNSW | TBD |

### 3.3 Benchmark Query Categories

The `benchmark/queries.py` file defines **22 parameterized benchmark queries** across 6 categories:

| Category | Count | Queries |
|----------|-------|---------|
| `exact` | 2 | cr_number, name_ar |
| `partial` | 4 | ILIKE name_ar prefix/middle, cr_number prefix, city |
| `filter` | 3 | Multi-field combinations (2–4 fields) |
| `sort` | 6 | created_at, name_ar, confidence_score (ASC/DESC each) |
| `pagination` | 4 | Page 1, mid (offset ~20%), deep (offset ~50%), large page |
| `count` | 2 | COUNT(*) with and without filters |

**File**: `salesos/backend/benchmark/queries.py`

### 3.4 N+1 Detection Risk

No explicit N+1 queries were found in the search or entity retrieval paths. However:

- **`facets_raw()`** (`postgres_repo.py:287-321`): Executes N separate SQL queries (one per facet field) in sequence. With 5 facet fields, this is **5 sequential DB round trips** per faceted search.
- **`process_entity` task** (`tasks.py:240-250`): Calls `_sync_to_graph()` then `_generate_embedding()` **sequentially** even though they are independent operations.
- **Evidence engine**: `collect()` without sources iterates ALL builtin providers per call.

### 3.5 Missing Performance Config

- **Slow query log**: "Not configured" per PERFORMANCE_BASELINE.md
- **`auto_explain`**: Not configured — no automatic EXPLAIN for slow queries
- **No `pg_stat_statements`** tracking mentioned
- **No connection pool monitoring** in Prometheus (no `pg_stat_activity` alerts beyond connection count)

---

## 4. Caching Strategy Assessment

### 4.1 Three Redis Cache Implementations

There are **three separate cache implementations** with overlapping functionality:

| File | Class | Pattern | Features |
|------|-------|---------|----------|
| `backend/sdk/cache.py` | `CacheService` | Direct client | `remember()`, `delete_pattern()` via SCAN, `flushall()` |
| `backend/app/common/cache.py` | (module-level) | Decorator `@cached()` | FastAPI dep caching, SHA-256 key, auto-serialize/deserialize |
| `backend/app/cache.py` | `CacheService` (duplicate) | Direct client | `set_many()`, `get_many()` with pipeline, `flush()` via KEYS |

**Problems**:

1. **Duplicate class name** `CacheService` in two files — namespace collision risk
2. **Different TTL defaults**: SDK uses 300s, common/cache uses 60s
3. **Different key construction**: SDK uses colon-delimited, common/cache uses `tenant:resource:sha256`
4. **Different serialization approaches**: Both use JSON but different key formats
5. **No cache invalidation strategy**: No event-driven invalidation, just TTL expiry
6. **Redis is optional**: All three implementations gracefully degrade (return None/execute function), but the dashboard shows Redis as "🔴 Not Deployed"

### 4.2 In-Memory Caches

| Component | Type | Max Size | Eviction |
|-----------|------|----------|----------|
| `SearchEmbeddingService` | Dict LRU | 1024 entries | Oldest 25% evicted on overflow |
| `EvidenceEngine.store` | Map | **Unbounded** | None |
| `DecisionEngine.history` | Array | **Unbounded** | None |
| `FeedbackEngine.feedbackStore` | Map | **Unbounded** | None |
| `LearningEngine.store` | Array | **Unbounded** | None |
| Rate limiter store | Dict of timestamps | Cleaned hourly | Stale entries > 1h |

**Critical finding** (from PERFORMANCE_OPTIMIZATION_REPORT.md §12.1):

> The in-memory stores grow unboundedly. Without LRU eviction or TTL-based pruning, lookup operations will degrade to O(n) over time regardless of micro-optimizations.

### 4.3 HTTP Caching

- **No `Cache-Control` headers** configured in any API response
- **No ETags**, no `Last-Modified` headers
- **Nginx**: No `proxy_cache` configured, no `gzip` enabled (see §7.2)
- **Next.js**: No `stale-while-revalidate` or ISR configuration

### 4.4 Caching Effectiveness Summary

| Data | Cached? | TTL | Layer |
|------|---------|-----|-------|
| API responses (FastAPI deps) | Optional (Redis) | 60s (configurable) | Backend |
| Embeddings (OpenAI) | Yes (memory LRU) | Until evicted | Backend |
| Company data | No | — | — |
| Dashboard aggregations | Simulated in benchmarks | — | — |
| Search results | No | — | — |
| Static assets (JS/CSS/images) | No (no CDN) | — | Frontend |
| Rate limit counters | Yes (in-memory dict) | Cleanup hourly | Backend |

---

## 5. Background Job Architecture

### 5.1 Celery Configuration (`backend/app/celery_app.py`)

```python
celery_app.conf.update(
    task_serializer="json",
    task_track_started=True,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    task_acks_late=True,               # Acknowledge AFTER execution
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    result_expires=settings.celery_result_expires,
)
```

**Key design choices**:

- `task_acks_late=True`: Good for reliability (prevents lost tasks on worker crash)
- `worker_max_tasks_per_child`: Good for preventing memory leaks in long-lived workers
- `worker_prefetch_multiplier`: Configurable — controls how many tasks a worker reserves ahead

### 5.2 Task Inventory (`backend/app/tasks.py`)

| Task | Description | Max Retries | Parallelism | Bottleneck |
|------|-------------|-------------|-------------|------------|
| `ping` | Worker heartbeat | default | N/A | None |
| `process_entity` | Graph sync + embedding | default + entity delay | **Sequential** | sync_to_graph → generate_embedding (sequential) |
| `index_for_search` | Meilisearch indexing | default + index delay | Synchronous HTTP | Single HTTP call |
| `enrich_company` | Scrape + recompute | default + enrich delay | **Parallel** (scraping) | 10s scraper timeout |
| `sync_notion_database` | Notion import | default-1 + notion delay | Single import | External API |

### 5.3 Async Bridge Pattern

All Celery tasks are **synchronous functions** that wrap async code via `asyncio.run()`:

```python
def _run_async(coro):
    return asyncio.run(coro)
```

This creates a **new event loop per task execution**, meaning:

- No shared event loop state
- No connection pooling across task executions
- Each task creates fresh DB sessions, Redis connections, etc.
- Acceptable for infrequent tasks, wasteful for high-frequency tasks

### 5.4 Queue Abstraction (`backend/sdk/queue.py`)

Two implementations of the `TaskQueue` ABC:

| Implementation | Use Case | Dedup Support |
|---------------|----------|---------------|
| `RedisTaskQueue` | Simple Redis lists + sorted sets (delayed) | `enqueue_unique()` via Redis SET |
| `CeleryTaskQueue` | Production Celery workers | `enqueue_unique()` via Celery inspector |

**Issues**:

- `CeleryTaskQueue.enqueue_unique()` calls `inspect()` which iterates ALL active/scheduled tasks across ALL workers — **O(total_tasks)** per dedup check
- `RedisTaskQueue` has no worker to process tasks — it's just a queue, not a job processor

### 5.5 Background Job Performance Concerns

| Concern | Location | Severity |
|---------|----------|----------|
| `process_entity` runs graph sync + embedding sequentially | `tasks.py:246-247` | Medium |
| Each task creates fresh `asyncio.run()` event loop | `tasks.py:14-15` | Low |
| `_do_scrape` has 10s timeout per scraper | `tasks.py:171-173` | Medium |
| Feature recompute creates 7 new computer instances per call | `tasks.py:209-218` | Medium |
| No batch processing — one entity per task | `tasks.py:240` | Low |

---

## 6. Frontend Performance Analysis

### 6.1 Build Configuration (`frontend/next.config.js`)

```javascript
const nextConfig = {
  output: "standalone",          // Self-contained production build
  typescript: { ignoreBuildErrors: true },  // ⚠️ Skips type checking
  images: { domains: ["localhost"] },       // Only localhost images
};
```

**Gaps**:

- **`ignoreBuildErrors: true`**: TypeScript errors in build are silently ignored — potential runtime failures
- **No `swcMinify`**: Not explicitly configured (defaults to true in Next 14)
- **No `compress`**: Build-level compression not configured
- **No bundle analyzer**: No `@next/bundle-analyzer` configured
- **`images.domains` limited to `["localhost"]`**: Production images from external domains will fail

### 6.2 Code Splitting (`frontend/src/lib/dynamic-imports.tsx`)

**17 components** use `next/dynamic` with `ssr: false`:

| Component | Bundle Path | Loading State |
|-----------|-------------|---------------|
| `DynamicSearchPanel` | `@/components/search-panel` | Hidden div |
| `DynamicCopilotPanel` | `@/components/copilot-panel` | Hidden div |
| `DynamicExecutiveDashboard` | `@/components/executive-dashboard` | Skeleton `h-96` |
| `DynamicPipelineKanban` | `@/components/pipeline-kanban` | Skeleton `h-96` |
| `DynamicTimelineWidget` | `@/components/timeline-widget` | Skeleton `h-64` |
| `DynamicMissionCenterView` | `@/features/dashboard/.../MissionCenterView` | Skeleton `h-64` |
| `DynamicSmartTimelineView` | `@/features/company-intelligence/.../SmartTimelineView` | Skeleton `h-64` |
| `DynamicSignalsFeedView` | `@/features/company-intelligence/.../SignalsFeedView` | Skeleton `h-64` |
| `DynamicRelationshipGraphView` | `@/features/company-intelligence/.../RelationshipGraphView` | Skeleton `h-80` |
| `DynamicCompanyDNAView` | `@/features/company-intelligence/.../CompanyDNAView` | Skeleton `h-64` |
| `DynamicAIRecommendationView` | `@/features/company-intelligence/.../AIRecommendationView` | Skeleton `h-48` |
| `DynamicDecisionMakersView` | `@/features/company-intelligence/.../DecisionMakersView` | Skeleton `h-64` |
| `DynamicBuyingJourneyView` | `@/features/company-intelligence/.../BuyingJourneyView` | Skeleton `h-64` |
| `DynamicRevenueHealthView` | `@/features/revenue-execution/.../RevenueHealthView` | Skeleton `h-48` |
| `DynamicForecastView` | `@/features/revenue-execution/.../ForecastView` | Skeleton `h-64` |
| `DynamicOpportunityListView` | `@/features/revenue-execution/.../OpportunityListView` | Skeleton `h-64` |
| `DynamicMeetingIntelligenceWidget` | `@/features/revenue-execution/.../MeetingIntelligenceWidget` | Skeleton `h-48` |

**Assessment**: Good use of `dynamic()` for code splitting. All widgets are `ssr: false` (client-only), which keeps initial JS bundle smaller. Skeleton loaders prevent CLS (Cumulative Layout Shift). However:

- **No preloading hints**: No `<link rel="preload">` for critical bundles
- **No `priority` flag**: No prioritized loading for critical above-fold widgets
- **No chunk naming**: All dynamic chunks get auto-generated names — no cache optimization
- **No bundle size analysis**: Unknown if any widgets are unexpectedly large

### 6.3 Docker Build (`frontend/Dockerfile`)

```dockerfile
FROM node:22-alpine AS build
# ... build stage ...
RUN NODE_ENV=production ./node_modules/.bin/next build

FROM node:22-alpine AS production
RUN addgroup -S salesos && adduser -S salesos -G salesos
COPY --from=build --chown=salesos:salesos /app/.next/standalone ./
COPY --from=build --chown=salesos:salesos /app/.next/static ./.next/static
COPY --from=build --chown=salesos:salesos /app/public ./public
USER salesos
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1
CMD ["node", "server.js"]
```

**Positives**:

- Multi-stage build (build → production)
- Non-root user (`salesos`)
- Copy only `.next/standalone` + `.next/static` + `public`
- Healthcheck configured

**Gaps**:

- **No `.dockerignore`** verification — build context may be large
- **No layer caching optimization**: `COPY . .` after `npm install` invalidates cache on any source change
- **No startup probe**: Only health check, no startup probe with longer grace period
- **wget dependency**: Adds to image size vs using `node` for health check

### 6.4 Missing Frontend Optimizations

- **No image optimization**: No `next/image` remote patterns beyond localhost, no AVIF/WebP config
- **No font optimization**: Font system (Viga + IBM Plex Sans/Arabic/Mono) not using `next/font` for self-hosting
- **No service worker**: No offline support
- **No bundle analysis**: No `ANALYZE=true` script
- **No Core Web Vitals monitoring**: No web-vitals integration
- **No script prioritization**: All dynamic imports at same priority

---

## 7. Network and Infrastructure Performance

### 7.1 Nginx Configuration (`frontend/nginx.conf`)

```nginx
server {
  listen 80;
  server_name localhost;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
```

**Critical gaps**:

1. **No gzip compression** — all responses sent uncompressed
2. **No caching headers** — `expires`, `Cache-Control` not set for static assets
3. **No `proxy_buffering`** — default `on`, but no tuning
4. **No `proxy_read_timeout`** — default 60s, too long for APIs
5. **No SSL/TLS** — HTTP only (listen 80, no 443)
6. **No rate limiting at Nginx level** — all rate limiting is in-app
7. **No `gzip_types`** — even if gzip were enabled, no MIME type list
8. **No `client_max_body_size`** — default 1MB, may be insufficient for file uploads

### 7.2 Recommended Nginx Additions

```nginx
# Missing from current config:
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
gzip_min_length 256;
gzip_comp_level 6;

location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /api/ {
    proxy_read_timeout 30s;
    proxy_buffering on;
    proxy_cache_valid 200 10s;
}
```

### 7.3 Prometheus Monitoring (`infra/monitoring/prometheus.yml`)

| Job | Target | Scrape Interval | Port |
|-----|--------|-----------------|------|
| `salesos-backend` | backend:8000 | 15s | `/metrics` |
| `prometheus` | localhost:9090 | 15s | `/metrics` |
| `postgres-exporter` | postgres-exporter:9187 | 15s | `/metrics` |
| `redis-exporter` | redis-exporter:9121 | 15s | `/metrics` |

**Gaps**:

- **Neo4j**: No exporter target despite being in alert rules
- **Node exporter**: Not configured (no CPU/memory/disk metrics for the host)
- **Kafka exporter**: Alert rule exists (`kafka_consumer_lag > 1000`) but no scrape target
- **No application-level tracing**: No OpenTelemetry/Jaeger integration

### 7.4 Alert Rules (`infra/monitoring/alerts.yml`)

| Alert | Threshold | Severity | For |
|-------|-----------|----------|-----|
| `HighErrorRate` | 5xx > 5% | critical | 5m |
| `HighLatency` | P99 > 1s | critical | 5m |
| `HighLatencyP95` | P95 > 500ms | warning | 5m |
| `BackendServiceDown` | `up == 0` | critical | 1m |
| `BackendUnhealthy` | `up == 0` | critical | 5m |
| `BackendDegraded` | Any 5xx | warning | 10m |
| `PostgresDown` | `pg_up == 0` | critical | 1m |
| `PostgresHighConnections` | `> 50 connections` | warning | 5m |
| `RedisDown` | `redis_up == 0` | critical | 1m |
| `Neo4jDown` | `neo4j_up == 0` | critical | 1m |
| `SlowDatabaseQueries` | P95 > 1s | warning | 5m |
| `SlowAIInference` | P95 > 10s | warning | 5m |
| `NoTraffic` | Zero requests/5m | warning | 10m |
| `QueueDepthHigh` | Kafka lag > 1000 | warning | 5m |
| `DiskSpaceLow` | < 10% free | critical | 10m |
| `MemoryUsageHigh` | > 90% used | warning | 5m |

**Issues**:

- `BackendServiceDown` and `BackendUnhealthy` are **identical** expressions (`up{job="salesos-backend"} == 0`) with different `for` durations — the 1m alert will always fire first
- `Kafka consumer lag` alert exists but Kafka is marked "🔴 Not Deployed — Planned for V4"
- `Neo4jDown` alert exists but no `neo4j-exporter` scrape target
- No **paging/notification** integration configured (AlertManager routes not shown)

### 7.5 In-Memory Metrics (`backend/app/common/metrics.py`)

The `MetricsTracker` class provides **in-memory Prometheus-style metrics** with predefined histogram buckets:

```python
BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
```

| Metric | Type | Labels |
|--------|------|--------|
| `salesos_http_requests_total` | Counter | method, path, status |
| `salesos_http_request_duration_seconds` | Histogram | method, path |
| `salesos_db_query_duration_seconds` | Histogram | query_name |
| `salesos_ai_inference_duration_seconds` | Histogram | model |
| `salesos_uptime_seconds` | Gauge | — |

**Issues**:

- **In-memory only**: Metrics lost on restart — no persistent storage
- **No cardinality limits**: Path label includes dynamic IDs (e.g., `/api/companies/123`) unless explicitly cleaned
- **No quantile summary**: Histogram quantiles rely on bucket interpolation
- **No export push**: Metrics are pull-only via `/metrics` endpoint — no Pushgateway for batch jobs

---

## 8. Search Performance

### 8.1 Hybrid Search Architecture (`domains/search/engine/hybrid_search.py`)

```
┌───────────┐     ┌──────────────┐
│ Full-Text  │     │   Semantic   │
│ (tsvector) │     │ (pgvector)   │
└─────┬─────┘     └──────┬───────┘
      │                   │
      └────────┬──────────┘
               │
        ┌──────▼──────┐
        │ RRF Fusion  │
        │ (k=60)      │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ Ranked List │
        └─────────────┘
```

**Key implementation details**:

- Full-text and semantic searches run **in parallel** via `asyncio.gather()` (line 164)
- Both use `SET LOCAL statement_timeout = '5s'` (lines 214, 284)
- RRF constant `k=60` (standard literature value)
- Result limit: `limit * 2` fetched from each backend, then fused and paginated
- Filter semantics differ: full-text applies filters in SQL WHERE clause; semantic filters are applied post-hoc via Python loop (lines 182-183)

### 8.2 Search Repository (`domains/search/engine/postgres_repo.py`)

| Operation | Approach | Timeout | Max Page Size |
|-----------|----------|---------|---------------|
| `search_raw` | tsvector `@@ plainto_tsquery()` + GIN index | 10s | 50 |
| `search_by_filters` | tsvector + field equality filters | 10s | 50 |
| `count_raw` | `COUNT(*)` with tsvector match | default | — |
| `facets_raw` | N queries (one per field), GROUP BY | default | 20 per facet |
| `suggest_raw` | `DISTINCT field ILIKE 'prefix%'` | default | 10 |

**Performance notes**:

- `search_raw` uses `count(*) OVER()` window function for total count — **good** (single scan for results + count)
- `search_by_filters` uses **separate COUNT query** then SELECT — **suboptimal** (two scans)
- `facets_raw` uses **N separate queries** for N facet fields — **O(N * table_size)**
- `suggest_raw` uses `ILIKE 'prefix%'` — B-Tree can prefix-scan, but `%middle%` patterns would full-scan
- `search_vector @@ plainto_tsquery()` uses `simple` config in HybridSearchEngine but `arabic` in PostgresSearchRepository — **inconsistent**

### 8.3 Semantic Search Pipeline

1. **Query** → `SearchEmbeddingService.get_embedding(query)` → OpenAI API (cached with LRU)
2. **Vector similarity**: `c.embedding_vector <=> :emb::vector` (pgvector cosine distance)
3. **Score**: `1 - (distance)` = cosine similarity
4. **Fallback**: If OpenAI unavailable or no API key, returns empty list (graceful degradation)

**Performance concerns**:

- Embedding API call is **~50ms network round trip** (OpenAI) per search
- `embedding_vector IS NOT NULL` filter: if many companies lack embeddings, full scan
- No **approximate nearest neighbor** (HNSW/IVFFlat index) mentioned — likely using exact search
- `pgvector` exact search is **O(n * d)** where n=rows, d=3072 dimensions

### 8.4 RRF Fusion Algorithm (`hybrid_search.py:321-382`)

```python
scores[result.id] = 1.0 / (k + rank)  # for each result in each list
```

- O(n) single pass per result list
- No cross-list deduplication cost (Python dicts)
- Final sort: `sorted(all_results.values(), key=lambda r: -r.score)` — O(n log n)

### 8.5 Search Benchmarks

The `benchmarks/search_benchmark.py` uses **simulated latencies** (not real DB queries):

```python
def _simulate_search_latency(record_count: int, base_ms: float = 5.0) -> float:
    return base_ms + (record_count * 0.001) + (math.log(record_count + 1) * 0.5)
```

| Record Count | Full-text (p95) | Semantic (p95) | Hybrid (p95) | Index Creation (p95) |
|-------------|-----------------|----------------|-------------|----------------------|
| 100 | 5.4ms | 47.8ms | 52.8ms | 408ms |
| 1,000 | 7.5ms | 49.8ms | 54.8ms | 3,636ms |
| 10,000 | 17.6ms | 60.0ms | 65.0ms | **35,910ms** ❌ |

**Violation**: Index creation for 10,000 records exceeds 30,000ms budget (p95=35,910ms).

**Critical issue**: All search benchmarks use **mathematical simulations**, not actual PostgreSQL queries. The benchmark results, budgets, and comparisons cannot be trusted as they don't reflect real database behavior (index selectivity, cache warmth, I/O patterns).

### 8.6 Ranking Pipeline (`domains/search/ranking/pipeline.py`)

Four composable stages running **sequentially**:

| Stage | Operation | Complexity |
|-------|-----------|------------|
| `ExactMatchStage` | String equality on `fields` per item | O(items × fields) |
| `PartialMatchStage` | Substring `in` on `fields` per item | O(items × fields) |
| `FreshnessStage` | Age calculation (30-day linear decay) | O(items) |
| `TenantWeightStage` | No-op (placeholder) | O(1) |

**Performance**: For 50 results and 4 fields per stage, ~200 string comparisons — negligible (< 1ms). The real cost is the SQL execution, not the ranking.

---

## 9. Memory and CPU Analysis

### 9.1 Baseline Memory (from `PERFORMANCE_BASELINE.md`)

| Container | Idle Memory | Notes |
|-----------|-------------|-------|
| PostgreSQL | 51MB | With pgvector + pg_trgm extensions |
| Neo4j | 446MB | Highest memory consumer |
| API (FastAPI) | 136MB | Python 3.12-slim |

### 9.2 Docker Image Size

- Backend: ~600MB (Python 3.12-slim)
- Frontend: Node.js 22-alpine (multi-stage, optimizes to standalone output)

### 9.3 Unbounded Memory Growth Risks

Per `PERFORMANCE_OPTIMIZATION_REPORT.md` §12.1:

| Store | Type | Growth Pattern | Risk |
|-------|------|----------------|------|
| `DecisionEngine.history` | Array of all past decisions | Linear with usage | **High** — every evaluate() appends |
| `EvidenceEngine.store` | Map[tenant+entity → EvidenceItem[]] | Per entity, unbounded | **High** — every collect() appends |
| `FeedbackEngine.feedbackStore` | Map[feedbackId → Feedback] | Linear with feedback | Medium |
| `LearningEngine.store` | Array of events | Linear with usage | Medium |
| `SearchEmbeddingService._cache` | Dict (1024 max) | Bounded (LRU-ish on overflow) | Low |
| `Rate limiter _store` | Dict[key → timestamp[]] | Per user+resource, cleaned hourly | Low-Medium |

### 9.4 CPU-Bound Operations in Hot Paths

| Operation | Location | Frequency | Impact |
|-----------|----------|-----------|--------|
| `DecisionEngine.evaluate()` | API request path | Per dashboard load | ~15-45ms (sync, blocks event loop) |
| `crypto.randomUUID()` | DecisionEngine | ~5-20 per evaluate() | ~0.01-0.05ms per call |
| `Array.reduce()` (double pass) | Scoring/Decision engines | Per evaluate() | ~0.5-1ms |
| `Array.some()` in rule loop | DecisionEngine | Per rule × evaluate() | O(rules × evidence) |
| Embedding API call (network I/O) | Search path | Per search | ~50ms (not CPU-bound but blocks) |
| `RRF fusion + sort` | Hybrid search | Per search | ~1ms for 40 results |

---

## 10. Performance Budget Assessment

### 10.1 Current Budgets (from `ENGINEERING_DASHBOARD.md`)

| Endpoint | p95 Budget | Actual p95 | Compliance | Actual p99 | p99 Concern |
|----------|-----------|------------|------------|------------|-------------|
| `GET /companies/{id}` | 200ms | 120ms | 🟢 Within | 250ms | Exceeds p95 budget |
| `POST /search` | 500ms | 450ms | 🟢 Near limit | **900ms** | 🔴 1.8x p95 budget |
| `GET /timeline` | 300ms | 300ms | 🟡 At limit | **600ms** | 🔴 2x p95 budget |
| `POST /enrich` | 5,000ms | **8,000ms** | 🔴 1.6x | **15,000ms** | 🔴 3x p95 budget |

### 10.2 Decision Platform Budgets (Suggested, from PERFORMANCE_OPTIMIZATION_REPORT.md)

| Engine Operation | Estimated Current | Suggested Budget | Status |
|-----------------|-------------------|------------------|--------|
| `DecisionEngine.evaluate()` | 2–15ms | < 10ms | 🟡 Near limit |
| `EvidenceEngine.collect()` | 1–5ms | < 3ms | 🟡 |
| `ScoringEngine.score()` | < 0.5ms | < 1ms | 🟢 |
| `RecommendationEngine.generate()` | 5–20ms | < 15ms | 🟡 |
| `RuleEngine.evaluate()` | 2–8ms | < 5ms | 🟡 |
| `evaluateBatch()` (10 contexts) | 50–300ms | < 100ms | 🔴 Sequential |

### 10.3 Budget Gaps

- **No p99 budgets**: Only p95 budgets are defined — p99 tail latency is not governed
- **No request-per-second (RPS) budgets**: No throughput targets
- **No error budget**: 5% threshold in load test but no formal SLO
- **No latency budget per service**: The Decision Platform engines contribute 15–45ms to `/enrich` but lack individual latency budgets
- **No p50 budgets**: p50 metrics are reported but not budgeted

---

## 11. Bottleneck Identification

### 11.1 Critical Bottlenecks (P0)

| ID | Bottleneck | Evidence | Impact |
|----|-----------|----------|--------|
| BOT-001 | **POST /enrich over budget at all percentiles** | p50=2.5s vs 5s budget, p99=15s | User-facing timeout risk, blocks enrichment pipeline |
| BOT-002 | **Unbounded in-memory stores** | 4 engines with Map/Array stores growing linearly | O(n) degradation, eventual memory exhaustion |
| BOT-003 | **Nginx: no gzip, no caching** | `nginx.conf` has no compression or caching directives | Adds latency for every static asset request |
| BOT-004 | **Search benchmarks are simulated** | `search_benchmark.py` uses `_simulate_search_latency()` | No real performance data for search operations |
| BOT-005 | **Sequential `evaluateBatch()`** | `index.ts:497-503` — for..of loop with await | 10x slowdown for batch operations |

### 11.2 High-Severity Bottlenecks (P1)

| ID | Bottleneck | Evidence | Impact |
|----|-----------|----------|--------|
| BOT-006 | **`facets_raw()` executes N sequential queries** | `postgres_repo.py:304-318` — for loop over fields | Each facet is a full GROUP BY scan |
| BOT-007 | **p99 tail latency across search and timeline** | Dashboard shows p99=900ms (search), 600ms (timeline) | GC pressure from repeated array allocations |
| BOT-008 | **Evidence engine recomputes BUILTIN_PROVIDERS map every `collect()`** | `evidence-engine/index.ts:219-222` | O(providers × types) wasted per call |
| BOT-009 | **Recommendation engine: repeated `getScoreValue()` linear scans** | `recommendation-engine/index.ts:34-44` | 16–32 O(n) scans per `generate()` |
| BOT-010 | **No Redis in infrastructure** | Engineering Dashboard: "🔴 Not Deployed" | All Redis features are no-ops in production |

### 11.3 Medium-Severity Bottlenecks (P2)

| ID | Bottleneck | Evidence | Impact |
|----|-----------|----------|--------|
| BOT-011 | **Three duplicate cache implementations** | `sdk/cache.py`, `app/common/cache.py`, `app/cache.py` | Code complexity, inconsistent behavior |
| BOT-012 | **Rule engine re-sorts registry on every `evaluate()`** | `rule-engine/index.ts:308-310` | O(n log n) for static data |
| BOT-013 | **`search_by_filters` uses separate COUNT + SELECT** | `postgres_repo.py:237-254` | Two scans instead of one `count(*) OVER()` |
| BOT-014 | **No database slow query logging** | PERFORMANCE_BASELINE.md: "Slow query log: Not configured" | No visibility into slow queries |
| BOT-015 | **`process_entity` runs graph sync + embedding sequentially** | `tasks.py:246-247` | Wastes parallelism opportunity |

### 11.4 Low-Severity Bottlenecks (P3)

| ID | Bottleneck | Evidence | Impact |
|----|-----------|----------|--------|
| BOT-016 | Frontend: `ignoreBuildErrors: true` | `next.config.js:5` | Runtime errors from uncaught TS issues |
| BOT-017 | Frontend: `images.domains` limited to `["localhost"]` | `next.config.js:7-9` | Production images fail |
| BOT-018 | No CDN for static assets | No CDN configuration in any file | Higher latency for global users |
| BOT-019 | `CeleryTaskQueue.enqueue_unique()` scans all workers | `sdk/queue.py:93-100` | O(all_tasks) per dedup check |
| BOT-020 | In-memory metrics lost on restart | `metrics.py` — no persistent storage | No historical metrics after crash |

---

## 12. Performance Technical Debt Register

### 12.1 Critical (P0 — Must Fix Before Production Scaling)

| ID | Description | Location | Effort | Owner |
|----|-------------|----------|--------|-------|
| P-TD-001 | Add TTL/LRU eviction to all 4 unbounded in-memory stores | `evidence-engine/`, `decision-engine/`, `feedback-engine/`, `learning-engine/` | 3 days | Backend |
| P-TD-002 | Enable gzip + caching headers in Nginx | `frontend/nginx.conf` | 1 hour | DevOps |
| P-TD-003 | Convert search benchmarks to real PostgreSQL queries | `benchmarks/search_benchmark.py` | 2 days | Search Engineer |
| P-TD-004 | Parallelize `evaluateBatch()` | Decision Platform `index.ts:497-503` | 1 day | AI Engineer |
| P-TD-005 | Deploy and configure Redis | `docker-compose.prod.yml`, env config | 1 day | DevOps |
| P-TD-006 | Add `pg_stat_statements` + `auto_explain` for slow query detection | PostgreSQL config | 2 hours | Database Engineer |

### 12.2 High (P1 — This Sprint)

| ID | Description | Location | Effort | Owner |
|----|-------------|----------|--------|-------|
| P-TD-007 | Merge `facets_raw()` into single query | `postgres_repo.py:287-321` | 1 day | Backend |
| P-TD-008 | Pre-compute BUILTIN_PROVIDERS map at module level | `evidence-engine/index.ts:219-222` | 1 hour | AI Engineer |
| P-TD-009 | Replace repeated `getScoreValue()` with single Map lookup | `recommendation-engine/index.ts:34-44` | 2 hours | AI Engineer |
| P-TD-010 | Parallelize `process_entity` graph sync + embedding | `tasks.py:246-247` | 1 hour | Backend |
| P-TD-011 | Consolidate 3 cache implementations into one | `sdk/cache.py`, `app/common/cache.py`, `app/cache.py` | 2 days | Backend |
| P-TD-012 | Implement p99 budget for all critical endpoints | Spec + monitoring config | 1 day | Architecture |

### 12.3 Medium (P2 — This/Next Sprint)

| ID | Description | Location | Effort | Owner |
|----|-------------|----------|--------|-------|
| P-TD-013 | Pre-sort rule registry, re-sort only on register() | `rule-engine/index.ts:308-310` | 1 hour | AI Engineer |
| P-TD-014 | Use `count(*) OVER()` in `search_by_filters` | `postgres_repo.py:237-238` | 30 min | Backend |
| P-TD-015 | Configure PostgreSQL slow query log (≥500ms) | `postgresql.conf` | 30 min | Database Engineer |
| P-TD-016 | Add Neo4j exporter Prometheus target | `prometheus.yml` | 15 min | DevOps |
| P-TD-017 | Add `proxy_read_timeout` to Nginx API location | `nginx.conf` | 5 min | DevOps |
| P-TD-018 | Fix identical `BackendServiceDown`/`BackendUnhealthy` alerts | `alerts.yml:35-51` | 5 min | DevOps |

### 12.4 Low (P3 — Backlog)

| ID | Description | Location | Effort | Owner |
|----|-------------|----------|--------|-------|
| P-TD-019 | Remove `ignoreBuildErrors: true` | `next.config.js:5` | TBD | Frontend |
| P-TD-020 | Expand `images.domains` for production | `next.config.js:7-9` | 5 min | Frontend |
| P-TD-021 | Add bundle analyzer (`@next/bundle-analyzer`) | `next.config.js` | 1 hour | Frontend |
| P-TD-022 | Add `next/font` self-hosting for font stack | Layout components | 2 hours | Frontend |
| P-TD-023 | Add `<link rel="preload">` for critical bundles | `_document.tsx` or `<Head>` | 1 hour | Frontend |
| P-TD-024 | Evaluate CDN for static assets (CloudFront/Azure CDN) | Infrastructure | 3 days | DevOps |
| P-TD-025 | Add `node_exporter` for host CPU/memory/disk metrics | `prometheus.yml` | 1 hour | DevOps |
| P-TD-026 | Add `SALESOS_` prefix to all env vars (consistency) | `docker-compose.yml` | 1 day | DevOps |
| P-TD-027 | Remove `redis_socket_timeout` from env (hardcoded in settings) | `app/config.py` | 30 min | Backend |

---

## Appendix A: File Reference Index

| File | Purpose |
|------|---------|
| `salesos/PERFORMANCE_BASELINE.md` | Infrastructure and API latency baselines |
| `salesos/docs/PERFORMANCE_OPTIMIZATION_REPORT.md` | Decision Platform engine optimizations |
| `salesos/scripts/load-test.py` | GA readiness load test (5 scenarios) |
| `salesos/backend/benchmarks/runner.py` | Benchmark orchestration, result storage, comparison |
| `salesos/backend/benchmarks/search_benchmark.py` | Simulated search benchmarks (not real queries) |
| `salesos/backend/benchmarks/api_benchmark.py` | Simulated API endpoint benchmarks |
| `salesos/backend/benchmarks/dashboard_benchmark.py` | Simulated dashboard benchmarks |
| `salesos/backend/benchmarks/rag_benchmark.py` | Simulated RAG pipeline benchmarks |
| `salesos/backend/benchmarks/cli.py` | CLI entry point for benchmark suite |
| `salesos/backend/benchmarks/results/c41d3e01.json` | Sample benchmark run results |
| `salesos/backend/benchmark/runner.py` | Real DB query benchmark runner |
| `salesos/backend/benchmark/queries.py` | 22 parameterized benchmark queries |
| `salesos/backend/benchmark/reporter.py` | Markdown/JSON report generator |
| `salesos/backend/benchmark/data_generator.py` | Deterministic test data generator |
| `salesos/backend/app/database.py` | SQLAlchemy async engine + connection pool config |
| `salesos/backend/app/common/cache.py` | Redis decorator cache for FastAPI deps |
| `salesos/backend/app/common/redis_client.py` | Singleton async Redis client with graceful degradation |
| `salesos/backend/app/common/rate_limit.py` | In-memory sliding window rate limiter |
| `salesos/backend/app/common/metrics.py` | In-memory Prometheus-style metrics tracker |
| `salesos/backend/app/cache.py` | Duplicate CacheService implementation |
| `salesos/backend/sdk/cache.py` | CacheService with remember/scan patterns |
| `salesos/backend/sdk/queue.py` | TaskQueue ABC + Redis/Celery implementations |
| `salesos/backend/app/celery_app.py` | Celery configuration |
| `salesos/backend/app/tasks.py` | Celery task definitions (5 tasks) |
| `salesos/backend/domains/search/engine/hybrid_search.py` | RRF-based hybrid search engine |
| `salesos/backend/domains/search/engine/postgres_repo.py` | PostgreSQL search repository |
| `salesos/backend/domains/search/engine/planner.py` | Search orchestrator/planner |
| `salesos/backend/domains/search/engine/vector_store.py` | In-memory + pgvector vector stores |
| `salesos/backend/domains/search/engine/embedding_service.py` | OpenAI embedding adapter with LRU cache |
| `salesos/backend/domains/search/engine/strategy_matrix.py` | Search intent → strategy mapping |
| `salesos/backend/domains/search/engine/specifications.py` | Filter specification pattern |
| `salesos/backend/domains/search/ranking/pipeline.py` | 4-stage composable ranking pipeline |
| `salesos/backend/domains/search/contracts/repository.py` | SearchRepository ABC |
| `salesos/backend/domains/search/contracts/models.py` | SearchQuery/SearchResult domain models |
| `salesos/frontend/next.config.js` | Next.js config (standalone, rewrites, images) |
| `salesos/frontend/src/lib/dynamic-imports.tsx` | 17 dynamic component imports |
| `salesos/frontend/Dockerfile` | Multi-stage Docker build |
| `salesos/frontend/nginx.conf` | Basic Nginx reverse proxy (no gzip/cache) |
| `salesos/infra/monitoring/prometheus.yml` | Prometheus scrape config (4 jobs) |
| `salesos/infra/monitoring/alerts.yml` | 15 alert rules |

---

## Appendix B: Performance Scorecard

| Area | Score | Status |
|------|-------|--------|
| API Latency (p50/p95) | 7/10 | Search and timeline borderline; enrich critical |
| API Latency (p99) | 3/10 | Tail latency 2x budget on 3 of 4 endpoints |
| Database Performance | 6/10 | Good index strategy, missing slow query monitoring |
| Caching Strategy | 4/10 | 3 duplicate implementations, Redis not deployed, no HTTP caching |
| Background Jobs | 6/10 | Good Celery config, some sequential patterns |
| Frontend Performance | 5/10 | Good code splitting, no gzip/caching/CDN/font optimization |
| Infrastructure | 4/10 | No Redis, no CDN, nginx bare-minimum, monitoring has gaps |
| Search Performance | 5/10 | Solid architecture, benchmarks are simulations, missing HNSW index |
| Memory Management | 4/10 | 4 unbounded stores, no eviction policies |
| Benchmarking | 3/10 | Two frameworks exist but search benchmarks are simulated, not real |
| **Overall** | **4.7/10** | **Below production readiness for scale** |

---

*Audit generated: 2026-07-13 — READ-ONLY — No files modified.*
