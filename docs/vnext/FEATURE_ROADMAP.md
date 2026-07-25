# SalesOS vNext Feature Roadmap

> Product Director — Strategic Feature Plan for vNext
> Derived from audit data: Overall completion ~79% (~320 sub-features: ~160 complete, ~100 partial, ~55 missing)

---

## Priority Matrix

Features ranked by Impact vs Effort. Quick Wins first, then Strategic Bets, then Fill-Ins, then Future.

| Rank | Feature | Group | Completion | Priority | Effort | Impact Rationale |
|------|---------|-------|-----------|----------|--------|-----------------|
| 1 | Security | Foundation | 95% | P0 | S | Polished, highest confidence, market differentiator for enterprise sales |
| 2 | Search | Core CRM | 92% | P0 | S | Already strong — minor polish for vNext lock-in |
| 3 | Backend Platform | Foundation | 92% | P0 | S | Core stability; any gap blocks everything |
| 4 | Dashboard — Marketplace | Marketplace | 95% | P0 | M | Highest-visibility feature; widget marketplace is only gap |
| 5 | Settings | Administration | 65% | P0 | L | No consolidated UI today — blocks self-service, blocks tenant onboarding |
| 6 | AI — Agent Runtime | AI | 85% | P0 | XL | Placeholder runtime + zero tests — highest risk for AI narrative |
| 7 | Infrastructure | Foundation | 78% | P0 | L | Terraform state, Redis deploy, Helm charts — blocks production scale |
| 8 | Data Fabric | Knowledge | 65% | P0 | XL | No unified ingestion — foundational gap for all data features |
| 9 | Multi-tenancy | Foundation | 72% | P1 | L | Self-service provisioning — required for scale |
| 10 | Arabic/RTL | Foundation | 72% | P1 | L | i18n framework needed for KSA market commitment |
| 11 | CRM | Core CRM | 75% | P1 | XL | Email, proposals, quotes UIs — core sales workflow |
| 12 | Enrichment | Core CRM | 70% | P1 | L | Unified framework needed — currently fragmented |
| 13 | Notifications | Foundation | 70% | P1 | M | Real-time push + email templates — user retention |
| 14 | Entity Resolution | Core CRM | 85% | P1 | M | Auto-scheduling + HITL UI — operational polish |
| 15 | Administration | Administration | 75% | P1 | M | RBAC admin UI — ops efficiency |
| 16 | Customer Success | Revenue Intelligence | 72% | P1 | L | Churn prediction — direct revenue impact |
| 17 | Feature Store | Knowledge | 82% | P2 | M | Real-time computation + drift monitoring |
| 18 | Monitoring | Analytics | 90% | P2 | S | Already strong; incremental dashboard enhancements |
| 19 | Automation | Automation | 85% | P2 | M | Visual workflow builder polish |
| 20 | Decision Intelligence | Revenue Intelligence | 85% | P2 | M | Mostly complete; incremental improvements |
| 21 | Revenue | Revenue Intelligence | 75% | P2 | XL | ML forecast + quota management — complex |
| 22 | Company Intelligence | Company Intelligence | 90% | P2 | S | Bulk ops + comparison views — quick win |
| 23 | Knowledge Graph | Knowledge | 80% | P2 | M | Interactive explorer + path analysis |
| 24 | Signals | Company Intelligence | 75% | P2 | L | Detection pipeline + real-time processing |
| 25 | Employee Intelligence | Employee Intelligence | 70% | P3 | XL | Career pathing + retention prediction — deep |
| 26 | Company 360 | Company Intelligence | 80% | P3 | M | Hierarchy + financial health + news |
| 27 | Employee 360 | Employee Intelligence | 75% | P3 | M | Profile + skills + enrichment |
| 28 | Frontend Platform | Foundation | 90% | P3 | S | Minor polish |
| 29 | Testing | Foundation | 90% | P3 | M | Load testing in CI |
| 30 | Documentation | Foundation | 92% | P3 | S | Minor gaps |

**Priority Key:**
- **P0** — Blocking vNext ship; must complete before GA
- **P1** — High-value; should ship in vNext or immediately after
- **P2** — Important; planned for vNext.x
- **P3** — Nice-to-have; next major cycle
- **P4** — Future; no current timeline

---

## Foundation

### Backend Platform

| Field | Detail |
|-------|--------|
| **Current Status** | 92% complete. Mostly stable across all domain services. Repository pattern implemented. PostgreSQL + Neo4j operational. |
| **Priority** | P0 |
| **Dependencies** | None |
| **Estimated Complexity** | S |
| **Required Design Work** | — |
| **Required Backend Work** | Hardened error handling across all endpoints; standardized API response envelopes; rate-limit retry headers verified on all routes |
| **Required Frontend Work** | — |
| **Required AI Work** | — |
| **Testing Requirements** | Integration tests for remaining untested service boundaries; error-path coverage to 90%+ |
| **Definition of Done** | All backend services pass integration tests at 90%+ coverage; error handling standardized; retry semantics documented |

---

### Frontend Platform

