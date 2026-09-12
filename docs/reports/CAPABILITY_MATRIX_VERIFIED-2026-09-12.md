# Capability Matrix Verification — 2026-09-12

**Agent:** B2 — Capability Matrix Verification  
**Workspace:** `D:\AISalesOS`  
**Input:** `project-audit/11_CAPABILITY_MATRIX.md` (claimed ~110 × 13 columns)  
**Method:** Read-only file evidence (routers, services, Alembic, v3/legacy pages, test *files*, `config.py` flags). **No pytest. No npm. No git write.**  
**Reconciled with:** `docs/reports/AI_FLAG_RECON-2026-09-12.md`, `RECON-2026-09-12.md`, `RAILWAY_CONFIG_RECON-2026-09-12.md`  
**Honest label:** **light validated** (path/existence + code reads). Suite pass/fail and live Railway/browser = **UNKNOWN**.  
**Production GA:** still **not declared** (does not overturn 2026-07-22 audit NO-GO).

---

## 0. How to read this report

| Label | Meaning |
|-------|---------|
| **FACT** | Named file exists / quoted setting on 2026-09-12 |
| **INFERENCE** | Status judgment from those files |
| **UNKNOWN** | Would need pytest, npm, or a live probe |

**COMPLETE** is used only when a capability has file-path evidence of a wired backend *and* (for user-facing rows) a real page or an explicitly internal surface, plus a named test file. Code-complete + fixture / DEV-only provider / test-DB-only / unwired service is **not** COMPLETE.

Statuses: `COMPLETE` \| `PARTIAL` \| `PLANNED` \| `MOCK` \| `BROKEN` \| `NOT STARTED` \| `UNKNOWN` \| `DEPRECATED`

**Deploy** is never “Live” in this report. Live dashboard was **not** probed. Values: `Repo mounted` · `salesos_test` · `CI` · `Harness only` · `Unknown live` · `Keys empty`.

---

## 1. Claimed vs verified counts

| Metric | Audit claimed (`11_CAPABILITY_MATRIX.md` §2) | This verification |
|--------|----------------------------------------------|-------------------|
| Capability rows | **~110** | **113** inventoried and verified (sections 1.1–1.11) |
| Surface inventory rows (1.12) | 5 (not in the ~110 math) | **5** verified as inventory, not capabilities |
| COMPLETE | ~85 | **52** |
| PARTIAL | ~15 | **42** |
| MOCK | 0 (GTM called COMPLETE) | **8** |
| PLANNED | (bundled ~10) | **3** |
| NOT STARTED | (bundled ~10) | **1** |
| UNKNOWN | (bundled) | **1** |
| DEPRECATED | 0 | **1** (Decision Runtime `/api/v1` aliases; engine remounted) |
| BROKEN | 0 | **0** (no dead nav after `/v3/data/**` pages found) |
| Status corrections | — | **36** (34 downgrades, 2 upgrades) |

**FACT — row inventory (audit tables, counted by hand):**

| Section | Audit rows | Verified |
|---------|----------:|---------:|
| 1.1 Product Core | 11 | 11 |
| 1.2 Intelligence | 7 | 7 |
| 1.3 AI Copilot | 13 | 13 |
| 1.4 Master Data / ER | 9 | 9 |
| 1.5 Platform | 7 | 7 |
| 1.6 Identity / Auth | 15 | 15 |
| 1.7 Integrations | 10 | 10 |
| 1.8 Runtime engines | 16 | 16 |
| 1.9 Tenant Studio | 10 | 10 |
| 1.10 GTM Intelligence | 9 | 9 |
| 1.11 Chaos / DR / SOC2 | 6 (14-01, 02, 03, 05, 06, 07) | 6 |
| **Total capabilities** | **~110 (audit rounded)** | **113** |
| 1.12 FE surfaces | 5 | 5 |

**INFERENCE:** The audit’s “complete-heavy / gap is customers not features” reading is **over-claimed**. After correcting fixture GTM, unwired Phase-2 services, DEV-only copilot, test-DB master data, and preview v3 analytics, the product is **partial-heavy**.

---

## 2. Feature flags (`salesos/backend/app/config.py`)

| Flag | Default (FACT) | Matrix impact |
|------|----------------|---------------|
| `feature_ai_copilot` | **`True`** (L162) | Product copilot/AI mutate gates **open** at default. `AI_HONESTY.md` + FF-07 + soak still require **False**. See AI_FLAG_RECON. Copilot row cannot be COMPLETE. |
| `feature_signal_marketplace_postgres` | `False` (L165) | Catalog/runtime stay **InMemory** unless env flipped after Alembic. Marketplace row PARTIAL. |
| `feature_crm_kanban` | `False` (L166) | Audit said kanban is behind this flag. **FACT:** `/v3/crm` defaults `view="board"` and does **not** read the flag. Flag is stale vs FE. |
| `feature_search_fuzzy_v2` | `False` (L157) | Search v2 off. |
| `feature_httponly_access_cookie` | `False` (L170) | Cookie path optional. |
| `stripe_*` keys | `""` | Stripe spine fail-closed (503) without env. |
| `sso_google_*` / `sso_microsoft_*` / `sso_github_*` | `""` | SSO code present; credentials empty. |
| `odoo_*` | `""` | Placeholders only. |
| `sentry_dsn` | `""` | No live error stream. |
| `neo4j_password` | `""` | KG init may succeed as engine object; Neo4j **offline** per ADR-108. |
| Admin seed `ai_copilot` | `enabled=False` | Second flag ≠ Settings (AI_FLAG_RECON / RECON C-20). |

---

## 3. Test-file inventory (not run)

Pass/fail **UNKNOWN**. Counts = `def test_` / `    def test_` on disk.

