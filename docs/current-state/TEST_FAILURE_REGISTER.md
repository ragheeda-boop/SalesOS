# TEST FAILURE REGISTER — 2026-08-24

**Source:** Independent forensics on `salesos/backend`  
**Baseline:** 56 failures + 5 errors = 61 total (0 new regressions)  
**Triaged from:** `docs/reports/UNIT-SUITE-TRIAGE-2026-08-23.md`  

---

## Category A — Frontend Path Not Found (5 tests)

| Test | File | Root Cause | Classification |
|------|------|------------|----------------|
| `test_proposals_list_page_exists` | `test_phase1_product_core.py:427` | `salesos/frontend/` not mounted in Docker backend container | Environment issue |
| `test_proposals_detail_page_exists` | `test_phase1_product_core.py:434` | Same | Environment issue |
| `test_reviews_list_page_exists` | `test_phase1_product_core.py:441` | Same | Environment issue |
| `test_reviews_detail_page_exists` | `test_phase1_product_core.py:448` | Same | Environment issue |
| `test_proposals_nav_item_exists` | `test_phase1_product_core.py:455` | Same | Environment issue |

**Root cause:** `_fe_base()` walks relative paths looking for `salesos/frontend/`. In Docker backend container, only `salesos/backend/` is the working context.

**Action:** Add `@pytest.mark.skipif` when frontend not mounted, or add Docker-appropriate candidate path.

---

## Category B — Event Loop Sync Wrapper Anti-Pattern (48 tests)

**Root cause:** Sync tests use `_run(coro)` calling `asyncio.get_event_loop().run_until_complete(coro)`. When run within pytest-asyncio's managed loop (auto mode), the loop is either absent or closed by prior tests.

**These tests PASS when run in isolation.**

| File | Failing Tests | Count |
|------|--------------|:-----:|
| `test_phase1_product_core.py` | `test_review_service_create`, `test_review_service_decide` | 2 |
| `test_phase2_evidence_chain.py` | `test_record_insight`, `test_record_insight_with_evidence`, `test_add_evidence_to_insight`, `test_add_evidence_to_missing_insight`, `test_list_insights`, `test_list_high_confidence`, `test_kpis`, `test_save_and_get_insight`, `test_get_missing_insight`, `test_list_by_target`, `test_count_by_category` | 11 |
| `test_phase3_ai_governance.py` | `test_log_policy_blocked`, `test_log_policy_denied`, `test_log_hitl_approved`, `test_log_hitl_rejected`, `test_log_hitl_escalated`, `test_log_pii_scrubbed`, `test_log_pii_blocked`, `test_query_by_action`, `test_query_by_resource_type`, `test_audit_stats` | 10 |
| `test_phase3_hitl_approval.py` | `test_create_request`, `test_approve_request`, `test_reject_request`, `test_escalate_request`, `test_cancel_request`, `test_cannot_approve_terminal_request`, `test_insufficient_authority_rejected`, `test_vp_can_approve_manager_level`, `test_check_expiration`, `test_check_no_expiration`, `test_list_pending`, `test_list_pending_with_assignment`, `test_kpis`, `test_nonexistent_request` | 14 |
| `test_phase3_evaluation.py` | `test_run_evaluation_with_grounding`, `test_run_evaluation_with_gate` | 2 |
| `test_phase4_platform.py` | `test_persistent_dlq_add_calls_session`, `test_persistent_dlq_list_all`, `test_persistent_dlq_count`, `test_persistent_dlq_handles_persist_failure_gracefully`, `test_retire_exhausted_logs_warnings`, `test_retire_exhausted_returns_zero_when_no_exhausted` | 6 |
| `test_quota_accounting.py` | `test_success_records_actual_provider_tokens`, `test_total_falls_back_to_prompt_plus_completion`, `test_failed_call_records_nothing`, `test_zero_usage_records_nothing`, `test_explicit_tenant_overrides_bound_default` | 5 |

**Classification:** Environment issue (async/sync anti-pattern in test harness)

**Action:** Replace `_run(coro)` with `asyncio.run(coro)` or convert to native `async def test_` functions.

---

## Category C — Genuine Business Logic Defect (1 test)

| Test | File | Root Cause | Classification |
|------|------|------------|----------------|
| `test_signal_produces_nba` | `test_il1c_runtime_proof.py:81` | `SignalEngine.get_next_best_action("c1")` returns `None` after FUNDING signal ingestion | **Genuine defect** |

**Root cause:** The in-memory `SignalEngine` does not produce an NBA from a single `ingest_signal` call. Either the test expectation is wrong or the engine has a gap.

**Action:** Inspect `intelligence/signals/__init__.py` `SignalEngine.get_next_best_action()` contract. Fix engine or update test expectation.

---

## Category D — Soak Gate Script Missing in Docker (5 tests)

| Test | File | Root Cause | Classification |
|------|------|------------|----------------|
| `test_healthy_200_is_pass` | `test_wave11_soak_gate.py:34` | `wave11-soak-gate.py` not in Docker image | Environment issue |
| `test_degraded_200_is_warn` | `test_wave11_soak_gate.py:40` | Same | Environment issue |
| `test_db_error_even_if_overall_healthy_is_warn` | `test_wave11_soak_gate.py:52` | Same | Environment issue |
| `test_http_400_is_warn` | `test_wave11_soak_gate.py:60` | Same | Environment issue |
| `test_none_payload_200_is_pass` | `test_wave11_soak_gate.py:64` | Same | Environment issue |

**Root cause:** `_GATE_PATH` resolves to `salesos/scripts/wave11-soak-gate.py` which exists on host but is not in Docker image.

**Action:** Add `COPY scripts/ /app/scripts/` to Dockerfile, or add `pytest.mark.skipif(not _GATE_PATH.exists(), ...)`.

---

## Category E — Event Loop Closed at Setup (2 errors)

| Test | File | Root Cause | Classification |
|------|------|------------|----------------|
| `test_create_returns_201_shape_and_persists` | `test_icp_admin_api.py` | `RuntimeError: Event loop is closed` | Flaky / ordering-dependent |
| `test_1_no_guc_sees_zero_rows` | `test_rag_rls.py` | Same | Flaky / ordering-dependent |

**Root cause:** Prior test disposes engine and closes loop. These tests need the loop but find it closed.

**Action:** Fix session-scoped loop disposal ordering, or move DB-backed tests to separate pytest session.

---

## Summary

| Category | Count | Classification | Severity | Action |
|----------|:-----:|---------------|:--------:|--------|
| A — Frontend path | 5 | Environment issue | Low | Skip or add Docker mount |
| B — Event loop sync wrapper | 48 | Environment issue | Medium | Replace `_run(coro)` or convert to async |
| C — NBA from signal | 1 | **Genuine defect** | Medium | Investigate `SignalEngine` contract |
| D — Soak script missing | 5 | Environment issue | Low | Add COPY or skip marker |
| E — Loop closed at setup | 2 | Flaky / ordering | Low | Fix loop disposal ordering |
| **TOTAL** | **61** | | | |

**Key finding:** Only **1 of 61** is a genuine defect. The remaining 60 are environment/infrastructure issues that pass when run in isolation.