| Field | Detail |
|-------|--------|
| **Current Status** | 90% complete. Widget SDK frozen v1.0. Design system and UI kit operational. |
| **Priority** | P3 |
| **Dependencies** | None |
| **Estimated Complexity** | S |
| **Required Design Work** | Component usage documentation for design-to-dev handoff |
| **Required Backend Work** | — |
| **Required Frontend Work** | Component API consistency audit; deprecate unused variants; frozen API surface for vNext |
| **Required AI Work** | — |
| **Testing Requirements** | Visual regression tests for all 22 foundation components |
| **Definition of Done** | All UI components have frozen APIs; visual regression suite passes; unused variants removed |

---

### Infrastructure

| Field | Detail |
|-------|--------|
| **Current Status** | 78% complete. Docker Compose operational. GitHub Actions CI/CD in place. Terraform state management, Redis deployment, and Helm charts pending. |
| **Priority** | P0 |
| **Dependencies** | Security audit completion; Backend Platform stability |
| **Estimated Complexity** | L |
| **Required Design Work** | Infrastructure architecture diagram for production topology; DR/HA plan |
| **Required Backend Work** | Health-check endpoints on all services; graceful shutdown hooks |
| **Required Frontend Work** | — |
| **Required AI Work** | — |
| **Testing Requirements** | Infrastructure smoke tests (deploy → verify → rollback); terraform plan validation in CI |
| **Definition of Done** | Terraform state in remote backend; Redis deployed via Helm; production-grade Helm charts for all services; rollback-tested in staging |

---

### Security

| Field | Detail |
|-------|--------|
| **Current Status** | 95% complete. External pentest passed 10/10. RBAC, CSRF, rate limiting operational. All routers authenticated. Dependency audit clean. |
| **Priority** | P0 |
| **Dependencies** | None |
| **Estimated Complexity** | S |
| **Required Design Work** | Security self-service UI for tenant admin (API key rotation UI, audit log viewer) |
| **Required Backend Work** | API key rotation endpoint; audit log export API; session management improvements |
| **Required Frontend Work** | Security settings page in Admin panel (API keys, audit log viewer) |
| **Required AI Work** | — |
| **Testing Requirements** | Quarterly pentest schedule documented; automated security scan in CI (Trivy, Bandit, Semgrep) |
| **Definition of Done** | All 10/10 pentest findings verified closed; automated security pipeline runs every PR; security self-service UI shipped |

---

### Multi-tenancy

| Field | Detail |
|-------|--------|
| **Current Status** | 72% complete. Tenant isolation operational. Self-service provisioning UI missing. |
| **Priority** | P1 |
| **Dependencies** | Infrastructure — Redis (for tenant cache); Settings (for tenant config UI) |
| **Estimated Complexity** | L |
| **Required Design Work** | Tenant onboarding flow (signup → verification → provisioning → welcome); tenant switching UX |
| **Required Backend Work** | Self-service tenant provisioning API; tenant data isolation verification suite; tenant-scoped rate limiting; tenant usage metering |
| **Required Frontend Work** | Tenant onboarding wizard; tenant switcher in nav bar; tenant admin dashboard (users, billing, usage) |
| **Required AI Work** | — |
| **Testing Requirements** | Multi-tenant isolation tests (cross-tenant data leakage); tenant provisioning E2E |
| **Definition of Done** | Tenant can self-register, provision, and manage users without human ops; 100% isolation verified by automated tests |

---

### Arabic/RTL

| Field | Detail |
|-------|--------|
| **Current Status** | 72% complete. Design system supports RTL. No centralized i18n framework. Arabic data normalization has known gaps. |
| **Priority** | P1 |
| **Dependencies** | Frontend Platform (for i18n integration points) |
| **Estimated Complexity** | L |
| **Required Design Work** | i18n framework architecture (ICU message format, locale resolution, RTL layout strategy); Arabic typography guidelines |
| **Required Backend Work** | Arabic text normalization service; locale-aware sorting and searching; date/number formatting locale support |
| **Required Frontend Work** | i18n library integration (react-i18next or equivalent); locale switcher; RTL layout verification for all components; Arabic font loading optimization |
| **Required AI Work** | Arabic NLP pipeline improvements; Arabic entity extraction validation |
| **Testing Requirements** | i18n test suite (all strings render in Ar/En); RTL visual regression tests; Arabic search accuracy tests |
| **Definition of Done** | 100% of UI strings internationalized; Arabic full RTL verified across all screens; Arabic search/filter parity with English |

---

### Notifications

| Field | Detail |
|-------|--------|
| **Current Status** | 70% complete. Basic notification infrastructure exists. Real-time push and email templates missing. |
| **Priority** | P1 |
| **Dependencies** | Backend Platform; Infrastructure (Redis/pub-sub for real-time) |
| **Estimated Complexity** | M |
| **Required Design Work** | Notification preference UX design; email template system architecture; push notification architecture (WebSocket/SSE) |
| **Required Backend Work** | Notification service (queuing, delivery, read tracking); email template engine (MJML or similar); push notification gateway; notification preference API |
| **Required Frontend Work** | Notification center UI (inbox, preferences, history); toast notification system; email template preview in admin |
| **Required AI Work** | — |
| **Testing Requirements** | Notification delivery tests (push, email, in-app); preference enforcement tests; template rendering tests |
| **Definition of Done** | Users receive real-time in-app notifications; email notifications delivered per preference; template management in admin UI |