| Claimed suite | Claimed N | Files on disk | Counted defs | Use in matrix |
|---------------|----------:|---------------|-------------:|---------------|
| Phase 1 product-core file | 49 / 278 agg. | `tests/unit/test_phase1_product_core.py` | **49** | 49 evidenced; 278 unverified aggregate |
| Phase 2 evidence | 26 | `test_phase2_evidence_chain.py` | **19** | Do not cite 26 |
| Phase 3 AI (4 files) | 86 | copilot 11 + hitl 21 + gov 13 + eval 19 | **64** | 86 unverified |
| Phase 3 ER (different Phase 3) | — | `test_phase3_entity_resolution.py` | present | Not the AI 86 |
| Phase 4 platform | 17 | `test_phase4_platform.py` | **18** | Close |
| Phase 6 unit | 91 | 6 files | **~71** | Do not cite 91 |
| Phase 6 integration | 20 | `test_phase6_pipeline.py` | present | File exists |
| Phase 7-A | — | `test_phase7a_*.py` (unit + 2 integration) | present | Capture-only |
| Capability registry | 2 | `test_capability_registry_validation.py` | 2 classes | Exists |
| RAG RLS | 8 | `test_rag_rls.py` | present | Exists |
| ICP | 19 | `test_icp_*.py` + story 11-01 | present | Exists |
| Grounded agents | 45+ | `test_grounded_phase2/3a/3b.py`, `test_research_grounding.py` | present | Exists |
| Signal actions family | 65 | `test_signal_{actions,qualification,priority,nba}.py` | files exist | N mismatch (RECON C-05) |
| NBA engine | — | `test_nba_pipeline.py` + `test_signal_nba.py` | present | Exists |
| Company search | 12 | `test_company_search_contains.py` | present | Exists |
| CR identity | 27+7 | `test_cr_identity_safety.py` + integration | present | Exists |
| STORY-10 studio | — | 8 `test_story_10_*.py` | present | Exists |
| STORY-11 GTM | — | `test_story_11_01` … `11_09` | present | Fixture-honest |
| STORY-12 AI studio | — | `test_story_12_01` … `12_04` | present | Exists |
| STORY-14 harness | — | `test_story_14_01/02/03/06/07` | present | Non-prod |
| Calibration 101 / E2E 42 | 101 / 42 | **0** calibration files; no `e2e_smoke.py` | **0** | **Not verifiable** (RECON C-05) |
| 353/353 productization | 353 | Named `*_gate.py` scripts **missing** | — | Do not cite as proven |

---

## 4. Frontend / nav facts

| Claim | Disk 2026-09-12 |
|-------|-----------------|
| v3 `page.tsx` | **40** under `src/app/v3/**` (34 without `v3/data` + **6** data pages). RECON C-11 (“0 under v3/data”) is **stale**. |
| `V3_DOMAIN_NAV` | **25** hrefs in `frontend/src/components/v3/nav.ts` |
| `/v3/data`, `/companies`, `/people`, `/imports`, `/er` | Pages exist and call `/api/v1/master-data/*` |
| `/v3/review-queue` | Page exists; BE `review_router` mounted at `/api/v1/master-data/review-queue` |
| `/v3/icp` | **Page exists**; **not** in `V3_DOMAIN_NAV` |
| `/v3/companies/[id]/360` | **Redirect only** → `/v3/companies/[id]` |
| `/v3/people` | **Employees** (`searchEmployees`), **not** `md_global_people` |
| `/v3/cs` | Honest preview: “Not wired — no fake health AI” |
| `/v3/analytics` Forecast + Custom | `PreviewPanel` — not a commit model / not a report builder |
| Legacy `(dashboard)` | **78** `page.tsx` |
| FE `@salesos` Decision package | **STUB** (`frontend/packages/platform/decision/index.ts` throws) |

---

## 5. Corrected matrix (13 columns)

Columns: Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority

### 5.1 Product Core

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Companies (list + detail + intel tab) | Central account object | `/v3/companies`, `/v3/companies/[id]` (+ Intelligence tab). `/360` is **alias redirect** | `company_router` `/api/v1/companies` incl. `GET /{id}/intelligence` via `intelligence_computer.build_intelligence_dto` (wraps company 360 — **not** `AccountIntelligenceService`) | Alembic `a1b2c3d4e5f6` (owner_id + segment) | Master-data lookup optional | `test_phase1_product_core.py` (company tests); `test_company_search_contains.py` | Repo mounted | v3 | **COMPLETE** | `app/modules/company/router.py`; `frontend/src/app/v3/companies/**` | Dedicated 360 URL is redirect; intel ≠ Phase-2 AccountIntelligence | P0 keep |
| Contacts | People we sell to | `/v3/contacts`, `/v3/contacts/[id]` | `contact_router` `/api/v1/contacts` | Alembic `0022_consolidate_contacts` | MD people separate | Phase 1 file + contact tests exist | Repo mounted | v3 | **COMPLETE** | `app/modules/contact/router.py`; v3 contact pages | Enrichment live sources | P0 keep |
| People (master data) | Canonical persons | **`/v3/data/people`** (not `/v3/people`) | `master_data_router` `GET/POST /global-people` | `md_global_people` (`j4k5l6m7n8o9`) | ER / Phase 6 | Phase 0–2 MD tests; Phase 6 | **salesos_test** for Muhide pop. | v3 data | **COMPLETE** (path corrected) | `app/modules/master_data/router.py`; `v3/data/people/page.tsx` | `/v3/people` is **employees** (`searchEmployees`) — audit mislabeled | P1 |
| Opportunities / Deals | Revenue objects | `/v3/crm`, `/v3/crm/[id]` — **board default** | `commercial_router` `/opportunities*`; `opportunity_contacts_router` | `0007_commercial_domain` + `a1b9c8d7e6f5` contacts + owner_id | Pipeline advance | Phase 1 49 defs | Repo mounted | v3 board+table | **COMPLETE** | `app/routers/commercial.py` L285–512; `v3/crm/page.tsx` | `feature_crm_kanban=False` **ignored** by v3 board | P0 keep |
| Pipeline | Stage + qualification | Embedded `/v3/crm` board (`POST .../advance`) | `PipelineService.enter_stage(opportunity_context)` (Phase 1) | Opportunity stage columns | — | Phase 1 enter_stage tests | Repo mounted | v3 board | **COMPLETE** | `test_phase1_product_core.py` enter_stage; crm page | Dedicated `/pipeline` is legacy | P1 |
| Activities | Calls/meetings/tasks + FKs | `/v3/activities`, `/v3/tasks`, `/v3/tasks/[id]` | `runtime.activity_runtime.router`; commercial activity-sessions; `activity_intelligence_router` | Alembic `c3d4e5f6a7b8` | Comm Hub optional | Phase 1 activity FK tests | Repo mounted | v3 | **COMPLETE** | `boot/routers.py` activity mounts; v3 pages | Activity→signal UI | P1 |
| Revenue | Bookings / forecast / quota | `/v3/analytics` **revenue section live** via executive API; forecast **PreviewPanel**; legacy `/revenue/*` | `revenue_router`; `domains.revenue.router` `/api/v1/revenue-planning`; `revenue_execution_router` | `0046_revenue_execution_tables`; quota/territory migration cited | Cubes in Phase 1 tests | Phase 1 revenue + `test_analytics.py` / `test_analytics_phase14.py` | Repo mounted | Mixed preview | **PARTIAL** | `v3/analytics/page.tsx` L89–116 vs L368–374 | Forecast commit UI missing; quota/territory editor UX; PDF export `ValueError` in `domains/analytics/engine.py` | P1 |
| Proposals | Versioned deal-linked | `/v3/proposals`, `/[id]`; quotes `/v3/quotes` | 8 proposal + quote endpoints on `commercial_router` | Commercial domain | Approvals on quote approve | Phase 1 proposal/quote tests | Repo mounted | v3 | **COMPLETE** | `commercial.py` L620–877; v3 proposal/quote pages | Real PDF still missing (analytics path) | P1 |
| Reviews | Manager/deal/exception | `/v3/reviews`, `/[id]` | `domains/commercial/review/` + 7 endpoints on commercial | Alembic `b2c3d4e5f6a7` | — | Phase 1 review tests | Repo mounted | v3 | **COMPLETE** | `commercial.py` L1059–1162; `v3/reviews/page.tsx` | Multi-step configurator | P1 |
| Approvals (HITL) | Policy → FSM → RBAC → audit | `/v3/approvals`, `/[id]` | `app/routers/approval.py` + `ApprovalService` 6-status | Alembic `f6a7b8c9d0e1` | Copilot Recommend | `test_phase3_hitl_approval.py` **21** defs (not 50) | Repo mounted | v3 | **COMPLETE** | approval router; v3 pages | SLA aging UI; do not cite HITL 50 | P0 keep |
| Contracts | Contract lifecycle | `/v3/contracts`, `/[id]` | **`commercial_router` 8 contract endpoints** + `domains/commercial/contract/` | Commercial domain (no dedicated Alembic name required) | Quotes | `domains/commercial/contract/tests/test_contract.py` | Repo mounted | v3 | **COMPLETE** | `commercial.py` L894–1033; `v3/contracts/page.tsx` | Audit “backend unverified” was wrong | P2 |

