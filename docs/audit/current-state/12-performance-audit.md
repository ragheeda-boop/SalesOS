# Performance Audit — SalesOS

> **Audit Date:** 2026-07-16
> **Scope:** Backend (FastAPI), Frontend (Next.js), Database (PostgreSQL), Middleware
> **Methodology:** Static code analysis + benchmark report review + pattern scanning

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Backend: Missing Pagination](#2-backend-missing-pagination)
3. [Backend: N+1 Query Patterns](#3-backend-n1-query-patterns)
4. [Backend: Synchronous Blocking in Async Code](#4-backend-synchronous-blocking-in-async-code)
5. [Backend: Missing / Ineffective Caching](#5-backend-missing--ineffective-caching)
6. [Backend: Large / Inefficient Response Payloads](#6-backend-large--inefficient-response-payloads)
7. [Backend: Database Query Efficiency](#7-backend-database-query-efficiency)
8. [Backend: Middleware Chain Overhead](#8-backend-middleware-chain-overhead)
9. [Frontend: Layout & Component Performance](#9-frontend-layout--component-performance)
10. [Frontend: Missing Image Optimization](#10-frontend-missing-image-optimization)
11. [Frontend: Missing Memoization](#11-frontend-missing-memoization)
12. [Frontend: Bundle & Import Efficiency](#12-frontend-bundle--import-efficiency)
13. [Dashboard Performance](#13-dashboard-performance)
14. [Prioritized Recommendation Summary](#14-prioritized-recommendation-summary)
15. [Benchmark Correlation](#15-benchmark-correlation)

---

## 1. Executive Summary

SalesOS demonstrates good baseline DB-level performance (p95 <100ms for most queries at 100k companies according to `reports/benchmark_full.md`), but several architectural patterns and missing optimizations will cause progressive degradation as data and usage scale.

**Overall Score: 6.5/10** — Functional for current scale, but predictable bottlenecks exist at 5x+ data volume or under concurrent load.

| Area | Score | Key Issues |
|------|-------|-----------|
| Missing Pagination | 4/10 | 12+ endpoints return unbounded lists |
| N+1 Patterns | 3/10 | Workspace endpoint loops DB calls per-opportunity |
| Async Blocking | 5/10 | Sync file I/O in async endpoints |
| Caching Coverage | 5/10 | Only 2 endpoints use `@cached` |
| Response Payloads | 6/10 | 360 endpoint returns 20+ sub-collections |
| DB Query Efficiency | 7/10 | Wide rows, no trigram index on partial text |
| Middleware Chain | 6/10 | 7 middleware layers, no overhead measurement |
| Frontend Layout | 5/10 | Un-memoized sidebar, 24-icon import, re-render issues |
| Dashboard | 6/10 | All-at-once fetch, N+1 in NBA feed |

---

## 2. Backend: Missing Pagination

### 2.1 Router-Level Endpoints Without Pagination

| Endpoint | File | Issue |
|----------|------|-------|
| `GET /workflows` | `app/routers/workflows.py:65` | No `limit`/`offset` params; returns all tenant workflows |
| `GET /workflows/executions` | `app/routers/workflows.py:285` | No pagination; returns all executions for a tenant |
| `GET /pipelines` | `app/routers/commercial.py:135` | No pagination on `svc.list_pipelines(tenant_id)` |
| `GET /analytics/reports` | `app/routers/analytics.py:95` | `engine.repository.list_reports(tenant_id)` with no limit |
| `GET /analytics/executions` | `app/routers/analytics.py:218` | `list_executions(report_id=report_id)` with no limit |
| `POST /analytics/cubes/{name}/query` | `app/routers/analytics.py:58` | `cube.query()` returns all rows — no limit parameter |
| `GET /meetings/{opportunity_id}` | `app/routers/meetings.py:49` | `list_by_opportunity` with no limit |
| `GET /emails/{opportunity_id}` | `app/routers/meetings.py:117` | `list_by_opportunity` with no limit |
| `GET /opportunities` (commercial) | `app/routers/commercial.py:93` | `OpportunityQuery(tenant_id=tenant_id)` — no `page_size` |
| `GET /analytics/kpis` | `app/routers/analytics.py:343` | `KPIRegistry.all().values()` — all KPIs returned |

### 2.2 Repository `list_by_tenant` Methods Without Limit

| Repository | File:Line | Signature |
|------------|-----------|-----------|
| `PostgresRecommendationRepository` | `commercial/infrastructure/...py:833` | `list_by_tenant(tenant_id, status=None)` — **no limit** |
| `PostgresDecisionRepository.list_policies` | `commercial/infrastructure/...py:793` | `list_policies(tenant_id)` — **no limit** |
| `PostgresContractRepository` | `commercial/infrastructure/...py:566` | `list_by_tenant(tenant_id, status=None)` — **no limit** |
| `PostgresProposalRepository` | `commercial/infrastructure/...py:473` | `list_by_tenant(tenant_id, status=None)` — **no limit** |
| `PostgresQuoteRepository` | `commercial/infrastructure/...py:381` | `list_by_tenant(tenant_id, status=None)` — **no limit** |

**Impact:** As tenants accumulate 1000+ workflows, reports, quotes, or contracts, these endpoints degrade linearly. At 10k records, response times will exceed 5s.

---

## 3. Backend: N+1 Query Patterns

### 3.1 Workspace Endpoint N+1 🔴 (Critical)

**File:** `app/routers/commercial.py:470-488`

```python
for opp in (opp_result.items if 'opp_result' in dir() else []):
    if opp.status.value != "open":
        continue
    ctx = await ctx_svc.build_context(tenant_id, opp.id, factors=[...])
    eng = RecommendationEngine()
    rec = await eng.evaluate(ctx)
    if rec:
        recs.append({...})
```

This loop executes **two sequential DB operations per open opportunity** — one to build context and one to evaluate. With 100 open opportunities, this is 200+ sequential DB round-trips inside a single request. The `page_size=100` on the upstream `OpportunityQuery` caps at 100, but even 50 open opportunities would trigger 100 DB queries.

**Impact:** Workspace endpoint latency scales as `O(n)` with open opportunity count. At 100 opportunities, expect 2-5s response time from this section alone.

### 3.2 NBA Feed N+1 🔴 (Critical)

**File:** `app/application/dashboard/router.py:163-208`

```python
for opp in opportunities:
    opp_id = str(opp["opp_id"])
    nba = await nba_engine.get_or_compute(opp_id, tenant_id)
```

For each of up to 50 opportunities, `get_or_compute` performs one or more DB queries. Even with caching, the first request triggers 50 sequential operations.

**Impact:** NBA feed initialization degrades linearly with opportunity count. Latency at 50 opportunities is 50x a single `get_or_compute`.

### 3.3 Meeting Brief Endpoint

**File:** `app/routers/meetings.py:73-95`

The `generate_brief` method involves multiple DB round-trips (opportunity lookup, meeting data, company lookup) not batched.

---

## 4. Backend: Synchronous Blocking in Async Code

### 4.1 Benchmark API Sync File I/O 🟡

**File:** `app/routers/benchmarks.py:148-176`

```python
def _load_runs() -> list[dict]:
    for fname in sorted(os.listdir(RESULTS_DIR), reverse=True):
        if fname.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)  # synchronous blocking
```

Both `_load_runs()` and `_load_run_detail()` use blocking `os.listdir`, `open()`, and `json.load()` inside async endpoints. Under concurrent benchmark reads, this blocks the event loop.

### 4.2 Notion Pipeline `time.sleep` 🟡

**File:** `pipeline/notion/__init__.py:35,51`

```python
time.sleep(RATE_LIMIT_DELAY)  # blocking sleep in async context
time.sleep(wait)
```

If called inside an async context, `time.sleep()` blocks the entire event loop.

---

## 5. Backend: Missing / Ineffective Caching

### 5.1 `@cached` Decorator Usage

Only **2 endpoints** use the `@cached` decorator across the entire codebase:

| Endpoint | Key | TTL |
|----------|-----|-----|
| `GET /revenue/dashboard` | `revenue:dashboard` | 60s |
| NBA recommendations | `nba:recommendations` | 120s |

**Missing cache on key endpoints:**
- `GET /workspace` — recomputes everything on every request
- `GET /pipelines/{pipeline_id}/kpis` — KPI computations are cacheable
- `GET /analytics/kpis` — KPI registry never changes per-request
- `GET /opportunities` — list results are cacheable per-tenant
- `GET /forecast` — latest forecast is cacheable
- `GET /{company_id}/360` — company 360 is cacheable per-company

### 5.2 Redis Client Redundancy

**File:** `app/cache.py`, `app/common/redis_client.py`, `main.py:147`

Redis clients are initialized in **three separate places**:
1. `CacheService` in `main.py:77` 
2. `AsyncRedisClient` in `main.py:149`
3. `RateLimitMiddleware` creates its own Redis connection via `redis.asyncio` in `main.py:368`

Each maintains a separate connection pool. This wastes connections and prevents shared connection reuse.

### 5.3 In-Memory Rate Limiter Memory Growth

**File:** `app/common/rate_limit.py:12`

Global `_store: dict[str, list[float]]` grows unboundedly between cleanup intervals (default 300s). Under high traffic, this dictionary accumulates entries for every unique key, consuming memory until cleanup runs.

---

## 6. Backend: Large / Inefficient Response Payloads

### 6.1 Company 360 Response

**File:** `app/modules/company/router.py:230-300`

The `GET /{company_id}/360` endpoint returns a `Company360Response` containing **20+ sub-collections**: related entities, decision makers, contacts, employees, emails, meetings, tasks, opportunities, contracts, invoices, timeline, documents, signals, branches, licenses, enrichment data — all in a single response.

**Impact:** Payload size is 50-200KB for companies with rich data. This slows down serialization and network transmission. Many consumers may only need a subset.

### 6.2 Wide Companies Table Rows

**File:** `reports/benchmark_full.md` (all query plans show `width=3341`)

The `companies` table row width is **3341 bytes** — very wide. Column count includes many text fields (name_ar, name_en, activity_description, etc.) and the row is always fetched completely even when only a few columns are needed.

**Impact:** Full table scan costs are higher per row. Index-only scans are only possible for a narrow set of queries. At 1M companies, a single row read consumes ~3.3MB of buffer pool per 1000 rows.

---

## 7. Backend: Database Query Efficiency

### 7.1 OFFSET Pagination Degradation

**File:** `reports/benchmark_full.md`

At 10k companies:
| Page | Method | p95 | Memory |
|------|--------|-----|--------|
| Page 1 | OFFSET 0 | 3ms | 41kB |
| Page **100** (mid) | OFFSET 2000 | 15ms | **1836kB** |
| Page **250** (deep) | OFFSET 5020 | 16ms | **3800kB disk spill** |

At 100k companies (from benchmark):
| Page | p95 |
|------|-----|
| Page 1 | 94ms |
| Page mid | 16ms |
| Page **deep** | 47ms |

Deep pagination with OFFSET degrades significantly. The `pagination_page_mid` query at 10k rows requires 1836kB of memory and `pagination_page_deep` spills to disk (3800kB). **Keyset pagination is listed as an open issue in the dashboard** but not yet implemented.

### 7.2 Full Table Scan on Partial Text Search

**File:** `reports/benchmark_full.md`

At 100k companies:
- `partial_search_name_ar` (prefix `شركة%`): **p95 1047ms** — Bitmap Heap Scan filtering 100k rows
- `partial_search_name_ar_middle` (`%تجارة%`): **p95 609ms** — same scan pattern
- `partial_search_city`: **p95 313ms**
- `multi_filter_status_region_activity`: **p95 438ms**

All partial search queries use `ILIKE` patterns on `name_ar`, `activity_description`, and `city`. No `pg_trgm` GIN index is in place. The benchmark report mentions adding a trigram index as a known open issue.

### 7.3 No Index on `confidence_score`

**File:** `reports/benchmark_full.md`

Sort by `confidence_score` (asc/desc) at 100k companies: **p95 93-94ms**. The engine performs a full sort of 10k rows (top-N heapsort, 41-44kB). An index on `confidence_score` would reduce this to <5ms.

**Known issue, low priority** per the engineering dashboard.

### 7.4 `search_by_filters` Double Query

**File:** `domains/search/engine/postgres_repo.py:237-260`

`search_by_filters` executes **two separate queries**:
1. `SELECT count(*) FROM companies c WHERE ...` (line 243)
2. `SELECT c.id, c.name_ar, ...` (line 248-257)

This doubles the query time for filtered searches. The `search_raw` method uses `count(*) OVER() AS total_count` in a single query (line 174), which is more efficient. The inconsistency means filtered searches are ~2x slower than unfiltered.

---

## 8. Backend: Middleware Chain Overhead

**File:** `app/main.py:350-379`

The middleware stack on every HTTP request:

```
1. CORSMiddleware
2. GZipMiddleware (minimum_size=1024)
3. RequestIDMiddleware
4. RequestLoggingMiddleware
5. SecurityHeadersMiddleware
6. CsrfEnforcementMiddleware
7. MetricsMiddleware
8. RateLimitMiddleware (Redis check + fallback)
9. AuditMiddleware
10. ApiKeyMiddleware
```

**10 middleware layers** execute on every request. Key concerns:
- **RequestLoggingMiddleware** decodes and parses JWT tokens inline for every request (`middleware.py:231-243`), adding base64 decode + JSON parse overhead
- **CsrfEnforcementMiddleware** parses cookies on every state-changing request, scanning the entire cookie string
- **RateLimitMiddleware** creates a `Request` object if scope is HTTP (redundant parsing)
- **GZipMiddleware** adds CPU overhead for non-compressible responses
- Middleware **order issue**: SecurityHeadersMiddleware runs before GZip, so security headers are added to the ASGI message before the GZip layer can modify it — minor but worth noting

---

## 9. Frontend: Layout & Component Performance

### 9.1 Sidebar Re-Render on Every Route Change

**File:** `frontend/src/app/(dashboard)/layout.tsx:193-217`

The sidebar renders all 23 `NAV_KEYS` items on every render. Since `pathname` changes on every route, the entire `<nav>` element re-renders, causing all 23 `<Link>` components to diff and potentially unmount/remount.

**Impact:** Every page navigation triggers 23 icon component re-evaluations + 23 link component re-evaluations.

### 9.2 Heavy Layout Import

**File:** `frontend/src/app/(dashboard)/layout.tsx:8`

```typescript
import { Building2, Users, DollarSign, Search, Settings, LayoutDashboard, 
         Bell, Menu, Bot, User, Shield, Workflow, MessageSquareText, Activity, 
         HeartHandshake, X, TrendingUp, BarChart3, Brain, CalendarClock, 
         Sparkles, GitGraph, Video, LineChart, Radio, ListChecks } from "lucide-react"
```

**24 named icon imports** from `lucide-react`. While tree-shaking works, the bundle still includes the icon SVG metadata for each. This contributes to layout's JS bundle size. The sidebar also defines `NAV_KEYS` as a const array of objects — each with an icon reference — meaning all 24 icon components are loaded in the layout chunk.

### 9.3 `DashboardContent` Not Memoized

**File:** `frontend/src/app/(dashboard)/layout.tsx:45`

`DashboardContent` is a function component defined in the same module. It is **not wrapped in `React.memo()`**. Since it imports context from `useAppShell()` and `useTranslation()`, any context change causes re-render of the entire layout including sidebar, header, and all children.

---

## 10. Frontend: Missing Image Optimization

### 10.1 Next.js Config is Minimal

**File:** `frontend/next.config.js`

```javascript
const nextConfig = {
  output: "standalone",
  images: {
    domains: ["localhost"],
  },
  async rewrites() { ... },
}
```

**Missing configuration:**
- `remotePatterns` — only `domains: ["localhost"]` is configured. No remote image sources defined.
- `formats` — no `image/formats` config for AVIF/WebP optimization
- `deviceSizes` — default (640, 750, 828, 1080, 1200, 1920, 2048, 3840)
- `imageSizes` — default (16, 32, 48, 64, 96, 128, 256, 384)
- `minimumCacheTTL` — not set (default 60s)
- `loader` — defaults to default Next.js loader
- No custom `imageSizes` or `deviceSizes` tuned to the dashboard layout grid

### 10.2 No `next/image` Usage in Dashboard

Only 3 files reference images across the frontend:
- `next-env.d.ts` — type reference
- `packages/ui/src/avatar.tsx` — uses `AvatarPrimitive.Image`
- `packages/icons/src/index.ts` — generic Image export

The dashboard has no `next/image` usage. If images are loaded, they are likely using `<img>` tags without optimization.

---

## 11. Frontend: Missing Memoization

### 11.1 Widget Cards

**File:** `frontend/src/features/dashboard/widgets/widget-card.tsx`

The `WidgetCardFrame` component is not memoized. Since it receives `title`, `status`, and `onRefresh` as props, any parent re-render re-renders the card frame.

### 11.2 WidgetRegistry Entries

**File:** `frontend/src/features/dashboard/widget-registry.tsx`

Each widget is wrapped with `withErrorBoundary`, but the resulting components (`MissionCenterBounded`, etc.) are defined at module scope with no memoization. The `createRegistry` call recreates the registry on every render since `widgetRegistry` is a `const` array at module scope — but the individual bounded components are created once at module initialization time, so this is less of a concern.

### 11.3 Dashboard Loading State

**File:** `frontend/src/features/dashboard/_layout/dashboard-layout.tsx:11`

```tsx
if (isLoading) return <DashboardLoading />
```

The `DashboardLoading` skeleton replaces the entire dashboard grid content on load. There is no progressive enhancement or partial rendering — it's an all-or-nothing loading pattern.

---

## 12. Frontend: Bundle & Import Efficiency

### 12.1 Dashboard Data Fetching Strategy

**File:** `frontend/src/application/dashboard/useDashboard.ts`

```typescript
export function useDashboard() {
  return useQuery({
    queryKey: dashboardKeys.main(),
    queryFn: fetchDashboard,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}
```

The entire dashboard is fetched as a single query. This means:
- All widgets wait for the single fetch to complete
- Cache invalidation is coarse (30s stale, 60s refetch)
- No partial data rendering
- A single slow sub-query blocks the entire dashboard

### 12.2 Widget-Level Fetching

**File:** `frontend/src/features/dashboard/sdk/create-widget.tsx`

Widgets receive data through `config.useData()` at the SDK level. The `createWidget` factory wraps components in `React.memo`, but the `useData` hook is called at the top of the component, meaning **every widget re-renders when any data changes** because `refetch` reference is captured by `useCallback` with `refetch` as a dependency.

---

## 13. Dashboard Performance

### 13.1 NBA Feed Inefficiencies

**File:** `app/application/dashboard/router.py:113-227`

The NBA feed endpoint:
1. Fetches up to **100 decisions** from `decision_engine.get_decisions()` synchronously (no pagination)
2. Fetches up to **50 opportunities** from the database
3. For each opportunity, calls `nba_engine.get_or_compute()` — **N+1 pattern**
4. **Sorts all items in Python** (not in DB)
5. **Applies pagination in Python** after sorting all results

This means the endpoint does the maximum work before filtering down. It's essentially `LIMIT 50` applied as Python slice rather than as SQL `LIMIT`.

### 13.2 Dashboard Aggregator Overhead

**File:** `app/application/dashboard/router.py:55-57`

```python
aggregator = DashboardAggregator(db, tenant_id)
handler = DashboardQueryHandler(aggregator)
dto = await handler.handle(query)
```

The `DashboardAggregator` builds the entire dashboard DTO synchronously in Python, aggregating data from multiple services. There is no partial loading or streaming support.

### 13.3 Cache Coverage Gap

The dashboard endpoint has caching (`cache.set(cache_key, ...)`), but the cache key includes `query.fields`, which causes cache fragmentation. The NBA feed endpoint does **not** cache results (`cached=False` hardcoded).

---

## 14. Prioritized Recommendation Summary

### 🔴 Critical (Fix Immediately)

| # | Issue | File(s) | Impact | Effort | Fix |
|---|-------|---------|--------|--------|-----|
| P1 | Workspace N+1 loop per opportunity | `routers/commercial.py:470-488` | 200+ DB queries per request | Medium | Batch context build + evaluate; cache per-opportunity context |
| P2 | NBA Feed N+1 per opportunity | `dashboard/router.py:163-208` | 50+ DB queries per NBA feed | Medium | Batch fetch NBA recommendations; use SQL JOIN |
| P3 | Missing pagination on 12+ endpoints | Multiple routers | Unbounded query growth | Low-Medium | Add `limit`/`offset` to all list endpoints |

### 🟡 High Priority (This Sprint)

| # | Issue | File(s) | Impact | Effort | Fix |
|---|-------|---------|--------|--------|-----|
| H1 | 6 `list_by_tenant()` methods without limit | `postgres_repositories.py` | Unbounded queries by tenant | Low | Add `LIMIT` clause with default |
| H2 | OFFSET-based deep pagination | Multiple repos | 3800kB disk spill at 10k rows | Medium | Implement keyset/cursor pagination |
| H3 | `search_by_filters` double query | `domains/search/engine/postgres_repo.py` | 2x query time for filtered search | Low | Use window function `count(*) OVER()` |
| H4 | 3 separate Redis client pools | `main.py`, `cache.py`, `redis_client.py` | Wasted connections | Low | Consolidate to single singleton |
| H5 | Sync file I/O in async benchmark endpoints | `routers/benchmarks.py` | Event loop blocking | Low | Use `aiofiles` |
| H6 | Missing image optimization config | `next.config.js` | Unoptimized images | Low | Add `remotePatterns`, `formats` |

### 🟢 Medium Priority (Next Sprint)

| # | Issue | File(s) | Effort | Fix |
|---|-------|---------|--------|-----|
| M1 | Missing `@cached` on 6+ endpoints | `analytics`, `workspace`, `forecast` | Low | Add caching decorator |
| M2 | Sidebar re-render on route change | `layout.tsx` | Low | Memoize nav items; use `React.memo` |
| M3 | Wide `companies` table row (3341B) | DB schema | Medium | Select only needed columns in queries |
| M4 | JWT decode in logging middleware | `middleware.py:231-243` | Low | Extract user_id from request state, not JWT |
| M5 | Dashboard all-at-once fetch | `useDashboard.ts` | Medium | Implement widget-level data fetching |
| M6 | Layout re-render from context changes | `layout.tsx`, `dashboard-provider.tsx` | Low | Memoize `DashboardContent` |
| M7 | NBA feed Python-side sorting/pagination | `dashboard/router.py:212-217` | Low | Push LIMIT/OFFSET to SQL |

### 🔵 Low Priority (Backlog)

| # | Issue | File(s) | Effort |
|---|-------|---------|--------|
| L1 | No `pg_trgm` index on partial text fields | DB schema | Low |
| L2 | No index on `confidence_score` | DB schema | Low |
| L3 | In-memory rate limiter memory growth | `rate_limit.py` | Low |
| L4 | 10 middleware layer overhead | `main.py` | Medium |
| L5 | `DashboardContent` not memoized | `layout.tsx` | Low |
| L6 | GZip order relative to SecurityHeaders | `main.py` | Low |
| L7 | 24-icon import in layout | `layout.tsx` | Low |

---

## 15. Benchmark Correlation

### 15.1 Existing Benchmark Results (100k Companies)

Reference: `reports/benchmark_full.md` and `reports/benchmark_100.md`

| Category | p95 at 100 | p95 at 1k | p95 at 10k | p95 at 100k | Degradation Factor |
|----------|-----------|-----------|------------|-------------|-------------------|
| Exact Search | 0ms | 0ms | 0ms | 63ms | ~63x (10k→100k) |
| Partial Search | 0ms | 15ms | 47ms | **1047ms** | ~70x (10k→100k) |
| Filter | 0ms | 0ms | 31ms | **438ms** | ~14x |
| Sort | 0ms | 0ms | 16ms | **234ms** | ~15x |
| Pagination | 0ms | 0ms | 16ms | 109ms | ~7x |
| Count | 0ms | 0ms | 0ms | 16ms | ~16x |

### 15.2 Predicted Bottlenecks at Scale

| Dataset Size | Expected Latency (Worst p95) | Primary Bottleneck |
|-------------|------------------------------|-------------------|
| 100k | 1047ms (partial search) | Missing trigram index |
| 500k | ~5-8s (partial search) | Full table scan on ILIKE |
| 1M | ~10-15s | N+1 patterns + missing pagination |
| 5M | Unpredictable | OFFSET pagination + N+1 |

### 15.3 Test Environment Limitations

Per the engineering dashboard and `docs/FINAL_PERFORMANCE_REPORT.md`:
- **Docker Desktop adds ~5s overhead per request** — not representative
- **Middleware chain buffering bug blocks HTTP load testing** — only DB-level benchmarks are reliable
- **Redis not deployed** — in-memory rate limiter is the only active limiter
- **Single node PostgreSQL** — no read replicas

---

*Audit generated by automated pattern scan + manual code review. Recommendations should be reviewed by architecture team before implementation.*
