# SalesOS vNext — Product Roadmap

> **Overall Readiness**: 7.5/10 (79-85% complete)
> **Current State**: 15 domains, 31 runtimes, 57 routers, 34 migrations, 93% coverage, 269 E2E tests
> **Target**: Production GA with full Arabic support, multi-tenancy, and AI platform

---

## Phase Overview

```
Phase 0 ██ Platform Stabilization        Sprint 1-2    (4 weeks)
Phase 1 ██ Design System V2              Sprint 3-4    (4 weeks)
Phase 2 ██████ Foundation Features       Sprint 5-6    (4 weeks)
Phase 3 ██ Intelligence Features         Sprint 7-8    (4 weeks)
Phase 4 ██ Revenue & Pipeline            Sprint 9-10   (4 weeks)
Phase 5 ██████ AI Platform               Sprint 11-12  (4 weeks)
Phase 6 ██ Automation & Knowledge        Sprint 13-14  (4 weeks)
Phase 7 ██████ Advanced Features         Sprint 15-16  (4 weeks)
Phase 8 ██████ Administration            Sprint 17-18  (4 weeks)
Phase 9 ████████████ Arabic & i18n       Sprint 19-20  (4 weeks)
Phase 10 ████ Production Hardening       Sprint 21-22  (4 weeks)
──────────────────────────────────────────────────────────────────
Total: 22 sprints ≈ 44 weeks (~11 months)
```

---

## Phase 0 — Platform Stabilization

| | |
|---|---|
| **Duration** | Sprint 1-2 (4 weeks) |
| **Themes** | Security fixes, infrastructure gaps, critical bugs |
| **Dependencies** | None — starts from current codebase |

### Deliverables

| Area | Deliverable | Risks Addressed |
|------|-------------|-----------------|
| Security | Add auth to webhooks router | R-001 (Critical) |
| Security | Parameterize all Neo4j queries | R-016 (Critical) |
| Security | Add auth to GraphQL endpoint | R-039 (Critical) |
| Security | Add rate limiting to MCP server | R-040 (High) |
| Backend | Fix body consumption bug in middleware | R-005 (High) |
| Backend | Fix N+1 workspace/NBA pattern (DataLoader) | R-006 (High) |
| Backend | Remove `print()` / `console.debug()` from production code | R-038 (Low) |
| Backend | Fix `vectors` table column type | R-037 (High) |
| Backend | Implement PostgreSQL NotificationRepository | R-036 (High) |
| DevOps | Configure Terraform remote state (S3/Azure + locking) | R-003 (High) |
| DevOps | Admin router state → PostgreSQL persistence | R-002 (High) |
| DevOps | Add Kafka healthcheck to Docker Compose | R-008 (Medium) |
| DevOps | Add Celery worker to Docker Compose | R-009 (Medium) |
| DevOps | Deploy Redis to production | R-011 (Medium) |
| DevOps | Add quarterly backup restore drill to runbook | R-007 (High) |
| Architecture | Split `api.ts` (1,240 lines) → per-domain router files | R-023 (High) |
| Architecture | Modularize `main.py` (773 lines) startup | R-024 (High) |
| Architecture | Decompose knowledge graph runtime (1,087 lines) | R-025 (High) |
| Architecture | Decompose decision engine (1,003 lines) | R-041 (High) |

### Definition of Done
- All P0 security risks resolved (R-001, R-016, R-039)
- Body consumption bug fixed
- Redis deployed in production
- Terraform remote state operational
- All monolithic files decomposed

---

## Phase 1 — Design System V2

| | |
|---|---|
| **Duration** | Sprint 3-4 (4 weeks) |
| **Themes** | Design language, component gaps, UI consistency |
| **Dependencies** | Phase 0 (stabilized platform) |

### Deliverables

| Area | Deliverable |
|------|-------------|
| Design | Audit existing 22 foundation components for v2 gaps |
| Design | Complete missing components (data table, date picker, tree view) |
| Design | Dark mode consistency pass across all domains |
| Design | RTL-proof component layout audit (before i18n) |
| Frontend | Add import boundary enforcement (eslint-plugin-import) | R-027 |
| Frontend | Reduce 284 `Any` types by 50% | R-035 |
| Frontend | Adopt React Query + Zustand state management | D-010 |
| Architecture | Implement API versioning (`/api/v1/...`) | R-026, D-003 |
| Architecture | Add OpenAPI codegen for client SDK | R-029 |

---

## Phase 2 — Foundation Features

| | |
|---|---|
| **Duration** | Sprint 5-6 (4 weeks) |
| **Themes** | Core domains: Dashboard, Companies, Search, Settings |
| **Dependencies** | Phase 1 (design system) |

### Deliverables

| Area | Deliverable |
|------|-------------|
| Dashboard | Dashboard v2 with customizable widgets |
| Dashboard | Widget SDK v1.1 gap analysis (if needed) | D-011 |
| Companies | Companies domain — full CRUD + entity resolution |
| Companies | Keyset pagination on all list endpoints | R-018 |
| Search | Hybrid search refinements (full-text + semantic) |
| Search | Add HNSW index on 3072-dim vectors | R-020 |
| Settings | Settings domain — 65% → 100% complete |
| Settings | Configuration management consolidation | D-014 |
| Platform | Build Helm umbrella chart for all runtimes | D-015 |

