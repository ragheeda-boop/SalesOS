# SalesOS Implementation Loop — 2026-09-20

## Status

**Implemented and locally tested; not production-ready.** This loop completed three roadmap slices: persist authenticated product telemetry, turn an actionable NBA into a CRM task, and apply ADR-0113 evidence strength to explicitly classified evidence. The authenticated test-browser follow-up now proves the Company NBA & Outcomes surface through reason-coded rejection, CRM task completion, and outcome capture on `salesos_test`. It also fixed a UI/API completion-route mismatch, sends seller decisions/outcomes to telemetry immediately, and establishes shared Python/TypeScript scoring parity on eight ADR-0113 vectors. Production remains **NOT APPROVED** and Master Data Phase 7 remains **BLOCKED**.

The repository already had a heavily modified working tree. These changes remain uncommitted; this loop did not stage files or change unrelated paths.

## What changed

### 1. Product telemetry

- The frontend tracker now posts through the authenticated SalesOS API client instead of `sendBeacon`, which could not supply SalesOS authentication and CSRF headers.
- `POST /api/v1/analytics/events` now validates a bounded event batch, normalizes the client event names, rejects oversized metadata, pins tenant RLS, and persists the identity from the authenticated request. A payload-supplied `userId` is ignored.
- Active-user reporting now requires a tenant and reads only that tenant's events. Search success can also be correlated from a separate click event by search/query ID.
- Each client event now carries a UUID generated once before transmission. The API accepts this ID and PostgreSQL deduplicates `(tenant_id, client_event_id)` while retaining backward compatibility for older clients that omit it.
- The live Company 360 panel records each recommendation once when the recommendation list is actually displayed. My Day now persists accept/reject decisions; rejection offers the supported reason codes. The Sales Dashboard records completion separately. The previously orphaned Company NBA panel is now reachable as a company-page tab; it records HITL outcomes to the business outcome API. Client event names map to distinct `nba_view`, `nba_accept`, `nba_reject`, `nba_executed`, and `nba_outcome_recorded` storage types; execution no longer inflates acceptance.
- A signed ASGI HTTP check with an isolated RS256 Bearer token verified the real auth dependency chain, tenant claim/header mismatch rejection, ignored payload `userId`, and event persistence under the authenticated user. Replaying the same UUID persisted one event in a tenant; using the same UUID in another tenant was independent. Browser/page-exit delivery remains unverified.

### 2. NBA to CRM task

- An actionable NBA now creates a tenant-scoped task and an `agent_sales_actions` audit record in the same transaction. Deterministic IDs and conflict-safe inserts make database state idempotent on retries.
- Company linkage uses an exact tenant-local name match. Blank or ambiguous names leave the task unlinked.
- Completing an action also completes its linked task. `NO_ACTION` records a skipped audit row without creating a task. “Today” is due today.
- The flow does not send email or WhatsApp and does not create opportunities. A database-backed check on `salesos_test` confirmed retry idempotency, exact company linkage, cross-tenant completion rejection, and same-tenant task/action completion.
- The previously inert Reject control now records the decision and selected reason through the existing HITL feedback API, marks the pending action `skipped`, removes only its same-tenant, incomplete, AI-generated (`source='nba'`) CRM task, records `nba.rejected`, and refreshes the work queue after success. Completed or non-NBA tasks are preserved. The authenticated browser and test-database follow-up exercised this path with a synthetic seller and company.
- The existing Company NBA panel was unreachable and assumed an array response where the API returns `{count, actions}`; its company filter also used the wrong query parameter. The company detail page now exposes it as **NBA & Outcomes**, unwraps the documented response, filters by the selected company, shows loading/error states, and emits outcome telemetry after the outcome API succeeds.
- Three UI callers used `/signal-actions/complete/{id}`, while the backend contract is `POST /signal-actions/complete` with `action_id` in the request body. All three callers now follow the backend contract. An authenticated browser verified HTTP 200 and completed action/task state.
- Seller decisions (`nba.accepted`, `nba.rejected`, `nba.executed`, `nba.outcome_recorded`) now flush immediately; passive exposure and other events remain batched. The authenticated browser received a persisted `nba_executed` event, and targeted Jest cases cover all four immediate event types.

### 3. ADR-0113 evidence strength

- Python and TypeScript now carry explicit evidence kinds, ADR weights, noisy-OR combination, a `0.99` score ceiling, and a `0.45` contradiction cap. Provider/model confidence remains a separate measure.
- Account and Deal Intelligence producers now classify aggregated CRM facts as `crm.system_of_record`, with the tenant CRM entity ID retained as the source ID. The kind has a provisional non-primary weight of `0.55`; multiple factors from the same entity and kind count once, and cannot auto-verify a fact.
- Field policy requires two primary sources for industry, permits one exact primary source for a CR number, and keeps employee count and description in proposed/review status.
- Python persists the kind in the existing evidence JSON column, so this slice needs no schema migration. Typed evidence uses the new scorer; fully untyped legacy evidence retains the old average as an explicitly marked compatibility path.
- TypeScript primary-source counting now uses the same stable source ID rule as Python. A shared JSON vector file now drives both Python and TypeScript tests for eight scoring cases; all outputs match, including evidence count. Field-aware fact decisions still exist only in Python, and evidence producers have not all been classified, so the scorer does not govern every existing fact.

### 4. Test compatibility

- Updated the legacy evidence-chain test helper to use `asyncio.run()`. Under the current Python runtime, the previous `get_event_loop()` helper failed after pytest had cleared the main-thread event loop; product code was not the cause.

## Verification

