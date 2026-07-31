# Program Plan — Epics, Stories, and Tasks

> **Reads with:** `PRODUCT_ROADMAP.md` (which phase each epic sits in), `ENGINEERING_ROADMAP.md` (which sprint each story lands in), `IMPLEMENTATION_SEQUENCE.md` (why this order).
> **Complexity scale:** S (≤3 days, 1 engineer), M (1 sprint, 1 engineer), L (1 sprint, 2 engineers or 2 sprints, 1 engineer), XL (2+ sprints, 2+ engineers).
> **Story ID scheme:** `STORY-{EPIC}-{NN}`. **Task ID scheme:** `TASK-{STORY}-{letter}`.

---

## EPIC-01 — Security P0 Remediation

**Phase:** 0 · **Complexity:** L · **Dependencies:** None (root of dependency tree)

**Business Goal:** Eliminate the three documented P0 vulnerabilities before any commercial-layer code is written on top of them. A SaaS platform cannot be sold with a known cross-tenant data leak.

**Capabilities:** None new — this epic hardens existing DOM-001–019 code, no new CAP ID.

| Story | Description | Complexity |
|---|---|---|
| STORY-01-01 | Fix Decision Center cross-tenant IDOR in `domains/decision_center/postgres_repo.py` | M |
| STORY-01-02 | Fix Webhook SSRF — URL allowlist in `app/routers/workflows.py:493` | M |
| STORY-01-03 | Fix CSRF bypass via `X-API-Key` header in `app/common/csrf.py` | S |
| STORY-01-04 | Establish cross-tenant regression test template reused by every later epic | M |

**Technical Tasks:** TASK-01-01-a (reproduce IDOR with a failing test first); TASK-01-01-b (add tenant_id filter + RLS policy); TASK-01-02-a (implement allowlist config + validation); TASK-01-02-b (add SSRF regression test hitting internal IP ranges); TASK-01-03-a (require CSRF token even when `X-API-Key` present, or scope API-key auth to non-browser clients only).

**Infrastructure Tasks:** Wire SAST scan into CI; add dependency vulnerability scan (e.g., `pip-audit`/`npm audit`) as a CI gate, non-blocking initially (informational) then blocking from Sprint 2.

**Security Tasks:** Independent review of each fix by someone other than the author; document each in a fix-verification memo.

**Documentation Tasks:** Update `CANONICAL_ARCHITECTURE.md` §14 to move these 3 items from "Critical Gaps" to "Resolved" with commit references.

**QA Tasks:** Each fix ships with a regression test that fails against the pre-fix code (proves the test actually catches the bug) and passes against the fix.

