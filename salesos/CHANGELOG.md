# Changelog

## SalesOS Product v0.6 — Revenue Execution Platform (2026-07-11)

### Release Tag: `v0.6.0`

Wave 2 — Revenue Execution Platform. Transforms SalesOS from intelligence into commercial execution.

### What's Included

**Wave 2 Complete:**
- **NBA Engine** — Decision pipeline with AI reasoning, feedback loop, explainable recommendations
- **Opportunity Workspace** — Full lifecycle management with playbooks, deal health tracking
- **Pipeline Intelligence** — Velocity, conversion rates, health map, forecast engine
- **Meeting Intelligence** — Pre-meeting briefs, post-meeting summaries, sentiment analysis
- **Email Intelligence** — Sentiment analysis, topic extraction, urgency detection
- **Revenue Workspace** — Unified shell combining all Wave 2 components

### Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Opportunity storage | First-class `opportunities` table | Opportunity is a first-class entity with its own lifecycle |
| NBA storage | `opportunity_features` table | Reuses Feature Store caching, versioning, and confidence tracking |
| NBA computation | Event-driven + Scheduled | Stage changes trigger immediate recompute; idle detection on schedule |
| Activity model | Reuse Activity Runtime (`entity_type='opportunity'`) | Zero new infrastructure; all queries work out of box |
| Workspace architecture | `createWorkspaceProvider` per workspace | Consistent with Wave 1 pattern |
| Permissions | Extended `opportunity.*` + `nba:*` resources | No new permission framework needed |
| AI reasoning | Hybrid rule + AI scoring | AI runs when rules < 0.7 or conflict; graceful degradation without AI key |

### NBA Engine

- **Decision Pipeline:** Signal → Normalization → Business Rules → Scoring → AI Reasoning → Risk Assessment → Confidence → Ranking → Recommendation → Feedback → Learning
- **12 pipeline stages** with full trace on every NBA generation
- **10+ business rules:** Stage-based, time-based, signal-triggered, health-based
- **3 scoring models:** OpportunityScorer (7 weighted factors), UrgencyScorer, EffortEstimator
- **6 risk detectors:** Stagnation, competition, engagement drop, stakeholder change, budget concern, timeline slip
- **Explainability:** Every recommendation includes evidence trail, alternatives, confidence breakdown
- **Feedback loop:** Accept/Dismiss/Complete with automatic rule weight adjustment
- **Performance:** < 200ms rule-only, < 3s with AI (timeout + fallback)

### Opportunity Workspace

- Opportunity CRUD (list, create, update, delete, stage management)
- NBA widget embedded in workspace context
- Timeline widget (activities for this opportunity)
- Company Snapshot (from Wave 1 Company Intelligence)
- Deal Health indicators (healthy / at_risk / critical)
- Playbook Engine — CRUD + assignment to opportunities

### Pipeline Intelligence

- Kanban view (drag & drop stage changes)
- List view (sortable, filterable table)
- Pipeline Analytics: Velocity, Win Rate, Conversion Rate per stage
- Health Map: Traffic light visualization for all open opportunities
- Forecast Engine: Best Case, Commit, Pipeline forecasts
- Pipeline export (CSV, PDF)

### Meeting Intelligence

- Pre-Meeting Intelligence: Company Brief, Talking Points
- During/Post-Meeting: Notes, Action Items
- AI Meeting Intelligence: AI brief generation, Action Item extraction
- Meeting data model + CRUD API
- Integration with Activity Runtime

### Email Intelligence

- Sentiment analysis on inbound/outbound emails
- Topic extraction and classification
- Urgency detection and prioritization
- Email data model + CRUD API
- Gmail API connector + Outlook API connector

### Revenue Workspace

- Executive Summary: Target vs Forecast
- Team Performance dashboard
- AI Insights: At-Risk Deals, Coaching Recommendations
- Unified shell combining NBA, Pipeline, Meeting, Email, Revenue Goals

