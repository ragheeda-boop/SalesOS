# SalesOS vNext — Master Planning

> **Audit-to-Plan Transformation**
> Generated: 2026-07-16
> Source: [Engineering Discovery Audit](../audit/current-state/README.md)
> Status: Planning Phase — Ready for Implementation

---

## Navigation

This directory contains the complete implementation blueprint for SalesOS vNext. Every document is derived from the engineering audit findings in [`docs/audit/current-state/`](../audit/current-state/).

---

## Documents

| # | Document | Purpose | Read First |
|---|----------|---------|------------|
| 1 | **[MASTER_PLAN.md](./MASTER_PLAN.md)** | Executive overview: current status, target vision, top priorities, success criteria | ✅ **Start here** |
| 2 | **[ROADMAP.md](./ROADMAP.md)** | High-level phasing: 11 phases across 22 sprints (~44 weeks) | ✅ After Master Plan |
| 3 | **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** | Detailed implementation plan with tasks per phase | Next |
| 4 | **[ARCHITECTURE_VNEXT.md](./ARCHITECTURE_VNEXT.md)** | Target architecture: frontend, backend, runtimes, modules, data flow, API contracts | Architects |
| 5 | **[FEATURE_ROADMAP.md](./FEATURE_ROADMAP.md)** | Per-feature detail: current status, required work, DOD for 30 feature areas | Product |
| 6 | **[DESIGN_STRATEGY.md](./DESIGN_STRATEGY.md)** | Design system V2, UI consistency, accessibility, component gaps | Design |
| 7 | **[AI_STRATEGY.md](./AI_STRATEGY.md)** | AI platform evolution: multi-agent, multi-provider, evaluation, testing | AI |
| 8 | **[ENGINEERING_STRATEGY.md](./ENGINEERING_STRATEGY.md)** | Branch strategy, CI/CD, quality gates, code review, testing strategy | Engineering |
| 9 | **[TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md)** | 68 ranked debt items with recommendations and effort estimates | All |
| 10 | **[SPRINT_PLAN.md](./SPRINT_PLAN.md)** | 18 implementation phases with deliverables, dependencies, risks | Project Mgmt |
| 11 | **[BACKLOG.md](./BACKLOG.md)** | 104 engineering backlog items across 11 categories | Engineering |
| 12 | **[RISKS.md](./RISKS.md)** | 41 risks catalogued with mitigation plans | All |
| 13 | **[DECISIONS.md](./DECISIONS.md)** | 15 architecture decisions to be made with options and recommendations | Architects |

---

## How to Use This Roadmap

### For Executives
1. Read **[MASTER_PLAN.md](./MASTER_PLAN.md)** for the big picture
2. Read **[ROADMAP.md](./ROADMAP.md)** for the timeline
3. Read **[RISKS.md](./RISKS.md)** for key risks

### For Product Managers
1. Read **[FEATURE_ROADMAP.md](./FEATURE_ROADMAP.md)** for feature priorities
2. Read **[SPRINT_PLAN.md](./SPRINT_PLAN.md)** for sprint scheduling
3. Read **[MASTER_PLAN.md](./MASTER_PLAN.md)** for success criteria

### For Architects
1. Read **[ARCHITECTURE_VNEXT.md](./ARCHITECTURE_VNEXT.md)** for target architecture
2. Read **[DECISIONS.md](./DECISIONS.md)** for pending decisions
3. Read **[TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md)** for debt to resolve

### For Engineers
1. Read **[ENGINEERING_STRATEGY.md](./ENGINEERING_STRATEGY.md)** for process
2. Read **[BACKLOG.md](./BACKLOG.md)** for work items
3. Read **[SPRINT_PLAN.md](./SPRINT_PLAN.md)** for current phase

### For Designers
1. Read **[DESIGN_STRATEGY.md](./DESIGN_STRATEGY.md)** for design system evolution
2. Read **[FEATURE_ROADMAP.md](./FEATURE_ROADMAP.md)** for feature context

### For AI Engineers
1. Read **[AI_STRATEGY.md](./AI_STRATEGY.md)** for AI platform evolution
2. Read **[DECISIONS.md](./DECISIONS.md)** for AI-related decisions

---

## File Inventory

```
docs/vnext/
├── README.md                  (This file)
├── MASTER_PLAN.md             (Executive overview)
├── ROADMAP.md                 (Phased timeline)
├── IMPLEMENTATION_PLAN.md     (Detailed tasks)
├── ARCHITECTURE_VNEXT.md      (Target architecture)
├── FEATURE_ROADMAP.md         (Feature-level detail)
├── DESIGN_STRATEGY.md         (Design system evolution)
├── AI_STRATEGY.md             (AI platform evolution)
├── ENGINEERING_STRATEGY.md    (Engineering process)
├── TECHNICAL_DEBT.md          (Debt register)
├── SPRINT_PLAN.md             (Sprint-by-sprint)
├── BACKLOG.md                 (Engineering backlog)
├── RISKS.md                   (Risk register)
└── DECISIONS.md               (Architecture decisions)
```

---

## Related Documents

- [Engineering Discovery Audit](../audit/current-state/README.md) — The source data for this plan
- [Engineering Constitution](../../engineering-os/ENGINEERING_CONSTITUTION.md) — Non-negotiable rules
- [Engineering Dashboard](../../engineering-os/ENGINEERING_DASHBOARD.md) — Current metrics

---

*This is a living document. Update as decisions are made and implementation progresses.*
