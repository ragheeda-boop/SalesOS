# Sprint 02 — Independent Verification Report

**Verified by:** Independent Verification Agent (2026-07-31)
**Sprint:** 02 (Phase 0 — Tenant Isolation Tooling, RLS Design, Coverage Gate)
**Prepared from:** Direct evidence only — no reported claims accepted at face value

---

## 1. Repository Review

All Sprint 02 changes are **uncommitted** (working tree only). The working tree also
carries ~400 uncommitted modified frontend files from Sprint 01's codemod work —
none of which are part of Sprint 02 scope (the engineer's report explicitly disclaims
them; spot-checked, none touch Sprint 02 backend files).

### Files Modified (Sprint 02 scope)
| File | Change | Status |
|------|--------|--------|
| `.github/workflows/ci.yml` | `fetch-depth: 0` on checkout; new "Diff coverage gate" step (PR-only, `--fail-under 80`, after the `--cov-report=xml:coverage.xml` step) | ✅ Applied |
| `salesos/backend/app/routers/meetings.py` | R-15 fix: `if not opp or getattr(opp, "tenant_id", None) != tenant_id:` in `get_meeting_brief` (1 line) | ✅ Applied |

### Files Added (Sprint 02 scope)
| File | Purpose | Status |
|------|---------|--------|
| `salesos/backend/tests/support/tenant_isolation.py` | STORY-01-04 reusable cross-tenant harness (`assert_cross_tenant_read_blocked`, `assert_cross_tenant_listing_excludes`) | ✅ Created |
| `salesos/backend/tests/support/__init__.py` | Package init | ✅ Created |
| `salesos/backend/tests/support/schema.py` | `ensure_tables_created` helper (documents `Base.metadata.create_all()` import-order fragility) | ✅ Created |
| `salesos/backend/tests/unit/test_meeting_brief_tenant_isolation.py` | R-15 regression test (first real harness consumer) | ✅ Created |
| `salesos/backend/tests/unit/test_decision_center_harness_demo.py` | Harness demo vs existing Decision Center hand-written coverage | ✅ Created |
| `salesos/backend/scripts/check_diff_coverage.py` | STORY-03-03 diff-coverage gate (pure stdlib, read-only git ops, exit 0/1/2) | ✅ Created |
| `salesos/backend/tests/unit/test_check_diff_coverage.py` | 19 unit tests for the gate | ✅ Created |
| `salesos/backend/scripts/generate_rls_policies.py` | STORY-02-01 RLS policy generator (10-table pilot, `--apply` requires explicit URL + confirmation flag) | ✅ Created |
| `salesos/backend/tests/integration/test_rls_policy_generation.py` | 5 RLS policy-generation tests (clone-table strategy, WITH CHECK rejection asserted) | ✅ Created |
| `docs/program/TEST_STRATEGY.md` §11 (untracked) | Tenant isolation policy + harness documentation | ✅ Matches implementation |
| `docs/program/RISK_REGISTER.md` (untracked) | R-14, R-15 added | ✅ Consistent with evidence |

**Note:** `docs/program/RISK_REGISTER.md`, `docs/program/TEST_STRATEGY.md`, and the
entire `salesos/docs/audit/` tree are themselves untracked — the documentation record
is as uncommitted as the code.

---

## 2. Story Verification

| Story | Result | Evidence |
|-------|--------|----------|
| STORY-01-03 (CSRF) | ✅ PASS | Already satisfied from Sprint 01 — `api_key_authenticated` bypass removed; all 8 CSRF middleware tests passed in Sprint 01 independent verification. Nothing in Sprint 02 touches it. |
| STORY-01-04 (Cross-tenant regression template) | ✅ PASS | Harness is two-sided (blocks tenant B read **and** asserts tenant A can read its own record), raises `CrossTenantIsolationViolation` with tenants/key/leaked value, documented in TEST_STRATEGY.md §11. Wired into 2 real consumers. Plus a **live cross-tenant IDOR found and fixed** (R-15) while picking a demo target. |
| STORY-03-03 (Coverage gate) | ⚠️ CONDITIONAL | Script logic correct and independently exercised against real git history (see F-01 below: the CI wiring has a critical path-mismatch that makes the gate permanently red). |
| STORY-02-01 (RLS design, start) | ✅ PASS | 10-table pilot SQL verified; correct fail-closed design (`FORCE RLS`, `current_setting('app.tenant_id', true)` returns NULL when unset → zero rows, `DROP POLICY IF EXISTS` idempotency, `USING` + `WITH CHECK`). R-14 blocker independently confirmed (see §4). |

