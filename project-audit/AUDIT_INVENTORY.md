  **CURRENT STATUS — 2026-09-24:** Canonical current state is report [57](57_CAPABILITY_REGISTER_RECONCILIATION_2026-09-23.md) (132-row register + mechanical verification), [58](58_EFFECTIVENESS_FORCE_RLS_CLOSURE_2026-09-23.md) (FORCE RLS on `account_funnel`/`score_observations`), [59](59_ORPHAN_KEEP_TABLES_RLS_GAP_2026-09-23.md) (14 live orphan-keep tables correction), and **report [89](89_BOOKKEEPING_RECONCILIATION_2026-09-24.md)** (2026-09-24 bookkeeping: register re-verified against R58–R88 — **zero row flips, 124/132 = 93.9% COMPLETE proposed, 8 BLOCKED rows (40/46/52/53/59/60/131/132) unchanged, zero CODE-CLOSABLE** — and all four mechanical checks re-run on current source: **129 migration files (126 at R57 + R58/R68/R75), single Alembic head `f2e3d4c5b6a7` with a clean empty→head upgrade; on a fresh ephemeral DB migrated to head 211 public tables with 139 RLS / 138 FORCE (139 incl. partitioned parent) / 139 policies (136 `tenant_isolation_*` + 3 legacy), 0 RLS-without-policy, 0 policy-without-RLS, `ALL_TENANT_TABLES`=66 in both files, `rls.py` SHA matches container; feature flags unchanged (`feature_ai_copilot` and the other 4 = False, entitlement/quota enforcement = True); v3=49 / legacy=78 pages**; report signed (PO) 2026-09-24 for bookkeeping only). **PO Phase-A decisions ([report 91](91_PO_PHASE_A_DECISION_RECORD_2026-09-24.md), 2026-09-24):** A1 **ACCEPTED** — the 132-row register is the single source of truth; **124/132 = 93.9% is now the operational figure** and the historical 89/113 is retired as an unaudited historical scalar; bare-scalar tracking stops. A2 **RELEASED Phase 7 implementation** with explicitly tracked risk (supersedes 2026-08-29 planning-only Option B); the 2,661 P3 pairs (never auto-merge) and 36 short-CR (never auto-adjudicate) remain pending human review, and production (G8) is not opened. A3 **ACCEPTED** P2 sampling 3% / 1% stratified; acceptance threshold still PO-set. Reports 60–88 (2026-09-23/24) are quality/bug findings with register effect **None/UNCHANGED**. **Data-state re-check (report 89 session):** the Phase 6 review population (54,185) lives **only** in evidence CSVs — `salesos_test` currently has 0 rows in `md_review_candidates`/`md_identity_classifications`/`md_source_rows` and 180,000/296,746 `md_global_companies` (integration teardown truncates `md_*`; restore via `muhide_ingest_real.py` + `muhide_v1_enrichment.py`). **Human-gate enablement ([report 90](90_HUMAN_GATE_INDEX_2026-09-24.md), 2026-09-24):** full 16-gate index produced; review workbooks created read-only at `docs/data/phase6/review/` — `REVIEW_36_SUSPICIOUS_SHORT_CR.csv` (36 separator-list accounts), `REVIEW_P3_PAIRS_2661.csv` (all 2,661 fuzzy pairs, all `final_review_required=YES`), `README.md`. No gate opened by the index itself (PO decisions did the openings), no review performed, no DB/code/production change. **Register operational figure is now 124/132 = 93.9%** (accepted A1); **production (G8) NOT APPROVED and NOT OPEN.** Historical content below is retained for traceability.
# AUDIT INVENTORY — AQLIYA / SalesOS
  **أحدث متابعة 2026-09-22:** صفحات البيانات اختُبرت على `salesos_test` عند `q9r0s1t2u3v4` (التقرير 22). لاحقًا تقدمت قاعدة الاختبار وحدها إلى `r1s2t3u4v5w6` لإضافة idempotency للتحليلات؛ راجع التقرير 25. Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

  بقية المخزون لقطة من يوم التدقيق؛ نتائج المتصفح موثقة في التقرير 22، وجولة idempotency اللاحقة وحدودها موثقة في التقرير 25. العدد التاريخي 109 migration files في لقطة 12 سبتمبر؛ checkout الحالي يحوي 113 ملف revision بصيغة Python (114 ملفًا إجمالًا)، منها migration telemetry الجديدة.

