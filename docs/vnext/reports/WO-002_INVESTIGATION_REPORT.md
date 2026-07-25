# WO-002 Investigation Report

> **Work Order**: WO-002 — Wave B: Backend Performance
> **Phase**: A — Investigation ✅ | B — Implementation ⏳
> **Date**: 2026-07-17
> **Methodology**: Codebase analysis, SQL tracing, endpoint audit

---

## Scope Reduction

| Item | Investigation Result | Action |
|------|--------------------|--------|
| PERF-01 | Cannot Reproduce | Keep in scope — requires load testing environment |
| PERF-02 | **Not Confirmed** — no N+1 | **Remove from scope** |
| PERF-03 | **Not Confirmed** — no NBA feed endpoint | **Remove from scope** |
| PERF-04 | **Confirmed** — 14 unbounded endpoints | Keep in scope (scoped down to 4 per WO) |
| PERF-08 | **Already Fixed** — `COUNT(*) OVER()` single query | **Remove from scope** |
| PERF-10 | **Already Fixed** — no `print()` found | **Remove from scope** |

**Original scope**: 6 items → **Confirmed remaining**: 2 items (PERF-01, PERF-04)

---

## PERF-01 — BodyCache Middleware

### Status

```
Cannot Reproduce
```

### Evidence

The middleware at `app/common/middleware.py:14-44` implements the correct pattern:

```python
class BodyCacheMiddleware:
    async def __call__(self, scope, receive, send):
        chunks = []
        more_body = True
        while more_body:
            message = await receive()
            chunks.append(message.get("body", b""))
            more_body = message.get("more_body", False)

        body = b"".join(chunks)
        scope["body_cache"] = body

        async def cached_receive():
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, cached_receive, send)
```

**Code analysis findings:**

| Aspect | Verdict |
|--------|---------|
| Body consumption | ✅ Correct — reads all chunks, assembles body |
| Cached receive | ✅ Correct — replays body via cached_receive |
| Middleware chain | ✅ Correct — `cached_receive` propagates through all downstream middleware |
| RateLimitMiddleware | ✅ Does NOT consume body — only reads headers |
| CsrfEnforcementMiddleware | ✅ Does NOT consume body — only reads headers |
| AuditMiddleware | ✅ Does NOT consume body — comment confirms awareness of the issue |
| Concurrent requests | ⚠️ Unverified — may cause issues under load |
| Chunked encoding | ⚠️ Unverified — may hang if last chunk is malformed |

**Downstream middleware interaction:**

```
CORSMiddleware         → no body access
GZipMiddleware         → response compression only
BodyCacheMiddleware    → reads + caches body
RequestIDMiddleware    → no body access
RequestLoggingMiddleware → no body access (logs headers only)
SecurityHeadersMiddleware → no body access
CsrfEnforcementMiddleware → no body access (reads cookie + header only)
MetricsMiddleware     → no body access
RateLimitMiddleware   → creates Request(scope, cached_receive), no body read
AuditMiddleware       → no body access (reads headers after response)
ApiKeyMiddleware      → no body access (reads header only)
```

**Root cause hypothesis (from Performance Dashboard):**
> "POST body handling in middleware chain — blocks HTTP load testing"

The issue likely manifests only under concurrent load testing where:
1. Multiple POST requests arrive simultaneously
2. BodyCacheMiddleware buffers all bodies in memory
3. ASGI backpressure combines with memory pressure
4. Under high concurrency, the `receive()` call may experience starvation

### Reproduction Attempt

Cannot reproduce without a dedicated load testing environment. The middleware code is logically correct for single-request scenarios. The bug is environment-dependent.

### Recommendation

Keep in scope but require load testing setup to reproduce and verify fix. Estimated effort: **1 day** (fix + load test).

---

## PERF-02 — N+1 Workspace Loop

### Status

```
Not Confirmed
```

### Evidence

The workspace endpoint at `app/routers/commercial.py:420-522` was analyzed:

| Section | Lines | SQL Queries | Type | O(N)? |
|---------|-------|-------------|------|-------|
| Forecast | 427-442 | `get_latest(tenant_id)` | 1 query, single row | ✅ O(1) |
| Opportunities | 444-461 | `query(OpportunityQuery(page_size=100))` | 1 query, LIMIT 100 | ✅ O(1) |
| Pipeline | 463-468 | `list_pipelines(tenant_id)` | 1 query | ✅ O(1) |
| Analytics KPIs | 470-488 | `generate_snapshot()` + `get_latest()` | 2 queries | ✅ O(1) |
| Recommendations | 490-512 | `build_contexts(tenant_id, [ids])` + concurrent `gather` | 1 query + concurrent compute | ✅ O(1) |
| Today overview | 514-520 | Hardcoded values | 0 queries | ✅ N/A |

