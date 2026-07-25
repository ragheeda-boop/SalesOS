# Performance Review — Wave C: AI Foundation (WO-003)

> **Reviewer**: performance-reviewer
> **Date**: 2026-07-16
> **Status**: ✅ Gate Passed — 4 minor findings, 0 blockers
> **Base Report**: `SPRINT0_WAVE_C_REPORT.md`

---

## 1. Cost Tracker — Accuracy of Token/Cost Estimation

**Verdict: ✅ Accurate — with 1 maintenance risk**

### Strengths
- Pricing covers all 10 deployed models (GPT-4o-mini, GPT-4o, Claude-3.5-Sonnet, Claude-3.5-Haiku, Gemini-1.5-Pro/Flash, text-embedding-3-large/small) at correct per-1K-token rates (`cost_tracker.py:15-24`, `base.py:65-76`)
- `estimate_cost()` formula matches provider billing: `(prompt_tokens/1000)*input_rate + (completion_tokens/1000)*output_rate`, micro-dollar precision
- `CostRecord` captures all required fields per G-C.5 (model, prompt/completion tokens, cost, tenant_id, latency_ms)
- `DEFAULT_COST` fallback (input $0.001/k, output $0.002/k) prevents silent zero-cost for unknown models
- `ON CONFLICT (id) DO NOTHING` prevents double-counting on retry persistence
- Budget enforcement per tenant with `is_budget_exceeded()` gate (`cost_tracker.py:138-145`)

### Finding 1 (Minor): Duplicated pricing dictionary
`MODEL_COST_PER_1K_TOKENS` is declared in `base.py:65-76` AND mutated in `cost_tracker.py:15-24` via `MODEL_COST_PER_1K_TOKENS.update()`. The `update()` mutates the shared dict at import time, so both files see the same final set. However, any future price update must be checked in both locations or the `update()` must be kept in sync. Recommend eliminating the copy and keeping pricing solely in `base.py`.

### Finding 2 (Minor): Cost tracker not wired into providers
Both `OpenAIProvider.chat()` and `AnthropicProvider.chat()` compute `cost` via `estimate_cost()` and attach it to `ChatResponse.cost`, but **neither provider calls `CostTracker.track()`**. The cost tracker is a library the application-layer must invoke — there is no automatic per-call persistence unless the caller explicitly passes `persist=True`. Streaming paths (`chat_stream()`) have **no cost tracking at all** — the generators yield `StreamEvent` without cost metadata.

| Path | Cost Computed | Cost Persisted |
|------|:-:|:-:|
| OpenAI `chat()` | ✅ in `ChatResponse.cost` | ❌ caller must `.track()` |
| Anthropic `chat()` | ✅ in `ChatResponse.cost` | ❌ caller must `.track()` |
| OpenAI `chat_stream()` | ❌ not computed | ❌ not tracked |
| Anthropic `chat_stream()` | ❌ not computed | ❌ not tracked |

---

## 2. Streaming — Truly Streaming or Batching Chunks?

**Verdict: ✅ True token-by-token streaming — no buffering**

### Evidence
- **OpenAI**: Uses `stream=True` with `stream_options={"include_usage": True}`, iterates `async for chunk in stream`, yields each `delta.content` immediately as `StreamEvent(type="chunk")` — token-level granularity (`openai_provider.py:89-100`)
- **Anthropic**: Uses `async with client.messages.stream()`, iterates `async for text in stream.text_stream` — the SDK's `text_stream` yields text as it arrives character-by-character (`anthropic_provider.py:116-118`)
- **SSE wrapper** (`sse.py:39-41`): `stream_to_sse()` is a pure pass-through `async generator` — no intermediate buffering, no batch accumulation. Each `StreamEvent` is immediately formatted as `data: {json}\n\n` and yielded.
- Both `stream_to_sse()` and `stream_to_async_gen()` preserve all four event types (chunk, done, error, tool_call).

### Finding 3 (Minor): No latency/usage metrics on stream `done` event
The `done` event carries `usage` dict (token counts from the provider), but **no `latency_ms` field**. Non-streaming `chat()` measures elapsed time via `time.monotonic()` and reports it in `ChatResponse.latency_ms`. Streaming consumers cannot determine how long the full generation took. This is acceptable for chat/copilot (which is the target use case) but would be a gap for billing/auditing.

---

## 3. Provider Switching — Latency Impact

**Verdict: ✅ Selection latency ~0ms; failover latency = 1 HTTP round-trip**

### Analysis
- **Route selection** (`router.py:route()`): Pure local computation — word counting, dict lookups, list comprehensions. No I/O. Latency: **< 1ms**.
- **Provider instantiation** (`factory.py:create_from_settings()`): Dict lookup + lambda execution + constructor. `OpenAIProvider.__init__` creates `AsyncOpenAI(client)` synchronously (no network). `AnthropicProvider.__init__` stores config only — actual client creation is lazy in `_get_client()`. Latency: **< 5ms**.
- **Failover chain** (`factory.py:chat_with_failover()`): Sequential — creates a new provider instance, calls `provider.chat()`, and on exception moves to the next. The dominant cost is the failed HTTP call to the primary provider (typically seconds on timeout). Factory overhead is negligible.
- **Router tiers** map complexity to providers: SIMPLE → ollama, MODERATE → anthropic (haiku), COMPLEX → openai (gpt-4o). The tier dict lookup is O(1).

