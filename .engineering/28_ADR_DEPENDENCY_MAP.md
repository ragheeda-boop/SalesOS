---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 28 â€” ADR DEPENDENCY MAP

> Purpose: for every ADR, the affected modules/directories, related APIs, database objects, deployments, and tests. Any agent modifying a governed file must consult this map to know which ADR rules it and whether that ADR is still Active.
> **Conflicts recorded as observed facts; nothing corrected.**

## Traceability schema

```
ADR-### â†’ Affected DIR / Module â†’ Related API (FILE) â†’ DB objects â†’ Tests (TST) â†’ Deployment â†’ Status
```

## 1. Product-root ADRs (`docs/adr/`)

### ADR-030 â€” Unified Provider Architecture (Status: Accepted)
- **DIR/Modules:** `salesos/backend/intelligence/providers/` (target), `salesos/backend/domains/ai/service.py`, `salesos/backend/intelligence/agents/llm.py`, all agent code
- **Related APIs:** `LLMProvider.chat()/chat_stream()/embed()`; `ProviderFactory.create()/get_provider()`
- **DB objects:** none
- **Tests:** mock-provider tests per provider (no specific file named); CI bans direct OpenAI/Anthropic SDK imports outside `intelligence/providers/`
- **Deployment:** backend image (intelligence layer)
- **Status note:** Active; date mismatch index vs file (LOW)

### ADR-031 â€” Webhook Auth API Key Assessment (Status: Accepted â€” No Change Required)
- **DIR/Modules:** `salesos/backend/app/modules/webhooks/router.py`, `salesos/backend/app/dependencies.py`
- **Related APIs:** `FILE: app/modules/webhooks/router.py` â†’ `/api/v1/webhooks` (JWT `verify_token` + `get_current_tenant_id`)
- **DB objects:** `webhook_subscriptions`, `webhook_deliveries`, `webhook_endpoints`
- **Tests:** none named
- **Deployment:** backend
- **Status note:** Active; future incoming webhook receiver should use API keys (out of scope)

### ADR-033 â€” Decision Engine Lifecycle (Status: CONFLICT â€” index Accepted, file Proposed)
- **DIR/Modules:** `salesos/frontend/packages/platform/decision/` (currently STUB that throws), `salesos/backend/domains/decision/`, `salesos/backend/domains/scoring/`, `salesos/scripts/arch-compliance.ps1`
- **Related APIs:** actual runtime endpoints `POST /api/v1/decision/evaluate`, `POST /api/v1/decision/next-best-action`, `GET /api/v1/decisions/history`, `GET /api/v1/decisions/{id}`, `GET /api/v1/decision/metrics` (runtime/decision_runtime/router.py). ADR cites non-matching paths `/api/v1/decisions/evaluate`, `/api/v1/decisions/recommend`, `/api/v1/decisions/context/{id}` â€” **contract drift (MEDIUM)**
- **DB objects:** `decisions`, `decision_center_decisions/audits/feedback/templates`
- **Tests:** unit test `useDecision()`; integration `POST /api/v1/decision/evaluate`; `scripts/arch-compliance.ps1` (Scoring â‰¥95%)
- **Deployment:** frontend (decision package) + backend
- **Status note:** If treated as binding â†’ Sprint 11 (Phase 5) FE decision engine implementation

### ADR-034 â€” Repository Pattern Compliance (Status: CONFLICT â€” index Accepted, file Proposed)
- **DIR/Modules:** `salesos/backend/app/modules/identity/service.py`, `salesos/backend/app/modules/identity/repositories.py`, `salesos/scripts/arch-compliance.ps1`
- **Related APIs:** all 12 Identity endpoints (unchanged, response-identical)
- **DB objects:** none (no schema change)
- **Tests:** full Identity suite (~88% coverage); swap `AsyncSession` mocks for `InMemoryUserRepository`
- **Deployment:** backend
- **Status note:** Identity documented as 100% compliant is the actual violator (observed)

### ADR-035 â€” Sprint 0 Architecture Reconciliation (Status: Proposed)
- **DIR/Modules:** docs only; no code
- **Related APIs / DB:** none
- **Tests:** none
- **Deployment:** none
- **Status note:** Produces CURRENT/TARGET architecture, MIGRATION_MATRIX, compliance/debt updates; build plan 22â†’23 sprints

