# Milestones

> **Canonical source** for program milestones. Referenced from `IMPLEMENTATION_SEQUENCE.md` §7 (which derives these from the build-order positions) and `RELEASE_PLAN.md` (which defines what each gate means for feature scope/target users). Dates are planning targets tied to the 26-sprint cadence in `ENGINEERING_ROADMAP.md` — if a phase slips, update the date here and note the reason, don't silently let this file drift out of sync with reality.

| ID | Milestone | Target date | Sprint | Maps to | Owner (Accountable) | Status |
|---|---|---|---|---|---|---|
| **M1** | Foundation Secure | 2026-09-13 | End of Sprint 03 | Phase 0 exit — all 3 security P0s closed, RLS live on 100% of tenant-scoped tables, green CI | Chief Architect | Pending |
| **M2** | First Commercial Transaction | 2026-11-08 | End of Sprint 07 | **Alpha** release — full provision→subscribe→gate→downgrade cycle working end-to-end, internal-only | Program Director | Pending |
| **M3** | First Real Tenant Data | 2027-01-03 | End of Sprint 11 | **Private Alpha** release — Odoo adapter GA, Muhide's real data live in production, 14-day soak begins | Backend Lead | Pending |
| **M4** | Self-Service Configuration Live | 2027-02-28 | End of Sprint 15 | **Internal Beta** release — Tenant Studio Core (Custom Objects/Fields, Workflow Builder, Scoring, Territories, Permissions, Branding) dogfooded internally | Chief Architect | Pending |
| **M5** | Framework Genericity Proven | 2027-04-25 | End of Sprint 19 | **Partner Beta** release — second connector certified by an engineer other than `OdooAdapter`'s author; directly closes R-02. **The single most important milestone in the plan.** | Chief Architect | Pending |
| **M6** | Ecosystem Proven | 2027-06-06 | End of Sprint 22 | **Public Beta** release — Marketplace live with ≥3 connector + ≥1 playbook listings, AI Studio tenant-facing | CPO | Pending |
| **M7** | Production-Grade Confidence | 2027-07-18 | End of Sprint 25 | **Release Candidate** declared — load/chaos/pentest/DR drills complete, feature freeze, 2-week soak begins | Release Manager | Pending |
| **M8** | General Availability | 2027-08-02 | End of Sprint 26 | **GA** declared — terminal milestone, all 9 `MASTER_EXECUTION_PLAN.md` §9 exit criteria satisfied simultaneously | Full leadership group (joint: CPO, CTO, Chief Architect, Program Director, Release Manager) | Pending |

---

## How to Update This File

1. When a milestone's gate review (per `IMPLEMENTATION_SEQUENCE.md` §10 Decision Gates) actually occurs, change its **Status** to `Achieved` (with the actual date noted in parentheses next to the target date) or `Slipped` (with a new target date and a one-line reason — never silently move a date with no reason recorded, per `MASTER_EXECUTION_PLAN.md` §9's "no silent slippage" rule).
2. If a milestone slips, check whether it sits on the critical path (`IMPLEMENTATION_SEQUENCE.md` §2) — a critical-path slip pushes every milestone after it by the same amount; a non-critical-path slip (rare, since almost everything here is sequential) may not.
3. Any newly identified milestone (e.g., a customer-driven commitment date) gets appended as `M9`, `M10`, etc. — never inserted into the middle of the existing numbering, since `IMPLEMENTATION_SEQUENCE.md` and sprint files reference these IDs directly.

## Milestone Dependencies (at a glance)

```
M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8
```

Strictly linear — there is no milestone in this plan that can be reached out of order, because each one is gated on the phase before it (`PRODUCT_ROADMAP.md` Go/No-Go criteria) and the critical path (`IMPLEMENTATION_SEQUENCE.md` §2) runs through all of them. This is a deliberate design choice, not an oversight: a program claiming to sell a multi-tenant SaaS platform commercially does not get to declare Public Beta (M6) before Framework Genericity (M5) is proven, no matter how much schedule pressure exists.
