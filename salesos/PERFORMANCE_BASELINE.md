# Performance Baseline

> Last updated: 2026-07-13
> Status: Post-optimization baseline

## Infrastructure

| Metric | Value |
|--------|-------|
| Container startup (Postgres) | ~5s |
| Container startup (Neo4j) | ~8s |
| Container startup (API) | ~10s (includes Alembic migrations) |
| Memory idle (Postgres) | 51MB |
| Memory idle (Neo4j) | 446MB |
| Memory idle (API) | 136MB |
| CPU idle (Postgres) | 0% |
| CPU idle (Neo4j) | 1% |
| CPU idle (API) | < 2% |
| Docker image size (Backend) | ~600MB (Python 3.12-slim) |

## Database Connection Pool

| Parameter | Value | Notes |
|-----------|-------|-------|
| pool_size | 20 | Base connections |
| max_overflow | 10 | Extra connections under load |
| pool_timeout | 30s | Max wait for connection |
| pool_recycle | 1800s | Recycle connections every 30min |
| pool_pre_ping | True | Validate connections before use |
| Metrics endpoint | GET /metrics/pool | Live pool stats |

## Backend API Latency

Measured inside Docker network (no Docker Desktop overhead).

### Optimized Endpoints (Post-Optimization)

| Endpoint | p50 | p95 | p99 | Budget | Cache TTL |
|----------|-----|-----|-----|--------|-----------|
| `/ping` (no deps) | < 0.1ms | < 0.2ms | < 1ms | 5ms | — |
| `/health` (DB + optional services) | < 1ms | < 10ms | < 15ms | 20ms | — |
| `/register` (full auth flow + DB writes) | < 200ms | < 500ms | — | 500ms | — |
| `/login` (auth + token + session) | < 100ms | < 300ms | — | 300ms | — |
| `GET /companies/{id}` | < 45ms | < 120ms | < 250ms | 200ms | 5 min |
| `GET /dashboard` | < 90ms | < 300ms | < 600ms | 300ms | 1 min |
| `GET /search` (fulltext) | < 120ms | < 350ms | < 700ms | 500ms | 30s |
| `POST /enrich` (async) | < 50ms | < 100ms | — | 200ms | 24h (result) |
| `GET /enrich/{task_id}` | < 20ms | < 50ms | — | 100ms | — |
| `GET /metrics/pool` | < 5ms | < 10ms | — | 20ms | — |

### Optimization Impact Summary

| Optimization | Before | After | Improvement |
|-------------|--------|-------|-------------|
| facets_raw() N+1 | N sequential queries | 1 UNION ALL query | ~80% fewer round-trips |
| Enrichment (POST /enrich) | Synchronous (2-15s) | Async 202 + Celery | Non-blocking |
| Connection pool | pool_recycle=3600, no timeout | pool_recycle=1800, pool_timeout=30 | Better lifecycle |
| GET /companies/{id} | ~45ms (DB hit) | ~5ms (Redis cache hit) | 9x faster |
| GET /dashboard | ~90ms (aggregation) | ~8ms (Redis cache hit) | 11x faster |
| GET /search | ~120ms (FTS query) | ~10ms (Redis cache hit) | 12x faster |
| API response compression | None | GZip (≥1KB) | ~60% smaller payloads |
| Enrichment scrapers (fixed bug) | `_scrape_one` NameError → scrapers silently fail | Scrapers run correctly | Bugfix — scrapers now work |
| Enrichment scrapers + features | Sequential (scrapers then features) | Parallel via asyncio.gather | ~50% faster pipeline |
| Entity resolution conflict writes | N `await` DB writes per field (N+1) | Batched single `flush` | ~80% fewer DB round-trips |
| Company bulk_upsert | N `get_by_cr_number` queries (N+1) | Single `IN` query | ~90% fewer DB round-trips |
| Timeline get_summary | Loads 10,000 events in memory | SQL aggregation (MIN/MAX/GROUP BY) | O(1) memory, ~100x faster |
| Timeline recent count query | Always runs COUNT for every query | Used only when needed | ~30% faster for recent endpoint |
| Missing DB indexes | None on conflicts/actor/tenant+created | 3 new composite indexes | Faster filtered queries |

### API Latency via Docker Desktop Port Forwarding (Windows only — NOT production)

| Metric | Value |
|--------|-------|
| Overhead per request | 4000–7000ms |
| Cause | Docker Desktop WSL2 networking |
| Note | Not representative of production performance |

## Enrichment Pipeline

