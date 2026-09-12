# 11 — Capability Matrix — مصفوفة القدرات

**Legend:**
- `Status`: COMPLETE / PARTIAL / PLANNED / MOCK / BROKEN / NOT STARTED / UNKNOWN / DEPRECATED
- `Evidence`: file path / doc path / test count / gate pack
- `Priority`: P0 (blocking) / P1 (should) / P2 (nice) / P3 (later)
- `FACT` / `INFERENCE` / `RECOMMENDATION` / `UNKNOWN` labels applied to evidence claim

---

## 1. Full Product Capability Matrix — 13 columns

Columns: Capability | Business Purpose | Frontend | Backend | Database | Integration | Tests | Deployment | UX | Status | Evidence | Gap | Priority

### 1.1 Product Core (Phase 1 — CLOSED)

| Capability | Business Purpose | Frontend | Backend | Database | Integration | Tests | Deployment | UX | Status | Evidence | Gap | Priority |
|-----------|------------------|----------|---------|----------|-------------|-------|------------|----|--------|----------|-----|----------|
| Companies (list + 360 + detail) | Central object, buyer's mental model | `/v3/companies`, `/v3/companies/[id]`, `/v3/companies/[id]/360` | `company_router` (`/api/v1/companies`) + `search_repository.py` (owner_id + segment filters) | Alembic `a1b2c3d4e5f6` (owner_id + segment) | Master Data lookup | Phase 1 tests 49/49; `test_company_search_contains.py` 12 tests | Live (Railway staging + prod) | v3 shell CLEAN per §39 | COMPLETE | `PHASE1_GATE_EVIDENCE_PACK.md`, `AGENTS.md` §12 | UX polish; empty states | P0 keep |
| Contacts | People to whom we sell | `/v3/contacts`, `/v3/contacts/[id]` | `contact_router` | Alembic `0022_consolidate_contacts` | Master Data people | 278 Phase 1 tests | Live | v3 shell CLEAN | COMPLETE | Same | Enrichment sources | P0 keep |
| People | Master data people entities | `/v3/people`, `/v3/people/[id]` | `master_data_router` people slice | `md_global_people` | | Phase 6 tests | Live | v3 | COMPLETE | Phase 6 packs | Person-Company relationship UI depth | P1 |
| Opportunities / Deals | Revenue objects | `/v3/crm`, `/v3/crm/[id]` | `commercial_router`, `opportunity_contacts_router` | Alembic `a1b9c8d7e6f5_adr030_opportunity_contacts` + owner_id | | Phase 1 tests | Live | v3 | COMPLETE | Phase 1 pack | Kanban toggle behind `feature_crm_kanban=False` | P0 keep |
| Pipeline | Stage transitions with qualification | `/v3/crm` (embedded) | `PipelineService.enter_stage(opportunity_context)` | | | Phase 1 tests | Live | v3 | COMPLETE | AGENTS.md §12 | Pipeline visualization | P1 |
| Activities | Calls/Meetings/Tasks/Emails/Notes with FK links | `/v3/activities`, `/v3/tasks`, `/v3/tasks/[id]` | `activity_router`, `activity_intelligence_router` | Alembic `c3d4e5f6a7b8` (activity FK links) | Comm Hub Gmail/Calendar | Phase 1 tests | Live | v3 CLEAN | COMPLETE | Phase 1 pack | Activity → Signal correlation UI | P1 |
| Revenue | Bookings, won/lost, forecast | `/v3/analytics`, `/v3/effectiveness`, legacy `/revenue/*` | `revenue_router`, `revenue_planning_router` (`/api/v1/revenue-planning`), `revenue_execution_router` | Alembic `d4e5f6a7b8c9_phase1_quota_territory_postgres`, `0046_revenue_execution_tables` | Analytics cubes wired to real DB | Phase 1 tests + analytics 57 | Live | v3 | COMPLETE | Phase 1 pack | Territory + Quota editor UX | P1 |
| Proposals | Versioned, deal-linked, approval-dependent | `/v3/proposals`, `/v3/proposals/[id]`, `/v3/quotes`, `/v3/quotes/[id]` | 8 proposal endpoints | | | Phase 1 tests | Live | v3 | COMPLETE | Phase 1 pack | PDF export replaced with `ValueError("PDF export not implemented")` per P1-04 fix — real PDF still missing | P1 |
| Reviews | Manager/deal/exception review workflows | `/v3/reviews`, `/v3/reviews/[id]` | Domain `domains/commercial/review/` + 7 endpoints | Alembic `b2c3d4e5f6a7_phase1_reviews_domain` | | Phase 1 tests | Live | v3 | COMPLETE | Phase 1 pack | Multi-step approval configurator UI | P1 |
| Approvals | Policy → state → authority → audit | `/v3/approvals`, `/v3/approvals/[id]` | `approval_router` + `ApprovalService` (6-status FSM, RBAC) | Alembic `f6a7b8c9d0e1_phase3_hitl_approval` (`approval_requests`) | Copilot Recommend mode | Phase 3 21/21 | Live | v3 | COMPLETE | Phase 3 pack | SLA aging + escalation UI | P0 keep |
| Contracts | Contract lifecycle | `/v3/contracts`, `/v3/contracts/[id]` | not confirmed as full router in this audit | | | UNKNOWN | UNKNOWN | v3 route exists | PARTIAL | route listing | Backend depth unverified this audit | P2 |

