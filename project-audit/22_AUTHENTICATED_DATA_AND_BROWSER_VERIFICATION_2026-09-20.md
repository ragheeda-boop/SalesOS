# 22 — Authenticated Data and Browser Verification — 2026-09-20

> This follow-up supersedes the earlier same-day statements that authenticated SalesOS data pages could not be tested. Verification used an isolated local API and `salesos_test`; production was not queried or changed. Phase 7 remains blocked and production remains **NOT APPROVED**.

## Result

Authenticated Master Data pages rendered against the restored test dataset. A review-queue display defect was fixed and browser-checked: P3 and P1/P2 tables now page through the complete API result instead of silently omitting rows. The test account and tenant used for the live browser session were removed afterward.

## Database and safety checks

- The only database inspected or modified was local `salesos_test`. Its `alembic_version` is `q9r0s1t2u3v4`; `alembic heads` against the current checkout reports the same revision as the sole head. The revision file is `salesos/backend/app/alembic/versions/q9r0s1t2u3v4_master_data_schema_reconciliation.py`, based on `q8r9s0t1u2v3`.
- Read-only catalog checks found **195 public tables**, including **30 `md_*` tables**. Final read-only counts: **296,746 companies; 1,124 people; 909,967 source rows; 7 source files; 1,524,717 field-provenance rows; 2,701 review-queue-state rows; 54,185 review candidates**.
- The seven system source files are assigned to the existing sentinel tenant, so the temporary browser tenant correctly saw no tenant-owned imports. The Companies and People pages read the global Master Data population; Entity Resolution had no tenant-owned conflicts, and the CRM pipeline had no tenant opportunities.
- A temporary QA user and tenant were created only in `salesos_test` to exercise authenticated pages. After testing, their account and tenant were deleted along with **19 device sessions** and **19 refresh-token families**. Read-only before/after checks confirmed the Master Data counts above were unchanged. No review disposition was submitted.
- The local migration-drill container was stopped after verification. Its isolated Docker volume was retained. Local API and frontend QA listeners on ports 8001, 8002, and 3000 were stopped. No production database, provider enrichment, Maps scrape, or CRM sync was used.

## Code changes verified

- `salesos/backend/app/modules/master_data/schemas.py`: company/person response schemas now accept the database UUID IDs and serialize them as strings for API responses. This fixed the 500 response on global company/person endpoints.
- `salesos/backend/app/modules/master_data/phase7/review_queue.py`: Short-CR lookup now starts from the 36 review-queue rows and joins source records by the unique source key rather than scanning the large source-row table. Read-only validation found 36 matches and no missing company mapping.
- `salesos/frontend/src/app/v3/review-queue/page.tsx`: P3 and triage use API page/page-size parameters, render all rows returned for that page, expose previous/next controls and visible ranges, and clamp the current page if the queue shrinks. Page size is 100. Short-CR remains a 36-row list.
- Regression tests recorded: response-schema unit tests **2/2 passed**; Short-CR database integration test **1/1 passed**. Targeted ESLint passed. `tsc --noEmit` passed on the isolated QA snapshot; its temporary tsconfig excluded an accidentally copied, incomplete dependency folder. The application tsconfig in the D: checkout was not changed.

## Browser evidence

### Live test API and authenticated session

- Login succeeded against the local test API. The main Data page showed **296,746 companies** and **1,124 people**.
- Companies and People pages returned 200 and rendered 50 data rows plus the table header on the initial page.
- Imports correctly showed the empty state for the temporary tenant (the seven source files belong to the system sentinel tenant).
- Entity Resolution returned 200 and showed the empty state for this tenant. Review Queue returned 200 and exposed the existing queue counts: **2,661 P3 pairs**, **36 short-CR cases**, and **54,185 triage candidates**. The CRM workspace returned 200 and showed an empty tenant pipeline.
- No review buttons were activated, no P0/P1/P2/P3 decision was recorded, and no source/master entity was modified.

### Pagination regression

After the UI change, a Chromium browser test used synthetic API responses to exercise navigation without changing candidate data:

| Queue view | Verified browser result |
|---|---|
| P3 domain-equal batch | Page 1 rendered 100 rows; page 2 rendered the remaining 14 and showed `101–114 of 114` |
| Remaining P3 queue | Page 2 requested 100 rows and rendered its distinct page-2 records |
| P1/P2 triage | Pages 1 and 2 each rendered 100 rows; page 2 requested `page=2` from the API |

