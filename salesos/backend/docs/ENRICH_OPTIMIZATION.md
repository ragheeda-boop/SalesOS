# POST /enrich — Optimization Report

> Dashboard: p50=2.5s, p99=15s | Budget: 5s | Target: p50<1s, p99<3s

---

## 1. Current Enrichment Pipeline

### Pipeline Stages

| # | Stage | Location | Est. Time | Type | Notes |
|---|-------|----------|-----------|------|-------|
| 1 | DB query (companies table) | `enrich/__init__.py:_call_enrichment_source` | ~20ms | SQL | Fast, negligible |
| 2 | Balady scraper (`fetch_all`) | `enrich/__init__.py` → `scrapers/balady.py` | 500ms–5s | External API | Sequential, no timeout guard |
| 3 | FeatureStore `get_features` | `enrich/__init__.py` → `feature_store/__init__.py` | 2–8s | DB + Compute | 7 feature computers run sequentially |
| 4 | Fallback simulated data | `enrich/__init__.py` | ~1ms | In-memory | Rarely hit |
| **Total** | | | **2.5–15s** | | |

### Root Causes of Latency

1. **Sequential pipeline stages** — Stages 1, 2, 3 run one after another despite being independent
2. **FeatureStore computes 7 features sequentially** — Each calls separate DB queries and runs one by one
3. **No caching** — Every enrichment call re-queries all sources; no in-memory or Redis cache
4. **No timeouts on external scrapers** — Scrapers have no deadline; a single hung API call blocks the entire pipeline
5. **No circuit breaker** — Failing external sources keep getting called on every request, wasting time
6. **BaladyScraper HTTP client timeout = 30s** — Very long default; contributes to p99 spikes
7. **Celery task retry delay = 120s** — Large delay before retry, poor UX

---

## 2. Optimization Recommendations

| # | Optimization | Est. Improvement | Effort | Complexity |
|---|-------------|-----------------|--------|------------|
| O1 | **Parallelize stages 1/2/3** (asyncio.gather) | 50–70% reduction | Low | Low |
| O2 | **In-memory cache with 24h TTL** | 90%+ hit rate → ~1ms | Low | Low |
| O3 | **Parallelize feature computers** (7× sequential → 1× parallel) | 60–80% reduction | Low | Low |
| O4 | **Add 10s timeout on scrapers & FS** | Eliminates hung-API p99 spikes | Low | Low |
| O5 | **Circuit breaker for external sources** | Skips failing sources after 3 failures | Low | Low |
| O6 | **Reduce BaseScraper HTTP timeout 30s→15s** | Faster failure detection | Trivial | None |
| O7 | **Parallelize Balady + Taqeem scrapers** (currently sequential) | ~50% scraper time reduction | Low | Low |
| O8 | **Parallelize graph sync + embedding in process_entity** | ~40% reduction | Low | Low |
| O9 | **Add Redis cache layer (future)** | Shared cache across workers | Medium | Medium |

### Estimated Cumulative Improvement

| Metric | Before | After (estimated) |
|--------|--------|-------------------|
| p50 | 2.5s | 200–500ms |
| p95 | 8s | 1–2s |
| p99 | 15s | 2–3s |
| Failure rate | Unknown | Reduced 60%+ |

---

## 3. Parallel Processing Opportunities

### Applied: `EnrichmentService._call_enrichment_source`

```
Before:                    After:
  DB query ──► ──►          DB query ──┐
  Scraper  ──►    ──►   ──►asyncio.gather──► merge results
  FS query ──►      ──►   FS query  ──┘
                            Scraper   ──┘
```

### Applied: `FeatureStore.get_features` and `recompute`

```
Before:                    After:
  Feature1 ──►              Feature1 ──┐
  Feature2   ──►           Feature2 ──┤
  Feature3     ──►   ──►  Feature3 ──┤── asyncio.gather
  ...                       ...      ──┘
  Feature7
```

### Applied: Celery `enrich_company` task

```
Before:                    After:
  scrape ──►               scrape ──┐
  features  ──►     ──►   asyncio.gather──► done
                            features ──┘
```

### Applied: `process_entity` (graph sync + embedding were sequential)

```
Before:                    After:
  graph sync ──►           graph sync ──┐
  embedding   ──►   ──►   asyncio.gather──► done
                            embedding   ──┘
```

---

## 4. Caching Strategy

### Tier 1: In-memory Cache (implemented)

| Component | Key | Value | TTL | Eviction |
|-----------|-----|-------|-----|----------|
| `EnrichmentService` | `company_id` | `dict[str, Any]` (enriched fields) | 24h | Manual `clear_cache(id)` |

### Tier 2: FeatureStore DB Cache (pre-existing)

- Already stores computed features in `company_features` table
- Avoids recompute on `get_features` if fresh row exists
- `recompute()` always bypasses cache (for explicit refresh)

### Future: Redis Cache

- Use Redis for shared cache across Celery workers
- Key: `enrich:{tenant_id}:{company_id}`
- TTL: 24h with active expiry
- Invalidate on `company.updated` event

---

## 5. Changes Applied

### File: `backend/intelligence/enrichment/__init__.py`

1. **In-memory cache** — `_cache: dict[str, tuple[float, dict]]` with 24h TTL check in `enrich_company()`
2. **Circuit breaker** — `_circuit_breakers: dict[str, dict]` tracks failures per source; trips after 3 failures, resets after 60s
3. **Parallel stages** — `_call_enrichment_source` now runs DB query, scrapers, FeatureStore via `asyncio.gather`
4. **10s timeout** — Each external call wrapped in `asyncio.timeout(10)`
5. **Parallel scrapers** — Balady scraper runs concurrently (multiple scrapers via `asyncio.gather`)
6. **`batch_enrich`** — Changed from sequential `asyncio.run` loop to `asyncio.gather`
7. **`clear_cache()`** — Public method to invalidate cache per company or globally
8. **`circuit_breaker_status()`** — Exposes breaker state for monitoring
9. **Stats** — Extended with `cache_size` and `circuit_breakers`

### File: `backend/app/tasks.py`

1. **Parallel enrich** — `enrich_company` task now calls `_parallel_enrich()` which runs scraping + feature recompute via `asyncio.gather`
2. **Parallel scrapers** — `_do_scrape` runs Balady + Taqeem concurrently with 10s timeout per scraper
3. **Promoted `_do_recompute`** — Async function at module level so `_parallel_enrich` can use it directly

### File: `backend/runtime/feature_store/__init__.py`

1. **Parallel feature computation** — `get_features()` and `recompute()` now run all feature computers via `asyncio.gather`

### File: `backend/runtime/data_fabric_runtime/scrapers/__init__.py`

1. **Reduced HTTP timeout** — `AsyncClient` timeout reduced from 30s to 15s

---

## 6. Monitoring Recommendations

| Metric | Where | Action |
|--------|-------|--------|
| `enrich.cache_hit_rate` | Stats endpoint | >90% expected after warmup |
| `enrich.circuit_breaker_open` | `circuit_breaker_status()` | Alert if any breaker stays open >5min |
| `enrich.stage_duration` | Per-stage timing | Track p50/p99 per stage |
| `feature_store.compute_time` | FeatureStore metrics | Alert if >2s avg |
| `scraper.timeout_count` | scraper errors log | Alert if >5/min |
