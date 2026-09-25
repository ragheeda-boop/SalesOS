# 16 — What Has Actually Been Built
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Purpose:** honest inventory of what exists in code, what runs in staging/prod, what is stubbed. Numbers are FACT-labeled from code/docs; runtime state is UNKNOWN-labeled unless verified this audit.

---

## 1. Product Core (CLOSED per Master Closure Sequence 2026-08-17)

| Item | State | Evidence |
|------|-------|----------|
| CRM: Companies domain | BUILT + LIVE | `domains/commercial/company/`, 40 v3/companies pages, 296,746 rows in `salesos_test` |
| CRM: Contacts domain | BUILT + LIVE | `domains/commercial/contact/`, `/v3/contacts`, `/v3/data/md-people` |
| CRM: Deals + Opportunities | BUILT | `domains/commercial/opportunity/`, `PATCH /opportunities/{id}/assign`, `/v3/crm` |
| Pipeline stages | BUILT | `PipelineService.enter_stage()` with real qualification criteria |
| Activities + FK links | BUILT | Alembic `c3d4e5f6a7b8` — activities.company_id/contact_id/deal_id |
| Revenue planning | BUILT | Router mounted at `/api/v1/revenue-planning`, Postgres-backed forecast |
| Analytics cubes | BUILT | ForecastCube + PipelineCube + TeamCube + ActivityCube wired to real DB |
| Proposals | BUILT | 8 endpoints (list, detail, approve, reject, expire, deliver, accept), `/v3/proposals` FE |
| Reviews | BUILT | 7 endpoints, Alembic `b2c3d4e5f6a7`, `/v3/reviews` FE |
| Approvals (HITL) | BUILT | ApprovalService 6-status FSM, RBAC levels, `/api/v1/approvals`, Alembic `f6a7b8c9d0e1` |
| Owner assignment | BUILT | `PATCH /companies/{id}/assign` with owner_id + segment |
| Segment classification | BUILT | Alembic `a1b2c3d4e5f6` |
| Domain events | BUILT | Runtime bridge; publish/subscribe pattern |

**Test evidence:** 49/49 Phase 1 smoke tests pass (2026-08-17).

---

## 2. Intelligence (CLOSED 2026-08-19)

| Item | State | Evidence |
|------|-------|----------|
| Commercial Memory | BUILT | `domains/commercial/memory/`, 21 event types, 9 entity types |
| Account Intelligence | BUILT | `intelligence/account_intelligence.py` |
| Deal Intelligence | BUILT | `intelligence/deal_intelligence.py` |
| Pipeline Analytics | BUILT | Real DB queries (was stub) |
| Forecasting | BUILT | `intelligence/forecasting.py` — Commit/Best Case/Pipeline/Risk from durable data |
| Evidence Chain | BUILT | `domains/commercial/evidence/`, `EvidenceService`, 10 categories, 8 evidence types, 4 confidence levels, Alembic `e5f6a7b8c9d0` (2 tables) |
| Recommendation Engine | BUILT (deterministic, non-LLM) | `intelligence/recommendation_engine.py` |

**Test evidence:** 26/26 Phase 2 tests pass.

---

## 3. AI Copilot (CLOSED 2026-08-19)

| Item | State | Evidence |
|------|-------|----------|
| Copilot Modes (Ask/Explain/Summarize/Investigate/Recommend) | BUILT | `/copilot/mode` endpoint |
| RAG (Retrieval-Augmented Generation) | BUILT + RLS-tenant-isolated | `rag_documents` table + `h1i2j3k4l5m7` RLS |
| NBA (Next Best Action) via HITL | BUILT | ApprovalService wired |
| AI Governance Audit | BUILT | `intelligence/governance_audit.py` — writes to `audit_logs` |
| Approval Domain + REST | BUILT | 6 endpoints, RBAC levels (SELF/MANAGER/VP/EXECUTIVE), 6 statuses, Alembic `f6a7b8c9d0e1` |
| Evaluation Quality Gates | BUILT | `intelligence/evaluation/quality_gates.py` — groundedness scorer + hallucination detector |
| Grounded EvidencePack Loop | BUILT + PROVEN | 13 agents (research, competitor, relationship, ICP, recommendation, forecast, pricing, proposal, renewal, tender, meeting, news, contract) all grounded per §19–§22 |
| PII enforcement | BUILT | 5-layer per F1 phase; live-tested 0 violations |
| Provider reliability | BUILT | ReliableProvider + CircuitBreaker + retry/backoff + timeouts |
| Provider policy gate | BUILT | ProviderModelPolicy, DataClassRule, max_model_tier |
| Cost tracking + budget | BUILT | DB-backed (Alembic `f8b3d4e5f6a7`), SELECT FOR UPDATE budget enforcement |
| Observability | BUILT | Prometheus `/metrics`, structured logging, request_id propagation |
| **`feature_ai_copilot` flag** | ~~True in code~~ **→ RESOLVED 2026-09-12/13: default `False`** (config.py:162), 12 test files/15 asserts `is False`, 101/101 Docker PASS, AI_HONESTY aligned; F-04 closed | See §00 F-04 → CLOSED |

