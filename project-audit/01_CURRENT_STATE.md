# 01 — Current State — الوضع الحالي / End-to-end honest snapshot

**Date:** 2026-09-12
**Method:** Cross-reference of code (`salesos/`), governance (`AGENTS.md`, `docs/audit/ga-engineering-audit/`), ADRs, phase evidence packs, and static configs. **Live systems NOT probed this audit** (see `AUDIT_LIMITATIONS.md`).

---

## 1. Product identity — what SalesOS is TODAY

**FACT:** SalesOS is a **Saudi-first, bilingual (AR/EN), DDD-architected sales intelligence platform** built as a monorepo under `salesos/` (FastAPI + Next.js 15). Domains: Companies, Contacts, Opportunities, Pipeline, Activities, Revenue, Proposals, Reviews, Approvals, ICP, Master Data (Muhide/Saudi CR), Signals, HITL, Effectiveness, Copilot, RAG, NBA, Communication Hub (Gmail/Calendar), Employee 360.

**FACT — Product boundary (per `00-EXECUTIVE-SUMMARY.md` + `AGENTS.md` §1):** SalesOS is the ONLY shipped product tree in this repo. Zero code matches for `AuditOS`, `DecisionOS`, `LocalContentOS`. Marketing that claims a "multi-product platform GA" is contradicted by code.

**INFERENCE:** The workspace-level name "**AQLIYA**" (per user rules) refers to a broader private-governed intelligence-platform vision. In shipped code, only SalesOS exists.

---

## 2. Layer-by-layer honest status

### 2.1 Phase 1 — Product Core

| # | Area | Gate Status | Evidence |
|---|------|-------------|----------|
| 1 | Domain Model | CLOSED | Alembic `a1b2c3d4e5f6_phase1_product_core_domain` (Company owner_id + segment; UBOM deprecated) |
| 2 | CRM | CLOSED | `PATCH /api/v1/companies/{id}/assign`; contacts module |
| 3 | Deals | CLOSED | Opportunity owner_id + assign; commercial router |
| 4 | Pipeline | CLOSED | `PipelineService.enter_stage()` uses opportunity_context; qualification runs on real data |
| 5 | Activities | CLOSED | Alembic `c3d4e5f6a7b8` — activity FK links to company/contact/deal |
| 6 | Revenue | CLOSED | `RevenueBrain._generate_forecasts()` base_revenue=0.0 (removed hardcoded $1M); revenue planning router mounted; analytics cubes wired to real DB |
| 7 | Proposals | CLOSED | 8 endpoints; FE `/v3/proposals` list+detail |
| 8 | Reviews | CLOSED | NEW domain + 7 endpoints + FE `/v3/reviews` |
| 9 | Approvals | CLOSED | RBAC enforcement in `POST /quote/approve`; `_record_approval_audit()` → audit_logs |

**Honest label:** **build validated + runtime validated + browser validated (9/9 v3 pages PASS)** per `PHASE1_GATE_EVIDENCE_PACK.md`. Not re-verified this audit.

### 2.2 Phase 2 — Intelligence

| # | Area | Gate Status | Evidence |
|---|------|-------------|----------|
| 1 | Commercial Memory | CLOSED | `domains/commercial/memory/` — 21 event types, 9 entity types |
| 2 | Account Intelligence | CLOSED | `intelligence/account_intelligence.py` — insights cite evidence chain |
| 3 | Deal Intelligence | CLOSED | `intelligence/deal_intelligence.py` |
| 4 | Pipeline Analytics | CLOSED | ForecastCube wired to real DB (was stub) |
| 5 | Forecasting | CLOSED | `intelligence/forecasting.py` — Commit/Best Case/Pipeline/Risk from durable data (no LLM) |
| 6 | Evidence Chain | CLOSED | `domains/commercial/evidence/` — Insight→Evidence→Source→Timestamp→Confidence |
| 7 | Recommendations | CLOSED | `intelligence/recommendation_engine.py` — deterministic, not LLM |

**Honest label:** **build validated + runtime validated** per `PHASE2_GATE_EVIDENCE_PACK.md`.

### 2.3 Phase 3 — AI

