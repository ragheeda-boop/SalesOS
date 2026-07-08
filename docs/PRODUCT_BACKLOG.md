# SalesOS — PRODUCT BACKLOG

> **Product Backlog — Epic → Capability → Feature → Story → Task → ADR → PR → Release**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Structure

```
Epic: Large strategic initiative (6-12 months)
  └── Capability: Product capability with full surface (1-3 months)
       └── Feature: Distinct user-visible functionality (1-4 weeks)
            └── Story: Smallest shippable unit (1-3 days)
                 └── Task: Technical work item (hours-1 day)
                      └── PR: Pull request implementing the task
                           └── Release: Version containing the PR
```

---

## EPIC I: PLATFORM FOUNDATION (2026 Q3-Q4)

### CAP-001: PostgreSQL Persistence (P0)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Identity Repository | [STO-001] PostgresIdentityRepository | 🔴 P0 | — | v0.1 |
| Company Repository | [STO-002] PostgresCompanyRepository | 🔴 P0 | — | v0.1 |
| Alembic Baseline | [STO-003] Create initial migration | 🔴 P0 | — | v0.1 |
| Integration Tests | [STO-004] 50+ integration tests | 🔴 P0 | — | v0.1 |

### CAP-002: Frontend MVP (P0.5)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Design System | [FE-001] Button, Input, Card, Table components | 🔴 P0.5 | — | v0.2 |
| Login/Register | [FE-002] Login page, Register page | 🔴 P0.5 | — | v0.2 |
| Company 360 | [FE-003] Company profile page | 🔴 P0.5 | — | v0.2 |
| Search UI | [FE-004] Search bar + results page | 🟡 P1 | — | v0.3 |

### CAP-003: Data Ingestion (P0.5)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Pipeline Framework | [DI-001] Extract → Validate → Load | 🔴 P0.5 | — | v0.2 |
| Balady Integration | [DI-002] Connect Balady scraper to pipeline | 🔴 P0.5 | — | v0.2 |
| Taqeem Integration | [DI-003] Connect Taqeem scraper to pipeline | 🔴 P0.5 | — | v0.2 |
| NCNP Integration | [DI-004] Connect NCNP scraper to pipeline | 🟡 P1 | — | v0.3 |

---

## EPIC II: INTELLIGENCE (2027 Q1-Q4)

### CAP-004: Revenue Brain (P1)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Architecture Design | [RB-001] Sequence diagrams, data flow | 🟡 P1 | — | v0.4 |
| State Manager | [RB-002] Current state computation | ❌ P1 | — | v0.4 |
| Next Best Action | [RB-003] NBA computation engine | ❌ P2 | — | v0.5 |

### CAP-005: AI Copilot (P2)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Search → Summarize | [AI-001] Natural language search | ❌ P2 | — | v0.5 |
| Company Q&A | [AI-002] Ask about any company | ❌ P2 | — | v0.5 |
| Compare | [AI-003] Compare two companies | ❌ P2 | — | v0.6 |

### CAP-006: Digital Twin (P1)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| State Manager | [DT-001] Event → State projection | ❌ P1 | — | v0.6 |
| Predictor | [DT-002] ML forecast models | ❌ P2 | — | v0.7 |
| Risk Detector | [DT-003] Rule + AI risk evaluation | ❌ P2 | — | v0.7 |
| Scenario Simulator | [DT-004] What-if analysis engine | ❌ P2 | — | v0.8 |

---

## EPIC III: DATA FABRIC (2026 Q4 — 2027 Q1)

### CAP-007: Entity Resolution (P0)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Matching Engine | [ER-001] Blocking + comparison + classification | 🔴 P0 | — | v0.3 |
| Golden Record Store | [ER-002] Merge + provenance | 🔴 P0 | — | v0.3 |
| Balady + NCNP merge | [ER-003] First 2 sources | 🔴 P0 | — | v0.3 |

### CAP-008: Feature Store (P1)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| Schema Definition | [FS-001] Feature registry tables | 🟡 P1 | — | v0.4 |
| First 10 Features | [FS-002] Growth rate, hiring velocity, etc. | 🟡 P1 | — | v0.4 |
| Feature Computation | [FS-003] Scheduled + event-driven computation | 🟡 P1 | — | v0.4 |

---

## EPIC IV: OPERATING SYSTEM API (2027 Q2-Q3)

| Feature | Stories | Status | PRs | Release |
|---------|---------|--------|-----|---------|
| MCP Server v1 | [OS-001] Company search + profile tools | ❌ P2 | — | v0.5 |
| GraphQL Surface | [OS-002] Schema + resolvers | ❌ P2 | — | v0.6 |
| Agent SDK | [OS-003] Python SDK package | ❌ P2 | — | v0.7 |

---

## BACKLOG ITEM TEMPLATE

```
---
ID: STO-001
Title: Implement PostgresIdentityRepository
Epic: EPIC I — Platform Foundation
Capability: CAP-001 — PostgreSQL Persistence
Feature: Identity Repository
Priority: P0
Status: 🔴 Not Started
Story Points: 8
Dependencies: None
Acceptance Criteria:
  - InMemoryIdentityRepository and PostgresIdentityRepository implement same interface
  - All IdentityService tests pass with both implementations
  - PostgreSQL connection managed via async SQLAlchemy session
  - Connection pooling configured (min=5, max=20)
  - Transactions handled correctly (commit on success, rollback on error)
  - Integration tests cover: create, read, update, delete, list, pagination
Technical Notes:
  - Use SQLAlchemy 2.0 async pattern
  - Repository interface in salesos/sdk/repository.py
  - Follow existing patterns from Company module
PRs: []
Release: v0.1
---
```

---

## RELEASE TRACKING

| Release | Date | Capabilities | Status |
|---------|------|-------------|--------|
| v0.1 | 2026 Q3 | PostgreSQL Persistence | 🔴 Planned |
| v0.2 | 2026 Q3 | Frontend MVP + Data Ingestion | 🔴 Planned |
| v0.3 | 2026 Q4 | Entity Resolution + Search UI | 🔴 Planned |
| v0.4 | 2026 Q4 | Feature Store + Revenue Brain Design | 🟡 Planned |
| v0.5 | 2027 Q1 | AI Copilot + MCP Server | ❌ |
| v0.6 | 2027 Q2 | Digital Twin v1 + GraphQL | ❌ |
| v0.7 | 2027 Q3 | Agent Runtime + Business Rules | ❌ |
| v0.8 | 2027 Q4 | Simulation + Experiment + AI Governance | ❌ |

---

*This backlog is the single source of truth for what we are building and when. Every feature must trace to a capability. Every capability must trace to an epic. Every epic must trace to the 5-Year Roadmap.*