### 1.2 Intelligence (Phase 2 — CLOSED)

| Capability | Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|-----------|---------|----|----|----|-------------|-------|--------|----|--------|----------|-----|----------|
| Commercial Memory | Durable CRM memory (21 event types, 9 entity types) | Consumed by Copilot | `domains/commercial/memory/` `CommercialMemoryService` | Alembic `e5f6a7b8c9d0_phase2_evidence_chain` | Event bus | Phase 2 26/26 | Live | Internal | COMPLETE | Phase 2 pack | Public memory viewer UI | P2 |
| Account Intelligence | Health insights per account | `/v3/companies/[id]/360` | `intelligence/account_intelligence.py` | Uses `md_global_companies` + activities | | Phase 2 tests | Live | v3 | COMPLETE | Phase 2 pack | | P1 |
| Deal Intelligence | Deal health/risk/opportunity | `/v3/crm/[id]` | `intelligence/deal_intelligence.py` | | | Phase 2 | Live | v3 | COMPLETE | | | P1 |
| Pipeline Analytics | ForecastCube wired to real DB | `/v3/analytics` | `pipeline_analytics_router` | Real DB (not stub) | | Phase 2 | Live | v3 | COMPLETE | | | P1 |
| Forecasting | Commit/Best Case/Pipeline/Risk (no LLM) | `/v3/analytics`, legacy `/forecast` | `intelligence/forecasting.py` | | | Phase 2 | Live | v3 + legacy | COMPLETE | | | P1 |
| Evidence Chain | Insight→Evidence→Source→Timestamp→Confidence | Consumed by Copilot | `domains/commercial/evidence/` + `EvidenceService` | Alembic `e5f6a7b8c9d0_phase2_evidence_chain` (`commercial_insights`, `commercial_evidence_items`) | | Phase 2 | Live | Internal | COMPLETE | | Public evidence panel UI | P1 |
| Recommendations | Data→Intelligence→Evidence→Recommendation (not LLM) | `/v3/my-day`, `/v3/sales-dashboard` | `intelligence/recommendation_engine.py` + agent | | | Phase 2 + 3 | Live | v3 CLEAN | COMPLETE | Phase 2/3 packs | | P0 keep |

### 1.3 AI Copilot (Phase 3 — CLOSED as code; provider DEV-ONLY)