| # | Area | Gate Status | Evidence |
|---|------|-------------|----------|
| 1 | Copilot | CLOSED | 5 modes (Ask/Explain/Summarize/Investigate/Recommend); Recommend creates ApprovalRequest (HITL) |
| 2 | RAG | CLOSED | Phase 2 evidence chain + citations + tenant isolation (`rag_rls` migration) |
| 3 | NBA | CLOSED | HITL gate wired via `ApprovalService` |
| 4 | AI Governance | CLOSED | `intelligence/governance_audit.py` — policy/HITL/PII enforcement to `audit_logs` |
| 5 | Human Approval | CLOSED | 6-status state machine, RBAC levels, 6 REST endpoints; Alembic `f6a7b8c9d0e1` |
| 6 | Evaluation gates | CLOSED | Groundedness + hallucination detection + quality gates (`EnhancedEvaluationRunner`) |

**FACT — provider path:** DEV-only (AI Horde / Cydonia-24B). Per `PROVIDER-EVAL-2026-08-23.md`: multilingual drift, input-gaslighting, 406 storms with empty completions. Production no-go. No signed contract with OpenAI Enterprise / Azure OpenAI / Anthropic evidence.

**FACT — grounded discipline:** All 13 Copilot agents use a shared `EvidencePack` loader that: (a) pins RLS via `set_config('app.tenant_id', …, true)` (DEC-085), (b) enforces PII strip (positions/counts only, no names/emails/phones), (c) uses value banding on money fields, (d) returns honest UNKNOWN/INSUFFICIENT EVIDENCE when data absent, (e) does NOT call the LLM when evidence path is empty. Live probes confirmed cross-tenant isolation and zero fabrication. See `AGENTS.md` §19–§22.

**CONTRADICTION:** `feature_ai_copilot: bool = True` in `salesos/backend/app/config.py:162` — flipped 2026-08-19 per code comment. `AI_HONESTY.md` §2 still lists default as **False** and mandates keeping it False for GA. Marketing must not claim Copilot GA. Reconcile by either reverting the default or re-signing `AI_HONESTY.md`.

### 2.4 Phase 4 — Platform

| # | Area | Gate Status | Evidence |
|---|------|-------------|----------|
| 1 | EventBus | CLOSED | No split-brain; DLQ persistent (Alembic `g1h2i3j4k5l6`, `event_dead_letters` table) |
| 2 | Capability Registry | CLOSED | pytest wrapper gates CI; DEC-134 / criterion 5.3 |
| 3 | Migrations | CLOSED | 109 files on disk; 1 head; drift check via `check_alembic_head.py --local-only` in CI |
| 4 | Observability | CLOSED | `_check_kafka_status()` shared across 4 endpoints; SLA monitor; Prometheus `/metrics`; structured logging |
| 5 | Background Jobs | CLOSED | IL-2B.2 lease/recovery hardened; EXHAUSTED task alerting |
| 6 | Backup / Restore | CLOSED | Scripts functional; `infra/docker/backup/Dockerfile` COPY paths fixed; DR drill simulated (non-prod) |
| 7 | Deployment | CLOSED | Railway (backend + celery-worker + celery-beat) + Vercel (frontend) canonical; K8s quarantined per DEC-149 |

**RESIDUAL:** Railway managed backup schedule NOT enabled (row 3b BLOCKED-HUMAN); `preDeployCommand` drift (live uses `init_db()`, `railway.json` says `alembic upgrade head`); OAuth staging pending Google Cloud Console.

### 2.5 Productization (2026-09-05 gate)

- 353/353 backend tests
- 109-page FE build, tsc 0, lint 0
- 42/42 E2E Commercial Loop
- 35/35 V3 pages CLEAN (0 mock data instances)
- `getDemoData()` removed from graph + knowledge (honest empty states)
- Logger bug fix in `signal_actions/router.py` (NameError)
- Broken link fix `/v3/data/review-queue`
- Nav 20 → 24 items; command palette 31 → 35
- V3 layout "Not Production GO" marker REMOVED; Studio/Admin markers KEPT

### 2.6 Phase 6 — Master Data (Saudi companies)

**FACT — technical CLOSED:**
- Schema gate script `phase6_schema_gate.py` created 18 tables (11 foundation + 7 Phase 6); idempotent ×2
- `phase6_dry_run.py` processed 296,746 accounts, staged 1,238,635 changes, all 9 safety counters = 0
- 91/91 unit + integration tests pass
- DB safety validation 12/12 PASS (per `PHASE6_FINAL_DB_SAFETY_VALIDATION.md`)
- All 7 Phase 6 modules (classification, industry, quality, readiness, canonical, relationships, pipeline) landed
- OPTION-C classifier corrected: CONTACTABILITY (email/phone) ≠ IDENTITY; only valid CR / Apollo Account ID / real (non-generic) domain establish identity
- No external APIs (no Apollo, Balady, Najiz, ZATCA, government APIs called at runtime)

