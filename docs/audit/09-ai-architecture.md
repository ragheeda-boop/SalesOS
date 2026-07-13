# SalesOS — AI/ML Architecture Audit Report

> **Audit Date:** 2026-07-13
> **Auditor:** AI Architect
> **Scope:** Full reverse-engineering audit of all AI/ML layers
> **Status:** READ-ONLY — Findings & Observations

---

## Executive Summary

SalesOS implements a **layered AI intelligence architecture** with 7 distinct layers:

1. **Data Fabric** — Connector → Identity Resolution → Entity Matching → Data Quality
2. **Company Intelligence** — Unified Business Object model with multi-source enrichment
3. **Intelligence Graph** — Network of relationships between business objects
4. **Signal & Recommendation Engine** — Buying signals → Recommendations → Actions
5. **Agent Runtime** — 11 specialized AI agents coordinated by AgentCoordinator
6. **Decision Platform** — NBA Engine, Recommendation Runtime, Rule Engine
7. **RAG Pipeline** — Chunking → Embedding → Retrieval → Generation

**Overall Assessment:** The architecture is well-designed with a strong foundation but exhibits significant gaps between documented intent and actual implementation. The intelligence layer (`backend/intelligence/`) is comprehensive in design but many components run with mock data or in-memory stores. The Decision Platform in TypeScript comes closer to production readiness.

---

## 1. Complete AI Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                           │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │  Company      │  │  Market      │  │  Revenue Brain    │    │
│  │  Intelligence │  │  Intelligence│  │  (Layer 6)        │    │
│  │  Engine       │  │  Engine      │  │                   │    │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬─────────┘    │
│         │                 │                    │               │
│  ┌──────▼─────────────────▼────────────────────▼─────────┐    │
│  │            SIGNAL ENGINE (Layer 4a)                    │    │
│  │  12 Signal Types → 7 Recommendation Categories        │    │
│  │  Weighted signal detection + Context boosting         │    │
│  └────────────────────────┬─────────────────────────────┘    │
│                           │                                    │
│  ┌────────────────────────▼─────────────────────────────┐    │
│  │         DIGITAL TWIN ENGINE (Layer 4b)                │    │
│  │  CompanyTwin → State Machine → Performance Analysis  │    │
│  └────────────────────────┬─────────────────────────────┘    │
│                           │                                    │
│  ┌────────────────────────▼─────────────────────────────┐    │
│  │      SIMULATION ENGINE (Layer 4c)                     │    │
│  │  7 Scenario Types → ScenarioResult → DecisionIntel   │    │
│  └───────────────────────┬──────────────────────────────┘    │
│                          │                                     │
│  ┌───────────────────────▼──────────────────────────────┐    │
│  │            DATA FABRIC (Layer 4)                      │    │
│  │  Connectors → Resolution → Matching → Quality → Trust │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐    │
│  │        RELATIONSHIP GRAPH SERVICE (In-Memory BFS)     │    │
│  │  Path Finding, Connection Suggestions, Ego Network   │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐    │
│  │           AGENT RUNTIME (Layer 5)                     │    │
│  │  11 Agents + Coordinator + GroundedBaseAgent          │    │
│  │  Prompt Registry (YAML) + Output Schema Validation    │    │
│  └───────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                                 │
│                                                                │
│  ChunkingService    →  EmbeddingService   →  RetrievalService  │
│  (3 strategies)         (OpenAI API)          (pgvector + FTS) │
│                                                                │
│  fixed_size / semantic / hybrid                                │
│  512 tokens / 128 overlap                                      │
│  Arabic-aware tokenization                                     │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    SEARCH DOMAIN                                │
│                                                                │
│  HybridSearchEngine (RRF k=60)                                 │
│  ┌──────────┐    ┌──────────────┐                             │
│  │ Full-Text │    │   Semantic   │                             │
│  │ (tsvector)│    │ (pgvector)   │                             │
│  └────┬─────┘    └──────┬───────┘                             │
│       └────────┬────────┘                                      │
│          ┌─────▼─────┐                                         │
│          │ RRF Fusion │                                         │
│          └─────┬─────┘                                         │
│          ┌─────▼─────┐                                         │
│          │ Ranked List│                                         │
│          └───────────┘                                         │
│                                                                │
│  Ranking Pipeline (composable stages):                         │
│  ExactMatch → PartialMatch → Freshness → TenantWeight         │
│                                                                │
│  Vector Stores: InMemoryVectorStore (dev) / PgVectorStore (prod)│
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│              NBA ENGINE + DECISION PLATFORM                     │
│                                                                │
│  NBA Pipeline (runtime/nba_engine/):                           │
│  1. Normalize (load opp + company context)                     │
│  2. Business Rules (stage-based, stagnation)                   │
│  3. Scoring (deal value + stage + engagement)                  │
│  4. AI Reasoning (NBAReasoner — optional, LLM-based)           │
│  5. Risk Assessment (stagnation detection)                     │
│  6. Recommendation Building                                    │
│                                                                │
│  Recommendation Templates (5 built-in):                        │
│  high_intent, funding_trigger, hiring_surge, renewal_risk,     │
│  expansion_potential                                           │
│                                                                │
│  Decision Feedback Loop:                                       │
│  Decision → Accepted/Rejected → Executed → Outcome → Learning │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. LLM Providers & Model Configuration

