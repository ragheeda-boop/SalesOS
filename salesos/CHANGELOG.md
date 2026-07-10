# Changelog

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
