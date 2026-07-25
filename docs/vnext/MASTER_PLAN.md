# SalesOS vNext — Master Plan

> **Author**: Chief Software Architect
> **Status**: Draft for Architecture Review Board
> **Version**: v1.0
> **Last Updated**: 2026-07-16

---

## 1. Current Platform Status

SalesOS has reached a robust **7.5/10 overall maturity**. The platform successfully powers **15 DDD domains** across **31 runtimes**, **26 modules**, and **57 routers**, backed by **34 database migrations**. Security posture is a verified **10/10** (external pentest confirmed), with **93% test coverage** across **2,110+ total tests** (269 E2E).

However, the platform exhibits a **long-tail completion problem**: the first 60-70% of each domain is well-built, but the final 20-30% — edge cases, advanced workflows, resilience, and AI-native integration — remains incomplete. Overall completion sits at **~79-85%**, concentrated in core CRM features while intelligence, automation, and data fabric capabilities lag.

This plan defines the architectural vision, priorities, and measurable criteria to close that gap and transform SalesOS from a capable CRM into an **AI-native Revenue Intelligence Platform**.

---

## 2. Target Vision for vNext

> **SalesOS vNext transforms from a powerful CRM into an AI-native Revenue Intelligence Platform** — where every user interaction is augmented by intelligence, every decision is data-driven, and every workflow is automated.

### Key Tenets

| Tenet | Description |
|-------|-------------|
| **AI-Native by Default** | AI is not a feature — it is the runtime. Every domain exposes intelligence via the Decision Platform. Agents are first-class system components with tests, observability, and lifecycle management. |
| **Zero-Trust Architecture** | Every endpoint authenticated, every request authorized, every data access audited. No exceptions. |
| **Data-First Platform** | Entity Resolution, Knowledge Graph, Feature Store, and Data Fabric form the foundation. All insights derive from a unified, consistent data layer. |
| **Multi-Tenant by Design** | Tenant isolation, data partitioning, and quota management are baked into every layer — not bolted on. |
| **Global-Ready** | Full Arabic/RTL support, localization framework, KSA PDPL compliance, and region-aware data residency from day one. |
| **Self-Service Intelligence** | Business users configure scoring, workflows, and decisions without engineering involvement. |

---

## 3. Current Completion Summary

| # | Area | Completion | Status |
|---|------|-----------|--------|
| 1 | Security | 95% | 🟢 Near Complete |
| 2 | Dashboard | 95% | 🟢 Near Complete |
| 3 | Backend Platform | 92% | 🟢 Near Complete |
| 4 | Search | 92% | 🟢 Near Complete |
| 5 | Documentation | 92% | 🟢 Near Complete |
| 6 | Testing | 90% | 🟢 Strong |
| 7 | Frontend Platform | 90% | 🟢 Strong |
| 8 | Monitoring | 90% | 🟢 Strong |
| 9 | Companies | 90% | 🟢 Strong |
| 10 | Decision Intelligence | 85% | 🟡 Needs Polish |
| 11 | Automation | 85% | 🟡 Needs Polish |
| 12 | AI | 85% | 🟡 Needs Polish |
| 13 | Entity Resolution | 85% | 🟡 Needs Polish |
| 14 | Company 360 | 80% | 🟡 Needs Work |
| 15 | Knowledge Graph | 80% | 🟡 Needs Work |
| 16 | Infrastructure | 78% | 🟡 Needs Work |
| 17 | CRM | 75% | 🟡 Significant Gap |
| 18 | Revenue | 75% | 🟡 Significant Gap |
| 19 | Signals | 75% | 🟡 Significant Gap |
| 20 | Employee 360 | 75% | 🟡 Significant Gap |
| 21 | Employee Intelligence | 70% | 🔴 Lagging |
| 22 | Notifications | 70% | 🔴 Lagging |
| 23 | Enrichment | 70% | 🔴 Lagging |
| 24 | Multi-tenancy | 72% | 🔴 Lagging |
| 25 | Arabic / RTL | 72% | 🔴 Lagging |
| 26 | Customer Success | 72% | 🔴 Lagging |
| 27 | Admin | 75% | 🟡 Significant Gap |
| 28 | Settings | 65% | 🔴 Critical Gap |
| 29 | Data Fabric | 65% | 🔴 Critical Gap |
| 30 | Frontend Design System | ~70% | 🔴 Lagging |