---

### Testing

| Field | Detail |
|-------|--------|
| **Current Status** | 90% complete. 2110+ tests, 93% unit coverage, 70% integration, 269 E2E tests. Load testing not in CI. |
| **Priority** | P3 |
| **Dependencies** | Infrastructure (CI runner capacity) |
| **Estimated Complexity** | M |
| **Required Design Work** | Load test scenario catalog (critical paths, concurrency levels, data volumes) |
| **Required Backend Work** | Performance instrumentation for load test CI integration |
| **Required Frontend Work** | Lighthouse CI performance budget enforcement |
| **Required AI Work** | AI evaluation test suite (prompt output validation, hallucination detection) |
| **Testing Requirements** | Load tests in CI with thresholds; performance regression gates; AI evaluation automated suite |
| **Definition of Done** | Load testing runs in CI with pass/fail gates; 90th-percentile latency budgets enforced; AI evaluation suite automated |

---

### Documentation

| Field | Detail |
|-------|--------|
| **Current Status** | 92% complete. User guide, admin guide, deployment guide, runbook, SLA, API portal, CHANGELOG published. Runbook content gaps noted. |
| **Priority** | P3 |
| **Dependencies** | All feature completion (docs are last-mile) |
| **Estimated Complexity** | S |
| **Required Design Work** | — |
| **Required Backend Work** | — |
| **Required Frontend Work** | — |
| **Required AI Work** | — |
| **Testing Requirements** | — |
| **Definition of Done** | Runbook gaps filled; API portal examples verified executable; CHANGELOG up to date for release |

---

## Core CRM

### CRM

| Field | Detail |
|-------|--------|
| **Current Status** | 75% complete. Email integration, proposals, and quotes UIs missing. Backend API-backed. DecisionProvider integrated. |
| **Priority** | P1 |
| **Dependencies** | Notifications (email delivery); Enrichment (contact data for proposals) |
| **Estimated Complexity** | XL |
| **Required Design Work** | Email composer UX (templates, attachments, threading); proposal builder (drag-drop sections, approval workflows); quote-to-order flow |
| **Required Backend Work** | Email service (IMAP/SMTP integration, threading, templates); proposal engine (versioning, approval state machine); quote engine (pricing, discounts, approval) |
| **Required Frontend Work** | Email client UI (inbox, compose, threading); proposal editor (rich text, drag-drop, approval UI); quote builder UI (line items, discounts, PDF preview) |
| **Required AI Work** | Email smart compose suggestions; proposal auto-generation from opportunity data; quote optimization recommendations |
| **Testing Requirements** | Email send/receive E2E; proposal lifecycle tests; quote calculation accuracy tests; PDF generation tests |
| **Definition of Done** | User can send/receive emails within SalesOS; create, approve, and share proposals; generate and send quotes from opportunities |

---

### Search

| Field | Detail |
|-------|--------|
| **Current Status** | 92% complete. Hybrid Search (full-text + semantic) with RRF fusion operational. PostgreSQL repositories implemented. |
| **Priority** | P0 |
| **Dependencies** | None |
| **Estimated Complexity** | S |
| **Required Design Work** | Search UX enhancement (facets, filter persistence, recent searches) |
| **Required Backend Work** | Search analytics tracking (query logging, zero-result tracking); saved search API; search suggestion endpoint |
| **Required Frontend Work** | Search UI faceted filters; saved search management; recent search display; keyboard shortcut for search |
| **Required AI Work** | Search result relevance tuning; query rephrasing for failed searches |
| **Testing Requirements** | Search accuracy benchmarks; hybrid search ranking tests; Arabic search parity tests |
| **Definition of Done** | Faceted search live; saved searches functional; search analytics dashboard shows query success rate |

---

### Entity Resolution

| Field | Detail |
|-------|--------|
| **Current Status** | 85% complete. pg_trgm matching + merge pipeline implemented. Auto-scheduling and HITL UI partial. |
| **Priority** | P1 |
| **Dependencies** | Notifications (for HITL task assignment); Search (for resolution lookup) |
| **Estimated Complexity** | M |
| **Required Design Work** | HITL resolution workflow UX (review → approve/reject/merge); resolution confidence visualization |
| **Required Backend Work** | Auto-scheduling engine for periodic resolution runs; HITL task queue API; merge audit trail; resolution undo API |
| **Required Frontend Work** | Resolution review queue UI; merge approval workflow; resolution history viewer; confidence score visualization |
| **Required AI Work** | Confidence scoring improvement; fuzzy-match parameter auto-tuning |
| **Testing Requirements** | Resolution accuracy benchmarks; HITL workflow E2E; auto-schedule reliability tests; undo/rollback tests |
| **Definition of Done** | Auto-scheduling runs daily without false positives; HITL queue processes resolutions with < 4h turnaround; undo/audit trail complete |

