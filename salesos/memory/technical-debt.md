# Technical Debt Register

> Last Updated: 2026-07-17 (WO-001)
> Maintained by: Engineering Team

---

## Active Items

| ID | Area | Description | Impact | Severity | Effort | Owner | Status | Resolution Plan |
|----|------|-------------|--------|----------|--------|-------|--------|-----------------|
| TD-002 | Infrastructure | Event bus → Kafka | No durable event streaming; limited scalability for cross-domain events | Medium | 2 sprints | Architecture | Open | Migrate event bus to Kafka with dead-letter queues and event replay |
| TD-004 | Config | Hardcoded configurations | Environment-specific values embedded in source; difficult to manage per-env | Low | 3 days | Backend | Resolved | 2026-07-14: Extracted hardcoded values from test_store.py, conftest.py, seed_graph.py, prod_audit.py, search_benchmark.py, api.ts — all now use config.py/settings/env vars. See TD-004-R1 |
| TD-005 | Security | Authorization review pending | 1 open issue remaining; RBAC hardened, CSRF added | Medium | 1 sprint | Security | Open | Complete authorization audit and remediate all findings |
| TD-S0-01 | Architecture | Dual Widget SDKs (Dashboard v1.0 frozen vs Workspace v5 active) | ADR-003 frozen interface duplicated; DRY violation; maintenance overhead | **Critical** | 3-4 days | Architecture | Open | Merge Workspace SDK into canonical Dashboard SDK; keep v1.0 API surface; schedule Sprint 3 |
| TD-S0-02 | Backend | `main.py` at 908 lines exceeds 600-line limit | Violates PROJECT_BIBLE §12.2.7; reduces maintainability | High | 1-2 days | Backend | Resolved | Resolved by refactoring into `app/middleware_setup.py`, `app/routers/router_registry.py`, `app/startup/`. `main.py` now 361 lines. (Pre-WO-001) |
| TD-S0-03 | Frontend | `src/lib/api.ts` at 1,734 lines exceeds 600-line limit | Violates PROJECT_BIBLE §12.2.7; monolithic types + API calls + localStorage | High | 2-3 days | Frontend | Open | Split by domain: `src/lib/api/{domain}.ts` |
| TD-S0-04 | Backend | Identity service bypasses own repositories (`UserRepository`/`TenantRepository`) | Violates Repository Pattern (ARC-3.3); domain documented as 100% compliant has clear violation | High | 1 day | Backend | Open | Refactor `identity/service.py` to use existing repository interfaces |
| TD-S0-05 | Backend | `init_db()` creates tables via raw SQL, bypassing Alembic | Migration history does not reflect actual DB state; schema drift risk | High | 2 days | Backend | Open | Create Alembic revision capturing current `init_db()` state; deprecate raw SQL table creation |
| TD-S0-06 | Backend | InMemoryDecisionCenterRepository active in production | No PostgreSQL persistence for Decision Center data | High | 2 days | Backend | Open | Create SQLAlchemy model + PostgreSQL repo; swap in DI |
| TD-S0-07 | Frontend | Decision Engine (`packages/platform/decision/`) is a non-functional stub | Documented as frozen Decision Platform component but throws "Not implemented" | Medium | 3-5 days or documentation | Frontend | Open | Option A: implement fully; Option B: officially deprecate with ADR for v2.5 |
| TD-S0-08 | Backend | BodyCacheMiddleware + downstream middleware interaction bug | Blocks HTTP load testing; documented in performance dashboard | Medium | 1 day | Backend | Open | Fix POST body buffering to not block downstream middleware |
| TD-S0-09 | Backend | Dual domain locations (`domains/search/` + `app/modules/search/`) | Ambiguity about canonical location; developer confusion | Low | 1 day | Backend | Open | Remove empty module directories; document `domains/` vs `app/modules/` distinction |
| TD-S0-10 | Both | Compliance scores misaligned between documentation and reality | Previously reported 87% (self-reported estimate); measured ~85% | Medium | Ongoing | Architecture | Open | Compliance scores updated in ARCHITECTURE_COMPLIANCE.md; accuracy improved through Sprint 0 codebase analysis |

---

## Resolved Items

