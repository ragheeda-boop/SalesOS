# Product Roadmap — Phase 0 → GA

> **Timeline:** 52 weeks, 26 two-week sprints, 8 phases. Baseline 2026-07-30 → GA target 2027-08-02.
> **Reads with:** `MASTER_EXECUTION_PLAN.md` (why/risks), `PROGRAM_PLAN.md` (epics/stories), `ENGINEERING_ROADMAP.md` (sprint detail), `RELEASE_PLAN.md` (release-stage gating overlaid on these phases).
> **Epic ID cross-reference:** EPIC-01 through EPIC-14, fully detailed in `PROGRAM_PLAN.md`.

```
Phase 0 (Sprints 1-3)   → Foundation & Security Hardening
Phase 1 (Sprints 4-7)   → Owner Platform Core (Tenants, Billing, Entitlements)
Phase 2 (Sprints 8-11)  → Integration Hub + Odoo GA
Phase 3 (Sprints 12-15) → Tenant Studio Core
Phase 4 (Sprints 16-19) → GTM Intelligence Nativization
Phase 5 (Sprints 20-22) → AI Studio + Marketplace
Phase 6 (Sprints 23-25) → Hardening, Scale, Compliance
Phase 7 (Sprint 26)     → GA Launch
```

---

## Phase 0 — Foundation & Security Hardening (Sprints 1-3, 6 weeks)

### Objectives
Close every documented P0 and make the codebase safe to build a commercial layer on top of. Nothing in Phase 1 onward is allowed to start against an unfixed foundation.

### Business Value
Every day this phase is skipped or shortened is a day the entire commercial roadmap rests on an IDOR bug and a broken CI pipeline. This phase has zero user-visible features and 100% risk-reduction value — it is justified entirely by what it prevents, not what it adds.

### Features
None user-facing. This phase ships fixes, not features.

### Architecture
- Introduce `middleware.ts` for server-side auth/tenant-context resolution (closes: *"No middleware.ts — Auth protection is client-side only"*).
- Postgres Row-Level Security (RLS) policies on all 72 tenant-scoped tables, replacing/augmenting application-level `WHERE tenant_id = ?` filtering.
- Formal separation of JWT issuer/audience in preparation for the future Owner/Tenant split (issued now even though Owner Platform doesn't exist yet, so EPIC-04-07 don't have to retrofit auth).

### Infrastructure
- CI pipeline gate: build must pass (frontend TypeScript + ESLint currently fails — fixed here, first).
- Alembic migration catch-up: reconcile 5 revisions of model/schema drift.

