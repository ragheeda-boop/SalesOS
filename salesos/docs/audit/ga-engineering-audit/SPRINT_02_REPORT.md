# Sprint 02 Report

**Date:** 2026-07-31
**Sprint:** 02 (Phase 0 — Foundation & Security Hardening)
**Role:** Lead Implementation Engineer (Sprint Execution Contract)
**Sprint contract document:** `docs/program/SPRINT_PLAN/Sprint-02.md`
**Program references:** `docs/program/RISK_REGISTER.md`, `docs/program/TEST_STRATEGY.md`, `docs/program/PRODUCT_ROADMAP.md` (Phase 0 exit criteria)

---

## Sprint Summary

Sprint 02's four originally-assigned stories are done: one (STORY-01-03, CSRF) arrived already satisfied, completed ahead of schedule during Sprint 01's actual execution — verified, not re-implemented. The remaining three (STORY-01-04, STORY-03-03, STORY-02-01) were implemented, tested against a real local Postgres/Docker stack (not mocked), and each surfaced at least one real, non-cosmetic finding worth reporting rather than glossing over:

- Building the reusable cross-tenant harness (STORY-01-04) required picking a real demonstration target, which led to discovering and fixing a **live, exploitable cross-tenant IDOR** in `app/routers/meetings.py` — unrelated to any assigned story, fixed under the Sprint Execution Contract's small-fix carve-out rather than left open.
- Hand-testing the RLS policy generator (STORY-02-01) against a throwaway non-superuser role revealed that **the application's actual database role is a Postgres superuser with BYPASSRLS** — meaning Sprint 03's planned RLS rollout cannot achieve real enforcement until the application's DB connection role changes first. This is now the single highest-scored risk in the program (R-14, score 25).
- Building the diff-coverage gate (STORY-03-03) and testing it against real historical commit history (not just synthetic examples) caught two real bugs in the tool itself before it ever reached CI: a Windows subprocess encoding crash against this Arabic-first codebase's actual content, and a path-relativity mismatch between `git diff` and `coverage.xml`.

**Scope boundary, stated plainly:** the working tree currently contains a large number of modified frontend files (`salesos/frontend/src/app/(dashboard)/**/page.tsx` and others) that this Sprint 02 session did not create or touch. This report covers only the backend files listed below. The frontend changes are not evaluated, tested, or claimed here — they appear to be other, concurrent work in the same repository, and their state should be confirmed with whoever is responsible for them before assuming they're part of any Sprint 02 deliverable.

---

## Stories Completed

| Story | Status | Notes |
|---|---|---|
| STORY-01-03 (CSRF bypass) | ✅ Already satisfied | Completed in Sprint 01's actual execution, ahead of the original plan. Re-verified this session (`tests/unit/test_middleware.py::TestCsrfMiddleware`, 8/8 pass) — not re-implemented. |
| STORY-01-04 (cross-tenant regression template) | ✅ Done | `tests/support/tenant_isolation.py` — reusable, documented in `TEST_STRATEGY.md` §11.1, 2 real consumers, demo performed and evidenced. |
| STORY-03-03 (coverage gate) | ✅ Done | `scripts/check_diff_coverage.py`, wired into `.github/workflows/ci.yml`, 19 unit tests, hand-verified against real history. |
| STORY-02-01 (RLS design, start) | ✅ Done | `scripts/generate_rls_policies.py`, 10 pilot tables, hand-tested against real Postgres via `tests/integration/test_rls_policy_generation.py`. Surfaced R-14 (critical). |

Plus, out-of-scope but disclosed: **R-15** (meetings.py cross-tenant IDOR), discovered and fixed under the small-fix carve-out.

---

## Files Changed

