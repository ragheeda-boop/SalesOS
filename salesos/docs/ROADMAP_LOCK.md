# SalesOS — Roadmap Lock

> **Sprint 0.5 Deliverable: Platform Freeze**
> Date: 2026-07-17 | Status: 🧊 IMMUTABLE
>
> The implementation roadmap is locked from this date.
> No sprint scope, order, or dependency may change without approved ADR.
> All future execution follows this roadmap.

---

## 1. Lock Declaration

Effective 2026-07-17, the following roadmap documents are locked:

| Document | Reference | Status |
|----------|-----------|--------|
| `docs/vnext/IMPLEMENTATION_PLAN.md` | 22-sprint execution plan | 🧊 Locked |
| `docs/vnext/FEATURE_ROADMAP.md` | Feature prioritization | 🧊 Locked |
| `docs/vnext/work-orders/WO-*` (25 files) | Per-sprint work orders | 🧊 Locked |
| `engineering-os/IMPLEMENTATION_ROADMAP.md` | Original roadmap | 🧊 Superseded |
| This document (`ROADMAP_LOCK.md`) | Locked roadmap | 🧊 Locked |

---

## 2. Sprint Structure (Locked)

```
Phase 0: Architecture Reconciliation (COMPLETE)
├── Sprint 0: Architecture Reconciliation ✅ (2026-07-17)
└── Sprint 0.5: Platform Freeze ✅ (2026-07-17)

Phase 0: Platform Stabilization (Sprints 1-2)
├── Sprint 1: Security & Critical Fixes
└── Sprint 2: Infrastructure & Performance

Phase 1: Design System V2 (Sprints 3-4)
├── Sprint 3: Design System Consolidation
│   ├── Widget SDK consolidation (ADR-0032 mandate)
│   └── Form components, Badge fix, CSS standardization
└── Sprint 4: Design System Expansion
    └── Storybook, a11y tests, visual regression

Phase 2: Foundation Features (Sprints 5-6)
├── Sprint 5: Settings & Dashboard
└── Sprint 6: Search & Companies

Phase 3: Intelligence Features (Sprints 7-8)
├── Sprint 7: Company 360 & Employee 360
├── Sprint 8: Knowledge Graph & Signals

Phase 4: Revenue & Pipeline (Sprints 9-10)
├── Sprint 9: Pipeline & CRM
└── Sprint 10: Revenue & Forecast

Phase 5: AI Platform (Sprints 11-12)
├── Sprint 11: Agent Runtime
│   ├── Decision Engine implementation (ADR-0033 mandate)
│   ├── Kafka activation
│   └── Workflow domain compliance
└── Sprint 12: AI Evaluation & Feedback

Phase 6: Enterprise & Scale (Sprints 13-22)
├── Sprint 13-14: Admin Portal & Multi-Tenancy
├── Sprint 15-16: Data Fabric & Connectors
├── Sprint 17-18: Notifications & Real-time
├── Sprint 19-20: Arabic/RTL, Accessibility
└── Sprint 21-22: Performance, Hardening, GA
```

---

## 3. Hard Prerequisites (Cannot Be Skipped)

| Prerequisite | Blocks | Reason |
|-------------|--------|--------|
| Widget SDK consolidation (TD-S0-01) | Sprint 3+ widget work | ADR-003 violation — dual SDKs |
| `main.py` split (TD-S0-02) | Sprint 2+ clarity | 908-line monolithic startup |
| `api.ts` split (TD-S0-03) | Sprint 5+ frontend work | 1,734-line monolithic API client |
| `init_db()` → Alembic (TD-S0-05) | Sprint 2+ schema changes | Migration drift risk |
| Identity repo refactor (TD-S0-04) | Identity domain extensions | Repository pattern violation |
| Decision Engine implementation (TD-S0-07) | Scoring domain compliance | Frontend stub blocks scoring |
| InMemory DecisionCenter → PG (TD-S0-06) | Decision Center features | Production data loss risk |

---

## 4. Sprint Assignments (Locked)

| Sprint | Primary Focus | TD Items | Critical Path |
|--------|--------------|----------|---------------|
| S1 | Security + Critical | TD-S0-02, TD-S0-05, TD-S0-06 | main.py split, Alembic, DecisionCenter PG |
| S2 | Infrastructure + Perf | TD-S0-03, TD-S0-04, TD-S0-08, TD-S0-09 | api.ts split, Identity repos, middleware fix |
| S3 | Design V2 | TD-S0-01 (MANDATORY) | Widget SDK consolidation |
| S4 | Design V2 | — | Storybook, a11y |
| S5 | Settings + Dashboard | — | Feature work |
| S6 | Search + Companies | — | Feature work |
| S7 | Company 360 | VIO-102 (Timeline refactor) | Timeline compliance |
| S8 | Knowledge Graph | — | Feature work |
| S9 | Pipeline + CRM | — | Feature work |
| S10 | Revenue + Forecast | — | Feature work |
| S11 | Agent Runtime | VIO-101 (Workflow), TD-S0-07 (Decision Engine) | Workflow compliance + Decision Engine |
| S12 | AI Evaluation | VIO-104 (AI framework) | AI compliance |
| S13-22 | Enterprise + Scale | TD-002 (Kafka), TD-005 (Auth review) | Phased enterprise delivery |