| Capability | Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|-----------|---------|----|----|----|-------------|-------|--------|----|--------|----------|-----|----------|
| Copilot Modes (Ask/Explain/Summarize/Investigate/Recommend) | 5 modes; Recommend → HITL | Legacy `/copilot`; embedded across v3 pages | `copilot_router` + coordinator + 13 grounded agents (`intelligence/agents/`) | | | Phase 3 11/11 + 45+ grounded tests | Live | Legacy shell + embedded widgets | COMPLETE | Phase 3 pack, AGENTS.md §19–§22 | Provider path DEV-ONLY | P0 blocker |
| Grounded EvidencePack loader | RLS-pinned, PII-strip, value-banding, honest UNKNOWN | Internal | `research_evidence.py` + `grounded_common.py` | Uses `md_*` + activities + timeline + audit + rag | | 19+ tests | Live | Internal | COMPLETE | AGENTS.md §19–§22 | | P0 keep |
| RAG | citations + tenant isolation + freshness | `/v3/data`, `/rag` legacy | `rag_router` | Alembic `0015_rag_tables`, `h1i2j3k4l5m7_phase4a_rag_rls` | | RLS 8/8 | Live | v3 + legacy | COMPLETE | Phase 4A pack | Corpus is 5 rows (pilot) | P1 populate |
| NBA | State→intelligence→evidence→candidate actions | `/v3/sales-dashboard` | `nba_router` (`runtime/nba_engine`) | | Approval | Phase 3 | Live | v3 | COMPLETE | Phase 3 | | P0 keep |
| AI Governance Audit | policy/HITL/PII enforcement to `audit_logs` | Admin viewer needed | `intelligence/governance_audit.py` | `audit_logs` | | Phase 3 13/13 | Live | UI missing | COMPLETE | Phase 3 pack | Admin viewer UI | P1 |
| Human Approval Service | 6-status FSM, RBAC, Postgres | `/v3/approvals` | `ApprovalService` | Alembic `f6a7b8c9d0e1` | | Phase 3 21/21 | Live | v3 | COMPLETE | Phase 3 pack | | P0 keep |
| Evaluation / Quality Gates | Groundedness + hallucination + quality | Internal | `intelligence/evaluation/quality_gates.py` + `EnhancedEvaluationRunner` | | | Phase 3 19/19 | Live | Internal | COMPLETE | Phase 3 pack | | P0 keep |
| ICP Engine | Fit scoring + evidence | `/v3/icp`, legacy `/gtm/icp` | `icp_router`, `icp_admin_router` | Alembic `h2i3j4k5l6m8_phase4a_icp_profiles`, `i3j4k5l6m7n8_phase4a_rls_ai_foundation` | Copilot | ICP suite 19/19 | Live | v3 CLEAN | COMPLETE | Phase 4A/4B/4C | Live tenant ICP data needed | P1 |
| Signal Marketplace | 22 platform signals across 3 packs | `/signals` legacy; embedded | `signal_marketplace_router`, `signal_actions_router`, `hitl_router` | Alembic `l7m8n9o0p1q2_signal_actions`, `m8n9o0p1q2r3_hitl_seller_operating_model` | Runtime bridge (subscribe→event) | Phase 4D/4E/4F, Signal Actions 65 | Live | | COMPLETE | Phase 4F | Expand packs (gov/retail/energy) | P1 |
| Prompt Library | Studio authoring | Legacy `/studio/prompt-library` | `prompt_library_router` | | | STORY-12-01 | Live | legacy | PARTIAL | AGENTS.md §21 | v3 shell | P2 |
| AI Policies | Studio data-class rules, tier caps | Legacy `/studio/ai-policies` | `ai_policies_router` | | | STORY-12-02 | Live | legacy | PARTIAL | | v3 shell | P2 |
| AI Memory | Conversation-level memory (opt-in) | Legacy `/studio/*` | `ai_memory_router` | | | STORY-12-03 | Live | legacy | PARTIAL | | v3 shell | P2 |
| AI Model Tiers | Per-plan model tier configurator | Legacy `/admin` | `ai_model_tiers_router` | `plan_entitlements` | | STORY-12-04 | Live | legacy | PARTIAL | | v3 shell | P2 |

### 1.4 Master Data / Entity Resolution (Phase 6 — READY; Phase 7 — BLOCKED)

