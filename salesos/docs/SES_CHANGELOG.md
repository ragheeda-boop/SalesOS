# SalesOS — SES CHANGELOG

> **Sprint 0 Deliverable: Architecture Reconciliation**
> Documents changes required to the System Evaluation Specification (SES) based on real repository findings.
> The SES is embedded across: ENGINEERING_IMPLEMENTATION_SPEC.md, ARCHITECTURE_BOOK.md Appendix F, PROJECT_BIBLE.md, ENGINEERING_CONSTITUTION.md.
> Date: 2026-07-17 | Classification: Confidential

---

## Change 001: Widget SDK — Single Canonical Implementation

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_IMPLEMENTATION_SPEC.md §1.2, ADR-003 |
| **Current SES** | Widget SDK v1.0 is the single, frozen SDK for all widget development |
| **Reality** | Two SDKs exist: Dashboard SDK (`src/features/dashboard/sdk/`, frozen v1.0) AND Workspace SDK (`packages/workspace/`, active v5) |
| **Required SES Change** | SES must acknowledge the dual-SDK reality and mandate consolidation in Sprint 3. The SES must state: "There is exactly one canonical Widget SDK. All widgets use the same `createWidget()` implementation." |
| **New SES Baseline** | `createWidget()` is frozen at the API level. The implementation must be single-sourced. Any extensions (workspace-specific) are via adapter or extension interface, not duplicate `createWidget()`. |
| **Migration Path** | Merge Workspace SDK into Dashboard SDK. Remove duplicate `createWidget()`. Remove `workspace-adapter.tsx`. Document in ADR-0032. |

---

## Change 002: Compliance Score Methodology

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_IMPLEMENTATION_SPEC.md §8 (Quality Gates), ENGINEERING_DASHBOARD.md |
| **Current SES** | Compliance scores are self-reported engineering estimates. Dashboard warns: "Scores without [A] are self-reported engineering estimates and should be treated as directional until independently verified." |
| **Reality** | Previously reported 87% overall compliance. Full codebase analysis in Sprint 0 measured ~85%. Gap analysis reveals scores were optimistic by ~2-3%. Dual SDK gap alone reduces Widget SDK domain from 100% to 70%. |
| **Required SES Change** | SES must mandate that compliance scores are **measured** (not estimated) before each release. The SES must specify: "Pre-release compliance verification shall use [A] (audited) methodology. Self-reported scores are provisional only." |
| **New SES Baseline** | Compliance verification script (`scripts/arch-compliance.ps1`) output is the single source of truth for compliance scores. Self-reported estimates are not permitted in the ENGINEERING_DASHBOARD without [A] annotation. |
| **Migration Path** | (Process change only) Update ENGINEERING_DASHBOARD to mark previously overestimated scores. Add script-measured scores as the baseline. |

---

## Change 003: File Size Budget Enforceability

| Field | Value |
|-------|-------|
| **SES Reference** | PROJECT_BIBLE.md §12.2.7 — "Not exceed 600 lines per file" |
| **Current SES** | 600-line limit is a documented rule with no enforcement mechanism |
| **Reality** | Two files exceed the limit: `main.py` (908 lines) and `api.ts` (1,734 lines). No CI gate catches this. |
| **Required SES Change** | SES must specify the enforcement mechanism: "File size limit shall be enforced via CI (CI scanner or lint rule). Exceptions require documented ADR approval." |
| **New SES Baseline** | CI pipeline includes a file-size check with 600-line limit. Files exceeding limit are flagged as violations, not blockers (to allow legacy migration). New files must comply. |
| **Migration Path** | Add file-size check to `scripts/arch-compliance.ps1` or as a standalone CI step. Create `pyproject.toml` and ESLint rules for enforcement. |

---

