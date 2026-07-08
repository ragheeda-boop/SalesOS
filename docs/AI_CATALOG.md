# SalesOS — AI CATALOG

> **سجل الذكاء الاصطناعي — كل Agent, Prompt, Model, Memory, Tool, Budget, Evaluation**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## 1. MODELS

| ID | Model | Provider | Purpose | Max Tokens | Cost/1K Input | Cost/1K Output | Status |
|----|-------|----------|---------|-----------|--------------|---------------|--------|
| M-001 | GPT-4o | OpenAI | Complex reasoning, Agent OS | 128K | $0.005 | $0.015 | ✅ Configured |
| M-002 | GPT-4o-mini | OpenAI | Simple queries, Entity resolution | 128K | $0.00015 | $0.0006 | ✅ Configured |
| M-003 | text-embedding-3-small | OpenAI | Embeddings (default) | 8K | $0.00002 | — | ✅ Configured |
| M-004 | text-embedding-3-large | OpenAI | Company DNA embeddings | 8K | $0.00013 | — | 🟡 Planned |
| M-005 | Claude 3.5 Sonnet | Anthropic | Enterprise fallback | 200K | $0.003 | $0.015 | 🟡 Planned |

### Model Selection Rules

```
IF query requires current data           → M-002 (GPT-4o-mini)
IF query requires complex reasoning      → M-001 (GPT-4o)
IF query requires Arabic understanding   → M-001 (GPT-4o)
IF query is embedding                    → M-003 (text-embedding-3-small)
IF query is for Company DNA              → M-004 (text-embedding-3-large)
IF GPT-4o unavailable                    → M-005 (Claude 3.5 Sonnet fallback)
```

---

## 2. AGENTS

| ID | Agent | Model | Tools | Memory | Status |
|----|-------|-------|-------|--------|--------|
| A-001 | AI Copilot | M-002/M-001 | Search, Timeline, KG, Feature Store | Company Memory | ❌ Missing |
| A-002 | Research Agent | M-001 | Web Search, Scraper, Company DB | Session Memory | ❌ Missing |
| A-003 | Scoring Agent | M-002 | Feature Store, Company DNA | None | ❌ Missing |
| A-004 | Risk Detection Agent | M-001 | Knowledge Graph, Timeline, Signals | Pattern Memory | ❌ Missing |
| A-005 | Recommendation Agent | M-001 | Revenue Brain, Feature Store, DNA | User Memory | ❌ Missing |
| A-006 | Data Quality Agent | M-002 | Entity Resolution, Golden Records | None | ❌ Missing |

---

## 3. PROMPTS

| ID | Prompt | Used By | Model | Version | Status |
|----|--------|---------|-------|---------|--------|
| P-001 | Company Summary | AI Copilot | M-002 | v0 (design) | ❌ Missing |
| P-002 | Company Comparison | AI Copilot | M-002 | v0 (design) | ❌ Missing |
| P-003 | Lead Scoring | Scoring Agent | M-002 | v0 (design) | ❌ Missing |
| P-004 | Intent Detection | Research Agent | M-001 | v0 (design) | ❌ Missing |
| P-005 | Entity Resolution | Data Quality Agent | M-002 | v0 (design) | ❌ Missing |
| P-006 | Risk Assessment | Risk Detection Agent | M-001 | v0 (design) | ❌ Missing |
| P-007 | Next Best Action | Recommendation Agent | M-001 | v0 (design) | ❌ Missing |
| P-008 | Arabic Search Query | Search Engine | — | v0 (design) | ❌ Missing |

### Prompt Template

```
Prompt ID:   P-001
Name:        Company Summary
Version:     0.1
Model:       GPT-4o-mini
Max Tokens:  1024
Temperature: 0.3

System:
You are a business intelligence assistant. Given company data from multiple
sources, produce a concise summary in {language} (Arabic by default).
Focus on: company size, industry, recent changes, and growth indicators.

Context:
- Company: {company_name}
- Industry: {industry}
- Employees: {employee_count}
- Recent signals: {signals}
- Licenses: {licenses}

Output format:
{ "summary_ar": "...", "summary_en": "...", "key_insights": [...], "confidence": 0.X }
```

---

## 4. TOOLS