### 2.1 Provider Architecture

| Component | File | Description |
|-----------|------|-------------|
| `LLMService` | `intelligence/agents/llm.py:17` | Primary LLM abstraction; wraps `openai.AsyncOpenAI` |
| `OpenAIProvider` | `intelligence/providers/openai_provider.py:8` | Full provider with `chat()` + `embed()` |
| `ProviderFactory` | `intelligence/providers/factory.py:11` | Registry: `{"openai": OpenAIProvider}` |
| `LLMProvider` (Protocol) | `intelligence/providers/base.py:37` | Abstract interface for chat + embed |
| `AIProvider` (ABC) | `domains/ai/service.py:16` | Abstract `generate()` interface |
| `OpenAIProvider` (domains) | `domains/ai/service.py:22` | Domain-layer OpenAI provider; default model `gpt-4o` |
| `DecisionPlatformProvider` | `domains/ai/service.py:55` | Wraps Decision Engine as AI provider |

### 2.2 Configured Models

| Model | Cost/1K Input | Cost/1K Output | Purpose |
|-------|--------------|---------------|---------|
| `gpt-4o-mini` | $0.00015 | $0.00060 | Default model for agents, simple queries |
| `gpt-4o` | $0.0025 | $0.010 | Complex reasoning (AIService domains/ai) |
| `gpt-4-turbo` | $0.01 | $0.03 | Registered but unused |
| `gpt-3.5-turbo` | $0.0005 | $0.0015 | Registered but unused |
| `text-embedding-3-large` | $0.00013 | — | Embeddings for RAG + Search (3072 dims) |
| `text-embedding-3-small` | $0.00002 | — | Cataloged as M-003 (1536 dims) |

**Model selection rules** (from `AI_CATALOG.md:21-28`):
- Simple queries → `gpt-4o-mini`
- Complex reasoning → `gpt-4o`
- Arabic understanding → `gpt-4o`
- Embeddings → `text-embedding-3-small` (default) / `text-embedding-3-large` (Company DNA)

### 2.3 Fallback Strategy

- **No OpenAI key configured** → Agents return low-confidence fallback responses with Arabic message: `"ييتطلب تكوين مفتاح OpenAI"`
- **Embedding API failure** → Returns `None` / empty list; search degrades to full-text only
- **RetrievalService pgvector unavailable** → Falls back to in-memory `_fallback_store`
- **OpenAI unavailable** → `LLMService.chat()` returns empty `LLMResponse` with `finish_reason="error"`
- **NBA AI Reasoning failure** → Falls back to rule-only mode (`agent_base.py:90`)
- **Circuit Breaker** (enrichment only): 3 failures → 60s cooldown (`enrichment/__init__.py:49-51`)
- **Planned fallback**: Claude 3.5 Sonnet (`M-005`) — not yet configured

### 2.4 SDK Configuration

Model, temperature, and max_tokens are configured via `sdk.config.sdk_settings`:
- `sdk_settings.openai_model` — default model
- `sdk_settings.openai_api_key` — API key
- `sdk_settings.llm_temperature` — default temperature
- `sdk_settings.llm_max_tokens` — default max tokens
- `sdk_settings.llm_research_max_tokens` — special limit for research agent

---

## 3. Agent Catalog

### 3.1 Agent Registry

All agents live in `intelligence/agents/` and extend `BaseAgent` (`intelligence/agents/base.py:39`).

| # | Agent | Class | File | Purpose | Prompt | Output Schema | Status |
|---|-------|-------|------|---------|--------|--------------|--------|
| 1 | **Research** | `ResearchAgent` | `agents/research.py:6` | Researches companies, markets, topics; generates Arabic analysis | `research_summary` | `ResearchSummary` | In-memory only |
| 2 | **News** | `NewsAgent` | `agents/news.py:5` | Monitors news for companies & industries | `news_monitoring` | `NewsSummary` | No live API |
| 3 | **Proposal** | `ProposalAgent` | `agents/proposal.py:5` | Generates business proposals in Arabic | `proposal_generation` | `ProposalContent` | LLM dependent |
| 4 | **Contract** | `ContractAgent` | `agents/contract.py:5` | Reviews & analyzes commercial contracts | `contract_review` | `ContractReview` | LLM dependent |
| 5 | **Meeting** | `MeetingAgent` | `agents/meeting.py:5` | Prepares meeting agendas & talking points | `meeting_preparation` | `MeetingPreparation` | LLM dependent |
| 6 | **Pricing** | `PricingAgent` | `agents/pricing.py:5` | Analyzes pricing strategies & market positioning | `pricing_analysis` | `PricingAnalysis` | LLM dependent |
| 7 | **Forecast** | `ForecastAgent` | `agents/forecast.py:5` | Revenue forecasts from pipeline signals | `forecast_analysis` | `ForecastAnalysis` | LLM dependent |
| 8 | **Renewal** | `RenewalAgent` | `agents/renewal.py:5` | Identifies at-risk accounts; retention strategies | `renewal_risk` | `RenewalRisk` | LLM dependent |
| 9 | **Competitor** | `CompetitorAgent` | `agents/competitor.py:5` | Tracks competitor movements & threats | `competitor_analysis` | `CompetitorAnalysis` | LLM dependent |
| 10 | **Tender** | `TenderAgent` | `agents/tender.py:5` | Monitors & analyzes government tenders | `tender_analysis` | `TenderAnalysis` | LLM dependent |
| 11 | **Relationship** | `RelationshipAgent` | `agents/relationship.py:5` | Maps business networks & decision makers | `relationship_mapping` | `RelationshipMap` | LLM dependent |

