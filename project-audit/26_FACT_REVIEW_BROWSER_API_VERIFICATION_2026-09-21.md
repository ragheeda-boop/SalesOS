# 26 — Fact Review authenticated browser/API verification — 2026-09-21

## Result

**PASS — isolated authenticated browser-to-API-to-PostgreSQL read path.** The V3 Fact Review page displayed a synthetic tenant proposal returned by the current D-source API. This closes the signed-auth browser listing gate for Fact Review; it does not close producer trust, CRM apply, Phase 7, or production gates.

## Scope and method

- Ran the current D-source FastAPI route on loopback port `8001` and the source-hash-matched frontend verification mirror on loopback port `3102`. The frontend proxy targeted only `127.0.0.1:8001`.
- The API used the real Fact Review router, `TenantContextMiddleware`, RS256 token decoding, database role permission checks, and tenant GUC/RLS. Only rate limiting was overridden for the synthetic local request.
- Created a temporary admin, tenant, Company, evidence record, and Fact proposal inside one outer transaction on **`salesos_test`**. Verified the database name and that its role was neither superuser nor `BYPASSRLS`.
- Used a short-lived test-only RS256 key and browser session. No application JWKS files, shared API container, `salesos` database, or real user account were used.

## Evidence

| Check | Result |
|---|---|
| Browser navigation to `/v3/fact-review` | **200; no login redirect** after the test-only session was set |
| Fact Review API GET | **200**; exactly one proposal returned for the temporary tenant and the expected fact ID was present |
| Rendered UI | **PASS**; showed `city: Dammam`, review status, score, and associated Test Registry evidence |
| Repeated cold-start browser run | **PASS**; proposal rendered again after a clean Next dev-server restart |
| Earlier authenticated API integration | **2/2 PostgreSQL integration tests** and **40/40 focused unit tests** (AGENTS.md §79) |
| Persistent fixture check after rollback | **0** temporary tenants, users, facts, or evidence records in `salesos_test` |
| Local process cleanup | Ports `3102` and `8001` closed; synthetic token, helper scripts, and temporary test routes removed |

## Observed limitation

The first Next dev-server run emitted one transient HTTP 500 with `Unexpected end of JSON input` during initial cold compilation/navigation. The authenticated UI then rendered successfully, and a clean server restart reproduced the full 200/list flow. A direct authenticated API request also returned 200 with the expected proposal. No root cause for that one transient development-server response was established; it did not reproduce on the clean restart.

## What this proves and what it does not

- It proves a signed JWT can pass the V3 browser → Next proxy → D-source Fact Review API → database-role/RLS path and display a tenant-scoped proposal.
- It does **not** test browser-side cross-tenant mutation, approve/reject interaction, production auth/OAuth, a production database, external Agent Reach/Maps/Scout calls, or CRM application. Backend authorization/tenant-isolation/reviewer behavior remains covered by the separate integration suite.
- All created rows were rolled back and independently checked as absent. No provider, deployment, staging, commit, or production database write occurred.

## Next gates

1. Connect Minder/Agent Reach through a separately defined trusted producer identity and conservative evidence classifier; keep all output proposal-only until human review.
2. Define field ownership, source freshness, conflict, and supersession contracts.
3. Design and prove a separate atomic approved-fact-to-CRM apply path.
4. Keep Phase 7 human review, DI P1/P2 methodology confirmation, PO sign-off, design-partner proof, hosting, backup, provider, and production gates unchanged.

Roadmap remains **46%** (last full census **52/113**); no new full census was run. Phase 7 remains **BLOCKED** and production remains **NOT APPROVED**.

## Correction — browser decision completed — 2026-09-21

The earlier “browser decision interaction not tested” limitation in this listing report is superseded by [report 28](28_FACT_REVIEW_BROWSER_DECISION_2026-09-21.md). The reason-gated approval action passed from the authenticated current V3 browser page through the current API to `salesos_test`; its reviewer/reason event persisted and the Company value stayed unchanged. All synthetic rows were cleaned and verified absent. Normal production login remains outside this proof.

## Google Maps lead-source gate — 2026-09-21

Follow-up review of current Google terms classifies the workspace Maps scraper and Places-derived lead-list retention as **not approved for SalesOS**. The current published terms prohibit scraping Maps content for use outside Maps and restrict using Maps Core Services for listings/directories and advertising; Places' indefinite-retention exception is limited to place_id. The Agent Reach proposal classifier now has an explicit regression denying persisted google_maps channel evidence; the focused proposal/security suite passes **60/60**. No Maps provider was called, no database was written, and the previous browser evidence remains scoped to review-only flows. Details and primary links: [report 29](29_GOOGLE_MAPS_PROVIDER_GATE_2026-09-21.md). Roadmap remains **46%** (52/113 last complete census; not re-censused); Phase 7 BLOCKED and production NOT APPROVED.
