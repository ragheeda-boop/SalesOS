# FULL CRM / INTELLIGENCE REALITY CHECK

**Starting HEAD:** 5485363  
**Date:** 2026-08-10  
**Mode:** Read-only forensic audit (no code modifications)  
**Authority:** GA Engineering Audit supersedes all prior GO claims

---

## 1. Executive Summary

SalesOS has undergone 6 major development phases since the Architecture Freeze:

| Phase | What Changed |
|-------|-------------|
| Sprint 27 | CRM Productization (Company/Opportunity/Contact/Employee 360) |
| Sprint 28 | ADR-031 foundation (opportunity_contacts junction) |
| Sprint 29 | Attribution runtime (shadow engine, 4-step resolution) |
| Sprint 30 | Attribution Phase 2 (persistence + Employee 360 integration) |
| E1/E2 | Odoo integration (foundation + reconciliation) |
| F | Company Intelligence Persistence (signal lifecycle + DB) |

**The system is materially different from the gap register's baseline.** The old gap register is stale and must not be used for execution planning.

### What Works

- **CRM core is solid:** Company/Opportunity/Contact/Employee 360 all use real APIs, no mock data in production rendering
- **Attribution is runtime-proven:** 4-step resolution chain, persisted, consumed by Employee 360
- **Company signals are persisted:** 16-column table with lifecycle, RLS, dedup, fail-graceful persistence
- **Odoo integration is complete:** Foundation + Company/Contact/Opportunity reconciliation, idempotent, scheduled
- **Security is well-layered:** 70 tables with RLS, RS256 JWT, CSRF, RBAC, TrustedHosts, no hardcoded secrets
- **Migration chain is unbroken:** 90+ migrations from 0001 to c1d2e3f4a5b6 (HEAD)

### What's Broken / Missing

- **2 P0 findings** (data corruption risk, mock-in-production)
- **6 P1 findings** (dead route, dual opportunity tables, stub analytics, dual feature flags, unused persistence, attribution priority ordering)
- **8 P2 findings** (dead code, transient calculations, deprecated routes, legacy consumers)
- **4 P3 findings** (dead guidance components, legacy functions, spec-only pages)

### Validation Classification

**Current classification: PRODUCTION NO-GO (P0s present)**

P0s are fixable in-repo without architecture changes. After P0 closure: **PILOT-READY WITH CONDITIONS**.

---

## 2. Current Capability Matrix

| Capability | Status | Evidence |
|-----------|:------:|----------|
| Company CRUD | RUNTIME_VERIFIED | Full DB-backed CRUD, search, bulk, export |
| Company 360 | RUNTIME_VERIFIED | Real API, 9 data sections, signals persistence |
| Opportunity CRUD | RUNTIME_VERIFIED | Full DB-backed CRUD via commercial module |
| Opportunity 360 | RUNTIME_VERIFIED | Real API, 3 data sources (opp + contacts + attributions) |
| Contact CRUD | RUNTIME_VERIFIED | Full DB-backed CRUD, bulk upsert |
| Contact 360 | RUNTIME_VERIFIED | Real API, company link, linked opportunities |
| Employee 360 | RUNTIME_VERIFIED | Real API, 5 sub-components, signals + scoring + attribution |
| Tasks | RUNTIME_VERIFIED | Real API, priority/status filters, completion |
| Pipeline | RUNTIME_VERIFIED | Real API, stage advancement, KPIs |
| ADR-030 (Opportunity Contacts) | PROVEN | Migration + RLS + runtime verified on staging |
| ADR-031 (Attribution) | PROVEN | Phase 1+2 runtime verified, persisted, consumed by Employee 360 |
| Company Signals | PROVEN | 10/10 runtime proof, persisted with lifecycle |
| Employee Signals | IMPLEMENTED | 5 signal types detected, surfaced in Employee 360 UI |
| Employee Scoring | IMPLEMENTED | Dual path (persisted + on-the-fly), surfaced in UI |
| Odoo Foundation | PROVEN | External identity table, JSON-RPC client, sync service |
| Odoo Reconciliation | PROVEN | Company/Contact/Opportunity sync, idempotent, scheduled |
| Agent Runtime Core | PROVEN | 8/8 tests pass |
| Agent Runtime Staging | NOT_VALIDATED | Blocked on Railway healthcheck config |
| NBA Engine | IMPLEMENTED | 6-stage pipeline, consumes company_signals via Deal Health |
| Signal Marketplace | IMPLEMENTED | Feature-gated (default OFF), separate from Company 360 signals |
| Intelligence DTOs | IMPLEMENTED | Computed on-the-fly from 360 response, no caching |
| Analytics Cubes | NOT_IMPLEMENTED | All 3 query methods return empty lists |
| Decision Engine | NOT_IMPLEMENTED | Frontend stub (`throw new Error('Not implemented')`) |
| Digital Twin | NOT_IMPLEMENTED | Deferred per ADR-103 |
| Revenue Brain | NOT_IMPLEMENTED | Deferred per ADR-105 |
| Knowledge Graph (Neo4j) | NOT_IMPLEMENTED | Deferred per ADR-108 |
| AI Copilot | NOT_IMPLEMENTED | Feature-flagged False per AI_HONESTY.md |
| SSO | IMPLEMENTED | Google/Microsoft/GitHub OAuth, feature-gated |