**Aggregate View**: ~320 sub-features across 35 areas: **~160 complete**, **~100 partial**, **~55 missing**, **~5 not started**.

---

## 4. Production Readiness Assessment

### 🟢 Production-Ready

| Area | Confidence | Evidence |
|------|-----------|----------|
| Security Posture | High (10/10) | External pentest verified, RBAC, CSRF, rate limiting, all routers authed |
| Search | High | Hybrid search (full-text + semantic, RRF fusion), trigram indexes, p95 <50ms |
| Dashboard | High | Widget SDK v1.0 frozen, Container/View pattern, 103 widget contract tests |
| Identity & Auth | High | JWT, tiered rate limiting, frozen interface |
| Monitoring | Medium | Prometheus/Grafana, alerting deployed, 9/10 |
| Core Backend Platform | High | 92% complete, all routers structured |

### 🟡 Functional but Needs Hardening

| Area | Issues |
|------|--------|
| Decision Intelligence | Scoring engine works but lacks comprehensive test coverage for decision chains |
| Entity Resolution | pg_trgm + merge pipeline complete, edge cases and conflict resolution need work |
| Knowledge Graph | 1,087-line runtime file — needs refactoring before production confidence |
| Companies | 90% complete, remaining 10% is bulk operations and advanced filtering |
| Testing Infrastructure | 90% coverage but backend AI tests at 0% |
| Automation / Workflows | Workflow engine exists, advanced branching and conditional logic incomplete |

### 🔴 Not Production-Ready

| Area | Critical Blockers |
|------|-------------------|
| **Data Fabric** | 65% — Feature Store exists but Settings and Data Fabric domains are the lowest scoring areas. No unified data access layer across domains. |
| **Multi-tenancy** | 72% — Tenant isolation partially implemented, missing quota management, tenant provisioning not automated |
| **Arabic / RTL** | 72% — Login page uses shadcn/ui tokens not MUHIDE tokens, chart colors mismatch, muted text fails WCAG AA (2.9:1) |
| **Employee Intelligence** | 70% — Signals domain incomplete, employee scoring not integrated with Decision Platform |
| **Notifications** | 70% — Missing webhook auth (CRITICAL), no unified notification bus, Kafka deferred |
| **Enrichment** | 70% — Async pipeline works but data quality metrics and fallback strategies incomplete |
| **Settings** | 65% — One of two lowest-scoring domains, lacks comprehensive admin UI |
| **Frontend Design System** | Missing Checkbox, Radio, Switch, Textarea, DatePicker components; design token inconsistencies |

---

## 5. Architecture Health

### 🟢 Healthy

| Component | Status | Notes |
|-----------|--------|-------|
| Identity Domain | 100% | Frozen interface, no debt |
| Widget SDK | 100% | v1.0 Feature Freeze, ADR-003 |
| Search Domain | 95% | PostgreSQL repos, no debt |
| CRM Domain | 95% | API-backed, DecisionProvider integrated |
| Scoring Domain | 95% | ScoringEngine → Decision Platform bridge |
| AI Domain | 95% | 92% test coverage (backend: 0% — see below) |
| Timeline Domain | 95% | TimelineService + Decision Platform |
| Workflow Domain | 95% | Container/View + Decision Platform |
| Entity Resolution | 95% | pg_trgm + merge pipeline |
| Feature Store | 95% | Data Fabric domain |

### 🟡 Needs Attention