**Audit start:** 2026-09-12 (Sat)
**Audited workspace:** `D:\AISalesOS`
**Auditor role:** Read-only, evidence-first Board / Founder / Investor / CTO / Product / Sales audit
**Method:** Discover → Inventory → Verify → Map → Reconcile → Analyze → Strategize → Prioritize → Report
**Write scope:** `D:\AISalesOS\project-audit\` only

  Every item below was inspected via `Read`, `Grep`, `Glob`, `Shell` (read-only), or listed directly. Documentation is NOT treated as proof of implementation. Code is NOT treated as proof of production.

---

## 1. Workspace root inventory (top level)

| Path | Type | Purpose (as read) | Notes / Honesty |
|------|------|-------------------|-----------------|
| `AGENTS.md` | Governance | Agent essentials + session summaries §11–§39 (78 KB) | Authoritative for daily ops; documents Phase 1–4 CLOSED + Phase 7 BLOCKED + Production NOT declared |
| `PRODUCT_BIBLE.md` | Product | Vision, personas, principles, priorities (21 KB) | Defers GO/NO-GO to ga-engineering-audit; DUAL-BIBLE hazard (EAB-001-P1-DOC-01) |
| `README.md` | Overview | Public-facing repo README | Overclaims — lists domains as 🟢 Live incl. Copilot / Knowledge Graph / Decision Center; conflicts with AI_HONESTY |
| `RUNBOOK.md` | Ops | System runbook | Not fully re-verified during this audit |
| `.env.example` (root) | Config | Root sample env | 4.9 KB — separate from `salesos/.env.example` (2 KB) |
| `.env.local` | Config | Local dev only (git-ignored expected) | Read-only inspection; not exfiltrated |
| `docker-compose.yml` (root) | Infra | Lighter local/dev-only stack | 11 KB — dual with `salesos/docker-compose.yml` (staging/prod-shaped) |
| `Dockerfile.railway` / `.celery` | Infra | Railway prod build | Referenced from `railway.json` |
| `railway.json` / `railway.beat.json` / `railway.worker.json` | Infra | Railway service configs | **File-side canonical (post-audit):** root `railway.json` HAS `preDeployCommand: alembic upgrade head`; `salesos/railway.json` = **STALE pointer stub** (`canonicalFile: ../railway.json`, old contents at `docs/archive/railway.json.stale`); live dashboard UNKNOWN |
| `.github/workflows/` | CI | 9 workflows (ci.yml 39 KB, deploy.yml 28 KB, staging/prod, docker-smoke, e2e-stage7, fitness-ci-subset, release-gates, security-scan) | Fixed 2026-07-30: moved from `salesos/.github/` to root |
| `.gitleaks.toml`, `.semgrepignore`, `.trivyignore` | Security | Scanner ignore lists | Present |
| `.gitmodules` | Repo | `engineering-os` submodule | 119 B |
| `salesos/` | Application | Main SalesOS monorepo (BE+FE+infra) | Canonical application tree |
| `docs/` | Docs | 27 top-level subfolders (adr, ai, api, audit, architecture, backend, compliance, current-state, data, design, frontend, incidents, migration, operations, ops, program, reality-check, reference, releases, reports, roadmap, security, ux, v2, vnext, docs, archive) | Massive; supersession chains |
| `packages/` | Shared code | scrapers (balady/najiz/rega/taqeem), data pipelines, widget-template — **DUPLICATED**: `packages/packages/data` also exists (looks like a nested copy) | Hygiene issue |
| `engineering-os/` | Governance submodule | ADRs, kernel, governance | Submodule (`.gitmodules`) |
| `infrastructure/` | Infra | Cloud/observability scripts | Contains only README + `infrastructure/` self-nested |
| `migration-log/` | History | phase-01..10.md restructure logs | Historical only |
| `archive/` | Retired | data-files, engineering-recovery, legacy-configs, old-outputs, sales-os — plus nested `archive/archive/*` self-duplication | Should be git-ignored; still on disk |
| `assets/` | Brand/marketing | reports, presentations, branding | Not audited in detail |
| `scripts/` | Ops | Root-level scripts | Not audited in detail |
| `salesos_test_export/` | Data | pg_dump `salesos_test.dump` | Referenced by Phase 7-A PO decision |
| `.ai/`, `.claude/`, `.cursor/`, `.engineering/` | Meta / agent | Cursor/Claude/agents config; `.engineering/` is a retired catalog | Present but staged-for-deletion in git index |

---

## 2. Application tree — `salesos/`

| Subtree | Purpose | Evidence read |
|---------|---------|---------------|
| `backend/` | FastAPI + SQLAlchemy 2.0 + Alembic; DDD-ish layout with `app/`, `domains/`, `intelligence/`, `runtime/`, `pipeline/`, `sdk/`, `application/`, `platform/`, `memory/`, `cli/`, `mcp_server/`, `data/`, `benchmark(s)/`, `demo/`, `design_tokens/`, `knowledge-packs/`, `migrations/`, `outputs/`, `reports/`, `scripts/`, `tests/`, `docs/` | dir listing + `boot/routers.py` + `config.py` fully read |
| `backend/app/modules/` | 37 module directories: admin, agent_reach, api_keys, audit, billing, cache, chaos_resilience, communication_hub, company, contact, decision, demo_mode, dr_drill, effectiveness, employee_360, entity_resolution, excel_import, executive, gtm, identity, integration_hub, load_slo, marketplace_listings, master_data, monitoring, notion_sync, revenue_execution, rules_engine, settings, signal_actions, signal_marketplace, sso, telemetry, tenant_studio, webhooks, work_intelligence | dir listing |
| `backend/domains/` | 18 domain packages: ai, analytics, approval, commercial, copilot, decision, decision_center, employee, feature_store, marketplace, notifications, rag, revenue, scoring, search, timeline, ubom (DEPRECATED per Phase 1), workflow | dir listing |
| `backend/app/routers/` | 20 top-level routers registered by `boot/routers.py` (admin_demo, ai, analytics, approval, attribution, benchmarks, commercial, copilot, demo, enrichment, mcp, meetings, metrics, notifications, opportunity_contacts, rag, revenue, search, source_of_truth, workflows) | `boot/routers.py` fully read (627 lines, ~85 include_router calls) |
| `backend/app/alembic/versions/` | **109 migration files** on disk (target head per AGENTS.md = `p7q8r9s0t1u2_nullable_company_cr`) | `Get-ChildItem` count |
| `backend/tests/` | Present but sizes not enumerated this audit | dir listing only |
| `backend/pyproject.toml` + `poetry.lock` | Python packaging | present |
| `backend/Dockerfile*` | 3 Dockerfiles (Dockerfile, .backend, .test) | present |
| `backend/scripts/` | Ops scripts (per AGENTS.md: `check_alembic_head.py`, `seed_icp_pif_demo.py`, `seed_rag_pilot.py`, `phase6_dry_run.py`, `phase6_schema_gate.py`, `muhide_ingest_real.py`, `muhide_v1_enrichment.py`, `fix_false_cr.py`, `classify_identity.py`, `safety_check.py`, `wave11-soak-gate.py`, `ops_live_probes.py`, `ops_runtime_probes.py`) | AGENTS.md + dir listing |
| `backend/.mypy_cache_*` × 12 | Build caches | Should be `.gitignored`; noise |
| `backend/.venv/` | Python venv on disk | Should not be committed |
| `backend/outputs/`, `benchmark/`, `benchmarks/` | Runtime output + benchmarks | Present |
| `frontend/` | Next.js 15 App Router + TypeScript + Tailwind | dir listing |
| `frontend/src/app/` | 6 top-level: `(auth)`, `(dashboard)`, `api`, `fe-sec-02`, `system`, `v3` | dir listing |
| `frontend/src/app/v3/` | 24 sub-routes: activities, admin, analytics, approvals, companies, contacts, contracts, crm, cs, data (+ 5 sub-pages: companies, er, imports, people, review-queue), effectiveness, employee, icp, my-day, people, proposals, quotes, review-queue, reviews, sales-dashboard, settings, shell, tasks | dir listing + `Glob page.tsx` (40 v3 pages) |
| `frontend/src/app/(dashboard)/` | Legacy dashboard shell — 78 routes (dashboard, companies, contacts, opportunities, activities, revenue, pipeline, forecast, search, decisions, meetings, rag, ai, graph, copilot, automation, analytics, signals, rules, monitoring, customer-success, settings, admin, employees, gtm/*, studio/*, marketplace/*, knowledge/*) | `Glob` |
| `frontend/src/app/api/` | 2 route.ts: `/api/v1/copilot/query` and `/api/auth/callback/google` — otherwise proxied to backend | `Glob route.ts` |
| `frontend/src/components/v3/nav.ts` | Primary v3 nav — 24 entries + 4 data sub-pages | Fully read |
| `frontend/vercel.json` | Vercel config: framework=nextjs, region=iad1, security headers | Fully read |
| `frontend/Dockerfile*`, `docker-compose.yml` | FE containers | present |
| `frontend/e2e/`, `tests/`, `playwright*.config.ts` | Playwright + Jest configs | present |
| `frontend/packages/` | Local FE packages (per docs: `@salesos/design-language`, `@salesos/ui`, `@salesos/widget-sdk`, decision STUB, agents STUB, tokens) | Not enumerated in detail this audit |
| `frontend/PRODUCT_COMPLETION_REPORT.md` / `PRODUCT_FINAL_SUMMARY.md` / `PRODUCT_RELEASE_PLAN.md` | FE product docs | Not fully re-audited |
| `salesos/docs/` | Internal SalesOS docs | Not fully enumerated |
| `salesos/knowledge-packs/` | Signal marketplace packs (per §26 seeding — 22 platform signals from kp-construction / kp-healthcare / kp-financial-services) | dir listing |
| `salesos/infra/` | 7 infra subtrees: caddy, docker, k8s, monitoring, scripts, staging, terraform | dir listing |
| `salesos/scripts/`, `platform/`, `application/`, `packages/`, `reports/`, `memory/`, `cli/` | Assorted | Present |
| `salesos/tests/` | Cross-cutting tests | present |

---

## 3. Backend routers registered (from `app/boot/routers.py`)

Read in full (627 lines). Router registrations (grouped):

- **Identity / Auth:** `identity_router` (`/api/v1/identity`), `nextauth_compat_router` (`/api/auth`), `sso_router` (`/api/v1`)
- **Metrics / Ops:** `metrics_router`, `runtime_admin_router`, `monitoring_router`, `cache_router`, `capability_router`, `ux_router`
- **CRM / Product Core:** `company_router` (`/api/v1/companies`), `contact_router`, `opportunity_contacts_router`, `attribution_router`, `activity_router`, `commercial_router`, `revenue_execution_router`, `revenue_planning_router` (`/api/v1/revenue-planning`), `pipeline_analytics_router`, `dashboard_router`, `executive_router`
- **Copilot / AI / Decision / RAG:** `copilot_router`, `approval_router`, `ai_router`, `ai_model_tiers_router`, `rag_router`, `decision_platform_router`, `decision_center_router`, `decision_router` (Runtime — remounted deprecated `/api/v1` aliases), `nba_router`, `graphql_router` (`/graphql`), `activity_intelligence_router`
- **Master Data / Entity Resolution / Phase 6/7:** `entity_resolution_router` (`/api/v1/entity-resolution`), `master_data_router` (`/api/v1/master-data`), `review_queue_router` (`/api/v1/master-data/review-queue`), `enrichment_router`
- **Signals / Actions / HITL / Effectiveness:** `signal_marketplace_router`, `signal_actions_router`, `hitl_router`, `effectiveness_router`
- **GTM Intelligence (STORY-11-\* pack):** `icp_router`, `icp_admin_router`, `market_sizing_router`, `lead_discovery_router`, `enrichment_router` (GTM), `gtm_verification_router`, `lookalike_router`, `website_intelligence_router`, `outreach_router`, `sequencing_router`
- **Tenant Studio (STORY-10-\* pack):** `tenant_studio_router`, `workflow_builder_router`, `scoring_rules_router`, `territories_studio_router`, `permissions_studio_router`, `notification_rules_router`, `branding_studio_router`, `prompt_library_router`, `ai_policies_router`, `ai_memory_router`
- **Communication Hub / Integrations:** `communication_hub_router` (Google OAuth callback path), `integration_hub_router`, `webhooks_router` (SoT for subscriptions), `notion_sync_router`, `excel_import_router`, `mcp_router`
- **Employee 360:** `employee_360_router`, `employee_domain_router`, `employee_intelligence_router` (also remounted at `""` for infra health), `employee_webhook_router`
- **Runtime infra:** `event_runtime_router`, `data_fabric_router`, `feature_store_router`, `feature_store_domain_router`, `timeline_router`, `search_router`, `search_api_router` (experimental), `schema_router`, `form_router`, `action_router`, `extension_router`, `plugin_router`
- **Marketplace:** `marketplace_listings_router`, `marketplace_router`
- **Load / Chaos / DR (STORY-14-\*):** `load_slo_router`, `chaos_resilience_router`, `ai_failover_router`, `llm_regression_router`, `dr_drill_router`
- **Billing:** `stripe_webhook_router` (public), `admin_router` (billing/plans/etc.)
- **Meetings / Workflows / Rules / Notifications / Audit / API Keys / Settings / Telemetry / Source of Truth / Demo:** all present

**Duplicates flagged in the router file itself:** commented notes describe historical duplicate mounts (opportunities.py deleted P1-01; decision_platform vs Center vs Runtime three-way overlap; search runtime vs experimental; workflow webhook CRUD vs Integration Hub `/webhooks`).

---

## 4. Alembic migrations

- **109 files** in `salesos/backend/app/alembic/versions/` (headcount from `Get-ChildItem`)
- **AGENTS.md §34** claims Phase 4 = "96 migrations, 1 head". `FINAL_GO_NOGO_ASSESSMENT.md` (2026-09-05) claims "97 migrations". Actual on-disk = 109 (includes `.bak` and merge revs).
- Named heads referenced across docs: `g1h2i3j4k5l6_phase4_dlq_persistence` (Phase 4 head), then Phase 4A/4F additions `h1i2j3k4l5m7`, `h2i3j4k5l6m8`, `i3j4k5l6m7n8`, then Phase 0 master data `j4k5l6m7n8o9`, then `j5k6l7m8n9o0_agent_reach_persistence`, `k6l7m8n9o0p1_merge_phase0_agent_reach` (merge rev), `l7m8n9o0p1q2_signal_actions`, `m8n9o0p1q2r3_hitl_seller_operating_model`, `n9o0p1q2r3s4_business_effectiveness`, `o0p1q2r3s4t5_observation_snapshot`, `p7q8r9s0t1u2_nullable_company_cr` (latest by naming)
- **Live head verification NOT performed this audit** (would require Docker exec). Latest schema on production per `FINAL_GO_NOGO_ASSESSMENT.md` = `g1h2i3j4k5l6` as of 2026-08-21 — this is 6+ migration levels behind repo head.

---

## 5. Key backend config (evidence-verified)

Read from `salesos/backend/app/config.py`:

- `feature_ai_copilot: bool = False` — **post-audit reconciled 2026-09-12/13** (PO-recon revert comment in config.py:160). Was `True` at snapshot (flipped 2026-08-19); now matches `AI_HONESTY.md` mandate. 12 test files/15 asserts `is False`; 101/101 Docker PASS; zero leftover `True` in non-test code.
- `feature_signal_marketplace_postgres: bool = False` — Postgres marketplace off; in-memory
- `feature_crm_kanban: bool = False`
- `feature_httponly_access_cookie: bool = False`
- `feature_search_fuzzy_v2: bool = False`
- `entitlement_enforcement_enabled: bool = True`, `quota_enforcement_enabled: bool = True`
- `demo_mode: bool = False`
- `env: str = "development"`, `debug: bool = False`
- Two DB users enforced: `postgres_user` (owner, BYPASSRLS) vs `app_postgres_user=salesos_app` (application role that respects RLS); staging/prod REFUSE to boot without `APP_POSTGRES_PASSWORD` set
- JWT hard-coded RS256 (validator raises on other algorithms)
- Stripe/Neo4j/Odoo/Google OAuth/SMTP credentials all defaulted to empty strings — fail-closed when unset
- `service_version: "5.1.0-rc1"` (release candidate, not GA)
- `sentry_dsn: ""` default
- Neo4j default connection present but per ADR-108 offline in v1.0

---

## 6. Frontend inventory

**v3 shell (canonical current UI) — 40 `page.tsx` files under `src/app/v3/`:**
Home, companies (list + detail + 360), contacts (list + detail), people (list + detail), crm (list + detail), activities, tasks (list + detail), proposals (list + detail), quotes (list + detail), contracts (list + detail), reviews (list + detail), approvals (list + detail), analytics, sales-dashboard, my-day, effectiveness, cs, admin, settings, data (list + 5 sub-pages: companies, people, imports, er, review-queue), icp, employee, shell.

**Legacy `(dashboard)` shell — 78 `page.tsx` files** still present covering: dashboard, companies, contacts, opportunities, activities, revenue (+ territories, quotas), pipeline (+ analytics), forecast, search (+ analytics), decisions (+ templates), meetings, rag, ai, graph, copilot (+ telemetry), automation (+ workflows/new + analytics), analytics (+ sales/employees/revenue/pipeline/automation/reports/builder), signals, rules, monitoring, customer-success, settings, admin (+ tenants/integrations/billing/audit/config/flags), employees (+ [id] + me), gtm/* (icp, market-sizing, lead-discovery, enrichment, verification, lookalikes, sequences, outreach, website-intelligence, page), studio/* (workflows, territories, scoring, prompt-library, permissions, custom-fields, ai-policies, branding, notifications), marketplace (+ [pluginId]/config + listings), knowledge (+ connectors), rag.

**Dual-shell honesty risk:** the workspace currently maintains BOTH `/v3/*` and `/(dashboard)/*` route trees for many capabilities (companies, contacts, activities, analytics, admin, settings, etc.). Nav (`v3/nav.ts`) only points at `/v3/*`. The `(dashboard)/*` routes remain reachable if URL-typed. This is a UX / IA drift.

**Frontend API routes (Next.js):** only 2 — `api/v1/copilot/query/route.ts` and `api/auth/callback/google/route.ts`. All other data traffic is proxied to backend.

**Build claim (per FINAL_GO_NOGO_ASSESSMENT.md, 2026-09-05):** 109 pages, tsc 0 errors, lint 0 errors — **not re-verified this audit** (would require `npm run build`).

---

## 7. Documentation inventory (highlights)

### Authoritative gate docs (read this audit)
- `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` — 2026-07-22 **NO-GO**, scorecard 38/100 Production Readiness
- `docs/audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md` — 2026-08-17 locked; Phases 1–4 marked CLOSED
- `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` — 2026-09-05 (latest), "pilot-ready with conditions"
- `docs/audit/ga-engineering-audit/AI_HONESTY.md` — mandates `feature_ai_copilot=False` for GA
- `docs/audit/ga-engineering-audit/PAGE_MAP_SALESOS.md` — 2026-07-22 (STALE — pre-v3 rewrite; predates 24-item v3 nav)
- `docs/audit/ga-engineering-audit/PHASE1..PHASE4F_GATE_EVIDENCE_PACK.md` — 5 gate evidence packs

### Data intelligence / master data
- `docs/data/phase6/*` — 22 files (handoff, evidence, gate, PO decision, safety validation)
- `docs/data/phase7/*` — 12 files (planning, implementation, human review, PO decision 2026-09-09)

### ADRs (`docs/adr/`)
- ~40+ ADRs including 0100 (repo canonicalization), 0101 (bootstrap), 0102 (hardening), 0103–0108 (deferrals + Neo4j offline), 0109 (ICP persistence + Kafka posture), 0110–0117 (agent runtime, tasks queue, state machine, evidence, canonical write boundary, security boundary, tool capability, signal-agent integration)

### Other doc surfaces
- `docs/reports/` (session reports, gaps)
- `docs/vnext/` (roadmap, deprecated GO_NO_GO_DECISION.md + GA_CHECKLIST.md — SUPERSEDED)
- `docs/audit/star-audit/` (20-file STAR audit series)
- `docs/audit/current-state/` (19 files — 2026-07-15 snapshot; stale for page counts)
- `docs/adr/index.md`, `docs/api/OPENAPI.md`, `docs/PROJECT_BIBLE.md`, `docs/DOMAIN_MAP.md`, `docs/CAPABILITY_CATALOG.md`, `docs/DECISION_LOG.md`, etc.

**Doc supersession is documented in-place.** Contradictions **updated post-audit (2026-09-13):**
1. `README.md` claims Copilot/Decision Center/Knowledge Graph/Communication Hub all "🟢 Live" — contradicts `AI_HONESTY.md` + `NEO4J_GOVERNANCE_GAP.md` (unchanged; README rewrite is a P2 residual).
2. Migration count differs: on-disk 109 vs AGENTS.md 96 vs FINAL 97 (unchanged).
3. ~~`feature_ai_copilot=True` in code vs `AI_HONESTY.md` mandate `False`~~ → **RESOLVED 2026-09-12/13**: default `False`, tests `is False`, AI_HONESTY aligned.

---

## 8. Deployment / Hosting evidence (read-only)

- **Backend:** Railway (services: main API, celery-worker, celery-beat via `railway.json` + `railway.worker.json` + `railway.beat.json`). Prod URL per README: `salesos-production-96c0.up.railway.app`; staging `salesos-staging.up.railway.app`.
- **Frontend:** Vercel (`vercel.json`, region `iad1`, security headers set).
- **Live health checks NOT executed this audit** (would require network hits; scope kept to code + docs).
- **DB:** PostgreSQL 16 primary (per README). `salesos_test_export/salesos_test.dump` present locally for Phase 7-A restore. Production schema `g1h2i3j4k5l6` per FINAL_GO_NOGO (as of 2026-08-21).
- **Redis:** Deployed, ephemeral only (per Governance Reconciliation §6).
- **Neo4j:** Deployed but OFFLINE per ADR-108 — Railway shows `graph=connected` in health, but no production traffic per governance gap doc.
- **Kafka:** In-memory fallback default (`event_bus_type: "in_memory"`).
- **Backups:** Railway managed backup schedule NOT enabled (residual per FINAL_GO_NOGO).
- **DR:** OPS-01 rows 1–3 + 8 signed 2026-08-24; row 3b Railway backup schedule still BLOCKED-HUMAN.
- **CI:** 9 workflows at `.github/workflows/` (verified). CI schema-drift-gate fixed 2026-08-21 (commit `6f27699`).

---

## 9. Git repository state (READ-ONLY inspection + POST-AUDIT UPDATE)

- **Branch:** `fix/login-and-keys` (checked out)
- **Remote:** `origin  https://github.com/ragheeda-boop/SalesOS.git`
- **HEAD commit (snapshot):** `3bfa6adb  fix: login redirect, CSP dev mode, duplicate React keys`
- **HEAD commit (post-audit 2026-09-13):** `951a86f1  docs: record tick 32 commit hash in loop state` — 69 local commits since snapshot, **none pushed**
- **Dependabot branches:** 15+ open PRs on remote for docker/GHA/npm updates
- **Working tree — CRITICAL FINDING (snapshot) → REPAIRED (post-audit):**
  - Snapshot: **4,748 files marked deleted** in `git status`, 27 top-level `??` entries, consistent with `git rm --cached -r .` never reversed.
  - **Post-audit (2026-09-12, A1): `git reset HEAD -- .` → index == HEAD, 0 staged deletes.** The purge-on-commit danger is **gone**.
  - **Residual (still to triage by name):** **25 unstaged D** (files really gone from disk), **37 unstaged M**, **512 untracked**. **Never `git add -A`.**
  - **Status trap:** plain `git status` **aborts silently** on the broken `engineering-os` submodule; always use `git status --porcelain --ignore-submodules=all`.

---

## 10. Feature flags catalog (Settings class — `salesos/backend/app/config.py`)

| Flag | Default | Notes |
|------|---------|-------|
| `feature_ai_copilot` | **False** | **Post-audit reconciled 2026-09-12/13** — default `False` (config.py:162); 12 test files/15 asserts `is False`; 101/101 Docker PASS; AI_HONESTY.md aligned. Lab via `FEATURE_AI_COPILOT=true`. |
| `feature_signal_marketplace_postgres` | False | Runtime-flippable |
| `feature_crm_kanban` | False | Non-GA |
| `feature_httponly_access_cookie` | False | Half-break flag |
| `feature_search_fuzzy_v2` | False | |
| `entitlement_enforcement_enabled` | True | |
| `quota_enforcement_enabled` | True | |
| `demo_mode` | False | |
| `kg_allow_sql_fallback` | None → env-derived | KG offline in production per ADR-108 |
| `debug` | False | |

---

## 11. Tests inventory (per AGENTS.md session summaries)

- Backend regression (2026-09-05): **353/353 PASS** (Agent Reach 58 + Signal Actions 65 + HITL 50 + Effectiveness 37 + Calibration 101 + E2E 42)
- Full unit suite (2026-08-19): **2388 passed, 10 xfailed, 3 skipped**
- Full unit suite (2026-08-23 Phase 4F): 2761 passed, 56 pre-existing failures (env-dependent), 3 skipped, 10 xfailed, 7 errors — documented as no NEW failures
- E2E Commercial Loop: **42/42 PASS**
- Frontend build: 109 pages, 0 tsc errors, 0 lint errors
- **Tests NOT re-run this audit.** Numbers accepted from AGENTS.md as reported; classified as **build validated** (per honest label), not independently reproduced this audit.

---

## 12. Data intelligence status (from `docs/data/phase6/*` and `docs/data/phase7/*`)

- **Phase 6 (Data quality / classification / OPTION-C):** technically CLOSED — schema gate ×2 idempotent, 91/91 unit + integration tests, dry run over 296,746 companies with all 9 safety counters = 0, DB safety validation 12/12 PASS. Verdict: **PHASE_6_READY** for the DB-safety/evidence gate.
- **Phase 6 human review NEEDED (not done):** 54,185 review candidates (6,908 P1 + 46,736 P2 + 541 P3) + 36 suspicious short-CR accounts + reconciliation of DI's P1/P2 enrichment-priority formula.
- **Phase 7-A (Assisted human review):** PO decision recorded 2026-09-09 (D1 SEPARATE 9 branch-CR pairs, D2 return 1,763 missing-counterpart pairs to engineering, D3 114 domain-equal + 4 P1 CR-field confirms, D4 escalation owner = Ragheb (PO)). Capture-only writes applied 2026-09-10 on `salesos_test` (2,697 P3 + SHORT_CR + 4 TRIAGE rows added; Phase 6 tables Δ = 0). **Production NOT approved. No merges. No CR promotion. Phase 7-B/7-C not authorized.**

---

## 13. What was inspected during this audit — file/read summary

| Category | Read/Listed |
|----------|-------------|
| Fully read | `AGENTS.md` (78 KB), `PRODUCT_BIBLE.md`, `README.md`, `salesos/backend/app/config.py`, `salesos/backend/app/boot/routers.py`, `salesos/frontend/src/components/v3/nav.ts`, `salesos/frontend/vercel.json`, `railway.json`, `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md`, `SALESOS_MASTER_CLOSURE_SEQUENCE.md`, `FINAL_GO_NOGO_ASSESSMENT.md`, `AI_HONESTY.md`, `PAGE_MAP_SALESOS.md` (partial), `docs/data/phase6/PHASE6_HUMAN_REVIEW_PO_GATE.md` (partial), `docs/data/phase7/PHASE7A_PO_DECISION_2026-09-09.md` |
| Listed / enumerated | Root, `salesos/`, `salesos/backend/{app, app/modules, app/routers, app/boot, app/alembic/versions, domains}`, `salesos/frontend/src/app/{v3, (dashboard), api}`, `docs/audit/ga-engineering-audit/*`, `docs/data/phase6/**`, `docs/data/phase7/**`, `packages/**`, `archive/*` (depth 2), `engineering-os/*`, `migration-log/*`, `infrastructure/*`, `.github/workflows/*` |
| Git commands run (read-only) | `git status --short` (grouped), `git log --oneline -20`, `git branch -a`, `git remote -v`, `git merge-base fix/login-and-keys origin/master` |

---

## 14. What was NOT inspected — see `AUDIT_LIMITATIONS.md`

See sibling document for detailed limitations (live hosting, MCPs, DB rows, browser QA, full test re-execution, node_modules, .venv, private secrets, every ADR). The "4,748 docs files" reference is superseded — index was unpoisoned 2026-09-12 (see §9 post-audit).

## Current overlay — Agent Reach bridge — 2026-09-21

The internal Agent Reach-to-Fact Review adapter and authenticated human proposal route are documented in [report 27](27_AGENT_REACH_FACT_REVIEW_BRIDGE_2026-09-21.md). The route is proposal-only, requires `agent_reach:READ` and `master-data-review:CREATE`, and is proven by **66/66 focused checks** plus the OpenAPI contract on `salesos_test`. It does not invoke a provider, establish an automated Minder caller, or mutate CRM.

## Google Maps source/provider gate — 2026-09-21

Current Google Maps terms prohibit scraping/extracting Maps content for use outside Maps and prohibit use of Maps Core Services for a listings/directory service or to create/augment an advertising product. Places API output also cannot be retained as a durable SalesOS lead dataset; the persistent place_id exception does not extend to company fields. The standalone business/google-maps-scraper-kit is therefore **not approved as a SalesOS lead source**, and its CSV/JSON output must not feed Master Data, Fact Review, or CRM. SalesOS already rejects google_maps as an Agent Reach research channel; a new explicit proposal-classifier regression locks that boundary. No Maps provider was called. Durable spend reservations have since been implemented and verified only on salesos_test; they remain unconfigured, so no provider can run. See [report 30](30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md) and [report 29](29_GOOGLE_MAPS_PROVIDER_GATE_2026-09-21.md). Phase 7 remains BLOCKED, production NOT APPROVED, and roadmap remains **46%** (52/113 last full census; not re-censused).


## New verification report

| File | Scope | Status |
|---|---|---|
| 30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md | Durable provider spend budget ledger, concurrency and lifecycle tests, test database safety, stopped Maps scraper status | Complete; test-only; no provider enabled |


## Additional verification report

| File | Scope | Status |
|---|---|---|
| 31_AGENT_REACH_VALUE_SUPPORT_GATE_2026-09-21.md | Proposed-value lexical relevance screen, tenant DB regression, trust boundary | Complete; review-only; no CRM write |

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

## Current report map — Refresh 49

| Reports | Scope | Current interpretation |
|---|---|---|
| 32–35 | Capability closures and verification loops | Code-scope progress reached 85/113; operational gates separate |
| 36–40 | Phase 7 snapshot, P2 review and capture routes | Review evidence/capture only; no canonical promotion |
| 41–46 | P1/Fuzzy/Short-CR/MA review and derived files | 792 deterministic proposals; unresolved/escalated cases preserved |
| 47 | Phase 7 gate acceptance | Safe hold; GP-to-person promotion contract required |
| 48 | Production readiness loop | Scoped verification pass; production no-go |
| 49 | Full audit refresh | Current canonical snapshot and all remaining release gates |