The browser test reported **0 page errors**. The Next.js development server compiled the updated review page successfully. Earlier authenticated live-page checks and this later synthetic pagination check are separate evidence: the row counts for page 2 were validated against mocked responses, not by recording any human review action.

## LeadGen provider status

Read-only `leadgen status` at the end of verification reported Google Maps reachable with **2 active jobs**, Scout **OK**, and SalesOS Agent Reach **NOT CONFIGURED** (required base URL, token, and tenant ID absent). No new scrape or enrichment was launched. Minder should remain paused at its Maps wait gate until those jobs finish; configure Agent Reach before the bounded lead-generation pilot.

## Remaining gates

1. The 1,213-row P2 comparison remains assisted evidence only; PO acceptance is still required. The full 54,185-candidate review, suspicious Short-CR decisions, DI P1/P2 methodology confirmation, and Product/PO sign-off remain open. Phase 7 is still **BLOCKED**.
2. Resolve the two existing Maps jobs, configure Agent Reach credentials, then run only the explicitly bounded and approved pilot. Do not send records to SalesOS or external providers before source, consent, cost, and quality gates are accepted.
3. Production remains **NOT APPROVED** pending the existing deployment, backup/restore, hosting-residency, privacy, and human-review gates.
4. This follow-up did not rerun the full frontend build/Jest suite or the complete backend suite. It verified targeted backend tests, the updated TypeScript project, route compilation, live authenticated rendering, and mocked pagination.

## Temporary artifacts and cleanup limit

The automatic command review blocked deletion of the isolated local test-signing key files and two API log files from `%LOCALAPPDATA%\Temp\codex-salesos-test-jwks-20260920` and `%LOCALAPPDATA%\Temp\codex-salesos-qa-api.*.log`. It also blocked removal of the incomplete copied dependency directory and temporary browser harness under `C:\Users\raghe\Documents\Muhide\salesos\frontend\.codex-qa-src`. These are test-only artifacts, not production credentials. The user can remove them after review. No secret values were copied into this report.

## Later frontend verification follow-up — 2026-09-20

This later check supersedes the statement above that the full frontend suite/build was not rerun. It did not replace or repeat the authenticated Master Data checks in this report.

- Reused the preinstalled dependency tree from the C: checkout after confirming its `package.json`, `package-lock.json`, Jest config, and TypeScript config exactly matched the current D: source. The D: volume is FAT32, so the source was copied to a disposable C: temp directory; environment files were excluded and no dependencies were installed.
- `tsc --noEmit`: **PASS**. Full Jest: **318 suites passed, 2,635 passed, 1 skipped**. `next build`: **exit 0**, with **110/110** routes generated.
- A legacy company page emitted a nested-button hydration warning in the full test run. Both modal triggers now use Radix `asChild`; the focused page test and type check passed afterward without that warning.
- A Chrome smoke ran against the standalone Next server after copying `.next/static` and `public` as the checked-in frontend Dockerfiles do. `/`, `/login`, and `/register` rendered; `/v3/companies`, `/v3/data/companies`, and `/v3/sales-dashboard` redirected to `/login`. After network idle there were **0** console/page errors, non-abort request failures, or static-asset failures.
- No authenticated account was used in this smoke; it does not prove live tenant/global data display, NBA decisions, outcome persistence, or telemetry delivery. No database, provider, staging, or production was accessed or modified. The temporary server was stopped. Automatic command review rejected deletion of `C:\Users\raghe\AppData\Local\Temp\SalesOS-frontend-check-20260920`, a source/build copy with environment files excluded and a junction to the existing C: dependencies; no credentials were copied there. The review did not provide a more specific rejection reason. The user may remove this temp folder after review.

## Google Maps lead-source gate — 2026-09-21

Follow-up review of current Google terms classifies the workspace Maps scraper and Places-derived lead-list retention as **not approved for SalesOS**. The current published terms prohibit scraping Maps content for use outside Maps and restrict using Maps Core Services for listings/directories and advertising; Places' indefinite-retention exception is limited to place_id. The Agent Reach proposal classifier now has an explicit regression denying persisted google_maps channel evidence; the focused proposal/security suite passes **60/60**. No Maps provider was called, no database was written, and the previous browser evidence remains scoped to review-only flows. Details and primary links: [report 29](29_GOOGLE_MAPS_PROVIDER_GATE_2026-09-21.md). Roadmap remains **46%** (52/113 last complete census; not re-censused); Phase 7 BLOCKED and production NOT APPROVED.