| Check | Result | Scope |
|---|---|---|
| Focused Python tests | **102 passed** | Telemetry route/service (including distinct accept/reject/execute mapping), NBA task execution and rejection lifecycle, ADR-0113 scoring/persistence, Account/Deal producer classification, HITL service, and evidence-chain regressions |
| Shared ADR-0113 parity | **PASS** | Eight shared JSON vectors match in Python and TypeScript for score, uncapped score, contradiction flag, primary-source count, and evidence count. Latest Python scorer file: **12/12**; TypeScript parity suite: **8/8**. |
| Decision-package custom Jest | **PASS (later run)** | The later three-suite run passes **118/118**. The earlier 134/145 report is superseded; the package no longer has that unresolved test status. |
| Ruff | **Partial** | E4/E7/E9/F/I checks pass on changed telemetry/HITL modules; earlier full telemetry-file scan reports 43 diagnostics, mainly argument-count, magic-value, unused-noqa, and modernization rules. No broad autofix was applied. |
| Python compile check | **Pass** | Changed backend modules |
| `git diff --check` | **Pass** | Whitespace check; Git emitted line-ending conversion warnings for the existing Windows checkout |
| Broader Ruff scan | **Not clean: 226 diagnostics** | Wider legacy/touched modules contain existing lint debt; this loop did not auto-fix unrelated files |
| TypeScript test/build | **PASS (follow-up)** | Reused preinstalled dependencies from a matching `package-lock.json` in an isolated source copy; no packages were installed. `tsc --noEmit` passed; Jest passed **318/318 suites, 2,635 passed, 1 skipped**; `next build` exited 0 and generated **110/110** routes. The temporary standalone trace emitted an `EPERM` symlink warning because its dependencies were linked from the other checkout; production Dockerfiles' static/public copy steps were mirrored for runtime smoke testing. |
| Isolated DB integration | **Pass** | Current checkout invoked against `salesos_test` using `salesos_app` (`rolsuper=false`, `rolbypassrls=false`); task idempotency/completion, RLS tenant isolation, and telemetry persistence passed |
| Rejection cleanup | **PASS (TEST DB + BROWSER)** | Reason-coded rejection was exercised against a synthetic `salesos_test` tenant; action skip and generated-task cleanup are also covered by focused regression tests. |
| Company NBA surface | **PASS (AUTHENTICATED TEST BROWSER)** | Tab is reachable from company details, its response/filter contract matches the API, and synthetic rejection, completion, outcome, and view/execution/outcome telemetry were verified. |
| Authenticated HTTP integration | **Pass** | ASGI HTTP request used a valid RS256 Bearer token signed with a temporary isolated test key; tenant mismatch returned 403, user spoofing was ignored, and event replay deduplicated by client UUID |
| Test database migration | **Pass (TEST ONLY)** | `r1s2t3u4v5w6` adds nullable UUID `client_event_id` and tenant-scoped uniqueness; `salesos_test` is at this head. Production `salesos` was not migrated. |
| Unauthenticated browser routing smoke | **PASS** | Chrome loaded `/`, `/login`, `/register`; protected `/v3/companies`, `/v3/data/companies`, and `/v3/sales-dashboard` redirected to login. The standalone runtime had **0** console/page errors, non-abort request failures, or static asset failures. Authenticated seller coverage is summarized in the separate row below; page-exit telemetry remains open. |
| Authenticated seller browser | **PASS (TEST ONLY)** | Current-source Company NBA & Outcomes page was opened with a synthetic test user. Reason-coded rejection, meeting outcome, and task completion were exercised. Completion returned **200**; the linked CRM task and action were both completed. Browser delivery and `salesos_test` read-back confirmed `nba_view`, `nba_executed`, and `nba_outcome_recorded`. **0** page errors or API failures. This is synthetic test data, not customer or production evidence. |
| Completion contract regression | **FIXED + PASS** | Updated the API helper, Company NBA tab, and Sales Dashboard to send `action_id` in the body expected by the backend; authenticated browser verified the current-source path. |
| Decision telemetry delivery | **PASS (SCOPED)** | Four targeted Jest cases verify immediate flush for accept, reject, execute, and outcome events. Browser + `salesos_test` read-back confirmed a persisted `nba_executed` event for the authenticated user/action. Page-exit reliability remains unverified. |
| Focused verification after browser fix | **PASS** | Guarded backend run: **8/8** tests (HITL seller DB lifecycle, authenticated seller unit tests, and signal-action execution tests). Frontend analytics suite: **11/11**; TypeScript `tsc --noEmit`: **PASS**. The first unqualified pytest invocation stopped at the test-DB safety assertion because local settings named `salesos`; it did not connect or write. The passing run explicitly targeted `salesos_test` and verified owner `salesos` / app `salesos_app`. |

## Database safety and cleanup

- Ran the current action and telemetry code against the explicitly selected `salesos_test` database under the non-superuser, non-BYPASSRLS application role. Confirmed one task/action after retry, authenticated telemetry identity, rejection of a wrong-tenant completion, successful same-tenant completion, reason-coded rejection, outcome capture, and browser completion of the linked task.
- The HTTP telemetry check used a new RS256 key in a temporary directory because the local test process could not decrypt the repository's configured signing key. The temporary key directory was removed; the existing JWKS key files were not changed.
- Deleted only the synthetic browser-test tenant, company, seller, task/action/outcome/feedback/follow-up rows, telemetry, device sessions, and refresh-token families from `salesos_test`. Read-back showed **zero** remaining rows for that tenant/user/company. No write was made against `salesos` or production.
- An attempt to start the compose PostgreSQL service could not bind port `6432` because the existing PgBouncer owns that port. The failed, newly created PostgreSQL container and its empty volume were removed. Existing SalesOS containers were left running.

## Remaining acceptance gates

1. The authenticated browser now proves recommendation exposure, reason-coded rejection, task completion, outcome capture, and execution telemetry on synthetic test data. Remaining proof: run the browser path for acceptance, confirm browser persistence for accept/reject telemetry, validate page-exit/retry delivery, and add override-event semantics. A design-partner run and revenue attribution remain future gates.
2. Eight shared golden vectors now prove Python/TypeScript scorer parity. The remaining decision-integrity gate is field-policy/write-boundary alignment, classifying all producers, and preserving the explicit legacy compatibility boundary.
3. Classify evidence kinds at the actual evidence producers and connect field decisions to the canonical write boundary. Keep legacy average scoring clearly marked until migration is complete.
4. Continue beyond the now-proven synthetic browser loop with accepted partner data, then tie reviewed outcomes to opportunity/revenue attribution. Do not promote Master Data to production or unblock Phase 7 until its existing human and Product/PO gates are satisfied.
5. The separate decision-package Jest suite now passes 118/118 in the later §58 run. Keep production decisions blocked on the product, human-review, and operational gates already listed above.

### Mixed typed/legacy evidence compatibility — 2026-09-20