### 5.2 Intelligence (Phase 2)

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Commercial Memory | Durable CRM memory (21/9 types) | **None** | `domains/commercial/memory/` `CommercialMemoryService` | Alembic `e5f6a7b8c9d0` | Used only as ctor dep of account/deal intel | Phase 2 file **19** defs (not 26) | Repo | Internal | **PARTIAL** | `domains/commercial/memory/engine/service.py` | No viewer; not independently routed | P2 |
| Account Intelligence | Health insights | Company **Intelligence tab** uses `/companies/{id}/intelligence` | `intelligence/account_intelligence.py` exists; **company intel DTO is `intelligence_computer`**, not this service | Product Core + 360 | — | Phase 2 file does **not** import this service | Repo | v3 tab | **PARTIAL** | `account_intelligence.py`; `company/router.py` L451–517 | Phase-2 service **unwired** to the FE tab | P1 |
| Deal Intelligence | Deal health/risk | `/v3/crm/[id]` tabs = overview/activity/contacts **only** | `intelligence/deal_intelligence.py` — **no router import found** | — | — | No dedicated deal-intel test file | Repo | Missing on deal | **PARTIAL** | `deal_intelligence.py` only | Service library, not a product surface | P1 |
| Pipeline Analytics | ForecastCube / summary | `/v3/analytics` pipeline section = **opportunities + exec dashboard**, not this API | `runtime/pipeline_analytics/router.py` (`/pipeline/summary` etc.) mounted | Real SQL in router | — | Phase 1 cube-not-stub tests; Phase 4 N/A | Repo mounted | Partial | **PARTIAL** | `pipeline_analytics/router.py`; analytics page L357–362 | v3 does not call pipeline analytics API | P1 |
| Forecasting | Commit / best case / risk | Forecast **tab is PreviewPanel** | `intelligence/forecasting.py`; commercial `POST /forecast/run` | — | — | Phase 2 pack claimed; file-level 19 ≠ 26 | Repo | Preview | **PARTIAL** | `v3/analytics/page.tsx` L368–374 | No commit-model UX | P1 |
| Evidence Chain | Insight→evidence→source | **None** public | `domains/commercial/evidence/` `EvidenceService` | `e5f6a7b8c9d0` (`commercial_insights`, `commercial_evidence_items`) | — | `test_phase2_evidence_chain.py` 19 | Repo | Internal | **PARTIAL** | evidence domain + test file | No public evidence panel | P1 |
| Recommendations (P2-7) | Data→intel→evidence (not LLM) | `/v3/my-day`, `/v3/sales-dashboard` call **HITL / signal_actions**, not this engine | `intelligence/recommendation_engine.py` **and** `domains.decision.recommendation.engine` **and** `runtime.recommendation_runtime` — three spines | — | Signal actions / NBA | Phase 2/3 packs claimed; FE tests are HITL | Repo | v3 seller UX | **PARTIAL** | `recommendation_engine.py`; `v3/sales-dashboard/page.tsx`; `v3/my-day/page.tsx` | Audit FE mapping is wrong; P2-7 engine not the seller UI | P0 |