### 3.2 Coordinator

`AgentCoordinator` (`agents/coordinator.py:15`) distributes tasks to specialized agents based on keyword matching in the user's goal:

| Trigger | Agents Dispatched |
|---------|------------------|
| "meeting" / "اجتماع" | research → meeting → relationship |
| "proposal" / "عرض" | research → pricing → proposal |
| "contract" / "عقد" | contract → competitor |
| "forecast" / "توقع" | forecast |
| "competitor" / "منافس" | competitor → research |
| "renew" / "تجديد" | renewal → pricing |
| "tender" / "مناقصة" | tender → competitor |
| "news" / "أخبار" | news |
| default (fallback) | research → competitor → relationship |

### 3.3 GroundedBaseAgent

`GroundedBaseAgent` (`agent_base.py:14`) implements the **retrieve-then-generate** pattern:
1. Fetches structured grounding context from PostgreSQL + Neo4j
2. Augments system prompt with retrieved data
3. Enforces JSON output schema validation
4. Falls back gracefully when no LLM or no grounding data available

Confidence scaling: `min(0.3 + evidence_count * 0.05, 0.7)` when output parsing fails.

### 3.4 Agent States & Lifecycle

```
IDLE → RUNNING → COMPLETED / FAILED / BLOCKED
```

- `AgentTask` (`base.py:16`): carries `id`, `agent_type`, `input`, `priority`, `deadline`, `context`
- `AgentResult` (`base.py:27`): carries `task_id`, `success`, `output`, `confidence`, `duration_ms`
- All agents inherit from `BaseAgent`; all run `async _run(task) → AgentResult`
- Task history tracked per agent with stats (total tasks, success rate, avg confidence, avg duration)

---

## 4. Prompt System

### 4.1 Prompt Registry (YAML-based)

**File:** `intelligence/prompts/registry.py` + `intelligence/prompts/agents.yaml`

The YAML registry (`agents.yaml`) contains 11 prompt templates, each versioned:

| Prompt ID | System Prompt | Model | Temp | Output Schema |
|-----------|--------------|-------|------|---------------|
| `competitor_analysis` | Analyst for Saudi market | gpt-4o-mini | 0.3 | `competitor_analysis` |
| `meeting_preparation` | Sales meeting preparation assistant | gpt-4o-mini | 0.4 | `meeting_preparation` |
| `research_summary` | Saudi market sales researcher | gpt-4o-mini | 0.3 | `research_summary` |
| `proposal_generation` | Arabic business proposal expert | gpt-4o-mini | 0.5 | `proposal_content` |
| `contract_review` | Saudi commercial contract advisor | gpt-4o-mini | 0.2 | `contract_review` |
| `pricing_analysis` | Saudi market pricing expert | gpt-4o-mini | 0.2 | `pricing_analysis` |
| `forecast_analysis` | Financial forecasting expert | gpt-4o-mini | 0.2 | `forecast_analysis` |
| `renewal_risk` | Contract renewal risk management | gpt-4o-mini | 0.3 | `renewal_risk` |
| `tender_analysis` | Saudi tender analysis expert | gpt-4o-mini | 0.3 | `tender_analysis` |
| `news_monitoring` | Business news analyst | gpt-4o-mini | 0.4 | `news_summary` |
| `relationship_mapping` | Business relationship mapping expert | gpt-4o-mini | 0.3 | `relationship_map` |

### 4.2 Domain Prompt Registry (Code-based)

**File:** `domains/ai/registry.py`

A second, programmatic `PromptRegistry` exists in the AI domain with:
- Versioned template storage
- Activation/deactivation (`activate()`)
- Domain-based filtering (`list(domain=...)`)
- Used by `AIService` for template-based generation via `POST /ai/generate`

### 4.3 Prompt Versioning

Two parallel versioning systems exist:
1. **Intelligence prompts** — versioned via `agents.yaml` integer version field, loaded by `PromptRegistry` in `intelligence/prompts/registry.py`
2. **AI domain prompts** — versioned via `PromptTemplate.version` string field (`"1.0"`), managed by `domains/ai/registry.py`

These are **NOT synchronized** — they serve different subsystems.

### 4.4 Output Schemas

All output schemas defined in `intelligence/schemas.py` as Pydantic models:

| Schema | Base | Extra Fields |
|--------|------|-------------|
| `AgentAnalysis` | — | analysis, confidence, evidence[], sources[] |
| `CompetitorAnalysis` | AgentAnalysis | competitors[], market_position |
| `MeetingPreparation` | AgentAnalysis | agenda[], talking_points[], decision_makers[] |
| `ProposalContent` | AgentAnalysis | proposal, status |
| `ContractReview` | AgentAnalysis | risks[], recommendations[] |
| `PricingAnalysis` | AgentAnalysis | suggested_price, price_range |
| `ForecastAnalysis` | AgentAnalysis | predicted_revenue, confidence_interval |
| `RenewalRisk` | AgentAnalysis | risk_level, retention_strategies[] |
| `TenderAnalysis` | AgentAnalysis | opportunities[], eligibility |
| `NewsSummary` | AgentAnalysis | articles[] |
| `RelationshipMap` | AgentAnalysis | network[], key_contacts[] |
| `ResearchSummary` | AgentAnalysis | key_facts[], opportunities[], recommendations[] |