## Change 004: Repository Pattern — Identity Domain Exception

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_CONSTITUTION.md Art. 3.3, ARC-3.3 |
| **Current SES** | "Every Domain Service depends on Repository Interface. The Implementation is in Infrastructure Layer Only. Domain Layer doesn't know about the database." — with NO exceptions |
| **Reality** | Identity service (`app/modules/identity/service.py`) uses `db.execute(select(...))` directly. The `UserRepository` and `TenantRepository` interfaces exist but are unused. This is a clear violation in the domain documented as 100% compliant. |
| **Required SES Change** | SES must either: (a) mandate the Identity service be refactored to use its repositories within 1 sprint, or (b) document a formal exception with justification and expiration date. |
| **New SES Baseline** | No exceptions to Repository Pattern. All domain services must be refactored to use repository interfaces by end of Sprint 2. |
| **Migration Path** | Refactor `identity/service.py` to inject and use `UserRepository`/`TenantRepository`. Remove raw `db.execute()` calls. |

---

## Change 005: Decision Engine — Complete vs Planned

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_IMPLEMENTATION_SPEC.md §1.2, DECISION_PLATFORM_ARCHITECTURE.md |
| **Current SES** | Decision Platform is documented as a complete, frozen component in the architecture. Decision Engine is core to all scoring and recommendations. |
| **Reality** | Backend Decision Engine is complete. Frontend Decision Engine (`packages/platform/decision/index.ts`) is a stub that throws "Not implemented." Scoring domain at 92% compliance because frontend Decision Engine is non-functional. |
| **Required SES Change** | SES must clearly distinguish between: (a) backend Decision Platform (complete) and (b) frontend Decision Platform (planned). The SES must set a timeline for completion or document an official deferral. |
| **New SES Baseline** | Option A (Recommended): Frontend Decision Engine targeted for Sprint 11. Scoring domain target adjusted to 95% conditional on Decision Engine delivery. Option B: Officially deferred to v2.5, scoring compliance target adjusted accordingly. |
| **Migration Path** | Decision required (see ADR-0033). If implemented: Sprint 11. If deferred: update all references to Decision Platform completeness. |

---

## Change 006: Migration History Integrity

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_IMPLEMENTATION_SPEC.md §1.3 (Backend Stack), ARCHITECTURE_BOOK.md §4 |
| **Current SES** | "Database: PostgreSQL + Neo4j" — no specification of migration mechanism |
| **Reality** | `init_db()` in `config.py` creates tables via raw SQL. Alembic is configured but not the actual source of truth. Migration history and actual DB state can diverge. |
| **Required SES Change** | SES must specify: "All database schema changes must go through Alembic migrations. `init_db()` is responsible only for extensions, triggers, and idempotent setup operations, not table creation." |
| **New SES Baseline** | Alembic is the single source of truth for schema state. A baseline Alembic revision must capture all tables currently created by `init_db()`. Raw SQL table creation in `init_db()` is deprecated. |
| **Migration Path** | Create Alembic revision documenting current schema. Remove table creation from `init_db()`. Add CI check ensuring new migrations are created for any schema change. |

---

## Change 007: Performance Testing Blockers

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_IMPLEMENTATION_SPEC.md §8 (Performance Review), FINAL_PERFORMANCE_REPORT.md |
| **Current SES** | All endpoints must meet performance budgets. Performance review gate requires passing budgets. |
| **Reality** | BodyCacheMiddleware + downstream middleware interaction bug blocks HTTP-level load testing. DB-level benchmarks isolate DB performance but do not validate full HTTP path. Performance report has "Medium" confidence for HTTP-level metrics. |
| **Required SES Change** | SES must recognize that HTTP-level performance testing is blocked. Performance gate should differentiate between: (a) DB-level benchmarks (passing) and (b) HTTP-level benchmarks (blocked). The middleware bug must be a prerequisite for full performance certification. |
| **New SES Baseline** | DB-level budgets are final (verified). HTTP-level budgets are conditional on middleware fix. Performance gate is provisionally passed with "Medium" confidence pending middleware correction in Sprint 1. |
| **Migration Path** | Fix BodyCacheMiddleware bug in Sprint 1. Re-run HTTP-level benchmarks. Confirm budgets. Upgrade performance confidence to "High." |

---

## Change 008: Sprint Structure — Sprint 0 Addition

