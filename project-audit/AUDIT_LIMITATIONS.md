# AUDIT LIMITATIONS — AQLIYA / SalesOS

**Audit date:** 2026-09-12
**Constraint:** READ-ONLY; no heavy commands; MCP inspection only if authenticated
**Purpose:** Document every source of truth that could NOT be fully verified. Any claim depending on these sources is labeled **UNKNOWN** in the reports.

---

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

> If the user later authorizes live MCP inspection, these reports can be updated. Current verdicts do NOT depend on these sources except where explicitly labeled UNKNOWN.

---

## 2. Database and application data

| Source | Access status | Impact |
|--------|--------------|--------|
| PostgreSQL live production DB | **UNKNOWN** — no `docker exec` / `psql` executed | Cannot verify: live row counts, RLS policy enforcement, actual `alembic_version` stamp, index presence, connection pool status, `salesos_app` role presence, real GRANTs |
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
8. Full `npm run build` + `npm run lint` + `tsc --noEmit`
9. Playwright e2e for the entire v3 nav tree
10. Bugbot / security-review pass on last 30 days of commits