| Component | Issues |
|-----------|--------|
| **Knowledge Graph Runtime** | 1,087-line single file — violates Single Responsibility Principle. Must be decomposed. |
| **Backend `api.ts`** | 1,240-line file — monolith router. Must be split by domain. |
| **Main Entry Point** | 773-line `main.py` — startup logic, middleware, router registration all conflated. |
| **Agent Runtime** | Placeholder "PLANNED FOR RT3" — agents exist in registry but cannot execute autonomously. |
| **Vendor Lock-in** | Only OpenAI supported for AI features — no provider abstraction. |
| **Cross-Domain Data Access** | No unified Data Fabric layer — domains access data ad-hoc. |
| **Webhooks** | No authentication on webhooks router — **CRITICAL SECURITY GAP** despite overall 10/10 security posture. |

### 🔴 Needs Immediate Refactoring

| Component | Severity | Action Required |
|-----------|----------|-----------------|
| `knowledge_graph_runtime` (1,087 lines) | High | Decompose into service + repository + router pattern |
| `api.ts` (1,240 lines) | High | Split by bounded context |
| `main.py` (773 lines) | Medium | Extract startup into boot sequence modules |
| N+1 workspace loops | Critical | Fix in all workspace/NBA query paths |
| Middleware body consumption bug | Critical | Fix middleware chain to not consume request body before route handler |
| 12+ unbounded pagination endpoints | High | Add keyset/cursor pagination everywhere |

---

## 6. Technical Health

### Code Quality

| Metric | Score | Assessment |
|--------|-------|------------|
| Overall Code Quality | 7/10 | Functional but inconsistent across domains |
| Architecture Compliance | 95% | Verified by automated script — target achieved |
| Pattern Scan | 95%+ | 80 violations resolved |
| Technical Debt | Low | 1 tracked item (TD-004 resolved, TD-005 resolved) |

### Architecture Hotspots

| File | Lines | Problem |
|------|-------|---------|
| `api.ts` | 1,240 | Monolithic router — violates DDD bounded context isolation |
| `main.py` | 773 | Startup/middleware/registration spaghetti — violates separation of concerns |
| `knowledge_graph_runtime.py` | 1,087 | God object — violates single responsibility |

### Testing

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Unit Test Coverage | 93% | 85% | 🟢 Exceeded |
| Integration Test Coverage | 70% | 70% | 🟢 Met |
| E2E Coverage | 60% | 60% | 🟢 Met |
| E2E Tests | 269 | 250+ | 🟢 Exceeded |
| Total Tests | 2,110+ | 2,000+ | 🟢 Exceeded |
| **Backend AI Tests** | **0** | Required | 🔴 **Critical Gap** |
| **Agent Runtime Tests** | **0** | Required | 🔴 **Critical Gap** |
| **RAG Pipeline Tests** | **0 (empty test dir)** | Required | 🔴 **Critical Gap** |

### Performance

| Aspect | Score | Critical Issues |
|--------|-------|-----------------|
| Overall Performance | 6.5/10 | Multiple systemic issues |
| DB-Level | 8.2/10 | p95 <50ms at 100k companies |
| Endpoint Budgets | All within budget | After ILIKE trigram fix |
| **Middleware Body Consumption** | 🔴 Critical | Blocks HTTP load testing entirely |
| **N+1 Patterns** | 🔴 Critical | Workspace and NBA query paths |
| **Unbounded Pagination** | 🔴 Critical | 12+ endpoints return all results |
| **Redis Pool Sprawl** | 🟡 Medium | 3 separate Redis pool instances |

---

## 7. Business Readiness

### Core CRM (75%)

| Capability | Status | Gap |
|-----------|--------|-----|
| Lead Management | Present | Advanced scoring/routing incomplete |
| Contact Management | Present | Bulk operations missing |
| Pipeline Management | Present | Advanced forecasting incomplete |
| Activity Tracking | Present | Timeline integration needs depth |
| Deal Management | Present | Revenue intelligence integration incomplete |

