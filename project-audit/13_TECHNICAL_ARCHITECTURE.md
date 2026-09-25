# 13 — Technical Architecture — المعمارية التقنية
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Source:** derived from actual code in `salesos/` (not diagrams). See `AUDIT_INVENTORY.md` §2–§4 for exact paths.

---

## 1. Bird's-eye view

```
                                  ┌─────────────────────────────────────┐
                                  │  Users (browsers, KSA-first, AR/EN) │
                                  └──────────────────┬──────────────────┘
                                                     │  HTTPS
                                                     ▼
                                     ┌──────────────────────────────┐
                                     │   Vercel (region iad1)       │
                                     │   Next.js 15 App Router      │
                                     │   /v3/* (40 pages) +          │
                                     │   /(dashboard)/* legacy (78)  │
                                     │   /api/* (2 route handlers)   │
                                     │   CSP + security headers      │
                                     └───────┬──────────────────────┘
                                             │  Bearer JWT (RS256, JWKS)
                                             │  CSRF token (double-submit)
                                             ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │                            Railway (US region)                        │
   │                                                                       │
   │  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
   │  │ FastAPI Backend       │  │ Celery Worker     │  │ Celery Beat  │   │
   │  │ (uvicorn)             │  │ (railway_celery)  │  │ (schedule)   │   │
   │  │  ~85 include_router() │  │  agent tasks +    │  │  cron        │   │
   │  │  20 top-level +       │  │  background jobs  │  │              │   │
   │  │  37 module routers +  │  └────────┬──────────┘  └──────┬───────┘   │
   │  │  runtime routers      │           │                    │           │
   │  └───────┬───────────────┘           │                    │           │
   │          │                           │                    │           │
   │          │  DB: salesos_app role (RLS-enforced)           │           │
   │          │  Migrations: salesos owner role (BYPASSRLS)    │           │
   │          ▼                                                            │
   │  ┌────────────────────────────────────────────────────────────┐      │
   │  │  PostgreSQL 16 (managed)                                    │      │
   │  │  109 alembic migrations · pgvector · pg_trgm                │      │
   │  │  RLS on 51 tenant tables (categories B1–B7)                 │      │
   │  │  Foundation: 11 md_* tables  · Phase 6: 7 md_* tables       │      │
   │  │  Approvals · Signals · RAG · ICP · Events · DLQ persistent  │      │
   │  └────────────────────────────────────────────────────────────┘      │
   │                                                                       │
   │  ┌───────────────┐  ┌───────────────┐  ┌──────────────────────┐     │
   │  │  Redis 7      │  │  Neo4j 5      │  │  Kafka (opt.)         │     │
   │  │  ephemeral    │  │  OFFLINE      │  │  event bus fallback   │     │
   │  │  rate limit   │  │  per ADR-108  │  │  in_memory default    │     │
   │  │  session      │  │  (governance  │  │                       │     │
   │  │  cache        │  │  gap)         │  │                       │     │
   │  └───────────────┘  └───────────────┘  └──────────────────────┘     │
   │                                                                       │
   └──────────────────────┬────────────────────────────────────────────────┘
                          │
                          ▼
     ┌─────────────────────────────────┐        ┌──────────────────────────┐
     │ LLM Provider — DEV-ONLY (AI     │        │ Google Workspace           │
     │ Horde / Cydonia)                │        │ (Gmail sync historyId,     │
     │ Grounded EvidencePack loop      │        │ Calendar sync syncToken)   │
     │ HITL gate before write          │        │ OAuth 2.0 Fernet-encrypted │
     │ Cost tracker + budget enforce   │        │ tokens                     │
     │ NO PRODUCTION CONTRACT SIGNED   │        └──────────────────────────┘
     └─────────────────────────────────┘

     ┌─────────────────────────────────┐        ┌──────────────────────────┐
     │ Stripe (billing, dunning,       │        │ Notion / Odoo / Meili /   │
     │ portal, subscriptions, webhook  │        │ Sentry — placeholders in  │
     │ ledger)                         │        │ config; DSN empty by def. │
     │ Keys empty; fail-closed 503     │        │                            │
     └─────────────────────────────────┘        └──────────────────────────┘
```

---