| Capability | Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|-----------|---------|----|----|----|-------------|-------|--------|----|--------|----------|-----|----------|
| Muhide ingestion | 296,746 companies + 862,775 source rows + 1,124 people | `/v3/data/imports` | `muhide_adapter.py` + `muhide_ingest_real.py` + `muhide_v1_enrichment.py` | `md_*` 11 foundation + 7 Phase 6 tables | Excel Import | 16/16 integration + Phase 5/6 | `salesos_test` only | v3 CLEAN | PARTIAL (test-DB only) | AGENTS.md §34–§37 | Production ingestion blocked pending Phase 7 | P0 |
| Entity Resolution (CR-safe) | Government-anchor + safe CR normalization | `/v3/data/er` | `entity_resolution/resolution_policy.py` + `matching_pipeline.py` | `md_entity_matches`, `md_entity_conflicts` | | 27 unit + 7 integration | Live in `salesos_test` | v3 CLEAN | COMPLETE | AGENTS.md §36 | | P0 |
| Identity Classifier | 7 buckets, OPTION-C corrected | Consumed | `phase6/classification.py` | `md_identity_classifications` | | 31/31 | `salesos_test` | Internal | COMPLETE | AGENTS.md §37 | | P0 |
| Industry Normalization | Raw immutable, normalized separate | Consumed | `phase6/industry.py` | | | 13/13 | `salesos_test` | Internal | COMPLETE | AGENTS.md §37 | | P1 |
| Quality Scoring | Versioned, 5 dimensions | Consumed | `phase6/quality.py` | | | 6/6 | `salesos_test` | Internal | COMPLETE | AGENTS.md §37 | | P1 |
| Sales Readiness Recompute | Versioned 5 states | Consumed | `phase6/readiness.py` | | | 10/10 | `salesos_test` | Internal | COMPLETE | AGENTS.md §37 | | P1 |
| Canonical Authority Survivorship | Authority > frequency | Consumed | `phase6/canonical.py` | | | 10/10 | `salesos_test` | Internal | COMPLETE | AGENTS.md §37 | | P1 |
| Contact Relationships | VERIFIED / INFERRED with evidence | Consumed | `phase6/relationships.py` | | | 6/6 | `salesos_test` | Internal | COMPLETE | AGENTS.md §37 | | P1 |
| Review Queue (Phase 7-A) | 54,185 candidates + 36 short-CR + 2,661 fuzzy pairs | `/v3/data/review-queue`, `/v3/review-queue` | `review_queue_router` (`/api/v1/master-data/review-queue`) | `md_review_queue_state`, `md_review_candidates` | | Phase 7-A tests | `salesos_test` only | v3 CLEAN | PARTIAL — Phase 7-A capture-only | `PHASE7A_PO_DECISION_2026-09-09.md` | Phase 7-B merge + Phase 7-C CR promotion + production ingest all BLOCKED | P0 |

### 1.5 Platform (Phase 4 — CLOSED)

| Capability | Purpose | FE | BE | DB | Integration | Tests | Deploy | UX | Status | Evidence | Gap | Priority |
|-----------|---------|----|----|----|-------------|-------|--------|----|--------|----------|-----|----------|
| EventBus (in-memory / Kafka opt) | Single-path event stream + persistent DLQ | Internal | `runtime/event_runtime` + `persistent_dlq.py` | Alembic `g1h2i3j4k5l6_phase4_dlq_persistence` (`event_dead_letters`) | | Phase 4 17/17 | Live | Internal | COMPLETE | Phase 4 pack | Kafka not required for MVP | P0 keep |
| Capability Registry | Drift-gated in CI | Internal | pytest wrapper `test_capability_registry_validation.py` | | | 2 tests | CI | Internal | COMPLETE | Phase 4 | | P0 keep |
| Alembic drift gate | `check_alembic_head.py --local-only` in CI | Internal | script | | | | CI | Internal | COMPLETE | Phase 4 + `deploy.yml` | live prod `preDeployCommand` drift residual | P0 |
| Observability | Prometheus /metrics + structured logs + SLA monitor | `/metrics` endpoint | `runtime/admin_router`, `_check_kafka_status()` shared | | | | Live | Internal | COMPLETE | Phase 4 | Sentry DSN empty (no live error stream) | P1 |
| Background Jobs | Lease/recover + EXHAUSTED alerting | Celery worker + beat services | `celery_app.py` + task queue in Postgres | Alembic `f4aee055fd6e_create_agent_tasks` | | IL-2B.2 evidence + Phase 4 | Live (2 Railway services) | Internal | COMPLETE | Phase 4 | | P0 keep |
| Backup / Restore | pg_dump + Neo4j backup + DR drill scripts | Ops | `infra/scripts/*.sh`, `infra/docker/backup/Dockerfile` | | | DR sim non-prod | **Managed schedule OFF** | Internal | PARTIAL | Phase 4 + `OPS01` signature pack | **Enable managed schedule** | P0 |
| Deployment | Railway + Vercel canonical; K8s quarantined | | `Dockerfile.railway` + `vercel.json` + 9 GH workflows | | | | Live | | COMPLETE | Phase 4 | preDeployCommand drift, OAuth staging | P0 |

### 1.6 Identity / Auth / RBAC

