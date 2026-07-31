# Engineering Roadmap — Index

> **Full per-sprint detail lives in** [`SPRINT_PLAN/`](SPRINT_PLAN/Sprint-01.md) — one file per sprint (`Sprint-01.md` through `Sprint-26.md`), each self-contained with Sprint Goal, Stories, Owner, Priority, Risk, Acceptance Criteria, Expected Demo, and Technical Debt Created.
> This file is the map: cadence, team roster, priority/risk conventions, and the phase→sprint index. Start at [Sprint-01.md](SPRINT_PLAN/Sprint-01.md) and follow the Prior/Next links, or jump directly via the table below.

---

## Cadence & Conventions

- **Cadence:** 2-week sprints, 26 sprints total, Sprint 01 starts 2026-08-03, Sprint 26 closes 2027-08-02.
- **Priority scale:** P0 (blocks the sprint goal), P1 (required for phase exit), P2 (fits if capacity allows, slips without re-planning if not).
- **Risk scale:** Low / Medium / High, referencing `RISK_REGISTER.md` risk IDs (R-01…R-10) where applicable.
- **Story ID scheme:** `STORY-{EPIC}-{NN}`, cross-referenced to `PROGRAM_PLAN.md`'s epics (EPIC-01…14).

## Team Roster (growth curve per `MASTER_EXECUTION_PLAN.md` A1)

| Role | Joins | Notes |
|---|---|---|
| BE-Lead, FE-Lead, Program Director | Sprint 01 (baseline) | Core team at kickoff |
| BE1, FE1 | Sprint 01 (baseline) | Core team at kickoff |
| Security (part-time) | Sprint 01 (baseline) | Full-time from Sprint 08 |
| DevOps/SRE, QA-Lead | Sprint 03 | First growth wave, ahead of Phase 1 |
| BE2 | Sprint 05 | Ahead of Billing/Entitlement work |
| AI-Lead | Sprint 07 | Ahead of Odoo InteractionNote/PII work in Sprint 11 |
| BE3, FE2 | Sprint 09 | Ahead of Odoo adapter build-out |
| Release Manager | Sprint 20 | Ahead of RC/GA gates |

## Phase → Sprint Index

| Phase | Sprints | Gate at exit | Files |
|---|---|---|---|
| 0 — Foundation & Security Hardening | 01-03 | Phase 0 Go/No-Go | [01](SPRINT_PLAN/Sprint-01.md) · [02](SPRINT_PLAN/Sprint-02.md) · [03](SPRINT_PLAN/Sprint-03.md) |
| 1 — Owner Platform Core | 04-07 | **Alpha** | [04](SPRINT_PLAN/Sprint-04.md) · [05](SPRINT_PLAN/Sprint-05.md) · [06](SPRINT_PLAN/Sprint-06.md) · [07](SPRINT_PLAN/Sprint-07.md) |
| 2 — Integration Hub + Odoo GA | 08-11 | **Private Alpha** | [08](SPRINT_PLAN/Sprint-08.md) · [09](SPRINT_PLAN/Sprint-09.md) · [10](SPRINT_PLAN/Sprint-10.md) · [11](SPRINT_PLAN/Sprint-11.md) |
| 3 — Tenant Studio Core | 12-15 | **Internal Beta** | [12](SPRINT_PLAN/Sprint-12.md) · [13](SPRINT_PLAN/Sprint-13.md) · [14](SPRINT_PLAN/Sprint-14.md) · [15](SPRINT_PLAN/Sprint-15.md) |
| 4 — GTM Intelligence Nativization | 16-19 | **Partner Beta** | [16](SPRINT_PLAN/Sprint-16.md) · [17](SPRINT_PLAN/Sprint-17.md) · [18](SPRINT_PLAN/Sprint-18.md) · [19](SPRINT_PLAN/Sprint-19.md) |
| 5 — AI Studio + Marketplace | 20-22 | **Public Beta** | [20](SPRINT_PLAN/Sprint-20.md) · [21](SPRINT_PLAN/Sprint-21.md) · [22](SPRINT_PLAN/Sprint-22.md) |
| 6 — Hardening, Scale, Compliance | 23-25 | **Release Candidate** | [23](SPRINT_PLAN/Sprint-23.md) · [24](SPRINT_PLAN/Sprint-24.md) · [25](SPRINT_PLAN/Sprint-25.md) |
| 7 — GA Launch | 26 | **General Availability** (terminal) | [26](SPRINT_PLAN/Sprint-26.md) |

## Reads With

`PRODUCT_ROADMAP.md` (phase-level objectives this sprint index implements), `PROGRAM_PLAN.md` (epic/story detail behind each sprint's story IDs), `RELEASE_PLAN.md` (what each gate listed above actually means for feature scope and target users), `RISK_REGISTER.md` (risk IDs referenced per-story), `MILESTONES.md` (the M1-M8 milestones mapped onto this same sprint sequence).
