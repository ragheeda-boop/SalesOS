  **CURRENT STATUS — 2026-09-22:** Canonical current state is [Audit Refresh 49](49_AUDIT_REFRESH_2026-09-22.md): roadmap 85/113 (75.2%), backend scoped verification PASS, Phase 7 test-only and non-canonical, frontend toolchain blocked in this checkout, production NOT APPROVED. Historical content below is retained for traceability.
# AUDIT LIMITATIONS — AQLIYA / SalesOS
  **أحدث متابعة 2026-09-22:** يصف التقرير 22 استكمال test DB lineage وعرض البيانات المصادق عليها واختبار pagination. ما زالت قيود الإنتاج وPhase 7 قائمة.

  هذا الملف يحفظ حدود التدقيق؛ استخدم [التقرير 22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للحالة الحالية لقاعدة الاختبار والمتصفح. لا يوجد اعتماد إنتاج أو فتح لبوابة Phase 7.

## Latest frontend verification follow-up — 2026-09-20

The current source now has a full local frontend verification pass. The D: source was copied to a temporary C: verification directory because D: is FAT32; existing dependencies were reused only after matching the package and tool configuration files. No packages were installed. `tsc --noEmit` passed; Jest passed **318 suites, 2,635 tests, 1 skipped**; `next build` exited 0 and generated **110/110** routes. Jest prints non-failing React `act(...)` warnings from existing ContextualInsightsProvider tests. The standalone browser smoke loaded the public landing/login/register pages, confirmed protected-route redirects, and after network idle reported **0** console/page errors, non-abort request failures, or static-asset failures. It had no authenticated user or live API data. The temporary runtime mirrored the Dockerfiles' `.next/static` and `public` copy steps; no Docker image or deployment was produced. Automatic command review rejected removal of the temporary source/build copy at `C:\Users\raghe\AppData\Local\Temp\SalesOS-frontend-check-20260920`; environment files were excluded and its dependency junction points to the existing C: install. Details: [report 25](25_IMPLEMENTATION_LOOP_2026-09-20.md).

**Audit date:** 2026-09-12
**Constraint:** READ-ONLY; no heavy commands; MCP inspection only if authenticated
**Purpose:** Document every source of truth that could NOT be fully verified. Any claim depending on these sources is labeled **UNKNOWN** in the reports.

---

## Earlier verification overlay — 2026-09-20 (superseded by report 22)

This overlay captured the state before the test schema/auth baseline was completed. Report 22 supersedes its local database and authenticated-browser rows; the production status is unchanged.

| Area | Latest evidence | Remaining limitation |
|---|---|---|
| Frontend build | Current-source Next.js 15.5.22 production build passed; TypeScript validation passed; 110 pages generated | Authenticated runtime and live API not verified |
| Frontend tests | Isolated Jest: 318/318 suites passed, 2,633 passed, 1 skipped, 0 failed | Backend and browser end-to-end suites not run |
| Browser | Current-source isolated preview rendered `/login` and `/register`; `/v3/data`, `/v3/data/companies`, and `/v3/pipeline` redirected unauthenticated requests to `/login` (307) | No authenticated session; no live `salesos_test` API/data display verification |
| LeadGen / Agent Reach | LeadGen tests 69/69; Ruff + compileall pass; adapter now requires explicit API base URL + token + tenant UUID | Agent Reach remains unconfigured; no live research/scrape/sync run |
| Backend for browser QA | Existing `salesos-backend-1` source mount is `C:\Users\raghe\Documents\Muhide\salesos`; database target is `postgres/salesos` | Not the `D:\AISalesOS` checkout or `salesos_test`; excluded from verification. Current `docker-compose.test.yml` defines Postgres + Redis only, no API service |
| `salesos_test` | Read-only snapshot: 296,746 companies, 1,124 people, 909,967 source rows, 7 source files, 1,524,717 provenance rows, 54,185 review candidates | No database writes. During the migration investigation, one metadata-only `alembic current` lookup was inadvertently sent by local `.env` to a local database named `salesos`; it returned only the Alembic version and did not read business rows or write. Remote Railway production was not queried. |
| Phase 7 | **BLOCKED** pending human ER review, 36 short-CR adjudications, DI P1/P2 confirmation, and PO sign-off | No automatic resolution or production ingestion |

See `21_POST_EXECUTION_VERIFICATION_2026-09-20.md` for the changes and ordered closure plan.

### Historical follow-up runtime evidence — before test-schema completion

| Area | Latest evidence | Remaining limitation |
|---|---|---|
| Current-source backend | Built from `D:\AISalesOS\salesos\backend`, isolated at `127.0.0.1:8001`; `/health` returned 200 with PostgreSQL connected through `salesos_app` to `salesos_test` | Startup was in `SALESOS_TESTING=true`; health does not establish full application readiness |
| Master Data API | Unauthenticated `GET /api/v1/master-data/global-companies` returned 401 | No test user session was created; `users` and `tenants` tables are absent from `salesos_test` |
| Migration lineage | Current checkout head is `p7q8r9s0t1u2`; database stamp is `p6a0b1c2d3e4`; Alembic cannot resolve that revision | No migration or manual schema repair was run; authenticated UI/data verification is blocked pending an approved baseline and valid migration lineage |
| Database safety | Read-only inspection only; no migration, DDL, account seeding, or row changes | Existing test DB must be preserved until its origin and recoverable baseline are confirmed |
| Providers | Google Maps reports 2 active `working` jobs; Scout healthy; Agent Reach not configured | No additional Maps job, Agent Reach request, enrichment, or CRM sync was started |

The earlier statement that the current backend could not be started is superseded: it was started and reached the test DB. The remaining blocker is the incomplete/inconsistent test schema, not backend build or database connectivity. Details are in report 21.

## 1. Live infrastructure & production data

| Source | Access status | Impact |
|--------|--------------|--------|
| Railway backend production (`salesos-production-96c0.up.railway.app`) | **UNKNOWN** — did not hit `/health`, `/version`, `/openapi.json`, or metrics from this session | Cannot verify live schema_version, live env, live Redis/Kafka/Neo4j connectivity, live rate-limit posture, or live SLO. Claims in `FINAL_GO_NOGO_ASSESSMENT.md` (staging schema `g1h2i3j4k5l6` on 2026-08-21) accepted as reported |
| Railway staging (`salesos-staging.up.railway.app`) | **UNKNOWN** | Same as above |
| Vercel frontend (production + preview) | **UNKNOWN** | Live UI + build status not verified — labels default to what `FINAL_GO_NOGO_ASSESSMENT.md` reports |
| Railway MCP (`plugin-railway-railway`) | Available but NOT invoked — user did not explicitly authorize live MCP calls; audit scope is read-only local | Live service list / deployment history / environment variables / logs / recent errors UNKNOWN |
| Vercel MCP (`plugin-vercel-vercel`) | Available but NOT invoked | Live deployment list / preview URLs / build logs / Web Analytics UNKNOWN |
| GitHub MCP (`plugin-github-github`) | Available but NOT invoked | Live PRs / CI runs / issues / branches / releases UNKNOWN beyond local git |
| Notion MCP (`plugin-notion-workspace-notion`) | Available but NOT invoked | Roadmap / OKRs / meeting notes in Notion UNKNOWN |
| Prisma MCPs (Local + Remote) | Available but NOT invoked — this stack uses SQLAlchemy + Alembic, not Prisma | N/A |
| Google Cloud Console / OAuth clients | **UNKNOWN** — no access | Staging OAuth client status per FINAL_GO_NOGO residual is UNKNOWN |

  If the user later authorizes live MCP inspection, these reports can be updated. Current verdicts do NOT depend on these sources except where explicitly labeled UNKNOWN.

---

## 2. Database and application data

| Source | Access status | Impact |
|--------|--------------|--------|
| PostgreSQL live production DB | **UNKNOWN** — no direct production connection was intended or verified; a local `.env`-routed metadata query accidentally read only the version stamp from a database named `salesos` on `localhost` | Cannot verify remote live row counts, RLS policy enforcement, production `alembic_version`, indexes, pool status, `salesos_app` role, or GRANTs. No DDL or writes occurred. |
| `salesos_test` DB | **UNKNOWN** — Docker daemon status unknown; not executed | Cannot re-verify Phase 6 dry-run 296,746 companies / 1,238,635 staged changes / 0 safety-counter violations, Phase 7-A capture writes |
| Redis contents | **UNKNOWN** | |
| Kafka topics | N/A — event bus default is `in_memory` |
| Neo4j graph contents | **UNKNOWN**; but per ADR-108 offline in v1.0 |
| Meilisearch index | **UNKNOWN** |
| `salesos_test_export/salesos_test.dump` (pg_dump on disk) | Present, NOT restored / inspected this audit | Row counts accepted from Phase 7-A PO decision doc |

---

## 3. Code artifacts NOT fully inspected

| Area | Reason | What is unknown |
|------|--------|----------------|
| Every `.py` file in `salesos/backend/` | Repo has thousands of files — audited routers, config, and boot; individual module internals inspected only via docs/router registrations | Business-logic correctness of individual modules (e.g., internal `signal_actions/router.py` beyond the bugfix noted in AGENTS.md §39) |
| Every `.tsx` file in `salesos/frontend/src/` | Only nav, one page (v3/companies/page.tsx from open-files context) fully read | Whether individual pages contain silent mocks / hardcoded data / dead handlers |
| Full test suite | Not re-executed | Test pass counts accepted from AGENTS.md session summaries |
| `node_modules/`, `.venv/`, `.mypy_cache_*/` | Skipped by policy | N/A |
| `frontend/packages/*` | Not enumerated in detail | Widget SDK / decision STUB / agents STUB internals |
| `salesos/knowledge-packs/` internal content | Directory listed; individual pack YAML/JSON not read | Actual 22 signal definitions not diffed |
| Every ADR (`docs/adr/`) | ~40+ files — cited when relevant; not exhaustively read | Full decision text for less-cited ADRs |
| Every session-report / progress doc | 60+ `PROGRESS-WAVE*.md` files — not exhaustively read | Fine-grained wave history |
| Every test file | Not enumerated | Individual assertion quality |
| GraphQL schema (`app/graphql/schema.py`) | Referenced in `boot/routers.py` `include_router("/graphql")`; not read | GraphQL surface unknown |
| Full `salesos/docs/` internal tree | Not enumerated | User guide / admin guide freshness |
| Full `assets/` tree | Skipped | Presentation deck freshness |
| Full `packages/scrapers/*` code | Directory listed only | Scraper current status, connector health |

---

## 4. Runtime verifications NOT performed

| Verification | Reason | Impact |
|--------------|--------|--------|
| Live browser QA on `/v3/*` and `/(dashboard)/*` pages | Read-only audit; no browser MCP call | Cannot re-confirm 35/35 V3 pages clean claim (2026-09-05) |
| Live `curl /api/v1/health`, `/api/v1/version`, `/openapi.json` | Not run | Live schema/version/config UNKNOWN |
| Full `npm run build` (frontend) | Low-load protocol; not run | 109-page build claim accepted as reported |
| Full `pytest` (backend) | Low-load protocol; not run | Test counts accepted as reported |
| `docker compose up` + `alembic upgrade head` | Not run | Cannot re-confirm alembic head vs DB stamp |
| `npm run lint` / `tsc --noEmit` | Not run | Lint/tsc counts accepted as reported |
| Playwright e2e | Not run | 42/42 E2E accepted as reported |
| Load test / soak / chaos | Not run | Optional load evidence (STORY-14-01 r3, wave11 soak) accepted as reported |
| Real network scans against Railway | Not authorized | Live TLS / headers / rate limit UNKNOWN |
| SSRF / IDOR live re-exploitation | Explicitly forbidden by scope | Post-fix efficacy accepted from AGENTS.md + FINAL_GO_NOGO_ASSESSMENT.md |

---

## 5. External-provider status

| Provider | Status |
|----------|--------|
| OpenAI API (real production key) | UNKNOWN — key value not inspected; not called |
| AI Horde / Cydonia-24B (dev-only per §28 provider-eval) | Documented as DEV-ONLY, production no-go |
| Notion API | UNKNOWN — token not inspected |
| Google OAuth (staging) | Per FINAL_GO_NOGO, blocked pending Google Cloud Console access |
| Stripe | Sandbox/live keys empty by default; fail-closed |
| Odoo | Empty config; fail-closed |
| Apollo / government APIs (CR, Balady, Najiz, ZATCA) | Not used per AGENTS.md §28 policy — confirmed at code-review level, not runtime |

---

## 6. Historical claims accepted (not independently re-run this audit)

- Backend regression 353/353 (2026-09-05)
- Full unit 2388/2401 pass (2026-08-19); 2761/2820 pass (2026-08-23)
- E2E Commercial Loop 42/42
- Frontend build 109 pages, 0 tsc, 0 lint (2026-09-05)
- Phase 6 dry run 296,746 companies, 0 safety violations
- Browser QA 9/9 v3 pages (2026-08-17)
- Production schema `g1h2i3j4k5l6` verified via `/api/v1/version` on staging (2026-08-21)
- OPS-01 rows 1–3, 8 signed 2026-08-24 (AGENT-EXECUTED per PO directive)
- Phase 7-A capture writes applied 2026-09-10 on `salesos_test`

These claims are **cited as reported** in this audit's reports, labeled per honesty scale (`build validated + runtime validated` for code paths; `light validated` for browser paths; `not validated` for external live surfaces).

---

## 7. Sources of truth deliberately preserved unchanged

- `AGENTS.md` sessions §11–§39 — accepted as engineering ledger
- Phase evidence packs (Phase 1–4F) — accepted as gate closure evidence
- All ADRs — accepted as decision records
- All `docs/data/phase6/` and `docs/data/phase7/` — accepted as data lineage evidence
- `AI_HONESTY.md` — accepted as AI marketing constraint

Contradictions between these sources are surfaced in `01_CURRENT_STATE.md` and `19_RISK_REGISTER.md` but NOT rewritten.

---

## 8. Recommended next-round verifications (post-audit)

1. Live Railway MCP inspection: services, envs, deployment history, backup schedule status
2. Live Vercel MCP: current deployments, build status
3. GitHub MCP: PR/CI health for open dependabot branches; CODEOWNERS state
4. Live `/health`, `/version`, `/openapi.json` on staging + production
5. Live `alembic current` vs `alembic heads` inside a running backend container
6. Restore `salesos_test.dump` locally and re-run Phase 6/7-A capture-only writes
7. Full `pytest` in Docker with real DB
8. **Frontend `npm run build` and `tsc --noEmit` completed later;** authenticated E2E and deployment-image build remain open.
9. Playwright E2E for the authenticated v3 nav tree and seller workflows
10. Bugbot / security-review pass on last 30 days of commits

## متابعة مراجعة P2 — 2026-09-20

The sample has now been compared against the master snapshot and the internal mismatch count is zero in both strata. This is a consistency check against the same source used to derive the data, not independent current-world verification. No official review-queue disposition or database write was made; PO acceptance remains outstanding. Detailed counts, hashes, scope, and limits: `docs/data/phase7/p2_sample_20260920/PHASE7A_P2_MASTER_REVIEW_20260920.md`.

## Fact Review browser limitation update — 2026-09-21

The prior mocked-browser-only limitation is superseded for authenticated **proposal listing**: current D-source UI/API was exercised with a synthetic signed JWT against `salesos_test`; the expected proposal/evidence rendered, and all rows rolled back with zero residue. No real Agent Reach/Maps/Scout request, browser decision action, CRM apply, production authentication, or production DB activity was performed. See [report 26](26_FACT_REVIEW_BROWSER_API_VERIFICATION_2026-09-21.md).
## Agent Reach-to-Fact Review bridge limitation — 2026-09-21

The prior adapter-only status is superseded for route existence. An authenticated human route now requires `agent_reach:READ` and `master-data-review:CREATE`; JWT/RBAC/RLS and ordinary-user denial are proven on `salesos_test`. Focused regression is **66/66**, OpenAPI contract **1/1**, and existing Agent Reach router/security regression **35/35**. There is still no automated Minder/service identity or provider execution, no provider budget enforcement for an automated caller, and no independent source-to-value validation. No live Agent Reach/Maps/Scout provider request was made. A second human review is required; CRM apply, ownership/freshness policy, browser decision action, and Phase 7 gates remain open. During the latest browser attempt, `localhost:3102` refused the connection and the agent-browser CLI was unavailable. See [report 27](27_AGENT_REACH_FACT_REVIEW_BRIDGE_2026-09-21.md).

## Fact Review browser decision limitation correction — 2026-09-21

The earlier browser decision limitation is now closed for the isolated reviewer action. Current V3 UI and API saved a reasoned approval to `salesos_test`, showed the Approved item, and preserved the canonical Company value. The JWT was bootstrapped for the test and normal login/OAuth was not tested. Browser console capture is still unavailable because the `agent-browser` CLI is absent; visual/accessibility state and Next server HTTP 200 were checked. Test rows were all verified absent afterward. The temporary signing key/helper remain in `%TEMP%` because Windows policy blocked deletion; see [report 28](28_FACT_REVIEW_BROWSER_DECISION_2026-09-21.md). No provider/production writes. Phase 7 BLOCKED; roadmap **46%**.

## Google Maps source/provider gate — 2026-09-21

Current Google Maps terms prohibit scraping/extracting Maps content for use outside Maps and prohibit use of Maps Core Services for a listings/directory service or to create/augment an advertising product. Places API output also cannot be retained as a durable SalesOS lead dataset; the persistent place_id exception does not extend to company fields. The standalone business/google-maps-scraper-kit is therefore **not approved as a SalesOS lead source**, and its CSV/JSON output must not feed Master Data, Fact Review, or CRM. SalesOS already rejects google_maps as an Agent Reach research channel; a new explicit proposal-classifier regression locks that boundary. No Maps provider was called. Durable spend reservations have since been implemented and verified only on salesos_test; they remain unconfigured, so no provider can run. See [report 30](30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md) and [report 29](29_GOOGLE_MAPS_PROVIDER_GATE_2026-09-21.md). Phase 7 remains BLOCKED, production NOT APPROVED, and roadmap remains **46%** (52/113 last full census; not re-censused).


## Provider spend and scraper status — 2026-09-21

Spend controls are verified only on salesos_test; no provider pricing/budget is configured and no provider run was tested. The gmaps-scraper container is stopped and its volumes/outputs are retained. The last read-only snapshot was 521 tasks (519 ok, 2 working); after stopping, 127.0.0.1:8080 refused connections, so the two in-progress task states are unverified. See report 30.


## Evidence-to-value limitation — 2026-09-21

A lexical screen checks phrase presence in captured Agent Reach title/summary only. It cannot establish that the page is authentic, the summary is faithful, or the claim is semantically correct. Provider-specific normalization and independent semantic/source verification remain untested. See report 31.

---

## Current audit addendum — 2026-09-22 / Audit Refresh 49

**Status authority:** This addendum supersedes stale progress percentages and current-state claims in this file while preserving the historical narrative above. The complete current snapshot is [Audit Refresh 49](49_AUDIT_REFRESH_2026-09-22.md), with execution evidence in [Production Readiness Loop 45](48_PRODUCTION_READINESS_LOOP_2026-09-22.md).

- Current code-scope roadmap: **85/113 = 75.2% (75%)**.
- Backend health: /health HTTP 200; database, cache, graph and Redis connected.
- Scoped evidence: focused product **69/69**, Phase 5 CR **7/7**, ER pipeline **10/10**, compileall and diff checks PASS.
- Phase 7 remains controlled and non-canonical: P2 sample 1,213 at 0.00% internal material error; P1 6,904 captured; Fuzzy 2,661 captured without merge; Short-CR 11 unresolved escalation; MA staging 1,114 rows on salesos_test only (792 PROPOSED / 322 ESCALATED).
- Production database remained read-only: 107 policies total, 106 tenant-isolation named; commercial contracts have RLS and FORCE RLS; no Phase 7 proposal table or write in salesos.
- Frontend source inventory is 49 V3 pages and 78 legacy pages. Local dependency repair failed with EISDIR/EPERM; TypeScript, Next build and authenticated browser are **not release evidence** in this checkout.
- No provider call, CRM apply, production migration, deployment, commit or push occurred.
- Production approval remains **NOT APPROVED** pending frontend toolchain, Phase 7 owner closure, staging connector E2E, backup/restore, monitoring/DR, SSO, Stripe, PDPL and final PO/Data/DevOps sign-off.

Current detailed evidence: report 49 and report 48.