---

### Enrichment

| Field | Detail |
|-------|--------|
| **Current Status** | 70% complete. Enrichment exists but lacks a unified framework. Async processing available. |
| **Priority** | P1 |
| **Dependencies** | Data Fabric (unified ingestion); Feature Store (for storing enrichment output) |
| **Estimated Complexity** | L |
| **Required Design Work** | Unified enrichment pipeline architecture (source abstraction, dedup, confidence scoring); enrichment provider plugin model design |
| **Required Backend Work** | Enrichment provider abstraction layer; enrichment pipeline orchestrator; source prioritization engine; enrichment dedup logic; enrichment confidence scoring |
| **Required Frontend Work** | Enrichment configuration UI (provider selection, field mapping); enrichment status dashboard; enrichment results viewer |
| **Required AI Work** | Cross-source data fusion; enrichment gap prediction (which fields need human input) |
| **Testing Requirements** | Provider plugin integration tests; enrichment accuracy benchmarks; pipeline performance tests at scale |
| **Definition of Done** | Unified enrichment framework ships with 2+ providers; pipeline handles dedup + confidence; UI shows enrichment provenance |

---

## Company Intelligence

### Companies

| Field | Detail |
|-------|--------|
| **Current Status** | 90% complete. Core CRUD, search, and list views operational. Bulk operations and comparison views missing. |
| **Priority** | P2 |
| **Dependencies** | None |
| **Estimated Complexity** | S |
| **Required Design Work** | Bulk operation UX (select → action → confirm); company comparison view layout |
| **Required Backend Work** | Bulk company operations API (delete, merge, tag, export); company comparison data endpoint |
| **Required Frontend Work** | Bulk selection UI (select-all, multi-page); company comparison view (side-by-side, diff highlighting); bulk action confirmation dialog |
| **Required AI Work** | — |
| **Testing Requirements** | Bulk operation correctness tests; comparison view rendering tests |
| **Definition of Done** | Bulk operations functional for 500+ companies; comparison view shows side-by-side field diff |

---

### Company 360

| Field | Detail |
|-------|--------|
| **Current Status** | 80% complete. Hierarchy, financial health, and news aggregation are partial. |
| **Priority** | P3 |
| **Dependencies** | Enrichment (for financial data); Knowledge Graph (for hierarchy); Signals (for news aggregation) |
| **Estimated Complexity** | M |
| **Required Design Work** | Company 360 unified view layout (tabs: overview, hierarchy, financial, news); hierarchy visualization design |
| **Required Backend Work** | Company hierarchy service (parent/subsidiary tree); financial health scoring engine; news aggregation pipeline (RSS/crawler + summarization) |
| **Required Frontend Work** | Company 360 tabbed view; interactive hierarchy tree (expand/collapse/search); financial health dashboard (charts, trends); news feed with AI summaries |
| **Required AI Work** | Financial health scoring model; news article summarization; entity extraction for news → company linking |
| **Testing Requirements** | Hierarchy accuracy tests; financial score consistency tests; news relevance tests |
| **Definition of Done** | Company 360 view shows complete org hierarchy; financial health score with trend; relevant news aggregated and summarized |

---

### Signals

| Field | Detail |
|-------|--------|
| **Current Status** | 75% complete. Detection pipeline partial. Real-time processing missing. |
| **Priority** | P2 |
| **Dependencies** | Data Fabric (for signal sources); Notifications (for signal alerts) |
| **Estimated Complexity** | L |
| **Required Design Work** | Signal detection rule engine UX; signal priority/severity classification system; real-time signal dashboard |
| **Required Backend Work** | Signal detection pipeline (source ingestion → classification → scoring → alert); rule engine for custom signals; real-time event processor (Kafka/Redis streams); signal history and analytics |
| **Required Frontend Work** | Signal feed UI (real-time updates, filters, search); signal detail view (evidence, timeline, related entities); signal rule configuration UI |
| **Required AI Work** | Signal classification model (priority, severity, category); anomaly detection for unexpected signals; false-positive reduction |
| **Testing Requirements** | Signal detection accuracy benchmarks; real-time delivery latency tests (< 5s); rule engine correctness tests |
| **Definition of Done** | Signals pipeline processes 100+ sources in real-time; user configures custom signal rules; signal feed updates within 5s of detection |

---

## Employee Intelligence

### Employee 360

| Field | Detail |
|-------|--------|
| **Current Status** | 75% complete. Profile, skills, and enrichment are partial. |
| **Priority** | P3 |
| **Dependencies** | Enrichment (for skill data); Knowledge Graph (for skill relationships) |
| **Estimated Complexity** | M |
| **Required Design Work** | Employee 360 unified profile view (skills, experience, performance, signals); skill visualization design |
| **Required Backend Work** | Employee profile enrichment pipeline; skill extraction and normalization service; experience timeline service; performance data integration |
| **Required Frontend Work** | Employee 360 profile view; skill map visualization (radar chart, skill clusters); experience timeline; performance trend charts |
| **Required AI Work** | Skill extraction from unstructured data (resumes, performance reviews); skill gap analysis; role-skill fit scoring |
| **Testing Requirements** | Skill extraction accuracy tests; profile enrichment E2E; performance data integration tests |
| **Definition of Done** | Employee 360 shows enriched profile with skill map, experience timeline, and performance trends; skill gap analysis available |