---

## Phase 3 — Intelligence Features

| | |
|---|---|
| **Duration** | Sprint 7-8 (4 weeks) |
| **Themes** | Company 360, Employee 360, Knowledge Graph |
| **Dependencies** | Phase 2 (Companies domain) |

### Deliverables

| Area | Deliverable |
|------|-------------|
| Company 360 | Company 360 view — signals, enrichment, timeline |
| Company 360 | Decision Provider integration for scoring |
| Employee 360 | Employee 360 view — signals, scoring, timeline |
| Knowledge Graph | Knowledge graph v2 with full traversal API |
| Knowledge Graph | Graph visualization widget |
| Knowledge Graph | Entity resolution pipeline enhancements |
| Feature Store | Feature Store v1 — feature registry, computation, serving |
| Platform | Nx/Turborepo build orchestration | D-001 |

---

## Phase 4 — Revenue & Pipeline

| | |
|---|---|
| **Duration** | Sprint 9-10 (4 weeks) |
| **Themes** | Pipeline management, Revenue analytics, CRM, Opportunities |
| **Dependencies** | Phase 3 (Company 360, Knowledge Graph) |

### Deliverables

| Area | Deliverable |
|------|-------------|
| Pipeline | Pipeline management — stages, deals, forecasting |
| Revenue | Revenue analytics — metrics, dashboards, reporting |
| CRM | CRM integration — sync, activity tracking |
| Opportunities | Opportunity management — scoring, routing |
| Scoring | Scoring engine — model management, A/B testing |
| Platform | Tenant-based partitioning strategy | R-017 |

---

## Phase 5 — AI Platform

| | |
|---|---|
| **Duration** | Sprint 11-12 (4 weeks) |
| **Themes** | Agent runtime, Multi-AI providers, AI tests, Evaluation |
| **Dependencies** | Phase 0 (body consumption bug fixed), Phase 2 (Search) |

### Deliverables

| Area | Deliverable | Risks Addressed |
|------|-------------|-----------------|
| AI | Implement agent runtime (real, not placeholder) | R-010 |
| AI | Add AI provider abstraction (OpenAI + Anthropic + local) | R-012, D-006 |
| AI | Write backend AI tests (from zero) | R-004 |
| AI | Add AI evaluation harness (prompt regression, quality) | R-004 |
| AI | Implement agent observability (tracing, logging) | — |
| AI | Resolve or document 5 runtime stubs | R-028 |
| AI | Implement agent runtime architecture (hybrid) | D-005 |
| Platform | Kafka full adoption — remove in-memory event bus | D-004 |

---

## Phase 6 — Automation & Knowledge

| | |
|---|---|
| **Duration** | Sprint 13-14 (4 weeks) |
| **Themes** | Workflow engine, Rules engine, RAG, Knowledge packs |
| **Dependencies** | Phase 5 (AI platform) |

### Deliverables

| Area | Deliverable |
|------|-------------|
| Workflow | Workflow engine — visual builder, triggers, actions |
| Workflow | Workflow runtime (not stub) |
| Rules | Rules engine — condition builder, evaluation |
| RAG | RAG pipeline — document ingestion, chunking, retrieval |
| Knowledge | Knowledge packs — pre-built industry content |
| Knowledge | Knowledge graph — semantic search improvements |
| Platform | Multi-tier caching strategy with Redis | D-009 |

---

## Phase 7 — Advanced Features

| | |
|---|---|
| **Duration** | Sprint 15-16 (4 weeks) |
| **Themes** | Data Fabric, Signals, Marketplace, Customer Success |
| **Dependencies** | Phase 5 (AI), Phase 6 (Workflow) |

### Deliverables

| Area | Deliverable | Risks Addressed |
|------|-------------|-----------------|
| Data Fabric | Build connector SDK | D-008 |
| Data Fabric | Implement top-3 connectors (HubSpot, Salesforce, Zoho) | R-033 |
| Data Fabric | Replace mock data with real connector data | R-013 |
| Signals | Signal detection pipeline — rule + ML-based |
| Marketplace | Extension API for third-party plugins | D-012 |
| Customer Success | Customer Success domain — health scores, alerts |
| Customer Success | Customer 360 — full domain completion |

---

## Phase 8 — Administration

| | |
|---|---|
| **Duration** | Sprint 17-18 (4 weeks) |
| **Themes** | Admin panel, Multi-tenancy, Settings, Audit |
| **Dependencies** | Phase 2 (Settings), Phase 7 (Data Fabric) |

### Deliverables

