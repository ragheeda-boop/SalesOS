# 09 — AI: LLMs, Embeddings, Agents, MCP

> Source: Source code + documentation cross-reference (Phase 9)
> Classification: VERIFIED, ARCHITECTURAL DRIFT, DOCUMENTATION ONLY

---

## Executive Summary

AI is documented as "the runtime, not a feature" — but in reality, **AI is gated off by default, partially implemented, and lacks test coverage**. The guardrails are production-grade, the grounding service works, and the copilot chat works if enabled — but the agent runtime is a placeholder, the decision engine is a stub, and there are zero AI-specific tests.

---

## 1. AI Components: Documented vs Implemented

| Component | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| **AI Copilot** | Natural language → query → recommend | Chat UI exists; SearchCompaniesTool only; `feature_ai_copilot=False` | ⚠️ PARTIALLY IMPLEMENTED |
| **Agent Runtime** | Full lifecycle (plan→execute→learn) | Placeholder string "PLANNED FOR RT3" | ❌ NOT IMPLEMENTED |
| **Revenue Brain** | NBA per user per context | Basic rule-based NBA; no AI reasoning | ⚠️ PARTIALLY IMPLEMENTED |
| **Scoring Engine** | ICP fit, engagement, intent | 7 feature store score computers | ⚠️ PARTIALLY IMPLEMENTED |
| **AI Memory** | Short/long/working memory | Basic persistence only | ⚠️ PARTIALLY IMPLEMENTED |
| **Prompt Studio** | Versioned, A/B testable | Prompt library CRUD exists | ⚠️ PARTIALLY IMPLEMENTED |
| **AI Governance** | Cost, latency, accuracy tracking | Cost tracker exists; no governance dashboard | ⚠️ PARTIALLY IMPLEMENTED |
| **Simulation Engine** | What-if scenario modeling | Minimal placeholder | ❌ NOT IMPLEMENTED |
| **Experiment Engine** | A/B tests with auto-selection | Not implemented | ❌ NOT IMPLEMENTED |
| **Digital Twin** | Real-time computational mirror | Zero components | ❌ NOT IMPLEMENTED |
| **AI Guardrails** | PII, injection, content filtering | Production-grade implementation | ✅ VERIFIED |
| **AI Grounding** | Data retrieval for context | Postgres + Neo4j retrieval | ✅ VERIFIED |
| **Arabic NLP** | Sentiment, extraction, understanding | Normalization only | ⚠️ PARTIALLY IMPLEMENTED |

---

## 2. LLM Providers

| Provider | Status | Usage |
|----------|--------|-------|
| OpenAI GPT-4o | ✅ Configured | Complex reasoning (default: gpt-4o-mini) |
| OpenAI GPT-4o-mini | ✅ Configured | Simple queries |
| OpenAI text-embedding-3-small | ✅ Configured | Embeddings |
| OpenAI text-embedding-3-large | 🟡 Planned | Larger embeddings |
| Anthropic Claude 3.5 Sonnet | 🟡 Planned | Enterprise fallback |

**Provider abstraction:** `intelligence/providers/` — OpenAI only; Anthropic not yet integrated.

**Vendor lock-in risk:** HIGH — single provider (OpenAI) for all AI capabilities.

---

## 3. Embeddings

| Dimension | Status |
|-----------|--------|
| Model | text-embedding-3-small (configured) |
| Storage | pgvector extension in PostgreSQL |
| Usage | Company embeddings, contact embeddings |
| Search | Vector similarity search via PgVectorStore |
| Caching | Embedding cache in knowledge_graph_runtime |

**Status:** ✅ Functional — embeddings are generated, stored, and searched.

---

## 4. RAG Pipeline

| Dimension | Status |
|-----------|--------|
| Retrieval | Postgres (pg_trigram + pgvector) + Neo4j |
| Ranking | Multi-factor ranking engine |
| Context Building | GroundingService retrieves from multiple sources |
| Generation | OpenAI API call with context |
| Guardrails | Prompt injection + PII scrubbing + output validation |

**Status:** ⚠️ Partial — pipeline exists but limited tools and no evaluation framework.

---

## 5. Knowledge Graph

| Dimension | Status |
|-----------|--------|
| Backend | Neo4j + SQL fallback |
| Production Status | Neo4j OFFLINE in production |
| Fallback | SQL-based graph queries |
| Security | ⚠️ SQL queries missing tenant filters (P0) |

**Status:** ⚠️ Partial — architecture exists but Neo4j is offline and SQL fallback has security gaps.

