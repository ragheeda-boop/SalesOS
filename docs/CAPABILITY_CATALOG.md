# SalesOS — CAPABILITY CATALOG

> **السجل الكامل لكل Capability — البطاقة التعريفية، الحالة، التبعيات، الواجهات**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Capability Card Template

```
ID:             CAP-{NNN}
Name:           {English / Arabic}
Layer:          Kernel | Platform | Business | Application
Owner:          {team}
Priority:       P0 | P1 | P2 | P3
Status:         ✅ Complete | 🟡 Partial | ❌ Missing
Dependencies:   [CAP-xxx, CAP-yyy]
API Status:     REST | GraphQL | Both | None
UI Status:      Has UI | No UI
AI Status:      Has AI | No AI
Workflow:       Has Workflow | No Workflow
Events:         [event1, event2]
Metrics:        [metric1, metric2]
Docs:           [link to ADR, README]
Version:        v{current}
Roadmap:        Phase {I-VI}
```

---

## KERNEL CAPABILITIES

### CAP-001: Identity

| Field | Value |
|-------|-------|
| Layer | Kernel |
| Status | 🟡 Partial (backend 90%, persistence missing) |
| Dependencies | None |
| API | REST — 12 endpoints |
| UI | ❌ No UI |
| AI | ❌ No AI |
| Events | `TenantCreated`, `UserCreated`, `UserLoggedIn`, `APIKeyGenerated`, `RoleAssigned` |
| Metrics | tenant count, user count, active sessions, auth failures |
| Resilience | Timeout 10s, Retry 2x, Circuit breaker 5 failures |

### CAP-002: Company

| Field | Value |
|-------|-------|
| Layer | Kernel |
| Status | 🟡 Partial (backend 90%, persistence missing) |
| Dependencies | CAP-001 (Identity) |
| API | REST — 14 endpoints |
| UI | ❌ No UI |
| AI | ❌ No AI |
| Events | `OrganizationCreated`, `OrganizationUpdated`, `ContactAdded`, `LicenseCreated` |
| Metrics | company count, contact count, license count, enrichment coverage |
| Resilience | Timeout 10s, Retry 2x, Circuit breaker 5 failures |

### CAP-003: Search

| Field | Value |
|-------|-------|
| Layer | Kernel |
| Status | ✅ Complete (95%) |
| Dependencies | CAP-001, CAP-002 |
| API | Integrated (not standalone) |
| UI | ❌ No UI |
| AI | 🟡 Semantic search via pgvector |
| Events | `SearchExecuted` |
| Metrics | search count, latency p95, result count avg, zero result rate |
| Resilience | Timeout 5s, RRF fusion degrades gracefully |

### CAP-004: Timeline

| Field | Value |
|-------|-------|
| Layer | Kernel |
| Status | 🟡 Partial (backend 90%, persistence missing) |
| Dependencies | CAP-001 |
| API | Integrated |
| UI | ❌ No UI |
| AI | ❌ No AI |
| Events | Consumes all domain events |
| Metrics | events ingested, timeline queries, entity coverage |

---

## PLATFORM CAPABILITIES

### CAP-005: Data Fabric

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing (5% — scrapers only) |
| Dependencies | CAP-001, CAP-002, CAP-004 |
| API | ❌ |
| UI | ❌ |
| AI | ❌ |
| Events | `CollectorCompleted`, `EntityResolved`, `GoldenRecordUpdated` |
| Metrics | records ingested, resolution precision, dedup rate, pipeline latency |

### CAP-006: Feature Store

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |
| Dependencies | CAP-005, CAP-004 |
| API | ❌ |
| UI | ❌ |
| AI | ❌ |
| Events | `FeatureComputed`, `FeatureInvalidated` |
| Metrics | features computed, features consumed, computation latency |