**BLOCKER — Phase 7 NOT started:**
- 54,185 candidates await human review (6,908 P1 + 46,736 P2 + 541 P3)
- 36 SUSPICIOUS_SHORT separator-list accounts need government-registry adjudication
- DI's original P1/P2 enrichment-priority formula not reconstructed (best 18,657/17,222 vs official 23,306/37,719)
- 2,661 fuzzy pairs remain human-review population (never auto-merge per ADR-0104)
- Production ingestion into `salesos` DB forbidden until Phase 7 gate + Product/PO sign-off

### 2.7 Phase 7-A — Assisted human review

**FACT — PO decision recorded 2026-09-09** (`PHASE7A_PO_DECISION_2026-09-09.md`):
- D1: SEPARATE all 9 branch-CR pairs (same name + different CR = distinct legal entity)
- D2: 1,763 P3 pairs with `global_company_id_b` NULL → return to engineering (not reviewer task)
- D3: 114 domain-equal HIGH_MATCH pairs = first review batch (NOT auto-MATCH); 4 P1 CR-field conflicts CONFIRMED
- D4: Escalation owner = Ragheb (PO)

**FACT — Executed 2026-09-10** on `salesos_test` only:
- Restored from `salesos_test_export/salesos_test.dump`
- Applied 9 SEPARATE + 1,763 deferred_engineering + 114 note + 4 TRIAGE CONFIRM writes
- Phase 6 table Δ = 0
- Production `salesos` DB NOT touched
- Phase 7-B (canonical merge) + Phase 7-C (CR promotion / segmentation) + production ingestion NOT AUTHORIZED

---

## 3. Repository state

| Aspect | Reality |
|--------|---------|
| Branch | `fix/login-and-keys` — ahead of `origin/master` by 2 commits |
| HEAD | `3bfa6adb  fix: login redirect, CSP dev mode, duplicate React keys` |
| Working tree | **CRITICAL:** 4,748 files staged as deleted; 27 top-level entries untracked (`??`). Files exist on disk. Pattern consistent with `git rm --cached -r .` never reversed. **A commit from this state would purge the repository.** |
| Untracked at root | `.ai/`, `.engineering/`, `.github/`, `salesos/`, `docs/`, `packages/`, `assets/`, `infrastructure/`, `migration-log/`, `archive/`, `salesos_test_export/`, `scripts/`, plus root `.env.example`, `README.md`, `AGENTS.md`, `PRODUCT_BIBLE.md`, `RUNBOOK.md`, `docker-compose.yml`, `Dockerfile.railway`, `Dockerfile.railway.celery`, `railway.json`, `railway.beat.json`, `railway.worker.json`, `.gitattributes`, `.gitignore`, `.gitmodules`, `.semgrepignore`, `.trivyignore`, `.vercelignore` |
| Dependabot | 15+ open remote branches for GHA/docker/npm updates |
| Submodules | `engineering-os` per `.gitmodules` |

