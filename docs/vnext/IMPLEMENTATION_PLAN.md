# SalesOS vNext — Implementation Plan

> **Detailed Execution Blueprint**
> Generated: 2026-07-16
> Sources: [ROADMAP.md](./ROADMAP.md), [TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md), [SPRINT_PLAN.md](./SPRINT_PLAN.md), [BACKLOG.md](./BACKLOG.md)
> Total Duration Estimate: 22 sprints (~44 weeks)

---

## Phase 0: Platform Stabilization (Sprints 1-2)

### Sprint 1 — Security & Critical Fixes

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Add auth to webhooks router (`app/routers/webhooks/router.py`) | Security | 2h | Backend | — |
| Fix `print()` in `metrics.py:18` | Cleanup | 30m | Backend | — |
| Fix `console.debug` in `monitoring.ts:126` | Cleanup | 30m | Frontend | — |
| Add `verify_token` to GraphQL router | Security | 4h | Backend | — |
| Fix Neo4j f-string queries to parameterized Cypher | Security | 4h | Backend | — |
| Add Kafka healthcheck in `docker-compose.yml` | DevOps | 1h | DevOps | — |
| Add Celery worker service to `docker-compose.yml` | DevOps | 2h | DevOps | — |
| Add MCP server rate limiting | Security | 2h | Backend | — |
| Fix middleware chain body consumption bug | Performance | 1d | Backend | — |
| Fix `search_companies` frontend tool returning empty | AI | 4h | AI/Frontend | — |

### Sprint 2 — Infrastructure & Performance

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Configure Terraform remote state (S3 + DynamoDB) | Infrastructure | 1d | DevOps | — |
| Implement backup restore verification in CI | DevOps | 2d | DevOps | Sprint 1 |
| Fix Workspace N+1 loop (`commercial.py:470-488`) | Performance | 2d | Backend | — |
| Fix NBA N+1 feed (`dashboard/router.py:163-208`) | Performance | 2d | Backend | — |
| Add pagination to 12+ unbounded endpoints | Performance | 2d | Backend | — |
| Consolidate 3 Redis client pools into single singleton | Performance | 4h | Backend | — |
| Add `@cached` to 6 missing endpoints | Performance | 1d | Backend | — |
| Fix `search_by_filters` double-query pattern | Performance | 2h | Backend | — |
| Align chart colors with backend tokens | Design | 1h | Frontend | — |
| Fix muted text WCAG AA contrast | Design | 1h | Frontend | — |

---

## Phase 1: Design System V2 (Sprints 3-4)

### Sprint 3 — Design System Consolidation

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Remove deprecated Foundation Card component | Design | 1h | Frontend | — |
| Migrate Login page to `@salesos/ui` + MUHIDE tokens | Design | 1d | Frontend | — |
| Fix Badge `primary` variant to use orange | Design | 30m | Frontend | — |
| Standardize page styling: `text-neutral-900` → `var(--text-primary)` | Design | 2d | Frontend | Sprint 2 |
| Add missing form components (Checkbox, Radio, Switch, Textarea) | Design | 3d | Frontend | — |
| Create DatePicker component | Design | 2d | Frontend | — |
| Componentize pagination component | Design | 1d | Frontend | Sprint 2 (API pagination) |

### Sprint 4 — Design System Expansion

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Create Storybook for visual component documentation | Design | 3d | Frontend | Sprint 3 |
| Add automated a11y assertion tests (`jest-axe`) | Testing | 1d | Frontend | Sprint 3 |
| Add visual regression tests (Chromatic/Percy) | Testing | 2w | Frontend | Sprint 3 |
| Create EmptyState component | Design | 1d | Frontend | — |
| Create Drawer component | Design | 2d | Frontend | — |
| Create Breadcrumb component | Design | 1d | Frontend | — |
| Create Combobox/Autocomplete component | Design | 2d | Frontend | — |

---

## Phase 2: Foundation Features (Sprints 5-6)

### Sprint 5 — Settings & Dashboard

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Create consolidated Settings UI page | Frontend | 3d | Frontend | Sprint 3 |
| Implement tenant settings module | Backend | 2d | Backend | Sprint 1 |
| Implement notification preferences UI | Frontend | 2d | Frontend | — |
| Implement widget-level data fetching for Dashboard | Performance | 3d | Frontend | Sprint 2 |
| Memoize Sidebar nav items | Performance | 2h | Frontend | — |

### Sprint 6 — Search & Companies

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement keyset/cursor pagination for search | Performance | 2d | Backend | Sprint 2 |
| Add cross-domain search federation | Search | 3d | Backend | — |
| Add company comparison views | Frontend | 2d | Frontend | — |
| Add bulk company operations UI | Frontend | 2d | Frontend | — |
| Implement deep pagination with SQL keyset | Performance | 1d | Backend | — |

---

## Phase 3: Intelligence Features (Sprints 7-8)