### CAP-007: Knowledge Graph

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | 🟡 Neo4j configured, zero data |
| Dependencies | CAP-005 |
| API | ❌ |
| UI | ❌ |
| AI | ❌ |
| Events | `GraphRelationCreated`, `GraphRelationUpdated` |
| Metrics | nodes, edges, traversal latency |

### CAP-008: Revenue Graph

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |
| Dependencies | CAP-005, CAP-007 |
| API | ❌ |
| UI | ❌ |
| AI | ❌ |
| Events | `RevenueEdgeCreated`, `RevenueEdgeWeightUpdated` |
| Metrics | graph completeness, traversal depth, entity coverage |

### CAP-009: Workflow Engine

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |
| Dependencies | CAP-001, CAP-002 |
| API | ❌ |
| UI | ❌ |
| AI | ❌ |
| Events | `WorkflowTriggered`, `WorkflowCompleted`, `WorkflowFailed` |
| Metrics | workflows executed, success rate, avg duration |

### CAP-010: Semantic Cache

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |
| Dependencies | CAP-003 |
| API | ❌ |
| UI | ❌ |
| AI | 🟡 Embedding-based semantic matching |
| Events | `CacheHit`, `CacheMiss`, `CacheInvalidated` |
| Metrics | hit ratio, cost saved, avg response time |

---

## BUSINESS CAPABILITIES

### CAP-011: Company Intelligence

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | 🟡 Partial (backend 30%) |
| Dependencies | CAP-001, CAP-002, CAP-003, CAP-004 |
| API | REST — partial |
| UI | ❌ No UI |
| AI | ❌ No AI |
| Events | `CompanyInsightGenerated`, `CompanyProfileUpdated` |
| Metrics | profiles enriched, data sources, coverage % |

### CAP-012: Opportunity Management

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ✅ Complete (85%, in-memory) |
| Dependencies | CAP-001, CAP-002 |
| API | REST — 8 endpoints |
| UI | ❌ No UI |
| AI | ❌ No AI |
| Events | `OpportunityCreated`, `OpportunityMoved`, `OpportunityClosed` |
| Metrics | pipeline value, win rate, avg deal size, velocity |

### CAP-013: Pipeline Intelligence

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ✅ Complete (85%, in-memory) |
| Dependencies | CAP-012 |
| API | Integrated |
| UI | ❌ No UI |
| AI | 🟡 Stage prediction |
| Events | `PipelineStageChanged`, `PipelineForecastRefreshed` |
| Metrics | pipeline health, stage velocity, conversion rates |

### CAP-014: Forecast

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ✅ Complete (85%, in-memory) |
| Dependencies | CAP-012, CAP-013 |
| API | Integrated |
| UI | ❌ No UI |
| AI | 🟡 ML forecast model |
| Events | `ForecastUpdated`, `ForecastScenarioApplied` |
| Metrics | forecast accuracy, bias, coverage |

### CAP-015: Analytics & KPIs

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ✅ Complete (85%, in-memory) |
| Dependencies | CAP-001, CAP-002, CAP-012 |
| API | Integrated — 16 KPIs |
| UI | ❌ No UI |
| AI | ❌ No AI |
| Events | `KPICalculated`, `SnapshotTaken` |
| Metrics | KPI count, snapshot frequency |

### CAP-016: Recommendation

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ✅ Complete (90%, in-memory) |
| Dependencies | CAP-012, CAP-013, CAP-014, CAP-015 |
| API | Integrated — Rule engine |
| UI | ❌ No UI |
| AI | 🟡 Rule-based + ML |
| Events | `RecommendationGenerated`, `RecommendationAccepted`, `RecommendationRejected` |
| Metrics | recommendation count, acceptance rate, revenue influenced |

### CAP-017: GTM Intelligence

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ❌ Missing |
| Dependencies | CAP-011, CAP-012 |
| Events | `TerritoryAssigned`, `PlaybookActivated` |

### CAP-018: Marketing Intelligence

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ❌ Missing |

### CAP-019: Customer Success

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ❌ Missing |