Confidence is universally constrained `ge=0, le=1`.

---

## 5. RAG Pipeline Architecture

### 5.1 Pipeline Components

**Files:** `intelligence/rag/`

```
Document → ChunkingService → EmbeddingService → RetrievalService → RagService
```

### 5.2 Chunking (`chunking.py`)

Three chunking strategies:

| Strategy | Method | Use Case |
|----------|--------|----------|
| `fixed_size` | Token-based sliding window | Simple documents |
| `semantic` | Paragraph-boundary aware | Reports, proposals |
| `hybrid` | Semantic boundaries → re-chunked | Default, best for Arabic |

**Defaults:** chunk_size=512 tokens, overlap=128 tokens

Arabic-aware tokenization: detects Arabic script characters (`[\u0600-\u06FF...]`) and switches to word-level tokenization with 20-char fallback for long words.

### 5.3 Embedding (`embeddings.py`)

- **Model:** `text-embedding-3-large` (3072 dimensions) via `EmbeddingConfig`
- **Caching:** SHA-256 hash of text → embedding; in-memory unlimited cache
- **Retry:** 3 attempts with exponential backoff (`2^attempt` seconds)
- **Batch:** Splits into config.batch_size batches, re-orders by index
- **Graceful degradation:** Returns empty list on failure

### 5.4 Retrieval (`retrieval.py`)

Storage: PostgreSQL `rag_documents` + `rag_document_chunks` tables

**Vector Search:**
- pgvector `<=>` operator for cosine similarity
- IVFFlat index with 100 lists
- Embedding column: `vector(3072)`
- Min score filter: 0.7 (configurable)

**Hybrid Retrieval:**
- Weighted blend: `vector_score * 0.7 + text_score * 0.3`
- Uses PostgreSQL `ts_rank` + `plainto_tsquery` for text matching
- Note: Uses `query_text=""` in current implementation (line 136) — **BUG: text component not receiving actual query text**

**Fallback:** In-memory `_fallback_store` dict when pgvector unavailable

### 5.5 Generation (`service.py`)

`RagService.answer()`:
1. Embed question
2. Retrieve top-k chunks (default k=5, min_score=0.7)
3. Build context from chunks
4. Generate answer via LLM with Arabic system prompt
5. Return `RagAnswer` with citations, chunks_used, confidence

`RagService.generate_brief()`:
- Retrieves by source_type + source_id
- Summarizes all chunks for an entity

### 5.6 API Endpoints (`app/routers/rag.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rag/ask` | POST | Q&A with RAG (tenant-scoped) |
| `/rag/ingest` | POST | Ingest a document (chunk + embed + store) |
| `/rag/documents` | GET | List documents for tenant |
| `/rag/documents/{id}` | DELETE | Delete document and chunks |

---

## 6. Embedding Strategy

| Property | Value |
|----------|-------|
| **Primary Model** | `text-embedding-3-large` (OpenAI) |
| **Dimensions** | 3072 |
| **Alternative** | `text-embedding-3-small` (1536 dims) — cataloged, lower cost |
| **Local Fallback** | `all-MiniLM-L6-v2` (384 dims) — referenced but not integrated |
| **Storage** | PostgreSQL `vector(3072)` column + IVFFlat index |
| **Caching** | SHA-256 hash → embedding (in-memory), LRU eviction (search domain: max 1024) |
| **Indexing** | IVFFlat with 100 lists, cosine distance operator `<=>` |
| **Batch Size** | Config-based (search: 256 per API call) |
| **Dual Usage** | Same embeddings serve both RAG pipeline and Hybrid Search |

**Gap:** The AI Catalog documents `text-embedding-3-small` as the default but actual code uses `text-embedding-3-large`.

---

## 7. Knowledge Graph Architecture

### 7.1 Graph Service

**File:** `intelligence/graph/__init__.py`

`RelationshipGraphService` — pure in-memory graph with no Neo4j integration at this level.

| Feature | Implementation |
|---------|---------------|
| Node storage | `dict[str, GraphNode]` (in-memory) |
| Path finding | BFS with max_depth (default 3) |
| Connection suggestions | Shared-neighbor heuristic with strength weighting |
| Mutual connections | Set intersection of neighbor IDs |
| Ego network | BFS traversal to max_degree |

### 7.2 Neo4j Integration

Used in `GroundingService` (`grounding.py:117-132`) for relationship queries:
- Queries `Company` nodes by ID
- Retrieves `related` nodes with edge types and strengths
- Connection handled via `neo4j_driver` parameter

### 7.3 Knowledge Graph Runtime

**File:** `runtime/knowledge_graph_runtime/router.py`

REST API endpoints for graph operations:

| Endpoint | Purpose |
|----------|---------|
| `POST /graph/populate/{company_id}` | Populate graph from golden record |
| `POST /graph/rebuild` | Rebuild entire graph for tenant |
| `GET /graph/competitors/{company_id}` | Find competitors |
| `GET /graph/path` | Shortest path between two entities |
| `GET /graph/network/{company_id}` | Ego network |
| `GET /graph/decision-makers/{company_id}` | Senior contacts |
| `GET /graph/search` | Full-text graph search |
| `GET /graph/query/custom` | Raw graph queries (company/opportunity/contract) |
| `GET /graph/query/companies-without-activity` | Stagnant companies |
| `GET /graph/query/employees-with-most-meetings` | Most-active reps |
| `POST /graph/enrich/{company_id}` | Discover & create relationships |
| `POST /graph/merge-nodes` | Merge graph nodes during entity resolution |
| `GET /graph/subgraph/{entity_id}` | Subgraph by depth |
| `GET /graph/metrics` | Graph engine metrics |

### 7.4 Data Fabric → Graph Integration

`DataFabric` pipeline:
```
Connector sync → Identity Resolution → Entity Matching → Data Quality → Company Engine → Graph
```

Entity relationships are built via `EntityMatcher` matching on: cr_number, vat_number, email, phone, domain, name (fuzzy).

---

## 8. Scoring Engine Architecture

### 8.1 ScoringEngine

**File:** `domains/scoring/engine.py`

Bridges signals from `SignalEngine` to the Decision Platform:

```
Signals → DecisionContext factors → RecommendationEngine → ScoreCard
```

### 8.2 Scoring Dimensions

Six weighted scoring dimensions:

| Dimension | Weight | Signal Types |
|-----------|--------|-------------|
| BUYING_INTENT | 30% | funding, expansion, tender |
| ENGAGEMENT | 20% | hiring, contract |
| FIT | 15% | regulatory |
| URGENCY | 15% | project |
| RELATIONSHIP | 10% | partnership, leadership |
| MARKET_SIGNAL | 10% | merger, competitor_move, news |

### 8.3 Scoring Flow

1. **Signal-to-Factor Conversion:** Raw signals → `DecisionFactor` objects with severity mapping
2. **Context Building:** Factors fed to `DecisionService.build_context()`
3. **Recommendation Evaluation:** `RecommendationEngine.evaluate()` produces recommendation with evidence
4. **Dimension Scoring:** Weighted sum of signal intensities per dimension
5. **Overall Score:** Weighted average across dimensions, capped at 1.0
6. **Confidence Level:** Based on signal count (≥5 = HIGH, ≥2 = MEDIUM, <2 = LOW)

### 8.4 ScoreCard Output

```python
ScoreCard(
    id, tenant_id, target_id, target_type,
    scores=[Score(dimension=..., normalized_score=..., confidence=..., narrative=...)],
    overall_score=float,
    overall_confidence=ConfidenceLevel
)
```

---

## 9. Decision Platform Architecture

### 9.1 NBA Engine

**File:** `runtime/nba_engine/__init__.py` (NBAEngine class)

Full pipeline (6 stages):

| Stage | Function | What It Does |
|-------|----------|-------------|
| 1. Normalize | `_normalize()` | Loads opportunity + company + recent activities from DB |
| 2. Business Rules | `_apply_rules()` | Stage-based actions + stagnation detection (14d threshold) |
| 3. Scoring | `_score_candidates()` | Deal value (25%) + stage score (20%) + engagement (15%) |
| 4. AI Reasoning | `_ai_evaluate()` | Delegates to `NBAReasoner`; **currently returns None** (Sprint 5 pending) |
| 5. Risk Assessment | `_assess_risk()` | Stagnation, competition, engagement drop detection |
| 6. Recommendation | `_build_recommendation()` | Top candidate → NBAResult with evidence, alternatives, impact |

### 9.2 AI Reasoner (`nba_engine/engine/ai/reasoner.py`)

`NBAReasoner` — optional LLM reasoning layer:
- Builds structured JSON prompt with opportunity, company, signals, activities, candidates
- Parses LLM response for ranking, explanation, confidence, risks
- Falls back gracefully when no LLM available
- **Status:** Integrated but `_ai_evaluate()` stubbed to return `None`

### 9.3 Recommendation Runtime

**File:** `runtime/recommendation_runtime/__init__.py`

Turns `DecisionObject` → structured `Recommendation` objects with:
- 5 built-in templates (high_intent, funding_trigger, hiring_surge, renewal_risk, expansion_potential)
- Template matching based on Feature Store scores (intent, funding, hiring, expansion)
- Ordered actions with workflow suggestions
- Status tracking (PENDING → ACTIVE → ACCEPTED/REJECTED → COMPLETED)

### 9.4 Decision Runtime

**File:** `runtime/decision_runtime/`

REST API for the decision engine:
- `POST /decision/evaluate` — Evaluate company, return NBA
- `GET /decision/next-best-action` — Get highest-priority decision
- `GET /decisions/history` — Decision timeline for company
- `POST /decisions/{id}/accept` — Accept a decision
- `POST /decisions/{id}/execute` — Execute a decision
- `POST /decisions/{id}/feedback` — Submit feedback on decision
- `GET /decisions/{id}/reasoning` — Explainability
- `GET /decision/metrics` — Engine metrics

### 9.5 Rule Engine (TypeScript)

**File:** `docs/RULE_ENGINE_GUIDE.md`

