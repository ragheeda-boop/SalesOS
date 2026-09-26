# 122 — PostgresProposalRepository: guaranteed crash (3rd occurrence of the report 120/121 bug class) + an independent double-fetch bug that silently discarded 4 different mutations

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container migrated to head, torn down after use. No write to `salesos_test` or production.

## 1. Reachability — live, same wiring pattern as reports 120/121

`PostgresProposalRepository` is instantiated by `app/routers/commercial.py`'s `_get_proposal(db)` factory (`ProposalService(PostgresProposalRepository(db))`). Every real call to `ProposalService.create_proposal()` / `approve()` / `deliver()` / `mark_viewed()` / `accept()` / `reject()` / `expire()` would have crashed on its first `save()`.

## 2. Bug 1 — same class as StageEntry/Quote, this time a partial mismatch

`Proposal` (contract) has `viewed_at`/`accepted_at` (which genuinely exist and match `ProposalModel`'s columns) but **no** `sent_at`, `rejected_at`, or `rejection_reason` — `ProposalModel` (table `commercial_proposals`, FORCE RLS) has all three as flat columns. `save()` read `proposal.sent_at`/`rejected_at`/`rejection_reason` directly — `AttributeError` on every call, confirmed below. `_to_domain()` constructed `Proposal(sent_at=..., rejected_at=..., rejection_reason=...)` — none accepted. `kpis()`'s `ProposalKPIs` construction had the identical mismatch pattern as report 121's `QuoteRevenueKPIs` (`total_sent`/`accepted_count`/`avg_days_to_decision` vs. the real `total_proposals`/`delivery_rate`/`average_cycle_hours`/`proposal_to_win_conversion`).

## 3. Bug 2 — found while fixing bug 1: `_transition()`'s double-fetch silently discarded 4 different mutations

Tracing `ProposalService`'s lifecycle methods (not visible from the mypy finding alone — found by reading the actual call flow) revealed a second, independent, and arguably more consequential bug: `deliver()`, `mark_viewed()`, and `accept()` each fetch their own `proposal` object, mutate a field on it (`delivery_method`/`delivery_url`, `viewed_at`, `accepted_at` respectively), then call `self._transition(proposal_id, ...)` — which **re-fetches its own, independent copy** of the proposal from the repository and saves *that* unmutated copy. `Proposal` is a plain dataclass with no session-identity-map semantics, so the two fetches produce two unrelated Python objects; the caller's mutation was silently discarded every time, regardless of the field-name crash in bug 1. `reject(reason)` had a related, distinct gap: `reason` was passed only into the emitted event's `extra` payload, never onto the `proposal` object at all (there was no field to put it on before this fix added `rejection_reason` to the contract).

## 4. Fix

- `save()` / `_to_domain()`: corrected field mapping, dropping `sent_at`/`rejected_at` from the constructor calls (no contract equivalent) and infers them via status-transition detection — when the persisted status differs from the new status and the new status is `DELIVERED`/`REJECTED`, the corresponding timestamp is set to `proposal.updated_at` (which every transition method already sets to "now" immediately before saving) — same technique as report 121's Quote fix, not fabricated history.
- Added `rejection_reason: str = ""` to the `Proposal` contract (additive; confirmed every construction call site in the repo uses keyword arguments).
- `reject()` now fetches the proposal itself, sets `proposal.rejection_reason = reason`, and passes that **same object** through.
- `_transition()` now accepts an optional pre-fetched `proposal` parameter — when given (by `deliver()`, `mark_viewed()`, `accept()`, `reject()`), it uses that object directly instead of re-fetching, so the caller's own mutations are the ones actually persisted. `approve()`/`expire()` (which have no extra mutation beyond what `_transition()` itself does) are unaffected, still relying on the internal fetch.
- `kpis()`: fixed field names, mirroring the in-memory reference repository's exact formulas (same convention already established for `PostgresPipelineRepository.compute_kpis()` and report 121's `revenue_kpis()`).

**Not fixed, disclosed**: `proposal.sections` (the proposal's actual content, mutated by the real `update_section()` service method) has **no persistence column of any kind** on `ProposalModel` — a materially deeper gap than report 121's Quote-lines case, where an existing, unused sibling table (`QuoteLineModel`) just needed wiring up. Here there is no existing schema home at all; closing this would require a new migration (a `commercial_proposal_sections` table or a JSONB column), out of scope for a crash-fix pass. Documented, not silently worked around.

## 5. Verification — genuine red→green, both bugs together

New `tests/integration/test_proposal_repository_persistence_db.py` (2 tests) drives the real service-level lifecycle (`create_proposal → approve → deliver → mark_viewed → accept`, and separately `create_proposal → reject`) against a fresh, fully-migrated, RLS-enforced disposable database, then asserts directly against the raw table. The `deliver()` assertion specifically proves the double-fetch fix: it checks that `deliver()`'s **own** `delivery_method="portal"` mutation is what's actually in the database, not silently reverted to the model's prior value.

Reverting exactly the 3 changed files (scoped `git stash`): `AttributeError: 'Proposal' object has no attribute 'sent_at'` — the exact predicted failure. Restored: both tests PASS.

Regression: `domains/commercial/proposal/tests/test_proposal.py` + the new integration test: **13/13 PASS**. Ruff (`E4,E7,E9,F,I`): confirmed via scoped stash/pop that the combined 3-file baseline went from 49→48 findings (this fix removed 1 pre-existing issue, added 0); the new test file is Ruff-clean on its own. `compileall` and `git diff --check` clean.

## 6. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py`, `salesos/backend/domains/commercial/proposal/contracts/models.py`, `salesos/backend/domains/commercial/proposal/engine/service.py`, `salesos/backend/tests/integration/test_proposal_repository_persistence_db.py` (new, includes report 118/121's `current_database() != "salesos"` safety guard from the outset).
- `salesos_test` and production: untouched. Only the disposable container (destroyed after use) was written to — every environment-variable export was kept in the same Bash call as the command that needed it throughout this fix, per report 121's disclosed incident.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing "6 hours, all approvals" authorization. This is the 3rd occurrence of the exact same "domain contract vs. denormalized DB model" bug class in this one file (`StageEntry`, `Quote`, `Proposal`); the remaining untouched classes in the same file (`Contract`, `Forecast`, `Analytics`, `Decision`, `Recommendation`, `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory`, `Evidence`) are the natural next candidates, given this file's demonstrated hit rate.
