# 102 — PO Phase-B implementation: B4–B8 (2026-09-25)

**Authority:** PO Phase-B decisions, [report 99](99_PO_PHASE_B_DECISION_RECORD_2026-09-25.md). Owner directive: "كلها موافق عليها + وثق كل شي" (all approved, document everything).
**Scope:** code and tests only. Disposable container `loop4h-pg` and local unit runs. No writes to production or `salesos_test`. No commit or push.
**Invariants (report 91):** unchanged. No gate opened, no merge, no CR adjudication.

## 1. Implemented decisions

| # | Decision (report 99) | Implementation | Files |
|---|---|---|---|
| B4 | Route NBA feedback through the HITL path | `POST .../nba/feedback` now takes `nba_id: UUID`, `action` (`accepted`/`dismissed`), required `original_action_type`, and `reason`. Seller comes from `get_current_user_id`. It resolves `company_name` via `commercial_opportunities` LEFT JOIN `companies` under a pinned tenant (404 if not found). It calls `FeedbackService.record(...)` with `action_id = recommendation_id = nba_id` and maps `dismissed` to `rejected`. Returns `{"status":"ok","feedback_id":...}`. The broken `NBAEngine.record_feedback()` (report 92, finding 4) is removed and replaced by a pointer comment. | `runtime/nba_engine/api/router.py`, `runtime/nba_engine/__init__.py` |
| B5 | Grounding reads `company_signals` + `activity_records` | Signals: `confidence_score AS intensity`, `severity AS priority`, `COALESCE(last_seen_at, first_seen_at, created_at) AS detected_at`. Activity: `action AS event_type`, `COALESCE(metadata->>'description', action) AS description`, `"timestamp" AS occurred_at`, filtered by `entity_type='company' AND entity_id=:cid`. This replaces the nonexistent `buying_signals`/`timeline_events` (report 71). | `intelligence/grounding.py` |
| B6 | Seller leaderboard for managers/admins only | `GET /hitl/analytics` resolves the role (`get_current_user_role`). `admin`/`manager` get the tenant-wide dashboard. Every other role gets `get_dashboard(tenant, current_user_id, leaderboard=False)`, which returns only their own productivity row; a supplied `seller_id` is ignored. `leaderboard=False` without a seller raises `ValueError` (fail-closed). | `app/modules/signal_actions/hitl_router.py`, `hitl_service.py` |
| B7 | Outcome idempotency key required | `OutcomeRequest.idempotency_key: str = Field(..., min_length=1, max_length=128)`. A missing key is a 422, which closes the NULL-dedup gap from report 87. The frontend type `recordOutcome` now requires `idempotency_key: string`. The only caller (`company-nba-tab.tsx`) already sends `crypto.randomUUID()`. | `hitl_router.py`, `salesos/frontend/src/lib/api/hitl.ts` |
| B8 | Comm-hub cross-tenant account enumeration | `_active_accounts_all_tenants()` reads `SELECT id FROM tenants` (not RLS-scoped). For each tenant it pins `app.tenant_id` and calls `GoogleAccountRepository.list_active()`. Both sync tasks use it and keep their per-account pin (report 84). | `app/modules/communication_hub/tasks.py` |

## 2. B8: implementation differs from the recorded decision

Report 99 recorded B8 as "a narrow SECURITY DEFINER function". It was implemented instead as **per-tenant pinned enumeration**. The decision's intent (least privilege, no RLS bypass) is kept. The reason for the change:

- `google_accounts` is **FORCE** RLS. FORCE applies to the table owner as well. A SECURITY DEFINER function runs as its owner, so it would still see zero rows. It would only work if that owner had `BYPASSRLS` or was a superuser, which is the broad privilege the decision meant to avoid.
- `tenants` is not tenant-RLS-scoped. Listing tenant IDs and then reading each tenant's accounts under that tenant's own pin needs no new role, function, or migration. Every account read still goes through the normal tenant policy.
- Cost: one query per tenant for each sync tick. That is acceptable for a scheduled job, and the job has no worker provisioned yet (report 84).