### Sprint 7 — Company 360 & Employee 360

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Create dedicated Company 360 consolidated view | Frontend | 3d | Frontend | Sprint 2 |
| Build firmographics enrichment pipeline | Backend | 3d | Backend | — |
| Enhance hierarchy visualization | Frontend | 2d | Frontend | — |
| Create dedicated Employee 360 consolidated frontend page | Frontend | 3d | Frontend | Sprint 3 |
| Build skills taxonomy system | Backend | 3d | Backend | — |

### Sprint 8 — Knowledge Graph & Signals

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Build interactive graph explorer UI | Frontend | 4d | Frontend | Sprint 3 |
| Build relationship browser | Frontend | 2d | Frontend | — |
| Build path analysis UI | Frontend | 2d | Frontend | — |
| Implement signal detection engine | AI | 3d | AI | — |
| Implement real-time signal processing | AI | 3d | AI | — |
| Build signal-specific alerting | Backend | 2d | Backend | — |

---

## Phase 4: Revenue & Pipeline (Sprints 9-10)

### Sprint 9 — Pipeline & CRM

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Add dedicated Contracts management UI | Frontend | 3d | Frontend | Sprint 3 |
| Add Email intelligence UI | Frontend | 3d | Frontend | — |
| Add Proposals management UI | Frontend | 3d | Frontend | — |
| Add Quotes management UI | Frontend | 3d | Frontend | — |
| Add Playbooks management UI | Frontend | 2d | Frontend | — |
| Build opportunity scoring refinement | AI | 2d | AI | — |

### Sprint 10 — Revenue & Forecast

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement ML-based revenue forecasting | AI | 3d | AI | — |
| Add pipeline coverage analysis | Backend | 2d | Backend | — |
| Add quota management | Backend/Frontend | 4d | Full-stack | — |
| Add territory management | Backend/Frontend | 3d | Full-stack | — |
| Add compensation tracking | Backend/Frontend | 3d | Full-stack | — |

---

## Phase 5: AI Platform (Sprints 11-12)

### Sprint 11 — Agent Runtime

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement agent runtime execution environment | AI | 4d | AI | Sprint 1 |
| Add multi-LLM provider support (Anthropic, local) | AI | 3d | AI | — |
| Add agent observability (tracing, logging, metrics) | AI | 3d | AI | — |
| Add embedding cache (Redis) | Performance | 1d | AI | — |
| Build agent monitoring dashboard | Frontend | 3d | Frontend | Sprint 3 |

### Sprint 12 — AI Quality

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Write backend AI tests (agents, RAG, data fabric) | Testing | 3d | AI | Sprint 11 |
| Create evaluation test cases with golden datasets | AI | 2d | AI | — |
| Fix HNSW index for 3072-dim vectors | Infrastructure | 2d | Backend | — |
| Fix `vectors` table type from ARRAY(FLOAT) to vector | Infrastructure | 1d | Backend | — |
| Build AI evaluation metrics dashboard | Frontend | 2d | Frontend | — |
| Implement agent memory persistence | AI | 2d | AI | — |

---

## Phase 6: Automation & Knowledge (Sprints 13-14)

### Sprint 13 — Workflow Automation

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Build visual workflow builder (drag-and-drop) | Frontend | 5d | Frontend | Sprint 3 |
| Add advanced branching/conditions | Backend | 3d | Backend | — |
| Add workflow templates library | Backend/Frontend | 3d | Full-stack | — |
| Implement workflow execution logging | Backend | 2d | Backend | — |
| Add rule execution log UI | Frontend | 2d | Frontend | — |

### Sprint 14 — RAG & Knowledge

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Add document management bulk operations | Backend | 2d | Backend | — |
| Add RAG query analytics | Backend/Frontend | 3d | Full-stack | — |
| Build knowledge pack authoring tools | Frontend | 3d | Frontend | Sprint 3 |
| Implement automated knowledge pack updates | AI | 2d | AI | — |

---

## Phase 7: Advanced Features (Sprints 15-16)

### Sprint 15 — Data Fabric

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Build unified data ingestion framework | Backend | 5d | Backend | Sprint 1 |
| Productionize scrapers (Balady, Taqeem) | Backend | 3d | Backend | — |
| Implement real Data Fabric connectors (not mock) | Backend | 4d | Backend | — |
| Build connector management UI | Frontend | 3d | Frontend | Sprint 3 |
| Add data quality scoring dashboard | Frontend | 2d | Frontend | — |

### Sprint 16 — Notifications & Enrichment

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement real-time push notifications | Backend/Frontend | 4d | Full-stack | — |
| Add email notification templates | Backend | 2d | Backend | — |
| Build notification preferences UI | Frontend | 2d | Frontend | Sprint 3 |
| Build unified enrichment framework | Backend | 3d | Backend | Sprint 15 |
| Add enrichment quality scoring | AI | 2d | AI | — |
| Implement deduplication with enrichment pipeline | Backend | 2d | Backend | Sprint 15 |

---

## Phase 8: Administration (Sprints 17-18)

