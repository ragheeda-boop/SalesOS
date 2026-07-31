# Sprint 01 — 2026-08-03 → 2026-08-16

> **Phase:** 0 — Foundation & Security Hardening · **Next:** [Sprint 02](Sprint-02.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Stop the bleeding — reproduce and fix the 2 highest-severity P0s, get CI green.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-01-01 (Decision Center IDOR) | BE-Lead | P0 | High (R-01) | Failing repro test written first; fix merged; test now passes; independent review by BE1 |
| STORY-01-02 (Webhook SSRF) | BE1 | P0 | High (C2) | URL allowlist implemented; regression test hits internal IP ranges and is blocked |
| STORY-03-01 (Frontend build fix) | FE-Lead | P0 | High (R-08) | CI frontend job green 3 consecutive runs |
| STORY-03-02 (Alembic catch-up, start) | BE2* | P1 | High (R-09) | Migration diff generated against current models, reviewed, not yet applied to prod |

*BE2 not yet hired — Program Director or BE-Lead covers this task in Sprint 1 as a stopgap.

**Expected Demo:** Reproduce the IDOR bug live (pre-fix), show the fix blocking it; show a green CI pipeline for the first time in the project's recent history.

**Technical Debt Created:** None intentional — this sprint pays debt down, it doesn't create it. **Technical Debt Identified (not yet paid):** SSRF fix is allowlist-based; a future hardening pass should add outbound-request signing for defense in depth (logged as backlog item, not this sprint's scope).

---

## Closure Status: ✅ CLOSED (verified 2026-07-30)

All 4 stories above independently verified across three review passes, including one mid-sprint defect found and fixed (`R-12`, an unrelated execution-ID collision bug surfaced by the `testpaths` fix that came out of this sprint's own work). Full detail: [`SPRINT_01_CLOSURE_REPORT.md`](../../../salesos/docs/audit/ga-engineering-audit/SPRINT_01_CLOSURE_REPORT.md). Carried forward into Sprint 02, not blocking it: an owner decision on 6 pre-existing/unrelated test failures + R-13 (environment parity), and provisioning the `salesos_test` database (also unblocks STORY-01-01's Postgres-layer test coverage). Risk statuses: `docs/program/RISK_REGISTER.md`.
