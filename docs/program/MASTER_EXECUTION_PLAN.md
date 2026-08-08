# Master Execution Plan — SalesOS to Commercial SaaS GA

> **Status:** Approved planning baseline (pending CTO/CPO sign-off per §16.2 of `CANONICAL_ARCHITECTURE.md`)
> **Supersedes:** Nothing — this is the execution layer sitting *underneath* `CANONICAL_ARCHITECTURE.md` (what exists) and `SAAS_PLATFORM_ARCHITECTURE.md` (what the target shape is). This document answers: **in what order, by whom, by when, and how do we know we're done.**
> **Companion documents:** `PRODUCT_ROADMAP.md`, `PROGRAM_PLAN.md`, `ENGINEERING_ROADMAP.md` (+ `SPRINT_PLAN/`), `RELEASE_PLAN.md`, `PRODUCTION_READINESS_CHECKLIST.md`, `TEST_STRATEGY.md`, `OPERATIONS_MANUAL.md`, `COMMERCIAL_LAUNCH_PLAN.md`, `IMPLEMENTATION_SEQUENCE.md`, `RISK_REGISTER.md`, `DECISION_LOG.md`, `MILESTONES.md`
> **Baseline date:** 2026-07-30 · **Target GA date:** 2027-08-02 (Sprint 26 close, 52 weeks from baseline)
> **Reference commit:** `6f75e8d` (the same commit `CANONICAL_ARCHITECTURE.md` was validated against)

---

## 1. Current State

Verified against executable code as of `6f75e8d`, not aspiration:

| Dimension | Current state | Source |
|---|---|---|
| **Tenancy model** | Single production tenant (Muhide), `tenant_id` present on 72/77 tables, but no billing, no plan entitlement, no Owner Platform, no self-service provisioning | `CANONICAL_ARCHITECTURE.md` §17.2 |
| **Production readiness** | **NO-GO** (per `GA_STATUS.md`, same-day audit) | Referenced in `SalesOS_Odoo_Enterprise_Integration_Assessment.md` §Executive Snapshot |
| **Security posture** | 3 unresolved P0s: Decision Center cross-tenant IDOR, Webhook SSRF (`app/routers/workflows.py:493`), CSRF bypass via `X-API-Key` (`app/common/csrf.py`) | `CANONICAL_ARCHITECTURE.md` §14 |
| **Data layer maturity** | 45 Postgres-backed repos (production-grade), 35 InMemory-only repos (no production path) — includes Revenue Territory/Quota/Forecast, Signal Marketplace, Decision Context | `CANONICAL_ARCHITECTURE.md` §17.1 |
| **Event-driven adoption** | Grade D — 5 of ~60 modules actually emit/subscribe; Kafka defaults to `in_memory` | `CANONICAL_ARCHITECTURE.md` §13, §17 |
| **Graph layer** | Neo4j provisioned, zero data | `CANONICAL_ARCHITECTURE.md` §13 |
| **Test coverage** | Grade D — 13.8% test-to-source ratio (277 test files / 2,009 source files); 25 of 31 runtime engines have zero dedicated tests | `CANONICAL_ARCHITECTURE.md` §14, §17 |
| **Frontend build** | Currently fails (TypeScript + ESLint errors) | `CANONICAL_ARCHITECTURE.md` §14 |
| **Schema drift** | Alembic 5 revisions behind models | `CANONICAL_ARCHITECTURE.md` §14 |
| **AI agent honesty** | 11 of 11 AI agents return mock/hardcoded data in production paths (per internal remediation backlog) | `SalesOS_Odoo_Enterprise_Integration_Assessment.md` §1.2 |
| **Integration layer** | `connectors.py` is a stub returning `mock_data.get(connector_id, [])`; zero live external system connections | `SalesOS_Odoo_Enterprise_Integration_Assessment.md` §1.2 |
| **Multi-tenant commercial layer** | Does not exist: no `Subscription`, no `Plan.entitlements`, no Owner Platform shell, no Integration Hub, no Tenant Studio, no Marketplace beyond a `plugins` stub | `SAAS_PLATFORM_ARCHITECTURE.md` §0 |
| **Team** | 5-7 engineers (per `ARB_REVIEW_ODOO_INTEGRATION.md` §7 sizing assumption), no dedicated Security, SRE, QA, Customer Success, or Sales function yet | Inferred from repo/org evidence |
| **Commercial infrastructure** | None — no billing integration, no pricing, no marketplace revenue share, no support tiering | New scope, this document |