### Revenue Intelligence (75%)

| Capability | Status | Gap |
|-----------|--------|-----|
| Revenue Forecasting | Partial | No ML-backed models |
| Pipeline Analytics | Present | Advanced insights missing |
| Quota Management | Missing | Not started |
| Territory Planning | Missing | Not started |
| Deal Risk Scoring | Partial | Scoring engine exists, models not trained |

### Decision Intelligence (85%)

| Capability | Status | Gap |
|-----------|--------|-----|
| Scoring Engine | Present | Comprehensive, integrated |
| Decision Platform | Present | DecisionProvider in most domains |
| Rule Engine | Present | Advanced conditionals missing |
| What-If Analysis | Missing | Not started |

### AI Capabilities (85%)

| Capability | Status | Gap |
|-----------|--------|-----|
| Prompt Registry | Present | Complete |
| AIService | Present | OpenAI-only, no provider abstraction |
| RAG Pipeline | Present | Test directory empty |
| Agent Runtime | **Placeholder** | "PLANNED FOR RT3" — cannot execute |
| Backend AI Tests | **0** | Critical gap |
| Model Evaluation | Partial | Basic, no systematic evaluation |

### Automation / Workflows (85%)

| Capability | Status | Gap |
|-----------|--------|-----|
| Workflow Engine | Present | Core engine functional |
| Workflow Builder | Present | Advanced branching incomplete |
| Webhook Support | Present | **No auth — critical security gap** |
| Scheduled Jobs | Partial | Missing advanced scheduling |

### Employee Intelligence (70%)

| Capability | Status | Gap |
|-----------|--------|-----|
| Employee Signals | Partial | Collection works, analysis incomplete |
| Employee Scoring | Partial | Not fully integrated with Decision Platform |
| Employee 360 | 75% | View exists, intelligence layer missing |

### Data & Foundation

| Capability | Status | Gap |
|-----------|--------|-----|
| Entity Resolution | 85% | Core pipeline works, edge cases remain |
| Knowledge Graph | 80% | Runtime needs refactoring, query optimization |
| Feature Store | 95% | New, well-architected |
| Data Fabric | 65% | **Critical gap** — no unified data layer |
| Multi-tenancy | 72% | Partial isolation, no quota management |
| Arabic / RTL | 72% | Token inconsistencies, WCAG AA failures |

---

## 8. AI Readiness

### Maturity Assessment

| Dimension | Score | Status |
|-----------|-------|--------|
| AI Feature Completeness | 85% | 🟡 Core AI works, backend tests absent |
| Agent Runtime | 0% | 🔴 Placeholder only |
| AI Test Coverage (Backend) | 0% | 🔴 Critical gap |
| RAG Pipeline Tests | 0% | 🔴 Empty test directory |
| Model Diversity | 20% | 🔴 OpenAI-only vendor lock-in |
| Prompt Registry | 95% | 🟢 Complete and well-maintained |
| Evaluation Framework | 30% | 🔴 Basic, no systematic evaluation |
| AI Observability | 40% | 🟡 Partial, no dedicated AI monitoring |

### Architecture Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| Agent Runtime is placeholder | Critical | Cannot execute autonomous agents |
| Zero backend AI tests | Critical | No regression safety for AI features |
| OpenAI vendor lock-in | High | Single point of failure, no fallback |
| RAG test directory empty | High | Pipeline reliability unverifiable |
| No AI-specific monitoring | Medium | Cannot detect model drift or degradation |
| 15 agents registered but untested | Medium | Agent contracts unverified |

### vNext AI Targets