| ID | Area | Description | Resolved | Resolution |
|----|------|-------------|----------|------------|
| TD-ARC-001 | Architecture | Container/View Pattern for admin widgets | 2026-07-14 | HealthDashboard split into HealthDashboardContainer + HealthDashboardView. |
| TD-ARC-002 | Architecture | Direct axios calls → centralized api client | 2026-07-14 | Replaced axios with api client in 5 revenue-execution files: RevenueWorkspace, OpportunityWorkspace, PipelineWorkspace, EmailIntelligenceWidget, MeetingIntelligenceWidget. |
| TD-ARC-003 | Architecture | localStorage for business data removed | 2026-07-14 | Removed localStorage persistence from OnboardingProvider (onboarding progress) and CopilotPanel (chat messages). Business data now uses in-memory state only. |
| TD-ARC-004 | Config | api.ts hardcoded URL | 2026-07-14 | Added API_URL env var fallback before hardcoded localhost. |
| TD-ARC-005 | Config | salesos_api_url setting | 2026-07-14 | Added `salesos_api_url` to app/config.py for demo/script usage. |
|----|------|-------------|----------|------------|
| TD-001 | Data Layer | In-memory repositories → PostgreSQL | 2026-07-12 | All domain repos migrated: Company, Scoring, Workflow, Timeline, Contact, Admin, Audit, Telemetry |
| TD-003 | Quality | Test coverage below 85% target | 2026-07-12 | Coverage reached 93% — 207 suites, 2054 tests, 0 failures |
| TD-006 | Frontend | `api.ts` at 1169 lines needs splitting | 2026-07-12 | Split types → `api/types.ts`, client → `api/client.ts` (1320→629 lines) |
| TD-007 | Frontend | `pipeline-kanban.tsx` at 512 lines | 2026-07-12 | Extracted `OpportunityCard.tsx`, `PipelineColumn.tsx` (543→411 lines) |
| TD-008 | Frontend | `any` types in production code (~40) | 2026-07-12 | Replaced all 29 `any` types with specific types across 13 files |
| TD-009 | Quality | Unit test coverage at 93% | 2026-07-12 | 207 suites, 2054 tests, 0 failures — no longer blocking |
| TD-004-R1 | Config | Hardcoded Config Cleanup | 2026-07-14 | Extracted hardcoded DB/Neo4j/Redis/Kafka URLs from test_store.py, conftest.py, seed_graph.py, prod_audit.py, search_benchmark.py, api.ts. All now reference app.config.settings or env vars. Added SALESOS_API_URL to .env.example and config.py. 8 files cleaned. |
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
| TD-S0-02-R1 | Backend | main.py 908 lines → 361 lines | 2026-07-17 | Refactored into app/middleware_setup.py, app/routers/router_registry.py, app/startup/. Verified on 2026-07-17. |

---

## Summary

| Metric | Value |
|--------|-------|
| Active items | 11 (TD-002, TD-005, TD-S0-01, TD-S0-03 through TD-S0-10) |
| Resolved items | 23 |
| Total tracked | 34 |
| Last updated | 2026-07-17 (WO-001 — Security Hardening) |

## Sprint 0 Additions

The 10 new items (TD-S0-01 through TD-S0-10) were identified during Sprint 0 Architecture Reconciliation — the first full codebase analysis comparing actual repository state against approved architecture documentation. Details in `docs/CURRENT_ARCHITECTURE.md` and `docs/MIGRATION_MATRIX.md`.

### WO-001 Resolutions

| ID | Resolution | Verified By |
|----|-----------|-------------|
| TD-S0-02 | `main.py` refactored from 908→361 lines via `middleware_setup.py`, `router_registry.py`, `startup/`. Verified codebase analysis 2026-07-17. | Codebase revalidation |
| SEC-001 | Webhooks router already has `Depends(verify_token)` — router-level auth | Codebase revalidation |
| SEC-003 | GraphQL `get_context()` already validates Bearer + tenant match | Codebase revalidation |
| SEC-004 | JWKS already serves RS256 keys (4096-bit RSA) at `/.well-known/jwks.json` | Codebase revalidation |
| SEC-016 | Zero f-string Cypher queries found. All data via `$param`. Identifiers validated via `_validate_cypher_identifier()`. | Codebase revalidation |

---

## Guidelines

- **Logging**: Every new TD must include: description, impact, severity (High/Medium/Low), estimated effort, owner, and resolution plan
- **High severity** items must be resolved within 1 Sprint
- **Medium severity** items should be addressed within 2 Sprints
- **Low severity** items are scheduled during maintenance windows
- Review this register at the start of every Sprint planning
