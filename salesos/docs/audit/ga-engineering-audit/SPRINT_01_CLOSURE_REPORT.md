# Sprint 01 Closure Report

**Date:** 2026-07-30
**Sprint:** 01 (Phase 0 — Foundation & Security Hardening)
**Supersedes for closure purposes:** `SPRINT_01_REPORT.md`, `SPRINT_01_VALIDATION_REPORT.md` (both retained as historical record of the two prior passes; this document is the final word)
**Prepared by:** Independent verification pass (Chief Architect / Release Manager function), re-running all claimed evidence directly rather than accepting prior summaries at face value
**Program references:** `docs/program/RISK_REGISTER.md`, `docs/program/SPRINT_PLAN/Sprint-01.md`, `docs/program/PRODUCT_ROADMAP.md` (Phase 0 exit criteria)

---

## 1. How Sprint 01 Actually Went (three passes)

| Pass | What happened |
|---|---|
| **Pass 1 — original implementation** | 5 stories claimed complete (STORY-01-01 IDOR, STORY-01-02 SSRF, STORY-01-03 CSRF, STORY-03-01 Build, STORY-03-02 Alembic). Reported 1665 tests passing. |
| **Pass 2 — independent verification (this reviewer)** | Re-ran the claims directly. CSRF, build fix, and migration checked out. IDOR fix was structurally sound but had **zero dedicated adversarial test**. SSRF fix was correct but **broke 7 existing tests** in `domains/workflow/tests/`, which was invisible to the reported test command because that directory was missing from `pyproject.toml`'s `testpaths`. |
| **Pass 3 — validation follow-up** | Fixed the 7 broken fixtures (HTTP → HTTPS), added `domains/workflow/tests` and `domains/decision_center/tests` to `testpaths`, fixed 6 pre-existing Decision Center template test failures (unrelated `tenant_id` signature drift), added real adversarial IDOR and SSRF regression coverage. Re-verified independently: decision_center 50/50 matched exactly; workflow came back **142/143**, not the reported 143/143 — one deterministic, reproducible failure (`test_list_executions`) traced to a latent, pre-existing timestamp-collision bug in execution ID generation (R-12), invisible in the report's Docker/Linux run but reproducible every time on this reviewer's Windows environment. Also surfaced 7 pre-existing `test_graphql.py` failures not in either report (R-13, environment-parity question, not a regression). |
| **This closure task** | R-12 fixed and independently re-verified. R-13 formally logged and left open (not a blocker, needs a parity check). Final full re-run performed. This report is the closing record. |

---

## 2. R-12 Fix — What Was Done