### Sprint 17 — Multi-tenancy & Admin

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement tenant self-service provisioning UI | Frontend | 3d | Frontend | Sprint 3 |
| Migrate admin router from in-memory to PostgreSQL | Backend | 2d | Backend | — |
| Add tenant usage/billing | Backend/Frontend | 4d | Full-stack | — |
| Add tenant data migration tools | Backend | 2d | Backend | — |
| Build role management UI | Frontend | 2d | Frontend | — |

### Sprint 18 — Audit & Governance

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Create ADR directory and migrate decisions | Documentation | 2d | Architecture | — |
| Add API versioning strategy | Architecture | 3d | Architecture | — |
| Add OpenAPI/Swagger contract tests | Testing | 1w | Backend | — |
| Add database migration rollback tests | Testing | 1w | Backend | — |
| Consolidate `.env` files to centralized config | Infrastructure | 2d | Backend | — |
| Reduce Python `Any` types from 284 to <50 | Code Quality | 3d | Backend | — |

---

## Phase 9: Arabic & i18n (Sprints 19-20)

### Sprint 19 — Internationalization Framework

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement i18n framework (react-intl) | Frontend | 3d | Frontend | Sprint 3 |
| Translate UI to Arabic | Frontend | 5d | Frontend | Sprint 19 |
| Add RTL E2E tests | Testing | 2d | QA | — |
| Add Arabic documentation | Documentation | 3d | Docs | Sprint 19 |

### Sprint 20 — Arabic NLP Enhancement

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Enhance Arabic NLP pipeline | AI | 3d | AI | — |
| Add Arabic-specific ML models | AI | 3d | AI | — |
| Build Arabic search analytics | Backend/Frontend | 3d | Full-stack | — |
| Add local LLM support for KSA data sovereignty | AI | 3d | AI | Sprint 11 |

---

## Phase 10: Production Hardening (Sprints 21-22)

### Sprint 21 — Performance & Scale

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Implement data partitioning strategy | Infrastructure | 3d | Backend | — |
| Vertical partitioning of companies table | Infrastructure | 3d | Backend | — |
| Add performance regression tests in CI | Testing | 2w | DevOps | Sprint 2 |
| Add load testing to CI pipeline (k6/locust) | Testing | 2d | DevOps | — |
| Add chaos/resilience testing | Testing | 1w | QA | — |
| Add concurrent write conflict tests | Testing | 1w | QA | — |
| Add multi-tenant data isolation tests | Testing | 1w | QA | — |

### Sprint 22 — Final Hardening

| Task | Type | Effort | Owner | Depends On |
|------|------|--------|-------|------------|
| Deploy Redis in production | Infrastructure | 1w | DevOps | — |
| Implement Helm charts for K8s | DevOps | 2w | DevOps | — |
| Add frontend package import boundary enforcement | Architecture | 3d | Frontend | — |
| Refactor `api.ts` into domain modules | Architecture | 3d | Frontend | Sprint 3 |
| Refactor `main.py` into modular bootstrap | Architecture | 2d | Backend | — |
| Refactor `knowledge_graph_runtime` | Architecture | 3d | Backend | — |
| Refactor `decision/engine.py` | Architecture | 2d | Backend | — |
| Full integration test pass | QA | 1w | QA | Sprints 1-21 |

---

## Summary

| Phase | Focus | Sprints | Total Tasks | Est. Effort |
|-------|-------|---------|-------------|-------------|
| 0 | Platform Stabilization | 2 | 16 | ~15 days |
| 1 | Design System V2 | 2 | 12 | ~14 days |
| 2 | Foundation Features | 2 | 10 | ~14 days |
| 3 | Intelligence Features | 2 | 10 | ~21 days |
| 4 | Revenue & Pipeline | 2 | 10 | ~24 days |
| 5 | AI Platform | 2 | 10 | ~18 days |
| 6 | Automation & Knowledge | 2 | 8 | ~18 days |
| 7 | Advanced Features | 2 | 10 | ~24 days |
| 8 | Administration | 2 | 8 | ~18 days |
| 9 | Arabic & i18n | 2 | 6 | ~16 days |
| 10 | Production Hardening | 2 | 12 | ~30 days |
| **Total** | | **22** | **112** | **~212 days** |

---

## Key Milestones

| Week | Milestone |
|------|-----------|
| W2 | All critical security fixes deployed |
| W4 | N+1 patterns eliminated, pagination added |
| W8 | Design system V2 complete, Login page migrated |
| W10 | Settings & Dashboard consolidated |
| W14 | Company 360 & Employee 360 shipped |
| W18 | CRM UIs (Contracts, Email, Proposals, Quotes) |
| W22 | Agent runtime operational, AI tests passing |
| W26 | Workflow builder, RAG enhancements |
| W32 | Data Fabric live with real connectors |
| W36 | Multi-tenancy self-service |
| W40 | Arabic/RTL full support |
| W44 | Production hardening complete, vNext launched |

---

*This implementation plan is derived from the engineering audit findings. Adjust priorities and timelines based on business needs.*