---

### Employee Intelligence

| Field | Detail |
|-------|--------|
| **Current Status** | 70% complete. Career pathing and retention prediction are missing. |
| **Priority** | P3 |
| **Dependencies** | Employee 360; Knowledge Graph (for career path modeling); AI (for prediction models) |
| **Estimated Complexity** | XL |
| **Required Design Work** | Career pathing UX (path visualization, what-if analysis); retention risk dashboard design |
| **Required Backend Work** | Career path modeling engine (role transitions, skills alignment, timeline estimation); retention prediction service (risk scoring, driver analysis); flight-risk flagging and alerting |
| **Required Frontend Work** | Career path explorer (interactive path map, alternative paths, timeline); retention risk dashboard (risk heatmap, driver breakdown, at-risk list) |
| **Required AI Work** | Career path recommendation model; retention prediction model (XGBoost/LightGBM); driver importance analysis (SHAP) |
| **Testing Requirements** | Career path accuracy tests (historical validation); retention prediction precision/recall benchmarks; model drift monitoring |
| **Definition of Done** | Career pathing suggests realistic career progressions; retention prediction flags at-risk employees with >80% precision; drivers of risk are explainable |

---

## Revenue Intelligence

### Revenue

| Field | Detail |
|-------|--------|
| **Current Status** | 75% complete. ML forecast and quota management missing. |
| **Priority** | P2 |
| **Dependencies** | AI (for ML forecast models); CRM (for pipeline data); Decision Intelligence (for scoring inputs) |
| **Estimated Complexity** | XL |
| **Required Design Work** | Revenue forecasting dashboard (ML + manual override); quota management UX (targets, tracking, attainment); what-if scenario planner |
| **Required Backend Work** | ML forecast engine (ensemble: time-series + regression); quota management service (targets, assignments, attainment tracking); scenario simulation engine; revenue attribution service |
| **Required Frontend Work** | Revenue forecast dashboard (chart, table, filters); quota management UI (targets by rep/team/region, attainment %, progress bars); what-if scenario builder |
| **Required AI Work** | Forecast model training pipeline; model selection and ensemble logic; confidence interval estimation; anomaly detection in forecast |
| **Testing Requirements** | Forecast accuracy back-testing (holdout validation); quota calculation correctness tests; scenario simulation accuracy tests |
| **Definition of Done** | Revenue forecast within 10% accuracy at 90d horizon; quota management operational for all sales orgs; what-if scenarios update in real-time |

---

### Decision Intelligence

| Field | Detail |
|-------|--------|
| **Current Status** | 85% complete. ScoringEngine and DecisionProvider integrated across domains. Mostly complete. |
| **Priority** | P2 |
| **Dependencies** | Feature Store (for feature computation) |
| **Estimated Complexity** | M |
| **Required Design Work** | Decision explainability UX (why did this score change?); decision audit trail viewer |
| **Required Backend Work** | Decision explainability service (feature importance per decision); decision audit trail (who/what/when/why); batch scoring API; decision simulation endpoint |
| **Required Frontend Work** | Decision explainability widget (feature contribution breakdown, what-if sliders); decision audit log viewer (filterable, searchable) |
| **Required AI Work** | SHAP/LIME integration for explainability; feature importance tracking; model comparison dashboard |
| **Testing Requirements** | Explainability accuracy tests; batch scoring correctness tests; audit trail completeness tests |
| **Definition of Done** | Every decision shows feature importance breakdown; audit trail captures all decision context; batch scoring handles 10k+ records/min |

---

### Customer Success

| Field | Detail |
|-------|--------|
| **Current Status** | 72% complete. Churn prediction missing. |
| **Priority** | P1 |
| **Dependencies** | Signals (for usage signals); AI (for churn model); Notifications (for churn alerts) |
| **Estimated Complexity** | L |
| **Required Design Work** | Customer health dashboard (health score, trends, risk flags); churn prediction UX (risk list, driver breakdown, intervention recommendations) |
| **Required Backend Work** | Customer health score engine (usage, support, satisfaction, financial); churn prediction service (risk score, timing estimate, driver analysis); intervention tracking service (action → outcome) |
| **Required Frontend Work** | Customer health dashboard (score trends, segment breakdown, risk list); churn prediction view (risk details, drivers, recommended interventions); intervention tracking UI |
| **Required AI Work** | Churn prediction model (usage patterns + sentiment + support); intervention effectiveness model; next-best-action recommendation |
| **Testing Requirements** | Churn prediction precision/recall back-testing; health score consistency tests; recommendation relevance tests |
| **Definition of Done** | Churn prediction flags accounts 30+ days in advance with >80% precision; health score reflects multi-signal reality; intervention recommendations available |