| Target | Current | Goal |
|--------|---------|------|
| Agent Runtime | Placeholder | Production runtime with lifecycle, retry, observability |
| AI Test Coverage | 0% | 85%+ for backend AI code |
| Supported LLM Providers | 1 (OpenAI) | 3+ (OpenAI, Anthropic, open-source fallback) |
| RAG Test Coverage | 0 tests | Full contract tests for retrieval, reranking, synthesis |
| Model Evaluation | Ad-hoc | Systematic eval harness with regression detection |
| AI Observability | Partial | Full tracing, token tracking, cost attribution, drift detection |

---

## 9. Top 10 Priorities

### Priority 1: Fix Critical Security Gap — Webhooks Authentication 🔴
**Impact**: The webhooks router has NO authentication. Despite the 10/10 security posture score from external pentest, this is an unauthenticated endpoint that could be exploited. This is the single most critical security finding and must be fixed immediately.
**Effort**: 1 day
**Dependency**: None

### Priority 2: Fix Middleware Body Consumption Bug 🔴
**Impact**: This bug blocks all HTTP-level load testing and breaks any middleware or handler that needs to read the request body after the middleware chain. Currently, the middleware consumes the stream, leaving handlers with empty bodies.
**Effort**: 2–3 days
**Dependency**: Backend Platform team

### Priority 3: Fix N+1 Query Patterns in Workspace & NBA Paths 🔴
**Impact**: Systemic N+1 patterns cause severe performance degradation in workspace listing and NBA (Next Best Action) recommendation queries. This is the primary contributor to the 6.5/10 performance score.
**Effort**: 1 week
**Dependency**: Backend Platform team

### Priority 4: Implement Pagination on All List Endpoints 🟡
**Impact**: 12+ endpoints return unbounded result sets. As tenant data grows, this will cause memory exhaustion, network timeouts, and poor UX. Every list endpoint must support cursor-based (keyset) pagination.
**Effort**: 2 weeks
**Dependency**: Backend Platform team

### Priority 5: Decompose Three Monolithic Files 🟡
- **`api.ts`** (1,240 lines) — split by bounded context
- **`main.py`** (773 lines) — extract boot sequence modules
- **`knowledge_graph_runtime`** (1,087 lines) — service + repository + router pattern
**Impact**: All three files violate Single Responsibility Principle. They block parallel development, make testing difficult, and increase merge conflict probability.
**Effort**: 2–3 weeks
**Dependency**: Architecture Board approval of decomposition plan

### Priority 6: Build Agent Runtime from Placeholder to Production 🟡
**Impact**: The 15 registered agents cannot execute — the runtime is a placeholder string "PLANNED FOR RT3". This blocks the entire AI-native vision. Agents must have lifecycle management, retry logic, observability, and contract tests.
**Effort**: 3–4 weeks
**Dependency**: AI domain team

### Priority 7: Achieve Backend AI Test Coverage (85%+) 🟡
**Impact**: Zero backend AI tests means no regression safety for the entire AI domain (AIService, PromptRegistry, RAG pipeline, agents). This is a governance violation under the Engineering Constitution (Article 2.2).
**Effort**: 2 weeks
**Dependency**: AI domain team

### Priority 8: Implement Provider Abstraction for LLMs 🟡
**Impact**: OpenAI-only support creates vendor lock-in, single point of failure, and no fallback for production outages. Abstract behind `LLMProvider` interface with OpenAI, Anthropic, and local open-source implementations.
**Effort**: 2–3 weeks
**Dependency**: AI domain team

### Priority 9: Complete Design System — Missing Components & Token Audit 🟡
**Impact**: Login page uses shadcn/ui tokens (not MUHIDE), chart colors mismatch between frontend/backend, Checkbox/Radio/Switch/Textarea/DatePicker all missing, and muted text fails WCAG AA (2.9:1). This blocks UI consistency and accessibility compliance.
**Effort**: 3 weeks
**Dependency**: Frontend Platform team

