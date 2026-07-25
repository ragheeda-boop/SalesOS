# Sprint 0 — Wave C Security Review: AI Foundation

> **Reviewer**: security-reviewer
> **Date**: 2026-07-16
> **Artifact**: WO-003 / WAVE-C deliverables

---

## Review Verdict: **Conditional Approval**

**Condition**: Fix `SdkSettings` to include `anthropic_api_key` (and `gemini_api_key`, `azure_api_key`) before production deployment, plus document `ANTHROPIC_API_KEY` in `.env.production.template`.

---

## Review Scope & Methodology

Source files examined:

| File | Path |
|------|------|
| Anthropic Provider | `intelligence/providers/anthropic_provider.py` |
| Provider Factory | `intelligence/providers/factory.py` |
| Cost Tracker | `intelligence/providers/cost_tracker.py` |
| Postgres Memory Store | `intelligence/memory/postgres_store.py` |
| Memory Base | `intelligence/memory/base.py` |
| Prompt Registry v2 | `intelligence/prompts/registry.py` |
| Streaming / SSE | `intelligence/streaming/sse.py` |
| SDK Config | `sdk/config.py` |
| Migration | `migrations/007_ai_foundation.sql` |
| Env Template | `.env.production.template` |
| Agent Prompts | `intelligence/prompts/agents.yaml` |

---

## 1. Anthropic Provider — API Key Handling

### Finding ✅ No hardcoded keys
`AnthropicProvider.__init__()` accepts `api_key: str | None = None` (line 22) — no hardcoded key in source.

### Finding ⚠️ Configuration gap: `SdkSettings` missing `anthropic_api_key`
The factory (`factory.py:40`) resolves the key via:

```python
getattr(sdk_settings, "anthropic_api_key", None)
```

But `SdkSettings` (`sdk/config.py`) does **not** define `anthropic_api_key` as a field. Because `model_config.extra = "ignore"`, `pydantic-settings` silently drops any `ANTHROPIC_API_KEY` env var. Result: the factory always gets `None`, and `AnthropicProvider._get_client()` returns `None`, causing silent fallback to error responses.

**Impact**: Anthropic provider is **non-functional in production** despite the code existing. Any production routing to "anthropic" will silently fail to empty/error responses.

**Same issue applies to**: `gemini_api_key` and `azure_api_key`.

### Finding ⚠️ `.env.production.template` missing ANTHROPIC_API_KEY
Line 40-42 documents `OPENAI_API_KEY` but there is no `ANTHROPIC_API_KEY` entry in the template. Operators have no documented path to configure it.

---

## 2. Cost Tracker — Sensitive Data Exposure

### Finding ✅ No PII in cost records
`CostRecord` stores: `provider`, `model`, tokens, `cost`, `latency_ms`, `operation`, `tenant_id`, `user_id` — none of these contain PII. The `user_id` and `tenant_id` are opaque identifiers, not names/emails.

### Finding ⚠️ Error field could leak sensitive data
`CostRecord.error: str | None` (line 41) is persisted to `llm_cost_tracking` (migration line 37: `error TEXT`). LLM provider error responses can contain:
- Stack traces from the provider SDK
- Internal service names
- Debug information from proxy/gateway errors

The `get_summary()` method (line 224) does not expose individual error messages — only counts. However, `load_records_from_db()` (line 188) returns full records including the `error` field. Any admin endpoint that exposes these records could leak sensitive error details.

**Recommendation**: Sanitize or truncate error messages before persistence. Strip stack traces and provider-internal details.

---

## 3. Memory Runtime — PII in Episodic Memory

### Finding 🔴 PII CAN be stored but is NOT marked or classified
The `episodic_memory` table stores:
- `content` (TEXT) — arbitrary conversation content, can contain PII
- `metadata` (JSONB) — arbitrary structured data, can contain PII
- `agent_id`, `session_id`, `conversation_id` — opaque identifiers

The `MemoryEntry` dataclass (`memory/base.py`) has **no PII classification field**:
- No `is_sensitive` or `contains_pii` boolean
- No `sensitivity_level` enum
- No `classification` string
- The `MemoryScope` enum (`WORKING`, `SESSION`, `CONVERSATION`, `EPISODIC`, `SEMANTIC`) does not include a sensitive scope

### Finding ⚠️ No encryption at rest
The migration creates the table with no mention of column encryption, pgcrypto, or TDE. PII data stored in the `content` or `metadata` columns is in cleartext at rest.

### Finding ✅ TTL mechanism exists
`cleanup_expired()` (line 119) provides a cleanup mechanism for time-bound memory, which can reduce the PII retention window if TTLs are set appropriately.

**Recommendation**: Add a `sensitivity` field to `MemoryEntry` (enum: `public`, `internal`, `sensitive`, `pii`) and a corresponding column in the schema. Consider encrypting sensitive entries or marking them for stricter access control.