---

## 3. Acceptance Criteria

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Regression template reusable, documented | ✅ | `tests/support/tenant_isolation.py` plain async helpers; §11 in TEST_STRATEGY.md |
| Template used by ≥1 real test | ✅ | 2 consumers: meeting brief isolation + decision center harness demo |
| Real security gap found with it | ✅ | R-15: `get_meeting_brief` fetched opportunity without tenant check — any tenant could read another tenant's meeting brief by opportunity_id |
| Fix mirrors established pattern, no interface change | ✅ | 1-line change, exactly matches the guard used 5× in `app/routers/opportunities.py` (lines 135, 182, 213, 239, 265) |
| Diff-coverage gate ≥80% on new lines, blocks merge | ⚠️ | Gate exists and exit codes correct, but CI wiring misresolves coverage paths (F-01) — see §8 |
| Gate exercises against real history | ✅ | Independently ran `_changed_python_files`/`_added_line_numbers` against `HEAD~5...HEAD` (BUG-005 commits) — correct file/line identification |
| Windows UTF-8 safety | ✅ | `_run_git` uses explicit `encoding="utf-8", errors="replace"`; verified on Windows host against this Arabic-first repo (live demonstration: the cp1252 decode failure occurs on first Arabic string without the fix) |
| RLS design start, 10 pilot tables | ✅ | `generate_rls_policies.py` emits correct DDL for all 10 tables; 5 tests pass |
| R-14 (superuser/BYPASSRLS) decision requested | ✅ | Confirmed independently (see §4); correctly blocks Sprint 03 RLS rollout until role is fixed |

---

## 4. Security Review

| Risk | Finding | Verdict |
|------|---------|---------|
| **R-14 — app DB role is superuser with BYPASSRLS** | **INDEPENDENTLY CONFIRMED.** `docker exec salesos-postgres-1 psql -U salesos -d salesos -c "SELECT rolname, rolsuper, rolbypassrls, rolcanlogin FROM pg_roles"` → `salesos` = `rolsuper=t, rolbypassrls=t, rolcanlogin=t`. App config connects as `postgres_user=salesos`. Any RLS policy is **silently bypassed** for all application traffic. Score 25, highest in register — accurate. Blocks Sprint 03's RLS rollout. | ⚠️ Open — correctly flagged, blocks Sprint 03 |
| **R-15 — live cross-tenant IDOR (`POST /meetings/{id}/brief`)** | Fixed and verified. Endpoint now: `if not opp or getattr(opp, "tenant_id", None) != tenant_id: raise 404` (meetings.py:86). `tenant_id` comes from authenticated session (`get_current_tenant_id`). `generate_brief`'s internal opportunity queries are unguarded but only reached after the endpoint guard, and `company_id` is sourced from the guarded record. Sibling endpoints checked: `get_meeting_summary` performs no DB reads (processes request notes only); `get_emails` tenant-scopes in the repository query. | ✅ Fixed |
| **CSRF** | Unchanged from Sprint 01; bypass removal intact. | ✅ Contained |
| **Tenant isolation (DB layer)** | RLS remains ineffective while the app role is a superuser (R-14). Application-layer isolation for the discovered surface is now guarded. | ⚠️ Blocked by R-14 |

---

## 5. Architecture Compliance

- **Harness**: plain async helpers, not fixtures — correct call for the varying "thing to isolate" (repo method / service / router). No fixture-layer coupling. ✅
- **R-15 fix**: mirrors the established `opportunities.py` guard exactly; no interface change; repository-level debt (`PostgresOpportunityRepository.get` lacking `tenant_id`) correctly deferred to the risk register rather than absorbed out-of-scope. ✅
- **RLS generator**: side-effect-free default (prints SQL), `--apply` gated by explicit URL + long confirmation flag, never invoked from CI/Alembic/startup. Safety rails correct. ✅
- **Coverage gate**: pure-stdlib, read-only git ops only, distinct exit codes (0 pass / 1 genuine coverage failure / 2 environment error), fail-closed on absent file, test-file exclusion sensible. ✅ (but see F-01)

No architecture violations introduced by Sprint 02.

---

## 6. Executed Tests (independently run in Docker container)