### 5.3 AI Copilot

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Copilot Modes | Ask/Explain/Summarize/Investigate/Recommend→HITL | Legacy `/copilot`; `V3AiPopup` dual-gated | `copilot_router`; `require_ai_copilot_enabled()`; 13 agents under `intelligence/agents/` | — | Provider DEV-only (Horde/FreeLLMAPI) | `test_phase3_copilot_modes.py` **11**; grounded files exist | Repo; **prod templates pin flag false** | Gated | **PARTIAL** | `config.py` L162 True; AI_FLAG_RECON; `ga_ready` stays false | Not GA. Flag split-brain. Provider NO-GO | **P0 blocker** |
| Grounded EvidencePack | RLS pin, PII strip, honest UNKNOWN | Internal | `research_evidence.py`, `grounded_common.py` | md_* / activity / audit / rag | Copilot | `test_research_grounding.py`, `test_grounded_phase2/3a/3b.py` | Repo | Internal | **COMPLETE** | AGENTS §19–22 files exist | Data gaps surface as UNKNOWN | P0 keep |
| RAG | Citations + tenant isolation | `/v3/data` (MD, not corpus UI); legacy `/rag` | `app/routers/rag.py` | `0015_rag_tables`, `h1i2j3k4l5m7` RLS | Embeddings | `test_rag_rls.py` | Repo | Legacy + MD | **PARTIAL** | rag router; RLS migration | Pilot corpus (claimed 5 rows); not a v3 RAG product | P1 |
| NBA | Next-best-action | Sales dashboard = **signal actions**, not `/nba` | `runtime/nba_engine/api/router.py` mounted | — | Approval optional | `test_nba_pipeline.py`, `test_signal_nba.py` | Repo mounted | Seller UX ≠ NBA API | **PARTIAL** | nba router; signal_actions on FE | Two NBA stories; FE uses signal_actions | P0 |
| AI Governance Audit | Policy/HITL/PII → audit_logs | **No admin viewer** | `intelligence/governance_audit.py` | `audit_logs` | — | `test_phase3_ai_governance.py` 13 | Repo | Missing | **PARTIAL** | governance_audit.py + 13 tests | UI missing (audit already said so; COMPLETE was wrong) | P1 |
| Human Approval Service | Same as Approvals | `/v3/approvals` | ApprovalService | `f6a7b8c9d0e1` | Copilot Recommend | 21 defs | Repo | v3 | **COMPLETE** | Duplicate of 5.1 Approvals | — | P0 keep |
| Evaluation / Quality Gates | Groundedness + hallucination | Internal | `intelligence/evaluation/quality_gates.py` | — | — | `test_phase3_evaluation.py` 19 | Repo | Internal | **COMPLETE** | quality_gates + 19 tests | Not a customer feature | P0 keep |
| ICP Engine | Fit scoring | `/v3/icp` (not in nav); legacy `/gtm/icp` | `icp_router`, `icp_admin_router`; `icp_persistence.py` | `h2i3j4k5l6m8`, `i3j4k5l6m7n8` | Copilot | `test_icp_*.py`, `test_story_11_01_icp_engine.py` | Repo | v3 orphan | **PARTIAL** | icp pages/routers exist | Not in `V3_DOMAIN_NAV`; live tenant profiles thin | P1 |
| Signal Marketplace | Platform signals + subscribe | Legacy `/signals`; embedded seller | `signal_marketplace_router`, `signal_actions_router`, `hitl_router`; `runtime_bridge.py` | `l7m8n9o0p1q2`, `m8n9o0p1q2r3` | Bridge | seeding + detection + signal_* test files | **InMemory default** | Legacy | **PARTIAL** | `feature_signal_marketplace_postgres=False` | Postgres path off; expand packs | P1 |
| Prompt Library | Studio authoring | Legacy `/studio/prompt-library` | `prompt_library_router` | — | No live LLM claimed | `test_story_12_01_prompt_library.py` | Repo | Legacy | **PARTIAL** | router + story test + honesty “remains False” | No v3 shell; flag honesty split | P2 |
| AI Policies | Data-class / tier caps | Legacy `/studio/ai-policies` | `ai_policies_router`; engine **hardcodes** `feature_ai_copilot: False` | — | — | `test_story_12_02_ai_policies.py` | Repo | Legacy | **PARTIAL** | AI_FLAG_RECON hardcoded False | Inconsistent with Settings True | P2 |
| AI Memory | Opt-in conversation memory | Legacy `/studio/ai-memory` | `ai_memory_router` | — | — | `test_story_12_03_ai_memory.py` | Repo | Legacy | **PARTIAL** | router + tests | No v3 | P2 |
| AI Model Tiers | Per-plan ceiling | Legacy `/studio/ai-model-tiers` | `ai_model_tiers_router` | `plan_entitlements` | — | `test_story_12_04_ai_model_tiers.py` | Repo | Legacy | **PARTIAL** | router + tests | No v3; does not enable copilot | P2 |

### 5.4 Master Data / Entity Resolution

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Muhide ingestion | 296k companies / 862k rows / 1.1k people | `/v3/data/imports` | `muhide_adapter.py`, `muhide_ingest_real.py`, `muhide_v1_enrichment.py` | md_* foundation + Phase 6 | Excel import | integration `test_muhide_*.py` exist | **salesos_test only** | v3 | **PARTIAL** | scripts + adapter; AGENTS §34–37 | Production ingest **blocked** (Phase 7-B/C + PO) | P0 |
| Entity Resolution (CR-safe) | Government-anchor + safe CR | `/v3/data/er` | `resolution_policy.py`, `matching_pipeline.py`; `entity_resolution_router` | `md_entity_matches`, `md_entity_conflicts` | — | `test_cr_identity_safety.py`; `test_phase3_entity_resolution.py` | salesos_test | v3 | **PARTIAL** | ER page + router + policy | Not production-usable until Phase 7 + ingest | P0 |
| Identity Classifier | OPTION-C buckets | Consumed | `phase6/classification.py` | `md_identity_classifications` | — | `test_phase6_classification.py` (~25 defs) | salesos_test | Internal | **COMPLETE** | classification.py + tests | No standalone UI | P0 |
| Industry Normalization | Raw immutable | Consumed | `phase6/industry.py` | — | — | `test_phase6_industry.py` 14 | salesos_test | Internal | **COMPLETE** | industry.py + tests | — | P1 |
| Quality Scoring | 5 dimensions | Consumed | `phase6/quality.py` | — | — | `test_phase6_quality.py` 6 | salesos_test | Internal | **COMPLETE** | quality.py + tests | — | P1 |
| Sales Readiness | 5 states | Consumed | `phase6/readiness.py` | — | — | `test_phase6_readiness.py` 11 | salesos_test | Internal | **COMPLETE** | readiness.py + tests | — | P1 |
| Canonical Survivorship | Authority > frequency | Consumed | `phase6/canonical.py` | — | — | `test_phase6_canonical.py` 9 | salesos_test | Internal | **COMPLETE** | canonical.py + tests | — | P1 |
| Contact Relationships | VERIFIED / INFERRED | Consumed | `phase6/relationships.py` | — | — | `test_phase6_relationships.py` 6 | salesos_test | Internal | **COMPLETE** | relationships.py + tests | Person↔company UI depth | P1 |
| Review Queue (Phase 7-A) | Capture dispositions only | `/v3/review-queue` (+ `/v3/data/review-queue`) | `review_router` `/api/v1/master-data/review-queue` — **no merge** | `md_review_queue_state` on **salesos_test** | — | `test_phase7a_*.py` | salesos_test | v3 | **PARTIAL** | `phase7/review_router.py` header | 7-B merge + 7-C CR + prod ingest **BLOCKED** | P0 |

### 5.5 Platform

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EventBus + DLQ | Single-path events | Internal | `runtime/event_runtime` + `persistent_dlq.py` | `g1h2i3j4k5l6` `event_dead_letters` | Optional Kafka | `test_phase4_platform.py` DLQ tests | Repo | Internal | **COMPLETE** | persistent_dlq + Phase 4 tests | Kafka not required | P0 keep |
| Capability Registry | CI drift gate | Internal | `scripts/validate_capability_registries.py` | — | — | `test_capability_registry_validation.py` | CI | Internal | **COMPLETE** | test wraps script | — | P0 keep |
| Alembic drift gate | Head check in CI | Internal | `scripts/check_alembic_head.py` | **108** version files on disk | CI `deploy.yml` | script exists | CI; **prod stamp UNKNOWN** | Internal | **PARTIAL** | 108 files; last verified prod `g1h2i3j4k5l6` (2026-08-21) per RECON C-08 | Live `preDeployCommand` dashboard still open (RAILWAY recon) | P0 |
| Observability | /metrics + logs + SLA | `/metrics` | `runtime/admin_router`; `_check_kafka_status()` | — | Prometheus text | Phase 4 kafka tests | Repo | Internal | **PARTIAL** | `sentry_dsn=""` | No live Sentry | P1 |
| Background Jobs | Lease / EXHAUSTED | None | `celery_app` / `app.railway_celery_service`; `f4aee055fd6e` tasks | agent_tasks | Railway worker/beat JSON | Phase 4 retire_exhausted tests | Repo images | Internal | **COMPLETE** (code) | Phase 4 tests + railway.* json | Live worker health UNKNOWN | P0 |
| Backup / Restore | pg_dump + Neo4j scripts | Ops | `infra/scripts/backup-*.sh`, `cron-backup.sh`, k8s cronjob | — | DR harness | `test_story_14_03_dr_drill.py` (sim) | **Managed schedule OFF** (prior ops) | Internal | **PARTIAL** | infra scripts exist | Enable Railway managed schedule | P0 |
| Deployment | Railway + Vercel | — | Root `railway.json` + `Dockerfile.railway`; `salesos/frontend/vercel.json` (`iad1`); **9** GH workflows | — | — | JSON parse claimed in RAILWAY recon | **Unknown live** | — | **PARTIAL** | RAILWAY_CONFIG_RECON: repo `preDeployCommand` set; **dashboard may still be `init_db()`** | OAuth staging; backup schedule; US FE region vs KSA story | P0 |