### Backend
- Fix Decision Center cross-tenant IDOR (`domains/decision_center/postgres_repo.py`).
- Fix Webhook SSRF — add URL allowlist (`app/routers/workflows.py:493`).
- Fix CSRF bypass via `X-API-Key` header (`app/common/csrf.py`).
- Add tenant-scoping to the 4 currently-global tables that should stay global under the two-plane model (relabel, don't force tenant_id onto `sso_connections`/`marketplace_plugins`/`feature_definitions`/`feature_values` — see `SAAS_PLATFORM_ARCHITECTURE.md` §11.3).

### Frontend
- Fix TypeScript + ESLint build failures blocking CI.
- Move auth-gating logic from client-side `useEffect`/localStorage check into `middleware.ts`.

### AI
None this phase.

### Integrations
None this phase (Integration Hub is Phase 2).

### Security
- Full remediation of all 3 documented P0s.
- Baseline SAST/dependency scanning wired into CI.
- Cross-tenant regression test suite established as a merge-gate template (used by every phase after this one).

### Testing
- `TEST_STRATEGY.md` §Unit and §Integration baselines established.
- Contract tests for the 3 fixed endpoints (Decision Center, Webhooks, CSRF-protected routes).
- CI coverage gate turned on for **new code only** (not retroactive).

### Deliverables
- D0.1: All 3 P0s closed, verified by an independent security review.
- D0.2: Green CI build (frontend + backend), Alembic head reconciled.
- D0.3: RLS policies live on all 72 existing tenant-scoped tables.
- D0.4: `middleware.ts` live, client-side-only auth gating removed.

### Dependencies
None — this is the root of the dependency tree (see `IMPLEMENTATION_SEQUENCE.md` position 1).

### Acceptance Criteria
- Security review sign-off document for all 3 P0s, each with a reproduction test that now fails (fails to exploit) as fixed.
- CI green on `main` for 5 consecutive days with no manual overrides.
- RLS policy test suite: 100% of tenant-scoped tables have a passing "tenant B cannot read tenant A's row" test.

### Go/No-Go Criteria (Phase 0 → Phase 1)
**GO** requires all 4 deliverables complete and acceptance criteria met. **No partial credit** — Phase 1 (Owner Platform, which introduces new tenant-adjacent tables: `subscriptions`, `usage_meters`) does not start if RLS is not proven on the existing 72 tables first, since the new tables inherit the same isolation pattern.

---

## Phase 1 — Owner Platform Core (Sprints 4-7, 8 weeks)

### Objectives
Stand up Side A (`DOM-020 Platform Operations`) to the point where a real tenant can be provisioned, billed, and entitlement-gated — without yet exposing any Studio, Integration Hub, or GTM capability.

### Business Value
This is the first phase that makes "sell to more than one company" *possible at all*. Without it, every subsequent phase's output can only ever serve Muhide.

### Features
- Tenant provisioning (self-service signup deferred to Phase 5; sales-assisted provisioning ships here).
- Plan assignment (Starter/Growth/Enterprise scaffolding — full entitlement enforcement completes this phase).
- Owner Admin Console MVP (`owner.salesos.io`): tenant list, subscription status, basic health view.

### Architecture
- `DOM-020` objects: `Tenant` (extended), `Subscription`, `Plan` (extended with `entitlements` JSONB), `UsageMeter`.
- Owner/Tenant JWT audience split goes live (built on Phase 0's groundwork).
- Two-plane API gateway routing: `/api/v1/owner/*` vs. tenant-scoped `/api/v1/*`.

### Infrastructure
- Stripe (or equivalent) sandbox integration.
- Owner Postgres schema (separate from pooled tenant schema, per `SAAS_PLATFORM_ARCHITECTURE.md` §13).

### Backend
- CAP-068 Tenant Provisioning service.
- CAP-069 Subscription & Billing service (Stripe webhook handling: payment success/failure, subscription created/updated/canceled).
- CAP-070 License & Entitlement Engine — evaluates `Plan.entitlements` at request time, layered over the existing (Grade A) feature-flag system, not replacing it.
- Token-ceiling enforcement scaffolding (pulled forward per R-06 in `MASTER_EXECUTION_PLAN.md` — even though AI Studio itself is Phase 5, the *ceiling mechanism* ships now so nothing after this phase can accidentally ship without it).

### Frontend
- CAP-078 Owner Admin Console MVP: `/tenants`, `/billing` read views.

### AI
None new — token-ceiling enforcement (above) is billing/entitlement infrastructure, not an AI feature.

### Integrations
- Stripe only.

### Security
- Owner/Tenant credential separation verified (an Owner token must be provably unusable against any `/api/v1/{tenant}/*` endpoint, and vice versa).
- Entitlement-bypass test suite: attempt to access a DOM/CAP outside a tenant's plan, confirm denial.

### Testing
- Subscription state-machine test matrix (trial → active → past_due → suspended → churned) — every transition tested, per R-05 in `MASTER_EXECUTION_PLAN.md`.
- Billing webhook idempotency tests (Stripe can redeliver webhooks — must not double-charge or double-provision).

### Deliverables
- D1.1: A tenant can be created, assigned a plan, and billed through a full trial→active cycle in a Stripe sandbox.
- D1.2: Entitlement Engine correctly gates at least 3 existing DOM/CAP combinations (proof of mechanism, full catalog gating completes across later phases as each DOM ships its entitlement mapping).
- D1.3: Owner Admin Console MVP live, internal-only.

### Dependencies
Phase 0 complete (tenant isolation proven before new tenant-adjacent commercial tables are introduced).

### Acceptance Criteria
- 100% pass on subscription state-machine test matrix.
- Zero entitlement-bypass findings in the dedicated security pass.
- Stripe sandbox: 20 consecutive test transactions (mix of success/decline/retry) processed correctly with no manual reconciliation needed.

### Go/No-Go Criteria (Phase 1 → Phase 2)
**GO** requires D1.1-D1.3 and all acceptance criteria. This is also the **Alpha release gate** (internal-only) per `RELEASE_PLAN.md`.

---

## Phase 2 — Integration Hub + Odoo GA (Sprints 8-11, 8 weeks)

### Objectives
Generalize the Odoo connector work already reviewed (`ODOO_INTEGRATION_BLUEPRINT.md`, `ARB_REVIEW_ODOO_INTEGRATION.md`, `ARB_META_REVIEW.md`) into the permanent `SourceConnector` framework, and ship Odoo as the first production-certified connector.

### Business Value
Converts SalesOS from "a platform with mock AI agent data" into "a platform running on live tenant operational data" — directly closes the single most-cited internal gap (11/11 AI agents on mock data).

### Features
- Tenant-facing Integrations Studio MVP: connect, test connection, map fields, schedule sync, monitor, disconnect — for Odoo specifically, built generically.
- Odoo → SalesOS sync: Company/Contact (via `cr_number` join to the existing 141,221-company government dataset), Opportunity, InteractionNote (`mail.message`, the highest-value data source per the Blueprint's own findings).

### Architecture
- `DOM-021 Integration Hub`: `SourceConnector` interface (`pull_incremental`, `write_back`, `test_connection`), `ExternalSystemConnection` (OBJ-330, tenant-scoped, Fernet-encrypted), `FieldMappingConfig` (OBJ-331), `SyncRun` (OBJ-332), `ConflictResolutionPolicy` (OBJ-333).
- Anti-Corruption Layer: Mapper → Validator → Transformer → Normalizer → ConflictResolver, exactly as specified in `ARB_REVIEW_ODOO_INTEGRATION.md` §9, implemented as one `OdooTranslator` class with six internal responsibilities (per the meta-review's right-sizing, not six public classes).
- `OBJ-019 SupportTicket`, `OBJ-020 TaskCaseExtension`, `OBJ-021 CustomerInvoice`, `OBJ-111 TimelineEvent` extension — the four objects approved (with corrections) by the ARB.

### Infrastructure
- Secrets vault integration for `credential_ref` (never raw credentials in `connection_config`).
- Monthly partitioning on the `TimelineEvent`/`InteractionNote` extension table from day one (fastest-growing table in the schema, per ARB projection).

### Backend
- `OdooAdapter` implementing `SourceConnector`.
- Incremental sync via `write_date` cursor (mandatory per ARB — no full-table polling).
- PII scrubbing before any note content reaches RAG, reusing existing `AI-GR-001` guardrail (not reinvented).
- Feature-flagged rollout: `feature_odoo_integration`, using the existing Grade-A flag infrastructure.

### Frontend
- Integrations Studio UI (`/studio/integrations`): connection wizard, field-mapping review screen, sync monitor/log viewer.

### AI
- `AI-PR-010 "Interaction Note Risk/Sentiment Analysis"` prompt registered — first real (non-mock) input to the AI Coach (`AI-AG-004`) and Activity Intelligence.

### Integrations
- **INT-013 Odoo XML-RPC** (incremental pull) — primary mechanism.
- **INT-014 Odoo Webhook** — built but disabled behind a flag until Phase 0's SSRF/CSRF fixes are re-verified in this phase's security pass (defense in depth — don't just trust the Phase 0 fix, re-test it against this specific new caller).

### Security
- Cross-tenant regression test extended to all new Integration Hub tables.
- Odoo API user reviewed for least-privilege (dedicated integration user, not admin).
- Credential encryption verified against the same standard as the existing `GoogleAccount` precedent.

### Testing
- Contract tests against Odoo's XML-RPC response shape (mocked Odoo sandbox for CI — this was flagged as a gap the original ARB itself missed, per `ARB_META_REVIEW.md` §9, and is explicitly included here).
- Field-mapping drift-detection job tested: simulate a Studio admin renaming a mapped field, confirm the sync alerts loudly instead of silently nulling data.
- Load test: sync against a simulated 27,264-record CRM dataset (the real observed scale) completes within the scheduled job window.

### Deliverables
- D2.1: A tenant can connect Odoo end-to-end through Studio with zero engineering involvement.
- D2.2: Incremental sync running on a schedule, monitored, alerting on drift.
- D2.3: `InteractionNote`/`TimelineEvent` extension live, PII-scrubbed, feeding AI Coach.
- D2.4: `SourceConnector` interface documented and proven generic (even though only one adapter exists yet) — code review confirms zero Odoo-specific logic leaked outside `OdooAdapter`.

### Dependencies
Phase 1 (Entitlement Engine must gate Integration Hub access per plan) + Phase 0 (SSRF/CSRF fix, re-verified here).

### Acceptance Criteria
- Zero cross-tenant leakage findings on new tables.
- Sync completes and alerts correctly in 3 injected-failure scenarios (field disappears, Odoo timeout, malformed record).
- This is also the **Private Alpha gate** (first external design partner) per `RELEASE_PLAN.md` — Muhide's real Odoo instance is the proof case.

### Go/No-Go Criteria (Phase 2 → Phase 3)
**GO** requires D2.1-D2.4, zero P0/P1 security findings, and 14 consecutive days of scheduled sync running against Muhide's real Odoo instance with no unresolved sync failure.

---

## Phase 3 — Tenant Studio Core (Sprints 12-15, 8 weeks)

### Objectives
Give tenant admins a no-code configuration surface over existing DOM-001–019 capabilities, proving the "configuration compiler, not a second runtime" principle at scale across multiple Studio modules (not just Integrations, which shipped in Phase 2).

### Business Value
Self-service configuration is what makes a SaaS platform scale past a services-heavy, engineer-per-tenant-customization model — this is the difference between a product and a project.

### Features
- Custom Objects & Fields (schema extension without migration).
- Workflow Builder no-code canvas (extends existing `CAP-025`).
- Scoring Rules Studio (Lead/Company/Opportunity).
- Territory rule configuration (extends existing `CAP-017`).
- Permissions UI (custom roles, extends existing `CAP-003`).
- Branding & Languages (white-label theming).
- Notification Rules.

### Architecture
- `DOM-022 Tenant Studio`: `CustomObjectDefinition`, `CustomFieldDefinition`, `WorkflowTemplate`, `ScoringRuleSet`, `TerritoryRuleSet`, `BrandingConfig`, `NotificationRule`, `PermissionOverride` (OBJ-340-349).
- Studio config objects are read by existing runtimes at execution time — no new parallel execution engine.

### Infrastructure
No new infra category — this phase is additive schema + application layer on existing Postgres/Redis.

### Backend
- Dynamic schema extension mechanism (EAV-style or JSONB-column-based custom fields — decision made in `PROGRAM_PLAN.md` EPIC-10, not deferred).
- Workflow Builder backend: translates a no-code canvas graph into the existing Workflow Engine's execution model — no second workflow interpreter.
- Scoring Rule evaluation engine, pluggable into existing NBA/Decision Center scoring paths.

### Frontend
- `/studio/objects-fields`, `/studio/workflows`, `/studio/scoring`, `/studio/territories`, `/studio/branding`, `/studio/notifications` — all under the `/studio/*` shell defined in `SAAS_PLATFORM_ARCHITECTURE.md` §4.

### AI
None new this phase (AI Studio is Phase 5) — Scoring Rules here are rule-based/deterministic, not LLM-based, by design (keeps this phase's scope bounded).

### Integrations
None new.

### Security
- Custom field/object definitions must not allow a tenant to define a field that collides with or shadows a reserved system column — validated at definition time.
- Permission overrides tested against privilege-escalation scenarios (a tenant-defined role must never exceed the ceiling of the tenant's own plan entitlements).

### Testing
- Custom object/field CRUD round-trip tests across at least 3 distinct tenant schemas simultaneously (proving isolation, not just correctness).
- Workflow Builder canvas → execution equivalence tests (a workflow built no-code must produce identical execution results to the equivalent hand-coded workflow).

### Deliverables
- D3.1: A tenant admin can add a custom field to Company/Contact/Opportunity and see it render in existing UI without an engineering ticket.
- D3.2: A tenant admin can build and activate a workflow via the no-code canvas.
- D3.3: Scoring Rules Studio live, tenant can override the default scorer.
- D3.4: Branding (logo, color, name) live per tenant.

### Dependencies
Phase 1 (Entitlement Engine — Studio modules are plan-gated from day one) + Phase 2 (Integrations Studio pattern proven, reused here).

### Acceptance Criteria
- Zero schema-collision incidents across a 5-tenant test cohort running concurrent custom-field definitions.
- Workflow equivalence test suite: 100% pass.

### Go/No-Go Criteria (Phase 3 → Phase 4)
**GO** requires D3.1-D3.4. This is also the **Internal Beta gate** (full internal team dogfooding across ≥3 internally-provisioned tenant workspaces) per `RELEASE_PLAN.md`.

---

## Phase 4 — GTM Intelligence Nativization (Sprints 16-19, 8 weeks)

### Objectives
Nativize the iSkala-carousel GTM concepts (Lead Discovery, ICP, Lookalikes, Enrichment, Verification, Website Intelligence, AI Outreach, Sequencing) as vendor-agnostic SalesOS capabilities, per `SAAS_PLATFORM_ARCHITECTURE.md` §6. Also: certify the **second connector** here (SAP or HubSpot per `MASTER_EXECUTION_PLAN.md` A4/R-02), proving the Integration Hub is genuinely generic and not an Odoo-shaped framework in disguise.

### Business Value
This is the phase that makes SalesOS competitive against the exact stack (Apollo/Clay/SmartLead/Debounce) the iSkala report reverse-engineered — as one native, governed, cross-connected system instead of 8 disconnected subscriptions with no shared data model.

### Features
- ICP Engine + TAM/SAM/SOM market sizing (against the platform's own 141,221-company government dataset — the genuine moat).
- Lead Discovery (government-data-first, external-provider-fallback).
- Lookalike Accounts (trained on tenant's own won/lost Opportunity history).
- Enrichment Waterfall + Contact Verification (native orchestration, swappable providers).
- Website Intelligence (reuses existing LLM spend, not a separate per-row vendor tool).
- AI Outreach (routed through existing governed Prompt Registry).
- Sequencing Engine (channel-agnostic: email + LinkedIn-via-compliant-partner-API + WhatsApp, bound to existing Activity/Task objects).
- **Second connector certified** (SAP or HubSpot — decided at Sprint 16 kickoff based on actual pipeline demand).

### Architecture
- `DOM-023 GTM Intelligence`: `ICPProfile`, `MarketSizingSnapshot`, `LookalikeModel`, `EnrichmentRequest`, `VerificationResult`, `WebsiteIntelligenceSnapshot`, `SequenceDefinition` (OBJ-350-356).
- Second `SourceConnector` implementation, built entirely by a different engineer than who built `OdooAdapter`, specifically to test that the interface is learnable/generic without the original author's tribal knowledge (a deliberate process check, not just a code check).

### Infrastructure
No new infra category.

### Backend
- ICP Engine scoring service.
- Enrichment Waterfall orchestration (calls provider connectors behind Integration Hub — providers are the swappable part, orchestration/dedup logic is the native asset).
- Sequencing Engine, bound to existing `Activity`/`Task` objects (not a new parallel data model).

### Frontend
- `/gtm/discovery`, `/gtm/enrichment`, `/gtm/website-intelligence`, `/gtm/outreach`, `/studio/gtm` (ICP/Persona/TAM-SAM-SOM config).

### AI
- AI Outreach copywriting, routed through tenant Prompt Library (Phase 5 delivers the full AI Studio surface; this phase delivers the specific outreach-copy prompt flows needed for GTM features to function, pulled forward as a dependency).

### Integrations
- Second connector certified end-to-end (SAP or HubSpot, decided based on pipeline).
- At least one enrichment/verification provider connector (e.g., a generic contact-verification API) certified.

### Security
- LinkedIn channel implemented only via a compliant partner API — no ToS-risk scraping/automation, per the iSkala report's own explicit warning.
- Enrichment provider credentials follow the same `ExternalSystemConnection` encryption pattern as Odoo — no exception for "just an API key" providers.

### Testing
- ICP scoring backtested against Muhide's real historical won/lost Opportunity data — accuracy/precision reported, not assumed.
- Second-connector certification test suite run by someone other than the Integration Hub's original architect (process validation, per above).

### Deliverables
- D4.1: ICP Engine live, TAM/SAM/SOM computed against real government data for at least one tenant.
- D4.2: Enrichment Waterfall + Verification live with ≥1 swappable provider each.
- D4.3: Sequencing Engine live across email + 1 additional channel.
- D4.4: **Second connector certified and syncing in production for at least one real or pilot tenant.**

### Dependencies
Phase 2 (Integration Hub) + Phase 3 (Tenant Studio, for ICP/Persona config surface).

### Acceptance Criteria
- Second-connector certification passes the same test suite Odoo passed in Phase 2, executed independently.
- ICP backtest report reviewed and signed off by CPO.

### Go/No-Go Criteria (Phase 4 → Phase 5)
**GO** requires D4.1-D4.4 **and** R-02 from `MASTER_EXECUTION_PLAN.md` explicitly closed (second connector proves genericity). This is also the **Partner Beta gate** (3-5 paying pilot tenants) per `RELEASE_PLAN.md`.

---

## Phase 5 — AI Studio + Marketplace (Sprints 20-22, 6 weeks)

### Objectives
Formalize AI Studio as a tenant-facing product surface (not just backend primitives), and ship the Marketplace certification pipeline so first-party connectors/playbooks/prompt-packs are installable, proving the ecosystem mechanism before GA.

### Business Value
AI Studio is what makes "your own prompts, your own scoring, your own AI memory" (from the platform framing) real and self-service rather than an engineering request. Marketplace is the proof that the platform, not just a product, model is real.

### Features
- Tenant-facing Prompt Library (extends `CAP-023`).
- AI Policies UI (data-class-to-model-tier rules, extends existing `AI-GR-*` guardrails).
- AI Memory MVP (tenant-scoped, `CAP-063`, currently ❌ — first real implementation here, scoped deliberately small: conversation-level memory only, not cross-session long-term memory, which is explicitly deferred).
- Marketplace browse/install UI (`/marketplace`, superseding the `CAP-036` stub).
- Certification pipeline (`CAP-094`) exercised against the second connector (from Phase 4) and at least one playbook.

### Architecture
- AI Studio wraps existing DOM-012 primitives — no new AI runtime, per `SAAS_PLATFORM_ARCHITECTURE.md` §7.
- `DOM-024 Marketplace & Ecosystem`: `MarketplaceListing` (OBJ-325) as the single object across connector/app/playbook listing types.

### Infrastructure
No new infra category.

### Backend
- Prompt Library CRUD + versioning, tenant-scoped.
- AI Memory storage (tenant-scoped, encrypted, with an explicit retention/deletion policy from day one — not retrofitted).
- Certification pipeline: automated contract testing (schema conformance to `SourceConnector`), security review checklist, sandboxed trial run.

### Frontend
- `/studio/ai` (Prompt Library, Policies, Memory settings).
- `/marketplace` (browse, install, manage installed).

### AI
- AI Memory MVP live.
- Per-tenant, per-plan model tier selection (Starter gets a smaller/cheaper model tier by default; Enterprise gets full tier access) — this is the commercial/AI cost link closing the loop opened in Phase 1's token-ceiling scaffolding.

### Integrations
None new — Marketplace surfaces the connectors already certified in Phases 2 and 4.

### Security
- AI Memory: explicit per-tenant data isolation test (tenant A's memory must never leak into tenant B's prompt context, including via any shared model-provider-level caching).
- Marketplace listing certification includes a security review step before any listing (even first-party) is publishable.

### Testing
- AI Memory isolation test suite (adversarial: attempt to retrieve tenant A's memory from a tenant B session).
- Certification pipeline dry-run: publish and install a test connector end-to-end, confirm the pipeline catches an intentionally broken test listing (negative test, not just happy path).

### Deliverables
- D5.1: Tenant-facing Prompt Library live, ≥1 tenant actively using a custom prompt.
- D5.2: AI Memory MVP live, scoped and tested for isolation.
- D5.3: Marketplace live with ≥3 first-party connector listings, ≥1 playbook listing.
- D5.4: Certification pipeline has processed at least one listing end-to-end, including one intentional failure case.

### Dependencies
Phase 3 (Tenant Studio pattern) + Phase 4 (second connector to certify through the pipeline).

### Acceptance Criteria
- Zero AI Memory cross-tenant leakage findings.
- Certification pipeline correctly rejects the intentionally-broken test listing.

### Go/No-Go Criteria (Phase 5 → Phase 6)
**GO** requires D5.1-D5.4. This is also the **Public Beta gate** (open signup with waitlist) per `RELEASE_PLAN.md`.

---

## Phase 6 — Hardening, Scale, Compliance (Sprints 23-25, 6 weeks)

### Objectives
No new user-facing features. Prove the system holds under real load, real failure modes, and real compliance scrutiny before committing to GA.

### Business Value
This phase is what separates "it worked in Partner Beta with 5 tenants" from "it will hold with 50+ tenants and an Enterprise prospect's security questionnaire." Skipping it is how SaaS companies have their first major incident in month one of GA.

### Features
None new.

### Architecture
- No structural changes — this phase validates the architecture built in Phases 0-5, it does not add to it. Any finding that *requires* an architecture change here is treated as a Phase 6 blocker, escalated to CTO/Chief Architect, not silently patched around.

### Infrastructure
- Load testing infrastructure (simulate 50 concurrent tenants, pooled-tier scale target per `SAAS_PLATFORM_ARCHITECTURE.md` §13).
- Chaos testing: connector failure injection, AI provider outage simulation, database failover drill.
- Backup/restore drill: full restore-from-backup exercised at least once, timed.

### Backend
- Performance profiling and optimization pass on any endpoint failing its SLO under load test.
- AI provider failover implemented and tested (per `OPERATIONS_MANUAL.md` runbook).

### Frontend
- Performance pass (bundle size, load time) — no new features, optimization only.

### AI
- LLM regression test suite established (detect silent quality degradation on provider model updates).
- AI provider failover: if primary provider (e.g., OpenAI) is unavailable, fallback provider engages within defined SLO.

### Integrations
- Connector failure-mode testing: simulate Odoo/second-connector being unreachable, confirm graceful degradation (no data corruption, clear tenant-facing status, automatic retry with backoff).

### Security
- Full penetration test (external firm or dedicated internal red-team exercise) — this is the first *external* security validation in the entire plan, deliberately scheduled after internal hardening, not instead of it.
- SOC2 Type I evidence collection begins (audit logging completeness, access review process, change management evidence).

### Testing
- Load test: 50 concurrent tenants, sustained peak traffic, SLOs held (see `PRODUCTION_READINESS_CHECKLIST.md` for specific numbers).
- Chaos test: connector outage, AI provider outage, database failover — each drill produces a written postmortem even though nothing "failed" (practice postmortems, not just incident postmortems).
- DR drill: full backup restore, timed against the RTO/RPO targets in `OPERATIONS_MANUAL.md`.

### Deliverables
- D6.1: Load test report — all SLOs held or a documented remediation plan for any miss.
- D6.2: Penetration test report — zero unresolved criticals.
- D6.3: DR drill completed, RTO/RPO measured and documented.
- D6.4: SOC2 Type I evidence collection underway (does not need to be complete — Type I audit itself is explicitly post-GA per `MASTER_EXECUTION_PLAN.md` A5).

### Dependencies
Phase 5 complete (feature-complete system to test against — this phase deliberately does not overlap with active feature development).

### Acceptance Criteria
- Zero unresolved pentest criticals.
- Load test SLOs held at 50-tenant simulated scale.
- DR drill RTO/RPO measured and within target.

### Go/No-Go Criteria (Phase 6 → Phase 7)
**GO** requires D6.1-D6.4. This is also the **Release Candidate gate** per `RELEASE_PLAN.md` — feature freeze begins here.

---

## Phase 7 — GA Launch (Sprint 26, 2 weeks)

### Objectives
Cut over from Release Candidate to General Availability. No new engineering scope — this phase is entirely about launch execution, monitoring, and commercial go-to-market activation.

### Business Value
The commercial payoff of every prior phase — pricing goes live, sales can quote confidently, support is staffed and ready.

### Features
None new (feature freeze carried from Phase 6).

### Architecture / Infrastructure / Backend / Frontend / AI / Integrations
No changes — RC build is the GA build, byte-for-byte, unless a P0 is found during the RC soak (in which case the fix is the only permitted change, re-tested, and the soak clock restarts per `RELEASE_PLAN.md`).

### Security
Final go/no-go security sign-off — confirms nothing regressed during the RC soak window.

### Testing
- Full regression suite run one final time against the exact GA candidate build.
- Launch-day monitoring dashboards verified live and alerting correctly (dry-run alert test).

### Deliverables
- D7.1: GA build tagged and deployed.
- D7.2: Commercial launch executed per `COMMERCIAL_LAUNCH_PLAN.md` (pricing live, sales enablement complete, support staffed).
- D7.3: Launch-day war room staffed per `OPERATIONS_MANUAL.md` incident response runbook, on standby (not necessarily needed — but staffed).

### Dependencies
Phase 6 RC soak (minimum 2 weeks, zero P0/P1 regressions) — this is a hard gate per `MASTER_EXECUTION_PLAN.md` §9 Exit Criteria.

### Acceptance Criteria
All 9 exit criteria in `MASTER_EXECUTION_PLAN.md` §9 satisfied simultaneously.

### Go/No-Go Criteria (GA Declaration)
Full leadership group (CPO, CTO, Chief Architect, Program Director, Release Manager) sign-off, per the RACI in `IMPLEMENTATION_SEQUENCE.md`. This is the only phase gate in this roadmap with no "next phase" on the other side of it — it is the terminal gate.