7 built-in rules:
- `rule_expired_license` (risk, priority 90)
- `rule_no_decision_maker` (risk, priority 80)
- `rule_low_confidence` (warning, priority 60)
- `rule_high_revenue` (opportunity, priority 85)
- `rule_government_tender` (strategic, priority 75)
- `rule_high_hiring_growth` (intent, priority 70)
- `rule_relationship_strength` (relationship, priority 65)

### 9.6 Feedback Loop

**File:** `runtime/decision_runtime/feedback_loop.py`

Tracks the full decision lifecycle:
```
Decision → Accepted/Rejected → Executed → Outcome (Won/Lost/Pending) → Learning
```

Data stored in `decision_feedback_loop` table for future ML model training.

---

## 10. Company Intelligence Pipeline

### 10.1 Business Object Model

**File:** `intelligence/business_objects/__init__.py`

Every entity is a `BusinessObject` with 7 facets:

| Facet | Component | Purpose |
|-------|-----------|---------|
| Identity | `ObjectIdentity` | Immutable core (id, entity_type, external_ids) |
| Profile | `ObjectProfile` | Mutable data (name_ar, name_en, website, etc.) |
| Signals | `ObjectSignal[]` | Detected buying signals |
| Graph | `ObjectGraph` | Relationship graph |
| Knowledge | `ObjectKnowledge` | Aggregated insights (summary, key_facts, events) |
| AI | `ObjectAI` | AI-generated insights (sentiment, risk, confidence) |
| Recommendations | `ObjectRecommendations` | NBAs, priorities, risks, opportunities |

**Entity Types:** COMPANY, DEAL, CONTACT, MEETING, SUPPLIER, PROJECT, OPPORTUNITY, CAMPAIGN, DOCUMENT, PRODUCT, TASK

### 10.2 Data Fabric

**File:** `intelligence/data_fabric/`

End-to-end data pipeline:

```
ConnectorEngine → IdentityResolver → EntityMatcher → DataQualityEngine → CompanyIntelligenceEngine
```

| Component | File | Function |
|-----------|------|----------|
| `ConnectorEngine` | `connectors.py` | 10 built-in connectors (Gmail, HubSpot, Odoo, SAP, Slack, etc.) |
| `IdentityResolver` | `identity_resolution.py` | Resolves fragments into unified identities via CR number, VAT, domain, name |
| `EntityMatcher` | `entity_matching.py` | Links entities across types; exact (0.85+) vs fuzzy matching |
| `DataQualityEngine` | `quality.py` | 5-dim quality: Completeness, Accuracy, Consistency, Freshness, Uniqueness |
| `DataFabric` | `fabric.py` | Orchestrator: runs full pipeline, computes data health |

**Source Reliability Weights:** government (0.95) > manual (0.90) > ERP (0.85) > CRM (0.80) > LinkedIn (0.70) > website (0.60) > news (0.50) > enrichment_api (0.40)

### 10.3 Enrichment Service

**File:** `intelligence/enrichment/__init__.py`

Three parallel enrichment sources:

1. **DB Query** — Fetches company details from PostgreSQL
2. **Balady Scraper** — Government registry scraper with circuit breaker
3. **Feature Store** — Retrieves computed features

Includes: 24h cache TTL, circuit breaker (3 failures → 60s cooldown), source priority system, batch enrichment.

### 10.4 Digital Twin

**File:** `intelligence/digital_twin/`

`DigitalTwin` (base) → `CompanyTwin` (specialized)

| Feature | Description |
|---------|-------------|
| State Machine | INITIALIZING → ACTIVE → STALE → SLEEPING → ERROR |
| CompanyState | revenue_trend, hiring_activity, expansion_signals, growth_potential |
| `analyze_performance()` | Computes growth, revenue trend, relationship health from signals |
| `predict_next_quarter()` | Revenue prediction using signals + FeatureStore scores |
| TwinEngine | Manages all twins; health summary across entity types |

### 10.5 Revenue Brain

**File:** `intelligence/revenue_brain/__init__.py`

Highest intelligence layer. Orchestrates all engines:

```
Input: Company Engine + Signal Engine + Market Engine + Graph Service + Enrichment
Output: Forecasts (W/M/Q/Y), ExecutiveDecisions, RevenueInsights
```

Forecast generation uses: signal momentum, hot company momentum, FeatureStore growth scores, DB revenue totals.

---

## 11. AI Evaluation System

### 11.1 Evaluation Framework

**File:** `domains/ai/evaluator.py`

5 built-in evaluation metrics:

| Metric | Function | Description |
|--------|----------|-------------|
| `exact_match` | Output == expected | Exact string comparison |
| `contains_keyword` | Keyword in output | Substring check |
| `length_check` | Min/max length | Output length validation |
| `json_valid` | Valid JSON parse | JSON syntax validation |
| `confidence_threshold` | Confidence ≥ threshold | Check JSON confidence field |

### 11.2 Evaluation Runner

**File:** `intelligence/evaluation/runner.py`

- Loads test cases from YAML files in `test_cases/`
- Measures: Faithfulness, Relevance, Accuracy
- Faithfulness: word overlap between output and source data
- Relevance: keyword match between output and query
- Accuracy: structured checks against expected schema fields
- Pass threshold: faithfulness ≥ 0.6 AND relevance ≥ 0.5 AND accuracy ≥ 0.5