## 2. Backend architecture (DDD-ish)

**Layout under `salesos/backend/`:**

```
app/
  boot/            (main FastAPI wiring: routers, middleware, startup, exceptions)
  main.py          (~265 lines per audit; small entry point)
  config.py        (Pydantic Settings — 328 lines; single source of truth)
  database.py      (SQLAlchemy engine, init_db(), tenant GUC pinning)
  cache.py         (Redis client)
  celery_app.py + celery_schedule.py + railway_celery_service.py
  dependencies.py  (verify_token + tenant/user extraction)
  owner_auth.py    (Owner-Platform JWT audience)
  metrics/         (Prometheus)
  graphql/         (schema — mounted at /graphql)
  application/     (dashboard router + orchestration)
  common/          (middleware — CSRF, rate limit, tenant GUC, request id)
  modules/         (37 modules — see below)
  routers/         (20 legacy routers)
  alembic/         (versions/*.py — 109 files + env + script.py.mako)
domains/           (18 domain packages — DDD strict)
intelligence/      (Copilot agents + evaluation + governance + providers + reliability)
runtime/           (18 runtime engines: activity, capability, data_fabric, decision, event, feature_store, knowledge_graph, search, timeline, ux, schema, form, action, extension, plugin, nba, pipeline_analytics, admin)
platform/          (cross-cutting engines)
pipeline/          (data pipelines)
sdk/               (auth/jwks etc.)
memory/            (technical-debt, etc.)
cli/               (CLI tools)
mcp_server/        (MCP protocol server code)
knowledge-packs/   (Signal Marketplace content — construction, healthcare, financial-services)
scripts/           (ops scripts — seed, ingest, dry-run, safety, drift gate)
tests/             (unit + integration + evaluation + performance)
```

### Router hierarchy (from `boot/routers.py`)

- **Auth-required routers:** all mounted under `Depends(verify_token)` unless public
- **Public routers:** `/api/v1/identity` (login/register), Stripe webhook, employee-webhooks
- **GraphQL:** `/graphql` mounted with Bearer auth
- Approx **85 `include_router()` calls** across ~30 unique prefix groups

### Middleware chain
- Body size limit (`max_body_size` default 10 MB)
- CORS (env-configurable + auto-merge extra origins)
- Rate limit (Redis-backed; separate buckets per identity/auth/search/anon/etc.)
- CSRF (double-submit + `X-CSRF-Token` header; bare X-API-Key no longer bypasses per P1 fix)
- Tenant GUC pinning (`set_config('app.tenant_id', …, true)` per request — DEC-085)
- Request ID + structured logging
- Audit trail middleware (writes to `audit_logs`)

---

## 3. Data model architecture

### 3.1 Multi-tenancy

- Every tenant table has `tenant_id` column + RLS policy `USING (tenant_id::text = current_setting('app.tenant_id', true))`
- RLS covers 51 tenant tables (Categories B1–B7 per Alembic naming)
- Application connections use `salesos_app` role (respects RLS)
- Migration + DDL connections use `salesos` owner role (BYPASSRLS)
- Config REFUSES to start in production/staging without `APP_POSTGRES_PASSWORD`
- Cross-tenant IDOR closed on Decision Center (P0-01)

### 3.2 Master Data schema (Phase 6)

11 foundation tables + 7 Phase 6 tables:

Foundation:
- `md_source_files` (source files ingested)
- `md_source_rows` (raw immutable rows; `raw_payload` never modified)
- `md_global_companies` (canonical 296,746 records)
- `md_global_people` (canonical 1,124 records)
- `md_entity_matches` (canonical mapping)
- `md_entity_merge_history` (empty — no auto-merge)
- `md_entity_conflicts` (conflict audit)
- `md_provenance` (1,524,725 evidence rows)
- `md_review_candidates` (54,185 rows)
- `md_review_queue_state` (Phase 7-A capture-only)
- Other foundation

Phase 6:
- `md_identity_classifications` (7 buckets)
- `md_industry_normalization`
- `md_quality_scores` (versioned)
- `md_sales_readiness` (versioned)
- `md_canonical_authority`
- `md_contact_relationships` (VERIFIED / INFERRED)
- `md_derived_data` (misc derived)