**Sprint 02 scope only** (this session's work — see Scope Boundary above for what this excludes):

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | STORY-03-03: added diff-coverage gate step to `test-backend` job; `fetch-depth: 0` on checkout |
| `salesos/backend/scripts/check_diff_coverage.py` | New — STORY-03-03 |
| `salesos/backend/tests/unit/test_check_diff_coverage.py` | New — 19 tests for the above |
| `salesos/backend/scripts/generate_rls_policies.py` | New — STORY-02-01 |
| `salesos/backend/tests/integration/test_rls_policy_generation.py` | New — hand-test for the above |
| `salesos/backend/tests/support/__init__.py` | New — STORY-01-04 |
| `salesos/backend/tests/support/tenant_isolation.py` | New — the reusable harness itself |
| `salesos/backend/tests/support/schema.py` | New — defensive schema-sync helper (see Technical Debt) |
| `salesos/backend/tests/unit/test_meeting_brief_tenant_isolation.py` | New — harness consumer #1, and the regression test for R-15's fix |
| `salesos/backend/tests/unit/test_decision_center_harness_demo.py` | New — harness consumer #2, and the file used for the Expected Demo |
| `salesos/backend/app/routers/meetings.py` | R-15 fix: added the missing `if not opp or getattr(opp, "tenant_id", None) != tenant_id: raise 404` check to `get_meeting_brief` |
| `salesos/backend/domains/workflow/engine.py` | Carried over from the immediately-preceding R-12 task (this session, pre-Sprint-02): UUIDv4 execution IDs |
| `salesos/backend/tests/unit/test_workflow_engine.py` | Carried over: R-12 regression tests |
| `docs/program/RISK_REGISTER.md` | R-01 closed, R-04 updated (mechanism shipped), R-14 and R-15 added |
| `docs/program/TEST_STRATEGY.md` | §11.1 (harness) and §0 (diff-coverage implementation) added |
| `docs/program/SPRINT_PLAN/Sprint-02.md` | Closure addendum |

**Explicitly not part of this report** (pre-existing from Sprint 01 or concurrent/unrelated): `salesos/backend/domains/decision_center/postgres_repo.py`, `domains/decision_center/tests/test_decision_center.py`, `domains/decision_center/tests/test_postgres_repo.py`, `domains/workflow/service.py`, `domains/workflow/tests/test_phase13.py`, `domains/workflow/tests/test_router.py`, `pyproject.toml` (testpaths), `tests/unit/test_middleware.py`, `poetry.lock`, the Alembic migration, and the entire frontend diff.

---

## Database Changes

None applied to any persistent schema. `scripts/generate_rls_policies.py`'s `--apply` path exists but was never invoked with `--yes-i-understand-this-affects-live-queries` against any real database — all hand-testing used `CREATE TABLE ... (LIKE real_table INCLUDING ALL)` clone tables, rolled back automatically via the existing `db_session` fixture's transaction, never committed. Zero net schema change from this sprint.

---

## API Changes

One behavior change, security-only, no contract change: `POST /meetings/{opportunity_id}/brief` now returns `404` (previously would have returned a real cross-tenant data leak, i.e., a *different* tenant's meeting brief) when the opportunity belongs to a different tenant than the caller. Response shape for the legitimate (same-tenant) case is unchanged.

---

## Security Changes

| Item | Detail |
|---|---|
| R-15 fixed | Cross-tenant IDOR in `get_meeting_brief`, live and exploitable prior to this fix. See Files Changed and Risk Register. |
| R-14 discovered, not fixed | Application DB role is superuser + BYPASSRLS — RLS is currently inert for any table it might be enabled on. Flagged as a Sprint 03 prerequisite, explicitly not fixed this sprint (role/connection provisioning change, outside STORY-02-01's "design, start" scope). |
| RLS mechanism validated | `FORCE ROW LEVEL SECURITY` + `current_setting(..., true)` fail-closed pattern + `USING`/`WITH CHECK` symmetry all confirmed working against real Postgres, for a non-superuser role, across 10 real pilot-table schemas. |

---

## Tests Executed

**Full backend suite** (`docker compose exec backend pytest tests/ domains/decision_center/tests/ domains/workflow/tests/ -q --ignore=tests/e2e`, real Postgres/Redis, not mocked):

| Result | Count |
|---|---|
| Passed | 1,957 |
| Failed | 11 |
| Skipped | 4 |
| Errors | 0 |

**The 11 failures are the same pre-existing/unrelated set identified in the Sprint 01 Closure Report** (`tests/integration/test_kafka_live.py`, `tests/test_architecture.py` architecture-boundary, `tests/test_integration.py` ×3, `tests/unit/test_authorization.py` ×2, `tests/unit/test_contact_service.py` ×2, `tests/unit/test_employee_360_service.py` ×2) — none touched by this sprint's changes, unchanged in count and identity from before this session's work began.

**New tests added this sprint, all passing:**
| Test file | Count |
|---|---|
| `tests/integration/test_rls_policy_generation.py` | 5 |
| `tests/unit/test_meeting_brief_tenant_isolation.py` | 1 |
| `tests/unit/test_decision_center_harness_demo.py` | 1 |
| `tests/unit/test_check_diff_coverage.py` | 19 |
| **Total new** | **26** |

(1,931 passed at the end of the immediately-preceding R-12 task + 26 new this sprint = 1,957 — reconciles exactly, confirming nothing regressed elsewhere.)

**Frontend:** `npx tsc --noEmit` — 0 errors (current tree state; not attributable to this sprint's work, see Scope Boundary).

---

## Technical Debt

| Item | Classification | Detail |
|---|---|---|
| `tests/support/schema.py` (`ensure_tables_created`) | Technical Debt, disclosed not silent | Works around `backend/conftest.py`'s `setup_database` fixture only creating tables whose model class happened to be imported by the current test invocation's collection set — same root cause as R-11, a variant one level down. Proper fix (build test schema from real Alembic migrations, matching what `.github/workflows/ci.yml` already does) is larger than any Sprint 02 story's scope. |
| `PostgresOpportunityRepository.get()` still has no `tenant_id` parameter | Architecture Debt, disclosed not silent | R-15's fix is at the router layer only (matching the existing pattern in `opportunities.py`). Adding a required `tenant_id` param to the repository method would touch its abstract interface, the in-memory counterpart, and every call site — out of the small-fix carve-out's scope. Any *new* caller of `.get()` must remember the check manually until this is addressed. |
| Second `.get()`-shaped repository method audit not performed | Documentation Gap | R-15 was found by manual code reading while picking one demo target, not a systematic audit. Whether other repositories have the same "no tenant param on a single-record getter" shape is unknown and not evaluated this sprint. |

---

## Known Issues

- The 11 pre-existing test failures (see Tests Executed) remain open, unowned by this sprint, carried forward from Sprint 01's closure report.
- R-13 (GraphQL/environment parity) remains open, untouched this sprint.
- The large uncommitted frontend diff observed in the working tree (see Scope Boundary) is not explained by this session's work — flagged for the repository owner to confirm, not investigated further here.

---

## Risks

See `docs/program/RISK_REGISTER.md` for full detail and live status. Summary of this sprint's activity:

| Risk | Status change this sprint |
|---|---|
| R-01 | Mitigating → **Closed** (Postgres-layer test coverage confirmed present) |
| R-04 | Mitigating → **Mitigating, mechanism shipped** (diff-coverage gate implemented and tested) |
| R-14 | **New, Open, Critical (score 25)** — highest in the register |
| R-15 | **New, Closed same session (score 20 pre-fix)** — second-highest the register has carried |

---

## Acceptance Criteria Checklist

| Story | Acceptance Criterion (from Sprint-02.md) | Met? |
|---|---|---|
| STORY-01-03 | `X-API-Key` no longer bypasses CSRF check; regression test added | ✅ (Sprint 01, re-verified) |
| STORY-01-04 | Reusable test harness merged; documented in `TEST_STRATEGY.md` | ✅ |
| STORY-01-04 (Expected Demo) | Show the harness catching a reintroduced Sprint 1 IDOR bug | ✅ — performed twice (one informative negative result, one clear catch); documented in `test_decision_center_harness_demo.py` |
| STORY-03-03 | CI blocks PRs with new-code coverage below threshold | ✅ mechanism-verified; not yet field-verified against a real PR event (requires an actual PR to trigger `github.event_name == 'pull_request'`) |
| STORY-02-01 | RLS policy generation script drafted against 10 pilot tables | ✅ — plus hand-tested (read-block, write-forgery-block, fail-closed-on-unset), exceeding "drafted" |

---

## Recommendation

**CONDITIONAL GO.**

All four assigned stories are satisfied, with real evidence, not self-report. The reason this isn't an unqualified GO: **R-14 is a critical, confirmed (not probabilistic) blocker for Sprint 03's stated Phase 0 exit criteria**, discovered this sprint, and it requires a decision from Chief Architect / DevOps-SRE (which role the app connects as, how that's provisioned) before Sprint 03's RLS rollout work can proceed as currently scoped in `docs/program/SPRINT_PLAN/Sprint-03.md`. This is not a reason to hold Sprint 02 itself — everything assigned to Sprint 02 is done — but Sprint 03 should not start its RLS rollout work until R-14 has an owner and a plan, per the Risk Register's own Escalation Rule for score ≥15 risks.

Also carried forward, not blocking: the two Sprint 01 carry-items (owner decision on the 6 pre-existing failures + R-13) are still pending and should not be allowed to accumulate through a third sprint without a decision.
