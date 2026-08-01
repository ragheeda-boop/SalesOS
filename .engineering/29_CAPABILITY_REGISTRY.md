---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 29 â€” CAPABILITY REGISTRY

> Purpose: single reference for SalesOS capabilities â€” the first source for assigning multi-agent work. Built from `docs/CAPABILITY_CATALOG.md` (40 CAP-###), `salesos/backend/runtime/capability_framework/` (14 decorator-registered), `salesos/backend/sdk/capability_registry.py` + `app/modules/registry.py` (~25 SDK), and `engineering-os/kernel/capability-registry.yaml` (~22 YAML).
> **IMPORTANT OBSERVED FACT: the string `CAP-###` appears nowhere in `salesos/backend/` code. Runtime identities are kebab/snake IDs. The 4 registries are NOT aligned (HIGH-severity drift â€” see Â§4 and 18).**

## 0. Registry sources

| Registry | Location | Entries | Identity scheme |
|---|---|---|---|
| Catalog (docs) | `docs/CAPABILITY_CATALOG.md` | 40 (`CAP-001..040`) | CAP-### |
| Decorator (runtime) | `salesos/backend/runtime/capability_framework/__init__.py` + `router.py` | 14 built-in | kebab IDs (`identity`, `company`, `data-fabric`, `search`, `timeline`, `knowledge-graph`, `feature-store`, `decision-engine`, `event-runtime`, `activity-intelligence`, `workflow`, `marketplace`, `capability-framework`) |
| SDK | `salesos/backend/sdk/capability_registry.py` + `app/modules/registry.py` | ~25 | `CapabilityType` names (domain/search/timeline/graph/workflow/ai/integration) |
| YAML (governance) | `engineering-os/kernel/capability-registry.yaml` | ~22 | `company-360`, `crm`, `ai`, ... (naming differs) |

> **Note (EOS v3.1):** the `crm` name above is a governance-YAML capability label in the `engineering-os` submodule. There is **no** SalesOS backend `app/modules/crm` and **no** `/api/v1/crm` route (v3.0 claimed both â€” invented; corrected in `14`, `23`, `24`).

## 1. Capability table (CAP-### catalog numbering; runtime IDs where mappable)

Legend â€” Status as observed in catalog: âœ… Complete (in-memory) Â· ðŸŸ¡ Partial Â· âŒ Missing. Runtime: STABLE/BETA/DRAFT/EXPERIMENTAL per `runtime/capability_framework`.

| ID | Name | Layer | Status (catalog) | Runtime | Owning code (DIR:) | APIs (FILE:) | DB (13) | Events | Tests (TST:) | ADR | Owner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CAP-001 | Identity | Kernel | ðŸŸ¡ Partial | STABLE | `app/modules/identity/` | `/api/v1/identity/*` (12) | users, tenants, refresh_token_families, device_sessions, token_blacklist, password_reset_tokens | TenantCreated, UserCreated, UserLoggedIn, APIKeyGenerated, RoleAssigned | identity tests (~88%) | ADR-034, ADR-001 | Backend/Cursor |
| CAP-002 | Company | Kernel | ðŸŸ¡ Partial | STABLE | `app/modules/company/`, `app/modules/contact/` | `/api/v1/companies/*`, `/api/v1/contacts` | companies, contacts, branches, licenses | OrganizationCreated/Updated, ContactAdded | company module tests | ADR-001 | Backend/Cursor |
| CAP-003 | Search | Kernel | âœ… 95% | STABLE | `runtime/search_runtime/`, `domains/search/`, `app/routers/search.py` | `/api/v1/search`, `/search/suggest`, `/search/similar/*` | pgvector, meilisearch, fulltext (pg_trgm) | SearchExecuted | Rule 4 frozen-interface tests | ADR-026 (file MISSING) | Backend/Cursor |
| CAP-004 | Timeline | Kernel | ðŸŸ¡ Partial | STABLE | `runtime/timeline_runtime/` | `/api/v1/timeline/*` | timeline_entries | consumes all domain events | timeline tests | ADR-001 | Backend/Cursor |
| CAP-005 | Data Fabric | Platform | âŒ Missing | STABLE | `runtime/data_fabric_runtime/`, `intelligence/data_fabric/` | `/api/v1/data-fabric/*` | scraper/source data | CollectorCompleted, EntityResolved | data_fabric tests | â€” | Shared |
| CAP-006 | Feature Store | Platform | âŒ Missing | STABLE | `domains/feature_store/`, `runtime/feature_store/` | `/api/v1/features/*`, `/api/v1/feature-store` | feature_store_* | FeatureComputed/Invalidated | feature_store tests | ADR-027 (file MISSING) | Backend/Cursor |
| CAP-007 | Knowledge Graph | Platform | ðŸŸ¡ Neo4j configured | BETA | `runtime/knowledge_graph_runtime/` | `/api/v1/graph/*` | Neo4j (external) | GraphRelationCreated/Updated | kgraph tests | ADR-028 (file MISSING) | Shared |
| CAP-008 | Revenue Graph | Platform | âŒ | â€” | (vision) | â€” | â€” | RevenueEdgeCreated | â€” | â€” | Shared |
| CAP-009 | Workflow Engine | Platform | âŒ | BETA | `app/routers/workflows.py`, `runtime/workflow_runtime/` (stub) | `/api/v1/workflows/*`, `/api/v1/jobs/*`, `/api/v1/webhooks/*` | workflow_definitions, workflow_executions, scheduled_jobs, job_executions, webhook_* | WorkflowTriggered/Completed/Failed | workflow/webhook tests | ADR-031 | Backend/Cursor |
| CAP-010 | Semantic Cache | Platform | âŒ | â€” | (vision) | â€” | redis | CacheHit/Miss | â€” | â€” | Shared |
| CAP-011 | Company Intelligence | Business | ðŸŸ¡ 30% | â€” | `frontend/src/features/company-intelligence/` | `/api/v1/companies/{id}/360` | â€” | CompanyInsightGenerated | company360Queries (FE) | ADR-002 | Claude |
| CAP-012 | Opportunity | Business | âœ… 85% in-memory | â€” | `app/routers/opportunities.py`, `domains/commercial/` | `/api/v1/opportunities` | opportunities, tasks | OpportunityCreated/Moved/Closed | commercial tests (Rule 5) | ADR-001 | Backend/Cursor |
| CAP-013 | Pipeline Intelligence | Business | âœ… 85% in-memory | â€” | `domains/commercial/pipeline/`, `runtime/pipeline_analytics/` | `/api/v1/pipeline-analytics/*` | pipeline tables | PipelineStageChanged | pipeline tests | ADR-001 | Backend/Cursor |
| CAP-014 | Forecast | Business | âœ… 85% in-memory | â€” | `domains/revenue/forecast/` | `/api/v1/forecast*` | forecast tables | ForecastUpdated | forecast tests | ADR-001 | Backend/Cursor |
| CAP-015 | Analytics & KPIs | Business | âœ… 85% in-memory | â€” | `domains/analytics/`, `app/routers/analytics.py` | `/api/v1/analytics*` | analytics_* | KPICalculated | analytics tests | ADR-001 | Backend/Cursor |
| CAP-016 | Recommendation | Business | âœ… 90% in-memory | BETA (decision-engine) | `domains/decision/`, `domains/decision_center/`, `runtime/decision_runtime/`, `app/modules/decision/` | `/api/v1/decision/*`, `/api/v1/decisions/*`, `/api/v1/decision-center/*` | decision_center_*, decisions | RecommendationGenerated/Accepted/Rejected | decision_center tests (tenant isolation) | ADR-033 (conflict) | Backend/Cursor |
| CAP-017 | GTM Intelligence | Business | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-018 | Marketing Intelligence | Business | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-019 | Customer Success | Business | âŒ | â€” | `frontend/src/features/customer-success/` | tenant health APIs | â€” | â€” | customer-success FE tests | â€” | Claude |
| CAP-020 | Customer Health Engine | Business | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-021 | Revenue Brain | Intelligence | âŒ | â€” | `runtime/nba_engine/` | `/api/v1/nba/*` | nba/score tables | NextBestActionComputed | nba_engine tests | â€” | Backend/Cursor |
| CAP-022 | AI Copilot | Intelligence | âŒ | â€” | `app/routers/copilot.py`, `app/routers/ai.py`, `domains/ai/` | `/api/v1/copilot`, `/api/v1/ai/*` | â€” | â€” | domains/ai tests | ADR-030 | Backend/Cursor |
| CAP-023 | Scoring Engine | Intelligence | âŒ | â€” | `domains/scoring/` | `/api/v1/scoring/*` | scoring_scorecards | â€” | scoring tests | ADR-033 | Backend/Cursor |
| CAP-024 | Company DNA | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-025 | AI Memory | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-026 | Agent Runtime | Intelligence | âŒ | stub | `runtime/agent_runtime/` (1-line stub) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-027 | Prompt Studio | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-028 | AI Governance Portal | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Human |
| CAP-029 | AI Playground | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-030 | Experiment Engine | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-031 | Simulation Engine | Intelligence | âŒ | stub | `runtime/simulation_runtime/` (stub) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-032 | Digital Twin Engine | Intelligence | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-033 | Entity Resolution | Data | âŒ | â€” | `app/modules/entity_resolution/`, `data/scripts/phase4_identity_v4.py` | `/api/v1/entity-resolution/*` | golden_records, entity_resolution_conflicts, entity_resolution_log, dead_letter_queue | EntityResolved, GoldenRecordUpdated | entity_resolution tests | ADR-025 (MISSING), ADR-Data-001 | Backend/Cursor |
| CAP-034 | Company 360 | Application | âŒ | â€” | `frontend/src/features/company-intelligence/widgets/company-360/` | `useCompany360` â†’ `/api/v1/companies/{id}/360` | â€” | â€” | FE company360 tests | ADR-002 | Claude |
| CAP-035 | Deal Room | Application | âŒ | â€” | (vision) | â€” | â€” | â€” | â€” | â€” | Shared |
| CAP-036 | AI Copilot UI | Application | âŒ | â€” | `frontend/src/features/*` + v3 | copilot UI routes | â€” | â€” | e2e copilot-page | â€” | Claude |
| CAP-037 | REST API | Platform | ðŸŸ¡ 12+ endpoints | STABLE (capability-framework) | `app/boot/routers.py` (67 include_router) | `/api/v1/*` | all | â€” | tests/test_integration.py | â€” | Shared |
| CAP-038 | GraphQL API | Platform | âŒ | â€” | `app/graphql/schema.py` | `/graphql` | all (read) | â€” | â€” | â€” | Shared |
| CAP-039 | MCP Server | Platform | âŒ | â€” | `app/routers/mcp.py` | `/api/v1/mcp/*` | â€” | â€” | tests/unit/test_mcp_server.py | â€” | Shared |
| CAP-040 | Agent SDK | Platform | âŒ | â€” | `sdk/`, `frontend/packages/platform/agents/` | â€” | â€” | â€” | Rule 3 arch test | ADR-001 | Shared |

## 2. Frontend capability-relevant packages (evidence)

| Package | Status | Notes |
|---|---|---|
| `@salesos/decision-platform` (alias â†’ `packages/platform/decision/index.ts`) | **STUB** | `decisionEngine`/`FeedbackEngine` throw `STUB_MSG`; only `ScoringEngine.score()` implements simple average; header references PROD-W6-001, AI_HONESTY.md |
| `@salesos/platform` | Contract-only shell | `kernel/platform.ts`; exports kernel + contracts/ai + contracts/revenue; no-op `Platform` |
| `@salesos/widgets`, `@salesos/charts-v3`, `@salesos/design-system`, `@salesos/layouts`, `@salesos/providers`, `@salesos/theme`, `@salesos/tokens`, `@salesos/workspace-generator` | Empty/stub | zero `src/` imports of any of these |
| `@salesos/widget-sdk`, `@salesos/workspace`, `@salesos/search`, `@salesos/renderer` | Production | canonical widget/workspace/search SDKs |

## 3. Backend decorator-registered capabilities (runtime/capability_framework) â€” 14

STABLE: identity, company, data-fabric, search, timeline, feature-store, event-runtime, activity-intelligence, capability-framework Â· BETA: knowledge-graph, decision-engine, workflow Â· DRAFT: marketplace.
Exposed via `GET /api/v1/capabilities` (router-level `verify_token`). Consumers: `app/routers/source_of_truth.py`, `runtime/ux_runtime/router.py`, `runtime/ui_schema_engine/router.py`, `runtime/object_viewer.py`, `runtime/widget_engine/__init__.py` (`WidgetRegistry.generate_from_capabilities()`).

## 4. Registry drift â€” observed facts (NOT fixed)

| # | Drift | Severity | Impact |
|---|---|---|---|
| 1 | 4 registries with different counts/IDs (40 / 14 / ~25 / ~22) | HIGH | Same capability has different identity per registry; automation can't rely on one source |
| 2 | `CAP-###` never present in backend code | HIGH | Docs numbering decoupled from runtime |
| 3 | YAML naming scheme (`company-360`, `crm`, `ai`) differs from catalog + SDK | HIGH | Governance vs runtime mismatch |
| 4 | YAML structural bug: code fence closes after `workflow` (line 377) then entries appended outside fence | MEDIUM | Registry section malformed |
| 5 | Audit finding: dual registry requires `sync_capability_registries.py` / `validate_capability_registries.py` just to stay aligned | HIGH | Structural defect (EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30 #9/#17; DEBT-ARC-003, E-21) |
| 6 | Decorator `/api/v1/capabilities` previously untested | MEDIUM | **Mitigated (DEC-131 READY FOR REVIEW):** `tests/contract/test_capabilities_api.py` — Arch/Val PENDING; does not close 5.1–5.3 |
| 7 | Catalog internal contradiction (CAPABILITY MATRIX vs sections, e.g. Search API âŒ vs Integrated; Timeline âœ… vs ðŸŸ¡) | MEDIUM | Catalog self-inconsistent |
| 8 | Naming drift across docs: audit calls CAP-017 "ICP Builder" vs catalog "GTM Intelligence" | LOW | Ambiguous references |

## 5. When this file changes

- When the capability catalog, runtime framework, SDK registry, or governance YAML changes. Also update `27/28` if ADRs change. Re-run `salesos/scripts/validate_capability_registries.py` (human-approved) to measure drift.

## 6. Usage as first assignment reference

Before assigning multi-agent work, consult this table: two capabilities are parallelizable if their Owning code (DIR:) sets do not overlap. See `26_AGENT_COORDINATION.md`.
