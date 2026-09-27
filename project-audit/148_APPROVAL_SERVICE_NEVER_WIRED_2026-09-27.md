# 148 — The entire Approval/HITL REST API always returned 503; the copilot's separate HITL gate wrote to a disposable store nobody could ever read

**Ephemeral, disposable Postgres container only (`sweep-pg19`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Scope — continuing the `domains/*/postgres_repo.py`-style sweep into `domains/*/infrastructure/postgres_repository.py`

Checked the 3 remaining, not-yet-swept files of this shape: `domains/analytics/infrastructure/postgres_repository.py` and `domains/scoring/infrastructure/postgres_repository.py` (both confirmed **fully clean** — every field across all 4 analytics sub-domains, and all 4 nested levels of the scoring `ScoreCard→Score→ScoringFactor→SignalEvidence` structure, map exactly to their real dataclasses; `PostgresReportRepository` is live via `app/routers/analytics.py`, `PostgresScoreCardRepository` is dead code with correct field mapping). `domains/approval/infrastructure/postgres_repository.py` was ALSO confirmed fully clean on the same field-mapping axis — but investigating its reachability surfaced a severe, unrelated, genuinely live defect.

## 2. The finding — `app.state.approval_service` was never set anywhere, ever

`app/routers/approval.py`'s `_get_service()`/`_get_optional_service()` are the **only** two places in the entire codebase that reference `app.state.approval_service` (confirmed via repo-wide grep) — both via `getattr(request.app.state, "approval_service", None)`, both raising `HTTPException(503, "Approval service not initialized")` (or returning `None`) when it's unset. Grepping `app/boot/startup.py` (the live boot module) for any assignment to this attribute, or any reference to `ApprovalService`/`domains.approval` at all, returns **zero matches**. The router itself IS correctly mounted (`app/boot/routers.py:512`, `/api/v1`, with real auth dependencies) — this is not a routing gap. Every real call to the entire Approval/HITL REST API (`POST /approvals`, decision endpoints, `list_pending`, `count_by_status`, etc.) has returned `503 Service Unavailable` unconditionally since the router was created (report 15's history: "P3-5 Human Approval (HITL)... COMPLETE").

## 3. A second, independent defect on the same feature — `app/routers/copilot.py`'s Recommend-mode HITL gate

`POST /copilot/mode` with `mode=RECOMMEND` (the "P3-1: Recommend mode → HITL approval gate (no auto-execute)" feature, per its own docstring) constructed `ApprovalService(repository=InMemoryApprovalRepository())` **fresh, on every single call** — a disposable, request-scoped, empty in-memory dict, garbage-collected the instant the HTTP response returns. The endpoint's response includes a real-looking `approval_id` UUID implying "this recommendation needs manager sign-off before it executes," but that ID can **never be looked up again by anyone** — not through the (also-broken) Approval REST API, not through any other path in the system. Combined with the finding above, the "human must approve before this executes" gate was, in the shipped code, completely unenforceable in two entirely independent ways simultaneously: even if `app.state.approval_service` had been wired, this branch didn't use it anyway.

## 4. Why existing tests never caught either defect

`tests/unit/test_phase3_copilot_modes.py::test_recommend_creates_approval` — the one test with a name suggesting it covers this — never calls the real `copilot_mode()` router function at all. It constructs its **own**, separate `InMemoryApprovalRepository()`/`ApprovalService()` and asserts only that `ApprovalService.create_request()` works as a unit in isolation. It could never have caught either defect, since it never exercises the actual code path. `tests/unit/test_phase3_hitl_approval.py` (23 tests) similarly tests `ApprovalService` directly against `InMemoryApprovalRepository`/`PostgresApprovalRepository`, never through the boot-wired `app.state` path. This matches the recurring pattern this session has found repeatedly: a unit test proving a *component* works correctly, while the *wiring* that would let a real request ever reach that component was never exercised by anything.

## 5. Fix

- **`app/boot/startup.py`**: added `_init_approval()`, following the exact, already-proven-correct `_init_decision_center()`/`_init_feature_store_domain()` pattern — `ApprovalService(repository=FactoryBoundRepository(PostgresApprovalRepository, async_session))`, correctly tenant-GUC-pinned per call via `tenant_scoped_session` (confirmed correct in reports 139/140). Added to Phase 1's parallel init task list.
- **`app/routers/copilot.py`**: the Recommend-mode branch now reads `request.app.state.approval_service` (the same shared, persistent service `app/routers/approval.py` reads) instead of constructing a disposable one; fails closed with `HTTPException(503, ...)` — matching the router's own existing convention exactly — if the service is somehow unavailable, rather than fabricating an untrackable approval ID.

## 6. Verification — genuine red→green

New `tests/integration/test_approval_service_wiring_db.py` (2 tests) against a fresh, disposable, fully-migrated, RLS-enforced Postgres container:

- `test_init_approval_wires_a_real_persistent_service`: calls `_init_approval()` directly against a bare `SimpleNamespace` stand-in for the FastAPI app, confirms `approval_service` is set, creates a real approval request through it, and — critically — retrieves it back via `svc.get(created.id)` from what is, per `FactoryBoundRepository`'s design, a genuinely separate database round trip each time (not an in-memory object the same Python reference happens to still hold) — proving persistence, not just object identity.
- `test_approval_router_service_lookup_finds_the_wired_service`: confirms `app/routers/approval.py`'s exact `_get_optional_service()` lookup succeeds against the wired state.

Reverting exactly `app/boot/startup.py` (scoped `git stash`): `ImportError: cannot import name '_init_approval' from 'app.boot.startup'` — the exact predicted failure (the function didn't exist at all before this fix). Restored: both PASS.

Regression: `tests/unit/test_approval_route_identity.py` (3) + `tests/unit/test_phase3_copilot_modes.py` (9) + `tests/unit/test_phase3_hitl_approval.py` (19) + the 2 new tests: **39/39 PASS**, no change to any existing behavior. Ruff (`E4,E7,E9,F,I`): pre-existing import-sort findings on both changed files unchanged in count (confirmed via scoped stash/pop, 0 new); the new test file's own transient import-order nit fixed directly. `compileall` and `git diff --check` clean.

## 7. Scope and safety

- Files changed: `salesos/backend/app/boot/startup.py` (new `_init_approval()` function + phase-1 registration), `salesos/backend/app/routers/copilot.py` (Recommend-mode branch rewired, dead imports removed), `salesos/backend/tests/integration/test_approval_service_wiring_db.py` (new).
- One disposable, ephemeral Postgres container (`sweep-pg19`) used for verification; destroyed after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.
- Noted, not investigated further: parallel-session changes visible in `git status` (`conftest.py`, `tests/integration/conftest.py`, `int_perfile_runner.py`, several `.ts` files) were left untouched — not part of this fix, not committed by this report.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is one of this session's most severe findings by scope — an entire, previously-celebrated-as-"COMPLETE" (report 15) feature area (HITL Approval) that was completely non-functional in two independent ways at once, on the live, mounted, real-world-reachable API surface. Closes the `domains/*/infrastructure/postgres_repository.py` file family (analytics/approval/scoring all now checked). Remaining candidates for the next tick: a repo-wide grep for other `InMemoryXRepository()` constructions inside request-handling code (the exact anti-pattern found here) to check for further instances of the same "disposable store masquerading as persistent" bug shape.