| Capability | Status | Evidence |
|-----------|--------|----------|
| JWT (RS256 enforced) | COMPLETE | `config.py` validator; ADR-102 |
| Refresh tokens | COMPLETE | Alembic `0012_refresh_token_tables` |
| Owner-platform vs Tenant-API JWT audiences | COMPLETE | `config.py` `jwt_owner_audience` |
| RBAC (custom roles + permissions) | COMPLETE | Studio `permissions_router` + Admin roles |
| SSO (Google) | PARTIAL — OAuth staging pending | `sso_router` + `google_accounts` migrations |
| SSO (Microsoft, GitHub) | NOT STARTED beyond config placeholders | `config.py` sso_microsoft_* etc empty |
| API Keys | COMPLETE | `api_keys_router` + retention 365d |
| CSRF (bare X-API-Key bypass fixed) | COMPLETE | Middleware fix; AGENTS.md §17 |
| Audit trail | COMPLETE | `audit_logs` writes across services |
| RLS (tenant isolation) | COMPLETE | 51 tenant tables; category B1–B7 migrations |
| salesos_app role fail-closed in prod | COMPLETE | `config.py:100-113` |
| PDPL statement | PLANNED-MISSING | doc not signed |
| SOC2 Type I | PLANNED (STORY-14-05 evidence pack scaffolding exists) | AGENTS.md §21 |
| SBOM / SCA | UNKNOWN | scanner ignores exist (`.gitleaks.toml`, `.semgrepignore`, `.trivyignore`) |

### 1.7 Integrations

| Capability | Status | Evidence |
|-----------|--------|----------|
| Communication Hub — Gmail sync (`historyId`) | COMPLETE | AGENTS.md §35 v1.0-rc1 release; Alembic `0044`, `0047`, `0048`, `0049` |
| Communication Hub — Calendar sync (`syncToken`) | COMPLETE | Same |
| OAuth token encryption (Fernet + rotation) | COMPLETE | `google_encryption_key` + `google_encryption_key_previous` in config |
| Notion sync | PARTIAL | `notion_sync_router` exists; live status UNKNOWN |
| Excel Import | COMPLETE | `excel_import_router` |
| Odoo | NOT STARTED beyond `b0d0e0f0a0d0_odoo_external_ids` migration + `odoo_*` config placeholders | |
| Stripe (subscriptions, portal, invoices, dunning, webhook ledger) | COMPLETE spine; keys empty | Alembic `c3a9f12d4e80`, `e5c1f34a6b02`, `f6d2a45b7c03`, `b8f4c67d9e15`, `a7e3b56c8d04`, `c9e5d78a0f26`, `d0f6e89b1a37` |
| Webhooks + SSRF-hardened | COMPLETE | `url_safety.py` 5-layer; `webhooks_router`; AGENTS.md §11 M1 |
| Integration Hub (STORY-08-*) | COMPLETE | Alembic `e1a7b68c2d05`, `c4d8e21a9f07`, `e5f9a32b0c08`, `f2b8c79d3e06`; AGENTS.md §14 |
| MCP server | present (`mcp_server/`) | Not audited in depth this session |

### 1.8 Runtime engines (dedicated `runtime/` folder)

| Runtime | Status | Notes |
|---------|--------|-------|
| Activity Runtime | Live | `runtime/activity_runtime/router` |
| Capability Framework | Live | `runtime/capability_framework/router` |
| Data Fabric Runtime | Live | `runtime/data_fabric_runtime/router` |
| Decision Runtime | Live under `/api/v1/decision-runtime` (deprecated `/api/v1` aliases) | EAB-001 |
| Event Runtime | Live | `runtime/event_runtime/router` |
| Feature Store | Live | `runtime/feature_store/router`, Alembic `0002`, `0018`, `0026` |
| Knowledge Graph Runtime | OFFLINE per ADR-108 | `runtime/knowledge_graph_runtime/router` — code present, prod not routed |
| Search Runtime | Live | `runtime/search_runtime/router` — primary; `app/routers/search.py` experimental |
| Timeline Runtime | Live | `runtime/timeline_runtime/router` |
| UX Runtime | Live | `runtime/ux_runtime/router` |
| Schema Engine | Live | `runtime/ui_schema_engine/router` |
| Form Engine | Live | `runtime/form_engine/router` |
| Action Engine | Live | `runtime/action_engine/router` |
| Extension API | Live | `runtime/extension_api/router` |
| Plugin Sandbox | Live | `runtime/plugin_sandbox/router` |
| Pipeline Analytics | Live | `runtime/pipeline_analytics/router` |
| NBA Engine | Live | `runtime/nba_engine/api/router` |