- Found that `Insight.recompute_confidence()` scored only typed evidence when an insight mixed ADR-0113 items with legacy untyped items. This silently excluded evidence and could overstate confidence.
- Changed the branch so ADR-0113 is used only when **all** evidence items have an explicit kind. Untyped or mixed evidence uses the complete historical average and keeps `legacy_average_compatibility` in metadata. The contradiction marker is cleared on that compatibility path.
- Added a regression covering one typed and one untyped evidence item. Focused suite `tests/unit/test_evidence_scoring_adr0113.py`: **12/12 PASS**.
- The separate decision-package run documented above is superseded by the later run in §58: **3 suites / 118 tests PASS**. This does not close producer classification, canonical write-boundary enforcement, freshness, or point-in-time semantics.
- No database, provider, or deployment writes. Roadmap remains **46% (last full census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

### Agent Reach command and permission hardening — 2026-09-20

- Replaced `create_subprocess_shell` with `create_subprocess_exec` and argument arrays for every provider command. The executable is checked against an allowlist; embedded shell metacharacters remain ordinary argument text. Timed-out children are killed and reaped. The process-local rate limiter is now shared across service instances rather than recreated per request.
- RSS now resolves the host, rejects any non-public DNS answer, and pins curl to one verified IP with `--resolve`; curl config, proxies, and redirects are disabled. The feed is parsed in-process. Direct X/Twitter and YouTube URL fetches now require HTTPS and official provider hostnames. GitHub repository reads validate the `owner/name` identifier format.
- Every external-provider POST now requires `agent_reach.CREATE`; status and intelligence reads remain `READ`, while clearing/pruning require `DELETE`.
- Added the shared API rate-limit dependency using the configured search limit (30/min by default), keyed by tenant/user and backed by Redis when available, with the project's in-memory fallback. The separate provider runner retains its shared per-worker channel cap.
- Verification: Agent Reach security, contact-enrichment, and parallel contact-enrichment tests **134/134 PASS**; Python compile and Ruff E9/F checks **PASS**. Tests cover private DNS rejection, address pinning, redirect behavior, official URL host allowlists, route permissions, API rate-limit configuration, shell-argument safety, and executable allowlisting.
- **Integration remains disabled:** the Agent Reach router is not registered in `app/boot/routers.py`. Monthly/tenant-wide provider spending budgets and the configured roles/credentials have not been validated. No provider request or database write was made; Maps still has 2 active jobs and LeadGen Agent Reach credentials are absent.
- Roadmap remains **46% (last full census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

### Agent Reach tenant evidence and signal persistence — 2026-09-21

- Removed the implicit write from `AgentReachService.research_company()` into a process-global in-memory store. The service now returns provider results; tenant-aware persistence stays at the authenticated API boundary.
- The research route persists successful evidence through the tenant-pinned Postgres store, derives deterministic first-pass signals from those evidence items, and persists the signals under the same tenant.
- Evidence insertion now preserves the evidence UUID and returns the canonical database row ID on both a fresh insert and a dedup hit. Derived signal `evidence_ids` therefore refer to the stored evidence row, including when an identical item already exists.
- The response reports newly inserted evidence and signals separately. Failed channels are excluded from persistence.
- Verification: Agent Reach security, contact-enrichment, and parallel-enrichment suites **137/137 PASS**; Python compile, Ruff E9/F, and scoped `git diff --check` **PASS**. New tests cover tenant-scoped evidence/signal calls, canonical evidence-ID linkage, dedup lookup behavior, and absence of the old process-global write.
- Database/provider/deployment writes were not performed. The SQL persistence behavior was exercised with a mocked session, not a live PostgreSQL integration. Agent Reach router remains unregistered pending spending budgets, role/credential checks, and the full security gate.
- Roadmap remains **46% (last full census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

### Agent Reach URL and research-request validation — 2026-09-21

- Replaced legacy private-IPv4 regex checks with parsed IP classification. Rejects non-global IPv4/IPv6, legacy decimal/octal/hex IP spellings, localhost/local/internal suffixes (including a trailing root dot), URL credentials, malformed IDNs, control/space/backslash characters, and non-default ports.
- Research requests now accept only the five implemented channels, require at least one, reject duplicates, and cap the request at five channels. This prevents unknown channels from silently producing an empty successful research response.
- Verification: Agent Reach security, contact-enrichment, and parallel-enrichment suites **154/154 PASS**; Python compile, Ruff E9/F, and scoped diff checks **PASS**. Added 12 direct URL-denial cases, a public HTTPS acceptance case, and request-channel validation cases.
- No provider, database, or deployment write. RSS still adds DNS resolution and IP pinning before curl; this parser check alone does not replace that network-level protection.
- Roadmap remains **46% (last full census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

### Agent Reach streamed process-output cap — 2026-09-21

- Fixed the subprocess limit so stdout and stderr are read incrementally with a 1 MiB cap per stream. The prior code truncated only after `communicate()` had already buffered all output in memory.
- If either stream exceeds the cap, the provider process is killed and the request returns a bounded-output error. Timeout and request cancellation also kill and reap the child process.
- Verification: Agent Reach security, contact-enrichment, and parallel-enrichment suites **156/156 PASS**. Added mocked subprocess cases for argument safety, oversized output termination, and timeout cleanup. Compile, Ruff E9/F, and whitespace checks are included in the final scoped verification.
- No live provider, database, or deployment was used. Roadmap remains **46% (last full census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

### Agent Reach live persistence proof — 2026-09-21

- Added `tests/integration/test_agent_reach_tenant_persistence_db.py`. It constructs a separate connection URL fixed to `salesos_test`, verifies `current_database()`, and requires an application role that is neither superuser nor `BYPASSRLS` before writing.
- The integration test inserted a synthetic tenant/company evidence row, confirmed a duplicate resolves to the same canonical database UUID without another insert, persisted a signal referencing that UUID, and read both rows back through tenant-pinned queries.
- Cleanup removed the synthetic records and read-back confirmed both scoped result sets were empty. The test passed **1/1**; no connection or write was made to `salesos`.
- This closes live PostgreSQL persistence proof for the Agent Reach evidence/signal path. Router registration remains gated on provider spending budgets, role grants, credentials, and end-to-end provider/security acceptance.
- Roadmap remains **46% (last full census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

## Files in this loop

- Telemetry and seller decisions: `salesos/frontend/src/lib/analytics.ts`, `salesos/frontend/src/lib/__tests__/analytics.test.tsx`, `salesos/frontend/src/features/company-intelligence/widgets/company-360/DecisionPlatformPanel.tsx`, `salesos/frontend/src/app/v3/{my-day,sales-dashboard}/page.tsx`, `salesos/frontend/src/app/v3/companies/[id]/{page.tsx,company-nba-tab.tsx}`, `salesos/backend/app/routers/analytics.py`, `salesos/backend/app/modules/telemetry/{models.py,repository.py,service.py,router.py}`, `salesos/backend/app/modules/signal_actions/hitl_service.py`, migration `salesos/backend/app/alembic/versions/r1s2t3u4v5w6_telemetry_event_idempotency.py`, and telemetry/HITL unit tests.
- CRM action: `salesos/backend/app/modules/signal_actions/{actions.py,router.py}` and `salesos/backend/tests/unit/test_signal_action_execution.py`.
- Evidence scoring and producers: `salesos/backend/domains/commercial/evidence/`, `salesos/backend/intelligence/{account_intelligence.py,deal_intelligence.py}`, `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py`, `salesos/packages/platform/decision/`, shared vectors `salesos/packages/platform/decision/evidence-engine/adr0113-golden.json`, and `docs/adr/0113-evidence-architecture.md`.
- Agent Reach: `salesos/backend/app/modules/agent_reach/{service.py,router.py,persistence.py}`, `salesos/backend/tests/unit/test_agent_reach_security.py`, and `salesos/backend/tests/integration/test_agent_reach_tenant_persistence_db.py`; includes command/URL validation, tenant-scoped evidence and signal persistence, and bounded research channel requests.
- Focused route and scorer tests: `salesos/backend/tests/unit/test_client_analytics_events.py`, `salesos/backend/tests/unit/test_evidence_scoring_adr0113.py`, and `salesos/backend/tests/unit/test_intelligence_evidence_classification.py`.
- Frontend follow-up: `salesos/frontend/src/app/(dashboard)/companies/[id]/page.tsx` uses `ModalTrigger asChild` to prevent nested-button hydration warnings; `signalActions.ts`, Company NBA, Sales Dashboard, and `analytics.ts` contain the completion-contract and immediate telemetry fixes. Frontend verification and browser evidence are recorded above.
- Roadmap reconciliation: [24_SALESOS_ROADMAP_CAPABILITY_MATRIX_2026-09-20.md](24_SALESOS_ROADMAP_CAPABILITY_MATRIX_2026-09-20.md).

## Recommendation-confidence contract — 2026-09-20

- Found a semantic defect in `salesos/packages/platform/decision/recommendation-engine/index.ts`: it returned action-fit score as recommendation confidence. For zero-confidence input scores, the selected `research` action could therefore be labeled high-confidence even though its inputs were untrusted.
- The TypeScript decision-platform twin now calculates confidence from action-specific input `Score.confidence` values, capped by the action-fit score. Alternative recommendations use the same confidence meaning; their explanation no longer describes action fit as “lower confidence.” The regression test now expects `research` with confidence `0` and a low label when its only relevant input has no confidence. A positive-confidence case checks the high-confidence path.
- Verification: the package's three Jest suites **118/118 PASS**; direct TypeScript compile of `recommendation-engine/index.ts` **PASS**. `domains/decision_center/tests/test_decision_center.py` **51/51 PASS** (in-memory/unit suite; no DB fixture requested).
- Scope limit: `salesos/packages/platform/decision/README.md` explicitly marks this TypeScript twin as lab-only and not the frontend package resolve target. The governed Decision Center ledger still receives confidence from its decision producer/ensemble path; producer lineage and customer calibration remain open. This change does not alter frontend/GA behavior.
- No database/provider/deployment writes. Overall roadmap percentage remains at the previous formal census of **46% (52/113)**; this batch did not re-census every capability row. Phase 7 remains BLOCKED and production remains NOT APPROVED.

## Page-exit telemetry reliability — 2026-09-20

- The tracker previously drained its queue into a normal Axios/XHR request on `pagehide`, which a browser can cancel during navigation. It now warms the CSRF cookie during tracking and sends queued and still-unconfirmed in-flight events through Axios Fetch `keepalive`, retaining the same event IDs. Request interceptors still add Bearer, tenant, and CSRF headers; `sendBeacon` is not used because it cannot carry those headers.
- Failed normal deliveries are placed back in the queue for interval retry. When `pagehide` races an in-flight request, the same event IDs are resent; the backend's unique `(tenant_id, client_event_id)` constraint makes that retry idempotent.
- Verification: analytics Jest **15/15 PASS**, including CSRF warmup, queued pagehide delivery, in-flight resend, and a failed-send retry with the same ID. The full frontend Jest regression passes **318/318 suites; 2,643 passed, 1 skipped**. An isolated TypeScript check of the analytics module's client/CSRF contract and Axios 1.18.1 `{ adapter: "fetch", fetchOptions: { keepalive: true } }` config also passes.
- Full frontend `npm run typecheck` could not be completed with the reused dependency tree: several `@types/*` files under `node_modules.incomplete-codex-20260920` are syntactically truncated. An earlier temporary mirror also included the wrong lab `packages` tree; it was not used as product evidence. The corrected mirror matches the checked-out `package-lock.json`; the focused Jest test passes. No dependency was installed or changed.
- No authenticated browser/page-exit DB read-back was run in this slice. Acceptance/rejection telemetry read-back, page-exit persistence, and real partner usage remain open. Provider status remains Maps **2 active jobs**, Scout **OK**, Agent Reach **not configured**. No database/provider/deployment write.
- Overall roadmap percentage remains at the last complete census of **46% (52/113)**; this slice did not re-evaluate the full capability denominator. Phase 7 remains BLOCKED; production remains NOT APPROVED.

## Evidence field-decision guard — 2026-09-21

- Reconciled a safety conflict between ADR-0113 and ADR-0114: a strong CR source qualifies the evidence band, but `cr_number` is an identity field that agents may not auto-apply. A VERIFIED CR candidate is retained only for human review.
- `decide_fact()` now rejects identity/control fields, fails closed when any evidence item is unclassified, and auto-applies only fields explicitly listed in the ADR-0114 enrichment allowlist. Unknown fields can be retained as review proposals but cannot auto-apply.
- Regression: `tests/unit/test_evidence_scoring_adr0113.py` **14/14 PASS**. Ruff E9/F and Python compile checks pass.
- Repository audit found no `FactRecorder`, canonical fact tables, or production call site for `decide_fact()`. This closes a decision-policy defect, not the canonical write integration. Ownership/dismissal checks, proposal persistence/UI, producer classification, and freshness/point-in-time policy remain open.
- No database/provider/deployment writes. Roadmap remains **46% (last complete census: 52/113)**; no full re-census in this focused slice. Phase 7 remains BLOCKED; production remains NOT APPROVED.

## Evidence producer boundary — 2026-09-21

- Producer inventory confirmed Account/Deal Intelligence is the only inspected commercial evidence producer that assigns ADR-0113 kinds. Grounded Research EvidencePack, Agent Reach channel evidence, and the alternate decision engine use separate contracts; their source semantics do not justify automatic conversion into commercial fact evidence.
- `ReasoningPipeline.conclude()` previously wrapped its own generated summary as an `EvidenceItem` with confidence `0.8`. Removed that self-citation; the summary remains in `analysis`, its origin remains `sources=["llm_reasoning"]`, and the evidence list is empty unless independently sourced evidence is supplied. Schema descriptions now state model-reported confidence is informational only.
- Regression: ADR-0113 and reasoning suites **25/25 PASS**; Ruff E9/F and Python compile checks pass.
- Remaining: classify each producer at its true source boundary, expose evidence provenance to users, and only connect to a governed writer after the FactRecorder/HITL and temporal contracts exist. No database/provider/deployment writes.
- Overall roadmap remains **46% (last complete census: 52/113)**. Phase 7 remains BLOCKED; production remains NOT APPROVED.

## Human approval identity and tenant boundary — 2026-09-21

- Found `approval.py` reading `request.state.user_id`, although no middleware in the application sets it. Creation therefore fell back to `system`; approval decisions could fail with 401. Both create and decide routes now depend on `get_current_user_id`, which derives the actor from the verified JWT.
- Approval get/approve/reject/escalate/cancel methods now accept an optional tenant scope and hide cross-tenant IDs as not found. HTTP get and decision routes pass the authenticated tenant; cross-tenant decision attempts do not mutate the pending request.
- Stabilized the legacy synchronous ApprovalService test helper with `asyncio.run`, so synchronous tests can run in the same process after async route tests.
- Company REST and GraphQL create/update paths now pass the verified user ID into `AuditTrail.performed_by`. Focused tests verify route dependency wiring and service actor persistence.
- Verification: approval route/service + evidence chain/scoring/producer/reasoning + company actor suites **74/74 PASS**; Ruff E9/F, compile, and diff checks pass.
- Architecture boundary: `domains/ubom` is explicitly deprecated. The active target is tenant CRM `Company`/`Contact`. The generic `approval_requests` table cannot replace canonical fact/evidence ledgers and does not apply approved facts transactionally. Other service/bulk paths and field-level ownership semantics still lack unified actor provenance; no auto-apply writer was added.
- No database/provider/deployment writes. Roadmap remains **46% (last complete census: 52/113)**; Phase 7 remains BLOCKED and production remains NOT APPROVED.

## Frontend verification follow-up — 2026-09-20

- The D: working copy is on FAT32 and cannot host a dependency junction. To avoid installing packages or changing the source checkout, copied the current frontend source into a temporary C: directory and reused the already installed dependency tree from the C: checkout after verifying that `package.json`, `package-lock.json`, Jest config, and TypeScript config match exactly. The temporary copy excluded environment files and generated artifacts.
- `npm run typecheck`: **PASS**. Full Jest: **318 suites passed; 2,635 tests passed, 1 skipped**. Next.js production build: **exit 0**, compile/type validation passed, **110/110** routes generated.
- The build emitted an `EPERM` warning while copying the linked dependency tree into `.next/standalone`; the checked-in Dockerfiles explicitly copy `.next/static` and `public`. The browser check used the standalone server after mirroring those two Dockerfile copy steps. No Docker image was built.
- Browser smoke: `/`, `/login`, and `/register` rendered; `/v3/companies`, `/v3/data/companies`, and `/v3/sales-dashboard` redirected unauthenticated visitors to `/login`. After network idle there were **0** console/page errors, non-abort request failures, or failed static assets.
- The full Jest run surfaced invalid nested buttons on a legacy company page. Updated both modal triggers to use `asChild`; its focused test and the full TypeScript check passed afterward with no nested-button warning. Jest also prints non-failing React `act(...)` warnings from the existing `ContextualInsightsProvider` tests; the browser smoke had no console errors.
- This follow-up did not log in, access business data, call providers, or access/write any database. The temporary local server was stopped. Automatic command review rejected deletion of `C:\Users\raghe\AppData\Local\Temp\SalesOS-frontend-check-20260920`; it contains a source/build verification copy with environment files excluded, plus a dependency junction to the existing C: install. No production credentials were copied there. No deployment, staging, commit, or staging-index action occurred. The automatic review provided no more specific reason for rejecting cleanup.

## Canonical fact ledger schema — 2026-09-21

- Added SQLAlchemy models and Alembic revision `s2t3u4v5w6x7` for tenant-scoped `evidence_records`, `canonical_facts`, `fact_evidence`, and `canonical_fact_events`. The revision is the sole migration head after the existing 113 revisions.
- Added same-tenant composite foreign keys, status/subject/score constraints, idempotency and duplicate-open-proposal indexes, a persistent dismissed-value uniqueness guard, and FORCE RLS on all four tables. Added these tables to the tenant RLS source inventory and the Alembic metadata registry.
- Schema/RLS tests: **7/7 PASS**. Ruff E9/F and compile checks pass. The new migration's isolated PostgreSQL offline rendering produced all four tables and four ENABLE/FORCE RLS pairs.
- At this schema-only checkpoint, no database migration had yet been attempted. The later implementation entry below records the successful online test-only upgrade; full-chain `alembic upgrade head --sql` remains blocked by pre-existing revision `0028_enrichment_performance.py`, which calls `inspect()` against Alembic's offline `MockConnection`. Auto-apply is not enabled.
- No provider, production, or test-database writes; no commit or staging. Phase 7 remains BLOCKED; production remains NOT APPROVED. Overall roadmap remains **46% (last full census 52/113)**.

## Proposal-only FactRecorder — 2026-09-21

- Implemented `FactProposalService` in `app/modules/facts/service.py`. It validates tenant GUC equality, a tenant-owned Company/Contact subject, the explicit ADR-0114 field allowlist, non-null JSON values, recognized evidence kinds, evidence-score storage policy, actor shape, and idempotency fingerprints before writes.
- Persistence records evidence snapshots, a `PROPOSED` canonical fact, evidence links, and a `PROPOSED` event in the caller's transaction. PostgreSQL `ON CONFLICT DO NOTHING` supports exact retries and handles concurrent uniqueness races. The service does not commit and has no Company/Contact update path. Changed-payload key reuse, concurrent/open duplicate values, and dismissed values fail closed.
- Proposal and reviewer focused scoring/service/schema/RLS scope: **38/38 unit tests PASS**. `tests/integration/test_fact_proposal_service_db.py`: **1/1 PASS** against actual PostgreSQL `salesos_test` using the configured application role (`rolsuper=false`, `rolbypassrls=false`).
- Applied Alembic `s2t3u4v5w6x7` from `r1s2t3u4v5w6` to `salesos_test` only. Verified current revision, 4/4 RLS-enabled+forced tables, and 4/4 tenant policies. Integration temporary tenant/fact/evidence counts are **0** after rollback. No production database was written.
- Remaining after this entry: connect a trusted proposal/review API caller, enforce authenticated reviewer permissions at the route, and establish ownership/freshness policy. CRM fields are not auto-applied. Full-chain offline SQL remains blocked by pre-existing revision `0028_enrichment_performance.py`; online upgrade from the current test head passed.
- No staging or commit. Phase 7 remains BLOCKED; production remains NOT APPROVED. Roadmap remains **46% (last full census: 52/113)**.

## FactRecorder human review transition — 2026-09-21

- Added `app/modules/facts/review_service.py`. It permits only `PROPOSED → APPROVED | REJECTED | DISMISSED`, checks tenant GUC equality, locks the fact row, records reviewer/reason/timestamp, and appends one `REVIEW_DECIDED` event. Exact same-review retries are idempotent; conflicting reviewer decisions fail closed.
- Expanded the PostgreSQL integration proof to exercise approval and dismissal, verify one decision event after retry, reject a conflicting decision, block re-proposal of a dismissed value, and confirm `Company.city` remains unchanged. The test used `salesos_test` with `salesos_app` (`rolsuper=false`, `rolbypassrls=false`) and rolled back all rows.
- Verification at this service-only checkpoint: **38/38 focused unit tests + 1/1 PostgreSQL integration test PASS**; Ruff E9/F, `compileall`, and `git diff --check` pass. The following API entry supersedes the then-open route item.
- No production/test residue, provider, deployment, staging, or commit action. Phase 7 remains BLOCKED; production NOT APPROVED; roadmap **46% (last full census: 52/113)**.

## FactRecorder authenticated review API — 2026-09-21

- Added `app/modules/facts/router.py` and registered it in `app/boot/routers.py`. `GET /api/v1/facts/proposals` provides bounded, tenant-scoped proposal/evidence listing. `POST /api/v1/facts/{fact_id}/decision` accepts only approve/reject/dismiss plus a required reason.
- Added `POST /api/v1/facts/proposals` for manual human proposals under `master-data-review:CREATE`. The actor is fixed to `human` and taken from the verified JWT subject; client-supplied actor metadata is rejected. The endpoint is admin-gated by the existing permission matrix.
- The routes require `master-data-review:READ/UPDATE`; reviewer identity is injected from the verified JWT dependency; tenant is resolved by the existing tenant dependency and revalidated against `app.tenant_id` in the service. Rate limiting is enabled. Human proposers cannot review their own facts. The response explicitly states `crm_applied: false`.
- Added router contract tests for pagination/evidence response, actor attribution, spoof rejection, CRM non-application, and route permission dependencies. App OpenAPI smoke confirms all three operations are registered. The PostgreSQL ASGI proof overrides auth/RBAC dependencies; it verifies handler-to-DB behavior, not JWT verification or live permission execution.
- Verification: **44/44 focused unit tests PASS**, including HTTP contract tests; PostgreSQL integration **1/1 PASS**; Ruff E9/F and compile pass. `salesos_test` still has the same single Alembic head, all four FORCE-RLS tables/policies, and zero test fixture residue.
- Remaining: Minder/Agent Reach proposal producer integration and review UI, tenant role acceptance, ownership/freshness/supersession policy, and a separate approved-fact transactional CRM apply boundary. The API is not an auto-apply path. No production DB, provider, deployment, staging, commit, or staging-index change. Phase 7 BLOCKED; production NOT APPROVED; roadmap **46% (last full census: 52/113)**.

## Fact Review V3 screen — 2026-09-21

- Added the internal route `/v3/fact-review` with status filtering, evidence/source display, required reviewer reason, approve/reject/dismiss actions, pagination, 403-specific permission state, and an explicit CRM non-application message. Linked it from the existing internal Phase 7 review queue; customer navigation remains unchanged.
- Added frontend query wrappers and two API-client unit cases for tenant header, request paths, decision/reason payload, and encoded fact IDs.
- Verification is pending: frontend dependency installation is still running from the locked `package-lock.json`; TypeScript, Jest, build, and browser checks have not passed yet. The existing incomplete dependency directory was preserved; source files and lockfile were not changed by installation.
- The UI is not release-ready until frontend checks and browser QA pass. No production DB, provider, deployment, commit, or staging. Phase 7 BLOCKED; production NOT APPROVED; roadmap remains **46% (last full census: 52/113)**.

## Fact Review V3 verification follow-up — 2026-09-21

- Stopped the locked `npm ci` attempt on D: before disk pressure: the FAT32 volume had about 1.1 GB free and the reification had created a large partial dependency tree without producing TypeScript/Jest launchers. The lockfile was unchanged. Automatic command review rejected deletion of that partial `salesos/frontend/node_modules`, so it remains; the pre-existing `node_modules.incomplete-codex-20260920` also remains untouched.
- Reused the existing isolated C: frontend verification copy only after SHA-256 equality for `package.json`, `package-lock.json`, `jest.config.js`, and `tsconfig.json`; copied the five changed/new Fact Review source/test files and verified their hashes. No environment files or credentials were copied.
- Focused TypeScript check (`tsc --noEmit -p tsconfig.fact-review.json`) **PASS** for the Fact Review page/client and transitive imports. Full `npm run typecheck` **FAILS with 88 diagnostics** in existing decision-platform/revenue-execution contracts and screens; the error log contains zero diagnostics in `fact-review` or `factReviewQueries`. A project-wide typecheck/build pass is not claimed.
- Focused Jest: **2/2 suites, 5/5 tests PASS** (page states/interactions and tenant-scoped API-client contract).
- Chromium smoke against local Next dev: `/v3/fact-review` returned **HTTP 200**, rendered proposal/evidence, accepted a reasoned approval using a synthetic API response, and rendered the reviewer state. **0** console/page errors or failed API requests. This was a mocked frontend flow with a synthetic token; it does not prove live JWT/RBAC or backend persistence. The local server was stopped; screenshot retained in the C: temp verification folder.
- No production/test-database writes occurred during frontend verification; no provider, deployment, commit, or staging. `git diff --check` passes; staging index is empty; working tree remains not clean. Phase 7 BLOCKED, production NOT APPROVED, roadmap remains **46% (last full census 52/113)**.

## Manual Fact Proposal Evidence Classification — 2026-09-21

- Review found the authenticated human proposal endpoint accepted a client-supplied `evidence_kind`; that could inflate the score of a self-described source before a second reviewer saw it.
- The route now replaces every human-submitted evidence class with `CITED_CLAIM` and descriptive confidence with `UNKNOWN` before `FactProposalService` scores or persists it. The client-supplied numeric confidence remains descriptive only and does not affect ADR-0113 scoring. Trusted internal sources need a separate verified producer/classifier path.
- Verification: Fact ledger/proposal/review/router plus ADR-0113 scoring unit scope **40/40 PASS**; PostgreSQL integration **1/1 PASS** on `salesos_test`. The integration submits `OFFICIAL_REGISTRY` and confirms persisted `CITED_CLAIM`, score **0.40**, POSSIBLE band, `UNKNOWN` confidence, and transaction rollback. Ruff E9/F and compile pass.
- The route remains proposal-only; review approval still cannot update CRM. No provider, production DB, deployment, commit, or staging. Phase 7 BLOCKED; production NOT APPROVED; roadmap remains **46% (last full census 52/113)**.

## Decision contract repair and full frontend verification — 2026-09-21

- Reconciled the shared TypeScript decision contract with its real consumers instead of adding legacy aliases: consumers now use `decisionId`, nested `recommendation`, `Explainability.expectedImpact`, `Feedback.timestamp`, and `DecisionHistoryItem.createdAt`. Score/evidence display categories are explicitly typed; ADR-0113 `EvidenceKind` trust classes are unchanged. Provider/scoring registries are partial so a display category does not imply a registered provider or score algorithm.
- The decision tests uncovered a behavior defect: missing data alone made both research and nurture appear as high-confidence actions. Both now require matching evidence text; absent actionable evidence keeps the conservative low-confidence nurture fallback. The decision package regression passes **94/94**, including one positive test per evidence-gated action and the no-signal fallback.
- Full frontend `npm run typecheck` passes with zero diagnostics in the current-source verification copy. `npm run build` exits **0** after compile, lint, and type validation and generates **111/111 routes**. In the C: mirror, Next prints a non-fatal `EPERM` while tracing the linked `node_modules` for `.next/standalone`; build exit remains 0. The changed project files were synchronized back to D: and SHA-256 checked.
- Fact Review remains proposal/review only. Focused frontend Jest **5/5**, focused TS, and mocked Chromium HTTP 200/interaction pass; this does not verify a real JWT/RBAC browser session. The manual proposal API evidence is normalized to `CITED_CLAIM` / `UNKNOWN`; backend tests **40/40 + 1/1** `salesos_test` PostgreSQL integration pass.
- `git diff --check` passes. No production DB, provider, or deployment write; no staging or commit. No full roadmap census was run, so the percentage stays **46% (last census 52/113)**. Phase 7 remains **BLOCKED** and production remains **NOT APPROVED**.

### Next proof gates
1. Verify Fact Review under a real JWT and tenant role in the isolated test app/database, including permissions and row isolation.
2. Connect Minder/Agent Reach only through a trusted source classifier and proposal service; retain review-only boundaries.
3. Define field ownership, freshness, supersession, and conflict policy before implementing atomic approved-fact CRM apply.
4. Resolve remaining human gates: 54,185 Phase 7 candidates, DI P1/P2 methodology, PO sign-off, and production/hosting/backup/provider requirements.



## Corrected full frontend verification — 2026-09-21

- The first C: run mapped `@salesos/decision-platform` to the root lab package. Those results are superseded; this did not change the frontend STUB or enable decision runtime behavior.
- Re-synchronized and SHA-256 verified the corrected mirror against D:: **1,024/1,024 `frontend/src` files** and **230/230 frontend package files** match. The temporary TS/Jest alias points to a separate copy of the actual frontend STUB; its source, package metadata, and public test match D:. `package.json` and `package-lock.json` match and were not changed.
- Full TypeScript: `npm run typecheck` **PASS, zero diagnostics**. Full Jest: **323/323 suites PASS; 2,768 passed, 1 skipped**. This includes the frontend STUB's actual public test and three isolated root-lab decision suites.
- Decision lab independently: **3/3 suites, 120/120 tests PASS**, covering evidence-gated research/nurture behavior, integration, and ADR-0113 scoring parity. Its HTTP decision evaluator is injected locally by the integration fixture and cleared after each test.
- Next build: **exit 0**, compilation/type validation pass, **111/111 routes generated**. Non-fatal warnings: Node reinterpreted the Tailwind preset as ESM after CommonJS parsing, and standalone tracing could not follow the linked `node_modules` symlink (`EPERM`).
- D: has no usable `tsc` launcher because dependency installation was stopped before disk pressure; verification used the hash-matched C: mirror. This turn made no database, provider, or deployment writes.
- NBA feedback now uses `decisionId ?? id` and the UI keeps optimistic accepted state via a local UI type extension. This preserves feedback UX while `frontend/packages/platform/decision` remains an explicit STUB.
- `git diff --check` passes; no staging or commit. The worktree remains broadly modified. Phase 7 BLOCKED; production NOT APPROVED; roadmap **46%** (last complete census 52/113; not re-censused).

### Next proof gates

1. Verify Fact Review with a real signed JWT and tenant role against `salesos_test`, including permission and tenant-row isolation.
2. Add trusted Minder/Agent Reach producer identity and evidence classification through the proposal service; keep human review and no-CRM-auto-apply boundaries.
3. Define field ownership, freshness, supersession, and conflict policy; then prove a separate atomic approved-fact CRM apply.
4. Complete the Phase 7 candidate reviews, DI P1/P2 confirmation, and PO sign-off. Partner, provider, hosting, backup, and production gates remain independent.


## Signed JWT/RBAC Fact Review integration — 2026-09-21

- Added a second `salesos_test` PostgreSQL integration that uses actual RS256 access-token creation/decoding, `TenantContextMiddleware`, `get_current_user_id`, `get_current_tenant_id`, database-backed user-role lookup, `PermissionEnforcer`, and per-request tenant GUC/RLS. Only rate limiting and the session factory are replaced by test fixtures; auth and permission checks are real.
- Verified anonymous `401`, ordinary-user READ/CREATE `403`, mismatched header/token tenant `403`, and two admins each seeing only their own proposal rows. API-created human proposals use the JWT subject, normalize claimed official-registry evidence to `CITED_CLAIM` / `UNKNOWN`, and cannot be reviewed by their author; a second admin can review. `crm_applied=false` and the Company row stays unchanged.
- Test signing keys are generated under pytest `tmp_path`, not the application's JWKS directory. Every inserted tenant/user/company/fact/evidence/event row is inside the test's outer transaction and rolled back. Both integration tests assert `salesos_test`, `rolsuper=false`, and `rolbypassrls=false`.
- The integration exposed a retry bug: proposal and review event timestamps can tie under PostgreSQL's transaction timestamp. `FactReviewService` now filters the retry lookup to `REVIEW_DECIDED` and uses an ID tie-breaker, preserving exact retry idempotency.
- Verification: **40/40** focused Fact Review/proposal/schema/ADR-0113 unit tests, **2/2** PostgreSQL integration tests, full Ruff on the changed integration file, Ruff E9/F on the review service, and Python compile pass. No persistent test residue.
- This closes the backend signed-auth/permission/RLS proof. A browser session against the running API remains open. Next: real browser flow, trusted Minder/Agent Reach producer boundary, canonical ownership/freshness policy, and the independent approved-fact CRM apply design. No production/provider/deployment writes, staging, or commit; Phase 7 BLOCKED; production NOT APPROVED; roadmap **46%** (last census 52/113).

## Loop 2026-09-21 — browser redirect and stale API runtime

- Started a temporary source-matched frontend and checked `/v3/fact-review`; middleware redirected to login with `callbackUrl`. No test account or credentials were present, so no login was attempted.
- Fixed the post-login destination mismatch: login now accepts middleware `callbackUrl`, keeps legacy `next`, and uses a same-origin URL check. Added focused unit coverage.
- TypeScript: **0 diagnostics**. Full frontend Jest: **324/324 suites**, **2,776 passed / 1 skipped**. Optimized build: exit 0, **111/111 routes**; Windows standalone tracing still warns on a linked `node_modules` symlink (`EPERM`).
- Added an OpenAPI registration contract and verified **1/1** against D source. The API at `localhost:8000` is a separate 2026-09-05 container checkout whose OpenAPI lacks Fact Review and whose DB target is `salesos`; no restart or write was attempted.
- Started a temporary API process from D source on port 8001 with lifespan disabled and a placeholder `salesos_test` DSN. OpenAPI included Fact Review and anonymous GET returned **401** before PostgreSQL access; stopped the process.
- Authenticated browser-to-current-API proof remains open. Next, run isolated current-source API/browser proof against `salesos_test`, then continue trusted Minder/Agent Reach producer identity, canonical ownership/freshness, and separate atomic CRM apply. No provider/deployment/production writes, staging, or commit; Phase 7 BLOCKED; production NOT APPROVED; roadmap **46%** (not re-censused).

## Authenticated Fact Review browser/API proof — 2026-09-21

- **PASS:** An isolated current-source API on loopback `8001` and the hash-matched frontend verification mirror on `3102` exercised the real signed RS256 JWT, tenant middleware, database role/permission checks, tenant GUC/RLS, and Next API proxy. A synthetic admin's Fact Review page loaded without a login redirect, fetched one proposal (HTTP 200), and rendered `city: Dammam` with status and evidence.
- **Cold-start note:** The first dev-server run logged one transient 500 / `Unexpected end of JSON input` during initial compilation/navigation. The UI then rendered; after a clean server restart the page and API both returned 200 and the proposal rendered again. A direct authenticated API check also returned 200. Root cause of the first transient response was not established.
- **Isolation/cleanup:** Synthetic tenant/user/company/fact/evidence were inside an outer `salesos_test` transaction. After rollback, read-only checks returned 0 temporary tenants/users/facts/evidence. Ports stopped and temporary token/helper/test routes removed. No production/shared DB, provider, deployment, staging, or CRM write.
- **Still open:** Browser decision interaction, trusted Minder/Agent Reach producer identity/classifier, field ownership/freshness/conflict/supersession, and independent atomic approved-fact CRM apply. See [report 26](26_FACT_REVIEW_BROWSER_API_VERIFICATION_2026-09-21.md).
- Phase 7 remains **BLOCKED**, production remains **NOT APPROVED**, and roadmap remains **46%** (last full census 52/113; not re-censused).

## Authenticated Agent Reach proposal route — 2026-09-21

- Registered `POST /api/v1/facts/proposals/from-agent-reach`. It accepts an existing evidence UUID and target company/field/value, delegates to the tenant-scoped bridge, and returns `crm_applied=false`. It does not start a provider run or expose the general Agent Reach router.
- The route requires `agent_reach:READ` and `master-data-review:CREATE`; the current default role matrix grants both to admin, while ordinary user is denied. Creator identity comes from the verified JWT, client actor spoofing is rejected, and a proposal's author cannot review it.
- The real RS256/JWT/RBAC/RLS test proves an admin can create the proposal, a regular user receives 403, a second admin can review, the source is stored as `CITED_CLAIM` / `UNKNOWN`, and Company remains unchanged. Existing bridge integration covers cross-tenant evidence, exact company match, expiry, sanitization and retry idempotency.
- Focused unit + authorization + PostgreSQL regression: **66/66 PASS** on `salesos_test`; existing Agent Reach security suite **35/35 PASS**; OpenAPI registration contract **1/1 PASS**. Combined execution: **102/102 PASS**. Ruff E4/E7/E9/F/I and `compileall` pass; tracked diff check and new-file whitespace check pass. One upstream Starlette/httpx deprecation warning. Fixtures roll back; test JWKS paths and key directory are redirected to pytest `tmp_path`.
- This is a human-invoked proposal route, not a Minder service integration. Remaining: browser decision interaction against this API, a distinct authenticated/budgeted Minder producer, source-to-value validation, field ownership/freshness/supersession, and a separate atomic approved-fact CRM apply. No provider/production/deployment writes, staging or commit. Phase 7 BLOCKED; production NOT APPROVED; roadmap **46%** (52/113 last census, not re-censused).

## Minder proposal identity and RLS gate — 2026-09-21

- Added a least-privilege `agent_reach_service` role with only `agent_reach:READ` and `master-data-review:CREATE`. The proposal route accepts a verified human JWT or an API key whose validated key ID, user, tenant, and exact two scopes are checked. Service actors are audited as non-human and cannot act as reviewers. Ordinary users, wrong-tenant headers, non-service users, missing identities, and keys with extra scopes fail closed.
- Reordered middleware so `TenantContextMiddleware` runs before `ApiKeyMiddleware`; `api_keys` has tenant RLS and key lookup must run after `X-Tenant-Id` establishes the RLS context. The `salesos_test` integration uses the actual key-validation middleware, a real persisted API-key row, and a non-superuser/non-BYPASSRLS connection.
- Verification after this integration: **123/123 focused unit, security, API, PostgreSQL integration, and OpenAPI checks PASS**; includes wrong-tenant key denial, extra-scope denial, service JWT denial on both proposal routes, and application middleware-order test. Ruff E4/E7/E9/F/I, compileall and diff checks pass. Fixtures and temporary key roll back. One upstream Starlette/httpx deprecation warning.
- The proposal route remains review-only and does not invoke providers or update Company/Contact. No Minder credential was created. The normal CSRF cookie/header rule remains required for API-key POSTs; no CSRF bypass was added.
- **Next:** run Fact Review decision interaction in a current-source browser environment; provide a controlled service-account/key provisioning mechanism; define provider-specific cost quotes and an atomic durable budget before enabling providers; add evidence-to-value validation; then settle field ownership/freshness/conflict/supersession before separate atomic CRM apply. Phase 7 remains BLOCKED, production NOT APPROVED, roadmap **46%** (last census 52/113, no recensus).
## Agent Reach → Fact Review proposal bridge — 2026-09-21

- Added an internal tenant-scoped adapter from persisted Agent Reach evidence to `FactProposalService`. It rejects expired/cross-tenant evidence, requires an exact normalized company-name match, sanitizes public HTTPS source URLs, strips tracking parameters, and never copies `raw_data`.
- All incoming observations are downgraded to `CITED_CLAIM` / `UNKNOWN` with fixed 0.40 scoring input; deterministic retries create one proposal. The target Company remains unchanged.
- Focused bridge + Fact Review unit/integration scope: **42/42 PASS** on `salesos_test`; fixtures are rolled back. Ruff, compileall, and `git diff --check` pass (one upstream Starlette/httpx deprecation warning).
- The module is not connected to an API route or production caller. It does not itself authenticate a producer or enforce provider permissions/budgets, and the supplied proposed value still requires human review. No provider, schema, production DB, deployment, staging, or CRM writes occurred.
- Next: authenticate/authorize the trusted producer and enforce budgets before connection; define ownership/freshness/conflict/supersession rules; keep approved-fact CRM apply separate and atomic. Phase 7 remains BLOCKED; production NOT APPROVED; roadmap **46%** (52/113 last full census; not re-censused). See [report 27](27_AGENT_REACH_FACT_REVIEW_BRIDGE_2026-09-21.md).

## Authenticated Fact Review browser decision — 2026-09-21

- **PASS:** Current source UI on loopback `3102` → Next proxy → isolated current-source FastAPI routers on `8001` → `salesos_test`; authenticated with a short-lived synthetic RS256 reviewer token and the actual tenant role/RLS path.
- **UI:** proposal and evidence rendered; approve remained disabled until a reason was entered; approval submitted successfully; selecting Approved rendered the same fact with reviewer ID and timestamp.
- **Database:** the proposal status is `APPROVED`; one `REVIEW_DECIDED` event contains the same reviewer, reason, and target status; the Company city remains `NULL`.
- **Cleanup:** tenant, user, Company, fact, evidence, links, event, device session, and refresh-token family all checked at zero after cleanup. Frontend/API ports stopped and browser token state cleared.
- **Limits:** test-only JWT bootstrap bypassed credential entry, so normal login/OAuth/secure-cookie behavior is not verified. The CUA UI reported no framework error overlay and the Next server returned HTTP 200; `agent-browser` was absent so browser console capture was unavailable. No production/provider/CRM apply occurred. Windows policy blocked deletion of the synthetic test key/helper under `%TEMP%`; report 28 lists exact paths.
- Roadmap remains **46%** (last census **52/113**, no recensus); Phase 7 BLOCKED; production NOT APPROVED.

See [browser decision report 28](28_FACT_REVIEW_BROWSER_DECISION_2026-09-21.md).

## Google Maps source/provider gate — 2026-09-21

Current Google Maps terms prohibit scraping/extracting Maps content for use outside Maps and prohibit use of Maps Core Services for a listings/directory service or to create/augment an advertising product. Places API output also cannot be retained as a durable SalesOS lead dataset; the persistent place_id exception does not extend to company fields. The standalone business/google-maps-scraper-kit is therefore **not approved as a SalesOS lead source**, and its CSV/JSON output must not feed Master Data, Fact Review, or CRM. SalesOS already rejects google_maps as an Agent Reach research channel; a new explicit proposal-classifier regression locks that boundary. No Maps provider was called. Durable spend reservations have since been implemented and verified only on salesos_test; they remain unconfigured, so no provider can run. See [report 30](30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md) and [report 29](29_GOOGLE_MAPS_PROVIDER_GATE_2026-09-21.md). Phase 7 remains BLOCKED, production NOT APPROVED, and roadmap remains **46%** (52/113 last full census; not re-censused).


## Durable provider spend reservation gate — 2026-09-21

- Added migration t3u4v5w6x7 and ProviderSpendCoordinator for versioned prices, shared-account plus tenant caps, atomic reservations, in-flight/unknown/settled/released states, and audit reasons.
- Review caught a duplicate-dispatch race for reused RESERVED idempotency keys; coordinator now rejects every reused reservation. Concurrent budget, lifecycle, idempotency, tenant-RLS, and role-privilege proofs pass.
- Checks: 79/79 focused Agent Reach/provider-spend unit/security tests; 2/2 PostgreSQL integration tests; Ruff and compileall pass. The test DB is at revision t3u4v5w6x7 with zero rows in all spend tables. salesos_app is non-superuser/non-BYPASSRLS with no direct spend-limit read/update or reservation insert.
- Stopped the standalone gmaps-scraper container. Docker data/cache volumes and local outputs were retained. Before stopping, the read-only jobs snapshot showed 521 tasks (519 ok, 2 working since 2026-09-19); the local jobs API is unavailable now, so those two states could not be refreshed.
- No provider, price card, budget, production migration, or deployment was enabled. No staging or commit. Maps remains excluded; Phase 7 BLOCKED; production NOT APPROVED; roadmap 46% (52/113 last full census).
- Next: contract and use-right approval, verified rate card and both caps, source-to-value evidence validation, then one provider integration behind the coordinator. See report 30.


## Agent Reach value-support screen — 2026-09-21

The bridge now checks that a bounded string claim appears as a whole phrase in persisted title or summary text before creating a proposal. Unicode NFKC/case folding avoids basic formatting mismatches; substring-only matches, missing values, non-strings, and oversized values fail closed. This does not establish truth or source authenticity: trust remains CITED_CLAIM / UNKNOWN, human review remains mandatory, and Company is unchanged. Combined scope passes 83/83 (80 unit/security + 3 PostgreSQL integrations), Ruff and compileall pass. See report 31.
