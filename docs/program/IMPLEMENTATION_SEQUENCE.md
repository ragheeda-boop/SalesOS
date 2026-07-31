# Implementation Sequence — What Gets Built First, and Why

> **This is the load-bearing document.** Every other document in this set (`MASTER_EXECUTION_PLAN.md`, `PRODUCT_ROADMAP.md`, `PROGRAM_PLAN.md`, `ENGINEERING_ROADMAP.md`) describes *what* and *when*. This document is the only one that argues, capability by capability, **why that order and not another** — and names the project-management scaffolding (RACI, gates, risk matrix) that enforces the order actually holds.

---

## 1. The Build Order, With Justification

Strict sequence. "Nothing parallel unless justified" — every row below either states an explicit justification for running alongside its neighbor, or is understood to be strictly sequential.

| Order | Capability | Why now | Why not later | Why not earlier | Dependencies | Risk if skipped/reordered | Effort | Business value |
|---|---|---|---|---|---|---|---|---|
| 1 | **Security P0 remediation** (IDOR, SSRF, CSRF) | These are live, exploitable vulnerabilities today — every day of delay is a day of live exposure | N/A — cannot be later, it's already overdue | N/A — this is position 1 | None | **Critical.** A commercial platform launched on top of a known cross-tenant leak is an existential/reputational risk, not a technical debt item | L (6 person-weeks) | Removes the single largest blocker to selling to anyone beyond Muhide |
| 2 | **Tenant isolation hardening (RLS)** | Must exist before any new tenant-adjacent commercial table (Subscription, UsageMeter) is created, or those new tables inherit the same class of risk from day one | Cannot be later — every subsequent phase adds tenant-scoped tables | Blocked on nothing, but sequenced right after security fixes because it shares the same regression-test infrastructure (STORY-01-04) | Security P0 remediation (shared tooling) | High — retrofitting RLS onto tables that already have production data and established access patterns is materially harder than building it in from table #1 | XL (2 person-weeks × 2 engineers) | Makes "hundreds of tenants" a safe claim instead of a hopeful one |
| 3 | **CI/CD & test foundation** (build fix, Alembic catch-up, coverage gate) | Runs in parallel with #1/#2 — **justified parallel track**: different engineers, no shared code paths (frontend build fix and backend security fixes don't touch the same files), and both must be done before Phase 1 starts regardless of order between them | N/A | N/A | None | High — every subsequent phase's velocity is throttled by a red or flaky CI | M (4 person-weeks) | Removes silent, compounding drag on every future sprint |
| 4 | **Tenant Provisioning** (`Tenant` extension, provisioning workflow) | First piece of Owner Platform — nothing commercial is possible without a formal representation of "a tenant" beyond the single hardcoded Muhide row | Cannot be later — it's the root object every subsequent commercial epic (billing, entitlement) foreign-keys against | Blocked until RLS is proven (order 2) — a new commercial table must not be the one that breaks the isolation guarantee just established | RLS hardening | Medium — a shaky provisioning foundation means every tenant created on top of it inherits its bugs | M (3 person-weeks) | Unlocks "onboard tenant #2" as a real, repeatable operation |
| 5 | **Subscription & Billing** | Immediately follows provisioning — a tenant that can't be billed can't be sold | Cannot be later — Partner Beta (order ~15) requires real billing, and billing bugs take a full sprint to properly test (state machine + Stripe webhooks), so it cannot be compressed into a later phase | Blocked on Tenant Provisioning existing (needs a real `Tenant` to attach a `Subscription` to) | Tenant Provisioning | High (R-05) — billing bugs mean literal revenue leakage or wrongful customer suspension; this is the single highest financial-risk item in the entire sequence | XL (6 person-weeks) | Converts the platform from "software" to "a business" |
| 6 | **License & Entitlement Engine** | Immediately follows billing — a `Plan` without enforceable entitlements is a marketing document, not a product boundary | Cannot be later — every subsequent Studio/GTM/AI Studio module needs to be gate-able from the moment it ships, not retrofitted with a gate after tenants are already using it ungated | Blocked on Subscription/Plan existing | Subscription & Billing | High — retrofitting entitlement gates onto already-shipped, already-used capabilities is how "everyone quietly has Enterprise features on a Starter plan" bugs happen | L (3 person-weeks) | Makes the pricing model in `COMMERCIAL_LAUNCH_PLAN.md` technically real, not just contractual |
| 7 | **Owner Admin Console (MVP, read-only)** | Runs in parallel with #6 — **justified parallel track**: frontend-only work, consumes APIs that #4/#5 already expose, no shared code path with the entitlement engine's backend work | Read-write actions (manual suspend, refund) are explicitly deferred — no engineering benefit to blocking on those before Alpha | Blocked on Tenant Provisioning + Billing existing (needs data to display) | Tenant Provisioning, Billing | Low — this is an internal tool; its absence slows Platform Ops, doesn't risk tenant data | M (2 person-weeks) | Lets Platform Ops actually run the business without engineer-mediated DB queries |
| 8 | **Integration Hub framework** (`SourceConnector`, `ExternalSystemConnection`, ACL) | This is the single most important architectural bet in the whole plan — building it generically now, before Odoo-specific code exists, is the only way to avoid the exact trap the original Odoo Blueprint fell into (a single-vendor-shaped "framework") | Cannot be later than immediately before the Odoo adapter — building Odoo-specific code first and generalizing after is precisely the anti-pattern the ARB debate already rejected once | Blocked on Entitlement Engine (Integration Hub access must be plan-gated from day one) and Security P0 (webhook path specifically) | Entitlement Engine, Security P0 (webhook path) | **Critical, R-02.** If skipped and Odoo is built bespoke "just this once," every future connector re-pays the same integration cost — this is the platform's core "sell to hundreds of customers, tomorrow another tenant connects SAP" promise, made or broken right here | XL (8 person-weeks) | The technical foundation of the entire Integration Hub / Marketplace commercial story |
| 9 | **Odoo Adapter GA** | Immediately follows the framework — proves the framework against a genuinely messy real system (Studio auto-generated fields, mixed-purpose tables) while a real, willing design partner (Muhide) is available to validate against | Cannot be meaningfully earlier — needs the framework (#8) to exist first, by definition | Blocked on Integration Hub framework | Integration Hub framework | Medium — without Odoo as the proof case, the framework's genericity claim (#8) is unverified theory | XL (8 person-weeks) | Closes the single most-cited internal gap: 11/11 AI agents on mock data become 11/11 on real data |
| 10 | **Tenant Studio Core** (Custom Objects/Fields, Workflow Builder, Scoring, Territories, Permissions, Branding) | Follows Integration Hub because Integrations Studio (built as part of #8) establishes the "config compiler over an existing runtime" pattern this epic reuses across many more domains — doing Studio first would mean inventing that pattern twice | Cannot be later — self-service configuration is what lets the platform scale past an engineer-per-customization model, needed well before Public Beta's open signup | Blocked on Entitlement Engine (Studio modules gated per plan from day one) and the Integrations Studio pattern (#8) | Entitlement Engine, Integration Hub (pattern reuse) | Medium — without this, every tenant customization request becomes an engineering ticket, which does not scale past a handful of tenants | XL (8 person-weeks) | The core self-service promise of "configure without writing code" |
| 11 | **GTM Intelligence Engine + second connector** | Follows Tenant Studio because ICP/Persona configuration needs a Studio surface to live in; the second connector is deliberately placed here (not earlier, not later) because this is the first point where a second, real, non-Odoo integration need naturally arises (GTM enrichment/verification providers) — proving genericity against a real need, not an artificial one | Cannot be later — `MASTER_EXECUTION_PLAN.md` R-02 requires the second connector proven before GA, and Partner Beta (which needs GTM features to be attractive to real paying pilots) is the natural forcing function | Blocked on Integration Hub (#8) and Tenant Studio (#10, for config surface) | Integration Hub, Tenant Studio | High (R-02) if the second connector slips past this point — the framework's genericity claim would go untested until dangerously close to GA | XL (8 person-weeks) | Makes SalesOS competitive against the exact stack (Apollo/Clay/SmartLead) the iSkala report reverse-engineered, as one native system |
| 12 | **AI Studio** (tenant-facing Prompt Library, Policies, Memory MVP) | Deliberately late — AI Studio formalizes DOM-012 primitives that have existed since before this plan started; making them tenant-facing is valuable but not blocking for anything before Public Beta | Cannot be indefinitely later — Public Beta's self-service tenants expect to control their own AI behavior, and AI Memory needs real usage time before GA to catch isolation bugs | Blocked on Tenant Studio pattern (#10) and per-plan model tier entitlement (#6) | Tenant Studio, Entitlement Engine | Medium (R-06 AI cost overrun) if token-ceiling enforcement (pulled forward to #6) wasn't already in place before this ships | L (6 person-weeks) | Tenant trust and cost control over their own AI usage |
| 13 | **Marketplace & Certification Pipeline** | Deliberately last among feature work — it needs at least 2 real certified connectors (#9, #11) and a Studio pattern (#10) to have anything genuine to list; a marketplace with nothing real in it is a stub, exactly like the existing `CAP-036` | Cannot be earlier — building a certification pipeline before there's a second connector to certify against means testing the pipeline against only one shape of input, an unvalidated pipeline | Blocked on Integration Hub, Odoo adapter, second connector, Tenant Studio | Integration Hub, second connector, Tenant Studio | Low if slipped slightly — Marketplace is the ecosystem proof-of-concept, not a Partner Beta blocker | L (6 person-weeks) | Proves the platform model, not just the product model, before promising it commercially |
| 14 | **Hardening, Scale, Compliance** | Deliberately last, deliberately non-overlapping with feature work — load/chaos/pentest results are only meaningful against a feature-complete system; testing against a moving target wastes the exercise | Cannot be earlier than feature-complete | Cannot be earlier | Everything above | **Critical if skipped** — this is the difference between a Partner-Beta-validated system and a GA-ready one; skipping it is how SaaS companies have their first major incident in month one | XL (6 person-weeks) | The actual GA go/no-go evidence base |

---

## 2. Critical Path

```
Security P0 (1) → RLS (2) → Tenant Provisioning (4) → Billing (5) → Entitlement Engine (6)
   → Integration Hub Framework (8) → Odoo Adapter (9) → Tenant Studio (10)
   → GTM Intelligence + 2nd Connector (11) → Hardening/Compliance (14) → GA
```

This is the longest dependency chain and therefore sets the floor on the overall timeline — **compressing any single link compresses the whole program's minimum duration**, while adding resources to a non-critical-path item (see §3) does not shorten the program at all. Program Director's primary job through this plan is protecting this specific chain from scope creep and resourcing starvation.

## 3. Parallel Tracks (explicitly justified, not default)

| Track A (critical path) | Track B (parallel) | Why parallel is safe here |
|---|---|---|
| Security P0 remediation (backend) | CI/CD & test foundation (frontend build fix + Alembic) | Different engineers, disjoint file sets, no shared review dependency |
| Entitlement Engine (backend) | Owner Admin Console MVP (frontend) | Console consumes already-stable APIs from earlier steps; frontend work doesn't block or get blocked by entitlement backend logic |
| Odoo Adapter hardening (Sprint 11 soak) | Tenant Studio Custom Objects/Fields design (Sprint 12 kickoff prep) | Design/spec work for #10 can begin during #9's production soak window without needing #9 to be "done," since the soak is monitoring, not active development |
| AI Studio (Phase 5) | Marketplace object model + certification pipeline scaffolding (Phase 5) | Different subsystems, different engineers per `PROGRAM_PLAN.md` EPIC-12/13 owner assignments, both consume already-stable Phase 2/4 outputs |

**Everything not listed above as an explicit parallel track is sequential.** In particular: Integration Hub framework and Odoo Adapter are **not** parallelized (building Odoo-specific code before the framework interface is finalized is the exact anti-pattern this plan rejects), and Tenant Studio and GTM Intelligence are **not** parallelized (GTM's Studio surface needs Tenant Studio's pattern to exist first).

## 4. Blocked Work (named explicitly, not silently dropped)

| Item | Blocked by | Unblocks when |
|---|---|---|
| Self-service tenant signup UI | Entitlement Engine + Billing production-mode | Phase 5 (sales-assisted provisioning is the Phase 1-4 substitute) |
| Third-party Marketplace submissions | A proven certification pipeline against first-party listings | Post-GA (explicitly, per `PRODUCTION_READINESS_CHECKLIST.md`) |
| Siloed/dedicated-tenant deployment tier | An actual Enterprise deal requiring it (no work started speculatively) | Post-GA, or pulled forward only if a signed deal forces it (named risk, `MASTER_EXECUTION_PLAN.md` A6) |
| Cross-session AI Memory | Conversation-level AI Memory MVP proving isolation safety first | Post-GA |
| Tenant sharding | Pooled-tier load test (Phase 6) actually showing strain — not built speculatively | Post-GA, only if triggered by real evidence |

## 5. Quick Wins

| Item | Why it's a quick win | Sequenced where |
|---|---|---|
| `crm.team` → Territory Management population | Real Odoo data slots directly into an existing, currently-empty (`InMemory`) capability with zero new object design | Bundled into Odoo Adapter (#9) |
| Relabeling the 4 "gap" tenant-isolation tables as correctly Owner-scoped | Resolves a documented inconsistency in `CANONICAL_ARCHITECTURE.md` §17.2 for free, no code change, just registry correction | Bundled into RLS hardening (#2) |
| Branding & Languages Studio module | Lowest technical complexity of all Tenant Studio modules, highest visible "this feels like a real SaaS product" signal for early demos | Sequenced last within Tenant Studio (#10) specifically so it's fresh for Internal Beta demos |
| Website Intelligence (GTM) | Reuses already-licensed LLM spend — zero new vendor integration needed, unlike Enrichment/Verification which need provider connectors | Sequenced mid-GTM Intelligence (#11), not gated behind provider-connector work |

## 6. High-Risk Items (cross-referenced to `MASTER_EXECUTION_PLAN.md` §7)

| Risk | Sequence position where it's most acute | Mitigation timing |
|---|---|---|
| R-01 Cross-tenant IDOR recurrence | Positions 4-13 (every new tenant-scoped table) | Regression-test gate established at position 1-2, reused at every subsequent position — not a one-time fix |
| R-02 Odoo-only framework | Position 8-9 until position 11 closes it | Explicitly named as unresolved risk between positions 9 and 11 — this is a known, tracked, temporary state, not an oversight |
| R-05 Billing revenue leakage | Position 5 | Full state-machine test matrix before position 5 is considered complete, not deferred to hardening (position 14) |
| R-06 AI cost overrun | Position 6 (ceiling mechanism) through position 12 (AI Studio) | Ceiling enforcement deliberately pulled forward to position 6, ahead of the feature (position 12) that makes it visible to tenants |

## 7. Milestones

> **Canonical, kept-current version:** [`MILESTONES.md`](MILESTONES.md) — includes target dates and owners. The table below is retained here because it's the direct output of the position numbering in §1; update `MILESTONES.md`, not this table, as dates/owners change.

| Milestone | Position | Maps to |
|---|---|---|
| M1 — Foundation Secure | After position 3 | Phase 0 exit, `PRODUCT_ROADMAP.md` |
| M2 — First Commercial Transaction | After position 7 | Alpha release, `RELEASE_PLAN.md` |
| M3 — First Real Tenant Data | After position 9 | Private Alpha release |
| M4 — Self-Service Configuration Live | After position 10 | Internal Beta release |
| M5 — Framework Genericity Proven | After position 11 | Partner Beta release — **the single most important milestone in the plan**, directly closing R-02 |
| M6 — Ecosystem Proven | After position 13 | Public Beta release |
| M7 — Production-Grade Confidence | After position 14 | Release Candidate declared |
| M8 — General Availability | Terminal | GA declared |

---

## 8. RACI Matrix

**R** = Responsible (does the work) · **A** = Accountable (owns the outcome, signs off) · **C** = Consulted · **I** = Informed

| Activity | CPO | CTO | Chief Architect | Program Director | Release Manager | Eng Leads |
|---|---|---|---|---|---|---|
| Security P0 remediation | I | A | C | I | I | R |
| Tenant isolation (RLS) architecture | I | C | A | I | I | R |
| Phase Go/No-Go decisions | C | C | C | **A** | C | I |
| Pricing & packaging | **A** | I | I | C | I | I |
| Entitlement schema design | C | A | R | I | I | R |
| Integration Hub framework design | I | C | **A** | I | I | R |
| Sprint planning & execution | I | I | I | **A** | I | R |
| Release stage gating (Alpha→GA) | C | C | C | C | **A** | I |
| Test strategy & coverage gates | I | C | I | I | I | **A** (QA Lead) |
| Production readiness sign-off | C | **A** | C | C | C | R |
| Commercial launch execution | **A** | I | I | R | I | I |
| GA declaration | **A** (joint) | **A** (joint) | **A** (joint) | **A** (joint) | **A** (joint) | I |
| Post-GA backlog prioritization | **A** | C | C | R | I | I |

---

## 9. Risk Matrix (program-level, consolidated view)

> **Canonical, kept-current version:** [`RISK_REGISTER.md`](RISK_REGISTER.md). The table below is retained as the sequencing-relevant snapshot; update the register, not this table, as statuses change.

| Risk ID | Description | Likelihood | Impact | Score (L×I, 1-5 scale) | Mitigation owner |
|---|---|---|---|---|---|
| R-01 | Cross-tenant IDOR recurrence | 3 | 5 | 15 | Security Eng / CTO |
| R-02 | Odoo-only framework at GA | 3 | 4 | 12 | Chief Architect |
| R-03 | Headcount growth doesn't materialize | 3 | 4 | 12 | Program Director |
| R-04 | Test debt carried into new code | 4 | 4 | 16 | QA Lead |
| R-05 | Billing revenue leakage | 3 | 4 | 12 | Backend Lead |
| R-06 | AI cost overrun | 3 | 3 | 9 | AI Lead |
| R-07 | Marketplace certification bottleneck | 2 (pre-GA) | 3 | 6 | CPO |
| R-08 | Frontend build failure blocks CI | 4 | 4 | 16 | Frontend Lead |
| R-09 | Alembic drift causes migration collision | 4 | 4 | 16 | Backend Lead |
| R-10 | Odoo write-back feedback loop corrupts data | 2 | 3 | 6 | Backend Lead |

**Highest-scored items (R-04, R-08, R-09, all scoring 16) are all Phase 0 items** — this is not a coincidence, it is the entire justification for Phase 0 existing as a dedicated, non-skippable phase before any commercial feature work begins.

---

## 10. Decision Gates

| Gate | Trigger | Decision authority |
|---|---|---|
| **Architecture Gate** | Any proposed change to a DOM/CAP/OBJ ID already reserved in `SAAS_PLATFORM_ARCHITECTURE.md`, or any new ID request | Chief Architect, per `CANONICAL_ARCHITECTURE.md` §16.2 immutability rule |
| **Release Gate** | Every stage transition in `RELEASE_PLAN.md` (Alpha→Private Alpha→...→GA) | Release Manager, per that document's exit criteria |
| **Quality Gate** | Every PR merge (coverage, contract tests, cross-tenant regression suite) | Automated in CI, no human override without a documented exception logged by QA Lead |
| **Phase Go/No-Go Gate** | Every phase boundary in `PRODUCT_ROADMAP.md` | Program Director, with input from all Eng Leads |
| **GA Gate** | Terminal — all of `MASTER_EXECUTION_PLAN.md` §9 exit criteria | Full leadership group jointly (CPO, CTO, Chief Architect, Program Director, Release Manager) — the only gate requiring unanimous sign-off rather than a single accountable owner |
