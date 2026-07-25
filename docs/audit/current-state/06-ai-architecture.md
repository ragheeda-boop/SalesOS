# 06 — AI Architecture Audit

> **Audit Date:** 2026-07-15
> **Scope:** All AI-related code across backend intelligence, agents, RAG, providers, guardrails, evaluation, runtime, MCP server, and frontend agent SDK.
> **Status Legend:** ✅ Implemented · 🔧 Partial · 🔲 Placeholder · ❌ Not Started

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Backend Intelligence Module](#2-backend-intelligence-module)
3. [Agent System](#3-agent-system)
4. [LLM Providers](#4-llm-providers)
5. [Prompt Registry](#5-prompt-registry)
6. [RAG Pipeline](#6-rag-pipeline)
7. [Guardrails & Safety](#7-guardrails--safety)
8. [Cost Tracking](#8-cost-tracking)
9. [Reasoning Pipeline](#9-reasoning-pipeline)
10. [Grounding Service](#10-grounding-service)
11. [Arabic NLP](#11-arabic-nlp)
12. [Evaluation Framework](#12-evaluation-framework)
13. [Graph Intelligence](#13-graph-intelligence)
14. [Signal Engine](#14-signal-engine)
15. [Market Intelligence](#15-market-intelligence)
16. [Revenue Brain](#16-revenue-brain)
17. [Digital Twin](#17-digital-twin)
18. [Simulation Engine](#18-simulation-engine)
19. [Data Fabric](#19-data-fabric)
20. [Domain AI Layer](#20-domain-ai-layer)
21. [REST API Layer](#21-rest-api-layer)
22. [MCP Server](#22-mcp-server)
23. [Runtime — Decision Intelligence](#23-runtime--decision-intelligence)
24. [Runtime — NBA AI Reasoner](#24-runtime--nba-ai-reasoner)
25. [Runtime — Agent Runtime](#25-runtime--agent-runtime)
26. [Frontend Agent SDK](#26-frontend-agent-sdk)
27. [Dependencies Matrix](#27-dependencies-matrix)
28. [Test Coverage](#28-test-coverage)
29. [Architecture Diagram](#29-architecture-diagram)
30. [Gaps & Recommendations](#30-gaps--recommendations)

---

## 1. System Overview

SalesOS AI architecture is a multi-layered system spanning backend intelligence services, a provider abstraction, a RAG pipeline, an agent framework, decision intelligence runtime, and a frontend agent SDK. The system is designed for B2B CRM intelligence with Arabic-first NLP support.

### High-Level Layers

| Layer | Responsibility | Location |
|-------|---------------|----------|
| **Intelligence Core** | Agent base, schemas, reasoning, guardrails, grounding, cost tracking | `backend/intelligence/` |
| **Agent System** | 11 specialized agents + coordinator + LLM service | `backend/intelligence/agents/` |
| **Provider Abstraction** | LLM provider interface + OpenAI implementation | `backend/intelligence/providers/` |
| **Prompt Registry** | Versioned YAML prompt templates with A/B testing | `backend/intelligence/prompts/` |
| **RAG Pipeline** | Chunking → Embeddings → Retrieval → Answer generation | `backend/intelligence/rag/` |
| **Arabic NLP** | Preprocessing, stemming, NER, quality scoring | `backend/intelligence/arabic/` |
| **Evaluation** | Faithfulness, relevance, accuracy metrics | `backend/intelligence/evaluation/` |
| **Graph Intelligence** | Relationship graph traversal | `backend/intelligence/graph/` |
| **Signal Engine** | Buying signals + recommendations | `backend/intelligence/signals/` |
| **Market Intelligence** | Market analysis engine | `backend/intelligence/market/` |
| **Revenue Brain** | Forecasting + executive decisions | `backend/intelligence/revenue_brain/` |
| **Digital Twin** | Company digital twin simulation | `backend/intelligence/digital_twin/` |
| **Simulation** | Scenario simulation engine | `backend/intelligence/simulation/` |
| **Data Fabric** | Connectors, identity resolution, entity matching, quality | `backend/intelligence/data_fabric/` |
| **Domain AI** | Domain-layer AI service, evaluator, registry | `backend/domains/ai/` |
| **REST API** | AI, Copilot, RAG endpoints | `backend/app/routers/` |
| **MCP Server** | MCP protocol server for AI agent tools | `backend/mcp_server/` |
| **Runtime** | Decision intelligence + NBA reasoner + agent runtime | `backend/runtime/` |
| **Frontend SDK** | Agent contracts, registry, orchestrator, memory, tools, RAG | `frontend/packages/platform/agents/` |

---

## 2. Backend Intelligence Module

### `intelligence/__init__.py`
- **Path:** `backend/intelligence/__init__.py`
- **Purpose:** Package root — exports all sub-modules
- **Status:** ✅ Implemented
- **Exports:** AgentBase, schemas, reasoning, guardrails, grounding, cost_tracker, signals, graph, market, revenue_brain, digital_twin, simulation, data_fabric

### `intelligence/agent_base.py`
- **Path:** `backend/intelligence/agent_base.py`
- **Purpose:** Abstract base class for all AI agents
- **Status:** ✅ Implemented
- **Key Classes:** `AgentBase`
- **Key Methods:** `execute()`, `validate_input()`, `format_output()`
- **Dependencies:** None (pure Python ABC)

### `intelligence/schemas.py`
- **Path:** `backend/intelligence/schemas.py`
- **Purpose:** Pydantic models for all intelligence data structures
- **Status:** ✅ Implemented
- **Key Classes:** Multiple Pydantic models for agent inputs/outputs, signals, recommendations
- **Dependencies:** `pydantic`

---

## 3. Agent System

### Agent Architecture

All agents inherit from `AgentBase` and are coordinated by `AgentCoordinator`. The LLM service provides the inference layer.

| Agent | Path | Purpose | Status | Tests |
|-------|------|---------|--------|-------|
| **Base Agent** | `intelligence/agents/base.py` | Abstract base with `execute()`, `validate_input()`, `format_output()` | ✅ | — |
| **LLM Service** | `intelligence/agents/llm.py` | LLM inference via provider abstraction | ✅ | — |
| **Coordinator** | `intelligence/agents/coordinator.py` | Multi-agent orchestration, task routing | ✅ | — |
| **Research Agent** | `intelligence/agents/research.py` | Company research & analysis | ✅ | — |
| **News Agent** | `intelligence/agents/news.py` | News monitoring & alerts | ✅ | — |
| **Proposal Agent** | `intelligence/agents/proposal.py` | Proposal generation | ✅ | — |
| **Contract Agent** | `intelligence/agents/contract.py` | Contract analysis | ✅ | — |
| **Meeting Agent** | `intelligence/agents/meeting.py` | Meeting prep & follow-up | ✅ | — |
| **Pricing Agent** | `intelligence/agents/pricing.py` | Pricing optimization | ✅ | — |
| **Forecast Agent** | `intelligence/agents/forecast.py` | Revenue forecasting | ✅ | — |
| **Renewal Agent** | `intelligence/agents/renewal.py` | Renewal management | ✅ | — |
| **Competitor Agent** | `intelligence/agents/competitor.py` | Competitive intelligence | ✅ | — |
| **Tender Agent** | `intelligence/agents/tender.py` | Tender analysis | ✅ | — |
| **Relationship Agent** | `intelligence/agents/relationship.py` | Relationship intelligence | ✅ | — |

### Agent Coordinator
- **Path:** `intelligence/agents/coordinator.py`
- **Purpose:** Routes tasks to appropriate agents, manages multi-agent workflows
- **Status:** ✅ Implemented
- **Key Methods:** `coordinate()`, `route_task()`, `get_agent()`

### LLM Service
- **Path:** `intelligence/agents/llm.py`
- **Purpose:** Wraps provider abstraction for agent use
- **Status:** ✅ Implemented
- **Dependencies:** Provider factory

---

## 4. LLM Providers

### Provider Abstraction

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Base Provider** | `intelligence/providers/base.py` | Abstract interface for LLM providers | ✅ Implemented |
| **OpenAI Provider** | `intelligence/providers/openai_provider.py` | OpenAI GPT integration | ✅ Implemented |
| **Provider Factory** | `intelligence/providers/factory.py` | Factory pattern for provider creation | ✅ Implemented |

### OpenAI Provider Details
- **Path:** `intelligence/providers/openai_provider.py`
- **Purpose:** OpenAI API integration (GPT-4, GPT-3.5)
- **Status:** ✅ Implemented
- **Key Classes:** `OpenAIProvider`
- **Key Methods:** `generate()`, `embed()`, `chat()`
- **Dependencies:** `openai` SDK, API key from env
- **Models Used:** `gpt-4`, `gpt-3.5-turbo`, `text-embedding-3-large`
- **Rate Limiting:** Via `tenacity` retry logic
- **Cost Tracking:** Integrated with `CostTracker`

### Provider Factory
- **Path:** `intelligence/providers/factory.py`
- **Purpose:** Creates provider instances based on config
- **Status:** ✅ Implemented
- **Key Classes:** `ProviderFactory`
- **Key Methods:** `create_provider()`, `get_provider()`
- **Supported Providers:** OpenAI only (extensible via interface)

---

## 5. Prompt Registry

### Prompt Management

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Prompt Registry** | `intelligence/prompts/registry.py` | Versioned YAML prompt templates | ✅ Implemented |
| **Domain Registry** | `domains/ai/registry.py` | Domain-layer prompt registry | ✅ Implemented |

### Prompt Registry Details
- **Path:** `intelligence/prompts/registry.py`
- **Purpose:** Load, version, and manage prompt templates from YAML files
- **Status:** ✅ Implemented
- **Key Classes:** `PromptRegistry`
- **Key Methods:** `get_prompt()`, `render_prompt()`, `list_prompts()`, `register_prompt()`
- **Template Format:** YAML with Jinja2 templating
- **Versioning:** Each prompt has version tracking
- **A/B Testing:** Supported via version selection
- **Dependencies:** `pyyaml`, `jinja2`

### Prompt Templates (YAML)
- **Location:** `intelligence/prompts/templates/`
- **Format:** YAML with Jinja2 variables
- **Usage:** Loaded at startup, rendered with context at inference time

---

## 6. RAG Pipeline

### RAG Architecture

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **RAG Service** | `intelligence/rag/service.py` | Orchestrates full RAG pipeline | ✅ Implemented |
| **Retriever** | `intelligence/rag/retrieval.py` | Vector similarity search | ✅ Implemented |
| **Embeddings** | `intelligence/rag/embeddings.py` | Text embedding generation | ✅ Implemented |
| **Chunking** | `intelligence/rag/chunking.py` | Document chunking strategies | ✅ Implemented |

### RAG Service
- **Path:** `intelligence/rag/service.py`
- **Purpose:** End-to-end RAG: ingest → chunk → embed → store → query → retrieve → generate
- **Status:** ✅ Implemented
- **Key Classes:** `RAGService`
- **Key Methods:** `ingest()`, `query()`, `retrieve()`, `generate_answer()`
- **Dependencies:** EmbeddingService, Retriever, ChunkingService, LLM

### Chunking Service
- **Path:** `intelligence/rag/chunking.py`
- **Purpose:** Split documents into chunks for embedding
- **Status:** ✅ Implemented
- **Key Classes:** `ChunkingService`
- **Strategies:** Fixed-size, semantic, hybrid
- **Default Chunk Size:** 512 tokens with 50-token overlap

### Embedding Service
- **Path:** `intelligence/rag/embeddings.py`
- **Purpose:** Generate vector embeddings for text
- **Status:** ✅ Implemented
- **Key Classes:** `EmbeddingService`
- **Model:** `text-embedding-3-large` (OpenAI)
- **Dimensions:** 3072
- **Dependencies:** OpenAI Provider

### Retriever
- **Path:** `intelligence/rag/retrieval.py`
- **Purpose:** Vector similarity search + hybrid retrieval
- **Status:** ✅ Implemented
- **Key Classes:** `Retriever`
- **Key Methods:** `search()`, `hybrid_search()`
- **Vector Store:** PostgreSQL pgvector
- **Similarity:** Cosine similarity
- **Fallback:** pg_trgm for text matching

---

## 7. Guardrails & Safety

### Guardrails

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Prompt Guard** | `intelligence/guardrails.py` | Prompt injection protection + output validation | ✅ Implemented |

### Prompt Guard Details
- **Path:** `intelligence/guardrails.py`
- **Purpose:** Protect against prompt injection, validate LLM outputs
- **Status:** ✅ Implemented
- **Key Classes:** `PromptGuard`
- **Key Methods:** `check_injection()`, `validate_output()`, `sanitize_input()`
- **Protections:**
  - Prompt injection detection (pattern matching)
  - Output JSON validation
  - Input sanitization
  - Content filtering
- **Dependencies:** None (pure Python)

### Safety Measures
- **Input Validation:** All agent inputs validated via Pydantic schemas
- **Output Validation:** LLM outputs validated against expected schemas
- **Cost Limits:** Budget enforcement per model/tenant
- **Rate Limiting:** Provider-level rate limiting via tenacity

---

## 8. Cost Tracking

### Cost Management

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Cost Tracker** | `intelligence/cost_tracker.py` | Track LLM usage costs per model/tenant | ✅ Implemented |

### Cost Tracker Details
- **Path:** `intelligence/cost_tracker.py`
- **Purpose:** Track and enforce LLM usage costs
- **Status:** ✅ Implemented
- **Key Classes:** `CostTracker`
- **Key Methods:** `track_usage()`, `get_cost()`, `check_budget()`, `get_report()`
- **Cost Rates:** Per-model pricing (configurable)
- **Budget Enforcement:** Per-tenant budget limits
- **Tracking:** Tokens in/out, cost in USD
- **Dependencies:** None (in-memory tracking)

### Cost Rates (Configurable)
| Model | Input $/1M tokens | Output $/1M tokens |
|-------|-------------------|---------------------|
| gpt-4 | $30.00 | $60.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |
| text-embedding-3-large | $0.13 | — |

---

## 9. Reasoning Pipeline

### Reasoning

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Reasoning Pipeline** | `intelligence/reasoning.py` | Analyze → Reason → Recommend pipeline | ✅ Implemented |

### Reasoning Pipeline Details
- **Path:** `intelligence/reasoning.py`
- **Purpose:** Multi-step reasoning for AI recommendations
- **Status:** ✅ Implemented
- **Key Classes:** `ReasoningPipeline`
- **Key Methods:** `analyze()`, `reason()`, `recommend()`
- **Pipeline Steps:**
  1. **Analyze:** Gather context from business data
  2. **Reason:** Apply reasoning with Arabic prompts
  3. **Recommend:** Generate actionable recommendations
- **Dependencies:** LLM Service, Grounding Service
- **Language:** Arabic-first prompts

---

## 10. Grounding Service

### Grounding

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Grounding Service** | `intelligence/grounding.py` | Retrieve-then-generate from business data | ✅ Implemented |

### Grounding Service Details
- **Path:** `intelligence/grounding.py`
- **Purpose:** Ground LLM responses in actual business data
- **Status:** ✅ Implemented
- **Key Classes:** `GroundingService`
- **Key Methods:** `ground()`, `retrieve_context()`, `generate_grounded()`
- **Pattern:** Retrieve relevant data → Inject into prompt → Generate grounded response
- **Dependencies:** RAG Service, LLM Service

---

## 11. Arabic NLP

### Arabic Processing

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Arabic Preprocessor** | `intelligence/arabic/preprocessing.py` | Arabic text normalization, stemming, NER | ✅ Implemented |

### Arabic Preprocessor Details
- **Path:** `intelligence/arabic/preprocessing.py`
- **Purpose:** Arabic-first NLP processing
- **Status:** ✅ Implemented
- **Key Classes:** `ArabicPreprocessor`
- **Key Methods:** `normalize()`, `stem()`, `extract_entities()`, `score_quality()`
- **Capabilities:**
  - Text normalization (diacritics, hamza, alef variants)
  - Stemming (root extraction)
  - Named Entity Recognition (companies, people, locations)
  - Quality scoring for Arabic text
- **Dependencies:** None (rule-based)

### Arabic Text Processing Features
| Feature | Method | Status |
|---------|--------|--------|
| Diacritics removal | `remove_diacritics()` | ✅ |
| Hamza normalization | `normalize_hamza()` | ✅ |
| Alef variants | `normalize_alef()` | ✅ |
| Ta Marbuta/Normal | `normalize_taa()` | ✅ |
| Yaa variants | `normalize_yaa()` | ✅ |
| Root stemming | `stem()` | ✅ |
| Company NER | `extract_companies()` | ✅ |
| Person NER | `extract_persons()` | ✅ |
| Location NER | `extract_locations()` | ✅ |
| Quality scoring | `score_quality()` | ✅ |

---

## 12. Evaluation Framework

### Evaluation

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Evaluation Runner** | `intelligence/evaluation/runner.py` | Run evaluation metrics on AI outputs | ✅ Implemented |
| **Test Cases** | `intelligence/evaluation/test_cases/` | Evaluation test case definitions | 🔲 Empty |

### Evaluation Runner Details
- **Path:** `intelligence/evaluation/runner.py`
- **Purpose:** Evaluate AI output quality
- **Status:** ✅ Implemented
- **Key Classes:** `EvaluationRunner`
- **Key Methods:** `evaluate()`, `run_faithfulness()`, `run_relevance()`, `run_accuracy()`
- **Metrics:**
  - **Faithfulness:** How well output matches source data
  - **Relevance:** How relevant output is to the query
  - **Accuracy:** Factual correctness of output
- **Dependencies:** LLM Service (for LLM-as-judge)

### Evaluation Metrics
| Metric | Method | Scoring | Status |
|--------|--------|---------|--------|
| Faithfulness | `run_faithfulness()` | 0-1 score | ✅ |
| Relevance | `run_relevance()` | 0-1 score | ✅ |
| Accuracy | `run_accuracy()` | 0-1 score | ✅ |
| Hallucination Detection | `detect_hallucination()` | Binary | ✅ |

---

## 13. Graph Intelligence

### Graph

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Relationship Graph** | `intelligence/graph/__init__.py` | Graph traversal for entity relationships | ✅ Implemented |

### Relationship Graph Service Details
- **Path:** `intelligence/graph/__init__.py`
- **Purpose:** Traverse and query entity relationship graphs
- **Status:** ✅ Implemented
- **Key Classes:** `RelationshipGraphService`
- **Key Methods:** `get_relationships()`, `find_path()`, `get_neighbors()`
- **Backend:** Neo4j
- **Dependencies:** Neo4j driver

---

## 14. Signal Engine

### Signals

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Signal Engine** | `intelligence/signals/__init__.py` | Detect buying signals + generate recommendations | ✅ Implemented |

### Signal Engine Details
- **Path:** `intelligence/signals/__init__.py`
- **Purpose:** Detect buying signals from business data and generate actionable recommendations
- **Status:** ✅ Implemented
- **Key Classes:** `SignalEngine`, `BuyingSignal`, `Recommendation`
- **Key Methods:** `detect_signals()`, `generate_recommendations()`, `score_signals()`
- **Signal Types:** Intent signals, engagement signals, timing signals, fit signals
- **Dependencies:** Company data, interaction data

---

## 15. Market Intelligence

### Market

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Market Intelligence** | `intelligence/market/__init__.py` | Market analysis and competitive intelligence | ✅ Implemented |

### Market Intelligence Engine Details
- **Path:** `intelligence/market/__init__.py`
- **Purpose:** Analyze market conditions, industry trends, competitive landscape
- **Status:** ✅ Implemented
- **Key Classes:** `MarketIntelligenceEngine`
- **Key Methods:** `analyze_market()`, `get_industry_trends()`, `competitive_analysis()`
- **Dependencies:** External data sources

---

## 16. Revenue Brain

### Revenue Intelligence

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Revenue Brain** | `intelligence/revenue_brain/__init__.py` | Revenue forecasting + executive decisions | ✅ Implemented |

### Revenue Brain Details
- **Path:** `intelligence/revenue_brain/__init__.py`
- **Purpose:** AI-powered revenue forecasting and executive decision support
- **Status:** ✅ Implemented
- **Key Classes:** `RevenueBrain`
- **Key Methods:** `forecast()`, `predict_revenue()`, `executive_decision()`
- **Capabilities:**
  - Revenue forecasting (time series)
  - Deal probability scoring
  - Executive decision recommendations
  - Pipeline health analysis
- **Dependencies:** LLM Service, Company data, Deal data

---

## 17. Digital Twin

### Digital Twin

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Digital Twin** | `intelligence/digital_twin/twin.py` | Company digital twin simulation | ✅ Implemented |
| **Company Twin** | `intelligence/digital_twin/company_twin.py` | Company-specific twin logic | ✅ Implemented |

### Digital Twin Details
- **Path:** `intelligence/digital_twin/twin.py`, `company_twin.py`
- **Purpose:** Create digital twins of companies for simulation and analysis
- **Status:** ✅ Implemented
- **Key Classes:** `DigitalTwin`, `CompanyTwin`
- **Key Methods:** `create_twin()`, `simulate()`, `predict_behavior()`, `analyze_patterns()`
- **Capabilities:**
  - Company behavior modeling
  - Pattern analysis
  - What-if simulations
  - Relationship mapping
- **Dependencies:** Company data, Graph Intelligence, Market Intelligence

---

## 18. Simulation Engine

### Simulation

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Simulation Engine** | `intelligence/simulation/simulation.py` | Scenario simulation and analysis | ✅ Implemented |

### Simulation Engine Details
- **Path:** `intelligence/simulation/simulation.py`
- **Purpose:** Run business scenario simulations
- **Status:** ✅ Implemented
- **Key Classes:** `SimulationEngine`
- **Key Methods:** `run_simulation()`, `compare_scenarios()`, `optimize()`
- **Scenario Types:** `ScenarioType` enum (pricing, pipeline, market, etc.)
- **Dependencies:** Digital Twin, Revenue Brain

---

## 19. Data Fabric

### Data Fabric Architecture

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Data Fabric** | `intelligence/data_fabric/fabric.py` | Orchestration layer | ✅ Implemented |
| **Connector Engine** | `intelligence/data_fabric/connectors.py` | External system connectors | ✅ Implemented |
| **Identity Resolver** | `intelligence/data_fabric/identity_resolution.py` | Cross-source identity resolution | ✅ Implemented |
| **Entity Matcher** | `intelligence/data_fabric/entity_matching.py` | Entity deduplication + matching | ✅ Implemented |
| **Data Quality** | `intelligence/data_fabric/quality.py` | Quality scoring + trust | ✅ Implemented |

### Connector Engine
- **Path:** `intelligence/data_fabric/connectors.py`
- **Purpose:** Connect to external data sources (CRM, ERP, Email, etc.)
- **Status:** ✅ Implemented
- **Key Classes:** `ConnectorEngine`, `Connector`, `ConnectorType`, `ConnectorStatus`
- **Built-in Connectors:** Gmail, Outlook, HubSpot, Odoo, SAP, Dynamics, Slack, WhatsApp, Excel, Google Drive
- **Connector Types:** EMAIL, CRM, ERP, CALENDAR, MESSAGING, STORAGE, SPREADSHEET, API, DATABASE
- **Status States:** DISCONNECTED, CONNECTING, CONNECTED, ERROR, EXPIRED
- **Key Methods:** `connect()`, `sync()`, `sync_all()`, `disconnect()`

### Identity Resolver
- **Path:** `intelligence/data_fabric/identity_resolution.py`
- **Purpose:** Resolve identities across data sources
- **Status:** ✅ Implemented
- **Key Classes:** `IdentityResolver`, `ResolvedIdentity`
- **Key Methods:** `resolve()`, `merge_identities()`, `get_unified_view()`

### Entity Matcher
- **Path:** `intelligence/data_fabric/entity_matching.py`
- **Purpose:** Match and deduplicate entities across sources
- **Status:** ✅ Implemented
- **Key Classes:** `EntityMatcher`, `MatchResult`, `MergeSuggestion`, `MergeStatus`
- **Key Methods:** `match()`, `batch_match()`, `approve_merge()`, `reject_merge()`, `get_pending_reviews()`
- **Matching Strategies:**
  - CR Number match (highest weight: 1.0)
  - VAT Number match (0.95)
  - Email match (0.8)
  - Phone match (0.7, last 8 digits)
  - Domain match (0.6)
  - Arabic name match (0.8 exact, 0.65 substring, 0.55 transliteration, 0.5 fuzzy)
  - English name match (0.8 exact, 0.65 substring)
- **Arabic Transliteration:** 18+ city/company name mappings
- **HITL Workflow:** Auto-merge ≥0.95, Review 0.7-0.95, Reject <0.7

### Data Quality Engine
- **Path:** `intelligence/data_fabric/quality.py`
- **Purpose:** Evaluate and maintain data quality
- **Status:** ✅ Implemented
- **Key Classes:** `DataQualityEngine`, `QualityScore`, `FreshnessScore`, `TrustScore`
- **Key Methods:** `evaluate()`, `calculate_trust()`, `get_quality_trend()`
- **Quality Dimensions:**
  - **Completeness:** 0.3 weight (field fill rate)
  - **Accuracy:** 0.25 weight (source reliability + corrections)
  - **Consistency:** 0.15 weight (cross-field validation)
  - **Freshness:** 0.2 weight (time since update)
  - **Uniqueness:** 0.1 weight (dedup indicators)
- **Freshness Grades:** REAL_TIME (<1h), FRESH (<24h), MODERATE (<168h), STALE (<720h), EXPIRED (>720h)
- **Source Reliability:** government(0.95) > manual(0.9) > erp(0.85) > crm(0.8) > linkedin(0.7) > website(0.6) > news(0.5) > enrichment_api(0.4) > ai_extraction(0.3) > web_scraper(0.2)

### Data Fabric Orchestration
- **Path:** `intelligence/data_fabric/fabric.py`
- **Purpose:** Orchestrate the full data fabric pipeline
- **Status:** ✅ Implemented
- **Key Classes:** `DataFabric`
- **Pipeline:** Connectors → Import/Sync → Validation → Identity Resolution → Entity Matching → Data Quality → Trust → Knowledge Graph

---

## 20. Domain AI Layer

### Domain Integration

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **AI Service** | `domains/ai/service.py` | Domain-layer AI service | ✅ Implemented |
| **AI Evaluator** | `domains/ai/evaluator.py` | Domain-specific evaluation | ✅ Implemented |
| **Prompt Registry** | `domains/ai/registry.py` | Domain prompt management | ✅ Implemented |
| **Schemas** | `domains/ai/schemas.py` | Domain AI schemas | ✅ Implemented |

### Domain AI Service
- **Path:** `domains/ai/service.py`
- **Purpose:** Expose AI capabilities to domain layer
- **Status:** ✅ Implemented
- **Key Classes:** `AIService`
- **Key Methods:** `generate()`, `analyze()`, `recommend()`
- **Dependencies:** Intelligence module, Provider factory

---

## 21. REST API Layer

### API Endpoints

| Endpoint | Path | Purpose | Auth | Status |
|----------|------|---------|------|--------|
| **AI Router** | `app/routers/ai.py` | Prompt CRUD, evaluation, generation | ✅ JWT | ✅ Implemented |
| **Copilot Router** | `app/routers/copilot.py` | AI copilot endpoint | ✅ JWT | ✅ Implemented |
| **RAG Router** | `app/routers/rag.py` | RAG API: ask, ingest, documents, delete | ✅ JWT | ✅ Implemented |

### AI Router
- **Path:** `app/routers/ai.py`
- **Purpose:** REST API for AI prompt management and generation
- **Status:** ✅ Implemented
- **Endpoints:**
  - `GET /ai/prompts` — List prompts
  - `POST /ai/prompts` — Create prompt
  - `GET /ai/prompts/{id}` — Get prompt
  - `PUT /ai/prompts/{id}` — Update prompt
  - `DELETE /ai/prompts/{id}` — Delete prompt
  - `POST /ai/evaluate` — Run evaluation
  - `POST /ai/generate` — Generate text
- **Auth:** JWT required
- **Dependencies:** Domain AI Service

### Copilot Router
- **Path:** `app/routers/copilot.py`
- **Purpose:** AI copilot for natural language interaction
- **Status:** ✅ Implemented
- **Endpoints:**
  - `POST /copilot/chat` — Chat with AI copilot
- **Auth:** JWT required
- **Dependencies:** Agent Coordinator

### RAG Router
- **Path:** `app/routers/rag.py`
- **Purpose:** RAG API for document ingestion and querying
- **Status:** ✅ Implemented
- **Endpoints:**
  - `POST /rag/ask` — Ask a question
  - `POST /rag/ingest` — Ingest documents
  - `GET /rag/documents` — List documents
  - `DELETE /rag/documents/{id}` — Delete document
- **Auth:** JWT required
- **Dependencies:** RAG Service

---

## 22. MCP Server

### MCP Protocol

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **MCP Server** | `mcp_server/server.py` | MCP protocol server (stdio + SSE) | ✅ Implemented |
| **MCP Tools** | `mcp_server/tools.py` | 8 AI agent tools | ✅ Implemented |

### MCP Server Details
- **Path:** `mcp_server/server.py`
- **Purpose:** Model Context Protocol server for AI agent integration
- **Status:** ✅ Implemented
- **Transport:** stdio + SSE (Server-Sent Events)
- **Key Classes:** `MCPServer`
- **Key Methods:** `start()`, `handle_request()`, `register_tool()`
- **Dependencies:** MCP SDK

### MCP Tools
- **Path:** `mcp_server/tools.py`
- **Purpose:** Expose SalesOS capabilities as MCP tools
- **Status:** ✅ Implemented
- **Tools:** 8 tools for AI agent integration
  - Company search/lookup
  - Opportunity management
  - Task creation
  - Contact management
  - Activity logging
  - Report generation
  - Data enrichment
  - Decision evaluation
- **Dependencies:** SalesOS domain services

---

## 23. Runtime — Decision Intelligence

### Decision Runtime

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Decision Intelligence Engine** | `runtime/decision_runtime/__init__.py` | Context-aware decision making with policies and feedback | ✅ Implemented |

### Decision Intelligence Engine Details
- **Path:** `runtime/decision_runtime/__init__.py`
- **Purpose:** Real-time decision intelligence with context, policies, and feedback loops
- **Status:** ✅ Implemented
- **Key Classes:** `DecisionIntelligenceEngine`
- **Key Methods:** `evaluate()`, `apply_policies()`, `get_context()`, `record_feedback()`
- **Capabilities:**
  - Context-aware decision making
  - Policy engine (rule-based)
  - Feedback loop for learning
  - Multi-factor scoring
- **Dependencies:** Company data, Signal Engine, Market Intelligence

---

## 24. Runtime — NBA AI Reasoner

### NBA Reasoner

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **NBA AI Reasoner** | `runtime/nba_engine/engine/ai/reasoner.py` | AI-powered Next-Best-Action reasoning | ✅ Implemented |

### NBA AI Reasoner Details
- **Path:** `runtime/nba_engine/engine/ai/reasoner.py`
- **Purpose:** AI-powered next-best-action recommendations
- **Status:** ✅ Implemented (optional LLM)
- **Key Classes:** `NBAReasoner`
- **Key Methods:** `reason()`, `get_recommendations()`, `score_actions()`
- **LLM Usage:** Optional (falls back to rule-based if no LLM)
- **Dependencies:** LLM Service (optional), Decision Intelligence Engine

---

## 25. Runtime — Agent Runtime

### Agent Runtime

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Agent Runtime** | `runtime/agent_runtime/__init__.py` | Agent execution runtime | 🔲 Placeholder |

### Agent Runtime Details
- **Path:** `runtime/agent_runtime/__init__.py`
- **Purpose:** Runtime environment for agent execution
- **Status:** 🔲 Placeholder — "PLANNED FOR RT3"
- **Note:** Not yet implemented. Planned for RT3 release.

---

## 26. Frontend Agent SDK

### Frontend Agents

| Component | Path | Purpose | Status |
|-----------|------|---------|--------|
| **Contracts** | `frontend/packages/platform/agents/contracts/index.ts` | Type definitions for agents, tasks, memory | ✅ Implemented |
| **Registry** | `frontend/packages/platform/agents/registry/index.ts` | Agent registration and lookup | ✅ Implemented |
| **Tools** | `frontend/packages/platform/agents/tools/index.ts` | Tool definitions and handlers | ✅ Implemented |
| **Orchestrator** | `frontend/packages/platform/agents/orchestrator/index.ts` | Task assignment and execution | ✅ Implemented |
| **Memory** | `frontend/packages/platform/agents/memory/index.ts` | In-memory agent memory with TTL | ✅ Implemented |
| **RAG (Context)** | `frontend/packages/platform/agents/rag/index.ts` | Agent context building | ✅ Implemented |

### Contracts
- **Path:** `frontend/packages/platform/agents/contracts/index.ts`
- **Purpose:** TypeScript type definitions for the agent system
- **Status:** ✅ Implemented
- **Key Types:**
  - `AgentStatus`: idle | busy | error | disabled
  - `TaskStatus`: pending | assigned | running | completed | failed | cancelled
  - `TaskPriority`: low | medium | high | critical
  - `MemoryType`: ephemeral | working | long_term
  - `AgentDefinition`: Agent configuration
  - `AgentContext`: Execution context
  - `AgentTask`: Task representation
  - `AgentAction`: Tool execution record
  - `AgentResult`: Task completion result
  - `MemoryEntry`: Memory storage entry

### Registry
- **Path:** `frontend/packages/platform/agents/registry/index.ts`
- **Purpose:** Register and look up agents
- **Status:** ✅ Implemented
- **Key Methods:** `register()`, `get()`, `list()`, `unregister()`
- **Pre-registered Agents:** NBA Agent (nba-consumption, opportunity-creation, task-creation, decision-execution)

### Tools
- **Path:** `frontend/packages/platform/agents/tools/index.ts`
- **Purpose:** Tool definitions and execution handlers
- **Status:** ✅ Implemented
- **Key Methods:** `register()`, `execute()`, `list()`, `registerHandler()`
- **Built-in Tools:**
  - `create_opportunity` — Creates SalesOS opportunities
  - `create_task` — Creates SalesOS tasks
  - `evaluate_decision` — Evaluates via Decision Platform
  - `search_companies` — Searches companies (placeholder)
  - `get_recommendation` — Gets NBA recommendations
- **Dependencies:** `@salesos/decision-platform`

### Orchestrator
- **Path:** `frontend/packages/platform/agents/orchestrator/index.ts`
- **Purpose:** Task assignment, execution, and batch processing
- **Status:** ✅ Implemented
- **Key Methods:** `assignTask()`, `executeTask()`, `executeBatch()`, `getTask()`, `getAgentStatus()`
- **Features:**
  - Concurrency control (maxConcurrency per agent)
  - Priority resolution (critical/high/medium)
  - Decision Engine integration
  - Memory storage for results
  - Batch execution support
- **Dependencies:** Registry, Tools, Memory, Decision Platform

### Memory
- **Path:** `frontend/packages/platform/agents/memory/index.ts`
- **Purpose:** In-memory agent memory with TTL-based eviction
- **Status:** ✅ Implemented
- **Key Methods:** `store()`, `recall()`, `forget()`, `clear()`, `getContext()`
- **Features:**
  - TTL-based auto-eviction
  - Per-agent isolation
  - Timer-based cleanup
  - Memory types: ephemeral, working, long_term
- **Storage:** In-memory (Map-based)
- **Default TTL:** 3,600,000ms (1 hour)

### RAG (Context Builder)
- **Path:** `frontend/packages/platform/agents/rag/index.ts`
- **Purpose:** Build agent context from memory and metadata
- **Status:** ✅ Implemented
- **Key Methods:** `buildContext()`
- **Output:** Markdown-formatted context string
- **Includes:** Agent ID, tenant, entity, decision, memory entries, metadata

### Frontend Tests
| Test File | Purpose | Status |
|-----------|---------|--------|
| `__tests__/tools.test.ts` | Tool registration and execution | ✅ |
| `__tests__/registry.test.ts` | Agent registry operations | ✅ |
| `__tests__/rag.test.ts` | Context building | ✅ |
| `__tests__/orchestrator.test.ts` | Task orchestration | ✅ |
| `__tests__/memory.test.ts` | Memory operations | ✅ |

---

## 27. Dependencies Matrix

### Backend Dependencies

| Module | External Dependencies | Internal Dependencies |
|--------|----------------------|----------------------|
| Intelligence Core | pydantic | — |
| Agent System | — | Intelligence Core |
| LLM Providers | openai, tenacity | — |
| Prompt Registry | pyyaml, jinja2 | — |
| RAG Pipeline | pgvector, psycopg2 | Providers, Chunking |
| Arabic NLP | — | — (rule-based) |
| Evaluation | — | LLM Service |
| Graph Intelligence | neo4j | — |
| Signal Engine | — | Company data |
| Market Intelligence | — | External APIs |
| Revenue Brain | — | LLM Service, Company data |
| Digital Twin | — | Graph, Market, Revenue Brain |
| Simulation | — | Digital Twin, Revenue Brain |
| Data Fabric | — | Connectors, Identity, Matching, Quality |
| Domain AI | — | Intelligence Core |
| REST API | fastapi | Domain AI, RAG, Agent Coordinator |
| MCP Server | mcp-sdk | Domain Services |
| Decision Runtime | — | Signal Engine, Market Intelligence |
| NBA Reasoner | — | LLM Service (optional), Decision Runtime |
| Agent Runtime | — | 🔲 Placeholder |

### Frontend Dependencies

| Module | External Dependencies | Internal Dependencies |
|--------|----------------------|----------------------|
| Agent Contracts | @salesos/decision-platform | — |
| Agent Registry | — | Contracts |
| Agent Tools | @salesos/decision-platform | Contracts |
| Agent Orchestrator | @salesos/decision-platform | Registry, Tools, Memory |
| Agent Memory | — | Contracts |
| Agent RAG | — | Memory, Contracts |

---

## 28. Test Coverage

### Backend Tests

| Module | Test Location | Coverage | Status |
|--------|--------------|----------|--------|
| Intelligence Core | `intelligence/tests/` | ⚠️ No test files found | 🔲 Gap |
| Agent System | `intelligence/agents/tests/` | ⚠️ No test files found | 🔲 Gap |
| RAG Pipeline | `intelligence/rag/tests/` | ⚠️ No test files found | 🔲 Gap |
| Data Fabric | `intelligence/data_fabric/tests/` | ⚠️ No test files found | 🔲 Gap |
| Domain AI | `domains/ai/tests/` | ⚠️ No test files found | 🔲 Gap |
| Evaluation | `intelligence/evaluation/test_cases/` | 🔲 Empty directory | 🔲 Gap |

### Frontend Tests

| Module | Test Location | Status |
|--------|--------------|--------|
| Agent Tools | `__tests__/tools.test.ts` | ✅ Implemented |
| Agent Registry | `__tests__/registry.test.ts` | ✅ Implemented |
| Agent RAG | `__tests__/rag.test.ts` | ✅ Implemented |
| Agent Orchestrator | `__tests__/orchestrator.test.ts` | ✅ Implemented |
| Agent Memory | `__tests__/memory.test.ts` | ✅ Implemented |

---

## 29. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React/TS)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Contracts │ │ Registry │ │  Tools   │ │Orchestr. │ │ Memory   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └─────────────┴────────────┴─────────────┴────────────┘       │
│                              │                                      │
│                    ┌─────────▼─────────┐                           │
│                    │  Agent RAG (ctx)  │                           │
│                    └─────────┬─────────┘                           │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ MCP / REST
┌──────────────────────────────┼──────────────────────────────────────┐
│                        Backend (Python/FastAPI)                     │
│                              │                                      │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │                    REST API Layer                              │  │
│  │  ┌────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────────┐  │  │
│  │  │AI Route│  │Copilot   │  │RAG Route│  │  MCP Server      │  │  │
│  │  └───┬────┘  └────┬─────┘  └────┬────┘  └────────┬─────────┘  │  │
│  └──────┼────────────┼──────────────┼────────────────┼────────────┘  │
│         │            │              │                │               │
│  ┌──────▼────────────▼──────────────▼────────────────▼────────────┐  │
│  │                  Domain AI Layer                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │AI Service│  │Evaluator │  │ Registry │  │ Schemas  │      │  │
│  │  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│  └───────┼────────────────────────────────────────────────────────┘  │
│          │                                                          │
│  ┌───────▼────────────────────────────────────────────────────────┐  │
│  │              Intelligence Core                                 │  │
│  │                                                                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ Agent    │ │ Provider │ │  Prompt  │ │   Guardrails     │  │  │
│  │  │ System   │ │ Factory  │ │ Registry │ │   & Safety       │  │  │
│  │  │(11 agents│ │ (OpenAI) │ │ (YAML)   │ │                  │  │  │
│  │  └────┬─────┘ └────┬─────┘ └──────────┘ └──────────────────┘  │  │
│  │       │            │                                           │  │
│  │  ┌────▼────────────▼───────────────────────────────────────┐   │  │
│  │  │              LLM Service + Cost Tracker                  │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  │                                                                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │  │   RAG    │ │ Reasoning│ │Grounding │ │ Arabic   │         │  │
│  │  │ Pipeline │ │ Pipeline │ │ Service  │ │ NLP      │         │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │                                                                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │  │  Graph   │ │  Signal  │ │  Market  │ │ Revenue  │         │  │
│  │  │  Intel   │ │  Engine  │ │  Intel   │ │  Brain   │         │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │                                                                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐   │  │
│  │  │ Digital  │ │Simulation│ │       Data Fabric             │   │  │
│  │  │  Twin    │ │  Engine  │ │Connectors│Identity│Matching│Q│   │  │
│  │  └──────────┘ └──────────┘ └──────────────────────────────┘   │  │
│  │                                                                │  │
│  │  ┌──────────┐ ┌──────────┐                                    │  │
│  │  │Evaluation│ │  Cost    │                                    │  │
│  │  │ Runner   │ │ Tracker  │                                    │  │
│  │  └──────────┘ └──────────┘                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │                    Runtime Layer                               │  │
│  │  ┌──────────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │Decision Intel.   │  │ NBA Reasoner │  │ Agent Runtime  │  │  │
│  │  │Engine            │  │ (optional    │  │ 🔲 PLANNED     │  │  │
│  │  │                  │  │  LLM)        │  │                │  │  │
│  │  └──────────────────┘  └──────────────┘  └────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │                    Data Layer                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │PostgreSQL│  │  Neo4j   │  │ pgvector │  │  Redis   │      │  │
│  │  │ (main)   │  │ (graph)  │  │ (embed)  │  │ (cache)  │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 30. Gaps & Recommendations

### Critical Gaps

| ID | Gap | Severity | Impact | Recommendation |
|----|-----|----------|--------|----------------|
| G-01 | **No backend AI tests** — Zero test files found for intelligence module, agents, RAG, data fabric, domain AI | 🔴 Critical | Cannot verify AI behavior, regressions likely | Write unit + integration tests for all AI modules |
| G-02 | **Agent Runtime placeholder** — `runtime/agent_runtime/` is "PLANNED FOR RT3" | 🔴 Critical | No runtime execution environment for agents | Implement agent runtime or remove placeholder |
| G-03 | **Evaluation test_cases empty** — No test cases for evaluation framework | 🟡 High | Evaluation framework has no baseline | Create evaluation test cases with golden datasets |
| G-04 | **search_companies tool placeholder** — Frontend tool returns empty results | 🟡 High | Frontend agents cannot search companies | Integrate with Search SDK |

### Medium Gaps

| ID | Gap | Severity | Impact | Recommendation |
|----|-----|----------|--------|----------------|
| G-05 | **Single LLM provider** — Only OpenAI supported | 🟡 Medium | No fallback, vendor lock-in | Add Anthropic/LOCAL provider via factory |
| G-06 | **In-memory memory** — Frontend agent memory is Map-based, lost on refresh | 🟡 Medium | Agent state not persistent | Add Redis/localStorage persistence option |
| G-07 | **Connector data simulated** — `_fetch_data()` returns mock data | 🟡 Medium | Data Fabric not functional with real sources | Implement real API connectors |
| G-08 | **No agent observability** — No logging, tracing, or metrics for agent execution | 🟡 Medium | Cannot debug agent behavior in production | Add OpenTelemetry tracing + structured logging |

### Low Gaps

| ID | Gap | Severity | Impact | Recommendation |
|----|-----|----------|--------|----------------|
| G-09 | **No A/B testing results** — Prompt registry supports A/B but no usage data | 🟢 Low | Cannot optimize prompts | Add A/B metrics tracking |
| G-10 | **No embedding caching** — Each query re-embeds | 🟢 Low | Unnecessary API costs | Add embedding cache (Redis) |
| G-11 | **No rate limiting on MCP** — MCP server has no rate limiting | 🟢 Low | Potential abuse | Add rate limiting middleware |

### Recommendations Summary

1. **Immediate (P0):** Write backend AI tests — all modules need coverage
2. **Immediate (P0):** Resolve Agent Runtime placeholder (implement or remove)
3. **Short-term (P1):** Create evaluation test cases with golden datasets
4. **Short-term (P1):** Integrate frontend search_companies with Search SDK
5. **Medium-term (P2):** Add alternative LLM providers (Anthropic, local models)
6. **Medium-term (P2):** Implement real data connectors
7. **Medium-term (P2):** Add observability (tracing, logging, metrics)
8. **Long-term (P3):** Embedding caching, A/B metrics, MCP rate limiting

---

*Audit completed: 2026-07-15*
*Auditor: Architecture Review Board*