| ID | Tool | Description | Used By | Status |
|----|------|-------------|---------|--------|
| T-001 | SearchCompanies | Search company database by query | AI Copilot, Research Agent | ✅ Available |
| T-002 | GetCompanyProfile | Fetch full company profile | AI Copilot | ✅ Available |
| T-003 | GetTimeline | Get entity timeline events | AI Copilot, Risk Agent | ✅ Available |
| T-004 | GetKnowledgeGraph | Query Neo4j relationships | Research Agent | 🟡 KG empty |
| T-005 | GetFeatureValues | Get computed features from Feature Store | Scoring Agent | ❌ Feature Store missing |
| T-006 | ComputeScore | Trigger scoring computation | Scoring Agent | ❌ Missing |
| T-007 | SimulateAction | Run simulation engine | Recommendation Agent | ❌ Missing |
| T-008 | DetectSignals | Check for new signals on entity | Risk Agent | ❌ Missing |
| T-009 | UpdateMemory | Write to AI Memory store | All agents | ❌ Missing |
| T-010 | WebSearch | Search the web for company info | Research Agent | ❌ Missing |

---

## 5. MEMORY

| ID | Memory Type | Storage | Scope | Decay | Status |
|----|-------------|---------|-------|-------|--------|
| MEM-001 | Company Memory | pgvector | Per-company facts and insights | 30-day half-life | ❌ Missing |
| MEM-002 | Session Memory | Redis | Per-conversation context | Session end | ❌ Missing |
| MEM-003 | User Memory | PostgreSQL | User preferences and patterns | 90-day half-life | ❌ Missing |
| MEM-004 | Pattern Memory | Neo4j | Detected patterns across entities | 60-day half-life | ❌ Missing |
| MEM-005 | Knowledge Pack Memory | PostgreSQL | Industry-specific domain knowledge | Permanent | ❌ Missing |

---

## 6. EVALUATION

| Metric | Target | Measurement | Current | Status |
|--------|--------|-------------|---------|--------|
| Answer Accuracy | >90% | Human eval on 100 samples/month | — | ❌ Missing |
| Hallucination Rate | <3% | Automated hallucination detection | — | ❌ Missing |
| Confidence Calibration | <10% error | Brier score | — | ❌ Missing |
| Response Latency (p95) | <5s | Prometheus metric | — | ❌ Missing |
| Cache Hit Rate | >50% | Semantic Cache metric | — | ❌ Missing |
| Cost per Query | <$0.01 | Token tracking | — | ❌ Missing |
| User Satisfaction | >4/5 | Post-interaction feedback | — | ❌ Missing |

---

## 7. GUARDRAILS

| Guardrail | Implementation | Action | Status |
|-----------|---------------|--------|--------|
| PII Detection | Regex + NLP model | Block output, log alert | ❌ Missing |
| Hallucination Check | LLM-as-judge (M-001) | Low confidence → flag | ❌ Missing |
| Content Filtering | OpenAI Moderation API | Block toxic content | ❌ Missing |
| Rate Limiting | Redis per-tenant counter | 429 Too Many Requests | ❌ Missing |
| Budget Cap | Monthly token budget per tenant | Block when exhausted | ❌ Missing |
| Model Fallback | M-002 → M-005 | Auto-fallback on error | ❌ Missing |

---

## 8. BUDGET & COST TRACKING

### Per-Query Cost Estimates

| Operation | Model | Avg Input Tokens | Avg Output Tokens | Estimated Cost |
|-----------|-------|-----------------|------------------|---------------|
| Simple company search | M-002 | 500 | 200 | $0.0002 |
| Company summary | M-002 | 2,000 | 500 | $0.0006 |
| Complex analysis | M-001 | 4,000 | 1,000 | $0.035 |
| Entity resolution | M-002 | 1,000 | 100 | $0.0002 |
| Embedding generation | M-003 | 500 | — | $0.00001 |

### Monthly Budget (Per Tenant)

| Tier | Monthly Budget | Daily Limit | Over-Limit Behavior |
|------|---------------|-------------|---------------------|
| Free | $5 | $0.17 | Degrade to GPT-4o-mini only |
| Growth | $50 | $1.67 | Notify admin |
| Enterprise | $500 | $16.67 | Custom limits |
| Enterprise+ | Custom | Custom | No hard limit |

---

*This catalog is the authoritative registry of all AI assets. Every new agent, prompt, model, tool, memory type, or guardrail must be registered here before implementation. Eval scores must be updated monthly.*