### 11.3 Test Cases

Two YAML test case files:
- `competitor.yaml` — Tests competitor analysis with rich context (contacts, opportunities, signals)
- `meeting.yaml` — Tests meeting preparation with contextual data (company, contacts, activities)

### 11.4 Evaluation Tests

| Test File | Tests |
|-----------|-------|
| `tests/evaluation/test_agent_grounding.py` | Context structure, empty detection, confidence scaling, schema validation |
| `tests/evaluation/test_rag_faithfulness.py` | Hallucination detection, confidence derivation, faithfulness checks |
| `domains/ai/tests/test_evaluator.py` | 13 tests: exact match, keyword, length, JSON, confidence threshold, batch, aggregation |

---

## 12. AI Security

### 12.1 Prompt Injection Protection

**File:** `intelligence/guardrails.py`

**Input Sanitization** (`sanitize_input()`):
- Strips special tokens: `{{`, `}}`, `{%`, `%}`, `<|`, `|>`, `<s>`, `</s>`, `[INST]`, `[/INST]`, `<<SYS>>`, `<</SYS>>`
- Strips Unicode escape sequences (`\uXXXX`, `\xXX`)
- Strips control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F)

**Harmful Pattern Detection** (`add_input_moderation()`):
- 15 regex patterns covering: "ignore previous instructions", "forget previous", "disregard", "system prompt", "you are now", "act as if", "pretend to be", "role-play", "do not follow", "output raw", "print secret/password/key/token", "bypass safety/filter/guardrail/restriction/rule", "jailbreak", "DAN"

**Output Validation** (`validate_output()`):
- Strips markdown code fences
- Validates JSON structure
- Ensures required keys present (analysis/proposal/summary)
- Validates confidence in range [0, 1]

### 12.2 Security Gaps

- Input moderation returns True/False but is not called in any agent code path — **detection exists but enforcement is missing**
- No PII detection in outputs
- No OpenAI Moderation API integration
- No content filtering at output level
- Guardrails are only in Python backend; TypeScript Decision Engine has no injection protection
- No rate limiting on AI endpoints at the application level (though global rate limiting exists)

### 12.3 Architecture Compliance

Per the Engineering Constitution:
- Article 4.1 (no secrets in code): **Compliant** — all secrets in env vars/settings
- Article 4.2 (all endpoints authenticated): **Compliant** — all AI routers require `verify_token`
- Article 4.3 (data encryption): **Compliant** — TLS 1.3 referenced in architecture

---

## 13. AI Technical Debt Register

### Critical (must fix before production AI launch)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| TD-AI-001 | Hybrid search RAG text component uses empty string for text query | `intelligence/rag/retrieval.py:136` | Hybrid retrieval degraded to vector-only |
| TD-AI-002 | Input moderation (`add_input_moderation`) never called in agent paths | `intelligence/guardrails.py:45` | Prompt injection protection not enforced |
| TD-AI-003 | NBA AI reasoning stubbed to `return None` | `runtime/nba_engine/__init__.py:274` | AI reasoning pipeline incomplete |
| TD-AI-004 | All agents run in-memory with no persistence | `intelligence/agents/` | Results lost on restart |
| TD-AI-005 | Connector data is mock/simulated | `intelligence/data_fabric/connectors.py:148` | No real external data imported |

### High

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| TD-AI-006 | Two separate prompt registries not synchronized | `intelligence/prompts/` and `domains/ai/registry.py` | Confusion, drift, duplicated effort |
| TD-AI-007 | No model fallback to Claude 3.5 Sonnet (cataloged but not wired) | `intelligence/providers/factory.py:12` | Single vendor dependency |
| TD-AI-008 | Embedding cache unlimited growth — no eviction | `intelligence/rag/embeddings.py:28` | Memory leak in long-running process |
| TD-AI-009 | Graph service is in-memory only — no Neo4j integration at this layer | `intelligence/graph/__init__.py` | Graph queries use BFS, not Cypher |
| TD-AI-010 | Cost tracking in-memory only — no DB persistence | `intelligence/cost_tracker.py` | Cost data lost on restart |

### Medium

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| TD-AI-011 | SignalEngine stores signals and recommendations in-memory | `intelligence/signals/__init__.py` | Data lost on restart |
| TD-AI-012 | Market Intelligence sources are mock data | `intelligence/market/__init__.py:81` | No real market signals |
| TD-AI-013 | Revenue Brain forecasts use hardcoded base revenue | `intelligence/revenue_brain/__init__.py:189` | Forecasts not production-grade |
| TD-AI-014 | Simulation engine uses simple mathematical models, not ML | `intelligence/simulation/simulation.py` | Limited accuracy |
| TD-AI-015 | TwinEngine and CompanyTwin not persisted | `intelligence/digital_twin/` | State lost on restart |
| TD-AI-016 | No evaluation pipeline for agent quality monitoring | `intelligence/evaluation/` | No continuous eval framework |

### Planned Features (from AI Catalog — all marked "❌ Missing")