**Action required (outside this audit's write scope):** the repo must be repaired via `git reset HEAD --` and re-adds (or `git restore --staged .` then careful re-tracking) BEFORE any commit is made. This audit does NOT perform that operation.

---

## 4. Deployment + hosting reality

| Layer | Provider | Reality |
|-------|----------|---------|
| Backend API | Railway | `salesos-production-96c0.up.railway.app` (per README) — live status UNKNOWN this audit |
| Celery worker | Railway | Separate service (per `railway.worker.json`); dispatched via `RAILWAY_SERVICE_NAME` case-statement in start command |
| Celery beat | Railway | Separate service (per `railway.beat.json`) |
| Frontend | Vercel | region `iad1`, security headers set (`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy`) |
| Postgres | Railway managed | `salesos_app` role enforced in staging/prod (fail-closed if `APP_POSTGRES_PASSWORD` empty). Prod schema last verified `g1h2i3j4k5l6` on 2026-08-21 |
| Redis | Railway | Ephemeral only; no persistence obligation |
| Neo4j | Railway | Deployed but per ADR-108 OFFLINE for v1.0 — governance gap (see `NEO4J_GOVERNANCE_GAP.md`) |
| Kafka | none | `event_bus_type` default `in_memory`; Kafka referenced but not required |
| Meilisearch | none required | Referenced in config but not part of critical path |
| Backups | Railway managed **NOT enabled** | Row 3b BLOCKED-HUMAN per FINAL_GO_NOGO |
| CI | GitHub Actions | 9 workflows at `.github/workflows/` |
| Domain / SSL | Railway subdomain | No custom domain evidence in this audit |
| Monitoring | Prometheus /metrics + structured logs | Sentry DSN empty by default |
| CSP | Enabled in Next.js frontend | Per ADR-102 |

**Live probes NOT run this audit.** Verification of live `/health`, `/version`, `/openapi.json` would require MCP/curl inspection outside read-only scope.

---

## 5. Frontend + UX current state

**FACT — dual shell coexists:**
- `/v3/*` — 40 pages, canonical current UI, 24-item nav, 4 data sub-pages
- `/(dashboard)/*` — 78 legacy pages still routable (dashboard, opportunities, gtm/*, studio/*, marketplace/*, knowledge/*, revenue+territories+quotas, forecast, decisions, meetings, rag, ai, graph, copilot+telemetry, automation+workflows/new+analytics, analytics+sales/employees/revenue/pipeline/automation/reports/builder, signals, rules, monitoring, customer-success, admin+tenants/integrations/billing/audit/config/flags, employees[+me+[id]])

**FACT — dead surfaces per `PAGE_MAP_SALESOS.md` (STALE 2026-07-22 but structurally still informative):**
- `/nba` in i18n but no page (planned-missing)
- Several 404 / 500 API paths noted (search analytics, workflows analytics, copilot telemetry API)
- Demo fallbacks in revenue/territories, revenue/quotas (must confirm still cleaned post-2026-09-05)
- Mock data cleanup done in graph + knowledge (per §39)

**HONESTY MARKERS:**
- V3 layout "Not Production GO" marker REMOVED 2026-09-05
- Studio/Admin markers KEPT (no live LLM / external deps)
- GTM pages fixture data — labeled honest per §39

**INFERENCE — IA drift:** With 24 v3 nav entries + 78 legacy shells still routable, discoverability is confusing and QA surface is 2×. This is a **product-strategy scope decision**, not a bug.

---

## 6. Data + AI — brutal honesty

### 6.1 Data

- **Muhide dataset:** 296,746 companies + 1,124 people (1,102 linked + 22 unlinked) + 314,421 mappings + 862,775 source rows + 6 source files + 1,524,725 provenance rows in `salesos_test`
- **Production DB:** live schema at `g1h2i3j4k5l6` (2026-08-21) but has **not** received Muhide ingestion — `salesos` prod DB per FINAL_GO_NOGO §Governance Reconciliation has 141,221 companies (a different, older population); Muhide 296,746 stays in test
- **Real live tenant activity:** the only tenant with CRM data in local DB during Phase 4A audit was `pif` (1 deal, 2 contacts) — otherwise the 5 companies were each in a different tenant (mostly empty)
- **rag_documents:** tenant A=5 (Agent-C pilot seed), tenant B=0 — de facto empty corpus
- **ICP profiles:** `pif-icp-demo` seeded once; test cleanup wipes it — pilot data
- **Signal marketplace:** 22 platform signals from 3 knowledge packs (construction / healthcare / financial-services), GLOBAL_PLATFORM classification

### 6.2 AI

- Provider: **DEV-ONLY AI Horde / Cydonia-24B** — production no-go per `PROVIDER-EVAL-2026-08-23.md`
- Quota accounting live and correct (44,535 ai_tokens / 52 events cumulative in a Phase-4F local run)
- Grounded EvidencePack loop proven for all 13 agents
- Real customer LLM production quality: **UNKNOWN — never proven on production traffic**
- FE Decision package: STUB (`salesos/frontend/packages/platform/decision/index.ts` throws)

---

## 7. Security posture (evidence-based, not tested this audit)

**Genuine strengths (from code):**
- RS256-only JWT enforced (config validator raises on other algorithms)
- Dual DB roles: `salesos` (owner, BYPASSRLS) for migrations only; `salesos_app` (application, RLS-enforced) for runtime — staging/prod REFUSE to boot without `APP_POSTGRES_PASSWORD`
- CSRF middleware; bare `X-API-Key` no longer bypasses (fixed per FINAL_GO_NOGO §2 P0-08)
- Webhook SSRF 5-layer pinning per `url_safety.py`
- Cross-tenant Decision Center IDOR closed (P0-01 fixed)
- audit_logs on approval + governance events

**Weaknesses / gaps (from docs, not re-tested):**
- No third-party pentest evidence in this audit
- OAuth staging not configured (Google Cloud Console pending)
- Sentry DSN empty by default (no live error stream)
- Neo4j deployed but offline — governance gap (traffic path unclear)
- No signed SBOM/SCA in this audit's scope
- KSA PDPL compliance NOT formally certified

---

## 8. Contradictions to resolve (source-of-truth clashes)

| # | Contradiction | Where | Recommended resolution |
|---|--------------|-------|------------------------|
| C-01 | `feature_ai_copilot=True` vs `AI_HONESTY.md` mandate False | `config.py:162` vs `AI_HONESTY.md` §2 | Either revert to False, or rewrite AI_HONESTY with signed PRC evidence |
| C-02 | README "🟢 Live" for Copilot/KG/Decision Center/Comm Hub vs AI_HONESTY + ADR-108 + FE-STUB | `README.md` §Domains | Rewrite README Domain table with honest labels |
| C-03 | Migration count: 109 on disk vs AGENTS.md "96" vs FINAL "97" | disk vs docs | Reconcile in AGENTS.md session summary |
| C-04 | "Production GA NOT DECLARED" (FINAL) vs README "🟢 Live" | disk | README needs "pilot-ready with conditions" banner |
| C-05 | `PAGE_MAP_SALESOS.md` dated 2026-07-22 uses legacy shell; v3 (24 nav items) is the actual current shell | `PAGE_MAP_SALESOS.md` vs `nav.ts` | Deprecate old page map or replace with v3-first version |
| C-06 | Dual FE shells with overlapping capabilities | `/v3/*` vs `/(dashboard)/*` | Product decision: retire one, or make one clearly internal |
| C-07 | Phase 6 dry-run + Phase 7-A capture on `salesos_test` vs Muhide NOT in `salesos` production DB | `salesos_test` vs prod | Explicit product decision + resourcing to promote |

---

## 9. Non-shipped features documented as if shipped

| Feature | Doc claim | Reality |
|---------|-----------|---------|
| Multi-product platform (AuditOS / DecisionOS / LocalContentOS) | Vision docs | Zero code — do not claim in sales |
| Autonomous Sales Agent (12-month horizon per Product Bible) | Vision | Zero code today — do not conflate |
| AI-native GA | Historical language | Explicitly forbidden by AI_HONESTY.md |
| Live production Copilot / RAG | Marketing language | Code exists, provider is DEV-ONLY, tenant corpus is 5 rows |
| Neo4j-powered relationship graph | Feature list | ADR-108 OFFLINE for v1.0 |
| Production Muhide data live | Some session summaries | Only in `salesos_test`; prod DB has a different 141,221-row population |

---

## 10. What is TRUE and DEFENSIBLE

- ✅ 4-phase gate discipline with evidence packs — best-in-class governance
- ✅ Product Core layer landed with 9/9 areas + 278 tests + browser QA
- ✅ Bilingual (AR/EN) UX + Saudi CR normalization is genuine local edge
- ✅ Tenant isolation via RLS + `salesos_app` role + fail-closed defaults
- ✅ Grounded, PII-safe, cross-tenant-safe Copilot with honest UNKNOWN degradation
- ✅ Phase 6 dry-run 0 safety violations across 296,746 companies
- ✅ Alembic drift gate + capability registry gate in CI
- ✅ Persistent DLQ + observability + structured logging
- ✅ Fail-closed defaults for Stripe / OAuth / Neo4j / SMTP
- ✅ ADR discipline (110+ ADRs, indexed)

---

## 11. Bottom line — three sentences

1. **Engineering:** SalesOS is a **serious, well-architected, evidence-governed product**, with Product-Core + Intelligence + AI + Platform layers all landed as code and tested — this is not vaporware.
2. **Business:** But it has **zero paying customers proven this audit, no signed pricing, no live production LLM, no external pentest, no active DR backup schedule, and its flagship Saudi data asset is stuck behind an unfinished human-review workstream**.
3. **Verdict:** It is **`pilot-ready with conditions`** — perfect for a founder-led design-partner pilot with 1–3 named Saudi B2B tenants, and **not** production-GA sellable-as-SaaS until the human decisions in §8 and Phase 7 close.
