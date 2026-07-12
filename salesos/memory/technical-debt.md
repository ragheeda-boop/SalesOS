# Technical Debt Register

> Last Updated: 2026-07-12
> Maintained by: Engineering Team

---

## Active Items

| ID | Area | Description | Impact | Severity | Effort | Owner | Status | Resolution Plan |
|----|------|-------------|--------|----------|--------|-------|--------|-----------------|
| TD-001 | Data Layer | In-memory repositories → PostgreSQL | Some repos (Company, Scoring, Workflow, Timeline) already on PostgreSQL; Contact still in-memory | High | 2 sprints | Backend | Partially Complete | Contact PostgreSQL repo implemented — `app/modules/contact/repositories.py` + `search_repository.py` |
| TD-002 | Infrastructure | Event bus → Kafka | No durable event streaming; limited scalability for cross-domain events | Medium | 2 sprints | Architecture | Open | Migrate event bus to Kafka with dead-letter queues and event replay |
| TD-003 | Quality | Test coverage at ~93% (target 85%) | Coverage target exceeded; monitoring and customer-success now covered | Medium | Ongoing | QA | Resolved ✅ 2026-07-12 | Coverage reached 93% — 207 suites, 2054 tests, 0 failures, 101 new tests in this session |
| TD-004 | Config | Hardcoded configurations | Environment-specific values embedded in source; difficult to manage per-env | Low | 3 days | Backend | Open | Extract all hardcoded values to environment variables or config files |
| TD-005 | Security | Authorization review pending | 1 open issue remaining; RBAC hardened, CSRF added | Medium | 1 sprint | Security | Open | Complete authorization audit and remediate all findings |
| TD-006 | Frontend | `api.ts` at 1169 lines needs splitting | Monolithic API file harms maintainability; difficult to navigate and test | Medium | 2 days | Frontend | Resolved ✅ 2026-07-12 | Split types → `api/types.ts`, axios client → `api/client.ts`, api.ts → barrel re-export (1320→629 lines) |
| TD-007 | Frontend | `pipeline-kanban.tsx` at 512 lines needs splitting | Single large component with mixed concerns; hard to maintain and test | Medium | 1 day | Frontend | Resolved ✅ 2026-07-12 | Extracted `OpportunityCard.tsx`, `PipelineColumn.tsx` from index (543→411 lines) |
| TD-008 | Frontend | `any` types in production code (~40 occurrences) | Loss of type safety; runtime errors not caught at compile time | Medium | 2 days | Frontend | Resolved ✅ 2026-07-12 | 29 remaining `any` types replaced across 13 files — zero `any` types in production code |
| TD-009 | Quality | Unit test coverage at 93% (exceeded 85% target) | Coverage target exceeded — no longer blocking feature development | High | — | QA | Resolved ✅ 2026-07-12 | 207 suites, 2054 tests, 0 failures, all domains ≥80% coverage |

---

## Resolved Items

| ID | Area | Description | Resolved | Resolution |
|----|------|-------------|----------|------------|
| TD-R1 | Security | Secrets hardcoded in source code | 2026-07-08 | Moved all secrets to environment variables (Sprint 0.5 S5/S8-S10) |
| TD-R2 | Architecture | Cross-domain imports violating bounded contexts | 2026-07-08 | Fixed via SDK-only inter-domain communication (Sprint 0.5 A1/A3) |
| TD-R3 | Security | Unprotected API routes | 2026-07-08 | Added auth middleware to all routes (Sprint 0.5 S2) |
| TD-R4 | Security | Refresh token architecture | 2026-07-08 | Implemented proper refresh token rotation (Sprint 0.5 S6) |
| TD-R5 | Frontend | api.ts monolithic (1169 lines) | 2026-07-12 | Split types → api/types.ts, client → api/client.ts (1320→629 lines) |
| TD-R6 | Frontend | pipeline-kanban.tsx at 512 lines | 2026-07-12 | Extracted OpportunityCard.tsx, PipelineColumn.tsx (543→411 lines) |
| TD-R7 | Frontend | `any` types in production code (29 remaining) | 2026-07-12 | Replaced all 29 `any` types with specific types across 13 files |
| TD-R8 | Quality | Unit test coverage (93%, exceeded 85%) | 2026-07-12 | 207 suites, 2054 tests, 0 failures — 101 new tests in session |
| TD-R9 | Data Layer | Contact domain PostgreSQL repos | 2026-07-12 | ContactRepository + ContactSearchRepository implemented for standalone Contact module |

---

## Guidelines

- **Logging**: Every new TD must include: description, impact, severity (High/Medium/Low), estimated effort, owner, and resolution plan
- **High severity** items must be resolved within 1 Sprint
- **Medium severity** items should be addressed within 2 Sprints
- **Low severity** items are scheduled during maintenance windows
- Review this register at the start of every Sprint planning