| ID | Feature | Priority |
|----|---------|----------|
| F-AI-001 | AI Copilot with tool integration (Search, Timeline, KG, Feature Store) | P1 |
| F-AI-002 | Scoring Agent with Feature Store integration | P2 |
| F-AI-003 | Risk Detection Agent with pattern memory | P2 |
| F-AI-004 | Recommendation Agent with user memory | P1 |
| F-AI-005 | Data Quality Agent with Entity Resolution | P2 |
| F-AI-006 | Semantic cache for embeddings | P2 |
| F-AI-007 | LLM-as-judge hallucination detection | P2 |
| F-AI-008 | Per-tenant budget enforcement | P1 |
| F-AI-009 | Automated evaluation pipeline (monthly) | P3 |
| F-AI-010 | OpenAI Moderation API integration | P2 |

---

## 14. Cost Tracking & Optimization

### 14.1 CostTracker

**File:** `intelligence/cost_tracker.py`

- Tracks token usage per model
- Estimates cost per call using per-model rates
- Supports per-tenant budget enforcement (in-memory)
- Budget exceeded flag available via `is_budget_exceeded()`

### 14.2 Model Cost Rates

| Model | Input/1K tokens | Output/1K tokens |
|-------|----------------|-----------------|
| gpt-4o-mini | $0.00015 | $0.00060 |
| gpt-4o | $0.0025 | $0.010 |
| gpt-4-turbo | $0.01 | $0.03 |
| gpt-3.5-turbo | $0.0005 | $0.0015 |
| text-embedding-3-large | $0.00013 | $0.00 |

### 14.3 Optimization Opportunities

- Embedding cache reduces API calls for repeated texts
- Batch embedding (256 per API call) reduces round-trips
- No semantic caching for LLM responses (planned but not implemented)
- No token budgeting at query level (tracked but not enforced)

---

## 15. System Architecture Diagram (Full Stack)

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTERFACES                          │
│  REST API (FastAPI)  │  Copilot  │  RAG API  │  Search API     │
│  Decision API        │  KG API   │  AI API   │                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    AGENT COORDINATOR                             │
│  Research │ News │ Proposal │ Contract │ Meeting │ Pricing      │
│  Forecast │ Renewal │ Competitor │ Tender │ Relationship       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 GROUNDED BASE AGENT                              │
│  GroundingService ← PostgreSQL + Neo4j ← AgentContext           │
│  Guardrails: sanitize_input + validate_output                   │
│  Schema validation: Pydantic output schemas                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    INTELLIGENCE LAYER                            │
│                                                                │
│  Revenue Brain ─── $ Intelligence Executive                    │
│       │                                                         │
│  ┌────┼──────────────────────────────┐                         │
│  │    ├── Signal Engine              │                         │
│  │    ├── Market Intelligence        │                         │
│  │    ├── Simulation Engine          │                         │
│  │    ├── Digital Twin               │                         │
│  │    └── Relationship Graph         │                         │
│  └───────────────────────────────────┘                         │
│       │                                                         │
│  ┌────▼──────────────────────────────┐                         │
│  │    DATA FABRIC                     │                         │
│  │    Connectors → Identity → Match   │                         │
│  │    → Quality → Trust → KG          │                         │
│  └───────────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                                  │
│  Document → Chunk (512) → Embed (3072) → Store (pgvector)       │
│  Query → Embed → Retrieve (cosine) → Generate (LLM)             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│        DECISION PLATFORM (NBA + Recommendation + Decision)     │
│  Signal → NBA Pipeline → Recommendation → Decision → Feedback  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SEARCH ENGINE                                 │
│  Full-Text (tsvector) + Semantic (pgvector) → RRF Fusion        │
│  Ranking: ExactMatch + PartialMatch + Freshness                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 16. Summary & Recommendations

### Strengths
1. **Layered Architecture**: Well-structured intelligence layer with clear separation of concerns
2. **Arabic-Native Design**: All prompts, schemas, and outputs in Arabic; Arabic-aware tokenization
3. **Graceful Degradation**: Every component falls back gracefully when LLM/DB unavailable
4. **Retrieve-Then-Generate**: GrounderBaseAgent enforces data-first before any LLM generation
5. **Evaluation Framework**: Built-in metrics and test cases for AI quality monitoring
6. **RAG Pipeline**: Complete chunking → embedding → retrieval → generation with hybrid search
7. **Feedback Loop**: Decision → outcome → learning pipeline designed for future ML

### Critical Gaps
1. **Mock Data Dominance**: Connectors, Market Intelligence, and Simulation use mock/simulated data
2. **In-Memory State**: Agent history, signal store, graph service, and cost tracking are not persisted
3. **Dual Registries**: Two parallel prompt registries need unification
4. **AI Pipeline Incomplete**: NBA AI reasoning stubbed; agents have no tool integration
5. **Security Enforcement Gap**: Prompt injection detection exists but is not called in agent code paths
6. **No Real-Time Signals**: Market monitoring uses mock data; no integration with news APIs, government portals

### Priority Actions
1. Wire `add_input_moderation()` into agent execution paths
2. Complete NBA AI Reasoning pipeline (NBAReasoner is built but unused)
3. Persist agent results and signal stores to PostgreSQL
4. Integrate real connector data sources (Odoo MCP, government portal)
5. Unify the two prompt registries
6. Migrate SignalEngine from in-memory to database-backed
7. Implement semantic cache for LLM responses
8. Add per-tenant budget enforcement with DB persistence

---

*End of AI Architecture Audit*