---

## 6. AI Guardrails (Production-Grade)

| Guardrail | Implementation |
|-----------|---------------|
| Prompt Injection | 20+ harmful patterns (ignore instructions, jailbreak, DAN, role-play) |
| PII Scrubbing | Emails, phones (Saudi + international), national ID/Iqama, IBAN, credit cards |
| Input Sanitization | Special tokens (`<|`, `[INST]`, `<<SYS>>`), escape sequences, control characters |
| Output Validation | JSON schema validation, confidence bounds checking |
| PII Leak Detection | Post-scrub audit via `detect_pii_leakage()` |

**Status:** ✅ Production-grade — the most mature AI component.

---

## 7. AI Test Coverage

| Metric | Value |
|--------|-------|
| AI-specific tests | 0 |
| AI evaluation tests | 3 files (minimal) |
| Target AI test coverage | 85% |
| Current AI test coverage | **0%** |

**Status:** ❌ Critical gap — zero AI test coverage.

---

## 8. MCP Server

| Dimension | Status |
|-----------|--------|
| Framework | FastMCP |
| Transport | stdio / SSE |
| Tools | SalesOS API operations |
| Resources | SalesOS data access |
| Client | SalesOS API client |

**Status:** ⚠️ Basic but functional — provides AI agent interface.

---

## 9. Copilot Details

### 9.1 Backend

| Component | Status |
|-----------|--------|
| SearchCompaniesTool | ✅ Real (delegates to PostgresSearchRepository) |
| Other tools | ❌ Not implemented |
| Feedback service | ✅ Real |
| Telemetry service | ✅ Real |
| Arabic detection | ✅ Real |
| Feature gate | `feature_ai_copilot=False` (default) |

### 9.2 Frontend

| Component | Status |
|-----------|--------|
| Copilot Panel | ✅ Real (chat, branching, feedback) |
| Contextual Insights | ✅ Real (per-page AI insights) |
| AI Insights Provider | ✅ Real (fetches insights) |
| Confidence Badge | ✅ Real |
| V3 AI Popup | ⚠️ Preview only (input disabled) |

---

## 10. Decision Engine

### 10.1 Frontend (`@salesos/decision-platform`)

| Method | Status |
|--------|--------|
| `decisionEngine.evaluate()` | ❌ THROWS "STUB" |
| `decisionEngine.evaluateBatch()` | ❌ THROWS "STUB" |
| `decisionEngine.explain()` | ❌ THROWS "STUB" |
| `decisionEngine.getHistory()` | ❌ THROWS "STUB" |
| `FeedbackEngine.submit()` | ❌ THROWS "STUB" |
| `FeedbackEngine.getStats()` | ❌ THROWS "STUB" |
| `ScoringEngine.score()` | ⚠️ Simple weighted average (no AI) |

**Classification:** DOCUMENTATION ONLY — explicitly marked "NOT PRODUCTION-READY" per AI_HONESTY.md.

### 10.2 Backend Decision Center

| Component | Status |
|-----------|--------|
| Decision Center Service | ✅ PostgreSQL-backed CRUD |
| Decision Runtime | ⚠️ Partial (engine + feedback loop) |
| IDOR Vulnerability | 🔴 Cross-tenant read/write (P0) |

---

## 11. AI Honesty Gate

| Gate | Status |
|------|--------|
| `feature_ai_copilot` | Default: `False` |
| Backend copilot status endpoint | Returns `feature_ai_copilot: false` by default |
| Frontend dual-gate | Both env + backend must be True |
| Stubs documented | AI_HONESTY.md explicitly prohibits marketing stubs as production AI |
| Classification | "Experimental/opt-in AI surfaces behind feature flags" |

---

## 12. Overall AI Assessment

| Area | Score | Notes |
|------|-------|-------|
| Guardrails | 9/10 | Production-grade |
| Grounding | 7/10 | Real retrieval, limited sources |
| Copilot | 4/10 | Gated, search-only tool |
| Embeddings | 7/10 | Functional pgvector |
| RAG | 5/10 | Pipeline exists, limited |
| Knowledge Graph | 3/10 | Neo4j offline |
| Agent Runtime | 1/10 | Placeholder only |
| Digital Twin | 0/10 | Zero components |
| AI Governance | 3/10 | Cost tracker only |
| Test Coverage | 0/10 | Zero AI tests |
| **Overall** | **4/10** | **Guardrails strong; everything else partial or missing** |

---

*This document describes the AI reality. The vision is captured in 01_THEORY_MODEL.md.*