---

## 4. Prompt Registry v2 — Injection Vectors

### Finding ⚠️ Template values not sanitized
The `render()` method (registry.py:201-232) uses naive `str.replace()` to fill template variables:

```python
for key, value in kwargs.items():
    user_prompt = user_prompt.replace(f"{{{key}}}", str(value))
```

There is **no validation, sanitization, or escaping** of the injected values. If user-controlled input reaches `kwargs`, an attacker could:
- Inject additional prompt instructions via closing braces or newlines
- Override the system prompt (if `system` template also uses same variable names)
- Inject special tokens that confuse the LLM

### Finding ✅ Placeholder validation present but limited
`_validate_placeholders()` (line 270) checks that all **declared** placeholders are provided — but does not reject **undeclared** kwargs. If a caller passes unexpected keys, they are silently used for replacement, potentially injecting content into unexpected parts of the template.

### Finding ✅ Regex validation on placeholder names
`validate()` (line 258) ensures placeholder names match `^[a-zA-Z_][a-zA-Z0-9_]*$` — no path traversal or special characters in placeholder names.

**Recommendation**: Add value-level sanitization in `render()`:
- Strip or escape curly braces in values
- Reject or warn on values that contain `{` or `}`
- Consider using a template engine with auto-escaping

---

## 5. Streaming / SSE — Data Leakage

### Finding ✅ Event payloads are well-structured
The SSE layer handles 4 event types correctly. Chunks contain only `type` + `content` (tokens). No extraneous data exposed.

### Finding ⚠️ Error events may leak provider internals
`format_sse_event()` (sse.py:29-30) passes `event.error` directly:

```python
payload = json.dumps({"type": "error", "error": event.error or "Unknown error"})
```

If provider errors contain PII or internal details, these are streamed directly to the client. The source of `StreamEvent.error` (anthropic_provider.py:99) is:

```python
yield StreamEvent(type="error", error="No API key configured")
```

This specific message is safe, but any future error paths may not be.

**Recommendation**: Implement an error sanitizer that maps provider errors to generic user-facing messages before streaming.

### Finding ✅ No request/response PII in normal streaming
The `chunk`, `done`, and `tool_call` events contain only token content and usage metadata. No request data, API keys, or user identifiers leak through normal streaming.

---

## 6. SQL Injection Assessment

### Finding ✅ Parameterized queries throughout
All SQL in `postgres_store.py` and `cost_tracker.py` uses SQLAlchemy `text()` with bound parameters (`:param` syntax). The f-string WHERE construction in `query()` (line 84) and `clear()` (line 112) builds conditions from hardcoded column names only — user input never reaches the SQL string structure.

**Result**: SQL injection risk is **negligible**.

---

## Summary of Findings

| # | Issue | Severity | Area | Status |
|---|-------|----------|------|--------|
| 1 | `SdkSettings` missing `anthropic_api_key` (and `gemini`, `azure`) | 🔴 High | Configuration — Provider | **Fix required** |
| 2 | `.env.production.template` missing `ANTHROPIC_API_KEY` | 🟡 Medium | Documentation | Fix recommended |
| 3 | PII storable in episodic memory with no classification/label | 🟡 Medium | Memory Runtime | Fix recommended |
| 4 | Prompt template values not sanitized against injection | 🟡 Medium | Prompt Registry | Fix recommended |
| 5 | Error messages from providers may leak via SSE/streaming | 🟢 Low | Streaming | Monitor |
| 6 | Cost tracker error field may contain sensitive data | 🟢 Low | Cost Tracking | Monitor |
| 7 | No encryption at rest on episodic_memory table | 🟢 Low | Memory | Future |

---

## Required Fixes (Before Production)

### Fix 1: Add missing fields to `SdkSettings`
`salesos/backend/sdk/config.py` — add:

```python
anthropic_api_key: str = ""
gemini_api_key: str = ""
azure_api_key: str = ""
```

### Fix 2: Add `ANTHROPIC_API_KEY` to `.env.production.template`
Insert after line 43:

```
# ─── Anthropic ──────────────────────────────────────────────
#ANTHROPIC_API_KEY=<CHANGE_ME: Anthropic API key>
```

---

## Recommended Fixes (Sprint +1)

1. **Add PII classification** to `MemoryEntry`: a `sensitivity` field (`MemorySensitivity` enum: `public`, `internal`, `sensitive`, `pii`) with corresponding migration column
2. **Sanitize LLM error messages** before persistence in cost tracker and before streaming in SSE layer
3. **Add value validation** in `PromptRegistry.render()` to block injection via template values

---

## Verdict

**CONDITIONAL APPROVAL** — subject to Fix 1 and Fix 2 being applied before production deployment. Wave C code is architecturally sound and free of critical vulnerabilities. The configuration gap is the only blocker; all other findings are recommendations for hardening.