---

## 3. CRM Reality

### 3.1 Company Module

| Aspect | Status | Evidence |
|--------|:------:|----------|
| CRUD API | IMPLEMENTED | `company/router.py` — full REST + bulk + export |
| Company 360 | RUNTIME_VERIFIED | `service.py:383-848` — loads 12+ sections |
| Intelligence DTO | IMPLEMENTED | `intelligence_computer.py` — transforms 360 to DTO |
| Search (cursored) | IMPLEMENTED | `search_companies_cursored()` — DB-backed |
| Ingest from source | IMPLEMENTED | `ingest_from_source()` — Notion/Excel |
| Sample data toggle | LOW RISK | Company 360 has demo toggle, off by default |

### 3.2 Opportunity Module

| Aspect | Status | Evidence |
|--------|:------:|----------|
| CRUD API | IMPLEMENTED | `commercial.py` — full REST |
| Stage advancement | IMPLEMENTED | PUT/PATCH stage endpoints |
| Pipeline management | IMPLEMENTED | `commercial_pipelines` table |
| KPIs | IMPLEMENTED | `/pipelines/{id}/kpis` endpoint |
| Quotes/Proposals/Contracts | IMPLEMENTED | Full workflow endpoints |
| Forecast | IMPLEMENTED | `/forecast/run` + `/forecast` |
| **Dual opportunity tables** | **CRITICAL** | `opportunities` (old) vs `commercial_opportunities` (new) — old still written by Odoo sync |

### 3.3 Contact Module

| Aspect | Status | Evidence |
|--------|:------:|----------|
| CRUD API | IMPLEMENTED | `contact/router.py` — full REST + bulk upsert |
| Contact 360 | RUNTIME_VERIFIED | Real API, company link, opportunity links |
| Duplicate schemas | LOW | `company/schemas.py` duplicates `contact/schemas.py` |

### 3.4 Tasks Module

| Aspect | Status | Evidence |
|--------|:------:|----------|
| Tasks API | IMPLEMENTED | `GET /api/v1/tasks`, `PUT /api/v1/tasks/{id}/complete` |
| Tasks page (legacy) | IMPLEMENTED | Real API, priority/status filters |
| Tasks page (v3) | IMPLEMENTED | Real API, search, honest empty state |

---

## 4. 360 Reality

### 4.1 Company 360

| Section | Data Source | Real API? |
|---------|-----------|:---------:|
| Health score | Computed from sections | N/A |
| Overview metrics | `companies` table | YES |
| Enrichment data | `company_features` | YES |
| Financial data | `commercial_contracts` + `commercial_quotes` | YES |
| Contacts | `contacts` table | YES |
| Branches/Licenses | `branches`/`licenses` tables | YES |
| Signals | `company_signals` (persisted) | YES |
| Intelligence | DTO computed from 360 | YES |
| Golden record | `golden_records` table | YES |
| Knowledge graph | `graph_nodes`/`graph_edges` | YES |

### 4.2 Opportunity 360

