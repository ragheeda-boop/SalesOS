# SalesOS AI Strategy — vNext

> **Author**: AI Engineering Director
> **Status**: Draft
> **Last Updated**: 2026-07-16
> **Version**: v0.1

---

## Table of Contents

1. [AI Architecture Vision](#1-ai-architecture-vision)
2. [Agent Architecture](#2-agent-architecture)
3. [Prompt Registry](#3-prompt-registry)
4. [Memory System](#4-memory-system)
5. [Knowledge System](#5-knowledge-system)
6. [Reasoning Engine](#6-reasoning-engine)
7. [Planning Engine](#7-planning-engine)
8. [Decision Engine](#8-decision-engine)
9. [Copilot](#9-copilot)
10. [RAG System](#10-rag-system)
11. [Provider Strategy](#11-provider-strategy)
12. [Evaluation](#12-evaluation)
13. [Guardrails & Safety](#13-guardrails--safety)
14. [Multi-Agent Architecture](#14-multi-agent-architecture)
15. [Implementation Phases](#15-implementation-phases)
16. [AI Testing Strategy](#16-ai-testing-strategy)

---

## 1. AI Architecture Vision

### Current State

The SalesOS AI platform has substantial infrastructure but critical gaps. The `intelligence/` module contains agent definitions (15 agents), RAG pipeline (chunking, embeddings, retrieval, service), Arabic NLP (tokenization, lemmatization, NER, sentiment, Saudi stop words), graph intelligence, and evaluation tooling. The `domains/ai/` module has 92% test coverage. The `runtime/` subsystem has a fully implemented Decision Runtime and NBA Reasoner, but the Agent Runtime is a **placeholder marked "planned for RT3"**.

The frontend has Decision Platform (8 engines) and Agent SDK (contracts, memory, orchestrator, registry, tools, RAG) in `packages/platform/`.

### Critical Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| Zero backend AI tests | Critical | No regression safety for any AI change |
| Agent Runtime is placeholder | Critical | No agent execution environment |
| Evaluation test_cases empty | High | No baseline for measuring AI quality |
| Only OpenAI supported | High | Vendor lock-in, no KSA data sovereignty option |
| No embedding cache | Medium | Every query re-embeds text |
| No agent observability | Medium | Debugging agent behavior is impossible |
| Data Fabric connectors return mock data | Medium | Not functional with real sources |
| search_companies tool returns empty | Medium | Frontend agent tool broken |
| vectors table uses ARRAY(FLOAT) | Medium | No native vector type support |

### Target State

```
┌─────────────────────────────────────────────────────┐
│                   AI Layer vNext                      │
├──────────────┬──────────────┬────────────────────────┤
│  Multi-Agent │   Runtime    │   Evaluation & Safety  │
│  System      │   Engine     │   Framework            │
│              │              │                        │
│  • Agent     │  • Agent     │  • Test cases          │
│    Registry  │    Runtime   │  • Golden datasets     │
│  • Tool      │  • Decision  │  • Regression suite    │
│    System    │    Runtime   │  • Guardrails          │
│  • Memory    │  • NBA       │  • Observability       │
│    Manager   │    Engine    │  • Cost tracking       │
│  • Orchestr. │  • Workflow  │                        │
├──────────────┴──────────────┴────────────────────────┤
│                Provider Layer                          │
│  OpenAI │ Anthropic │ Local (KSA) │ Fallback Chain    │
├──────────────────────────────────────────────────────┤
│             Infrastructure Layer                       │
│  PGVector │ Embedding Cache │ RAG │ Arabic NLP       │
└──────────────────────────────────────────────────────┘
```

---

## 2. Agent Architecture

### Current: 15 Specialized Agents

The intelligence module defines 15 agents: competitor, contract, coordinator, forecast, llm, meeting, news, pricing, proposal, relationship, renewal, research, tender, base, and a generic agent.

Each agent lives in `intelligence/` with schemas defined in `schemas.py`.

### vNext: Agent Runtime + Registry

The Agent Runtime placeholder must be replaced with a full implementation:

```
runtime/agent_runtime/
├── __init__.py
├── scheduler.py          # Agent scheduling + lifecycle
├── executor.py           # Agent execution engine
├── registry.py           # Runtime agent registry
├── context.py            # Execution context + tracing
├── telemetry.py          # Agent observability (NEW)
└── middleware.py         # Pre/post execution hooks (NEW)
```

**Key Design Decisions:**

1. **Agent Lifecycle**: Every agent goes through: REGISTERED → INITIALIZED → READY → RUNNING → COMPLETED / FAILED

2. **Tool Injection**: Tools are injected at runtime via dependency injection — agents do not hard-code tool references

3. **Tracing**: Every agent execution produces a trace span with: agent_id, input, output, duration, token_cost, provider, model

4. **Timeout & Retry**: Each agent call has configurable timeout (default 30s) and retry policy (default: 3 attempts with exponential backoff)

5. **Agent Registry**: Agents register their capabilities, required tools, and supported models — enabling dynamic discovery by the orchestrator

**Frontend Agent SDK** (`packages/platform/agents/`) is already strong with contracts, memory, orchestrator, registry, tools, and RAG. Backend parity is the goal.

---

## 3. Prompt Registry

### Current

Prompts are managed via YAML templates in `intelligence/prompts/agents.yaml` with a `registry.py` loader. This provides a single source of truth for agent prompts.

### vNext: Versioned Prompt Registry

```
intelligence/prompts/
├── agents.yaml            # Current (migrate to versioned)
├── v1/
│   ├── agents.yaml
│   └── schemas.yaml
├── v2/                    # vNext prompts
│   ├── agents.yaml
│   ├── schemas.yaml
│   └── evaluations.yaml  # Prompt evaluation criteria
└── registry.py            # Version-aware registry
```

**Enhancements:**

1. **Prompt Versioning**: Each prompt has a version hash. The registry can resolve by version or "latest".

2. **Prompt Evaluation**: Each prompt has associated evaluation criteria — enabling automated regression testing when prompts change.

3. **A/B Testing**: Registry supports `active_version` per agent — canary test new prompts against 5% of traffic.

4. **Dynamic Variables**: Registry validates that all template variables have corresponding runtime context keys.

5. **Arabic Support**: All prompts have Arabic variants. The registry selects the variant based on tenant locale settings.

---

## 4. Memory System

### Current

Frontend Agent SDK has a `memory` module in `packages/platform/agents/`. Backend intelligence has no explicit memory system.

### vNext: Multi-Tier Agent Memory

```
intelligence/memory/
├── __init__.py
├── base.py               # Abstract memory interface
├── episodic.py           # Episodic memory (agent runs)
├── semantic.py           # Semantic memory (facts + knowledge)
├── procedural.py         # Procedural memory (skills + workflows)
├── working.py            # Working memory (current context)
├── persistent.py         # Persistent storage layer
└── retrieval.py          # Memory retrieval + ranking
```

**Memory Architecture:**

| Tier | Scope | Volatility | Backend | Purpose |
|------|-------|-----------|---------|---------|
| Working | Session | Ephemeral | In-memory | Current conversation context |
| Episodic | Agent | Short-term | PostgreSQL | Recent agent runs + outcomes |
| Semantic | System | Long-term | PGVector | Encoded facts + knowledge |
| Procedural | Global | Permanent | YAML + DB | Agent skills + tool usage patterns |

**Cross-cutting:**

- **Memory Retrieval**: Episodic + semantic retrieval at query time, ranked by relevance + recency
- **Memory Consolidation**: Background job that converts episodic → semantic at configurable intervals
- **Memory Limits**: Configurable per-tier: max_episodes, max_tokens, TTL

---

## 5. Knowledge System

### Current

The intelligence module has graph intelligence (`graph/`), RAG pipeline (chunking, embeddings, retrieval, service), and a Data Fabric intelligence module (`data_fabric/`). The Knowledge Graph is integrated via Neo4j. The vectors table uses `ARRAY(FLOAT)` which lacks native vector index support.

### vNext: Unified Knowledge Layer

```
intelligence/knowledge/
├── __init__.py
├── graph.py              # Knowledge graph operations
├── vector.py             # PGVector (upgrade to native type)
├── hybrid.py             # Hybrid retrieval (graph + vector)
├── cache.py              # Embedding cache (NEW)
├── sync.py               # Background sync orchestrator
└── sources/
    ├── data_fabric.py    # Real Data Fabric connectors (replace mock)
    └── market.py         # Market intelligence integration
```

**Key Initiatives:**

1. **PGVector Migration**: Migrate `ARRAY(FLOAT)` → `VECTOR(n)` to enable IVFFlat/HNSW indexes. This is a schema migration + query update. Expected: ~50x query speed improvement on similarity search.

2. **Embedding Cache**: LRU cache keyed by (text_hash, model) to avoid re-embedding. Local in-memory cache + optional Redis persistence.

3. **Hybrid Retrieval**: Combine knowledge graph traversal (Neo4j) with vector similarity (PGVector) using RRF fusion — similar to the Search domain's approach.

4. **Data Fabric Connectors**: Replace mock data with real connectors. Target sources: CRM, ERP, market data feeds, news APIs. Each connector implements a `DataSource` protocol.

5. **Graph Intelligence**: Expand the `graph/` module to support entity resolution (already exists in Entity Resolution pipeline) and relationship inference.

---

## 6. Reasoning Engine

### Current

Reasoning exists in `intelligence/reasoning.py` and the Decision Runtime (`runtime/decision_runtime/`). The NBA Reasoner (`runtime/nba_engine/`) provides next-best-action reasoning.

### vNext: Multi-Strategy Reasoning Pipeline

```
intelligence/reasoning/
├── __init__.py
├── base.py               # Abstract reasoner
├── chain_of_thought.py   # Chain-of-thought reasoning
├── tree_of_thought.py    # Tree-of-thought reasoning (NEW)
├── structured.py         # Structured reasoning (JSON schema)
├── compositional.py      # Compositional reasoning (sub-problems)
├── ensemble.py           # Ensemble: weighted voting across strategies
└── planner.py            # Reasoning plan generation (moved from Planning)
```

**Strategy Selection:**

| Strategy | Use Case | Provider Required | Token Cost |
|----------|----------|-------------------|------------|
| Direct | Simple Q&A, classification | Any | Low |
| Chain-of-Thought | Analysis, explanation | Any (stronger preferred) | Medium |
| Tree-of-Thought | Complex decisions, optimization | OpenAI / Anthropic | High |
| Structured | JSON output, form filling | Any | Low |
| Compositional | Multi-step problem solving | Any | Medium-High |
| Ensemble | High-stakes decisions | Multi-provider | Very High |

The Decision Runtime selects the reasoning strategy based on:
- Task complexity (inferred from input)
- Latency budget
- Cost budget
- Required confidence level

---

## 7. Planning Engine

### Current

No formal planning engine exists. Agent orchestration is handled by the frontend Agent SDK orchestrator (`packages/platform/agents/orchestrator/`) but the backend Runtime has no planning capabilities.

### vNext: Plan-Execute-Observe Loop

```
runtime/planning/
├── __init__.py
├── planner.py            # Plan generation
├── executor.py           # Step-by-step execution
├── observer.py           # Plan observation + adaptation
├── templates.py          # Plan templates (common workflows)
└── validator.py          # Plan validation + safety checks
```

**Planning Cycle:**

```
User Request
    │
    ▼
┌─────────────┐     ┌──────────────┐
│  Decompose   │────►│  Generate    │
│  Task        │     │  Plan Steps  │
└─────────────┘     └──────┬───────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Validate   │◄──── Safety + Feasibility check
                    │  Plan       │
                    └──────┬─────┘
                           │
                    ┌──────▼──────┐
                    │  Execute    │
                    │  Step N     │────► Agent Runtime
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Observe    │
                    │  Result     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Adapt?     │────► Re-plan if needed
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Complete   │
                    └─────────────┘
```

**Plan Templates** — common workflows:
- `lead_research.yaml` — Research a lead across all sources
- `deal_health_check.yaml` — Evaluate deal health + next best actions
- `contract_review.yaml` — Review contract terms + risks
- `meeting_prep.yaml` — Gather context, recent activity, talking points

---

## 8. Decision Engine

### Current — Already Strong

The Decision Runtime (`runtime/decision_runtime/`) is fully implemented. The frontend Decision Platform (`packages/platform/decision/`) has 8 engines. The DecisionProvider is integrated across Dashboard, Company, Scoring, and Workflow domains. This is the strongest component of the AI platform.

### vNext: Enhancement Plan

No major rework needed. Focus on:

1. **Decision Audit Trail**: Every decision should produce an auditable record: input context, reasoning path, confidence, provider used, alternatives considered.

2. **Decision Feedback Loop**: Allow users to provide feedback on decisions (helpful / not helpful). Feedback feeds into the evaluation framework.

3. **Explicit Rejection Reason**: When the decision engine cannot produce a recommendation, it must explain why — not fall back to a generic response.

4. **Multi-Provider Voting** (P1): For high-stakes decisions (e.g., >$100K deals), invoke multiple providers and use ensemble reasoning to produce a consensus recommendation.

5. **Decision Templates**: Pre-configured decision patterns for common scenarios: lead qualification, deal progression, renewal risk, pricing optimization.

---

## 9. Copilot

### Current — Already Strong

Copilot has a working frontend Agent SDK with orchestrator, memory, registry, tools, and RAG. The frontend Decision Platform has 8 engines. This is the primary user-facing AI interface.

### vNext: Enhancement Plan

1. **Tool Result Observability**: Fix `search_companies` returning empty results. Add telemetry to every tool call — success rate, latency, result count.

2. **Copilot Feedback**: Add explicit rating mechanism (thumbs up/down + optional comment) on every copilot response. Store in evaluation database.

3. **Conversation Branching**: Support branch points where users can explore alternative paths without losing context.

4. **Proactive Copilot**: Push notifications when the system detects important events (e.g., "A competitor just announced a product that overlaps with ACME's needs — would you like a competitive brief?").

5. **Arabic Copilot**: Ensure all copilot interactions support Arabic RTL, Arabic NLP (existing `arabic/` module), and Saudi business context.

---

## 10. RAG System

### Current

The RAG pipeline is complete in `intelligence/` with chunking (`chunking.py`), embeddings (`embeddings.py`), retrieval (`retrieval.py`), and service (`service.py`). The graph intelligence module and Data Fabric intelligence module exist.

### vNext Improvements

1. **Embedding Cache** (P0): LRU cache to eliminate redundant embedding calls. Key: `(text_hash, model_name)`. TTL of 24 hours. Expected: 40-60% reduction in embedding API costs.

2. **Hybrid Retrieval** (P1): Combine vector similarity with keyword BM25 scoring. Use RRF fusion (as done in Search domain).

3. **Contextual Chunking** (P1): Improve chunking to preserve document structure boundaries (sections, paragraphs, lists) rather than fixed token windows.

4. **Multi-Model Embeddings** (P1): Support multiple embedding models. The retrieval service selects the model based on: language (Arabic vs English), content type (code, legal, general), and query complexity.

5. **Query Rewriting** (P2): Before retrieval, rewrite the user query to improve search quality — expand acronyms, correct Arabic transliterations, add domain-specific synonyms.

6. **RAG Evaluation** (P1): Each RAG response includes: retrieved chunks, relevance scores, and the generation source attribution — enabling evaluation of retrieval quality vs. generation quality.

---

## 11. Provider Strategy

### Current: OpenAI-Only

The LLM provider layer uses a factory pattern but only has one implementation: OpenAI. This is a **critical risk** for three reasons:
1. **Vendor lock-in** — no leverage in negotiations, no fallback if OpenAI has outages
2. **KSA data sovereignty** — OpenAI may not meet KSA PDPL requirements for all data types
3. **Cost optimization** — no ability to route simple queries to cheaper providers

### vNext: Multi-Provider Strategy

```
intelligence/providers/
├── __init__.py
├── factory.py              # Provider factory (exists, enhance)
├── protocol.py             # Provider protocol/interface
├── openai.py               # OpenAI provider (exists)
├── anthropic.py            # Anthropic provider (NEW)
├── local.py                # Local/on-prem provider (NEW)
├── fallback.py             # Fallback chain logic (NEW)
├── cost_tracker.py         # Cost tracking (exists, enhance)
└── router.py               # Intelligent query routing (NEW)
```

**Provider Tiers:**

| Tier | Provider | Use Case | Cost | Data Sovereignty |
|------|----------|----------|------|------------------|
| Premium | OpenAI GPT-4o | Complex reasoning, high-stakes decisions | $$$ | US-based |
| Standard | Anthropic Claude 3.5 | Analysis, content generation, general | $$ | US-based |
| Local | On-prem models | Simple Q&A, classification, Arabic NLP | $ | KSA-based |
| Fallback | Any available | Degraded mode, provider outage | Varies | Per provider |

**Routing Logic:**

```
Query → classify_complexity() → match_to_tier() → try_primary → fallback if failed
```

- Simple queries (classification, simple Q&A) → Local model
- Moderate queries (analysis, summaries) → Anthropic
- Complex queries (reasoning, decisions) → OpenAI
- If primary provider fails → try next tier within latency budget

**Local Provider Requirements:**
- Must run on-prem in KSA (meeting PDPL)
- Must support Arabic natively
- Minimum 7B parameter model for acceptable quality
- Candidates: Llama 3 (Arabic-tuned variant), AceGPT, Jais

---

## 12. Evaluation

### Current

The evaluation system exists: `evaluator.py`, `evaluation/` module. However, `test_cases/` is **EMPTY**. There is no baseline golden dataset for measuring AI quality.

### Critical Issue

Without evaluation test cases, there is no way to:
- Measure regression when prompts change
- Compare provider quality objectively
- Track AI quality over time
- Gate releases on AI quality metrics

### vNext: Evaluation Framework

```
intelligence/evaluation/
├── __init__.py
├── evaluator.py              # Core evaluator (exists)
├── test_cases/               # FILL THIS (was EMPTY)
│   ├── agents/               # Per-agent test cases
│   │   ├── competitor.yaml
│   │   ├── contract.yaml
│   │   ├── pricing.yaml
│   │   ├── proposal.yaml
│   │   ├── renewal.yaml
│   │   ├── forecast.yaml
│   │   ├── research.yaml
│   │   ├── meeting.yaml
│   │   └── news.yaml
│   ├── rag/                  # RAG evaluation cases
│   │   ├── chunking.yaml
│   │   ├── retrieval.yaml
│   │   └── generation.yaml
│   ├── reasoning/            # Reasoning evaluation
│   │   └── scenarios.yaml
│   └── edge_cases.yaml       # Cross-cutting edge cases
├── metrics.py                # Scoring metrics (NEW)
├── regression.py             # Regression detection (NEW)
├── report.py                 # Report generation (NEW)
└── runner.py                 # Batch evaluation runner (NEW)
```

**Test Case Schema (YAML):**

```yaml
# Example: intelligence/evaluation/test_cases/agents/pricing.yaml
test_cases:
  - id: "pricing-001"
    description: "Basic price recommendation for SaaS product"
    input:
      product_type: "SaaS"
      annual_contract_value: 120000
      industry: "FinTech"
      region: "KSA"
      competitor_pricing: [{"name": "CompetitorX", "price": 100000}]
    expected:
      min_price: 95000
      max_price: 140000
      reasoning_type: "value_based"
    acceptable_providers: ["openai", "anthropic"]
    metrics: ["price_accuracy", "reasoning_quality", "explanation_clarity"]
```

**Evaluation Metrics:**

| Metric | Description | Target |
|--------|-------------|--------|
| Accuracy | Exact match / within expected range | >85% |
| Relevance | Retrieved chunks relevant to query | >90% |
| Latency | P95 response time per provider | <5s |
| Cost | Token cost per query | <$0.05 |
| Safety | Blocked harmful content | 100% |
| Arabic Quality | Arabic NLP accuracy | >90% |

**Evaluation Cadence:**

- **Per commit**: Run evaluation on changed agents (smoke test)
- **Daily**: Full evaluation suite on staging
- **Weekly**: Cross-provider comparison report
- **Per release**: Gate release on evaluation metrics

---

## 13. Guardrails & Safety

### Current

Guardrails exist in `intelligence/guardrails.py`. The ground truth system is in `intelligence/grounding.py`. The base agent has input/output validation.

### vNext: Defense-in-Depth Guardrails

```
intelligence/safety/
├── __init__.py
├── guardrails.py           # Current, enhance
├── input_validator.py      # Input validation + sanitization
├── output_validator.py     # Output validation + safety check
├── grounding.py            # Ground truth verification (enhance)
├── jailbreak_detector.py   # Prompt injection detection (NEW)
├── pii_scanner.py          # PII detection + redaction (NEW)
├── cost_anomaly.py         # Cost anomaly detection (NEW)
└── rate_limiter.py         # Per-agent rate limiting (NEW)
```

**Guardrail Layers:**

```
User Input
    │
    ▼
┌──────────────────┐
│ Layer 1: Input   │  PII redaction, jailbreak detection, input validation
│ Safety           │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Layer 2: Context  │  Grounding check — are facts verifiable?
│ Safety            │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Layer 3: Provider │  Rate limiting, cost anomaly, provider routing
│ Safety            │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Layer 4: Output  │  Output sanitization, PII detection, fact grounding
│ Safety           │
└──────────────────┘
    │
    ▼
   Response
```

**Key Safety Policies:**

1. **No hallucinated data**: All factual claims must be grounded in retrieved context. Responses must cite sources.
2. **No PII leakage**: PII scanner redacts email, phone, national ID, passport, bank details before sending to providers.
3. **No pricing guarantees**: Pricing recommendations must include confidence intervals, not absolute guarantees.
4. **Deal value caps**: Pricing/renewal agents must not recommend values outside configured deal-size bounds.
5. **Competitor fairness**: Competitive analysis must be factual, not speculative. Must cite sources.

---

## 14. Multi-Agent Architecture

### Current

Agents exist as individual modules with no formal collaboration protocol. The agent runtime is a placeholder.

### vNext: Agent Collaboration Framework

```
runtime/orchestrator/
├── __init__.py
├── coordinator.py        # Agent coordination + task delegation
├── orchestrator.py       # Hierarchical orchestrator
├── delegation.py         # Task delegation protocol
├── consensus.py          # Multi-agent consensus (voting)
├── blackboard.py         # Shared blackboard pattern
└── supervisor.py         # Supervision + error handling
```

**Collaboration Patterns:**

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **Orchestrator** | Central coordinator assigns sub-tasks to agents | Complex multi-step workflows |
| **Debate** | Multiple agents discuss, then vote | High-stakes decisions |
| **Blackboard** | Agents share state via a shared context | Collaborative analysis |
| **Pipeline** | Sequential agent chain (A → B → C) | Data transformation workflows |
| **Hierarchy** | Supervisor agent delegates to specialized agents | Research, competitive analysis |

**Example: Complex Deal Evaluation (Orchestrator + Debate)**

```
Orchestrator receives: "Evaluate deal opportunity: ACME Corp, $500K"
    │
    ├──► Research Agent: Gather company intel
    ├──► Relationship Agent: Analyze relationship strength
    ├──► Forecast Agent: Predict close probability
    ├──► Pricing Agent: Recommend pricing strategy
    ├──► Competitor Agent: Competitive landscape
    │
    ▼
Debate phase: Agents review each other's findings
    │
    ▼
Orchestrator produces consolidated evaluation with:
    - Deal score
    - Risk factors
    - Recommended next actions
    - Confidence level
```

**Agent Communication Protocol:**

```
{
  "from_agent": "research",
  "to_agent": "orchestrator",
  "message_type": "result",
  "task_id": "task-123",
  "payload": { ... },
  "confidence": 0.92,
  "sources": [...],
  "trace_id": "trace-abc"
}
```

---

## 15. Implementation Phases

### P0 — Foundation (Sprint 1-2)

| # | Initiative | Effort | Dependencies | Success Criteria |
|---|-----------|--------|-------------|-----------------|
| 1 | Implement Agent Runtime | 2 weeks | None | `runtime/agent_runtime/` functional with lifecycle, tracing, execution |
| 2 | Fill evaluation test_cases | 2 weeks | Domain experts | 50+ golden test cases across all agents |
| 3 | Write backend AI tests | 2 weeks | Agent Runtime | >80% coverage on intelligence module |
| 4 | Embedding Cache | 3 days | None | Cache hit rate >40%, reduced embedding costs |
| 5 | Fix search_companies tool | 2 days | None | Tool returns populated results |

### P1 — Quality (Sprint 3-4)

| # | Initiative | Effort | Dependencies | Success Criteria |
|---|-----------|--------|-------------|-----------------|
| 6 | Anthropic provider | 1 week | Provider protocol | Switchable provider via config, parity on all agents |
| 7 | PGVector migration | 1 week | DB migration plan | `VECTOR(n)` type in production with HNSW index |
| 8 | Agent observability | 1 week | Agent Runtime | Tracing spans on all agent executions, Grafana dashboard |
| 9 | Multi-provider router | 3 days | Anthropic provider | Query routing by complexity, cost tracking per provider |
| 10 | Hybrid RAG | 1 week | PGVector | Combined vector + BM25 retrieval with RRF |
| 11 | Evaluation runner | 1 week | Test cases | Automated daily runs, report generation |
| 12 | Input/Output guardrails | 1 week | None | PII redaction, grounding check, jailbreak detection |

### P2 — Advanced (Sprint 5-6)

| # | Initiative | Effort | Dependencies | Success Criteria |
|---|-----------|--------|-------------|-----------------|
| 13 | Local KSA provider | 2 weeks | Provider protocol | On-prem model running, Arabic support verified |
| 14 | Multi-agent orchestration | 2 weeks | Agent Runtime | 3+ collaboration patterns operational |
| 15 | Data Fabric real connectors | 2 weeks | Data source contracts | 3+ real connectors replacing mock data |
| 16 | Planning engine | 2 weeks | Agent Runtime | Plan-execute-observe loop operational |
| 17 | Memory system | 1 week | Agent Runtime | Multi-tier memory with episodic → semantic consolidation |
| 18 | Proactive Copilot | 2 weeks | Agent Runtime + NBA | Event-driven copilot notifications |
| 19 | Decision ensemble | 1 week | Multi-provider | Multi-provider voting for high-stakes decisions |

---

## 16. AI Testing Strategy

### Current State: Critical Gap

- **Zero backend AI tests** — no tests for intelligence module, agents, RAG, Data Fabric AI
- **domains/ai/ has 92% coverage** — but that's the domain layer, not the intelligence/agents layer
- **No golden datasets** — evaluation test_cases/ is empty

### Target: 85% Coverage on AI Platform

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `intelligence/agents/` | 0% | 85% | P0 |
| `intelligence/prompts/` | 0% | 100% (schema validation) | P0 |
| `intelligence/reasoning.py` | 0% | 90% | P0 |
| `intelligence/guardrails.py` | 0% | 90% | P0 |
| `intelligence/grounding.py` | 0% | 85% | P1 |
| `intelligence/rag/` | 0% | 85% | P0 |
| `intelligence/arabic/` | 0% | 85% | P1 |
| `intelligence/evaluation/` | 0% | 80% | P1 |
| `intelligence/graph/` | 0% | 70% | P2 |
| `intelligence/memory/` | N/A | 85% | When implemented |
| `intelligence/providers/` | N/A | 85% | When implemented |
| `runtime/agent_runtime/` | N/A | 85% | When implemented |
| `runtime/planning/` | N/A | 80% | When implemented |
| `domains/ai/` | 92% | 95% | P1 |

### Testing Approach

**Unit Tests** (80% of AI tests):
- Agent input/output validation
- Prompt template rendering with valid + invalid variables
- Provider response parsing
- Guardrail rule evaluation
- Embedding cache hit/miss behavior
- Arabic NLP component correctness
- Each test must be deterministic and <1s

**Integration Tests** (15% of AI tests):
- Agent Runtime lifecycle (register → execute → complete)
- Provider switching (OpenAI → Anthropic, same prompt)
- RAG pipeline end-to-end (chunk → embed → retrieve → generate)
- Memory persistence and retrieval
- Multi-agent coordination patterns

**Evaluation Tests** (5% of AI tests):
- Golden dataset evaluation on every CI run
- Regression detection: track metrics over time, alert on degradation
- Cross-provider comparison: same test case, different providers → compare quality

**Critical Testing Rules** (ENGINEERING_CONSTITUTION compliance):

1. **No real API calls in unit tests** — all provider calls must be mocked
2. **Deterministic RNG** — seed all random operations for reproducible tests
3. **Test isolation** — no shared state between tests
4. **Fast feedback** — unit test suite for AI must complete in <30s
5. **Cost tracking** — tests verify cost_tracker accuracy without incurring real costs

**Test Doubles Strategy:**

| Component | Test Double | Method |
|-----------|-------------|--------|
| LLM Provider | Mock provider | Returns configurable responses |
| Embedding Model | Mock embedder | Returns deterministic vectors |
| Vector Database | InMemoryVectorStore | Thread-safe list of vectors |
| Knowledge Graph | InMemoryGraphStore | Dict-based graph |
| Data Fabric | Mock connectors | Returns fixture data |
| Agent Runtime | InMemoryRuntime | In-process execution |
| Memory Store | InMemoryMemoryStore | Dict-based storage |

**CI/CD Integration:**

```
Commit → 
  ├── pytest intelligence/ --fast        # Unit tests (no provider calls)
  ├── pytest intelligence/ --integration  # Integration tests with mocks
  └── pytest evaluation/ --eval          # Evaluation on golden dataset
                                            ↓
                                    Report: pass/fail + metric deltas
```

---

## Appendix A: Audit Cross-Reference

| Finding | Section | P0? |
|---------|---------|-----|
| 15 specialized agents exist | §2 | — |
| Agent Runtime is placeholder | §2, §15 | P0 |
| Zero backend AI tests | §16 | P0 |
| Evaluation test_cases empty | §12 | P0 |
| Only OpenAI supported | §11 | P1 |
| No embedding cache | §10 | P0 |
| No agent observability | §2, §15 | P1 |
| Data Fabric connectors return mock data | §5, §15 | P2 |
| search_companies tool returns empty | §9 | P0 |
| vectors table uses ARRAY(FLOAT) | §5, §15 | P1 |
| Decision Runtime fully implemented | §8 | — |
| NBA Reasoner fully implemented | §6 | — |
| Frontend Agent SDK strong | §2 | — |
| Frontend Decision Platform strong | §8 | — |
| Arabic NLP module exists | §13 | — |
| Graph intelligence module exists | §5 | — |
| Domains/ai at 92% coverage | §16 | — |
| Prompt registry with YAML | §3 | — |
| Guardrails/grounding exist | §13 | — |
| Cost tracker exists | §11 | — |
| MCP Server exists | §2 | — |

---

## Appendix B: Key Performance Indicators

| KPI | Current | P0 Target | P1 Target | P2 Target |
|-----|---------|-----------|-----------|-----------|
| Backend AI test coverage | 0% | 30% | 60% | 85% |
| Evaluation test cases | 0 | 50+ | 100+ | 200+ |
| AI response P95 latency | Unknown | <5s | <3s | <2s |
| Cost per query | Unknown | <$0.10 | <$0.05 | <$0.03 |
| Embedding cache hit rate | 0% | 40% | 50% | 60% |
| Arabic NLP accuracy | Unknown | 85% | 90% | 95% |
| Agent runtime uptime | 0% (not implemented) | 99% | 99.5% | 99.9% |
| Provider availability | 95% (single) | 95% | 99.5% (multi) | 99.9% (multi+fallback) |
| Multi-agent workflows | 0 | 0 | 3 patterns | 5 patterns |
| Data Fabric real connectors | 0 | 0 | 1 | 3+ |
| Guardrail pass rate | Unknown | 99% | 99.5% | 100% |