| Area | Deliverable | Risks Addressed |
|------|-------------|-----------------|
| Multi-tenancy | Tenant isolation — data separation, provisioning | R-015, R-031 |
| Multi-tenancy | Tenant-aware partitioning strategy | R-017 |
| Admin | Admin panel — user management, billing, audit log |
| Audit | Audit trail — immutable event log |
| Settings | Settings domain — 100% complete |
| Platform | PostgreSQL HA — streaming replication | R-021 |
| Platform | Wide companies table — vertical split | R-019 |

---

## Phase 9 — Arabic & i18n

| | |
|---|---|
| **Duration** | Sprint 19-20 (4 weeks) |
| **Themes** | Full i18n framework, Arabic UI, RTL QA |
| **Dependencies** | Phase 1 (design system audit for RTL), Phase 8 (all features stable) |

### Deliverables

| Area | Deliverable | Risks Addressed |
|------|-------------|-----------------|
| i18n | Implement react-intl (FormatJS) framework | D-007 |
| i18n | Arabic translation — full UI pass | R-014, R-030 |
| i18n | RTL layout — all components verified |
| i18n | Arabic text normalization fix (BUG-002) |
| i18n | Language switcher + persistence |
| i18n | Bidirectional date/number/currency formatting |
| QA | Full RTL QA pass — all 269 E2E tests pass in RTL |
| Docs | Arabic user guide |

---

## Phase 10 — Production Hardening

| | |
|---|---|
| **Duration** | Sprint 21-22 (4 weeks) |
| **Themes** | Performance optimization, Security final pass, Scale testing |
| **Dependencies** | All previous phases |

### Deliverables

| Area | Deliverable |
|------|-------------|
| Performance | Full load testing suite in CI (fix body consumption first) |
| Performance | OFFSET → keyset pagination on all endpoints |
| Performance | HNSW index optimization for 10M+ vectors |
| Performance | Query plan audit — all critical paths optimized |
| Security | External penetration test v2 |
| Security | Dependency audit — all zero vulns |
| Scale | Scale test — 1M companies, 10M events |
| Scale | Partition strategy verification |
| Infrastructure | K8s deployment validation (multi-node) |
| Infrastructure | Backup restore drill (automated) |
| Docs | Final runbook, SLA verification, operations guide |

---

## Dependency Graph

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
  │                      │                       │
  │                      ▼                       │
  └──────────────► Phase 5 ──► Phase 6 ◄────────┘
                                    │
                                    ▼
                              Phase 7 ──► Phase 8 ──► Phase 9 ──► Phase 10
```

- Phase 0 is the foundation — all other phases depend on platform stability
- Phase 3 (Intelligence) depends on Phase 2 (Foundation)
- Phase 5 (AI) depends on Phase 0 (body consumption fix) and Phase 2 (Search)
- Phase 6 (Automation) depends on Phase 5 (AI)
- Phase 9 (Arabic) depends on Phase 1 (design audit) and Phase 8 (all features stable)
- Phase 10 (Hardening) depends on everything being built

---

## Key Milestones

| Milestone | Phase | Sprint | Target Date |
|-----------|-------|--------|-------------|
| 🔴 Security baseline achieved | Phase 0 | Sprint 2 | +2 weeks |
| 🎨 Design system v2 complete | Phase 1 | Sprint 4 | +6 weeks |
| 🏗️ Foundation domains live | Phase 2 | Sprint 6 | +10 weeks |
| 🧠 AI platform operational | Phase 5 | Sprint 12 | +22 weeks |
| 🤖 Automation engine live | Phase 6 | Sprint 14 | +26 weeks |
| 🔌 Data Fabric real connectors | Phase 7 | Sprint 16 | +30 weeks |
| 👥 Multi-tenancy operational | Phase 8 | Sprint 18 | +34 weeks |
| 🌐 Arabic UI GA | Phase 9 | Sprint 20 | +38 weeks |
| ✅ vNext GA Launch | Phase 10 | Sprint 22 | +44 weeks |

---

## Phase Distribution by Domain Impact

```
              P0  P1  P2  P3  P4  P5  P6  P7  P8  P9  P10
Security      ██  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██
Infrastructure ██  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██
Architecture   ██  ██  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░
Design         ░░  ██  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██  ░░
Frontend       ░░  ██  ██  ░░  ░░  ░░  ░░  ░░  ░░  ██  ░░
Company        ░░  ░░  ██  ██  ░░  ░░  ░░  ░░  ░░  ░░  ░░
Search         ░░  ░░  ██  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██
Knowledge Graph ░░  ░░  ░░  ██  ░░  ░░  ██  ░░  ░░  ░░  ░░
CRM/Pipeline   ░░  ░░  ░░  ░░  ██  ░░  ░░  ░░  ░░  ░░  ░░
AI             ░░  ░░  ░░  ░░  ░░  ██  ██  ░░  ░░  ░░  ░░
Workflow       ░░  ░░  ░░  ░░  ░░  ░░  ██  ░░  ░░  ░░  ░░
Data Fabric    ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██  ░░  ░░  ░░
Multi-tenancy  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██  ░░  ░░
i18n/Arabic    ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██  ░░
Performance    ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ░░  ██
```

---

*Last updated: 2026-07-16*