### 1.9 Tenant Studio (STORY-10-* pack)

| Capability | Status |
|-----------|--------|
| Custom Fields | COMPLETE (STORY-10-01 / CAP-082) |
| Workflow Builder | COMPLETE (STORY-10-03 / CAP-083) |
| Scoring Rules Studio | COMPLETE (STORY-10-04 / CAP-085) |
| Territory Rules Studio | COMPLETE (STORY-10-05 / CAP-087) |
| Permissions Studio | COMPLETE (STORY-10-06 / CAP-003) |
| Branding & Languages | COMPLETE (STORY-10-07 / CAP-092) |
| Notification Rules Studio | COMPLETE (STORY-10-08 / CAP-093) |
| Prompt Library | COMPLETE (STORY-12-01 / CAP-089) |
| AI Policies | COMPLETE (STORY-12-02 / CAP-091) |
| AI Memory | COMPLETE (STORY-12-03 / CAP-063) |

Nav: mostly on legacy `/(dashboard)/studio/*`. Migrate to v3 progressively.

### 1.10 GTM Intelligence (STORY-11-* pack)

| Capability | Status |
|-----------|--------|
| ICP Engine (STORY-11-01) | COMPLETE |
| TAM/SAM/SOM Market Sizing (11-02) | COMPLETE (fixture-based) |
| Lead Discovery (11-03) | COMPLETE (gov-first + Hub fallback fixture) |
| Lookalike Accounts (11-04) | COMPLETE |
| Enrichment Waterfall (11-05) | COMPLETE (fixture-based, ≥2 providers scaffold) |
| Contact Verification (11-06) | COMPLETE (swap-in connector) |
| Website Intelligence (11-07) | COMPLETE (fixture + prompt registry) |
| AI Outreach (11-08) | COMPLETE (draft_only, no live LLM in path) |
| Sequencing Engine (11-09) | COMPLETE (email channel) |

All 11 stories are **fixture-based** — do not sell as "live enrichment" without customer proof.

### 1.11 Chaos / DR / SOC2 harnesses (STORY-14-* pack)

| Story | Purpose | Status |
|-------|---------|--------|
| STORY-14-01 | Load/SLO harness | COMPLETE (soak Option A signed) |
| STORY-14-02 | Chaos resilience fault injection (CI) | COMPLETE |
| STORY-14-03 | DR drill harness (backup/restore, RTO/RPO) | COMPLETE (non-prod) |
| STORY-14-05 | SOC2 Type I evidence pack | scaffolding present |
| STORY-14-06 | AI provider failover (fake providers, no live kill) | COMPLETE (non-prod only) |
| STORY-14-07 | LLM regression golden fixtures | COMPLETE (non-prod only) |

### 1.12 Frontend surfaces summary

| Surface | Page count | Status |
|---------|-----------|--------|
| v3 shell | 40 | Canonical current UI; 24-item nav; CLEAN per §39 |
| Legacy `(dashboard)` shell | 78 | Live-routable; **candidate for retirement**; some 404 / 500 API residuals |
| `api/` route handlers | 2 | Copilot query proxy + Google OAuth callback |
| Auth | 3 (login/register + fe-sec-02) | Live |
| System | 1 (`/system`) | Live for build-parity checks |

---

## 2. Aggregate

- **Total capability rows above:** ~110
- **COMPLETE:** ~85
- **PARTIAL:** ~15
- **PLANNED / NOT STARTED / DEPRECATED:** ~10

**Interpretation:** the codebase is **complete-heavy**, not sparse. The gap is **customers + revenue + operations**, not features.

---

## 3. Cross-cutting risks embedded in capabilities

1. **Copilot capability = COMPLETE code + DEV-ONLY provider** = misleading if reported as "COMPLETE" without provider qualifier
2. **Master Data capability = COMPLETE code + Phase 7 BLOCKED** = production usability gated by human review
3. **Deployment capability = COMPLETE + backup schedule OFF** = production risk
4. **KG capability = code present + OFFLINE per ADR-108** = do not sell against
5. **Studio capabilities = COMPLETE + on legacy shell** = enterprise sale friction until on v3

---

*Capability matrix — evidence-anchored. See `12_GAP_ANALYSIS.md` for what's promised vs what's real.*