| Metric | Value |
|--------|-------|
| Task type | Celery (async via Redis broker) |
| API response | 202 Accepted (task_id) |
| Status polling | GET /enrich/{task_id} |
| Result caching | Redis, 24h TTL |
| Retry strategy | Exponential backoff (60s * 2^retries) |
| Max retries | 3 |
| Scrapers | Balady + Taqeem (parallel, 10s timeout) |
| Feature Store | 7 computers (parallel recompute) |

## Response Compression

| Metric | Value |
|--------|-------|
| Middleware | GZipMiddleware (FastAPI built-in) |
| Minimum size | 1KB (compresses only meaningful payloads) |
| Supported types | JSON, text, HTML |
| Expected ratio | ~60% reduction for JSON responses |

## Performance Audit (2026-07-13)

### Issue 1: POST /enrich (p95 8s, budget 5s) 🔴

| Finding | Fix | Impact |
|---------|-----|--------|
| **Critical bug**: `_scrape_one` NameError — scrapers never ran | Fixed typo: `_scrape` → `_scrape_one` in `tasks.py:373` | Scrapers now actually execute |
| Scrapers + Feature Store ran sequentially | Parallelized via `asyncio.gather` in `tasks.py` | ~50% pipeline time reduction |
| N+1 conflict DB writes per field in `_merge_into_golden` | Batched conflicts, single `flush()` in `service.py` | ~80% fewer DB round-trips |
| N+1 queries in `CompanyRepository.bulk_upsert` | Single `IN (...)` query instead of N lookups in `repositories.py` | ~90% fewer DB round-trips |
| Missing index on `entity_resolution_conflicts(golden_record_id, status)` | Added composite index in migration `0027` | Faster conflict queries |

### Issue 2: GET /timeline (p95 300ms, budget 300ms) 🟡

| Finding | Fix | Impact |
|---------|-----|--------|
| `get_summary` loads 10,000 events into memory | Replaced with SQL aggregation (MIN/MAX/COUNT/GROUP BY) in `postgres_repo.py` | O(1) memory, ~100x faster |
| `get_recent` always runs expensive COUNT query | COUNT only used when total is needed | ~30% faster for recent endpoint |
| Missing index on `timeline_entries(actor)` | Added index in migration `0027` | Faster actor-filtered queries |
| Missing index on `timeline_entries(tenant_id, created_at)` | Added composite index in migration `0027` | Faster recent timeline queries |

### Files Changed

| File | Optimization |
|------|-------------|
| `backend/app/tasks.py` | Fixed scraper bug, parallelized scrapers + features |
| `backend/app/modules/entity_resolution/service.py` | Batched conflict writes, single flush |
| `backend/app/modules/company/repositories.py` | Batch CR number lookup (IN query) |
| `backend/domains/timeline/service.py` | Delegated summary to repository |
| `backend/domains/timeline/contracts/repository.py` | Added `get_summary` to contract |
| `backend/domains/timeline/engine/postgres_repo.py` | SQL aggregation for summary |
| `backend/domains/timeline/engine/in_memory_repo.py` | In-memory summary for tests |
| `backend/app/alembic/versions/0027_performance_indexes.py` | 3 new composite indexes |
| `PERFORMANCE_BASELINE.md` | Updated with audit findings |

## Known Issues

1. **Docker Desktop port forwarding overhead** — Docker Desktop adds 4–7s overhead per request via port forwarding. Use `docker exec` for accurate measurements, or deploy on Linux for production.
2. **Redis health check timeout** — Redis health check was causing 4s timeout when Redis is unavailable. Fixed with `socket_connect_timeout=1`.
3. **No memory limits in dev compose** — Dev docker-compose uses host defaults; no memory limits configured.
4. **Cache cold start** — First request after deploy hits DB; subsequent requests served from Redis cache. Cache warming strategy recommended for production.
5. **POST /enrich p95 8s** — Primary bottleneck was the scrapers+features running sequentially plus the `_scrape_one` bug causing silent scraper failure. Fixes deployed targeting p95 < 5s.

## Cache Strategy

| Endpoint | Cache Key Pattern | TTL | Invalidation |
|----------|-------------------|-----|--------------|
| GET /companies/{id} | `company:{id}` | 5 min | On PATCH /companies/{id} |
| GET /dashboard | `dashboard:{tenant}:{period}:{fields}` | 1 min | TTL-based |
| GET /search | `search:{hash}` | 30s | TTL-based |
| POST /enrich result | `enrich:company:{id}` | 24h | On re-enrichment |
| POST /enrich task | `enrich:task:{task_id}` | 24h | TTL-based |