**Test evidence:** 86/86 Phase 3 tests pass; 102 grounded-scope tests + 2761 total unit tests (56 pre-existing env failures — not new regressions).

**Provider status:** **DEV-ONLY** (AI Horde / Cydonia-24B). Production LLM contract unsigned. Per `PROVIDER-EVAL-2026-08-23.md` — **production no-go for AI Copilot until real provider provisioned.**

---

## 4. Master Data / Entity Resolution (Phases 4–6 READY)

| Item | State | Evidence |
|------|-------|----------|
| MUHIDE ingestion adapter | BUILT + PROVEN | `app/modules/master_data/muhide_adapter.py`, 16/16 integration tests |
| Global Companies + People + Mappings | BUILT | 11 foundation tables + 7 Phase 6 tables |
| CR (Commercial Registration) normalization | BUILT + SAFE | `normalize_cr` separator-aware, RTL-aware |
| CR classification | BUILT | SAFE / SUSPICIOUS_SHORT / SUSPICIOUS_MULTI / AMBIGUOUS |
| Identity classifier (OPTION C) | BUILT | Contactability ≠ Identity; email/phone not identity signals |
| Corrected bucket priority | BUILT | Fixes 1,261-account REVIEW_REQUIRED misclassification |
| False-anchor correction | BUILT + PROVEN | 8 concat artifacts removed, provenance-tracked |
| Fuzzy-never-auto-merge | BUILT + PROVEN per ADR-0104 | 2,661 fuzzy → REVIEW_REQUIRED |
| Government-ID hard-veto | BUILT + PROVEN per ADR-0105 | 563 GOVERNMENT_ANCHOR pairs → VETOED |
| Cross-source independence (field-level agreement) | BUILT | Frequency NEVER establishes canonical identity |
| Industry normalization | BUILT | Raw immutable, normalized separate, AR/EN mapping |
| Quality scoring | BUILT | Versioned, 5 dimensions (0-100), evidence basis, provenance tiers |
| Sales readiness | BUILT | DI-aligned 5 states |
| Canonical authority | BUILT | GOV_ANCHOR > STRONG_DETERMINISTIC > WEAK_DETERMINISTIC > NORMALIZED_EXACT > FUZZY |
| Contact relationships | BUILT | VERIFIED / INFERRED + confidence + evidence |
| Phase 6 pipeline (idempotent, dry-run) | BUILT + PROVEN | 296,746 accounts, 1,238,635 staged changes, 9/9 safety counters = 0 |
| Schema gate | BUILT | `phase6_schema_gate.py` idempotent stamp |
| MUHIDE V1 enrichment | BUILT | 223,073 rows attached, 1,410 missed-links reconciled, 3,793 new-company candidates queued |
| Phase 7-A capture-only writes | BUILT | Per PO decision 2026-09-09; `salesos_test` only |

**Data reality:** 296,746 companies + 1,124 people + 314,413 mappings in `salesos_test`. **Zero rows in `salesos` production per §25 evidence.**

---

## 5. Platform infrastructure (CLOSED Phase 4 2026-08-19)

| Item | State | Evidence |
|------|-------|----------|
| EventBus + persistent DLQ | BUILT | `event_dead_letters` table, RLS tenant-isolated, Alembic `g1h2i3j4k5l6` |
| Capability Registry | BUILT | Validation via `scripts/validate_capability_registries.py` + pytest wrapper |
| Migrations (Alembic) | 109 files, 1 head verified | Alembic current == head |
| Observability | BUILT | `_check_kafka_status()` DRY across 4 endpoints; SLA monitor; structured logging |
| Background jobs | BUILT | Celery worker + beat; EXHAUSTED task alerting |
| Backup/Restore | BUILT | Dockerfile paths fixed; scripts exist |
| Deployment | BUILT | Railway canonical + Vercel canonical; rollback script `scripts/railway_rollback.sh` |
| Signal Marketplace | BUILT | Postgres-backed catalog, 22 signals seeded (construction 7 + healthcare 7 + financial-services 8) |
| Signal detection bridge | BUILT | Subscribe → event → tenant feed (RLS-isolated) |
| ICP Persistence | BUILT | `icp_profiles` table (Alembic `h2i3j4k5l6m8`) |
| ICP Sync Adapter | BUILT (ADR-0109 Option A) | `SyncICPStore` with private loop thread |
| ICP Admin API | BUILT | GET/POST `/api/v1/icp/profiles` + GET/PATCH `/{id}` |
| RAG RLS | BUILT + PROVEN | Direct policy on `rag_documents` + EXISTS parent probe on chunks |
| Tenant isolation (Postgres RLS) | BUILT + PROVEN | 51 tenant tables, dual DB roles (`salesos` owner + `salesos_app` app), DEC-085 GUC pinning |
| JWT RS256 + JWKS | BUILT | HS256 forbidden |
| CSRF double-submit | BUILT | Cookie + header |
| Google OAuth | BUILT (backend + FE) | `/auth/google/callback` — OAuth staging **BLOCKED — needs Google Cloud Console app** |
| MCP server | BUILT (structure) | `salesos/backend/mcp_server/` |
| Chaos / DR / SOC2 harness | BUILT | 178 container tests + 49 smoke |
| Fitness gates | BUILT + LIVE in CI | FF-07 / AIGOV / FF-14 / FF-DUP-01 |

