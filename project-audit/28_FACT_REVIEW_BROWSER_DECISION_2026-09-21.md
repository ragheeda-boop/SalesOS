# 28 — Fact Review authenticated browser decision proof — 2026-09-21

## Result

**PASS — reviewer decision from the browser through the current UI/API into PostgreSQL.** A temporary tenant-scoped proposal was opened in V3 Fact Review, approved with a required reason, and reloaded under the Approved filter. PostgreSQL recorded the reviewer, timestamp, reason, and one `REVIEW_DECIDED` event. The target Company city remained `NULL`; approval did not apply a CRM value.

## Scope and setup

- Frontend: source-matched verification copy at `C:\Users\raghe\AppData\Local\Temp\SalesOS-frontend-check-20260920`, served on loopback port `3102`. Its current frontend source hashes matched the checked-out D source per the prior verification report.
- API: temporary FastAPI harness built from current D-source `identity_router` and `facts_router`, served on loopback `8001`; normal API database role, real RS256 signing/verification, tenant middleware, API-key middleware, CSRF middleware, RBAC, and tenant GUC were exercised.
- Database: `salesos_test` only. Before seeding, the harness asserted the database name and that the runtime database role was neither superuser nor `BYPASSRLS`.
- Fixture: one synthetic tenant, admin reviewer, Company, proposal, and evidence. The browser received a short-lived test JWT from an in-memory-only test route; no production key file or real account was used.

## Browser evidence

| Check | Result |
|---|---|
| V3 route | `/v3/fact-review` rendered with the authenticated tenant session |
| Proposal and evidence | **PASS**; page showed `city: Dammam`, pending status, evidence source/description, and confidence |
| Reason control | **PASS**; approval stayed disabled until the reviewer entered a non-empty reason |
| Approve action | **PASS**; clicked the real page action and the pending proposal left the default queue |
| Approved filter | **PASS**; selecting Approved returned the same proposal with its reviewer ID and review timestamp |
| PostgreSQL | **PASS**; status `APPROVED`, reviewer matched the test admin, reason matched, and exactly one `REVIEW_DECIDED` / `APPROVED` event existed |
| CRM value | **PASS**; `companies.city` stayed `NULL` after approval |
| UI/server errors | No visible framework error overlay. Next server output showed the page compiled and returned HTTP 200. Browser console capture was not available through the installed CUA surface; the `agent-browser` CLI was not installed. |

The frontend page and backend endpoint were both real current-source code. The test-only session bootstrap skipped the normal credential-entry/login flow, so this does not verify production login, OAuth, or secure-cookie behavior. The isolated browser/API harness did not call any Maps, Agent Reach, Scout, or other provider.

## Cleanup and safety

- API and frontend test servers were stopped; ports `8001` and `3102` were closed.
- An in-browser cleanup page removed the synthetic access token and tenant ID from local storage and cleared the test access-token cookie; the tab was closed.
- Exact-scope `salesos_test` checks returned zero for the synthetic tenant, user, Company, fact, evidence, fact-evidence link, decision event, device session, and refresh-token family.
- No production/shared database, provider, deployment, staging, CRM value, staging area, or commit was changed.
- **Local test artifacts:** the platform rejected removal of temporary helper/key files. The short-lived synthetic signing key pair and helper remain under `C:\Users\raghe\AppData\Local\Temp\salesos-fact-review-browser-jwks\` and `C:\Users\raghe\AppData\Local\Temp\salesos_fact_review_browser_harness.py`; they are not application or production keys, and the servers that used them are stopped. The temporary `salesos-fact-review-browser` folder also contains the one-time session-cleanup HTML page. No test token or state JSON remains.

## Remaining gates

1. Provision Minder’s service identity and API key through a controlled, auditable owner procedure.
2. Define provider quotes, durable per-tenant budgets, and source-to-value validation before any provider execution.
3. Set field ownership, freshness, conflict, and supersession rules.
4. Design and prove a separate atomic approved-fact-to-CRM apply path.
5. Complete Phase 7 candidate review, DI P1/P2 confirmation, PO sign-off, partner/production proof, and operational/commercial gates.

This focused browser proof does not change roadmap completion: **46%** (last full census **52/113**; no full recensus). Phase 7 remains **BLOCKED** and production remains **NOT APPROVED**.
