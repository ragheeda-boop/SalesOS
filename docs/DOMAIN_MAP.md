# SalesOS — DOMAIN MAP

> **خريطة النطاقات — Bounded Contexts, Relationships, Events, Dependencies**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Domain Context Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SALESOS PLATFORM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        KERNEL DOMAINS                                 │   │
│  │                                                                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │   │
│  │  │ Identity │←→│ Company  │←→│  Search  │←→│ Timeline │←→│  SDK   │ │   │
│  │  │ (CAP-001)│  │ (CAP-002)│  │ (CAP-003)│  │ (CAP-004)│  │(CORE)  │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      PLATFORM DOMAINS                                 │   │
│  │                                                                        │   │
│  │  ┌─────────────┐  ┌────────────┐  ┌───────────────┐  ┌────────────┐ │   │
│  │  │ Data Fabric │→│Feature Store│→│Knowledge Graph│→│Workflow    │ │   │
│  │  │ (CAP-005)   │  │ (CAP-006)  │  │ (CAP-007)     │  │ (CAP-009)  │ │   │
│  │  └─────────────┘  └────────────┘  └───────────────┘  └────────────┘ │   │
│  │       │                                                                │   │
│  │       ▼                                                                │   │
│  │  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐               │   │
│  │  │Revenue Graph │→│Semantic Cache │  │Entity Resol.  │                │   │
│  │  │ (CAP-008)    │  │ (CAP-010)    │  │ (CAP-033)     │                │   │
│  │  └──────────────┘  └──────────────┘  └───────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     BUSINESS DOMAINS                                  │   │
│  │                                                                        │   │
│  │  ┌────────────────────┐  ┌────────────────┐  ┌──────────────────┐    │   │
│  │  │ Company Intelligence│→│Opportunity Mgmt│→│Pipeline Intel    │    │   │
│  │  │ (CAP-011)          │  │ (CAP-012)      │  │ (CAP-013)        │    │   │
│  │  └────────────────────┘  └────────────────┘  └──────────────────┘    │   │
│  │       │                       │                       │               │   │
│  │       ▼                       ▼                       ▼               │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐        │   │
│  │  │ Forecast        │→│Analytics & KPIs│→│Recommendation    │        │   │
│  │  │ (CAP-014)       │  │ (CAP-015)      │  │ (CAP-016)        │        │   │
│  │  └────────────────┘  └────────────────┘  └──────────────────┘        │   │
│  │                                                                        │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐        │   │
│  │  │ GTM Intel      │  │ Marketing Intel│  │ Customer Success │        │   │
│  │  │ (CAP-017)      │  │ (CAP-018)      │  │ (CAP-019)        │        │   │
│  │  └────────────────┘  └────────────────┘  └──────────────────┘        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     INTELLIGENCE DOMAINS                               │   │
│  │                                                                        │   │
│  │  ┌─────────────┐  ┌───────────┐  ┌────────────┐  ┌────────────────┐  │   │
│  │  │Revenue Brain│→│AI Copilot │→│Scoring     │→│Company DNA     │  │   │
│  │  │ (CAP-021)   │  │ (CAP-022) │  │ (CAP-023)  │  │ (CAP-024)      │  │   │
│  │  └─────────────┘  └───────────┘  └────────────┘  └────────────────┘  │   │
│  │       │               │               │               │               │   │
│  │       ▼               ▼               ▼               ▼               │   │
│  │  ┌──────────────┐  ┌────────────┐  ┌───────────┐  ┌──────────────┐  │   │
│  │  │AI Memory     │→│Agent Runtime│→│Prompt    │→│AI Governance  │  │   │
│  │  │ (CAP-025)    │  │ (CAP-026)  │  │ (CAP-027) │  │ (CAP-028)    │  │   │
│  │  └──────────────┘  └────────────┘  └───────────┘  └──────────────┘  │   │
│  │                                                                        │   │
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐          │   │
│  │  │AI Playground │  │Experiment      │  │Simulation        │          │   │
│  │  │ (CAP-029)    │  │ (CAP-030)      │  │ (CAP-031)        │          │   │
│  │  └──────────────┘  └────────────────┘  └──────────────────┘          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      DIGITAL DOMAINS                                  │   │
│  │                                                                        │   │
│  │  ┌────────────────────┐                                                │   │
│  │  │ Digital Twin       │                                                │   │
│  │  │ (CAP-032)          │                                                │   │
│  │  └────────────────────┘                                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       APPLICATION DOMAINS                              │   │
│  │                                                                        │   │
│  │  ┌────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────────┐  │   │
│  │  │Company 360 │  │Deal Room │  │AI Copilot  │  │Revenue Dashboard │  │   │
│  │  │ (CAP-034)  │  │ (CAP-035)│  │ (CAP-036)  │  │                  │  │   │
│  │  └────────────┘  └──────────┘  └────────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Domain Dependency Table