### Priority 10: Data Fabric & Multi-tenancy Hardening 🟡
**Impact**: Data Fabric (65%) and Settings (65%) are the two lowest-scoring domains. Multi-tenancy (72%) lacks quota management and automated provisioning. These are foundational — every other domain depends on them for production scale.
**Effort**: 4–6 weeks
**Dependency**: Backend Platform + Infrastructure teams

### Quick Wins (Within First Sprint)

| # | Item | Effort |
|---|------|--------|
| QW-1 | Webhooks auth fix | 1 day |
| QW-2 | Fix muted text WCAG AA contrast | 1 day |
| QW-3 | Fix login page token mismatch (shadcn/ui → MUHIDE) | 1 day |
| QW-4 | Fix chart color sync between frontend/backend | 1 day |
| QW-5 | Consolidate 3 Redis pools into 1 | 2 days |
| QW-6 | Create RAG pipeline test directory + basic tests | 2 days |
| QW-7 | Add admin auth to in-memory admin stores | 1 day |
| QW-8 | Add FastAPI-level Depends(verify_token) to GraphQL endpoints | 1 day |

---

## 10. Success Criteria for vNext

### Gates

| Gate | Criteria | Current | Target |
|------|----------|---------|--------|
| **G-1** | Webhooks router requires authentication | ❌ Fails | ✅ Pass |
| **G-2** | N+1 patterns eliminated from workspace and NBA paths | ❌ Fails | ✅ Pass (verified by perf scan) |
| **G-3** | Middleware chain does not consume request body | ❌ Fails | ✅ Pass (HTTP load testing works) |
| **G-4** | All list endpoints paginated (keyset/cursor) | 12+ missing | ✅ 100% compliance |
| **G-5** | Backend AI test coverage ≥ 85% | 0% | ✅ ≥ 85% |
| **G-6** | Agent runtime production-ready (lifecycle, retry, observability) | Placeholder | ✅ Production runtime |
| **G-7** | ≥ 2 LLM providers supported (abstraction layer complete) | 1 (OpenAI) | ✅ ≥ 2 |
| **G-8** | No file exceeds 600 lines in main application code | 3 files > 700 lines | ✅ All files ≤ 600 lines |
| **G-9** | Frontend design system: all missing components built + token audit clean | 5 missing, WCAG AA fail | ✅ Complete, AA pass |
| **G-10** | Multi-tenancy: quota management, automated provisioning | 72% | ✅ ≥ 90% |
| **G-11** | Data Fabric: unified data access layer across all domains | 65% | ✅ ≥ 85% |
| **G-12** | Domain completion: every domain ≥ 85% | 9 domains below 85% | ✅ All ≥ 85% |

### Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Overall Maturity | 7.5/10 | ≥ 9.0/10 |
| Architecture Score | 8/10 | ≥ 9.5/10 |
| Code Quality Score | 7/10 | ≥ 9.0/10 |
| Testing Score | 8/10 | ≥ 9.5/10 |
| DevOps Score | 8/10 | ≥ 9.5/10 |
| Documentation Score | 7/10 | ≥ 9.0/10 |
| Product Completeness | 7/10 | ≥ 9.0/10 |
| Performance Score | 6.5/10 | ≥ 9.0/10 |
| AI Test Coverage | 0% | ≥ 85% |
| Overall Completion | ~79-85% | ≥ 95% |
| Total Tests | 2,110+ | ≥ 3,000 |
| Performance Budget Compliance | Partial | 100% of endpoints within budget |
| Technical Debt Items | 1 tracked | 0 critical, < 3 total |

---

## 11. Architectural Principles

These principles are **non-negotiable** for all vNext work. Any deviation requires an ADR approved by the Architecture Review Board.

### Principle 1: No File Shall Exceed 600 Lines
Any source file exceeding 600 lines of production code must be decomposed. This is non-negotiable — it directly impacts testability, maintainability, and parallel development velocity. The three current hotspots (`api.ts`, `main.py`, `knowledge_graph_runtime`) must be refactored as Priority 5.