**Blunt summary:** SalesOS today is a well-architected single-tenant product with real security debt, real test debt, and zero commercial-platform infrastructure. It is not 20% away from GA — it is a different *kind* of system away from GA. This plan does not pretend otherwise.

---

## 2. Target State (at GA, Sprint 26)

| Dimension | Target |
|---|---|
| **Tenancy** | N tenants live on pooled multi-tenant infrastructure with RLS enforcement, Owner Platform provisioning them self-service or via sales-assisted onboarding |
| **Security** | Zero unresolved P0/P1 findings; SOC2 Type I evidence collection in progress; penetration test passed with no criticals |
| **Commercial layer** | Subscription + billing (Stripe) live; 3 published plans (Starter/Growth/Enterprise); entitlement engine gating DOM/CAP access per plan |
| **Integration Hub** | Generic `SourceConnector` framework live; Odoo adapter GA-certified; ≥2 additional connectors in the certification pipeline (SAP or HubSpot, plus generic REST/CSV) |
| **Tenant Studio** | Workflow Builder, Scoring Rules, Custom Objects/Fields, Branding, Permissions all self-service, no-code |
| **GTM Intelligence** | ICP Engine, Lead Discovery, Enrichment Waterfall, Sequencing Engine live and native (no iSkala-stack vendor dependency for MVP) |
| **AI Studio** | Tenant-facing Prompt Library, Guardrails policy UI, AI Memory MVP — 11/11 agents running on real tenant data, zero mock paths in production |
| **Testing** | ≥65% test-to-source ratio on all Phase 0-6 code; 100% of new code carries unit + integration tests as a merge gate |
| **Marketplace** | Certification pipeline live; ≥3 first-party connectors, ≥2 first-party playbooks published |
| **Commercial readiness** | Pricing published, sales process defined, ≥5 paying pilot customers converted from Partner Beta before GA |

---

## 3. Guiding Principles

1. **Security and tenant isolation are prerequisites, not milestones.** No commercial feature ships on top of an unresolved cross-tenant data leak. Phase 0 is non-negotiable and blocks all subsequent phases (see `IMPLEMENTATION_SEQUENCE.md`).
2. **Configuration over code, everywhere a tenant touches the system.** Every Tenant Studio capability is a config compiler over an existing runtime, never a per-tenant code fork — this is the same lesson the Odoo ARB already forced onto the Integration Hub design (`ARB_REVIEW_ODOO_INTEGRATION.md` §8), generalized as a platform-wide rule.
3. **One adapter, one interface, no bespoke connectors.** Every new external system integration implements `SourceConnector` — there is no "special case" integration path, ever, starting with Odoo.
4. **Entitlements layer over feature flags, never replacing them.** Commercial packaging (what a plan unlocks) and technical rollout (canary/kill-switch) stay two independent mechanisms, per `SAAS_PLATFORM_ARCHITECTURE.md` §15.
5. **Ship to real tenants early, not just internally.** Private Alpha includes at least one real external design partner by Sprint 11 — internal-only validation systematically under-catches multi-tenant bugs.
6. **No phase exit without a Go/No-Go gate reviewed by the full leadership group** (CPO, CTO, Chief Architect, Program Director, Release Manager) — defined per-phase in `PRODUCT_ROADMAP.md`.
7. **Every capability traces to a business reason.** No engineering work enters `PROGRAM_PLAN.md` without a named business goal it serves — this plan explicitly rejects "build it because it's good architecture" as sufficient justification on its own.
8. **Reversibility discipline.** Every migration, every schema change, every connector write-back path has a documented rollback before it ships — codified per-feature in `PRODUCTION_READINESS_CHECKLIST.md` and per-incident in `OPERATIONS_MANUAL.md`.
9. **Defer what the Rule of Three says to defer.** Sharding-by-tenant-cohort, a fourth/fifth connector's edge cases, and event-sourcing platform-wide are explicitly out of scope through GA — flagged, not silently dropped (`SAAS_PLATFORM_ARCHITECTURE.md` §18).