| Domain | Depends On | Consumed By | Events Produced |
|--------|-----------|-------------|-----------------|
| Identity | — | All domains | tenant_created, user_created, user_logged_in, api_key_generated, role_assigned |
| Company | Identity | Search, Data Fabric, Opp, Analytics | organization_created, organization_updated, contact_added, license_created |
| Search | Identity, Company, Timeline | All domains | search_executed |
| Timeline | Identity, Company | All domains (consumer) | — (consumer only) |
| Data Fabric | Identity, Company | Feature Store, KG, Entity Res | collector_completed, entity_resolved, golden_record_updated |
| Feature Store | Data Fabric, Timeline | Scoring, DNA, Forecast, Revenue Brain | feature_computed |
| Knowledge Graph | Data Fabric, Timeline | Search, Revenue Brain, Digital Twin | graph_relation_created |
| Revenue Graph | Knowledge Graph, Opportunity | Revenue Brain, Digital Twin | revenue_edge_created |
| Opportunity | Identity, Company | Pipeline, Forecast, Analytics | opp_created, opp_stage_changed, opp_closed_won, opp_closed_lost |
| Forecast | Opportunity, Analytics | Revenue Brain, Digital Twin | forecast_updated, forecast_scenario_applied |
| Revenue Brain | All intelligence domains | Digital Twin, Recommendation | next_best_action_computed |
| Digital Twin | All domains | — | state_refreshed, risk_detected, recommendation_generated |
| Workflow | Identity, Company | — | workflow_triggered, workflow_completed, workflow_failed |

---

## Communication Patterns

| Pattern | Mechanism | Example |
|---------|-----------|---------|
| Sync (Request-Response) | FastAPI → Service → Repository | Get company profile |
| Async (Event-Driven) | EventBus → Projections | Company created → Update search index |
| Scheduled (Cron) | APScheduler → Workflow | Daily forecast recomputation |
| Agent (AI-Driven) | LangGraph → Tools | Research agent searches web |
| Streaming (Real-time) | WebSocket → Subscription | Live Digital Twin updates |

---

## Domain Isolation Rules

1. Domains communicate ONLY through events and the Capability Registry
2. No direct Python imports between domains (enforced by arch tests)
3. Shared value objects live in `salesos/sdk/domain/` — not in any domain
4. Cross-domain queries go through the API Gateway → Capability Router
5. Domain events are the contract — changing an event schema requires coordination with all consumers

---

## Context Boundary Summary

```
KERNEL (9 domains):     Identity, Company, Search, Timeline, SDK, Events, Metadata,
                        Capability Registry, Universal Timeline
PLATFORM (6 domains):   Data Fabric, Feature Store, Knowledge Graph, Revenue Graph,
                        Workflow Engine, Semantic Cache
BUSINESS (9 domains):   Company Intel, Opportunity, Pipeline, Forecast, Analytics,
                        Recommendation, GTM Intel, Marketing Intel, Customer Success
INTELLIGENCE (11):      Revenue Brain, AI Copilot, Scoring, DNA, AI Memory,
                        Agent Runtime, Prompt Studio, AI Governance, AI Playground,
                        Experiment, Simulation
DIGITAL (1):            Digital Twin
APPLICATION (4):        Company 360, Deal Room, AI Copilot UI, Revenue Dashboard
OS API (4):             REST, GraphQL, MCP Server, Agent SDK
```

---

*This domain map is the authoritative reference for bounded contexts and their relationships. All new capabilities must be placed in the correct domain layer. Cross-domain communication must follow the defined patterns.*