**Invariants:**
- Source immutability (never modify `md_source_rows.raw_payload`; never delete source rows)
- Global IDs stable (existing G-C / G-P IDs never change)
- Never auto-merge (per ADR-0104)
- Government-ID hard-veto (per ADR-0105)
- No external APIs at runtime (no Apollo, Balady, Najiz, ZATCA calls)

### 3.3 Approval + Governance

- `approval_requests` — 6-status FSM (PENDING / APPROVED / REJECTED / ESCALATED / EXPIRED / CANCELLED); RBAC levels SELF/MANAGER/VP/EXECUTIVE
- `audit_logs` — governance events (policy blocks, HITL decisions, PII enforcement, admin ops)
- `llm_cost_entries` + `tenant_llm_budgets` (F2 cost tracking — Alembic `f8b3d4e5f6a7`)

### 3.4 Signals + Events + DLQ

- `signal_catalog` (22 platform signals — GLOBAL_PLATFORM, no tenant_id)
- `signal_subscriptions` (tenant-scoped, RLS)
- `signal_events` (tenant-scoped, RLS)
- `event_dead_letters` — persistent DLQ table (Alembic `g1h2i3j4k5l6`)

### 3.5 RAG + Vector

- `rag_documents` + chunks (Alembic `0015_rag_tables`, `h1i2j3k4l5m7_phase4a_rag_rls` = direct RLS on both)
- pgvector for embeddings (Alembic `0021_fix_vectors_embedding_type`)
- HNSW index (`0017_hnsw_index`)
- Dropped dual embedding (`0016_drop_dual_embedding` → single embedding column)

### 3.6 Commerce + Billing

- `subscriptions` (`c3a9f12d4e80`)
- `plan_entitlements` (`d0f6e89b1a37`) — enforced when flag on
- `usage_meters` (`a7e3b56c8d04`) — enforced when flag on
- `stripe_webhook_ledger` (`e5c1f34a6b02`)
- `portal_invoices_catalog` (`f6d2a45b7c03`)
- `dunning_cases` (`b8f4c67d9e15`)
- `pending_plan_change` (`c9e5d78a0f26`)

### 3.7 Users + Identity

- `users` (with lockout columns per `0033_add_users_lockout_columns`, department per `0041`)
- `refresh_tokens` (`0012`)
- `google_accounts` (`0047`, `0048_calendar_sync_token`)
- `oauth_tokens` (`0045`)
- `api_keys` (retention 365d)
- `permissions_catalog` + custom_roles (Studio permissions)

---

## 4. AI architecture (grounded)

### 4.1 EvidencePack loop

For every Copilot query:
1. Load `EvidencePack` from real DB via a shared loader (`intelligence/agents/research_evidence.py`)
   - Pins RLS: `set_config('app.tenant_id', <caller_tenant>, true)` before query
   - Reads: `md_global_companies`, activities, timeline, audit, RAG, signal_events, ICP profile
   - PII strip: contacts reduced to positions/counts only; no names/emails/phones in prompt
   - Value banding: monetary fields banded, not exact
2. Compose grounded prompt with `[E1]…[Ei]` citations
3. If pack is empty → return honest `UNKNOWN` / `INSUFFICIENT EVIDENCE` — do NOT call LLM
4. Call LLM (currently DEV-ONLY AI Horde) with strict JSON contract
5. Parse output with lenient parser; degraded → honest label preserved
6. Log to `AIGovernanceAudit` (policy, HITL decision, PII enforcement, tokens spent, groundedness)
7. If mode = Recommend → create `ApprovalRequest` (HITL gate)
8. Never auto-execute writes

### 4.2 Reliability + policy stack

- `ReliableProvider` — 3 retries, exponential backoff, error classification, circuit breaker per provider
- `PolicyGate` — data-class rules (`DataClassRule`) + max model tier
- `ProviderModelPolicy` — allowlist enforcement
- `LLMCostTracker` — Postgres-backed, `SELECT FOR UPDATE` budget check, monthly billing period
- `AIObservability` — Prometheus + Circuit-breaker transitions + request_id propagation

### 4.3 Copilot agents (13 grounded)