### CAP-020: Customer Health Engine

| Field | Value |
|-------|-------|
| Layer | Business |
| Status | ❌ Missing |
| Dependencies | CAP-001, CAP-002, CAP-012, CAP-004 |

---

## INTELLIGENCE CAPABILITIES

### CAP-021: Revenue Brain

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |
| Dependencies | CAP-004, CAP-006, CAP-008, CAP-016 |
| Events | `NextBestActionComputed`, `BrainStateRefreshed` |

### CAP-022: AI Copilot

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |
| Dependencies | CAP-003, CAP-005, CAP-010 |

### CAP-023: Scoring Engine

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |
| Dependencies | CAP-006 (Feature Store) |

### CAP-024: Company DNA

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-025: AI Memory

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-026: Agent Runtime

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-027: Prompt Studio

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-028: AI Governance Portal

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-029: AI Playground

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-030: Experiment Engine

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

### CAP-031: Simulation Engine

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |

---

## DIGITAL CAPABILITIES

### CAP-032: Digital Twin Engine

| Field | Value |
|-------|-------|
| Layer | Intelligence |
| Status | ❌ Missing |
| Dependencies | CAP-004, CAP-006, CAP-008, CAP-021 |
| Components | State Manager, Predictor, Risk Detector, Scenario Simulator, Recommendation Engine, Feedback Loop |

### CAP-033: Entity Resolution

| Field | Value |
|-------|-------|
| Layer | Data |
| Status | ❌ Missing |
| Dependencies | CAP-005 |

---

## APPLICATIONS

### CAP-034: Company 360

| Field | Value |
|-------|-------|
| Layer | Application |
| Status | ❌ Missing |
| Dependencies | CAP-011, CAP-022, CAP-023, CAP-024 |

### CAP-035: Deal Room

| Field | Value |
|-------|-------|
| Layer | Application |
| Status | ❌ Missing |

### CAP-036: AI Copilot UI

| Field | Value |
|-------|-------|
| Layer | Application |
| Status | ❌ Missing |

---

## OS API CAPABILITIES

### CAP-037: REST API

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | 🟡 Partial (12+ endpoints, not all capabilities) |

### CAP-038: GraphQL API

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |

### CAP-039: MCP Server

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |

### CAP-040: Agent SDK

| Field | Value |
|-------|-------|
| Layer | Platform |
| Status | ❌ Missing |

---

## CAPABILITY MATRIX

```
                  Status        API    UI   AI   Events   DB    Priority
───────────────────────────────────────────────────────────────────────
Identity          🟡 90%        ✅12   ❌   ❌   ✅5     🟡    P0
Company           🟡 90%        ✅14   ❌   ❌   ✅4     🟡    P0
Search            ✅ 95%        ❌     ❌   🟡   ✅1     ✅    P1
Timeline          🟡 90%        ❌     ❌   ❌   📥all   🟡    P1
Data Fabric       ❌ 5%         ❌     ❌   ❌   ❌      ❌    P0
Feature Store     ❌ 0%         ❌     ❌   ❌   ❌      ❌    P1
Revenue Graph     ❌ 0%         ❌     ❌   ❌   ❌      🟡    P1
Revenue Brain     ❌ 0%         ❌     ❌   ❌   ❌      ❌    P1
Digital Twin      ❌ 0%         ❌     ❌   ❌   ❌      ❌    P1
MCP Server        ❌ 0%         ❌     ❌   ❌   ❌      ❌    P1
Company 360       ❌ 0%         ❌     ❌   ❌   ❌      ❌    P0
Deal Room         ❌ 0%         ❌     ❌   ❌   ❌      ❌    P1
AI Copilot        ❌ 0%         ❌     ❌   ❌   ❌      ❌    P2
```

---

*This catalog is the authoritative registry of all SalesOS capabilities. Every capability has a unique ID that is referenced across all documentation, code, and planning. New capabilities must be registered here before implementation begins.*
