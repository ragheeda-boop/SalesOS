# Sprint 22 — 2027-05-24 → 2027-06-06

> **Phase:** 5 — AI Studio + Marketplace · **Prior:** [Sprint 21](Sprint-21.md) · **Next:** [Sprint 23](Sprint-23.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Public Beta (open signup, waitlisted) — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §5

**Sprint Goal:** Marketplace UI live with real listings. **Public Beta gate.**

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-13-03 (Marketplace browse/install UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B FE-S13-03):** `/marketplace/listings` browse + tip submit/certify vs STORY-13-02 HTTP. No invented tenant `/install`. CAP-036 stub remains at `/marketplace` with honesty link. Crumb [`PHASE1_FE_S13_03_MARKETPLACE_CERTIFY_UX_CRUMB.md`](../PHASE1_FE_S13_03_MARKETPLACE_CERTIFY_UX_CRUMB.md). Not Production GO. |
| STORY-13-04 (publish 3 connectors + 1 playbook) | BE2, Program Director | P0 | Medium | All 4 listings certified and installable |
| Certification pipeline negative test | Security | P0 | Medium | Intentionally broken listing correctly rejected |

**Expected Demo:** **Phase 5 Go/No-Go + Public Beta release** (open signup with waitlist). Install a connector from Marketplace end-to-end as a brand-new self-service tenant.

**Technical Debt Created:** Third-party listing submission form not built — explicitly post-GA scope per `PROGRAM_PLAN.md` EPIC-13.
