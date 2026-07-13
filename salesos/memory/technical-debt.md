# Technical Debt Register

> Last Updated: 2026-07-13
> Maintained by: Engineering Team

---

## Active Items

| ID | Area | Description | Impact | Severity | Effort | Owner | Status | Resolution Plan |
|----|------|-------------|--------|----------|--------|-------|--------|-----------------|
| TD-002 | Infrastructure | Event bus → Kafka | No durable event streaming; limited scalability for cross-domain events | Medium | 2 sprints | Architecture | Open | Migrate event bus to Kafka with dead-letter queues and event replay |
| TD-004 | Config | Hardcoded configurations | Environment-specific values embedded in source; difficult to manage per-env | Low | 3 days | Backend | Open | Extract all hardcoded values to environment variables or config files |
| TD-005 | Security | Authorization review pending | 1 open issue remaining; RBAC hardened, CSRF added | Medium | 1 sprint | Security | Open | Complete authorization audit and remediate all findings |

---

## Resolved Items

| ID | Area | Description | Resolved | Resolution |
|----|------|-------------|----------|------------|
| TD-001 | Data Layer | In-memory repositories → PostgreSQL | 2026-07-12 | All domain repos migrated: Company, Scoring, Workflow, Timeline, Contact, Admin, Audit, Telemetry |
| TD-003 | Quality | Test coverage below 85% target | 2026-07-12 | Coverage reached 93% — 207 suites, 2054 tests, 0 failures |
| TD-006 | Frontend | `api.ts` at 1169 lines needs splitting | 2026-07-12 | Split types → `api/types.ts`, client → `api/client.ts` (1320→629 lines) |
| TD-007 | Frontend | `pipeline-kanban.tsx` at 512 lines | 2026-07-12 | Extracted `OpportunityCard.tsx`, `PipelineColumn.tsx` (543→411 lines) |
| TD-008 | Frontend | `any` types in production code (~40) | 2026-07-12 | Replaced all 29 `any` types with specific types across 13 files |
| TD-009 | Quality | Unit test coverage at 93% | 2026-07-12 | 207 suites, 2054 tests, 0 failures — no longer blocking |
| TD-R1 | Security | Secrets hardcoded in source code | 2026-07-08 | Moved all secrets to environment variables (Sprint 0.5 S5/S8-S10) |
| TD-R2 | Architecture | Cross-domain imports violating bounded contexts | 2026-07-08 | Fixed via SDK-only inter-domain communication (Sprint 0.5 A1/A3) |
| TD-R3 | Security | Unprotected API routes | 2026-07-08 | Added auth middleware to all routes (Sprint 0.5 S2) |
| TD-R4 | Security | Refresh token architecture | 2026-07-08 | Implemented proper refresh token rotation (Sprint 0.5 S6) |
| TD-R5 | Frontend | api.ts monolithic (1169 lines) | 2026-07-12 | Split types → api/types.ts, client → api/client.ts (1320→629 lines) |
| TD-R6 | Frontend | pipeline-kanban.tsx at 512 lines | 2026-07-12 | Extracted OpportunityCard.tsx, PipelineColumn.tsx (543→411 lines) |
| TD-R7 | Frontend | `any` types in production code (29 remaining) | 2026-07-12 | Replaced all 29 `any` types with specific types across 13 files |
| TD-R8 | Quality | Unit test coverage (93%, exceeded 85%) | 2026-07-12 | 207 suites, 2054 tests, 0 failures — 101 new tests in session |
| TD-R9 | Data Layer | Contact domain PostgreSQL repos | 2026-07-12 | ContactRepository + ContactSearchRepository implemented for standalone Contact module |
| TD-R10 | Data Layer | Admin module PostgreSQL repos | 2026-07-12 | 7 Postgres repos (Plan, License, Invoice, FeatureFlag, Job, AICost, Health) with SQLAlchemy ORM models |
| TD-R11 | Data Layer | Telemetry PostgreSQL migration | 2026-07-12 | Router switched from InMemoryTelemetryRepository to PostgresTelemetryRepository |

---

## Summary

| Metric | Value |
|--------|-------|
| Active items | 3 (TD-002, TD-004, TD-005) |
| Resolved items | 17 |
| Total tracked | 20 |
| Last updated | 2026-07-13 |

---

## Guidelines

- **Logging**: Every new TD must include: description, impact, severity (High/Medium/Low), estimated effort, owner, and resolution plan
- **High severity** items must be resolved within 1 Sprint
- **Medium severity** items should be addressed within 2 Sprints
- **Low severity** items are scheduled during maintenance windows
- Review this register at the start of every Sprint planning