Per AGENTS.md §19–§22:
1. Research
2. Competitor
3. Relationship
4. Forecast
5. Pricing
6. Proposal
7. Renewal
8. Tender
9. Meeting
10. News
11. Contract
12. ICP
13. Recommendation

All share the same EvidencePack contract; all return honest UNKNOWN when data missing.

---

## 5. Frontend architecture

- Next.js 15 App Router (React 19+)
- TypeScript strict
- Tailwind CSS + `@salesos/design-language` tokens
- Radix UI primitives via `@salesos/ui`
- Feature packages: decision (STUB), agents (placeholder), design-language, ui, widget-sdk
- Two shells:
  - `/v3/*` (canonical, 40 pages, 24-nav-item nav)
  - `/(dashboard)/*` (legacy, 78 pages, retained)
- Bilingual: `en.json` + `ar.json` locale files; browser-detected + localStorage stored
- CSP enabled (ADR-102)
- Auth via Bearer JWT (RS256) + optional httpOnly cookie behind `feature_httponly_access_cookie=False`
- API traffic via `NEXT_PUBLIC_API_URL` (proxied for local dev)
- E2E via Playwright (`playwright.config.ts`, `playwright.full-crawl.config.ts`, `playwright.smoke.config.ts`)

---

## 6. Deployment architecture

### 6.1 Railway

- Backend main API service (`Dockerfile.railway` — Python 3.12 + Poetry-locked)
- Celery worker service (`Dockerfile.railway.celery` + `railway.worker.json`)
- Celery beat service (`railway.beat.json`)
- Start command dispatches by `RAILWAY_SERVICE_NAME` (case statement in `railway.json`)
- Managed Postgres 16
- Managed Redis 7
- Managed Neo4j 5 (deployed but OFFLINE per ADR-108 — governance gap)
- Managed backups: **not enabled** (row 3b BLOCKED-HUMAN)
- `preDeployCommand` drift: live uses `init_db()`; `railway.json` says `alembic upgrade head`

### 6.2 Vercel

- Next.js frontend
- Region `iad1` (US East) — NOT KSA
- Build command sets `NEXT_PUBLIC_BUILD_COMMIT / DATE / ID` from `VERCEL_GIT_COMMIT_SHA`
- Security headers set: X-Content-Type-Options, Referrer-Policy, X-Frame-Options, Permissions-Policy
- No custom domain evidence in this audit
- No Vercel Firewall / WAF evidence in this audit

### 6.3 GitHub CI (`.github/workflows/`)

9 workflows:
- `ci.yml` (39 KB — main CI)
- `deploy.yml` (28 KB — production)
- `deploy-production.yml`, `deploy-staging.yml` (11 + 11 KB)
- `docker-smoke.yml`
- `e2e-stage7.yml`
- `fitness-ci-subset.yml`
- `release-gates.yml`
- `security-scan.yml`

Schema-drift-gate fixed 2026-08-21: uses `--local-only` flag; DB-vs-repo sync enforced at deploy time by Railway `preDeployCommand`.

### 6.4 K8s (`salesos/infra/k8s/`)

Manifests present but QUARANTINED per DEC-149 — Railway is canonical for pilot/scale. K8s reserved for future Enterprise VPC deployments.

### 6.5 Observability

- Prometheus `/metrics` endpoint (custom `AIObservability` + `_check_kafka_status()` + Celery + SLA monitor)
- Structured logging (`extra={}` — 6 reliability + 4 policy_gate + 1 cost_tracker log calls converted)
- Sentry DSN: empty by default (no live error stream in this audit)
- Loki referenced in root `docker-compose.yml` but not `salesos/docker-compose.yml`
- OpenTelemetry referenced but production instrumentation UNKNOWN this audit

---

## 7. Security architecture