**PO note:** this deviation is recorded here for sign-off. It needs no migration and can be reversed.

## 3. Verification

| Check | Result |
|---|---|
| B4 | `test_nba_feedback_hitl_db.py`: a real opportunity returns 200 and persists exactly one `nba_feedback` row with the authenticated seller, `action_id = recommendation_id = nba_id`, and `decision='rejected'` for `dismissed`. An unknown opportunity returns 404. A non-UUID `nba_id` returns 422. Cross-tenant invisibility comes from the pinned lookup; this test does not assert it separately. |
| B5 | `test_grounding_service_db.py` extended: seeded `company_signals` and `activity_records` rows appear in the grounding context (`"Hiring 20 engineers"`, `"Discovery call held"`). The old queries targeted nonexistent tables and returned `[]` (report 71). |
| B6 | Unit `test_analytics_leaderboard_only_for_managers`: admin/manager keep `seller_id` and the leaderboard; user/auditor/api are forced to `(me, leaderboard=False)`. DB `test_feedback_analytics_leaderboard_db.py`: a non-manager sees exactly their own row (2 outcomes, conversion 1.0). `leaderboard=False` without a seller raises `ValueError`. |
| B7 | Unit `test_outcome_without_idempotency_key_is_rejected` (pydantic `ValidationError`). The existing unit and DB seller tests now send a key. |
| B8 | `test_communication_hub_tasks_guc_db.py`, new cross-tenant enumeration test: accounts in two tenants are both returned by `_active_accounts_all_tenants()` under the restricted `salesos_app` role. An unpinned `list_active()` still returns 0. |
| Combined integration regression (container) | **69/69 PASS**, including the schema-contract test (report 101). |
| Full backend unit suite (local) | **3,781 passed, 0 failed**, 4 skipped, 7 xfailed, 3 xpassed (baseline was 3,779 + 2 new). |
| Frontend TypeScript (C: mirror, `sync-to-c-and-verify.ps1`) | **PASS**, 0 diagnostics. |
| Frontend Jest `nba\|hitl` | **4 suites, 51/51 PASS**. |

## 4. Not done / still open

- **B1–B3 (G5/G4/G3):** human review work. Not agent-executable, and no gate was opened.
- **B9.4 V3 page:** code-level delivery is done (§5). An authenticated render against `salesos_test` has not been run.
- **Browser proof** of the B6/B7 UI paths: not run. The API contract is covered by tests only.
- **B8 in production:** no Celery worker is provisioned, so this stays code-ready only.
- **Owner actions (report 100):** commit batches, rotating the pushed HS256 secret, a history-purge decision, and a CI job for `SCHEMA_CONTRACT_DSN`.

**Status:** Phase 7 gates G3/G4/G5 remain OPEN. Production is **NOT APPROVED**.

## 5. B9.4: V3 sales-usability page (added the same day)

| Item | Detail |
|---|---|
| Page | `/v3/sales-usability` (`salesos/frontend/src/app/v3/sales-usability/page.tsx`). Read-only. Shows the ready and usable counts, gate status (the source appears on hover), and counts per blocker with Arabic labels. It has a paginated account table (100 per page) with `usable` and `blocker` filters. A banner states that the page opens no gate. |
| Client | `fetchSalesUsabilitySummary` and `fetchSalesUsabilityAccounts` in `src/lib/reviewQueueQueries.ts` (tenant header, same pattern as the existing queue calls). |
| Navigation | "Sales usability" link on `/v3/review-queue`. Customer navigation is unchanged (internal Phase 7 tooling). |
| Tests | `sales-usability/__tests__/page.test.tsx`, 2 tests: summary, gates and blocked rows render; filters send `usable=false` and `blocker` and reset to page 1. |
| Verification | TypeScript PASS; ESLint PASS (0 findings); Jest `sales-usability\|fact-review` 2 suites, 5/5. In the browser, `/v3/sales-usability` redirects to `/login?callbackUrl=%2Fv3%2Fsales-usability` with 0 console errors. |
| Not verified | An authenticated render with real counts. It needs a D-source backend on `salesos_test` and a test session, which were not run. |