### Principle 2: Every Endpoint Must Be Authenticated
The webhooks auth gap is unacceptable. There will be zero exceptions to this rule. Every router, every endpoint, every hook — authenticated. Enforcement via automated security audit in CI/CD.

### Principle 3: Every List Endpoint Must Be Paginated
Unbounded result sets are a production incident waiting to happen. All list endpoints must use keyset (cursor) pagination. Offset pagination is permitted only for small, bounded datasets (< 100 rows).

### Principle 4: AI Must Be Testable
Zero backend AI tests is a governance violation. Every AI component (AIService, agents, RAG pipeline, PromptRegistry) must have contract and unit tests. The Engineering Constitution requires it (Article 2.2), and vNext will enforce it.

### Principle 5: No Vendor Lock-In
All infrastructure abstractions must support multiple providers. Currently: OpenAI-only for AI. vNext requires a minimum of 2 supported providers for every abstracted capability (LLMs, embeddings, vector stores).

### Principle 6: Domain Isolation Is Sacred
Cross-domain imports are forbidden. All inter-domain communication must go through defined interfaces, SDKs, or the Decision Platform. Any violation blocks the PR immediately (Constitution Article 3.2).

### Principle 7: Every Change Must Be Measurable
No feature ships without instrumentation. Business impact, performance, adoption, and cost must all be measurable. If you cannot measure it, you cannot ship it (Constitution Article 8.3).

### Principle 8: Multi-Tenancy Is Not Optional
All new features must consider tenant isolation, data partitioning, and quota management from design, not as an afterthought. Tenant-aware testing is mandatory.

### Principle 9: Middleware Must Be Transparent
The middleware chain must not consume, modify, or block the request body. Any middleware that needs to inspect the body must buffer it and restore it. The current body consumption bug violates this principle and blocks all HTTP load testing.

### Principle 10: Technical Debt Must Be Registered Immediately
Any workaround, shortcut, or known suboptimal implementation must be logged in the Technical Debt Register within 24 hours. High-severity debt must be resolved within the same sprint (Constitution Article 2.3).

---

## Appendix A: 48 Improvement Opportunities Summary

| Category | Count | Examples |
|----------|-------|----------|
| Critical | 6 | Webhooks auth, N+1 loops, middleware bug, 12+ pagination, zero AI tests, GraphQL auth |
| Quick Wins | 12 | Token mismatches, WCAG fixes, chart colors, Redis consolidation, RAG tests |
| High Impact | 9 | Agent runtime, LLM abstraction, file decomposition, multi-tenancy quotas |
| Medium | 21 | Admin UIs, advanced workflows, employee intelligence, enrichment fallbacks |
| Low | 12 | Minor UI polish, documentation refinements, non-critical performance tuning |
| Long-Term | 7 | Kafka event bus, Redis cluster, K8s multi-region, SSO/SAML |

---

## Appendix B: Domain Completion Roadmap

| Phase | Domains | Target Completion |
|-------|---------|-------------------|
| **Phase 1** (Sprint 1-2) | Security gaps, middleware, N+1, pagination, AI tests, Quick Wins | Fix critical blockers |
| **Phase 2** (Sprint 3-4) | File decomposition, Agent Runtime, LLM abstraction, Design System | All domains ≥ 85% |
| **Phase 3** (Sprint 5-6) | Data Fabric, Multi-tenancy, Arabic/RTL, Notifications, Enrichment | All domains ≥ 90% |
| **Phase 4** (Sprint 7-8) | Employee Intelligence, Revenue Intelligence, Customer Success, Settings | All domains ≥ 95% |
| **Phase 5** (Sprint 9-10) | Final polish, performance optimization, documentation, vNext launch | Overall 9.0+/10 |

---

*This master plan is a living document. It will be reviewed and updated at each Architecture Review Board meeting. All ADRs related to vNext must reference the relevant sections of this plan.*