- JWT: RS256 (RSA-4096) via JWKS, HS256 forbidden (validator raises)
- Owner-Platform JWT: separate `jwt_owner_audience`
- Refresh tokens: DB-persisted with rotation
- CSRF: double-submit `X-CSRF-Token`; bare X-API-Key no longer bypasses (fix per P1 batch)
- Rate limits: separate buckets (identity 10/min, health 120/min, authed 100/min, anon 20/min, search 30/min, default 60/min)
- Webhook SSRF: 5-layer pinning (per `webhooks/url_safety.py`)
- Body size limit: 10 MB default
- CORS: env-configurable + auto-merge extras
- RLS: 51 tenant tables enforced; `salesos_app` role
- Audit: `audit_logs` writes across auth/approval/governance/admin ops
- Secret handling: fail-closed defaults (Stripe/OAuth/Neo4j/SMTP empty by default)
- SAST: `.semgrepignore` + gitleaks + Trivy (scanner ignores present)
- Encryption at rest: Fernet for OAuth tokens (`google_encryption_key` + rotation via `_previous`)

**Missing:**
- External pentest evidence in this audit
- SBOM / SCA formal artifact
- No signed data-residency posture doc for KSA

---

## 8. Testing architecture

- Unit: `salesos/backend/tests/unit/` — 2388 pass / 10 xfail / 3 skip (2026-08-19 count)
- Integration: `tests/integration/` — Muhide ingestion 16/16, ER 7/7, etc.
- Evaluation: `tests/evaluation/` (STAR audit foundation — `test_ai_guardrails.py` + `test_ai_policies.py`)
- E2E: `frontend/e2e/` — Playwright — 42/42 Commercial Loop (per 2026-09-05)
- Chaos: STORY-14-02 fault injection in CI
- LLM regression: STORY-14-07 golden fixtures (offline)
- Load / SLO: STORY-14-01 soak Option A signed
- DR drill: STORY-14-03 simulated non-prod

---

## 9. Notable ADRs (top-of-mind)

| ADR | Decision |
|-----|----------|
| ADR-0100 | Repository canonicalization (`salesos/` monorepo) |
| ADR-0101 | Platform bootstrap stabilization |
| ADR-0102 | Engineering hardening (RS256, CSP, poetry, etc.) |
| ADR-0103 | Digital Twin deferred |
| ADR-0104 | Agent runtime deferred (initially) — later ADR-0110 build-now |
| ADR-0105 | Revenue Brain deferred |
| ADR-0106 | Platform scope |
| ADR-0107 | Data residency field |
| ADR-0108 | Neo4j keep offline (v1.0) |
| ADR-0109 | ICP persistence + Kafka posture |
| ADR-0110 | Agent runtime build-now |
| ADR-0111 | Agent task queue on PostgreSQL |
| ADR-0112 | Agent state machine |
| ADR-0113 | Evidence architecture |
| ADR-0114 | Canonical write boundary |
| ADR-0115 | Agent security boundary |
| ADR-0116 | Tool capability architecture |
| ADR-0117 | Signal-agent integration |
| DEC-085 | Tenant GUC pinning per request |
| DEC-107 | Swarm dispatch always-on parallel-ready |
| DEC-130b | MetaData drift prevention |
| DEC-134 | Capability registry drift gate |
| DEC-149 | K8s quarantine (Railway canonical) |

---

## 10. Architectural risks

1. **DEV-ONLY LLM provider** — must sign production before selling
2. **Neo4j deployed-but-offline** — governance gap (spend + confusion)
3. **Dual FE shell** — long-term maintenance drift
4. **preDeployCommand file-side canonical (post-audit verified)** — root `railway.json` HAS `preDeployCommand: alembic upgrade head`; `salesos/railway.json` is a STALE pointer stub (NOT used); live Railway dashboard **UNKNOWN** — confirm before next deploy
5. **Backup schedule off** — DR gap
6. **US-only hosting (Railway + Vercel iad1)** — KSA Enterprise sale blocker per PDPL
7. **Nested duplicates in `packages/packages/`, `archive/archive/`, `infrastructure/infrastructure/`** — repo hygiene
8. **12 mypy_cache_* directories in `salesos/backend/`** — should be `.gitignored` (not committed but present on disk)
9. **`.venv/` in `salesos/backend/`** — should not be under repo path
10. **Kafka referenced everywhere but `in_memory` default** — clarify whether Kafka is aspirational or required

---

*Technical architecture — from code, not slides. See `14_DEPLOYMENT_HOSTING_AUDIT.md` for full deployment reality.*
**File-specific update:** Architecture is locally exercised in scoped tests; production topology, migrations and provider integrations remain gated.


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