| Section | Data Source | Real API? |
|---------|-----------|:---------:|
| Opportunity detail | `commercial_opportunities` | YES |
| Linked contacts | `opportunity_contacts` (ADR-030) | YES |
| Attributions | `activity_attributions` (ADR-031) | YES |
| Company snapshot | `companies` table | YES |
| NBA recommendation | `nba_engine` (cached) | YES |

### 4.3 Contact 360

| Section | Data Source | Real API? |
|---------|-----------|:---------:|
| Contact detail | `contacts` table | YES |
| Company link | `companies` table | YES |
| Linked opportunities | `opportunity_contacts` | YES |
| Opportunity details | `commercial_opportunities` | YES |

### 4.4 Employee 360

| Section | Data Source | Real API? |
|---------|-----------|:---------:|
| Profile | `employees` table | YES |
| Signals | `employee_signals` table | YES |
| Scoring | `employee_scores` table | YES |
| Attribution summary | `activity_attributions` | YES |
| Timeline | `activity_records` | YES |
| Performance | Computed from signals | YES |
| Calendar | `employee_calendar_events` | YES |
| Email | `employee_email_events` | YES |

---

## 5. Intelligence Reality

### 5.1 Attribution (ADR-031)

| Aspect | Status | Evidence |
|--------|:------:|----------|
| Resolution engine | PROVEN | 4-step chain: explicit_ref → contact_match → domain_match → company_match |
| Persistence | PROVEN | `activity_attributions` table, 5 indexes, RLS |
| Employee 360 consumption | PROVEN | `_get_attribution_summary()` queries attributions |
| Opportunity 360 display | PROVEN | Frontend shows resolution method, confidence, state |
| Shadow mode | CONFIRMED | Read-only, no scoring/decision impact |
| **Priority ordering** | **DEFECT** | `domain_match` (0.30) checked before `company_match` (0.40) — inconsistent |

### 5.2 Employee Signals

| Aspect | Status | Evidence |
|--------|:------:|----------|
| Signal detection | IMPLEMENTED | 5 types: deal_assigned, contact_modified, meeting/call/email |
| Dead enum values | MINOR | DEAL_STAGE_CHANGED, TASK_COMPLETED, APPROVAL_COMPLETED defined but never detected |
| Persistence | IMPLEMENTED | `employee_signals` + `employee_scores` tables, RLS |
| UI surfacing | IMPLEMENTED | 5 frontend locations display employee signals |
| Scoring | IMPLEMENTED | Dual path: persisted + on-the-fly recomputation |

### 5.3 Company Signals

| Aspect | Status | Evidence |
|--------|:------:|----------|
| Detection logic | IMPLEMENTED | 9 signal types (expired, expiring, stalled, won, no_contacts, etc.) |
| Persistence | PROVEN | `company_signals` table, 16 cols, lifecycle, 10/10 proof |
| Fail-graceful | PROVEN | Persistence failure falls back to transient compute |
| Deal Health consumption | IMPLEMENTED | NBA engine queries `company_signals` |
| Revenue dashboard consumption | IMPLEMENTED | Revenue dashboard queries `company_signals` |
| Meeting intelligence consumption | IMPLEMENTED | Meeting brief queries `company_signals` |

### 5.4 NBA Engine

| Aspect | Status | Evidence |
|--------|:------:|----------|
| Pipeline | IMPLEMENTED | 6 stages: normalize → rules → scoring → AI → risk → rank |
| Deal Health | IMPLEMENTED | Consumes `company_signals` via raw SQL |
| Caching | IMPLEMENTED | Results cached in `company_features` table, 1h TTL |
| API endpoints | IMPLEMENTED | GET/POST/feedback endpoints with RBAC |
| Event subscription | IMPLEMENTED | Auto-recomputes on opportunity events |

---

## 6. Attribution Reality

See Section 5.1. Key additional findings:

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| Priority ordering inconsistency | MEDIUM | domain_match (0.30) before company_match (0.40) |
| Shadow mode only | INFO | No scoring/decision impact — intentional |
| Algorithm version v1.1.0-shadow | INFO | Versioned for future comparison |

---

## 7. Odoo Reality

