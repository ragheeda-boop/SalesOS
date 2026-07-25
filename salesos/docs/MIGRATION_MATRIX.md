# SalesOS — MIGRATION MATRIX

> **Sprint 0 Deliverable: Architecture Reconciliation**
> Maps each architectural component from its current state to its approved target state.
> Date: 2026-07-17 | Classification: Confidential

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Already aligned — no migration needed |
| ⚠️ | Partially aligned — bounded migration required |
| ❌ | Not aligned — migration required |
| 🔴 | Violates frozen interface or mandatory rule |
| 💎 | Improvement opportunity (not a violation) |

---

## 1. Backend Architecture Gaps

| Component | Current State | Target State | Gap | Migration Strategy | Effort | Priority | Sprint |
|-----------|--------------|-------------|-----|-------------------|--------|----------|--------|
| **main.py** | 908-line monolithic startup | ≤ 600 lines, modular startup | 🔴 File size violation (Art. 12.2.7) | Extract `startup/routers.py`, `startup/middleware.py`, `startup/lifespan.py` | 1-2d | High | S1 |
| **Identity Service** | Uses `db.execute()` directly instead of `UserRepository`/`TenantRepository` | Repository pattern — depends on repository interfaces | 🔴 Pattern violation (ARC-3.3) — repos exist but are unused | Refactor service methods to use existing repo interfaces | 1d | High | S2 |
| **init_db()** | Creates tables via raw SQL, bypassing Alembic | All schema changes through Alembic migrations | 🔴 Migration system bypass — schema drift risk | Create Alembic revision capturing current state; deprecate `init_db()` table creation | 2d | High | S1-S2 |
| **InMemoryDecisionCenterRepository** | In-memory repo active in production | PostgreSQL repository | ❌ Not migrated (TD-006 continuation) | Create SQLAlchemy model + PostgreSQL repo; swap DI | 2d | High | S1 |
| **EventBus** | In-memory EventBus (Kafka configured but inactive) | Kafka with dead-letter queues, event replay | ⚠️ Partial — Kafka configured but not wired | Activate Kafka, wire domain events, create consumers | 1-2 sprints | Medium | S11 |
| **Dual domain locations** | `domains/search/` AND `app/modules/search/` (empty) | Single canonical location per domain | ❌ Ambiguity — developer confusion | Remove empty module dirs; document `domains/` vs `app/modules/` distinction | 1d | Low | S2 |
| **register_routers()** | 168-line monolithic function | Domain-specific registration | ⚠️ File size approaching limit | Split into per-domain registration files | 1d | Low | S2 |
| **Health check endpoints** | 4 duplicate variants | Single consolidated endpoint | 💎 Duplication | Consolidate into single `/health` | 0.5d | Low | S2 |
| **Empty directories** | `domains/search/repositories/` empty | No empty directories | 💎 Cleanup | Remove empty dirs | 0.25d | Low | S2 |

---

## 2. Frontend Architecture Gaps

| Component | Current State | Target State | Gap | Migration Strategy | Effort | Priority | Sprint |
|-----------|--------------|-------------|-----|-------------------|--------|----------|--------|
| **Widget SDK** | Dual SDKs: Dashboard SDK (frozen v1.0) + Workspace SDK (active v5) | Single canonical Widget SDK | 🔴 ADR-003 violation — frozen interface duplicated | Merge Workspace SDK into Dashboard SDK; keep v1.0 API surface; extensions via adapter | 3-4d | **Critical** | S0-ADR / S3 |
| **api.ts** | 1,734-line monolithic file | Domain-split files ≤ 600 lines each | 🔴 File size violation (Art. 12.2.7) | Split by domain into `src/lib/api/{domain}.ts` | 2-3d | High | S2 |
| **API client duality** | `src/lib/api.ts` AND `src/lib/api/` both exist | Single centralized client | ⚠️ Partial — dual clients, confusion risk | Consolidate into single pattern; remove redundant files | 1d | Medium | S2 |
| **Decision Engine (frontend)** | `packages/platform/decision/index.ts` throws "Not implemented" | Working Decision Engine with full API | ❌ Stub — documented as frozen but non-functional | Either implement (Sprint 11) or officially deprecate with v2.5 notice | Documentation or 3-5d | Medium | S0-ADR |
| **Hardcoded localStorage keys** | String literals across multiple files | Constants file | 💎 Cleanup | Extract to constants file | 0.5d | Low | S3 |

---

## 3. Domain Gaps