---

## AI

### AI

| Field | Detail |
|-------|--------|
| **Current Status** | 85% complete for components, but agent runtime is a placeholder and zero AI tests exist. Prompt registry and evaluation exist. |
| **Priority** | P0 |
| **Dependencies** | Backend Platform (for service integration); Feature Store (for AI feature access); Knowledge Graph (for context) |
| **Estimated Complexity** | XL |
| **Required Design Work** | Agent runtime architecture (execution engine, sandboxing, memory, tools); AI orchestration UX (agent configuration, monitoring); prompt management UI; evaluation dashboard |
| **Required Backend Work** | Agent runtime engine (context builder, tool execution, memory management, output validation); agent registry and lifecycle management; prompt versioning and A/B testing service; evaluation framework (offline metrics, online monitoring, regression detection); guardrails service (content filtering, PII redaction, bias detection) |
| **Required Frontend Work** | Agent configuration UI (prompts, tools, memory settings); agent monitoring dashboard (execution logs, token usage, latency); prompt editor (versioning, diff, A/B test setup); evaluation results dashboard (accuracy, relevance, safety) |
| **Required AI Work** | Evaluation test suite (accuracy, hallucination, safety, relevance benchmarks); agent tool-use optimization; prompt optimization (few-shot selection, chain-of-thought tuning); guardrail model integration |
| **Testing Requirements** | Agent execution end-to-end tests; evaluation suite with automated pass/fail; hallucination detection benchmarks; prompt regression tests across all configured prompts |
| **Definition of Done** | Agent runtime executes configurable agents with tools and memory; evaluation suite runs automatically on every prompt change; guardrails filter PII, toxic content, and hallucinations; zero regressions in evaluation suite |

---

## Automation

### Automation

| Field | Detail |
|-------|--------|
| **Current Status** | 85% complete. Visual workflow builder is partial. Execution engine operational. |
| **Priority** | P2 |
| **Dependencies** | Notifications (for workflow alerts); Backend Platform (for webhook/API triggers) |
| **Estimated Complexity** | M |
| **Required Design Work** | Visual workflow builder UX (drag-drop nodes, connectors, property panels); workflow template library design; workflow execution visualization |
| **Required Backend Work** | Workflow node SDK (extensible node types); workflow debugger (step-through, variable inspection); workflow analytics (execution time, failure rate, bottleneck detection) |
| **Required Frontend Work** | Visual workflow builder (drag-drop interface, node configuration, branching); workflow template library; workflow execution viewer (live status, logs, visualization) |
| **Required AI Work** | Workflow template recommendation; workflow optimization suggestions (parallelization, retry logic) |
| **Testing Requirements** | Workflow execution correctness tests; visual builder usability tests; workflow template tests |
| **Definition of Done** | Visual workflow builder ships with 10+ node types; workflow templates available for common patterns; execution viewer shows live status with detailed logs |

---

## Knowledge

### Knowledge Graph

| Field | Detail |
|-------|--------|
| **Current Status** | 80% complete. Graph database operational with Neo4j. Interactive explorer and path analysis missing. |
| **Priority** | P2 |
| **Dependencies** | None |
| **Estimated Complexity** | M |
| **Required Design Work** | Interactive graph explorer UX (zoom, pan, search, filter, expand); path analysis visualization (shortest path, influence paths) |
| **Required Backend Work** | Graph explorer API (neighborhood queries, filtered subgraph); path analysis service (shortest path, weighted path, influence path); graph statistics service (centrality, density, clusters) |
| **Required Frontend Work** | Interactive graph canvas (D3.js/vis.js/Cytoscape); node/edge detail panel; path analysis view (paths list, visualization, comparison); graph statistics dashboard |
| **Required AI Work** | Entity resolution ↔ KG linking; influence scoring on graph edges; community detection for entity clusters |
| **Testing Requirements** | Graph query performance tests (sub-100ms for neighborhood queries); path analysis correctness tests; visualization rendering tests |
| **Definition of Done** | Interactive graph explorer loads sub-graphs in <100ms; path analysis shows shortest and influence paths; statistics dashboard shows key graph metrics |

---

### Feature Store

| Field | Detail |
|-------|--------|
| **Current Status** | 82% complete. Feature store implemented. Real-time computation and drift monitoring missing. |
| **Priority** | P2 |
| **Dependencies** | AI (for model features); Data Fabric (for real-time data sources) |
| **Estimated Complexity** | M |
| **Required Design Work** | Feature drift monitoring dashboard; feature registry UX (discovery, documentation, lineage) |
| **Required Backend Work** | Real-time feature computation engine (streaming); feature drift detection service (statistical drift, distribution comparison); feature lineage tracking; feature validation service (null checks, range checks, type checks) |
| **Required Frontend Work** | Feature registry UI (browse, search, documentation); feature drift monitoring dashboard (drift metrics, alert history); feature validation results viewer |
| **Required AI Work** | Drift detection model (adaptive thresholds); feature importance tracking for model decay correlation |
| **Testing Requirements** | Real-time computation latency tests; drift detection accuracy tests; feature validation correctness tests |
| **Definition of Done** | Real-time feature computation delivers features within 100ms; drift dashboard shows meaningful alerts for distribution changes; feature registry documents all features with lineage |