**Root cause:** `domains/workflow/engine.py:118` generated `WorkflowExecution.id` from `f"exec_{workflow.id}_{datetime.now(timezone.utc).timestamp()}"` — a raw float timestamp with no additional entropy. On a platform with coarse clock resolution, two `execute()` calls issued back-to-back (as the existing `test_list_executions` test does) can receive the identical timestamp, and therefore the identical ID, causing the second execution to silently overwrite the first wherever IDs are used as a lookup key (the in-memory repository's `self._executions[execution.id] = execution`).

**Fix applied:**
- `engine.py:118` — `WorkflowExecution.id` now built from `uuid.uuid4().hex` (full UUIDv4, 32 hex characters, no truncation).
- `engine.py` (`_execute_step`) — the identical defect pattern was found one method away, generating `WorkflowExecutionStep.id` the same way. Fixed at the same time, in scope, since it's the same bug in the same file rather than a separate concern — disclosed here explicitly rather than silently bundled.

**Compatibility verification performed before applying the fix (not after):**

| Check | Finding |
|---|---|
| DB column width | `WorkflowExecutionModel.id` is `String(64)`. New format is `exec_` (5) + 12-char workflow id + `_` (1) + 32-char UUID hex = **50 characters** — 14 characters of margin. |
| Format/regex validators | Grepped `schemas.py` and the router — `execution_id` is a plain `str` everywhere; no `pattern=`/regex constraint exists anywhere in the workflow domain that would reject the new format. |
| String parsing of the ID | Grepped the entire `domains/workflow/` tree for any code that splits, slices, or otherwise parses the ID's internal structure (e.g. to recover the timestamp or workflow ID) — none found. IDs are only ever compared for equality or used as dict/DB keys. |
| Frontend consumption | Grepped `salesos/frontend/src` for `execution_id`/`executionId` — zero matches. No frontend format assumption exists. |
| Serialization (JSONB step results) | `step_results` is stored as `JSONB` with no length constraint — the step-id fix carries no persistence risk beyond what the execution-id fix already carries. |
| Postgres integration path | Still blocked end-to-end by the pre-existing missing `salesos_test` database (same infra gap already tracked under R-01/R-11) — this was true before the fix and remains true after; not worsened, not resolved, by this change. |

**Test evidence added** (`tests/unit/test_workflow_engine.py`, `TestWorkflowEngine` class):
- `test_execution_ids_unique_under_rapid_sequential_execution` — 50 back-to-back `execute()` calls with no delay, asserts all 50 IDs are unique and that the repository actually retains all 50 (this is the exact original repro scenario, just at higher volume than the pre-existing 2-call test).
- `test_execution_ids_unique_under_concurrent_execution` — the same, but via `asyncio.gather` across 50 truly concurrent calls, the more realistic stress case for an async service under load.
- `test_execution_step_ids_unique_within_single_run` — proves the related step-id fix, since steps within one execution are exactly the scenario most likely to share a coarse timestamp.

**Verification runs (this reviewer, independent, not copied from any report):**

| Command | Before this fix | After this fix |
|---|---|---|
| `pytest tests/unit/test_workflow_engine.py -q` | 52 tests, N/A (file didn't have the new tests yet) | **52 passed** (49 pre-existing + 3 new) |
| `pytest domains/workflow/tests/ -q` | 142 passed, 1 failed | **143 passed, 0 failed** |
| `pytest domains/workflow/tests/test_engine_events.py -q` | not separately isolated | **4 passed** (event-emission ordering unaffected) |
| `pytest tests/ domains/decision_center/tests/ domains/workflow/tests/ -q --ignore=tests/e2e --ignore=tests/test_integration.py --ignore=tests/integration` | 1809 passed, 15 failed | **1813 passed, 14 failed** — exactly one failure resolved (`test_list_executions`), nothing else moved, nothing new introduced |

R-12 is closed with direct evidence, not a self-report.

---

## 3. Full Final Verification Table — All Sprint 01 Scope

| Item | Status | Evidence |
|---|---|---|
| STORY-01-01 IDOR (service-layer) | ✅ Verified | Real `tenant_id` column, sourced from trusted `Depends(get_current_tenant_id)`; expanded adversarial test covers direct read, audit, feedback, listing, aggregation; 50/50 `decision_center` tests pass |
| STORY-01-01 IDOR (Postgres-layer) | ⚠️ Open, tracked, not a Sprint 01 blocker | Fixed SQL never executes under test — blocked by missing `salesos_test` DB (pre-existing infra gap, tracked under R-01/R-11, not introduced by this sprint) |
| STORY-01-02 SSRF | ✅ Verified | `validate_webhook_url` wired into `create_webhook`/`update_webhook`; 7 real adversarial tests (HTTP, localhost, 3× private IP ranges, loopback-via-DNS, update-path, valid-HTTPS-passthrough), all independently re-run and passing |
| STORY-01-03 CSRF | ✅ Verified | Test correctly rewritten from asserting the bypass to asserting a 403; re-confirmed passing |
| STORY-03-01 Build | ✅ Verified | `npx tsc --noEmit` independently re-run, zero errors, suppression flags confirmed removed |
| STORY-03-02 Alembic | ✅ Verified, partial by design | Migration 0052 sound (correct backfill-then-NOT-NULL pattern); 1 of 13 drift items closed, 12 explicitly and honestly deferred to Sprint 02 |
| `testpaths` blind spot (R-11) | ✅ Closed for the 2 directories that mattered | Diff-confirmed; immediately paid for itself by surfacing R-12 |
| R-12 (execution ID collision) | ✅ Closed this session | See §2 above |
| R-13 (GraphQL / environment parity) | 🟡 Open, not a blocker | Unrelated to any Sprint 01 story; no code in this area was touched by Sprint 01; needs a Docker-vs-local dependency parity check, recommend as a Sprint 02 or ad hoc task |

---

## 4. Remaining Known Issues — Explicitly Not Sprint 01 Scope

These predate Sprint 01, are unrelated to any of its 5 stories, and are not part of the Phase 0 exit criteria in `docs/program/PRODUCT_ROADMAP.md` (which require the 3 named P0s closed, RLS live, and CI green — not a zero-failure count across the entire pre-existing suite, which `CANONICAL_ARCHITECTURE.md` already documents as Grade D test coverage):

- `tests/test_architecture.py::test_domain_does_not_import_ui[domain_dir6]` — pre-existing `domains/employee/*` architecture-boundary violation
- `tests/unit/test_authorization.py` ×2 — pre-existing authorization policy/test mismatch (`company:create` permission)
- `tests/unit/test_contact_service.py` ×2 — pre-existing contact model/test mismatch (`company_id` required)
- `tests/unit/test_employee_360_service.py` ×2 — pre-existing employee-360 logic/fixture mismatch
- `tests/unit/test_graphql.py` ×7 — newly surfaced in this reviewer's environment, tracked as R-13, likely a Docker/local dependency parity gap
- `tests/integration/*`, `tests/test_health.py`, `tests/test_integration.py` — blocked by the missing `salesos_test` database (pre-existing infra gap, also the reason STORY-01-01's Postgres-layer coverage can't be completed yet)

**These are not resolved by this closure and are not claimed to be.** Per the prior validation report's own recommendation, they need an explicit owner decision (accept as out-of-scope backlog, or assign) before or during Sprint 02 — this closure report does not make that call unilaterally, it only confirms none of them are Sprint 01 blockers.

---

## 5. Final Recommendation

**Sprint 01 is CLOSED.**

Rationale: all 5 originally-scoped stories are independently verified with real, reproducible evidence (not self-reported claims) — across three rounds of scrutiny, every gap that was found was fixed and re-verified, not argued away. The one new defect discovered mid-review (R-12) is fixed and closed with direct test evidence. The one remaining open item (R-13) is an environment-parity question unconnected to any Sprint 01 story, and the six pre-existing failures are documented, unrelated, and were already correctly out of scope in the prior report.

**Recommend proceeding to Sprint 02**, with two carry-forward items for the Sprint 02 kickoff (not blockers, but should not be forgotten):
1. Get an explicit owner decision on the 6 pre-existing failures + R-13 (per §4) — accept as backlog or assign.
2. Sprint 02's own scope (per `docs/program/SPRINT_PLAN/Sprint-02.md`) already includes the remaining Alembic drift reconciliation (12 tables) and should also absorb the `salesos_test` database provisioning, since that single infra fix would simultaneously unblock STORY-01-01's Postgres-layer test coverage, 54 integration tests, and `tests/test_health.py`.