| Domain | Current Compliance | Target Compliance | Gap | Key Issues | Sprint |
|--------|-------------------|-------------------|-----|-----------|--------|
| **Identity** | 100% | 100% | 0 | ✅ No gaps | — |
| **Widget SDK** | 70% | 100% | -30% 🔴 | Dual SDK violation (see §2) | S0-ADR / S3 |
| **Company** | 95% | 95% | 0 | ✅ Minor code smells | — |
| **Search** | 88% | 95% | -7% 🟡 | Repository pattern gaps | S2 |
| **Scoring** | 92% | 95% | -3% 🟡 | Frontend Decision Engine stub | S0-ADR |
| **CRM** | 88% | 95% | -7% 🟡 | Monolithic api.ts | S2 |
| **AI** | 82% | 95% | -13% 🟡 | No evaluation framework; frontend Decision Engine | S12 |
| **Timeline** | 78% | 95% | -17% 🟡 | Architecture redesign needed | S7 |
| **Workflow** | 48% | 95% | -47% 🔴 | Full implementation not started | S11 |
| **OVERALL** | **~85%** | **95%+** | **-10%** | **Dual SDK + Workflow are largest gaps** | S12 |

---

## 4. Infrastructure Gaps

| Component | Current State | Target State | Gap | Sprint |
|-----------|--------------|-------------|-----|--------|
| **Redis** | Configured but idle (in-memory fallback active) | Active caching, rate limiting, session store | ⚠️ Configured, not deployed | S2 |
| **Kafka** | Configured but inactive (in-memory EventBus) | Durable event streaming with DLQ | ❌ Inactive — events lost on restart | S11 |
| **Terraform** | Not configured | Remote state (S3 + DynamoDB) | ❌ Missing | S2 |
| **Helm Charts** | Not configured | Umbrella chart for all runtimes | ❌ Missing | S13 |
| **Production Deploy** | All gates passed but not live | Production environment | ⚠️ Ready but not deployed | Post-S22 |
| **Data Lake** | Not implemented | Iceberg-based data lake | ❌ Missing | Future |

---

## 5. Widget SDK Migration Detail

This is the single most critical migration because it involves a **frozen interface violation**.

### 5.1 Current State

```
DASHBOARD SDK (frozen v1.0)                WORKSPACE SDK (active v5)
src/features/dashboard/sdk/                packages/workspace/
├── createWidget.tsx                        ├── createWidget.tsx        ← DIFFERENT IMPL
├── createDashboardWidget.tsx               ├── createWorkspaceWidget.tsx
├── contract-test-utils.tsx                 ├── testing/
│   └── describeWidgetContract()            │   └── WidgetContract.tsx
├── types.ts                                ├── types.ts
│   (WidgetConfig, WidgetData, ...)         │   (overlapping types)
└── workspace-adapter.tsx                   └── widgets/
    (bridges SDKs)                              4 workspace widgets
```

### 5.2 Target State

```
CANONICAL WIDGET SDK (v1.0 Extended)
packages/widget-sdk/ (moved from src/features/dashboard/sdk/)
├── createWidget.tsx              ← FROZEN — single canonical implementation
├── createDashboardWidget.tsx     ← FROZEN
├── createWorkspaceWidget.tsx     ← NEW — extension, not duplicate
├── contract-test-utils.tsx       ← FROZEN — describeWidgetContract()
├── types.ts                      ← FROZEN
└── workspace-adapter.tsx         ← REMOVED (no longer needed)
```

### 5.3 Migration Steps

| Step | Action | Risk | Impact |
|------|--------|------|--------|
| 1 | Move Dashboard SDK from `src/features/dashboard/sdk/` to `packages/widget-sdk/` | Low — code move only | All imports across features change |
| 2 | Merge Workspace SDK `createWidget()` into canonical `createWidget()` | Medium — API must remain identical | Workspace widgets use canonical impl |
| 3 | Remove `packages/workspace/createWidget.tsx` (delegate to canonical) | Medium — verify all consumers | Eliminates DRY violation |
| 4 | Remove `workspace-adapter.tsx` | Low — no longer needed | Simplifies architecture |
| 5 | Update all widget imports across 13 features | Low — mechanical | All widgets use single SDK |
| 6 | Confirm all widget contract tests pass | Medium — behavior must be identical | Quality assurance |

---

## 6. Decision Platform Migration Detail

### 6.1 Current vs Target

| Component | Backend Current | Frontend Current | Target |
|-----------|----------------|-----------------|--------|
| Decision Engine | ✅ Implemented | ❌ Stub | ✅ Implemented |
| Rule Engine | ✅ Implemented | N/A (backend-only) | ✅ Implemented |
| Scoring Engine | ✅ Implemented | ✅ Connected via API | ✅ Implemented |
| Evidence Engine | ✅ Implemented | N/A | ✅ Implemented |
| Recommendation Engine | ✅ Implemented | ✅ Partial UI | ✅ Implemented |
| Explainability Engine | ✅ Implemented | ✅ Partial UI | ✅ Implemented |
| Feedback Engine | ✅ Implemented | ⚠️ Partial | ✅ Implemented |
| Learning Engine | ⚠️ Partial | N/A | ✅ Implemented |