| Aspect | Status | Evidence |
|--------|:------:|----------|
| External identity table | PROVEN | `odoo_external_ids`, 12 cols, RLS, FORCE |
| JSON-RPC client | PROVEN | `OdooJsonRpcClient` — real HTTP client |
| Company sync | PROVEN | Partner → Company, email/CR dedup, idempotent |
| Contact sync | PROVEN | Individual partner → Contact, email dedup |
| Opportunity sync | PROVEN | CRM lead → commercial_opportunities, stage mapping |
| Celery task | PROVEN | `odoo_sync_all` registered, beat schedule 6h |
| Feature gate | IMPLEMENTED | `feature_odoo_integration` flag in Integration Hub |
| Graceful skip | PROVEN | Returns `{"status": "skipped"}` when ODOO_URL empty |
| **Dual opportunity write** | **CRITICAL** | Odoo sync writes to `opportunities` (old table), not `commercial_opportunities` (canonical) |
| Configuration | NOT_CONFIGURED | All Odoo config fields default to empty strings |

---

## 8. Agent Runtime Reality

| Aspect | Status | Evidence |
|--------|:------:|----------|
| Core (8/8) | PROVEN | All unit tests pass |
| Schema/RLS | PROVEN | `agent_tasks`, `agent_actions`, `agent_runs` tables |
| State machine | PROVEN | ADR-112 defines states, implemented |
| Task queue | PROVEN | PostgreSQL CTE + FOR UPDATE SKIP LOCKED (ADR-111) |
| Dispatch task | PROVEN | `agent_dispatch_all` registered in Celery |
| **Staging worker** | **BLOCKED** | Railway healthcheck on non-HTTP Celery worker |
| **End-to-end** | **NOT_VALIDATED** | Cannot verify without working staging worker |

---

## 9. Security / RLS / RBAC

### 9.1 RLS Coverage

| Category | Tables | Status |
|----------|:------:|:------:|
| Category A (direct tenant_id) | 46 | ENABLE + FORCE |
| Category B (join/child) | 16 | ENABLE + FORCE |
| DB-05 Deferred-8 | 8 | ENABLE + FORCE |
| **Total** | **70** | **All covered** |

### 9.2 Auth / JWT

| Aspect | Status |
|--------|:------:|
| Algorithm | RS256-only (enforced at config + decode) |
| Key size | RSA-4096 |
| Dual audience | tenant (`salesos-api`) vs owner (`salesos-owner-platform`) |
| Refresh rotation | Family-based with reuse detection |
| Account lockout | 5 attempts → 15 min lock |
| Token blacklist | DB-backed |

### 9.3 RBAC

| Aspect | Status |
|--------|:------:|
| Roles | admin, manager, user, api, auditor |
| Enforcement | Dependency injection (per-endpoint opt-in) |
| Hierarchy | admin(3) > manager(2) > user(1) > api(1) > auditor(0) |

### 9.4 Security Headers

| Header | Value |
|--------|-------|
| CSP | `default-src 'self'` (strict) |
| X-Frame-Options | DENY |
| HSTS | `max-age=31536000; includeSubDomains` |
| X-Content-Type-Options | nosniff |
| Permissions-Policy | camera=(), microphone=(), geolocation=() |

### 9.5 CSRF

| Aspect | Status |
|--------|:------:|
| Mechanism | Double-submit cookie |
| Production misuse detection | Logs ERROR if testing flag set in prod |
| API key auth | CSRF still enforced |

### 9.6 Concerns

| Finding | Severity | Detail |
|---------|:--------:|--------|
| JWT payload in logs | LOW | `RequestLoggingMiddleware` extracts JWT without verification for logging |
| CSRF timing | LOW | Token compared with `!=` not `hmac.compare_digest()` |
| Dead HS256 code | LOW | `sdk/security.py` has `create_jwt()` defaulting to HS256 — zero callers |

---

## 10. Frontend ↔ Backend Contract Audit

### 10.1 API Coverage