---

### Data Fabric

| Field | Detail |
|-------|--------|
| **Current Status** | 65% complete. No unified ingestion pipeline. Scrapers not productionized. |
| **Priority** | P0 |
| **Dependencies** | Infrastructure (for ingestion worker pool); Backend Platform (for event system) |
| **Estimated Complexity** | XL |
| **Required Design Work** | Unified ingestion architecture (source connectors, transformation pipeline, schema mapping, dedup); scraper productionization plan; data quality framework |
| **Required Backend Work** | Ingestion pipeline orchestrator (source → transform → load → validate); connector SDK for new sources; scraper service (scheduling, proxy rotation, parsing, error handling); transformation pipeline (mapping, enrichment, normalization); data quality service (validation rules, quality scoring, alerting) |
| **Required Frontend Work** | Ingestion pipeline configuration UI (source setup, schedule, mapping); data quality dashboard (scores, trends, issue list); pipeline monitoring UI (status, throughput, error rate) |
| **Required AI Work** | Schema mapping recommendation; data quality anomaly detection; parsing improvement for unstructured sources |
| **Testing Requirements** | Connector integration tests; pipeline throughput benchmarks; data quality rule tests; scraper reliability tests (retry, rate-limit, rotate) |
| **Definition of Done** | Unified ingestion pipeline handles 5+ source types; scrapers run reliably with automatic retry and proxy rotation; data quality dashboard shows real-time health per source |

---

## Marketplace

### Dashboard — Widget Marketplace

| Field | Detail |
|-------|--------|
| **Current Status** | 95% complete. Widget SDK v1.0 frozen. Dashboard is operational with all core widgets. Widget marketplace is the only gap. |
| **Priority** | P0 |
| **Dependencies** | Frontend Platform; Widget SDK v1.0 (frozen) |
| **Estimated Complexity** | M |
| **Required Design Work** | Widget marketplace UX (browse, search, install, configure); widget listing submission workflow; widget rating/review system |
| **Required Backend Work** | Widget registry API (listing, versioning, dependency resolution); widget installation service (tenant-scoped); widget analytics (install count, usage, performance) |
| **Required Frontend Work** | Widget marketplace UI (gallery, search, filters, detail view); widget installation dialog (configure, confirm); widget management UI (installed list, updates, removal) |
| **Required AI Work** | Widget recommendation based on role/usage; widget performance anomaly detection |
| **Testing Requirements** | Marketplace E2E (browse → install → configure → use); widget installation isolation tests; widget update/rollback tests |
| **Definition of Done** | Widget marketplace ships with 5+ curated widgets; users can browse, install, configure, and remove widgets; widget usage analytics tracked |

---

## Administration

### Admin

| Field | Detail |
|-------|--------|
| **Current Status** | 75% complete. RBAC admin UI is partial. User and tenant management exist. |
| **Priority** | P1 |
| **Dependencies** | Multi-tenancy (for tenant admin scoping); Settings (for system config integration) |
| **Estimated Complexity** | M |
| **Required Design Work** | RBAC admin UI (role editor, permission matrix, user-role assignment); audit log viewer UX |
| **Required Backend Work** | RBAC management API (roles, permissions, assignments); audit logging service (event capture, retention, export); admin dashboard API (system health, usage stats) |
| **Required Frontend Work** | RBAC editor UI (role creation, permission matrix with toggle grid, user-role assignment); audit log viewer (filterable, searchable, exportable); admin dashboard (system stats, active sessions, error rates) |
| **Required AI Work** | — |
| **Testing Requirements** | RBAC enforcement tests (all permission combinations); audit log completeness tests; admin dashboard accuracy tests |
| **Definition of Done** | Admin UI allows full RBAC management without raw API calls; audit log captures all admin actions; admin dashboard shows live system health |

---

### Settings

| Field | Detail |
|-------|--------|
| **Current Status** | 65% complete. No consolidated Settings UI. Tenant module is a scaffold. |
| **Priority** | P0 |
| **Dependencies** | Admin (for RBAC integration in settings); Multi-tenancy (for tenant-specific settings) |
| **Estimated Complexity** | L |
| **Required Design Work** | Settings information architecture (categories, search, scoping); settings page layout (global vs tenant vs user scoping); settings schema registry design |
| **Required Backend Work** | Settings service (typed settings, validation, inheritance); settings schema definition API; settings audit trail; settings import/export API |
| **Required Frontend Work** | Settings framework UI (category nav, search, inline edit, validation); settings pages for all domains (general, security, notifications, integrations, billing); settings search with results grouped by category |
| **Required AI Work** | — |
| **Testing Requirements** | Settings persistence and inheritance tests; settings validation tests; settings import/export round-trip tests |
| **Definition of Done** | Consolidated Settings UI covers all configurable domains; settings support global/tenant/user scoping with inheritance; settings changes are audited and reversible |

