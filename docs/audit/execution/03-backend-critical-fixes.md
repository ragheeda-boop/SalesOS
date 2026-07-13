# Backend Critical Fixes — Execution Report

> Date: 2026-07-13
> Branch: muhide
> Status: All 6 fixes applied

---

## Fix 1: Coverage Gate (QA-002) ✅

**File**: `salesos/backend/pyproject.toml`

- Changed `fail_under = 30` → `fail_under = 85`
- Added `source = ["app", "domains", "sdk", "runtime", "intelligence"]` for accurate coverage tracking across all core packages

---

## Fix 2: RAG Hybrid Retrieval Bug (SEC-M-09) ✅

**File**: `salesos/backend/intelligence/rag/retrieval.py`

- **Bug**: `retrieve_hybrid()` accepted only `query_embedding`, `tenant_id`, `top_k` — no text query parameter. The SQL query was hardcoded with `"query_text": ""` on line 135, meaning the text/keyword half of the hybrid search always scored 0.
- **Fix**: Added `query_text: str` as a required parameter to `retrieve_hybrid()`. The parameter is now passed through to the SQL `:query_text` bind variable.

---

## Fix 3: Prompt Injection Detection (SEC-M-17) ✅

**Files**: `salesos/backend/intelligence/agent_base.py`, `salesos/backend/intelligence/guardrails.py`

- **Bug**: `add_input_moderation()` and `sanitize_input()` existed in `guardrails.py` but were never called from any agent execution path.
- **Fix**: 
  - Added imports of `add_input_moderation` and `sanitize_input` in `agent_base.py`
  - Wired `sanitize_input(user)` before every LLM call in `GroundedBaseAgent.execute_grounded()`
  - If `add_input_moderation()` detects harmful content, the agent immediately returns a failed result with `"Input rejected by content moderation"` — preventing the prompt from ever reaching the LLM

---

## Fix 4: Cache Consolidation ✅

**Files**: `salesos/backend/app/cache.py`, `salesos/backend/app/common/cache.py`

- **Canonical**: `sdk/cache.py` → `CacheService` + `cache_key()` remain the single source of truth
- **`app/cache.py`**: Fully re-written. Now subclasses `sdk.cache.CacheService`, accepts `redis_url` for backward compatibility, delegating all operations to the canonical parent. Also re-exports `cache_key`. Includes `health()` and `close()` methods. Includes a `create_cache_from_url()` factory.
- **`app/common/cache.py`**: Now imports `cache_key` from `sdk.cache` for consistent key format. TTL default aligned to 300s (was 60s). The `cached()` decorator remains for FastAPI dependency caching.
- **Consistent defaults**: TTL = 300s across all cache implementations. Key format uses `sdk.cache.cache_key()` colon-delimited pattern.

---

## Fix 5: NBA AI Reasoning ✅

**Files**: `salesos/backend/runtime/nba_engine/__init__.py`

- **Bug**: `NBAEngine._ai_evaluate()` was stubbed with `return None  # AI integration in Sprint 5`, meaning the entire AI reasoning pipeline was dead code.
- **Fix**:
  - NBAEngine constructor now accepts optional `llm_service` parameter
  - When provided, creates an `NBAReasoner` instance from `runtime.nba_engine.engine.ai.reasoner`
  - `_ai_evaluate()` now calls the reasoner with opportunity data, company context, activities, and candidates
  - Applies `sanitize_input()` and `add_input_moderation()` guardrails before AI evaluation
  - Falls back to `None` gracefully on any error (preserving rule-only behavior as safe fallback)
  - Returns ranked action names when AI succeeds

---

## Fix 6: Unbounded Memory Stores ✅

**Files**:
- `salesos/backend/runtime/decision_runtime/__init__.py`
- `salesos/backend/runtime/decision_runtime/feedback_loop.py`
- `salesos/backend/runtime/recommendation_runtime/__init__.py`
- `salesos/backend/runtime/memory_runtime/__init__.py`

### DecisionEngine (`decision_runtime/__init__.py`)
- Added `_max_decisions = 10000` and `_decision_ttl = 3600` (1 hour)
- New `_evict_decisions()` method:
  - Removes entries older than TTL
  - When over max, removes oldest entries (LRU by `created_at`)
  - Logs warning with eviction count
- Called before every new decision insertion in `evaluate()`

### DecisionFeedbackLoop (`decision_runtime/feedback_loop.py`)
- Added `_max_entries = 10000` and `_entry_ttl = 3600` (1 hour)
- New `_evict_entries()` method:
  - Filters out expired entries by `created_at`
  - Trims oldest entries when over max
  - Logs warning with eviction count
- Called before every `record_feedback()` append

### RecommendationEngine (`recommendation_runtime/__init__.py`)
- Added `_recommendations: dict[str, Recommendation]` store
- Added `_max_recommendations = 10000` and `_rec_ttl = 3600` (1 hour)
- New `_evict_recommendations()` method with same TTL+LRU eviction pattern
- Called before every `generate()` store operation

### MemoryRuntime (`memory_runtime/__init__.py`)
- Previously a stub (`# PLANNED FOR RT3`)
- Now implements a full `BoundedStore[T]` generic class with:
  - `OrderedDict`-backed LRU eviction
  - `time.monotonic()`-based TTL expiration
  - `get()`, `set()`, `delete()`, `contains()`, `size()`, `clear()`, `keys()`
  - Warning logs on every eviction event
- `MemoryRuntime` facade manages named bounded stores with shared TTL/max defaults
- Ready for use by any runtime module needing a bounded in-memory collection

---

## Summary

| Fix | Severity | Files Changed | Breaking |
|-----|----------|--------------|----------|
| 1. Coverage Gate | QA-002 Critical | 1 | No |
| 2. RAG Hybrid Retrieval | SEC-M-09 High | 1 | Yes (new param) |
| 3. Prompt Injection | SEC-M-17 Critical | 2 | No |
| 4. Cache Consolidation | Refactoring | 2 | No |
| 5. NBA AI Reasoning | Feature Gap | 1 | No |
| 6. Unbounded Memory Stores | Stability | 4 | No |

**Total**: 11 files modified, 0 files created (excluding this report and memory_runtime rewrite)