**Test evidence:** 17/17 Phase 4 tests + 2360 unit tests.

---

## 6. Frontend (Next.js 15)

### Canonical v3 shell (40 pages)

| Category | Pages | State |
|----------|-------|-------|
| Product Core | `/v3` (Today), `/v3/companies` × 2, `/v3/contacts` × 2, `/v3/crm`, `/v3/pipeline`, `/v3/activities`, `/v3/proposals` × 2, `/v3/reviews` × 2, `/v3/revenue` | BUILT + LIVE per Phase 1 browser QA 9/9 |
| Intelligence | `/v3/intelligence`, `/v3/signals`, `/v3/copilot`, `/v3/copilot/plans` × 2, `/v3/insights` | BUILT |
| Data & MD | `/v3/data`, `/v3/data/md-companies`, `/v3/data/md-people`, `/v3/data/imports`, `/v3/data/entity-resolution`, `/v3/review-queue` | BUILT (2026-09-05 nav additions) |
| Operations | `/v3/decisions`, `/v3/evidence`, `/v3/reports` | BUILT |
| Governance | `/v3/admin`, `/v3/audit`, `/v3/audit-log`, `/v3/status`, `/v3/security`, `/v3/settings` | BUILT |
| ICP Studio | `/v3/icp` | BUILT + LIVE (2026-08-23 Agent-B seed pif-icp-demo fit=HIGH) |
| Studio & Search | `/v3/studio` × 6 (agents, decisions, memories, models, playbooks, workflows), `/v3/search` | BUILT — "Studio-not-Live" marker retained |
| Marketing / demo | `/v3/pricing`, `/v3/executive` | BUILT |
| Command palette | 35 commands per `frontend/src/lib/commands.ts` | BUILT |

### Legacy `(dashboard)` shell (78 pages)

Present for backward compat / diagnostic. Product decision needed: retire or maintain.

### Design system

- `@salesos/tokens` (design tokens)
- `@salesos/ui` (components)
- `@salesos/design-language`
- `@salesos/widget-sdk`
- `@salesos/decision` — **STUB**
- `@salesos/agents` — **STUB**

### Bilingual

- ar-SA + en-SA
- RTL/LTR flipping
- Locale respects browser + localStorage (ADR-102)

### Auth pages

`/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email` in `(auth)` shell.

---

## 7. What is NOT built / is stubbed

| Item | State | Evidence |
|------|-------|----------|
| `@salesos/decision` FE package | STUB — do not present as GA AI | Per AGENTS.md §Essentials |
| `@salesos/agents` FE package | STUB | Same |
| AuditOS product tree | NOT a product in this repo | Per essentials rule |
| DecisionOS product tree | NOT a product in this repo | Per essentials rule |
| LocalContentOS product tree | NOT a product in this repo | Per essentials rule |
| Neo4j runtime graph queries | OFFLINE per ADR-108 | Deployed but not runtime-critical |
| Digital Twin | DEFERRED per ADR-0103 | — |
| Agent Runtime autonomous | DEFERRED per ADR-0104 | — |
| Revenue Brain autonomous | DEFERRED per ADR-0105 | — |
| Balady / Najiz / Taqeem external API integration | NOT built | Scrapers exist under `packages/scrapers/` but not integrated into runtime |
| ZATCA / VAT integration | NOT built | — |
| Google Meet / Microsoft Graph calendar sync | NOT built | Google OAuth exists (email/profile scope only) |
| WhatsApp Business / SMS | NOT built | — |
| Stripe live billing | NOT activated | Empty keys; deferred to Enterprise stage (C-18) |
| Mobile app (iOS / Android) | NOT built | Web PWA-ready per `manifest.webmanifest` |
| Public status page | NOT built | Recommendation only |
| DPA / MSA templates | NOT drafted (evidence) | Per compliance gap |
| SOC 2 report | NOT started | Harness exists; audit NOT started |
| ISO 27001 | NOT started | — |
| PDPL residency (in-KSA hosting) | NOT provisioned | Terraform + K8s exist but quarantined |
| Marketplace listings | NOT built | Signal Marketplace has platform packs only |
| Public API SDK (Python/JS/Go) | NOT built | OpenAPI exists |
| Webhooks outbound | LIMITED evidence | Verify per audit gap |
| SAML / SSO | NOT built | OIDC only |
| SCIM user provisioning | NOT built | — |
| Multi-currency (beyond SAR/USD) | NOT built | Config has `default_currency: "SAR"` |
| Multi-region DR | NOT provisioned | Single region deploy |