### Recommendation
Not needed for current scope. If failover latency becomes critical, a future optimization would be to use HTTP timeouts (e.g., `httpx.Timeout(5.0)`) per provider call rather than relying on default SDK timeouts.

---

## 4. Memory — PostgreSQL Query Performance

**Verdict: ✅ Well-indexed — 1 query gap (cleanup)**

### Index Coverage

| Index | Columns | Covers |
|-------|---------|--------|
| `ix_episodic_memory_agent` | `(agent_id, timestamp DESC)` | `query(agent_id=...)` — most common pattern |
| `ix_episodic_memory_scope` | `(scope, timestamp DESC)` | `query(scope=...)` |
| `ix_episodic_memory_session` | `(session_id, timestamp DESC)` | `query(session_id=...)` |
| `ix_episodic_memory_conversation` | `(conversation_id, timestamp DESC)` | `query(conversation_id=...)` |
| PK | `id` | `get(id)`, `delete(id)`, `store()` ON CONFLICT |

All composite indexes have `timestamp DESC` as the second column, matching the `ORDER BY timestamp DESC` in every query — enabling **backward index scans** with no separate sort step.

### Finding 4 (Minor): `cleanup_expired()` has no index support
The query (`postgres_store.py:121-126`) is:
```sql
DELETE FROM episodic_memory
WHERE ttl_seconds IS NOT NULL
  AND (timestamp + make_interval(secs => ttl_seconds)) < NOW()
```
This predicate `(timestamp + interval) < NOW()` with `ttl_seconds IS NOT NULL` cannot use any existing B-tree index efficiently — it requires a full sequential scan. On the `llm_cost_tracking` table (append-only, no TTL) this doesn't apply, but on `episodic_memory` with TTL-based expiry, every cleanup triggers a seq scan.

**Recommendation**: Add a partial index:
```sql
CREATE INDEX CONCURRENTLY ix_episodic_memory_ttl
  ON episodic_memory ((timestamp + make_interval(secs => ttl_seconds)))
  WHERE ttl_seconds IS NOT NULL;
```

### Additional Observations
- `metadata` column is JSONB — no GIN index needed currently (no metadata-key queries in code), but worth noting for future semantic memory queries
- No `confidence_score` column or ordering — fine for episodic memory but would matter for semantic retrieval
- `content` is TEXT with no full-text search index (no `tsvector` GIN) — acceptable since memory query is filter-based, not similarity-based

---

## 5. Tests — ≥ 30% AI Coverage

**Verdict: ✅ Confirmed — 40% coverage (exceeds 30% target)**

| Metric | Value |
|--------|-------|
| New test files | 5 |
| New tests | 64 |
| Module coverage (intelligence/) | 40% (target ≥ 30%) |
| All existing tests | 1407 passed, 0 failures |
| Real API calls in tests | 0 — all mocked per constraint |
| Test execution time | 3.35s (intelligence) / 48.22s (full suite) |

### Coverage by Area

| Area | Tests | Quality |
|------|-------|---------|
| Postgres memory | 13 | CRUD + query + cleanup + edge cases |
| SSE streaming | 7 | Format + stream wrapping + error |
| Cost tracker | 10 | Tracking + persistence + budgets + summary |
| Provider switching | 13 | Factory + register + all providers + router + failover |
| Prompt registry v2 | 15 | version_hash + evaluation_criteria + A/B testing |

**All tests are deterministic** (no network calls, no random values) and fast (mean < 30ms each).

---

## Summary

| Dimension | Verdict | Findings |
|-----------|---------|----------|
| Cost estimation accuracy | ✅ Accurate | Finding 1: duplicated pricing dict (minor) |
| Cost tracking integration | ⚠️ Partial | Finding 2: no automatic provider→tracker wiring; streaming has no cost tracking |
| Streaming quality | ✅ True streaming | Finding 3: no latency_ms on stream done event (minor) |
| Provider switching latency | ✅ ~0ms selection | No findings — failover cost is expected HTTP round-trip |
| Memory indexes | ✅ Well-indexed | Finding 4: cleanup_expired() seq scan (minor) |
| AI test coverage | ✅ 40% (target 30%) | No findings |

### Findings Summary

| ID | Severity | Area | Description |
|----|----------|------|-------------|
| F1 | Minor | Cost Tracker | Pricing dict duplicated in `base.py` and `cost_tracker.py` |
| F2 | Minor | Cost Tracker | Cost tracking not wired into providers — streaming has none |
| F3 | Minor | Streaming | No latency_ms on stream `done` event |
| F4 | Minor | Memory | `cleanup_expired()` full seq scan — missing partial TTL index |

### Overall Gate

**G-C.4 (Streaming)**: ✅ Passed — token-by-token, not batched
**G-C.5 (Cost Tracker)**: ✅ Passed — records all required fields per criteria
**G-C.7 (AI Coverage)**: ✅ Passed — 40% ≥ 30%

**No blockers. Wave C is cleared for integration.**