---

## Analytics

### Monitoring

| Field | Detail |
|-------|--------|
| **Current Status** | 90% complete. Prometheus/Grafana configured, alerting deployed. Performance dashboards operational. |
| **Priority** | P2 |
| **Dependencies** | None |
| **Estimated Complexity** | S |
| **Required Design Work** | Business KPI dashboard UX (revenue, users, usage); SLA compliance dashboard |
| **Required Backend Work** | Business KPI aggregation service; SLA compliance calculation service; custom metric API for tenant admins |
| **Required Frontend Work** | Business KPI dashboard (revenue trends, user growth, feature adoption); SLA compliance dashboard (uptime %, response time %, breach timeline) |
| **Required AI Work** | — |
| **Testing Requirements** | KPI accuracy tests; SLA calculation correctness tests; dashboard rendering tests |
| **Definition of Done** | Business KPI dashboard delivers real-time revenue/user/usage metrics; SLA compliance dashboard shows historical and current adherence |

---

## Feature Dependency Graph

```
                    ┌──────────────────────────────┐
                    │      Infrastructure (P0)       │
                    └────────────┬─────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
     ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
     │ Backend Platform │ │     Data     │ │  Multi-tenancy   │
     │      (P0)        │ │ Fabric (P0)  │ │      (P1)        │
     └────────┬────────┘ └──────┬───────┘ └────────┬─────────┘
              │                 │                   │
     ┌────────┴────────┐        │            ┌──────┴──────┐
     │  Notifications  │        │            │  Settings   │
     │      (P1)       │        │            │    (P0)     │
     └────────┬────────┘        │            └──────┬──────┘
              │                 │                   │
     ┌────────┴────────┐        │            ┌──────┴──────┐
     │   CRM (P1)      │        │            │   Admin     │
     │ Enrichment (P1) │        │            │    (P1)     │
     │ Entity Res (P1) │        │            └─────────────┘
     └────────┬────────┘        │
              │                 │
     ┌────────┴─────────────────┴────────┐
     │        AI — Agent Runtime (P0)      │
     │        Revenue (P2)                 │
     │        Customer Success (P1)        │
     └────────────────┬───────────────────┘
                      │
     ┌────────────────┴───────────────────┐
     │        Knowledge Graph (P2)          │
     │        Feature Store (P2)            │
     │        Employee Intelligence (P3)   │
     └────────────────────────────────────┘
```

---

## Delivery Phasing

| Phase | Focus | Features | Timeline |
|-------|-------|----------|----------|
| **Phase 1 — Foundation** | Infrastructure + Core | Infrastructure (P0), Backend Platform (P0), Security (P0), Settings (P0), Data Fabric (P0), Multi-tenancy (P1), Arabic/RTL (P1) | Sprint 1-3 |
| **Phase 2 — Intelligence** | AI + Data | AI — Agent Runtime (P0), Feature Store (P2), Knowledge Graph (P2), Search (P0) | Sprint 3-5 |
| **Phase 3 — Revenue** | CRM + Revenue | CRM (P1), Enrichment (P1), Entity Resolution (P1), Revenue (P2), Decision Intelligence (P2), Customer Success (P1) | Sprint 4-7 |
| **Phase 4 — Platform** | Admin + Marketplace | Administration (P1), Dashboard Marketplace (P0), Notifications (P1) | Sprint 6-8 |
| **Phase 5 — Polish** | Remaining | Company Intelligence (P2), Employee Intelligence (P3), Automation (P2), Monitoring (P2), Testing (P3), Documentation (P3) | Sprint 8-10 |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI Agent runtime delayed by evaluation requirements | High | Critical | Start evaluation suite in parallel with runtime development; ship MVP runtime without full eval gate |
| Data Fabric ingestion scope too broad | Medium | High | Limit Phase 1 to top 3 source connectors; connector SDK enables community contributions |
| Arabic/RTL i18n underestimated | Medium | High | Outsource i18n framework setup; phased rollout (RTL layout first, full i18n second) |
| Settings UI scope creep (too many domains) | High | Medium | Ship settings framework with top 5 domains; remaining domains in follow-up sprints |
| Infrastructure Helm charts delayed by K8s complexity | Medium | High | Use Docker Compose for single-tenant; Helm for multi-tenant only |
| CRM (email, proposals, quotes) is XL effort | Medium | High | Ship email first (P1), proposals second (P2), quotes third (P2+) |
| Employee Intelligence career pathing model accuracy | High | Low | Ship with baseline model; iterate with customer feedback; mark as beta |
| Widget marketplace adoption low | Medium | Medium | Seed with 5+ curated widgets; provide widget dev contest for ecosystem |
| Performance regression from new features | Medium | High | Performance gates in CI from Phase 1; load testing in CI before Phase 3 |
| Dependency chain delays (Feature A blocks Feature B) | High | Medium | Buffer sprints; parallelize independent tracks; phase dependency graph rigorously |

---

*Product Director — SalesOS vNext*
*Last updated: 2026-07-16*