---

## 4. Assumptions

| # | Assumption | Impact if wrong |
|---|---|---|
| A1 | Current engineering headcount (5-7) grows to ~12-14 by Sprint 12 (Backend ×2, Frontend ×1, AI/ML ×1, DevOps/SRE ×1, QA ×1, Security ×1 part-time→full-time) | Roadmap timeline in §2 slips proportionally; `PROGRAM_PLAN.md` complexity estimates assume this headcount curve |
| A2 | Muhide (the existing tenant) continues as the first production tenant and first design partner for Private Alpha | If Muhide's own Odoo integration timeline (per `ODOO_INTEGRATION_BLUEPRINT.md` roadmap) slips, Phase 2 slips with it |
| A3 | Stripe (or equivalent) is the billing provider — no in-house payment processing is built | Any alternate provider choice re-scopes EPIC-05 integration tasks, not the epic itself |
| A4 | Odoo remains the reference/first connector; a second connector (SAP or HubSpot) is scoped no later than Sprint 16 to validate the framework generality claim before GA | Skipping this means the Integration Hub's "generic" claim ships unverified — a direct repeat of the original Odoo Blueprint's single-vendor risk |
| A5 | Regulatory scope at GA is Saudi/GCC (PDPL-aligned), not full SOC2 Type II or GDPR — those are explicitly post-GA hardening, tracked as backlog, not blockers | If an early Enterprise prospect requires SOC2 Type II pre-contract, Phase 6 scope grows and GA date slips |
| A6 | Pooled multi-tenant Postgres (RLS-isolated) is sufficient through GA scale (target: dozens of tenants, not thousands) | If an early Enterprise deal requires dedicated-tenant isolation before Sprint 20, the siloed-tier work (`SAAS_PLATFORM_ARCHITECTURE.md` §13) pulls forward |
| A7 | No sibling product (AuditOS, DecisionOS, LocalContentOS) needs Owner Platform support before this plan's GA | Owner Platform is scoped for one product family only through GA; multi-product support is explicitly Phase 7+ (post-GA) |

---

## 5. Constraints

| # | Constraint | Source |
|---|---|---|
| C1 | Odoo is hosted on odoo.com SaaS — no custom server-side module deployment, no CDC/logical replication access; XML-RPC is the only viable mechanism | `ARB_REVIEW_ODOO_INTEGRATION.md` §6 |
| C2 | Webhook-based integrations (any connector, not just Odoo) are blocked platform-wide until the SSRF (`workflows.py:493`) and CSRF (`csrf.py`) P0s close — this is now a **launch blocker for the entire Integration Hub**, not an Odoo footnote | `SAAS_PLATFORM_ARCHITECTURE.md` §12 |
| C3 | Kafka is not production-proven anywhere in the codebase (Grade D adoption) — no phase through GA may introduce a hard dependency on Kafka for a critical path; Outbox-pattern-via-Postgres is the only durable event mechanism allowed pre-GA | `CANONICAL_ARCHITECTURE.md` §13, `ARB_REVIEW_ODOO_INTEGRATION.md` §6 |
| C4 | Neo4j has zero production data — no phase may make a user-facing feature *depend* on Neo4j being populated; graph population is additive/best-effort only through GA | `CANONICAL_ARCHITECTURE.md` §13 |
| C5 | Canonical IDs (DOM-*, CAP-*, OBJ-*) are immutable once assigned (`CANONICAL_ARCHITECTURE.md` §16.2) — every new feature in this plan must be traceable to an ID already reserved in `SAAS_PLATFORM_ARCHITECTURE.md`, not invented ad hoc during a sprint | Governance constraint |
| C6 | Widget SDK v1 is frozen (ADR-003) — no phase may silently reorder or reinterpret an existing widget; any such change requires its own ADR (e.g., the pending `ADR-037` for Employee 360 widget reordering) | `ARB_REVIEW_ODOO_INTEGRATION.md` §12 |
| C7 | Budget: no external financing event assumed inside this 52-week window — headcount growth (A1) must be affordable from existing runway; if not, `PROGRAM_PLAN.md` complexity estimates get re-sequenced, not silently compressed | Business constraint |