| Field | Value |
|-------|-------|
| **SES Reference** | ENGINEERING_IMPLEMENTATION_SPEC.md §8 (Sprints), docs/vnext/IMPLEMENTATION_PLAN.md |
| **Current SES** | Sprint 1 is the first sprint in the build plan. "Phase 0: Platform Stabilization (Sprints 1-2)" |
| **Reality** | The codebase is a production platform, not greenfield. Architecture reconciliation (Sprint 0) is required before any implementation sprint. The fundamental assumption of the build plan was incorrect. |
| **Required SES Change** | SES must insert Sprint 0 (Architecture Reconciliation) before Sprint 1. All existing sprint references must be shifted by +1 (Sprint 1 → Sprint 2, etc.). |
| **New SES Baseline** | Sprint 0: Architecture Reconciliation (documentation only, no code changes). Sprint 1+: Implementation following reconciled architecture. |
| **Migration Path** | (Already in progress — this document is part of Sprint 0). Update IMPLEMENTATION_PLAN.md to insert Sprint 0. Update work orders to shift sprint numbers. |

---

## Change 009: Build Order Dependency Graph Correction

| Field | Value |
|-------|-------|
| **SES Reference** | IMPLEMENTATION_ROADMAP.md §4 (Dependency Graph), docs/vnext/IMPLEMENTATION_PLAN.md |
| **Current SES** | Sprint 1 (Security) and Sprint 2 (Infrastructure) have no dependency on each other. |
| **Reality** | Multiple Sprint 0 findings (file size violations, Identity repo bypass, dual SDK) must be resolved before subsequent sprints. Specifically: Dual SDK merge (TD-S0-01) must happen before any new widget development in Sprint 3+. |
| **Required SES Change** | SES must add critical-path dependencies: (1) Dual SDK merge is a prerequisite for Sprint 3+ widget work. (2) Identity service refactoring is a prerequisite for Identity domain extensions. (3) init_db() baseline is a prerequisite for Sprint 2+ infrastructure. |
| **New SES Baseline** | Dependency graph updated. Widget SDK merge added as hard prerequisite for Phase 1 (Design System) sprints. Identity refactoring added as prerequisite for any Identity domain changes. |

---

## Change Summary

| # | SES Change | Criticality | Applies To | Sprint |
|---|-----------|-------------|-----------|--------|
| 001 | Single canonical Widget SDK | 🔴 **High** — ADR-003 violation | ADR-003, ENGINEERING_IMPLEMENTATION_SPEC §1.2 | S0-ADR |
| 002 | Measured (not estimated) compliance scores | 🟡 Medium — accuracy | ENGINEERING_DASHBOARD, compliance process | S0 |
| 003 | File size budget enforceability | 🟡 Medium — rule without teeth | PROJECT_BIBLE §12.2.7, CI pipeline | S2 |
| 004 | Identity repository pattern exception | 🟡 Medium — documented violation, no exception allowed | ENGINEERING_CONSTITUTION Art. 3.3 | S0-ADR |
| 005 | Decision Engine completeness status | 🟡 Medium — documented as complete, isn't | DECISION_PLATFORM_ARCHITECTURE.md | S0-ADR |
| 006 | Migration history integrity | 🟡 Medium — schema drift risk | ARCHITECTURE_BOOK §4, database.py | S1 |
| 007 | Performance testing blockers acknowledged | 🟡 Medium — blocked HTTP testing | FINAL_PERFORMANCE_REPORT.md | S1 |
| 008 | Sprint 0 added to build plan | 🟡 Medium — greenfield assumption incorrect | IMPLEMENTATION_PLAN.md | S0 |
| 009 | Build order dependency graph corrected | 🟡 Medium — missing critical paths | IMPLEMENTATION_PLAN.md, work orders | S0 |

---

## Decision Required

For changes 001, 004, and 005 — ADR updates are required to reconcile the approved architecture with the real repository. These are captured in the ADR deliverables.

For changes 002, 003, 006, 007, 008, 009 — updates to documentation are sufficient. The SES baseline shifts to reflect reality without requiring new decisions.