| Frontend Page | Backend Endpoint | Contract Match |
|---------------|-----------------|:--------------:|
| `/companies` | `GET /api/v1/companies` | ✅ |
| `/companies/[id]` | `GET /api/v1/companies/{id}` | ✅ |
| `/companies/[id]/360` | `GET /api/v1/companies/{id}/360` | ✅ |
| `/contacts` | `GET /api/v1/contacts` | ✅ |
| `/contacts/[id]` | `GET /api/v1/contacts/{id}` | ✅ |
| `/opportunities` | `GET /api/v1/opportunities` | ✅ |
| `/opportunities/[id]` | `GET /api/v1/opportunities/{id}` | ✅ |
| `/employees` | `GET /api/v1/employees` | ✅ |
| `/employees/[id]` | `GET /api/v1/employees/{id}/360` | ✅ |
| `/tasks` | `GET /api/v1/tasks` | ✅ |
| `/signals` | `GET /api/v1/signals` | ✅ |
| `/analytics` | `GET /api/v1/executive/dashboard` | ✅ |
| `/copilot` | `GET /api/v1/copilot/*` | ✅ (gated) |

### 10.2 Mock Data in Production

| Location | Type | Risk |
|----------|------|:----:|
| MSW handlers (`src/mocks/`) | Dev/test infrastructure | NONE |
| Company 360 sample toggle | Demo feature, off by default | LOW |
| V3 tasks empty state | Honest text, no fake data | NONE |

### 10.3 Dead Frontend Components

~15-20 components in `components/guidance/` (onboarding, tours, coach marks) appear unused. Low severity.

---

## 11. Dead / Mock / Transient Functionality

### 11.1 Dead Code

| Item | Location | Severity |
|------|----------|:--------:|
| `feature_search_fuzzy_v2` flag | `config.py:153` — defined, never checked | LOW |
| `feature_crm_kanban` flag | `config.py:161` — defined, never checked | LOW |
| `opportunities.py` router | `app/routers/opportunities.py` — defined but never mounted | MEDIUM |
| `_render_pdf_stub()` | `domains/analytics/engine.py:179` — returns JSON as "PDF" | MEDIUM |
| Analytics cubes | `domains/analytics/cubes.py` — all return `[]` | MEDIUM |
| `sdk/security.py` HS256 JWT | Dead code, zero callers | LOW |
| `to_dict_legacy()` | `sdk/events/base.py:79` — legacy serialization | LOW |
| `run_legacy_equality()` | `scripts/validate_capability_registries.py:400` | LOW |

### 11.2 Mock-in-Production

| Item | Location | Severity |
|------|----------|:--------:|
| **LookalikeStore default** | `app/modules/gtm/lookalike_store.py:27` — uses `build_demo_opportunity_history()` as default factory | **HIGH** |

### 11.3 Dual Systems

| System | Location | Severity |
|--------|----------|:--------:|
| **Two opportunity tables** | `opportunities` (old) vs `commercial_opportunities` (new) — old still written by Odoo sync | **HIGH** |
| **Two feature flag systems** | `config.py` env vars vs `admin_feature_flags` table — table never consulted at runtime | MEDIUM |
| **Two Contact schemas** | `company/schemas.py` vs `contact/schemas.py` — duplicate classes | LOW |
| **Two event hierarchies** | `sdk/events/schemas.py` vs `sdk/events/domain_events.py` — duplicate classes | LOW |

### 11.4 Transient Calculations

| Calculation | Location | Impact |
|-------------|----------|:------:|
| `_detect_signals()` | `service.py:563` — computed on every 360 request, now persisted with fail-graceful | LOW (persisted, but compute still runs) |
| Attribution queries | `employee_360/service.py:460` — queried per request, no cache | LOW |
| Employee scores | `performance.py:82` — recomputed instead of reading persisted | MEDIUM |
| Intelligence DTOs | `intelligence_computer.py:26` — computed per request | LOW |

### 11.5 Unused Persistence

| Table | Evidence |
|-------|----------|
| `signal_catalog/subscriptions/events` | Feature-gated (default OFF), InMemory used |
| `marketplace_plugins/lifecycle_events` | Tables exist, no production router |
| `analytics_report_shares` | Table exists, no production read/write |
| `admin_feature_flags` | Full CRUD but never consulted at runtime |
| `dead_letter_queue` | Table exists, in-memory DLQ also exists |