---

## 6. Dependencies

| Dependency | Depends on | Blocks |
|---|---|---|
| Owner Platform (EPIC-04–07) | Tenant isolation hardening (EPIC-02) being complete | All commercial motion — cannot bill/provision tenants safely until isolation is provably correct |
| Integration Hub GA (EPIC-08–09) | Webhook SSRF/CSRF closure (EPIC-01) for the webhook adapter path; XML-RPC path (Odoo) is unblocked earlier | Marketplace connector certification (EPIC-13) |
| Tenant Studio (EPIC-10) | Entitlement Engine (EPIC-06) — Studio modules must be gate-able per plan from day one, not retrofitted | GTM Intelligence Studio surface (EPIC-11's `/studio/gtm`) |
| GTM Intelligence (EPIC-11) | Integration Hub (for enrichment provider connectors) and Tenant Studio (for ICP/persona config) | Public Beta feature completeness |
| Marketplace (EPIC-13) | Integration Hub GA + Tenant Studio + at least one certified second-party connector to prove the certification pipeline against something other than Odoo | Commercial Launch Plan's marketplace revenue-share motion |
| Commercial Launch (pricing, sales, support) | Entitlement Engine + Billing (EPIC-05, 06) fully live | Public Beta → RC transition |
| SOC2/Compliance evidence (EPIC-14) | Security P0/P1 closure (EPIC-01) + audit logging completeness | Any Enterprise-tier sales conversation requiring compliance evidence |

---

## 7. Critical Risks

> **Canonical, kept-current version:** [`RISK_REGISTER.md`](RISK_REGISTER.md) — includes live status (Open/Mitigating/Monitoring/Closed) and scoring. The table below is the risk view as understood at plan baseline; update the register, not this table, as statuses change.

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Cross-tenant IDOR-class bug recurs in a new commercial-layer table (Subscription, UsageMeter) the way it did in Decision Center | Medium | Critical | Mandatory cross-tenant regression test as a merge gate on every PR touching a tenant-scoped table (carried forward from `ARB_REVIEW_ODOO_INTEGRATION.md` §16); RLS enforced at the DB layer, not just application code | Security Eng / CTO |
| R-02 | Odoo remains the only proven connector at GA, silently invalidating the Integration Hub's "generic framework" claim | Medium | High | A2/A4 mitigation: second connector scoped no later than Sprint 16, tracked as an explicit go/no-go gate in `PRODUCT_ROADMAP.md` Phase 4 | Chief Architect |
| R-03 | Team headcount growth (A1) doesn't materialize on schedule | Medium | High | `ENGINEERING_ROADMAP.md` sprint scope is explicitly re-sequenced (not silently slipped) at each Phase gate if headcount lags — Phase 4/5 scope is the flex point, Phase 0-2 is not | Program Director |
| R-04 | Test debt (Grade D, 13.8%) is carried forward instead of paid down, and commercial-layer code ships with the same thin coverage | High if unmanaged | High | Coverage gate enforced in CI starting Sprint 1 (new code only, not retroactive to avoid stalling everything) — see `TEST_STRATEGY.md` §Coverage Gates | QA Lead |
| R-05 | Billing integration (Stripe) edge cases (proration, dunning, failed payment retries) under-tested, causing revenue leakage or wrongful suspension | Medium | High | Dedicated EPIC-05 QA pass with a documented test matrix for every subscription-state transition before Partner Beta | Backend Lead |
| R-06 | AI cost overrun once tenant-facing AI Studio and GTM Intelligence (LLM-heavy) go live without per-plan token ceilings enforced | Medium | Medium | `CAP-070`/`CAP-077` token-ceiling enforcement ships in Phase 1, not deferred to Phase 5 alongside AI Studio itself | AI/ML Lead |
| R-07 | Marketplace certification pipeline becomes a bottleneck (manual review queue) once external parties want to publish | Low pre-GA (no 3rd parties yet), High post-GA | Medium | Explicitly scoped as first-party-only through GA; 3rd-party publishing is Phase 7+ backlog, not promised at GA | CPO |
| R-08 | Frontend build failure (existing, documented gap) blocks CI entirely once more frontend work lands on top of it | High if not fixed immediately | High | Fixed in Sprint 1, Phase 0, before any other frontend work is scheduled — see `IMPLEMENTATION_SEQUENCE.md` position 1 | Frontend Lead |
| R-09 | Alembic drift (5 revisions behind) causes a migration collision once commercial-layer tables are added | High if not fixed immediately | High | Migration catch-up is a Sprint 1 task, gating all subsequent schema work | Backend Lead |
| R-10 | Odoo write-back feedback loop (SalesOS writes an AI score back to Odoo, then re-reads it as if fresh) corrupts a risk model | Low | Medium | `ConflictResolutionPolicy` (OBJ-333) explicitly excludes SalesOS-authored fields from reverse-mapping, enforced in `FieldMappingConfig`, not developer memory — carried forward from `ARB_REVIEW_ODOO_INTEGRATION.md` §9 | Backend Lead |

---

## 8. Success Criteria (Program-Level)

| Criterion | Target | Measured how |
|---|---|---|
| Zero unresolved Security P0/P1 | 0 | Security scan + manual pentest sign-off, tracked in `PRODUCTION_READINESS_CHECKLIST.md` |
| Tenant isolation regression suite | 100% pass, run on every PR touching tenant-scoped tables | CI gate, `TEST_STRATEGY.md` §Tenant Isolation |
| Paying pilot tenants before GA | ≥5, converted from Partner Beta | Subscription table (OBJ-321) count with `status=active` |
| Connector count at GA | ≥2 certified (Odoo + 1 more) | Marketplace listing count with `status=certified` |
| Test-to-source ratio (new code, Phase 0 onward) | ≥65% | CI coverage report |
| AI agent mock-data elimination | 11/11 agents on real data paths | Manual audit against remediation backlog |
| Time-to-provision a new tenant | <10 minutes, self-service | Owner Platform telemetry (CAP-073) |
| Uptime during Public Beta → GA window | ≥99.5% | Platform Health Snapshot (OBJ-327) |
| Support SLA adherence (Partner Beta onward) | ≥95% of tickets within committed response time | Support Console (CAP-075) reporting |

---

## 9. Exit Criteria (Program Complete / GA Declared)

GA is declared only when **all** of the following hold simultaneously — this is an AND, not an OR:

1. `PRODUCTION_READINESS_CHECKLIST.md` shows 100% of "Mandatory for GA" items checked (partial credit does not count).
2. Zero open Security P0/P1 findings; most recent penetration test (within 60 days of GA) shows no unresolved criticals.
3. `RELEASE_PLAN.md`'s Release Candidate exit criteria have held for a minimum 2-week soak with no P0/P1 regressions.
4. At least 5 tenants are on a paid plan (`Subscription.status = active`) with at least 30 days of continuous production usage each.
5. Entitlement Engine (CAP-070) correctly gates all 3 published plans against a documented test matrix — no entitlement bypass found in the Phase 6 security review.
6. At least 2 connectors (Odoo + one other) are certified and have each completed at least one real tenant's incremental sync cycle in production for 14+ consecutive days without a P0 sync failure.
7. Operations runbooks (`OPERATIONS_MANUAL.md`) have each been exercised at least once in a game-day/DR drill (not just written) — tracked per-runbook.
8. Commercial infrastructure live: pricing published, billing integration processing real invoices, support tier defined and staffed.
9. `MASTER_EXECUTION_PLAN.md` §8 Success Criteria table shows every metric at or above target for 2 consecutive reporting periods (bi-weekly).

If any criterion is unmet, GA does not slip by default — the Release Manager convenes a Go/No-Go review (per `RELEASE_PLAN.md` gate structure) to decide between (a) a scoped GA with the unmet item explicitly named as a known limitation, or (b) a defined extension with a new date. **Silent slippage without a named reason is not an acceptable outcome under this plan.**