### Added
- `opportunities` table with full lifecycle support
- `opportunity_features` table for NBA scoring
- `playbooks` table for playbook engine
- `meetings` and `meeting_action_items` tables
- `emails` and `email_intelligence` tables
- `revenue_goals` table for target tracking
- Platform Kernel: `contracts/ai/` and `contracts/revenue/` type definitions
- 12 NBA API endpoints (GET/POST /opportunities/*, /nba/*, /pipeline/*)
- Meeting Intelligence API (GET/POST /meetings/*)
- Email Intelligence API (GET/POST /emails/*)
- Revenue Dashboard API (GET /revenue/dashboard)
- NBA Event Subscribers (opportunity events, time triggers)
- Email Integration connectors (Gmail API, Outlook API)
- 9 NBA frontend components (RecommendationCard, EvidencePanel, ConfidenceBadge, ImpactMeter, RiskPanel, AlternativeActions, FeedbackDialog, ActionLauncher, DecisionTimeline)
- Pipeline Workspace components (KanbanBoard, ListView, HealthMap, ForecastPanel)
- Meeting Workspace components (PreMeetingBrief, PostMeetingSummary, ActionItemTracker)
- Email Workspace components (SentimentBadge, TopicTag, UrgencyIndicator)
- Revenue Workspace shell (ExecutiveSummary, TeamPerformance, AIInsights)
- Test infrastructure: NBA engine tests, API tests, component tests

### Production Hardening
- Fixed IDOR vulnerability on opportunity endpoints — tenant ID now validated server-side
- Fixed tenant isolation leak in NBA scoring — queries scoped to authenticated tenant
- Added Pydantic validation on all Wave 2 API inputs (opportunities, meetings, emails, playbooks)
- Per-user rate limiting on all new endpoints (tier-based limits)
- RBAC enforced on all Wave 2 endpoints (`nba:*`, `opportunity:*`, `meeting:*`, `email:*`, `pipeline:*`)
- Parallel query optimization on pipeline analytics (3 queries run concurrently)

### New
- 192 unit tests added (229 total across backend)
- Decision Rule API fix — rules now correctly scoped to tenant on creation and update

### Security
- NBA endpoints require `nba:read` / `nba:update` / `nba:admin` permissions
- Opportunity endpoints require `opportunity:*` permissions
- Meeting endpoints require `meeting:read` / `meeting:create` / `meeting:update` permissions
- Email endpoints require `email:read` / `email:create` permissions
- Pipeline endpoints require `pipeline:read` permission
- All endpoints authenticated (JWT) + rate limited
- Email integration uses OAuth2 with minimal scope
- Calendar integration uses OAuth2 with minimal scope

### Architecture
- 9 architecture documents produced for Wave 2 design and validation
- Platform Kernel design (`contracts/ai/`, `contracts/revenue/`) — shared type definitions
- Cross-document consistency audit completed (`09-ARCHITECTURE_VALIDATION_REPORT.md`)
- Full API reference published (`11-API_REFERENCE.md`)

### Documentation
- `docs/wave-2/01-REVENUE_EXECUTION_REVIEW.md` — Platform capability audit
- `docs/wave-2/02-PLATFORM_KERNEL_DESIGN.md` — Platform Kernel architecture
- `docs/wave-2/03-NBA_ARCHITECTURE.md` — NBA decision pipeline design
- `docs/wave-2/04-NBA_BLUEPRINT.md` — NBA implementation blueprint
- `docs/wave-2/05-NBA_CONTRACTS.md` — TypeScript/Pydantic contracts
- `docs/wave-2/06-NBA_API_MAPPING.md` — REST API endpoint mapping
- `docs/wave-2/07-NBA_COMPONENT_CATALOG.md` — Frontend component catalog
- `docs/wave-2/08-NBA_IMPLEMENTATION_PLAN.md` — Sprint breakdown and risk analysis
- `docs/wave-2/09-ARCHITECTURE_VALIDATION_REPORT.md` — Cross-document consistency audit
- `docs/wave-2/10-WAVE2_RELEASE_NOTES.md` — Detailed release notes
- `docs/wave-2/11-API_REFERENCE.md` — Full API documentation

---

## SalesOS Product v0.5 — Execution Intelligence (2026-07-10)

### Release Tag: `v0.5.0`

First Product Release — closes Project Phase, opens Product Phase.

### What's Included

**Wave 1 Complete:**
- Dashboard Workspace (6 widgets, contract-tested)
- Universal Search (hybrid full-text + semantic + graph)
- Company Intelligence Workspace
- Widget SDK v1.0 (frozen)
- Workspace SDK

### Engineering Platform
- Design Language (`@salesos/design-language`)
- UI Kit (`@salesos/ui`, 16/18 components tested)
- Foundation Components (22 components, all tested)
- Search Runtime
- Data Fabric Pipeline (8 stages, production-ready)
- Feature Store (7 computers)
- Knowledge Graph (Neo4j + SQL fallback)
- Event Runtime
- Decision Engine
- Experimental AI Agents (11 agent types)
- Revenue Brain

### Added
- 15 backend test files (37/37 unit tests passing)
- 18 frontend test files (10 foundation + 10 UI Kit + mission center contract)
- Unit test infrastructure (tests/unit/ separate from integration)
- JSON structured logging with request ID tracking
- RequestLoggingMiddleware (all requests logged with method/path/status/duration)
- K8s health probes (/health/live, /health/ready)
- Neo4j full-text indexes (fuzzy search via `~` operator)
- All 6 dashboard widget mappers with real DB queries
- Executive dashboard service with real health data computation
- 4 Data Fabric pipeline functions (graph sync, embeddings, enrichment, feature recompute)

### Fixed
- BUG-001: Search timeout — ILIKE → GIN-indexed tsvector, 30s timeout guard
- BUG-002: Arabic normalization — alif maqsura, tashkeel, digit normalization
- BUG-003: Neo4j connection leak — 5 leak sites fixed across 4 files
- 8 silent catch {} blocks now log or display errors
- use_mock defaults to False (API no longer silently returns fake data)
- Hardcoded secrets removed from alembic.ini, seed_data.py, prod_audit.py
- Meilisearch API key moved to environment variable
- sync_notion_database task now passes session correctly
- Dashboard layout migrated to foundation AppShell (TD-008)
- Test conftest no longer autouses setup_database for unit tests

### Technical Debt Resolved
- TD-004: Monitoring — JSON logging, request middleware, K8s probes
- TD-005: Hardcoded configs — 6 secrets remediated
- TD-006: UI Kit unit tests — 16/18 components tested
- TD-007: Foundation component tests — all 10 tested
- TD-008: Dashboard layout migration to foundation AppShell

### Remaining
- Integration tests need test DB connection
- E2E test coverage (20% → 60%)
- Redis/Kafka deployment
- Wave 2: Revenue Execution Platform (in planning)

---

## Sprint 1 — Product Foundation (2026-07-10)

### Added
- 22 foundation components: AppShell, Sidebar, Header, Navigation, PageLayout, WorkspaceLayout, CommandBar, Typography, Surface, Stack, Grid, Container, Section, Divider, Icon, Card, Badge, Metric, Skeleton, Loading, EmptyState, ErrorBoundary
- Full ARIA accessibility attributes on all foundation components
- MUHIDE design system tokens

### Changed
- @salesos/ui kit restyled with MUHIDE tokens
- Dashboard layout migrated to MUHIDE color tokens
- 18 page/component files remediated (~340 class-level color violations)
- tailwind.config.ts updated with full MUHIDE theme

### Fixed
- Conflicting `WorkspaceZone` type
- Hardcoded spacing values deduplicated
- All SVG icons have aria-hidden where decorative
