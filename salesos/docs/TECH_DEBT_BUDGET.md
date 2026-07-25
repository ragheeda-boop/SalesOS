# SalesOS — Technical Debt Budget

> **Sprint 0.5 Deliverable: Platform Freeze**
> Date: 2026-07-17 | Status: 🧊 IMMUTABLE (baseline)
>
> Budget allocation for technical debt repayment across all sprints.
> Each sprint must allocate capacity to debt repayment before feature work.

---

## 1. Budget Policy

1. **Every sprint** must allocate minimum 20% capacity to technical debt repayment
2. **Critical debt** must be resolved within 1 sprint of identification
3. **High debt** must be resolved within 2 sprints of identification
4. **Medium debt** must be resolved within 4 sprints of identification
5. **No new technical debt** may be created without registering it in `memory/technical-debt.md`
6. **Debt budget** may be increased but never decreased without CTO approval

---

## 2. Debt Inventory at Freeze

| ID | Area | Severity | Effort | Sprint | Owner |
|----|------|----------|--------|--------|-------|
| TD-S0-01 | Widget SDK — Dual SDKs | **Critical** | 3-4d | S3 | Frontend Architect |
| TD-S0-02 | Backend — main.py (908 lines) | High | 1-2d | S1 | Backend Engineer |
| TD-S0-03 | Frontend — api.ts (1,734 lines) | High | 2-3d | S2 | Frontend Engineer |
| TD-S0-04 | Identity — repo bypass | High | 1d | S2 | Backend Engineer |
| TD-S0-05 | Database — init_db() bypasses Alembic | High | 2d | S1 | Database Engineer |
| TD-S0-06 | Decision Center — InMemory repo | High | 2d | S1 | Backend Engineer |
| TD-002 | Infrastructure — Event bus → Kafka | Medium | 2 sprints | S11 | Architecture |
| TD-S0-07 | Decision Engine — stub | Medium | 3-5d or doc | S11 | AI Engineer |
| TD-S0-08 | Middleware — body consumption bug | Medium | 1d | S2 | Backend Engineer |
| TD-S0-10 | Compliance — score accuracy | Medium | Ongoing | All | Architecture |
| TD-005 | Security — auth review | Medium | 1 sprint | S2 | Security Reviewer |
| TD-S0-09 | Cleanup — empty directories | Low | 0.25d | S2 | Any |

---

## 3. Per-Sprint Budget Allocation

### Phase 0: Platform Stabilization

| Sprint | Debt Capacity | Allocated To | Effort | % of Sprint |
|--------|--------------|-------------|--------|-------------|
| **S1** | 5-6 days | TD-S0-02 (main.py split) = 2d | 5-6d | ~40% |
| | | TD-S0-05 (Alembic baseline) = 2d | | |
| | | TD-S0-06 (DecisionCenter PG) = 2d | | |
| **S2** | 5-6 days | TD-S0-03 (api.ts split) = 3d | 5-6d | ~40% |
| | | TD-S0-04 (Identity repos) = 1d | | |
| | | TD-S0-08 (Middleware bug) = 1d | | |
| | | TD-005 (Auth review) = 1d | | |
| | | TD-S0-09 (Cleanup) = 0.25d | | |

### Phase 1: Design System V2

| Sprint | Debt Capacity | Allocated To | Effort | % of Sprint |
|--------|--------------|-------------|--------|-------------|
| **S3** | 4-5 days | TD-S0-01 (Widget SDK merge) = 4d | 4d | ~35% |
| **S4** | — | Design work only | 0 | 0% |

### Phase 2-4: Foundation + Intelligence + Revenue

| Sprint | Debt Capacity | Allocated To | Effort | % of Sprint |
|--------|--------------|-------------|--------|-------------|
| **S7** | 3d | VIO-102 (Timeline refactor) | 3d | ~20% |
| **S11** | 5-7d | VIO-101 (Workflow) + TD-S0-07 (Decision Engine) + TD-002 (Kafka) | 5-7d | ~40% |
| **S12** | 3d | VIO-104 (AI evaluation) | 3d | ~20% |

### Phase 6: Enterprise (Sprints 13-22)

| Sprint | Debt Capacity | Notes |
|--------|--------------|-------|
| S13-22 | 20% per sprint | Remaining medium/low items; any new debt discovered |

---

## 4. Budget Tracking

| Sprint | Debt Budget | Actual Spent | Remaining | Items Resolved | Items Added | Net Change |
|--------|-------------|--------------|-----------|----------------|-------------|------------|
| Baseline | — | — | 12 active | — | — | — |
| S1 | 6d | | | | | |
| S2 | 6d | | | | | |
| S3 | 4d | | | | | |
| S4 | 0d | | | | | |
| S5 | 0d | | | | | |
| S6 | 0d | | | | | |
| S7 | 3d | | | | | |
| S8 | 0d | | | | | |
| S9 | 0d | | | | | |
| S10 | 0d | | | | | |
| S11 | 7d | | | | | |
| S12 | 3d | | | | | |
| S13+ | 20% | | | | | |

*Table populated at end of each sprint.*

---

## 5. Debt Repayment Trajectory

```
Active TD Items
12 | ████████████  Baseline (Sprint 0.5)
   |
10 |                  ██████████  Target: S1 (main.py, Alembic, DecisionCenter)
   |
 8 |                               ████████  Target: S2 (api.ts, Identity, middleware)
   |
 6 |                                           ██████  Target: S3 (Widget SDK merge)
   |
 4 |
   |                                                        ████  Target: S11 (Workflow, Kafka, Decision Engine)
 2 |
   |                                                                          ██  Target: S12 (AI evaluation)
 0 |________________________________________________________________________________
   S0.5  S1    S2    S3    S4    S5    S6    S7    S8    S9    S10   S11   S12
```

---

## 6. Budget Violations

| Violation | Consequence |
|-----------|-------------|
| Debt not resolved within SLA | Automatically promoted to next sprint with 2x allocation |
| New critical debt added | Sprint halted until resolved |
| Sprint debt allocation skipped | CTO review required |
| Debt repayment < 20% for 2 consecutive sprints | Architecture Review Board audit |
| Unregistered debt discovered in code review | PR blocked + debt registered |

---

## 7. Budget Review

The debt budget is reviewed:
- **Per sprint**: During sprint retrospective
- **Per release**: During release readiness review
- **Quarterly**: Full debt audit by Architecture Review Board

---

## Appendix A: Debt Severity Classification

| Severity | Definition | Resolution SLA | Budget Allocation |
|----------|-----------|---------------|-------------------|
| 🔴 Critical | Violates frozen interface, causes data loss, blocks security | 0 sprints (immediate) | Unlimited |
| 🟡 High | Violates mandatory pattern, blocks feature work, causes significant maintenance burden | 2 sprints | 1-3 days |
| 🟡 Medium | Code smell, partial compliance, minor violation, technical inconvenience | 4 sprints | 0.5-1 day |
| 🟢 Low | Cleanup, documentation gap, unused code, cosmetic | Scheduled maintenance | < 0.5 day |

## Appendix B: Zero-Debt Domains

These domains have zero active technical debt and are frozen:

| Domain | Last Verified | Maintainer |
|--------|---------------|------------|
| Identity | 2026-07-17 | Backend Engineer |
| Company | 2026-07-17 | Backend Engineer |

*Note: Identity has TD-S0-04 registered against it. The domain data model is zero-debt; the service layer violation is tracked separately.*