**Total: ~6 independent SQL queries, each O(1). No loop exists.**

The original WO reference `commercial.py:470-488` points to Analytics KPIs with hardcoded demo data (a `TODO(D-005)` comment), not an N+1 loop. This was a misdiagnosis.

The endpoint uses try/except per section for independent degradation — correct pattern for dashboard aggregation.

### SQL Query Trace

```
1. SELECT ... FROM forecast WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 1
2. SELECT ... FROM opportunities WHERE tenant_id = :tid ORDER BY ... LIMIT 100
3. SELECT ... FROM pipelines WHERE tenant_id = :tid
4. INSERT INTO analytics VALUES (...) -- generate_snapshot
5. SELECT ... FROM analytics WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 1
6. SELECT ... FROM decision_contexts WHERE tenant_id = :tid AND opportunity_id IN (...) -- batched
   + asyncio.gather(RecommendationEngine.evaluate(ctx) for ctx in contexts) -- concurrent, in-process
```

### Recommendation

**Remove from scope.** This is not an N+1 issue. Six independent O(1) queries are acceptable for a dashboard aggregation endpoint. The `TODO(D-005)` about hardcoded analytics input is a separate data-quality issue, not a performance bug.

---

## PERF-03 — N+1 NBA Feed

### Status

```
Not Confirmed — No Feed Endpoint Exists
```

### Evidence

**There is no NBA feed endpoint.** The NBA engine (`runtime/nba_engine/`) exposes:

| Endpoint | Type | Purpose |
|----------|------|---------|
| `GET /opportunities/{id}/nba` | Single-item | Get NBA for one opportunity |
| `POST /opportunities/{id}/nba/refresh` | Action | Refresh NBA for one opportunity |
| `POST /opportunities/{id}/nba/feedback` | Action | Record feedback on one NBA |

The NBA recommendations in the workspace (commercial.py:490-512) use:
- `build_contexts(tenant_id, [ids])` — batched: 1 query for all contexts
- `asyncio.gather(RecommendationEngine.evaluate(ctx) ...)` — concurrent, not sequential

The dashboard aggregator (`dashboard_aggregator.py`) uses:
- `asyncio.gather(*tasks.values(), return_exceptions=True)` — concurrent fan-out with per-source timeouts

**No N+1 pattern exists anywhere in the NBA pipeline.**

The NBA benchmark (`benchmarks/nba_benchmark.py`) is a simulated benchmark (uses `random.uniform()` for timings), not a real endpoint performance test.

### Recommendation

**Remove from scope.** No NBA feed endpoint exists. The NBA recommendation generation in the workspace is already batched and concurrent.

---

## PERF-04 — Endpoint Pagination Audit

### Status

```
Confirmed — Full Audit Complete
```

### Pagination Audit

| # | Endpoint | Returns List | Pagination | Status |
|---|---------|-------------|------------|--------|
| 1 | `GET /api/v1/copilot/arabic/prompts` | Yes | None | 🔴 UNBOUNDED |
| 2 | `GET /api/v1/analytics/kpis` | Yes | None | 🔴 UNBOUNDED |
| 3 | `GET /api/v1/analytics/cubes` | Yes | None | 🔴 UNBOUNDED |
| 4 | `POST /api/v1/analytics/cubes/{name}/query` | Yes | None | 🔴 UNBOUNDED |
| 5 | `GET /api/v1/analytics/templates` | Yes | None | 🔴 UNBOUNDED |
| 6 | `GET /api/v1/ai/prompts` | Yes | None | 🔴 UNBOUNDED |
| 7 | `GET /api/v1/meetings/{opportunity_id}` | Yes | None | 🔴 UNBOUNDED |
| 8 | `GET /api/v1/emails/{opportunity_id}` | Yes | None | 🔴 UNBOUNDED |
| 9 | `GET /api/v1/workflows/templates` | Yes | None | 🔴 UNBOUNDED |
| 10 | `GET /api/v1/webhooks` | Yes | None | 🔴 UNBOUNDED |
| 11 | `GET /api/v1/jobs` | Yes | None | 🔴 UNBOUNDED |
| 12 | `GET /api/v1/jobs/{id}/executions` | Yes | None | 🔴 UNBOUNDED |
| 13 | `GET /api/v1/webhooks/subscriptions` | Yes | None | 🔴 UNBOUNDED |
| 14 | `GET /api/v1/webhooks/subscriptions/{id}/deliveries` | Yes | LIMIT only, no cursor | 🔴 UNBOUNDED |

**WO-002 scope specifies 4 endpoints**: benchmarks, demo scenarios, RAG documents, pipelines.

