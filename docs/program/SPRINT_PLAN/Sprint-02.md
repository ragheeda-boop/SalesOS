# Sprint 02 — 2026-08-17 → 2026-08-30

> **Phase:** 0 — Foundation & Security Hardening · **Prior:** [Sprint 01](Sprint-01.md) · **Next:** [Sprint 03](Sprint-03.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Close the remaining P0, establish the regression-test template every future epic reuses.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-01-03 (CSRF bypass) | BE1 | P0 | High | `X-API-Key` no longer bypasses CSRF check; regression test added |
| STORY-01-04 (cross-tenant regression template) | BE-Lead | P0 | High (R-01) | Reusable test harness merged; documented in `TEST_STRATEGY.md` |
| STORY-03-03 (coverage gate) | QA-Lead* | P1 | Medium | CI blocks PRs with new-code coverage below threshold |
| STORY-02-01 (RLS design, start) | BE-Lead | P1 | High | RLS policy generation script drafted against 10 pilot tables |

*QA-Lead not yet hired — BE1 covers as stopgap.

**Expected Demo:** Show the cross-tenant regression template catching a deliberately-reintroduced version of the Sprint 1 IDOR bug.

**Technical Debt Created:** RLS policy generation script is hand-tested against 10 tables only — remaining 62 tables are Sprint 3 scope, tracked explicitly, not silently deferred.

---

## Closure Status: ✅ CLOSED (verified 2026-07-31)

STORY-01-03 arrived already satisfied (completed ahead of schedule during Sprint 01's actual execution). All 4 stories independently verified, plus one live, unrelated cross-tenant IDOR discovered and fixed under the small-fix carve-out (see risk register R-15). **Critical finding: R-14** — the application's DB role is a Postgres superuser with BYPASSRLS, meaning Sprint 03's RLS rollout cannot achieve real enforcement until this is fixed first; this is now the #1 tracked risk in the program. Full detail: [`SPRINT_02_REPORT.md`](../../../salesos/docs/audit/ga-engineering-audit/SPRINT_02_REPORT.md). Risk statuses: `docs/program/RISK_REGISTER.md`.
