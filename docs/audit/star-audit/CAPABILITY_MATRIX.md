# Capability Matrix — Agent Inventory & Phase Readiness

**Status:** ACCEPTED
**Accepted:** 2026-08-09
**Review:** Cross-artifact consistency verified

---

## Agent Inventory (12 agents)

| # | Agent | File | Type |
|---|-------|------|------|
| 1 | ResearchAgent | `intelligence/agents/research.py` | Domain |
| 2 | CompetitorAgent | `intelligence/agents/competitor.py` | Domain |
| 3 | ContractAgent | `intelligence/agents/contract.py` | Domain |
| 4 | ForecastAgent | `intelligence/agents/forecast.py` | Domain |
| 5 | MeetingAgent | `intelligence/agents/meeting.py` | Domain |
| 6 | NewsAgent | `intelligence/agents/news.py` | Domain |
| 7 | PricingAgent | `intelligence/agents/pricing.py` | Domain |
| 8 | ProposalAgent | `intelligence/agents/proposal.py` | Domain |
| 9 | RelationshipAgent | `intelligence/agents/relationship.py` | Domain |
| 10 | RenewalAgent | `intelligence/agents/renewal.py` | Domain |
| 11 | TenderAgent | `intelligence/agents/tender.py` | Domain |
| 12 | AgentCoordinator | `intelligence/agents/coordinator.py` | Orchestrator |

**Supporting files (not agents):** `base.py` (BaseAgent), `llm.py` (LLMService)

---

## Phase Readiness Matrix

| Agent | Phase | Read | Write | LLM | Ext API | Evidence | Approval | Risk |
|-------|:-----:|:----:|:-----:|:---:|:-------:|:--------:|:--------:|:----:|
| **ResearchAgent** | **P1** | ✓ | ✗ | ✓ | Optional | P2 | No | LOW |
| NewsAgent | P2 | ✓ | ✗ | ✓ | ✓ | P2 | No | LOW |
| CompetitorAgent | P2 | ✓ | ✗ | ✓ | ✓ | P2 | No | MED |
| MeetingAgent | P2 | ✓ | ✗ | ✓ | ✗ | ✗ | No | LOW |
| RelationshipAgent | P2 | ✓ | ✗ | ✓ | ✗ | P2 | No | LOW |
| TenderAgent | P2 | ✓ | ✗ | ✓ | Optional | P2 | No | MED |
| ContractAgent | P2 | ✓ | ✗ | ✓ | ✗ | P2 | No | MED |
| ForecastAgent | P3 | ✓ | ✗ | ✓ | ✗ | ✗ | No | MED |
| PricingAgent | P3 | ✓ | ✗ | ✓ | ✗ | ✗ | No | MED |
| ProposalAgent | P3 | ✓ | ✓ | ✓ | ✗ | P3 | Yes | HIGH |
| RenewalAgent | P3 | ✓ | ✓ | ✓ | ✗ | ✗ | Yes | HIGH |
| Coordinator | P4+ | ✗ | ✗ | ✓ | ✗ | ✗ | N/A | HIGH |

---

## Column Definitions

| Column | Meaning |
|--------|---------|
| **Phase** | Earliest phase the agent can be activated through Agent Runtime |
| **Read** | Agent performs read operations (CRM, graph, features, sources) |
| **Write** | Agent performs write operations (enrichment, creation, scheduling) |
| **LLM** | Agent calls an LLM for inference |
| **Ext API** | Agent calls external APIs (Perplexity, LinkedIn, etc.) |
| **Evidence** | Agent produces evidence-requiring claims |
| **Approval** | Agent writes require human approval |
| **Risk** | Operational risk level (LOW/MED/HIGH) |

---

## Activation Strategy

```
Phase 1: ResearchAgent (read-only)
  └── Proves: durable execution, state machine, lease, fencing

Phase 2: + NewsAgent, CompetitorAgent, MeetingAgent, RelationshipAgent,
         TenderAgent, ContractAgent
  └── Proves: Tool architecture, evidence engine, canonical write path

Phase 3: + ForecastAgent, PricingAgent, ProposalAgent, RenewalAgent
  └── Proves: PDP integration, approval workflow, sandbox, signals

Phase 4+: AgentCoordinator
  └── Proves: multi-agent orchestration, fan-out, DAG workflows
```

---

## ResearchAgent — First Production Agent Rationale

| Criteria | Assessment | Evidence |
|----------|------------|----------|
| Business value | HIGH — every entity needs research before qualification | Core pipeline step |
| Data availability | HIGH — uses UBOM + FeatureStore scores | Existing APIs |
| Tool requirements | LOW — 3 tools, 2 existing capabilities | `company.lookup`, `graph.query`, `source.balady_lookup` |
| Risk | LOW — read-only enrichment, no destructive writes | Read-heavy |
| Write complexity | NONE in Phase 1 | Read-only execution |
| Evidence requirements | Phase 2 (deferred) | Not needed for read-only |
| Code changes needed | ZERO | Existing `GroundedBaseAgent.execute_grounded()` works as-is |
| Measurable outcome | AgentResult with structured analysis | Existing output schema |
