# 146 — Frontend "stale contract" spot-check: clean baseline confirmed, two recent pages verified field-by-field

**Read-only, C: mirror only.** No source changes; verification via the established `scripts/sync-to-c-and-verify.ps1` workflow (report 107).

## 1. Method

Per report 138's second suggested pivot: checking frontend API-client/type files against their real backend response shapes for the same "stale contract" bug class found repeatedly on the backend this session (a persisted/API contract silently drifting from what the consuming code expects — e.g. reports 142/143's field-name mismatches). Targeted the two most recently added, highest-consequence pages first, on the theory that newer code is where this session's backend bugs concentrated.

## 2. `/v3/fact-review` — fully clean, zero drift

Compared `src/lib/factReviewQueries.ts`'s `FactProposal`/`FactEvidenceSnapshot`/`FactProposalPage` TypeScript types against the real backend response construction:

- `app/modules/facts/router.py::_fact_response()` — every field (`id`, `subject_type`, `subject_id`, `field_name`, `proposed_value`, `status`, `evidence_band`, `score`, `decision_reason`, `actor_type`, `actor_id`, `evidence_snapshot`, `created_at`, `reviewer_id`, `reviewed_at`) matches exactly. (Backend also returns `value_hash`, unused by the frontend — not a bug, just an undeclared field.)
- `app/modules/facts/service.py::_evidence_snapshot()` — the nested `source: {source_domain, source_type, source_id, source_name}` shape matches `FactEvidenceSnapshot`'s `source` field exactly.
- `list_fact_proposals()`'s `{"items": [...], "limit": limit, "offset": offset}` matches `FactProposalPage` exactly; the page component's "next page" button correctly uses `items.length < PAGE_SIZE` rather than assuming a `total` field that was never returned.
- `apply_fact_proposal()`'s `POST /facts/{fact_id}/decision` response matches `decideFactProposal()`'s declared return type exactly, including the literal `crm_applied: false`.

## 3. `/v3/sales-usability` — fully clean, zero drift

Compared `src/lib/reviewQueueQueries.ts`'s `SalesUsabilitySummary`/`SalesUsabilityAccount`/`SalesUsabilityPage` types against `app/modules/master_data/phase7/usability.py`:

- `usability_summary()`'s return (`ready_accounts`, `usable_accounts`, `by_readiness`, `by_blocker`, `gates`) matches `SalesUsabilitySummary` exactly.
- `_load()`'s per-account dict (`global_company_id`, `slug`, `name`, `domain`, `city`, `sales_readiness`, `review_priority`, `usable`, `blockers`) matches `SalesUsabilityAccount` exactly.
- `list_accounts()`'s `{"total": total, "page": page, "page_size": page_size, "items": items}` matches `SalesUsabilityPage` exactly.

## 4. MA-proposal-staging (`md_person_company_link_proposals`) — confirmed no frontend consumer

`grep -rl "link_proposal\|linkProposal\|person_company_link" src/` returns nothing — no frontend page exists for this module, consistent with report 100's own description of it as a backend-only staging area (script-driven, not yet wired to any UI).

## 5. Full-suite regression — clean baseline reconfirmed

Ran the complete frontend verification via `scripts/sync-to-c-and-verify.ps1` (report 107's established C: mirror workflow):

- `npm run typecheck`: 0 errors.
- Full Jest suite: **335/335 test suites, 2691/2692 tests passed (1 pre-existing intentional skip)**, 144s.

## 6. Interpretation and scope

Two spot-checked pages representing this session's newest, highest-consequence frontend surfaces (fact review, sales usability) show **zero** contract drift — a different outcome from the backend, where nearly every newer or previously-mocked-only code path this session examined (StageEntry, Quote, Proposal, Decision, Recommendation, Timeline, Employee) had at least one real, previously undetected bug. A plausible explanation: these two frontend pages were built in the *same* sessions as their backend endpoints (reports 74-81, 97/102/143), so their contracts were kept in sync by construction, whereas this session's backend bugs concentrated in code that predated the current review effort and had only ever been exercised through mocks. This does not rule out drift elsewhere in the frontend, but the two highest-value, most recently built candidates are confirmed clean.

- No files changed. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. Both of report 138's suggested pivots (newer-module raw-SQL sweep; frontend stale-contract check) have now been tried and have reached a natural point of returns — the backend pivot found 2 real bugs and added meaningful coverage (reports 139-145); the frontend pivot confirms a clean baseline on its highest-value targets. Next: continue with a fresh methodology — reviewing recently-touched `app/modules/*` router files (outside `facts`/`agent_reach`/`billing`, already covered) for the same GUC-pinning and field-mapping bug classes, following this session's now well-established, high-yield technique.