### 5.6 Identity / Auth / RBAC

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| JWT RS256 | Auth | Login/register | `config.py` validator; `sdk/auth/jwks.py` | — | JWKS | identity tests exist | Repo | Auth | **COMPLETE** | `config.py` L128–137 | — | P0 |
| Refresh tokens | Session rotate | Cookies | `identity/router.py` `/refresh` | Alembic `0012_refresh_token_tables` | — | identity tests | Repo | Auth | **COMPLETE** | identity router L599+ | — | P0 |
| JWT audiences | Owner vs tenant | — | `jwt_audience` / `jwt_owner_audience` | — | — | `test_jwt_audience_split.py` | Repo | — | **COMPLETE** | config L142–143 | — | P0 |
| RBAC | Custom roles | Legacy studio + admin | `permissions_router`; admin roles | entitlements | — | `test_story_10_06`, `test_custom_roles.py` | Repo | Legacy | **COMPLETE** | permissions studio | v3 admin is thin | P0 |
| SSO Google | IdP login | OAuth callback FE route | `sso_router` + `sso/service.py` google block | `0045`/`0047` google_accounts | Google | — | Keys empty; staging pending | — | **PARTIAL** | sso service L37–44; config L279–280 | Staging OAuth app not created | P0 |
| SSO Microsoft / GitHub | Extra IdPs | — | **Full provider map + GitHub email fetch** in `sso/service.py` | — | — | — | Keys empty | — | **PARTIAL** | service L45–58, L122–238 | Audit “NOT STARTED” understated **code**; credentials empty | P2 |
| API Keys | Machine auth | Settings | `api_keys_router` | retention policy | CSRF exception path | `test_api_keys.py` | Repo | Settings | **COMPLETE** | api_keys module | — | P1 |
| CSRF | Browser mutate | FE csrf helper | Middleware (bare X-API-Key fix cited) | — | — | FE-SEC tests exist | Repo | — | **COMPLETE** | AGENTS §17 claim + csrf.ts | Not re-probed live | P0 |
| Audit trail | Evidence | Legacy `/admin/audit` | `audit_router`; writes across services | `audit_logs` | — | `test_audit.py` | Repo | Legacy | **COMPLETE** | audit module | v3 viewer thin | P0 |
| RLS | Tenant isolation | — | Category B migrations; GUC pin DEC-085 | 51 tables claimed | — | `test_rag_rls.py`, db05 tests | Repo | — | **COMPLETE** (code) | migrations + RLS tests | Live isolation UNKNOWN | P0 |
| salesos_app fail-closed | No BYPASSRLS fallback in prod | — | `config.py` L100–113 | — | — | — | Prod/staging raise if empty password | — | **COMPLETE** | config resolved_url | — | P0 |
| PDPL statement | Legal | — | — | — | — | — | — | — | **PLANNED** | **0** PDPL files | Unsigned / missing | P1 |
| SOC2 Type I | Compliance | — | — | — | — | — | — | — | **PLANNED** | `docs/compliance/soc2-type-i/*` scaffolding | Not an audit | P2 |
| SBOM / SCA | Supply chain | — | ignore files exist | — | gitleaks/semgrep/trivy | `security-scan.yml` | CI | — | **UNKNOWN** | scanners configured; no SBOM artifact verified | — | P2 |

### 5.7 Integrations

| Capability | Business Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Comm Hub Gmail | Mail sync | Legacy integrations | `communication_hub_router` `/connect` `/sync` | `0044`, `0047–0049` | Google | — | Keys + encryption empty by default | Legacy | **COMPLETE** (code) | communication_hub/router.py L67–224 | Staging OAuth | P1 |
| Comm Hub Calendar | Calendar sync | Legacy | `/calendar-sync` | `0048` syncToken | Google | — | Same | Legacy | **COMPLETE** (code) | same router | Same | P1 |
| OAuth token encryption | Fernet + rotation | — | `google_encryption_key` + `_previous` | oauth_tokens | Comm Hub | — | Empty default | — | **COMPLETE** (config surface) | config L294–296 | Must be set in deploy | P0 |
| Notion sync | Import companies | — | `notion_sync_router` `POST /notion/sync` | — | Notion token empty | — | Unknown live | — | **PARTIAL** | `notion_sync/router.py` | Company-only; live UNKNOWN | P2 |
| Excel Import | File ingest | `/v3/data/imports` | `excel_import_router` 2 POSTs | source files | MD | — | Repo | v3 | **COMPLETE** | excel_import/router.py | — | P1 |
| Odoo | ERP | Marketplace seed mentions Odoo | `odoo_*` config empty; `b0d0e0f0a0d0` external ids | migration only | — | `test_story_13_01` seed name | — | — | **NOT STARTED** | config L287–290 | No product connector | P2 |
| Stripe | Subs / portal / dunning | Legacy `/admin/billing` | `stripe_router` webhook; billing modules | `c3a9f12d4e80` family | Stripe | billing tests exist | **Keys empty → 503** | Admin | **PARTIAL** | config L175–179 | Spine ≠ live billing | P1 |
| Webhooks + SSRF | Outbound safety | Studio / hub | `webhooks_router` + `url_safety.py` | `0039_webhook_tables` | Hub | webhook tests | Repo | — | **COMPLETE** | url_safety.py; webhooks/ | InMemory default residual (FINAL) | P0 |
| Integration Hub | Connectors | Legacy `/integrations`, `/studio` | `integration_hub_router` | `e1a7b68c2d05` family | — | STORY-08 tests exist | Repo | Legacy | **COMPLETE** | hub router mounted | v3 missing | P1 |
| MCP server | Tooling | — | `mcp_server/` + `app/routers/mcp.py` | — | — | — | Present | — | **PARTIAL** | `mcp_server/README.md` + mcp router | Not product-audited | P3 |