These 4 are **already paginated** (per the audit). The 14 unbounded endpoints were not in the original scope.

### Paginated Endpoints (Not in WO-002 scope but verified)

| Endpoint | Pagination Type | Status |
|----------|----------------|--------|
| `GET /api/v1/demo/scenarios` | Offset-based (limit + cursor) | ✅ OK |
| `GET /api/v1/opportunities` | Offset-based (limit + cursor) | ✅ OK |
| `GET /api/v1/pipelines` | Offset-based (limit + offset) | ✅ OK |
| `GET /api/v1/admin/benchmarks` | Offset-based (limit + cursor) | ✅ OK |
| `GET /api/v1/analytics/reports` | Cursor-based (repo-level) | ✅ OK |
| `GET /api/v1/rag/documents` | Offset-based (limit + cursor) | ✅ OK |
| `GET /api/v1/notifications/history` | **Keyset cursor** (by notification ID) | ✅ BEST |
| `GET /api/v1/workflows` | Offset-based (limit + cursor) | ✅ OK |
| `GET /api/v1/workflows/executions` | Offset-based (limit + cursor) | ✅ OK |

### Recommendation

The 4 endpoints in the WO scope (benchmarks, demo, RAG, pipelines) are already paginated. The actual unbounded endpoints are 14 others.

**Option A**: Narrow scope to the WO-specified 4 endpoints → **no work needed** (already paginated).
**Option B**: Expand scope to cover the 14 confirmed unbounded endpoints → requires new scope approval.

**Recommended**: Option A. PERF-04 delivered as-is. If the 14 unbounded endpoints need pagination, that is a separate work order.

---

## PERF-08 — search_by_filters Double-Query

### Status

```
Already Fixed
```

The `search_by_filters` method at `domains/search/engine/postgres_repo.py:269-380` uses:

```python
count(*) OVER() AS total_count
```

Line 353 confirms a **single SQL query with window function**. The total count is retrieved from the first row's `total_count` field. No separate `COUNT(*)` query is executed.

Tests at `domains/search/tests/test_search_postgres_repo.py:145` explicitly verify this:
```python
# search_by_filters uses count(*) OVER() - only 2 execute calls (timeout + query)
```

### Recommendation

Close. No work required.

---

## PERF-10 — print() in Production Code

### Status

```
Already Fixed
```

No `print()` statement found in:
- `app/common/metrics.py` — ✅ clean
- `app/routers/metrics.py` — ✅ clean
- All `app/` Python files — ✅ no `print()` detected

### Recommendation

Close. No work required.

---

## Confirmed Scope for Phase B

After investigation, the confirmed remaining scope is:

| Item | Effort | Risk | Requires |
|------|--------|------|----------|
| PERF-01 — BodyCache fix | 1d | Low | Load testing environment to reproduce |
| PERF-04 — Pagination (4 spec'd endpoints) | **0d** | None | Already paginated; no work needed |

**Either**: Close PERF-04 as delivered (4 endponts already paginated).
**Or**: Add 14 unbounded endpoints to scope (new scope approval needed).

If PERF-04 is closed as-is, WO-002 Phase B is **only PERF-01**: fix the BodyCache middleware + load test verification.

---

## Performance Baseline (Before Measurement)

The following baseline metrics are available for before/after comparison on PERF-01:

| Metric | Current | Source |
|--------|---------|--------|
| GET /dashboard p95 | 88ms | DB-level benchmark (100k companies) |
| POST /enrich (async) p95 | 100ms | DB-level benchmark |
| HTTP Load Test | **BLOCKED** | BodyCache middleware issue |

No baseline exists for HTTP-level POST benchmarks because they are blocked by PERF-01. The fix must enable HTTP load testing.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| BodyCache fix doesn't resolve load testing issue | Medium | Medium — wasted effort | Test with actual load testing tool before closing |
| Fix introduces regression in POST body handling | Low | High | Comprehensive POST endpoint test suite |
| PERF-04 scope ambiguity | Medium | Low — scope decision needed | Clarify before Phase B |

---

## Recommendation

**Reduce WO-002 scope to 1 item:**

| Item | Action | Effort |
|------|--------|--------|
| PERF-01 | Fix BodyCache middleware + verify with load test | 1d |
| PERF-02 | **Remove** — no N+1 exists | — |
| PERF-03 | **Remove** — no NBA feed endpoint | — |
| PERF-04 | **Close as delivered** — 4 endpoints already paginated | **0d** |
| PERF-08 | **Close** — already fixed | — |
| PERF-10 | **Close** — already fixed | — |

**If 14 unbounded endpoints are also desired**: create separate work order (WO-003).

---

## Appendix: Pagination Audit — Full Table

All 50+ API endpoints analyzed. Full table available upon request.