## 2. Governance-submodule ADRs (`engineering-os/adr/`)

### ADR-001 â€” Modular Monolith Foundation (Accepted)
- **Governs:** whole `salesos/backend` layering (app / domains / runtime / sdk / intelligence); SDK may not import domains (enforced by `TST: salesos/backend/tests/test_architecture.py` Rule 3); kernel domains may not import commercial (Rule 2)
- **Related APIs:** all backend APIs
- **Deployment:** backend
- **Status:** Active

### ADR-002 â€” Executive Intelligence Workspace (Accepted)
- **Governs:** Executive/decision intelligence surfaces; referenced by ADR-033; frontend workspace SDK
- **Related APIs:** `/api/v1/executive-dashboard`, decision surfaces
- **Status:** Active

### ADR-003 â€” Widget SDK v1 Freeze (Accepted, amended by ADR-0032/D-016)
- **Governs:** `salesos/frontend/src/features/dashboard/sdk/` (frozen v1.0) and widget contract
- **Status:** Frozen; superseded in part by ADR-0032 (reconciliation)

### ADR-0032 â€” Widget SDK Reconciliation (Status: CONFLICT â€” index Accepted / file Proposed / D-016 Approved)
- **Governs:** Dashboard SDK v1.0 â†’ canonical `salesos/frontend/packages/widget-sdk/`; delete workspace duplicates
- **Related APIs:** widget contract; frontend workspace
- **Status note:** authority ambiguous pending conflict resolution

### ADR-012 â€” Activity Intelligence Capability (Proposed, unindexed)
- **Governs:** `salesos/backend/intelligence/activity_intelligence/`, `salesos/backend/runtime/activity_runtime/`, `domains/commercial/{activity,email,meeting}/`, `salesos/backend/app/routers/meetings.py`
- **Related APIs:** `/api/v1/activity/*`, meeting intelligence
- **Status:** not in index (MEDIUM)

## 3. Data-namespace ADR

### ADR-Data-001 â€” Identity Resolution v3 (Accepted, separate namespace)
- **Governs:** `data/` import pipeline; `data/scripts/phase4_identity_v4.py` (ADR describes v3 â€” drift)
- **DB:** Notion import â†’ golden entities
- **Status note:** referenced report `data/reports/identity_quality_report.md` missing

## 4. Cross-map: DIR â†’ governing ADR (who rules what)

| Path (DIR:) | Governing ADR | Active? |
|---|---|---|
| `salesos/backend/app/modules/identity/` | ADR-034, ADR-001 | ADR-034 status conflict (Proposed vs Accepted) |
| `salesos/backend/domains/commercial/` + `revenue/` + `decision/` | ADR-001 (Rule 5 registration in SDK registry) | Active |
| `salesos/backend/intelligence/providers/` | ADR-030 | Active |
| `salesos/backend/app/modules/webhooks/` | ADR-031 | Active |
| `salesos/frontend/packages/platform/decision/` | ADR-033 | Conflict |
| `salesos/frontend/src/features/dashboard/sdk/` + `packages/widget-sdk/` | ADR-003 + ADR-0032 | ADR-0032 conflict |
| `salesos/backend/domains/search/` | ADR-026 (`salesos/backend/docs/adr/0026-hybrid-search.md`; DEC-135) + ADR-001 (Rule 4 frozen interfaces) | Active |
| `data/` | ADR-Data-001 | Active (drift) |
| `salesos/backend/runtime/activity_runtime/`, `intelligence/activity_intelligence/` | ADR-012 | Unindexed |

## 5. When this file changes

- Update together with `27_ADR_INDEX.md` whenever an ADR affects new modules, APIs, DB objects, or tests.

## 6. Conflict summary (recorded, not fixed)

Full list in `27_ADR_INDEX.md` Â§4 and `18_TECH_DEBT.md`. Highest severity: ADR-033/034 status conflicts (HIGH); capability registry secondary extras (INFO after DEC-134a); ADR-025..028 path conflict **RESOLVED (DEC-135)** pending `.engineering/` commit via criterion **4.5**.