### 11.6 Deprecated Routes (Still Mounted)

| Route | File | Status |
|-------|------|:------:|
| `GET /search/analytics` | `search.py:70` | Deprecated |
| `GET /search/suggestions` | `search.py:159` | Deprecated |
| `GET /search/reindex` | `search.py:206` | Deprecated |
| `POST /ai/prompts/{id}/test` | `ai.py:140` | Deprecated + gated |
| `GET /ai/usage` | `ai.py:195` | Deprecated + gated |

---

## 12. P0 Register

| ID | Category | Finding | File | Impact | Fix Complexity |
|----|----------|---------|------|--------|:--------------:|
| **P0-01** | Data Corruption | **LookalikeStore uses demo data as production default** | `gtm/lookalike_store.py:27` | Lookalike queries return fake company data | LOW — change default_factory |
| **P0-02** | Data Corruption | **Odoo sync writes to wrong table** | `runtime/odoo/__init__.py:550` | Odoo-synced opportunities go to `opportunities` (old), not `commercial_opportunities` (canonical) | MEDIUM — redirect sync target |

### P0-01 Fix

```python
# Current (BROKEN):
LookalikeStore(default_factory=lambda: build_demo_opportunity_history(tenant_id=""))

# Fix:
LookalikeStore(default_factory=list)  # Empty — no fake data
```

### P0-02 Fix

Odoo `sync_leads()` writes to `opportunities` table (old model) instead of `commercial_opportunities` (canonical per ADR-029). Must redirect to canonical table.

---

## 13. P1 Register

| ID | Category | Finding | File | Impact | Fix Complexity |
|----|----------|---------|------|--------|:--------------:|
| **P1-01** | Dead Code | `app/routers/opportunities.py` defined but never mounted | `boot/routers.py:528` | Confusion, dead routes | LOW — remove file |
| **P1-02** | Dual System | Two feature flag systems (`config.py` vs `admin_feature_flags` table) | `config.py` + `admin/db_models.py:98` | Maintenance confusion | LOW — document which is authoritative |
| **P1-03** | Dead Code | Analytics cubes return empty lists | `domains/analytics/cubes.py` | Analytics pages show nothing | MEDIUM — implement or remove |
| **P1-04** | Dead Code | `_render_pdf_stub()` returns JSON as PDF | `domains/analytics/engine.py:179` | Fake output | LOW — remove or implement |
| **P1-05** | Unused Persistence | `marketplace_plugins`/`marketplace_lifecycle_events` tables with no consumers | Alembic migrations | Schema bloat | LOW — document or remove |
| **P1-06** | Attribution | Priority ordering: domain_match (0.30) before company_match (0.40) | `runtime/attribution/__init__.py` | Lower-confidence method evaluated first | LOW — swap order |

---

## 14. P2 Register

| ID | Category | Finding | File | Impact |
|----|----------|---------|------|--------|
| **P2-01** | Transient Calc | Employee scores recomputed in `performance.py` instead of reading persisted | `domains/employee/performance.py:82` | Unnecessary CPU |
| **P2-02** | Transient Calc | Intelligence DTO computed per request with no caching | `intelligence_computer.py:26` | Minor latency |
| **P2-03** | Deprecated | 5 API routes OpenAPI-deprecated but still mounted | `search.py`, `ai.py` | Confusion |
| **P2-04** | Dead Enum | Employee signal types DEAL_STAGE_CHANGED, TASK_COMPLETED, APPROVAL_COMPLETED never detected | `domains/employee/models.py` | Dead code |
| **P2-05** | Duplicate Schema | ContactCreate/Response duplicated in company vs contact modules | `company/schemas.py` vs `contact/schemas.py` | Maintenance |
| **P2-06** | Duplicate Events | OpportunityCreated/StageChanged duplicated in schemas.py vs domain_events.py | `sdk/events/` | Maintenance |
| **P2-07** | Dead Flags | `feature_search_fuzzy_v2`, `feature_crm_kanban` defined but never checked | `config.py:153,161` | Config bloat |
| **P2-08** | Unused Persistence | `analytics_report_shares`, `admin_feature_flags` tables with no production reads | Various | Schema bloat |