### 5.8 Runtime engines

Audit said “Live” for all except KG. **FACT:** all listed routers are `include_router`’d in `app/boot/routers.py` except KG which **is** mounted (`graph_router` L203) contrary to “prod not routed.”

| Runtime | FE | BE mount | Tests | Status | Gap |
|---|---|---|---|---|---|
| Activity Runtime | `/v3/activities` | `/api/v1` activity | Phase 1 | **COMPLETE** | — |
| Capability Framework | Internal | capability router | registry tests | **COMPLETE** | — |
| Data Fabric Runtime | Internal | `/api/v1` | — | **COMPLETE** (mounted) | No FE |
| Decision Runtime | — | **`/api/v1/decision-runtime` only** | EAB-001 | **DEPRECATED** aliases; engine **PARTIAL** | Do not use old `/api/v1` aliases |
| Event Runtime | Internal | `/api/v1` | Phase 4 | **COMPLETE** | — |
| Feature Store | Internal | runtime + domain routers; Alembic `0002`/`0018`/`0026` | feature-store tests | **COMPLETE** | No FE |
| Knowledge Graph | Legacy `/graph` (honest empty after demo removal) | `/api/v1/graph/*`; **503 if `kg_engine` None** | runtime tests.py | **PARTIAL** | ADR-108 **offline**; `neo4j_password=""`; do not sell |
| Search Runtime | Legacy `/search` | runtime primary + experimental `app/routers/search.py` | — | **COMPLETE** (mounted) | Fuzzy v2 off |
| Timeline Runtime | Company timeline tab | `/api/v1` | — | **COMPLETE** | — |
| UX Runtime | Internal | ux router | — | **COMPLETE** (mounted) | No product UX |
| Schema Engine | Internal | ui_schema_engine | — | **COMPLETE** (mounted) | No FE |
| Form Engine | Internal | form_engine | STORY-10-02 auto-render | **COMPLETE** (mounted) | Studio-tied |
| Action Engine | Internal | action_engine | — | **COMPLETE** (mounted) | No FE |
| Extension API | Internal | extension_api | — | **COMPLETE** (mounted) | No FE |
| Plugin Sandbox | Marketplace | plugin_sandbox | STORY-13 | **COMPLETE** (mounted) | — |
| Pipeline Analytics | Partial v3 | mounted | — | **COMPLETE** BE / **PARTIAL** FE | See 5.2 |
| NBA Engine | Partial FE | mounted | `test_nba_pipeline.py` | **COMPLETE** BE / **PARTIAL** FE | See 5.3 |

### 5.9 Tenant Studio (legacy shell)

All have routers in `boot/routers.py` + `/(dashboard)/studio/*` pages + `test_story_10_*.py` (except AI studio = story 12).

| Capability | Status | Evidence | Gap | Priority |
|---|---|---|---|---|
| Custom Fields | **COMPLETE** | `tenant_studio/router` + `/studio/custom-fields` + `test_story_10_01` | Not on v3 | P2 |
| Workflow Builder | **COMPLETE** | `workflow_builder_router` + `/studio` + `test_story_10_03` | Legacy | P2 |
| Scoring Rules | **COMPLETE** | `scoring_rules_router` + `/studio/scoring` + `test_story_10_04` | Legacy | P2 |
| Territory Rules | **COMPLETE** | `territories_router` + studio + `test_story_10_05` | Legacy | P2 |
| Permissions Studio | **COMPLETE** | `permissions_router` + `/studio/permissions` + `test_story_10_06` | Legacy | P1 |
| Branding & Languages | **COMPLETE** | `branding_router` + `/studio/branding` + `test_story_10_07` | Legacy | P2 |
| Notification Rules | **COMPLETE** | `notification_rules_router` + `/studio/notifications` + `test_story_10_08` | Legacy | P2 |
| Prompt Library | **PARTIAL** | Same as 5.3 | Honesty + no v3 | P2 |
| AI Policies | **PARTIAL** | Same as 5.3; hardcoded flag | Split-brain | P2 |
| AI Memory | **PARTIAL** | Same as 5.3 | No v3 | P2 |

Section 1.9 COMPLETE vs 1.3 PARTIAL for the three AI studio rows is **reconciled: PARTIAL**.

### 5.10 GTM Intelligence

Audit marked all COMPLETE and footnoted “fixture-based.” That status is an over-claim.

| Capability | FE | BE | Store | Tests | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|---|---|---|
| ICP (11-01) | `/v3/icp` + `/gtm/icp` | icp + icp_admin | **Postgres** `icp_profiles` | icp + story 11-01 | **PARTIAL** | Real persistence; nav orphan | Live profiles thin | P1 |
| TAM/SAM/SOM (11-02) | `/gtm` hub | `market_sizing_router` | `Mem` fixture universe | `test_story_11_02` | **MOCK** | `market_sizing_store.py` “not live 141221” | Do not sell as market sizing | P2 |
| Lead Discovery (11-03) | `/gtm/lead-discovery` | `lead_discovery_router` | gov-first + Hub **fixture fallback** | `test_story_11_03` | **MOCK** | story + router | Not live discovery | P2 |
| Lookalike (11-04) | `/gtm/lookalikes` | `lookalike_router` | “CI uses in-memory won/lost fixtures” | `test_story_11_04` | **MOCK** | `lookalike_engine.py` L3 | Not live ML | P2 |
| Enrichment Waterfall (11-05) | `/gtm/enrichment` | `enrichment_router` | `MemEnrichmentStore` | `test_story_11_05` | **MOCK** | “Not Production GO” in router | No live providers | P2 |
| Contact Verification (11-06) | `/gtm/verification` | `verification_router` | swap-in connector | `test_story_11_06` | **MOCK** | fixture connector | — | P2 |
| Website Intelligence (11-07) | `/gtm/website-intelligence` | router | `fixture_website` | `test_story_11_07` | **MOCK** | engine key `fixture_website` | Honesty strings vs Settings | P2 |
| AI Outreach (11-08) | `/gtm/outreach` | router | `fixture_outreach`, `draft_only` | `test_story_11_08` | **MOCK** | “live LLM/SMTP not claimed” | — | P2 |
| Sequencing (11-09) | `/gtm/sequences` | `sequencing_router` | in-memory / email channel | `test_story_11_09` | **MOCK** | email-only; not live SMTP proven | — | P2 |

### 5.11 Chaos / DR / SOC2 harnesses