### 6.2 Options

| Option | Effort | Risk | Recommendation |
|--------|--------|------|---------------|
| A — Implement frontend Decision Engine fully | 3-5d | Medium | Recommended path — aligns with approved architecture |
| B — Officially deprecate, mark as "v2.5 Planned" | 1d documentation | Low | Acceptable if resource-constrained; requires ADR |
| C — Remove stub entirely | 0.5d | Low | Risks confusion — "frozen" interface disappears |

**Recommended**: Option A, but if resourcing constraints prevent it, Option B with a clear ADR.

---

## 7. Compliance Restoration Path

| Phase | Sprints | Compliance Target | Key Actions |
|-------|---------|-------------------|-------------|
| **Sprint 0** | 0 | Baseline at ~85% | Document true state; create ADRs for known violations |
| **Phase 0** | 1-2 | 88% | Fix file sizes, identity repo bypass, in-memory repos |
| **Phase 1** | 3-4 | 92% | Merge dual SDKs, consolidate API client |
| **Phase 3** | 7-8 | 94% | Refactor Timeline, AI domains |
| **Phase 5** | 11-12 | 95% | Implement Workflow, activate Kafka, Decision Engine |

---

## 8. SES (System Evaluation Specification) Gaps

| SES Requirement | Current State | Target | Gap |
|----------------|--------------|--------|-----|
| Single canonical Widget SDK | Dual SDKs | Single SDK | 🔴 SES violation — ADR-003 frozen surface duplicated |
| Decision Platform complete | Frontend Decision Engine is stub | Full implementation | ⚠️ SES deviation — documented as frozen but non-functional |
| Repository Pattern — all domains | Identity service bypasses repos | 100% compliance | ⚠️ SES deviation |
| All endpoints paginated | 12+ unbounded endpoints | All endpoints paginated | ⚠️ SES gap |
| Performance budgets met | POST body middleware bug blocks HTTP testing | All budgets met | ⚠️ SES gap |
| Architecture compliance ≥ 95% | Measured ~85% | ≥ 95% | ❌ SES gap |
| All files ≤ 600 lines | 2 files exceed limit | 100% compliant | ⚠️ SES deviation |

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Workspace SDK merge breaks existing widgets | Medium | High | Comprehensive contract tests before/after merge; parallel testing period |
| Identity service refactoring introduces auth regression | Low | **Critical** | Full auth test suite; manual security review of refactored code |
| init_db() Alembic migration misses existing tables | Medium | High | Thorough inventory of all tables created by init_db() before creating revision |
| Decision Engine stub can't be implemented within budget | High | Medium | Option B (deprecation notice) as fallback |
| Production deployment delayed past target | Medium | Medium | Documented in GA_LAUNCH_PLAN; all gates already passed |

---

## 10. Quick Wins (< 2 days, no behavior change)

| Task | Effort | Impact |
|------|--------|--------|
| Split `register_routers()` into domain files | 1d | Readability, enables independent testing |
| Consolidate 4 health endpoints into 1 | 0.5d | Cleaner API surface |
| Remove empty directories | 0.25d | Repository hygiene |
| Extract localStorage key constants | 0.5d | Maintainability |
| Create Alembic revision for current state | 2d | Foundation for future migrations |
| Document `domains/` vs `app/modules/` distinction | 0.5d | Developer clarity |

---

## 11. Migration Sequencing

```
Sprint 0 (this sprint)
└── Architecture Reconciliation ✅ (current document)
    ├── ADR-0032: Widget SDK reconciliation
    ├── ADR-0033: Decision Engine deprecation or implementation
    └── SES_CHANGELOG: Updated SES baselines

Sprint 1 (Phase 0)
├── File size: main.py → modular startup
├── init_db() → Alembic baseline
├── InMemoryDecisionCenterRepository → PostgreSQL
└── Security fixes (if any)

Sprint 2 (Phase 0)
├── Identity service → repository pattern
├── api.ts → domain-split files
├── API client duality consolidated
├── Empty directories removed
└── Register_routers() → domain files

Sprint 3 (Phase 1)
├── Dual SDK merge ← MUST happen before any new widget
├── localStorage key constants
└── Design system consolidation

Sprint 7 (Phase 3)
├── Timeline domain refactoring (VIO-102)

Sprint 11 (Phase 5)
├── Workflow domain implementation (VIO-101)
├── Kafka activation

Sprint 12 (Phase 5)
├── AI domain evaluation framework (VIO-104)
└── Decision Engine implementation (if not deprecated)
```