| Scope | Command | Result |
|-------|---------|--------|
| RLS policy generation | `pytest tests/integration/test_rls_policy_generation.py -x -q` | **5 passed** |
| Tenant isolation (meeting brief) + harness demo | `pytest tests/unit/test_meeting_brief_tenant_isolation.py tests/unit/test_decision_center_harness_demo.py -q` | **2 passed** |
| Diff-coverage gate unit tests | `pytest tests/unit/test_check_diff_coverage.py -q` | **19 passed** |
| **Full suite (report's exact scope)** | `pytest tests/ domains/decision_center/tests/ domains/workflow/tests/ -q --ignore=tests/e2e` | **1957 passed, 11 failed, 4 skipped, 0 errors** |
| RLS generator dry-run | `python scripts/generate_rls_policies.py` | SQL emitted for all 10 tables, correct |
| Diff-coverage against real history (host) | `python -c "from scripts.check_diff_coverage import _changed_python_files, _added_line_numbers ..."` (HEAD~5) | Correct files + added lines identified |
| App role check | `psql ... "SELECT rolname, rolsuper, rolbypassrls, rolcanlogin FROM pg_roles"` | `salesos` = t/t/t ✅ R-14 confirmed |

### Test count comparison

| Metric | Sprint 02 report (claimed) | Independent run (actual) | Delta |
|--------|----------------------------|--------------------------|-------|
| Full suite | 1957 passed, 11 failed, 0 errors | 1957 passed, 11 failed, 4 skipped, 0 errors | **0** (4 skips were not listed in the report) |
| New tests added | +26 | 26 (5 + 2 + 19) | 0 |

### Note on "full suite" scope vs CI scope
The report's "full suite" (`tests/ domains/...`) is **narrower than the CI gate's** scope.
A CI-parity run (`pytest -m "not e2e" --cov=app --cov=domains --cov=sdk --cov=runtime --cov=intelligence`)
produces **23 failures** in this environment: the same 11, plus 12 in `app/modules/company/tests/`
and `app/modules/entity_resolution/tests/` that fail on DB-schema drift in the dev Postgres
(`companies.cr_number` NOT NULL, `contacts.tenant_id` NOT NULL, etc.). In CI the Postgres is
freshly migrated, so the drift subset may not reproduce there — but the 11 pre-existing
failures would. **The CI `test-backend` job is red regardless of the coverage gate.**

---

## 7. Regression Analysis

| Category | Finding |
|----------|---------|
| **Sprint regressions** | **0** introduced by Sprint 02 changes |
| **Pre-existing failures** | 11 confirmed identical to Sprint 01's independent run (architecture 1, authorization 2, contact_service 2, employee_360 2, integration 3, kafka_live 1) — none touch Sprint 02 files |
| **New security regressions** | 0 — R-15 regression test passes; harness two-sided checks pass |

---

## 8. Findings

| ID | Severity | Category | Description |
|----|----------|----------|-------------|
| **F-01** | **P1** | **CI Gate Broken (fail-closed)** | **The diff-coverage gate as wired in CI will fail on virtually every PR with production-code changes, regardless of actual test coverage.** Root cause: path mismatch. `coverage.py` (v7.15.1) writes Cobertura filenames **relative to each `--cov=` source root** — verified with the CI-exact flags in this container: `search/engine/postgres_repo.py` (physical `/app/domains/search/engine/postgres_repo.py`), `search_runtime/__init__.py` (physical `/app/runtime/search_runtime/__init__.py`), `routers/meetings.py` (physical `/app/app/routers/meetings.py`). The gate's `_changed_python_files` uses `git diff --relative` from `salesos/backend`, yielding `domains/search/engine/postgres_repo.py`, `runtime/search_runtime/__init__.py`, `app/routers/meetings.py`. **The two sets never intersect**, so `analyze()` finds every changed file absent from coverage and counts all its added lines as uncovered (fail-closed), producing `Diff coverage: 0.0%` and exit 1. Demonstrated end-to-end against `HEAD~5...HEAD` (BUG-005 commits) with real coverage output: reported 0/3 covered. The 19 unit tests all pass because they use a **synthetic** coverage XML whose paths happen to match the script's expectation with git monkeypatched — the real-world mismatch was never exercised. Failure direction is safe (blocks merges, cannot be gamed to allow untested code), but the gate is unusable as written. **Likely remediation (config-only, ~2 lines):** add `[tool.coverage.run] relative_files = true` (or a correctly-placed `source` list) so coverage.xml paths are CWD-relative and match `git diff --relative`, then re-verify against a real coverage.xml. |
| F-02 | P2 | CI Red (pre-existing) | The CI `test-backend` job (`-m "not e2e"`) fails on the 11 pre-existing failures regardless of the coverage gate, and additionally on 12 schema-drift failures in this environment. STORY-03-03's gate cannot be validated in CI until the unit-test step is green. The report's "full suite 1957/11" scope is narrower than CI's gate scope — the two should be reconciled. |
| F-03 | P3 | Test Gap | `test_rls_policy_generation.py` verifies SQL generation with a `clone`-schema strategy but not `generate_rls_policies.py`'s `--apply` path (needs the guarded confirmation + URL). Acceptable for a pilot (applying RLS now would be dangerous anyway given R-14), but the apply-path remains hand-verified only. |
| F-04 | P3 | Hygiene | My own coverage artifacts (`salesos/backend/coverage.xml`, `coverage2.xml`, `coverage3.xml`) were generated during verification and removed afterward; the pre-existing untracked state of all Sprint 01+02 work remains the primary hygiene debt (see §11). |

---

## 9. Risks

| Risk | Status | Note |
|------|--------|------|
| R-01 (IDOR) | Mitigating — improved | Harness now reusable for any future domain; R-15 is the second IDOR found and closed this cycle |
| R-14 (superuser + BYPASSRLS) | **Open — CONFIRMED** | Independently verified against live Postgres role table. Blocks Sprint 03 RLS rollout. Needs Chief Architect / DevOps-SRE decision (least-privilege role + `SET app.tenant_id` per request) before Sprint 03 |
| R-15 (meetings IDOR) | **Closed ✅** | Verified in diff, pattern-matched to siblings, regression test passing |
| R-11 / R-12 / R-13 (prior) | Unchanged | No Sprint 02 interaction |

---

## 10. Production Readiness

| Criterion | Rating | Evidence |
|-----------|--------|----------|
| Sprint scope complete | ✅ 3/4 stories fully verified; 1 (STORY-03-03) conditional | Per §2 |
| Acceptance criteria satisfied | ⚠️ Except F-01 | Coverage gate deliverable is broken as wired in CI |
| No Sprint-introduced regressions | ✅ 0 | Per §7 |
| Security hardened | ✅ R-15 IDOR closed | Verified fix + regression test |
| Tests independently verified | ✅ All re-run | 1957/11/4 reproduced exactly; 26 new tests pass |
| R-14 blocker correctly surfaced | ✅ Confirmed with primary evidence | Blocks Sprint 03 |
| Architecture preserved | ✅ No violations | Per §5 |
| Changes uncommitted | ⚠️ All working tree | Sprint 01 + 02 work, plus ~400 frontend files |

---

## 11. Decision

**CONDITIONAL GO**

### Conditions
1. **P1 — Fix F-01 before relying on the gate:** reconcile coverage.xml path semantics with `git diff --relative` (e.g., `[tool.coverage.run] relative_files = true` or corrected `source` config), then re-validate against a real coverage.xml produced with CI's exact `--cov=` flags. Until then the CI diff-coverage step is decorative-but-blocking: it fails everything. This must be fixed **before** Sprint 03 can claim a working merge gate. **Highest priority.**
2. **P2 — Make the CI unit-test step green first:** the 11 pre-existing failures (and the 12 environment drift failures) mean `test-backend` is red today; the coverage gate can only be meaningfully validated once it isn't.
3. **Decision on R-14 required before Sprint 03 starts** (R-14 is the explicit Sprint 03 entry gate): create a least-privilege app role without BYPASSRLS, and implement the per-request `SET app.tenant_id` session layer, or explicitly defer RLS rollout.
4. **Commit Sprint 01 + 02 working tree** (including all new files, `docs/program/`, and the risk register) — nothing is committed yet.
5. Close F-03 (apply-path test) when R-14 allows RLS to actually be enabled.

### Rationale
Sprint 02's code quality is high: the harness is genuinely reusable and two-sided, the RLS design is fail-closed and correctly gated behind R-14, the R-15 IDOR fix is minimal and matches the established pattern, and the script's own logic is sound and now exercised against real history. Every reported test count was reproduced exactly. The **only** substantive problem is F-01 — the CI wiring of the STORY-03-03 gate never matches real coverage.py output and will block every PR. It is a fail-closed failure (cannot let low-coverage code slip through), so there is no security exposure; it is a pipeline-correctness defect that must be fixed before the gate is treated as functional.

**Confidence: HIGH** (F-01 is fully evidenced; R-14 confirmed with primary DB evidence; all counts reproduced exactly).

---

*All commands executed in `salesos-backend-1` / `salesos-postgres-1` (docker) or the host repo, per AGENTS.md low-load protocol. Test artifacts removed after verification.*