---

## 5. Compliance Recovery Path

| Sprint | Compliance Target | Cumulative Gain | Key Action |
|--------|-------------------|-----------------|------------|
| Baseline (S0.5) | 85% | — | Measured baseline established |
| S1 | 86% | +1% | DecisionCenter PG, main.py split |
| S2 | 88% | +3% | Identity repos, api.ts split |
| S3 | 92% | +7% | Widget SDK consolidation (BIGGEST GAP) |
| S4 | 92% | +7% | Design system alignment |
| S5 | 93% | +8% | Settings + Dashboard |
| S6 | 93% | +8% | Search improvements |
| S7 | 94% | +9% | Timeline refactor |
| S8 | 94% | +9% | Knowledge Graph |
| S9 | 94% | +9% | Pipeline + CRM |
| S10 | 94% | +9% | Revenue + Forecast |
| S11 | 95% | +10% | Workflow + Decision Engine |
| S12 | 95% | +10% | AI evaluation |
| S13+ | 95% | Maintain | Enterprise hardening |

---

## 6. Scope Lock Rules

1. **Sprint scope** is defined by the work order (`docs/vnext/work-orders/WO-*`)
2. **No sprint may add scope** beyond its work order without ADR
3. **No sprint may skip** its assigned technical debt items
4. **No sprint may reorder** dependencies without Architecture Review Board approval
5. **Sprint swaps** (exchanging work between sprints) require CTO approval
6. **New features** outside the locked roadmap require a new ADR + work order

---

## 7. Phase Gates (Hard Locks)

| Gate | Phase | Criteria | Bypass |
|------|-------|----------|--------|
| G0 | Pre-S1 | Platform Baseline approved | No bypass |
| G0.5 | Pre-S1 | Roadmap Lock approved | No bypass |
| G1 | Post-S2 | Compliance ≥ 88%, all S1-S2 TD items resolved | CTO override only |
| G2 | Post-S4 | Compliance ≥ 92%, Widget SDK consolidated | No bypass |
| G3 | Post-S6 | Compliance ≥ 93%, pagination on all endpoints | CTO override |
| G4 | Post-S8 | Compliance ≥ 94%, Timeline refactored | CTO override |
| G5 | Post-S10 | Compliance ≥ 94%, Revenue pipeline complete | Architecture Review Board |
| G6 | Post-S12 | Compliance ≥ 95%, ALL TD items resolved | No bypass — GA readiness |
| G7 | Post-S22 | All gates passed, production deploy | No bypass |

---

## 8. Change Requests

Any proposed change to this locked roadmap must follow the ADR process:

1. **ADR** documenting the proposed change and justification
2. **Impact analysis** on all 7 gates
3. **Architecture Review Board** approval (2/3 majority)
4. **CTO** sign-off
5. **Roadmap update** with change record in this document's appendix

---

## Appendix A: Roadmap Change Log

| Date | Change | ADR | Approver |
|------|--------|-----|----------|
| 2026-07-17 | Initial roadmap lock | ADR-0035 | Architecture Review Board |

## Appendix B: Work Order Index

| Work Order | Sprint | Focus | Effort |
|------------|--------|-------|--------|
| WO-001 | S1 | Security — Wave A | Security fixes |
| WO-002 | S2 | Performance — Wave B | N+1, pagination, caching |
| WO-003 | S11 | AI — Wave C | Agent Runtime |
| WO-004 | S3-4 | Frontend — Wave D | Design System V2 |
| WO-005 | S12 | QA — Wave E | AI evaluation |
| WO-101 | S3 | Core Components | Form components |
| WO-102 | S3 | UI Infrastructure | Layout consolidation |
| WO-103 | S4 | Quality + Publishing | Storybook, a11y, visual regression |
| WO-201 | S5 | Dashboard | Settings + Dashboard |
| WO-301 | S6 | Companies | Company list + search |
| WO-401 | S7 | Company 360 | Company workspace |
| WO-501 | S5 | Employees | Employee list |
| WO-601 | S7 | Employee 360 | Employee workspace |
| WO-701 | S9 | Pipeline | Pipeline + CRM |
| WO-801 | S10 | Revenue | Revenue + Forecast |
| WO-901 | S9 | Decision Center | Decision Center UI |
| WO-1001 | S6 | Search | Cross-domain search |
| WO-1101 | S11 | Copilot | AI Copilot |
| WO-1201 | S8 | Knowledge | Knowledge Graph |
| WO-1301 | S13 | Automation | Workflow automation |
| WO-1401 | S14 | Analytics | Analytics |
| WO-1501 | S15 | Marketplace | Marketplace |
| WO-1601 | S16 | Admin | Admin Portal |
| WO-1701 | S22 | Hardening | Production hardening |