---

## 8. Rough size numbers (evidence-based)

| Layer | Count |
|-------|-------|
| Alembic migrations on disk | 109 files |
| Backend routers registered | ~85 include_router calls in `boot/routers.py` |
| Backend `app/modules/*` | 37 modules |
| Backend `domains/` packages | 18 packages |
| Backend runtime engines | 18 |
| Backend tests: unit total | 2761 pass (56 pre-existing env failures) |
| Backend tests: Phase 1-4 sum | 178 (49+26+86+17) |
| Backend tests: E2E Commercial Loop | 42/42 pass |
| Frontend v3 pages | 40 |
| Frontend legacy dashboard pages | 78 |
| Frontend nav domain items | 24 |
| Frontend command palette | 35 commands |
| ADRs | 40+ (0001 – 0117+) |
| Knowledge packs | 3 (construction, healthcare, financial-services) with 22 signals |
| Master data source rows | 862,775 |
| Master data companies (test DB) | 296,746 |
| Master data people (test DB) | 1,124 |
| Provenance rows | 1,524,725 |

---

## 9. What's live in production TODAY (best evidence)

| Item | Live status |
|------|-------------|
| API health `/health` | LIVE per 2026-08-24 probe |
| API version `/api/v1/version` | Available |
| Frontend `/v3` | Deployed on Vercel iad1 |
| Auth (register, login, OAuth) | Deployed |
| CRM screens | Deployed but **empty of real production tenant data** |
| Master Data | **On `salesos_test` only, NOT `salesos` production** |
| Signal Marketplace | 22 signals seeded (platform content, not tenant data) |
| ICP profiles | 1 demo profile (pif-icp-demo) — seeded, may be wiped by test runs |
| RAG documents | 5 in tenant A, 0 in tenant B (pilot seed) |
| AI Copilot | Backend gated on `feature_ai_copilot` (default **False** since 2026-09-12; lab via `FEATURE_AI_COPILOT=true`); **provider is DEV-ONLY** |
| HITL Approval | Backend + FE routes exist |
| Chaos harness | Not runtime |
| Monitoring dashboards | Prometheus text output at `/metrics`; Grafana dashboard config exists |
| Public status page | Not built |

---

## 10. Bottom line — what is Real vs Aspirational

**Real, defensible, works today:**
- Multi-tenant Postgres with dual roles + RLS + JWT RS256 + CSRF
- CRM Product Core (companies, contacts, deals, activities, pipeline, revenue, proposals, reviews)
- HITL approval FSM + RBAC + audit logging
- Grounded EvidencePack loop for 13 agents with honest INSUFFICIENT-EVIDENCE degradation
- Master Data / ER stack for Saudi companies (Muhide ingestion, safe CR handling, OPTION C)
- Phase 6 dry-run proven idempotent, zero safety violations
- Bilingual AR/EN UI at both dev + Vercel
- CI/CD pipelines with fitness gates
- Backend Railway + Frontend Vercel deployed

**Real but not yet valuable to a paying customer:**
- ICP scoring (needs real profiles)
- Signal Marketplace (needs tenant subscriptions + real events)
- RAG (needs real corpus)
- HITL (needs real reviewers with real work)
- Copilot (needs real LLM provider, real prompts, real evidence)

**Aspirational / stub / deferred:**
- Autonomous agents, digital twin, revenue brain
- External integrations (Balady/Najiz/Taqeem/ZATCA/WhatsApp/Calendar)
- Stripe live billing
- SAML/SSO/SCIM
- KSA-hosted deployment
- Mobile
- Multi-region DR

---

*Built inventory — evidence-based, honest, non-marketing.*
**File-specific update:** Built capability count is 85/113; evidence is scoped and must not be treated as production deployment proof.


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