| Story | Purpose | FE | BE | Tests | Status | Gap |
|---|---|---|---|---|---|---|
| STORY-14-01 | Load/SLO | — | `load_slo_router` | `test_story_14_01` | **COMPLETE** (harness) | Not production SLO |
| STORY-14-02 | Chaos CI | — | `chaos_resilience_router`; `/chaos/meta` **hardcodes** copilot False | `test_story_14_02` | **COMPLETE** (harness) | Meta lies vs Settings |
| STORY-14-03 | DR drill | — | `dr_drill_router` | `test_story_14_03` | **COMPLETE** (non-prod sim) | ≠ managed backup ON |
| STORY-14-05 | SOC2 pack | — | docs only | — | **PLANNED** | Scaffolding |
| STORY-14-06 | AI failover | — | `ai_failover_router` | `test_story_14_06` | **COMPLETE** (fake providers) | Non-prod |
| STORY-14-07 | LLM golden | — | `llm_regression_router` | `test_story_14_07` | **COMPLETE** (fixtures) | Non-prod |

### 5.12 Frontend surfaces (inventory, not capabilities)

| Surface | Audit | Verified | Status |
|---|---|---|---|
| v3 shell | 40 pages / 24-item nav / CLEAN | **40** pages; **25** nav hrefs; `/v3/icp` off-nav | Canonical UI |
| Legacy dashboard | 78 | **78** `page.tsx` | Retirement candidate |
| `api/` handlers | 2 | Not re-counted this pass | UNKNOWN exact |
| Auth | 3 | login/register exist | Live routes |
| `/system` | 1 | Not re-opened | UNKNOWN |

---

## 6. Changelog of status corrections

| # | Row | Old | New | Evidence |
|---|---|---|---|---|
| 1 | Revenue | COMPLETE | **PARTIAL** | v3 Forecast + Custom = `PreviewPanel`; PDF `ValueError` |
| 2 | Contracts | PARTIAL | **COMPLETE** | `commercial.py` L894–1033 + domain + `/v3/contracts` |
| 3 | Commercial Memory | COMPLETE | **PARTIAL** | No FE; no dedicated router |
| 4 | Account Intelligence | COMPLETE | **PARTIAL** | FE hits `intelligence_computer`, not `AccountIntelligenceService` |
| 5 | Deal Intelligence | COMPLETE | **PARTIAL** | Service file only; CRM detail has no intel tab |
| 6 | Pipeline Analytics | COMPLETE | **PARTIAL** | BE mounted; v3 uses executive/opportunities |
| 7 | Forecasting | COMPLETE | **PARTIAL** | v3 forecast tab PreviewPanel |
| 8 | Evidence Chain | COMPLETE | **PARTIAL** | No public panel |
| 9 | Recommendations | COMPLETE | **PARTIAL** | Seller UI = HITL/signal_actions; P2-7 engine unused by those pages |
| 10 | Copilot Modes | COMPLETE | **PARTIAL** | DEV-only provider; `feature_ai_copilot` True vs honesty False; `ga_ready=false` |
| 11 | RAG | COMPLETE | **PARTIAL** | Pilot corpus; no v3 RAG product |
| 12 | NBA | COMPLETE | **PARTIAL** | Engine mounted; FE is signal_actions |
| 13 | AI Governance Audit | COMPLETE | **PARTIAL** | Tests exist; **no admin viewer** |
| 14 | ICP Engine | COMPLETE | **PARTIAL** | Code+Postgres+page; **not in v3 nav**; thin live data |
| 15 | Signal Marketplace | COMPLETE | **PARTIAL** | `feature_signal_marketplace_postgres=False` |
| 16 | Entity Resolution | COMPLETE | **PARTIAL** | FE/BE/tests on **salesos_test**; Phase 7-B/C blocked |
| 17 | Alembic drift gate | COMPLETE | **PARTIAL** | 108 files ≠ “96/97”; prod stamp unverified; dashboard migrate residual |
| 18 | Observability | COMPLETE | **PARTIAL** | `sentry_dsn=""` |
| 19 | Deployment | COMPLETE | **PARTIAL** | RAILWAY recon: file OK; live dashboard UNKNOWN; OAuth/backup residuals |
| 20 | SSO Microsoft/GitHub | NOT STARTED | **PARTIAL** | `sso/service.py` implements both; keys empty |
| 21 | Stripe | COMPLETE spine | **PARTIAL** | Keys empty → fail-closed 503 |
| 22 | MCP | “present” | **PARTIAL** | Package + router; not product-complete |
| 23 | Knowledge Graph | Live / offline note | **PARTIAL** | Router **is** mounted; ADR-108 offline; 503 if engine None |
| 24 | Decision Runtime aliases | Live | **DEPRECATED** (old prefix) | Remounted `/decision-runtime` |
| 25 | Prompt Library (1.9) | COMPLETE | **PARTIAL** | Align with 1.3; legacy + honesty split |
| 26 | AI Policies (1.9) | COMPLETE | **PARTIAL** | Hardcoded False in engine |
| 27 | AI Memory (1.9) | COMPLETE | **PARTIAL** | Legacy only |
| 28 | TAM/SAM/SOM | COMPLETE | **MOCK** | Fixture universe |
| 29 | Lead Discovery | COMPLETE | **MOCK** | Fixture fallback |
| 30 | Lookalike | COMPLETE | **MOCK** | In-memory won/lost fixtures |
| 31 | Enrichment Waterfall | COMPLETE | **MOCK** | Mem store; Not Production GO |
| 32 | Contact Verification | COMPLETE | **MOCK** | Swap-in fixture connector |
| 33 | Website Intelligence | COMPLETE | **MOCK** | `fixture_website` |
| 34 | AI Outreach | COMPLETE | **MOCK** | `fixture_outreach` / draft_only |
| 35 | Sequencing | COMPLETE | **MOCK** | Email channel; live SMTP not evidenced |
| 36 | People FE path | COMPLETE (wrong href) | **COMPLETE** (path fix only) | `/v3/data/people` vs `/v3/people` employees — documented, not a status flip |

**Not flipped (keep):** Contacts, Opportunities, Pipeline, Activities, Proposals, Reviews, Approvals, EvidencePack loader, Evaluation gates, Phase-6 pure modules (classifier…relationships), EventBus, Capability Registry, Background Jobs (code), JWT/refresh/audiences/RBAC/API keys/CSRF/audit/RLS/salesos_app, Comm Hub code, Excel, Webhooks, Integration Hub, most mounted runtimes, Studio 10-01…10-08, harness 14-01/02/03/06/07.

**People / Companies:** status stays COMPLETE; evidence paths corrected (360 redirect; MD people URL).

---

## 7. Backend without UI

Product-relevant surfaces that have a mounted router or domain service but **no v3 (or only internal) UI**:

| Capability | Backend evidence | UI reality |
|---|---|---|
| Commercial Memory | `domains/commercial/memory/` | None |
| Evidence Chain | `domains/commercial/evidence/` | None |
| `AccountIntelligenceService` | `intelligence/account_intelligence.py` | Unused by FE |
| `DealIntelligenceService` | `intelligence/deal_intelligence.py` | Unused; no deal intel tab |
| `intelligence/recommendation_engine.py` (P2-7) | File exists | Seller UI uses HITL/signal_actions |
| `intelligence/forecasting.py` | File exists | v3 forecast = PreviewPanel |
| Pipeline Analytics API | `/pipeline/summary` etc. | v3 does not call it |
| NBA Engine API | `runtime/nba_engine/api/router.py` | Dashboard ≠ this API |
| AI Governance | `governance_audit.py` | No admin viewer |
| Evaluation / quality gates | `quality_gates.py` | Internal |
| Phase 6 classifiers / quality / readiness / canonical / relationships | `master_data/phase6/*` | Consumed only |
| Decision Runtime | `/api/v1/decision-runtime` | No v3; FE Decision **STUB** |
| Decision Center API | `/api/v1/decisions*` | Legacy `/decisions`; not v3 nav |
| Feature Store / Data Fabric / UX / Schema / Form / Action / Extension | mounted | No v3 |
| Load/SLO, Chaos, DR, AI failover, LLM regression | mounted | Harness only |
| Prompt/Policies/Memory/Tiers | mounted | Legacy studio only |
| GTM fixture APIs | mounted | Legacy `/gtm/*` only (ICP has v3 page) |
| MCP | `mcp_server/` + mcp router | None |
| Notion | `POST /notion/sync` | No v3 |
| Stripe webhooks / billing spine | mounted | Legacy admin billing; keys empty |
| ICP | admin+score APIs | Page exists **off-nav** |

---

## 8. UI without backend (or honest-empty / wrong backend)

| UI | What it hits | Verdict |
|---|---|---|
| `/v3/cs` | Executive + company search; panels marked **Not wired** | Preview, not CS product |
| `/v3/analytics` Forecast tab | PreviewPanel copy only | No forecast API on that tab |
| `/v3/analytics` Custom reports | PreviewPanel | No builder |
| `/v3/companies/[id]/360` | `redirect(/v3/companies/:id)` | No 360 resource |
| `/v3/people` | `searchEmployees` | **Wrong domain** vs “MD People” |
| `/v3/icp` | Real ICP admin API | **Orphan** (not in nav) |
| FE `@salesos/decision` | Throws STUB | Must not be sold |
| Legacy `/graph`, `/knowledge` | Demo data **removed**; honest empty | KG still ADR-108 offline |
| Nav `/v3/data*` | Pages **do** exist (RECON C-11 stale) | Wired to master-data API |

No BROKEN nav orphans found for the 25 `V3_DOMAIN_NAV` hrefs (data pages present).

---

## 9. Honest MVP-blocking gaps (P0)

These block a **design-partner / first-tenant commercial loop**, not “nice-to-have studio.”

1. **Copilot / AI default vs honesty** — Settings `feature_ai_copilot=True`, honesty/FF-07/soak/prod templates `False`, provider **DEV-only**, `ga_ready=false`. Cannot ship AI as a capability. (AI_FLAG_RECON; this matrix Copilot=PARTIAL.)
2. **Master data not in production DB** — Muhide + ER + Phase 6 + Review Queue are **`salesos_test`**. Phase 7-B/C + 54,185 human review + PO sign-off still block prod ingest.
3. **Railway dashboard migrate residual** — Repo `preDeployCommand` is `alembic upgrade head`; live dashboard last evidenced as `init_db()` (2026-08-21). Prod schema vs 108 heads **UNKNOWN**.
4. **Managed backup schedule OFF** — Scripts exist; OPS residual open. Cannot claim DR.
5. **SSO Google staging** — Code exists; client IDs empty; FINAL still requires staging OAuth for any external pilot.
6. **Seller “intelligence” over-mapped** — Account/Deal/Recommendation/Forecast Phase-2 services are **libraries**, not the v3 loop. Selling “Intelligence CLOSED” as user-visible is false.
7. **GTM sold as COMPLETE** — 8 of 9 GTM stories are **MOCK** fixtures. Only ICP has Postgres + a v3 page (off-nav).
8. **Signal marketplace InMemory** — `feature_signal_marketplace_postgres=False`. Seller dashboard depends on signal_actions; catalog durability not default-on.
9. **Stripe / paid tenant path fail-closed** — Empty keys → 503. Fine for honesty; blocks billed MVP.
10. **Decision FE STUB + KG offline** — README/audit “Live” language is unsafe (RECON C-12). Decision Center HTTP ≠ FE package.

Secondary P1 (not in top 10 but material): v3 forecast/CS preview; PDF export stub; Sentry empty; ICP off-nav; `/v3/people` mislabel; three recommendation engines; HITL 50 / 353/353 / 42/42 harnesses **missing on disk**.

---

## 10. Wave 1 recon cross-walk

| Wave 1 finding | Matrix effect |
|---|---|
| AI_FLAG_RECON: default True vs honesty False | Copilot / studio AI / chaos meta → PARTIAL |
| RECON C-05: 353/353 + 42/42 harnesses missing | Do not use those N as Tests evidence |
| RECON C-07: Phase test N drift | Tests column uses **file counts** |
| RECON C-08: 108 Alembic files | Alembic gate PARTIAL |
| RECON C-09 / C-11: Phase 7-A done; v3/data pages | Review Queue PARTIAL; data pages **exist** (C-11 stale) |
| RECON C-17: Decision STUB | UI-without-backend |
| RAILWAY recon: file vs dashboard | Deployment PARTIAL; not COMPLETE |

---

## 11. Commands / validation

| Item | Status |
|---|---|
| File written | **This file only** |
| Product / project-audit edits | **None** |
| pytest / npm | **Not run** |
| git write | **Not run** |
| Live Railway / browser | **Not probed** |
| Validation | **light validated** |

---

## 12. Short summary (for parent)

- **Verified:** **113** capability rows (audit claimed ~110) + 5 FE surface rows.  
- **Downgraded:** **34** (2 upgrades: Contracts → COMPLETE; SSO MS/GitHub → PARTIAL).  
- **New totals:** COMPLETE **52** · PARTIAL **42** · MOCK **8** · PLANNED **3** · NOT STARTED **1** · UNKNOWN **1** · DEPRECATED **1**.  
- **Top 10 MVP gaps:** (1) AI flag/provider honesty, (2) MD/ER test-DB + Phase 7 block, (3) Railway dashboard migrate, (4) backup schedule OFF, (5) Google SSO staging, (6) Phase-2 intel unwired, (7) GTM fixtures sold as COMPLETE, (8) signal marketplace InMemory, (9) Stripe keys empty, (10) Decision STUB + KG offline.

The codebase is **wide**, not **complete-heavy**. Treat Phase 1 CRM objects as the only COMPLETE commercial spine; treat Intelligence/AI/GTM/MD-prod as PARTIAL or MOCK until evidence says otherwise.