**Deployment Tasks:** Fixes deploy independently as they complete (don't batch security fixes waiting for the whole epic) — each is its own PR, its own deploy.

**Definition of Done:** All 3 fixes merged, independently reviewed, regression-tested, deployed to production, and verified against Muhide's live tenant with zero behavior regression.

---

## EPIC-02 — Tenant Isolation Hardening

**Phase:** 0 · **Complexity:** L · **Dependencies:** EPIC-01 (share the same regression-test infrastructure)

**Business Goal:** Move tenant isolation from "application-code discipline" (where the IDOR bug lived) to "database-enforced guarantee" — the only isolation model that scales to hundreds of tenants without every future PR being a potential repeat of EPIC-01's root cause.

**Capabilities:** None new — hardens the isolation guarantee underlying all of DOM-001–019.

| Story | Description | Complexity |
|---|---|---|
| STORY-02-01 | Design and roll out Postgres RLS policies across all 72 tenant-scoped tables | XL |
| STORY-02-02 | Introduce `middleware.ts` for server-side auth/tenant-context resolution | M |
| STORY-02-03 | Split JWT issuer/audience in preparation for future Owner/Tenant separation (EPIC-04) | M |
| STORY-02-04 | Relabel the 4 intentionally-global tables (`sso_connections`, `marketplace_plugins`, `feature_definitions`, `feature_values`) as Owner-Platform-scoped rather than "tenant-isolation gaps" | S |

**Technical Tasks:** Per-table RLS policy generation (scripted, not hand-written 72 times); session variable (`app.current_tenant_id`) set per-request from the JWT claim, RLS policies reference it; middleware redirect logic for unauthenticated/wrong-tenant access attempts.

**Infrastructure Tasks:** RLS policy test harness that can run against a seeded multi-tenant test database (≥5 synthetic tenants) as part of CI.

**Security Tasks:** Adversarial test suite: for every tenant-scoped table, attempt a cross-tenant read/write with a valid-but-wrong-tenant JWT, confirm denial at the DB layer even if application code has a bug.

**Documentation Tasks:** Document the RLS policy pattern as the mandatory template for every new tenant-scoped table going forward (referenced by every later epic that adds tables).

**QA Tasks:** RLS regression suite becomes a permanent CI gate — any PR adding a tenant-scoped table without an RLS policy fails CI automatically (schema-lint check).

**Deployment Tasks:** RLS rollout is staged per-table-group (not all 72 at once) with a rollback plan per group in case a policy misconfiguration blocks legitimate access.

**Definition of Done:** 100% of tenant-scoped tables have an RLS policy; adversarial cross-tenant test suite passes at 100%; schema-lint CI check blocks any future table missing the pattern.

---

## EPIC-03 — CI/CD & Test Foundation

**Phase:** 0 · **Complexity:** M · **Dependencies:** None (parallel to EPIC-01/02)

**Business Goal:** A commercial platform cannot ship on a red build. Fix the immediate blockers (frontend build failure, Alembic drift) and establish the coverage-gate discipline that prevents the existing Grade-D test debt from being reproduced in all the new commercial-layer code.

**Capabilities:** None new.

| Story | Description | Complexity |
|---|---|---|
| STORY-03-01 | Fix frontend TypeScript + ESLint build failures | M |
| STORY-03-02 | Reconcile Alembic migration drift (5 revisions behind) | M |
| STORY-03-03 | Establish CI coverage gate for new code (not retroactive) | S |
| STORY-03-04 | Baseline contract test framework (used by every future API-adding epic) | M |

**Technical Tasks:** Triage and fix each TS/ESLint error class (not just suppress); generate and apply the missing Alembic revisions against current models, verify no data-loss migration path; configure coverage tool (e.g., `pytest-cov`/`c8`) with a diff-coverage gate (new/changed lines only).

**Infrastructure Tasks:** CI pipeline restructure to run frontend build, backend tests, migration check, and coverage gate as independent, parallelized jobs (fail fast on whichever breaks first).

**Security Tasks:** None specific — covered by EPIC-01.

**Documentation Tasks:** `TEST_STRATEGY.md` §Coverage Gates references this epic's threshold and mechanism.

**QA Tasks:** Establish the contract-test template (OpenAPI schema validation against actual responses) used by every subsequent epic's API work.

**Deployment Tasks:** None (internal tooling only).

**Definition of Done:** Green CI on `main`, 5 consecutive days, zero manual overrides; coverage gate enforced and blocking merges below threshold on new code.

---

## EPIC-04 — Tenant Provisioning & Lifecycle

**Phase:** 1 · **Complexity:** L · **Dependencies:** EPIC-02 (RLS proven before new tenant-adjacent tables exist)

**Business Goal:** Make "onboard a new customer" a repeatable, self-service-capable operation instead of a manual, ad hoc process — the foundational unlock for selling to more than one company.

**Capabilities:** CAP-068 Tenant Provisioning

| Story | Description | Complexity |
|---|---|---|
| STORY-04-01 | `Tenant` object extension: `plan_id`, `region`, `data_residency`, `provisioning_status`, `trial_ends_at` | M |
| STORY-04-02 | Provisioning workflow: create tenant → seed default Studio config from plan template → assign first admin user | M |
| STORY-04-03 | Suspension/reactivation workflow (tenant read-only on suspension, not deleted) | M |
| STORY-04-04 | Deletion workflow with retention-window enforcement (PDPL-aligned) | M |

**Technical Tasks:** Migration adding new `Tenant` columns; provisioning orchestration service (idempotent — re-running a provisioning job for an already-provisioned tenant is a no-op, not a duplicate); default Studio config templates per plan tier.

**Infrastructure Tasks:** Background job queue for provisioning (reuses existing `CAP-028 Scheduled Jobs` infra, not a new job runner).

**Security Tasks:** Verify a suspended tenant's API tokens are rejected at the gateway, not just at the application layer (defense in depth).

**Documentation Tasks:** `OPERATIONS_MANUAL.md` runbooks for provisioning/suspension/deletion draw directly from this epic's implementation.

**QA Tasks:** Full lifecycle test: provision → use → suspend → reactivate → delete, verifying data state and access at every transition.

**Deployment Tasks:** Feature-flagged (`feature_self_service_provisioning`) — sales-assisted provisioning ships first (Phase 1), self-service UI is a Phase 5+ increment.

**Definition of Done:** A tenant can be provisioned, suspended, reactivated, and deleted via an internal Owner Console action, each step logged and auditable.

---

## EPIC-05 — Subscription & Billing

**Phase:** 1 · **Complexity:** XL · **Dependencies:** EPIC-04

**Business Goal:** Convert usage into revenue, reliably. This is the single highest-financial-risk epic in the plan (R-05 in `MASTER_EXECUTION_PLAN.md`) — billing bugs mean either revenue leakage or wrongful customer suspension, both directly reputational.

**Capabilities:** CAP-069 Subscription & Billing

| Story | Description | Complexity |
|---|---|---|
| STORY-05-01 | `Subscription` object + state machine (trial/active/past_due/suspended/churned) | L |
| STORY-05-02 | Stripe integration: checkout, webhook handling (idempotent), invoice sync | XL |
| STORY-05-03 | Usage metering (`UsageMeter`): seats, AI tokens, connector syncs, storage | L |
| STORY-05-04 | Dunning workflow (failed payment retry, grace period, auto-suspend) | M |
| STORY-05-05 | Proration logic for mid-cycle plan upgrade/downgrade | M |

**Technical Tasks:** Stripe webhook signature verification; idempotency key handling for replayed webhooks; usage-meter aggregation job (hourly rollup, not per-event write to avoid write amplification); proration calculation service with unit tests covering every upgrade/downgrade direction.

**Infrastructure Tasks:** Stripe sandbox → production credential rotation process (documented, not ad hoc); webhook endpoint monitoring (alert if Stripe reports repeated delivery failures).

**Security Tasks:** PCI scope confirmation (SalesOS never touches raw card data — Stripe Checkout/Elements only) documented explicitly so this is a designed decision, not an accident.

**Documentation Tasks:** Full subscription state-machine diagram in `COMMERCIAL_LAUNCH_PLAN.md`; billing runbook in `OPERATIONS_MANUAL.md`.

**QA Tasks:** Full state-machine test matrix (every transition × every trigger); webhook replay/idempotency test (send the same webhook twice, confirm no double-processing); 20-transaction sandbox soak test before Partner Beta.

**Deployment Tasks:** Billing goes live in Stripe **test mode** through Phase 4 (Partner Beta pilots are not charged real money until explicitly converted); production mode flips on for Phase 5 Public Beta.

**Definition of Done:** Every state transition in the subscription state machine is tested and correct; zero double-charge or double-provision incidents across the sandbox soak test; dunning workflow correctly suspends after the defined grace period with no manual intervention.

---

## EPIC-06 — License & Entitlement Engine

**Phase:** 1 · **Complexity:** L · **Dependencies:** EPIC-05 (`Plan.entitlements` needs a real `Plan`/`Subscription` model to gate against)

**Business Goal:** Make commercial packaging (what a customer paid for) enforceable in code, without duplicating the existing, mature feature-flag system — this is the mechanism that makes "Starter/Growth/Enterprise" mean something technically, not just on a pricing page.

**Capabilities:** CAP-070 License & Entitlement Engine

| Story | Description | Complexity |
|---|---|---|
| STORY-06-01 | `Plan.entitlements` schema design (which DOM/CAP + quota per plan) | M |
| STORY-06-02 | Entitlement evaluation middleware (checked per-request, cached per-tenant-per-minute to avoid a DB hit on every call) | L |
| STORY-06-03 | Quota enforcement (seats, AI tokens, connectors, storage) tied to `UsageMeter` | M |
| STORY-06-04 | Entitlement-bypass adversarial test suite | M |

**Technical Tasks:** Entitlement cache invalidation on plan change (must not let a downgraded tenant keep access until a stale cache expires — correctness over performance here); quota-exceeded response contract (clear 402/403-style response, not a silent failure).

**Infrastructure Tasks:** Redis-backed entitlement cache (reuses existing Redis infra, no new cache layer).

**Security Tasks:** Adversarial test: attempt to access a DOM/CAP outside the tenant's plan via direct API call (not just through UI, which could hide the gate) — confirm server-side denial in all cases.

**Documentation Tasks:** Entitlement-to-plan mapping table published and kept current in `COMMERCIAL_LAUNCH_PLAN.md` §Packaging — this is the single source of truth sales quotes against.

**QA Tasks:** Test every plan tier against every gated DOM/CAP combination — a full cross-product matrix, not spot checks.

**Deployment Tasks:** Ships alongside EPIC-05 — entitlements are meaningless without a real subscription to attach them to.

**Definition of Done:** Zero entitlement-bypass findings across the full plan × capability matrix; plan downgrade takes effect within the defined cache TTL (target: ≤60 seconds) with no manual cache flush needed.

---

## EPIC-07 — Owner Admin Console

**Phase:** 1 · **Complexity:** M · **Dependencies:** EPIC-04, EPIC-05

**Business Goal:** Give Platform Ops/Support/CS a working surface to actually run the business side of SalesOS — without this, every tenant question is a database query by an engineer.

**Capabilities:** Supports CAP-068, 069, 073, 074, 075, 076

| Story | Description | Complexity |
|---|---|---|
| STORY-07-01 | `/tenants` list + detail view (status, plan, usage snapshot) | M |
| STORY-07-02 | `/billing` view (subscription status, invoice history, dunning state) | M |
| STORY-07-03 | Owner-only auth shell (`owner.salesos.io`, separate JWT audience from EPIC-02) | M |

**Technical Tasks:** Read-only views first (Phase 1 scope) — write actions (suspend, refund, plan override) are additive in later phases as the underlying engines (EPIC-04-06) mature.

**Infrastructure Tasks:** Separate frontend deployment target (`owner.salesos.io` subdomain) from the tenant app shell.

**Security Tasks:** Confirm an Owner-console session token is rejected by every tenant-scoped API endpoint (and vice versa) — direct test of the EPIC-02 audience split.

**Documentation Tasks:** Internal runbook: "how Platform Ops uses the Owner Console" — feeds `OPERATIONS_MANUAL.md`.

**QA Tasks:** Cross-audience token rejection test (see Security Tasks) as an automated regression, not a one-time manual check.

**Deployment Tasks:** Internal-only release (no external users) — this is explicitly the Phase 1/Alpha-gate deliverable.

**Definition of Done:** Platform Ops can view any tenant's status/plan/billing without engineering involvement; audience-isolation test passes.

---

## EPIC-08 — Integration Hub Framework

**Phase:** 2 · **Complexity:** XL · **Dependencies:** EPIC-01 (webhook path), EPIC-06 (entitlement-gated access)

**Business Goal:** Build the generic connector framework once, correctly, so every subsequent connector (Odoo now, SAP/HubSpot/etc. later) is an adapter implementation, not a re-architecture. This is the direct resolution of the Odoo ARB's central debate — the framework the meta-review called premature for one connector is now mandatory because the scope is explicitly "hundreds of customers, many ERPs."

**Capabilities:** CAP-067 Integration Hub (generalized), CAP-081 Integrations Studio

| Story | Description | Complexity |
|---|---|---|
| STORY-08-01 | `SourceConnector` interface definition (`pull_incremental`, `write_back`, `test_connection`) | M |
| STORY-08-02 | `ExternalSystemConnection` object: tenant-scoped, Fernet-encrypted credentials, `credential_ref` vault pointer | L |
| STORY-08-03 | `FieldMappingConfig`: versioned, tenant-scoped, with drift-detection (`fields_get()`-equivalent diff-check job) | L |
| STORY-08-04 | Anti-Corruption Layer: `OdooTranslator`-pattern class (Mapper→Validator→Transformer→Normalizer→ConflictResolver as internal methods, not 6 public classes) | L |
| STORY-08-05 | `SyncRun` object + scheduling (reuses `CAP-028 Scheduled Jobs`) | M |
| STORY-08-06 | `ConflictResolutionPolicy`: per-field, per-connection resolution rules, with the write-back feedback-loop exclusion rule (SalesOS-authored fields never read back as "fresh" source data) | M |
| STORY-08-07 | Integrations Studio UI: connect / test / map fields / schedule / monitor / disconnect | L |

**Technical Tasks:** Vault integration for `credential_ref` (never store raw secrets in `connection_config` JSONB); incremental-cursor watermark storage per connection per model; drift-detection job scheduling and alerting (reuses `CAP-044/045` Monitoring/Telemetry).

**Infrastructure Tasks:** Monthly partitioning strategy applied to any high-volume synced table (e.g., the `TimelineEvent` extension) from creation, not retrofitted.

**Security Tasks:** Cross-tenant regression test extended to all Integration Hub tables (per EPIC-02's mandatory template); credential encryption verified against the `GoogleAccount` precedent standard.

**Documentation Tasks:** `SourceConnector` interface documented as the mandatory contract for every future adapter — this doc is what a second-connector engineer reads with zero other context (tested directly in EPIC-11's second-connector story).

**QA Tasks:** Contract test suite any adapter must pass to be considered "certified" (used later by CAP-094 Marketplace certification).

**Deployment Tasks:** Framework ships feature-flagged; no tenant sees any Integration Hub UI until at least one adapter (EPIC-09) is ready behind it.

**Definition of Done:** `SourceConnector` interface is documented and has zero implementation-specific leakage in its contract; `ExternalSystemConnection` passes the full cross-tenant regression suite; a mock/fake adapter can be written and certified against the framework using only the published interface docs (proves genericity before Odoo-specific work even starts).

---

## EPIC-09 — Odoo Adapter GA

**Phase:** 2 · **Complexity:** XL · **Dependencies:** EPIC-08

**Business Goal:** Ship the first real, production-hardened connector — directly closes the most-cited internal gap (11/11 AI agents on mock data) and validates the Integration Hub framework against a genuinely messy real-world system (Odoo Studio's auto-generated fields, mixed-purpose `project.task` usage).

**Capabilities:** Instantiates CAP-067 via `OdooAdapter`

| Story | Description | Complexity |
|---|---|---|
| STORY-09-01 | `OdooAdapter`: Company/Contact sync via `res.partner`, `cr_number` join to existing 141,221-company dataset | L |
| STORY-09-02 | `OdooAdapter`: Opportunity sync via `crm.lead`, translated (not passthrough) stage semantics | M |
| STORY-09-03 | `OdooAdapter`: `InteractionNote`/`TimelineEvent` extension via `mail.message`, PII-scrubbed before RAG | L |
| STORY-09-04 | `OBJ-019 SupportTicket` via `helpdesk.ticket` | M |
| STORY-09-05 | `OBJ-020 TaskCaseExtension` via `project.task` Studio fields (financing/insurance), modeled as a Value Object on existing `Task`, not a standalone aggregate | L |
| STORY-09-06 | `OBJ-021 CustomerInvoice` via `account.move` (kept distinct from `OBJ-303`/`PlatformBillingInvoice`) | M |
| STORY-09-07 | Incremental sync via `write_date` cursor; feature-flagged rollout (`feature_odoo_integration`) | M |

**Technical Tasks:** XML-RPC client with backoff/circuit-breaker (observed real timeouts on large `fields_get`/`ir.model` calls per the ARB's session evidence); `crm.team` → Territory Management data population; "unlinked record" visible badge for Golden-Record-match failures (per the ARB's flagged silent-skip risk) rather than silent exclusion.

**Infrastructure Tasks:** Sandboxed/mocked Odoo instance for CI contract testing (explicitly closes the gap the original ARB itself missed, per `ARB_META_REVIEW.md` §9).

**Security Tasks:** Odoo API user reviewed for least-privilege (dedicated integration user); PII scrubbing verified against real production note samples (phone numbers, names) before any RAG ingestion.

**Documentation Tasks:** `AI-PR-010 "Interaction Note Risk/Sentiment Analysis"` prompt registered and documented in the Prompt Registry.

**QA Tasks:** Load test against the real observed scale (27,264 CRM records); 3 injected-failure scenarios (field disappears, timeout, malformed record) each produce a loud alert, not a silent data gap.

**Deployment Tasks:** Feature-flagged rollout to Muhide first (the real tenant), monitored for 14 days before considered GA-certified per `PRODUCT_ROADMAP.md` Phase 2 exit criteria.

**Definition of Done:** All 4 new objects (SupportTicket, TaskCaseExtension, CustomerInvoice, TimelineEvent-extension) live and populated from real Odoo data for Muhide; 14 consecutive days of scheduled sync with zero unresolved P0 sync failures; zero Odoo-specific code exists outside `OdooAdapter`.

---

## EPIC-10 — Tenant Studio Core

**Phase:** 3 · **Complexity:** XL · **Dependencies:** EPIC-06 (entitlement-gated Studio modules), EPIC-08 (Integrations Studio pattern reused)

**Business Goal:** Prove the "configuration compiler, not a second runtime" principle across multiple domains at once (not just Integrations) — this is what makes SalesOS scale as a product instead of a services-heavy customization business.

**Capabilities:** CAP-082 (Custom Objects/Fields), CAP-083 (Workflow Builder), CAP-085 (Scoring Rules), CAP-087 (Territories config), CAP-092 (Branding), CAP-093 (Notification Rules), extends CAP-003 (Permissions)

| Story | Description | Complexity |
|---|---|---|
| STORY-10-01 | Custom Object/Field definition mechanism (JSONB-column-based, versioned schema, collision-checked against reserved columns) | L |
| STORY-10-02 | Custom fields render automatically in existing Company/Contact/Opportunity UI without per-field frontend code | L |
| STORY-10-03 | Workflow Builder no-code canvas → existing Workflow Engine execution model (no second interpreter) | XL |
| STORY-10-04 | Scoring Rules Studio (deterministic/rule-based, pluggable into existing NBA/Decision Center paths) | L |
| STORY-10-05 | Territory rule configuration UI over existing `CAP-017` | M |
| STORY-10-06 | Permissions UI: tenant-custom roles, capped at the tenant's own plan entitlement ceiling | M |
| STORY-10-07 | Branding & Languages (logo, color, tenant display name, i18n beyond existing Arabic/English default) | M |
| STORY-10-08 | Notification Rules configuration | M |

**Technical Tasks:** Schema-collision validation at custom-field definition time (reject any name shadowing a reserved system column); Workflow Builder canvas-to-execution-graph compiler with an equivalence test harness; scoring-rule evaluation engine with a fallback to platform-default scoring if a tenant rule errors (fail-safe, not fail-open into a broken state).

**Infrastructure Tasks:** None new — additive schema/application layer on existing Postgres.

**Security Tasks:** Privilege-escalation test: a tenant-defined custom role must never exceed the ceiling of the tenant's own plan entitlements (direct integration with EPIC-06).

**Documentation Tasks:** Tenant-facing Studio help documentation (this is customer-facing, not just internal — flagged for Customer Success review before Partner Beta).

**QA Tasks:** Multi-tenant concurrent custom-field-definition test (5 tenants defining conflicting-looking fields simultaneously, confirm isolation); Workflow Builder equivalence test suite (no-code-built workflow produces identical results to the hand-coded equivalent).

**Deployment Tasks:** Each Studio module ships independently and feature-flagged — Custom Objects/Fields first (highest leverage), Workflow Builder last (highest complexity).

**Definition of Done:** A tenant admin can add a custom field, build a workflow, define a scoring rule, and set branding — each without an engineering ticket; zero schema-collision incidents in the 5-tenant concurrency test.

---

## EPIC-11 — GTM Intelligence Engine

**Phase:** 4 · **Complexity:** XL · **Dependencies:** EPIC-08 (provider connectors), EPIC-10 (ICP/Persona Studio config surface)

**Business Goal:** Nativize the iSkala-carousel GTM concepts as governed, cross-connected SalesOS capabilities instead of 8 disconnected vendor subscriptions — and, critically, certify the **second connector** here to prove the Integration Hub is genuinely generic (see EPIC-08's stated goal and `MASTER_EXECUTION_PLAN.md` R-02).

**Capabilities:** CAP-095 (ICP Engine), CAP-096 (Market Sizing), CAP-097 (Lead Discovery), CAP-098 (Lookalikes), CAP-099 (Enrichment Waterfall), CAP-100 (Verification), CAP-101 (Website Intelligence), CAP-103 (AI Outreach), CAP-104 (Sequencing)

| Story | Description | Complexity |
|---|---|---|
| STORY-11-01 | ICP Engine: versioned, reusable `ICPProfile` object (not a one-off prompt) | M |
| STORY-11-02 | TAM/SAM/SOM computed against the platform's own 141,221-company government dataset | M |
| STORY-11-03 | Lead Discovery: government-data-first sourcing, external-provider fallback via Integration Hub | L |
| STORY-11-04 | Lookalike Accounts: trained on tenant's own won/lost Opportunity history | L |
| STORY-11-05 | Enrichment Waterfall: native multi-provider orchestration, swappable providers | L |
| STORY-11-06 | Contact Verification: commodity capability, single connector interface | S |
| STORY-11-07 | Website Intelligence: reuses existing LLM spend (no separate per-row vendor tool) | M |
| STORY-11-08 | AI Outreach: routed through existing governed Prompt Registry | M |
| STORY-11-09 | Sequencing Engine: channel-agnostic (email + LinkedIn-via-compliant-API + WhatsApp), bound to existing Activity/Task objects | L |
| STORY-11-10 | **Second connector certification** (SAP or HubSpot, decided at Sprint 16 kickoff), built by an engineer who did not build `OdooAdapter` | XL |

**Technical Tasks:** ICP scoring model backtested against real historical won/lost data; Enrichment Waterfall provider-priority/fallback logic; Sequencing Engine state machine bound to existing `Activity`/`Task` (no parallel data model); second-connector adapter built strictly from the EPIC-08 published interface docs (process validation).

**Infrastructure Tasks:** None new beyond what EPIC-08 already provisioned.

**Security Tasks:** LinkedIn channel implemented only via a compliant partner API — explicit ToS-risk avoidance, per the iSkala report's own warning; enrichment/verification provider credentials follow the same `ExternalSystemConnection` encryption pattern, no "just an API key" exception.

**Documentation Tasks:** ICP backtest report (accuracy/precision, not assumed) reviewed by CPO before Partner Beta.

**QA Tasks:** Second-connector certification test suite — identical to the one Odoo passed, run independently, by a different engineer, to prove the framework is actually learnable and generic.

**Deployment Tasks:** Feature-flagged per capability; second connector ships to at least one pilot tenant in production before Phase 4 exit.

**Definition of Done:** ICP/TAM-SAM-SOM live for at least one tenant with a reviewed backtest; Enrichment/Verification/Sequencing live end-to-end; **second connector certified and syncing in production for 14+ days with zero P0 sync failures** — this last item is a hard gate, not a nice-to-have (directly closes R-02).

---

## EPIC-12 — AI Studio

**Phase:** 5 · **Complexity:** L · **Dependencies:** EPIC-10 (Studio pattern), EPIC-06 (per-plan model tier entitlement)

**Business Goal:** Make "your own prompts, your own AI memory, your own guardrail policy" real and self-service, closing the loop opened by EPIC-06's token-ceiling scaffolding.

**Capabilities:** CAP-089 (Prompt Library), CAP-091 (AI Policies/Memory/Guardrails)

| Story | Description | Complexity |
|---|---|---|
| STORY-12-01 | Tenant-facing Prompt Library CRUD + versioning (extends existing `CAP-023`) | M |
| STORY-12-02 | AI Policies UI: data-class-to-model-tier rules (extends existing `AI-GR-*` guardrails, not reinvented) | M |
| STORY-12-03 | AI Memory MVP: conversation-level only (explicitly not cross-session long-term memory — deferred), tenant-scoped, encrypted, explicit retention/deletion policy | L |
| STORY-12-04 | Per-plan model tier selection (Starter: smaller/cheaper tier default; Enterprise: full tier access) | M |

**Technical Tasks:** Prompt versioning with rollback (a tenant can revert to a prior prompt version); AI Memory storage with a hard per-tenant encryption boundary, tested against shared-provider-cache leakage specifically (not just DB-level isolation).

**Infrastructure Tasks:** None new beyond existing DOM-012 primitives.

**Security Tasks:** Adversarial AI Memory isolation test: attempt to retrieve tenant A's memory context from a tenant B session, including via any model-provider-level prompt caching.

**Documentation Tasks:** AI Memory retention/deletion policy documented and linked from the tenant-facing Studio UI (not just an internal doc — this is customer-visible per data-handling transparency expectations).

**QA Tasks:** AI Memory adversarial isolation suite as a permanent regression (not one-time).

**Deployment Tasks:** AI Memory ships behind a flag, opt-in per tenant initially (not default-on) given it's the first implementation of a previously-❌ capability.

**Definition of Done:** Tenant-facing Prompt Library live with ≥1 active tenant customization; AI Memory MVP live with zero cross-tenant leakage findings in the adversarial suite.

---

## EPIC-13 — Marketplace & Connector Certification

**Phase:** 5 · **Complexity:** L · **Dependencies:** EPIC-08, EPIC-09, EPIC-11 (needs ≥2 certified connectors to have something real to list)

**Business Goal:** Prove the ecosystem mechanism — that a connector/playbook/prompt-pack can be certified and published through a repeatable pipeline — before promising it commercially at GA.

**Capabilities:** CAP-071/072 (Marketplace, Owner side), CAP-094 (Certification Pipeline)

| Story | Description | Complexity |
|---|---|---|
| STORY-13-01 | `MarketplaceListing` object (single object across connector/app/playbook types) | M |
| STORY-13-02 | Certification pipeline: automated contract testing (`SourceConnector` conformance) + security review checklist + sandboxed trial | L |
| STORY-13-03 | Marketplace browse/install UI (`/marketplace`, superseding the `CAP-036` stub) | M |
| STORY-13-04 | Publish ≥3 first-party connector listings, ≥1 first-party playbook listing | M |

**Technical Tasks:** Automated conformance test runner (reuses EPIC-08's contract test suite); sandboxed trial environment (install a listing into an isolated test tenant, verify no side effects on real tenants).

**Infrastructure Tasks:** Listing versioning and rollback (a bad listing update must be revertible without breaking tenants who already installed it).

**Security Tasks:** Every listing (even first-party) goes through the same security review checklist — no first-party exception, since the pipeline itself needs to be proven before any third party ever uses it.

**Documentation Tasks:** Certification pipeline documented as the process third parties will eventually follow post-GA (written now even though no external party uses it yet — per `MASTER_EXECUTION_PLAN.md` R-07, third-party publishing is explicitly Phase 7+/post-GA).

**QA Tasks:** Certification pipeline negative test: submit an intentionally broken listing, confirm the pipeline rejects it (not just a happy-path test).

**Deployment Tasks:** Marketplace ships with first-party-only content through GA — no external submission form exposed yet.

**Definition of Done:** ≥3 connector + ≥1 playbook listings live and installable; certification pipeline correctly rejects the intentional negative test case.

---

## EPIC-14 — Production Hardening, Compliance & DR

**Phase:** 6 · **Complexity:** XL · **Dependencies:** EPIC-01 through EPIC-13 (feature-complete system required to test against)

**Business Goal:** Prove the system holds under real load, real failure, and real external scrutiny before GA — the difference between "worked in Partner Beta" and "safe to sell broadly."

**Capabilities:** None new — this epic validates, it does not add.

| Story | Description | Complexity |
|---|---|---|
| STORY-14-01 | Load test: 50 concurrent simulated tenants at pooled-tier scale | L |
| STORY-14-02 | Chaos test: connector outage, AI provider outage, database failover injection | L |
| STORY-14-03 | Full backup/restore DR drill, RTO/RPO measured | M |
| STORY-14-04 | External penetration test (or dedicated internal red-team exercise) | L |
| STORY-14-05 | SOC2 Type I evidence collection (audit logging, access review, change management) | L |
| STORY-14-06 | AI provider failover implementation and drill | M |
| STORY-14-07 | LLM regression test suite (detect silent quality degradation on model updates) | M |

**Technical Tasks:** Performance profiling/optimization on any SLO-missing endpoint found under load; AI provider failover routing logic with defined SLO for failover time.

**Infrastructure Tasks:** Load/chaos testing tooling provisioned (e.g., k6/Locust for load, custom fault-injection harness for chaos); DR drill executed against a real (non-production) restore target, timed.

**Security Tasks:** Full pentest — first *external* validation in the entire plan; every finding triaged and either fixed or explicitly risk-accepted with CTO sign-off before GA.

**Documentation Tasks:** Written postmortem for every drill (even ones with no "failure") — practice postmortems, not just incident postmortems, per `MASTER_EXECUTION_PLAN.md` principle 8 (reversibility discipline).

**QA Tasks:** All of the above drills *are* the QA tasks for this epic — there is no separate QA phase after them.

**Deployment Tasks:** None — this epic is entirely pre-production validation, explicitly non-overlapping with active feature development (per `PRODUCT_ROADMAP.md` Phase 6 objectives).

**Definition of Done:** Load test SLOs held at 50-tenant scale (or documented remediation plan); zero unresolved pentest criticals; DR drill RTO/RPO measured and within target; AI provider failover tested and within SLO.