---

## 15. P3 Register

| ID | Category | Finding | File | Impact |
|----|----------|---------|------|--------|
| **P3-01** | Dead Components | ~15-20 guidance/tour/onboarding components unused | `components/guidance/` | Bundle size |
| **P3-02** | Legacy | `to_dict_legacy()` in domain events | `sdk/events/base.py:79` | Dead code |
| **P3-03** | Legacy | `run_legacy_equality()` validation | `scripts/validate_capability_registries.py:400` | Dead code |
| **P3-04** | Spec Page | V3 Shell page renders static spec, no functionality | `v3/shell/page.tsx` | Confusion |

---

## 16. Dependency Graph

```
P0-01 (LookalikeStore) ────── no dependencies, fix immediately
P0-02 (Odoo sync target) ──── depends on ADR-029 canonical model

P1-01 (dead opportunities router) ── no dependencies
P1-02 (dual feature flags) ────────── no dependencies
P1-03 (analytics cubes) ───────────── needs business requirements
P1-04 (PDF stub) ──────────────────── no dependencies
P1-05 (unused tables) ─────────────── no dependencies
P1-06 (attribution ordering) ──────── no dependencies

P2-01 (employee score caching) ── depends on persisted scores
P2-02 (intelligence DTO cache) ── needs cache strategy
P2-03 (deprecated routes) ─────── needs consumer audit
P2-04-P2-08 ────────────────────── no dependencies

Track C (Agent Runtime) ──────── blocked on Railway (external)
AI Foundation ─────────────────── independent track, can start in parallel
```

---

## 17. Recommended Next 3 Milestones

### Milestone 1: P0 Closure + Reality Check Complete

**Scope:**
- Fix P0-01 (LookalikeStore demo data default)
- Fix P0-02 (Odoo sync target table)
- Full regression on staging
- P0/P1/P2 re-ranking based on fixed state

**Exit criteria:** 0 P0s, staging runtime proof, gap register updated

### Milestone 2: Agent Runtime Recovery + P1 Batch

**Scope:**
- Railway healthcheck fix (external, but we prepare the config)
- P1-01 through P1-06 batch fix
- All P1s are independent, can be parallelized

**Exit criteria:** 0 P1s, agent worker running on staging, all CRM queries verified

### Milestone 3: AI Foundation Audit + Design

**Scope:**
- Audit current LLM usage (AI copilot flag, enrichment, RAG)
- Design LLM Governance layer (policy, classification, throttling)
- Design Model Gateway (provider abstraction, timeout, circuit breaker)
- Data classification framework
- PII controls design
- Cost tracking: in-memory → durable tenant-aware

**Exit criteria:** AI Foundation ADR, Model Gateway design, no architecture freeze violations

---

## 18. Architecture Integrity Statement

### What Was Checked

1. All ADRs (37 total across 3 namespaces)
2. Architecture Freeze compliance
3. Migration chain integrity (90+ migrations)
4. RLS coverage (70 tables)
5. Security posture (auth, RBAC, CSRF, CORS, headers)
6. Frontend-backend contract alignment
7. Dead code / mock data / transient calculations
8. Dual systems / duplicate models
9. Unused persistence

### What Was NOT Changed

- No code modifications
- No architecture decisions reopened
- No ADRs created or modified
- No migrations applied
- No configurations changed

### Integrity Verdict

**Architecture Freeze: PARTIALLY COMPLIANT**

- Decision-level freeze is functioning (ADR required for changes)
- Implementation-level freeze has gaps (ADR-110 re-opened scope within 48h of deferral, Decision Engine "frozen" but is a stub, Identity domain frozen but non-compliant with Repository Pattern)
- ADR-029/030/031 numbering collision between product-root and backend namespaces needs resolution

### Maturity Honesty

The documentation ecosystem contains **significant maturity inflation**. Multiple sprint closures claim Security 88/100 and Production Readiness up to 98%, while the authoritative GA audit records 48/100 and 38/100. **The GA Engineering Audit is the authority for GO/NO-GO** per AGENTS.md.

---

**End of FULL CRM / Intelligence Reality Check. No files were modified.**
