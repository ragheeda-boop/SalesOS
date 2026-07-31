# Product Release Plan — Alpha to General Availability

> **Reads with:** `PRODUCT_ROADMAP.md` (phase gates this plan overlays), `ENGINEERING_ROADMAP.md` (sprint detail per stage).
> **Principle:** Each stage is a strict superset of the previous stage's feature surface plus a strict subset of the eventual GA user population — nothing ships to a wider audience than the previous stage without also having shipped everything that audience needs to not be harmed by it.

| Stage | Sprint gate | Target users | Population size |
|---|---|---|---|
| Alpha | End of Sprint 7 | Internal only | 0 external users |
| Private Alpha | End of Sprint 11 | Internal + 1 external design partner (Muhide) | 1 external tenant |
| Internal Beta | End of Sprint 15 | Full internal team, dogfooding | 0 external, ≥3 internal synthetic tenants |
| Partner Beta | End of Sprint 19 | Invited paying pilots | 3-5 external tenants |
| Public Beta | End of Sprint 22 | Open signup, waitlisted | Uncapped, throttled by waitlist release rate |
| Release Candidate | End of Sprint 25 | Public Beta population, frozen | Whatever Public Beta reached, no new admits during freeze |
| General Availability | Sprint 26 | Open market | Uncapped |

---

## 1. Alpha (Sprint 7)

**Features enabled:** Owner Platform Core — tenant provisioning (sales-assisted only), Subscription/Billing against Stripe sandbox, Entitlement Engine v1 gating ≥3 DOM/CAP combinations, Owner Console MVP (read-only).

**Features disabled:** Integration Hub (no connectors yet), Tenant Studio, GTM Intelligence, AI Studio, Marketplace — everything from Phase 2 onward.

**Target users:** Internal engineering + product team only. No customer data, synthetic test tenants only.

**Exit criteria:** Full commercial lifecycle demo (provision → subscribe → gate → downgrade → status reflects in Owner Console) reproducible on demand; zero P0/P1 defects open against Phase 1 scope.

**Rollback plan:** Entire Owner Platform is net-new — rollback means reverting the deploy and restoring the pre-Phase-1 schema snapshot. No external users are affected by definition, so rollback carries zero customer-communication burden at this stage.

**Support plan:** None needed — internal Slack channel for issue triage, no formal SLA.

---

## 2. Private Alpha (Sprint 11)

**Features enabled:** Everything from Alpha, plus Integration Hub framework + Odoo adapter (Company/Contact/Opportunity/InteractionNote/SupportTicket/TaskCaseExtension/CustomerInvoice sync), Integrations Studio UI.

**Features disabled:** Tenant Studio (beyond Integrations), GTM Intelligence, AI Studio beyond existing DOM-012 primitives, Marketplace.

**Target users:** Internal team + **Muhide as the first and only external tenant**, using their real (already-reviewed, ARB-approved) Odoo connection.

**Exit criteria:** 14 consecutive days of scheduled Odoo sync in production with zero unresolved P0 sync failures; Muhide's Company 360 pages populated from real data with correct Golden Record matches; zero cross-tenant isolation findings.

**Rollback plan:** `feature_odoo_integration` flag can disable the entire connector instantly without affecting any other tenant capability (feature-flagged rollout was a mandatory condition per the Odoo ARB approval). If Muhide's data needs to be purged post-rollback, the deletion workflow from EPIC-04 handles it with the standard retention window.

**Support plan:** Direct engineering-to-customer channel with Muhide (no formal support tier yet — this is a design-partner relationship, not a commercial support relationship). Response target: same business day.

---

## 3. Internal Beta (Sprint 15)

**Features enabled:** Everything from Private Alpha, plus full Tenant Studio (Custom Objects/Fields, Workflow Builder, Scoring Rules, Territories, Permissions, Branding, Notifications).

**Features disabled:** GTM Intelligence, AI Studio (beyond existing primitives), Marketplace.

**Target users:** Full internal team, dogfooding across ≥3 internally-provisioned synthetic tenant workspaces configured to look meaningfully different from each other (different custom fields, different workflows, different branding) — specifically designed to stress-test Studio's multi-tenant configuration isolation, not just its happy path.

**Exit criteria:** 2 weeks of internal dogfooding with zero schema-collision incidents across the 3 synthetic tenants; every Studio module used at least once by someone who did not build it (usability validation, not just correctness validation).

**Rollback plan:** Each Studio module is independently feature-flagged (per `PROGRAM_PLAN.md` EPIC-10 deployment tasks) — a problem isolated to, say, Workflow Builder can be disabled without pulling Custom Objects/Fields down with it.

**Support plan:** Internal-only — findings logged as bugs through the standard engineering backlog, no external support surface yet.

---

## 4. Partner Beta (Sprint 19)

**Features enabled:** Everything from Internal Beta, plus GTM Intelligence (ICP, Market Sizing, Lead Discovery, Lookalikes, Enrichment, Verification, Website Intelligence, AI Outreach, Sequencing) and the **second certified connector**.

**Features disabled:** AI Studio's Prompt Library/Memory/Policies tenant-facing surface (still Phase 5), Marketplace.

**Target users:** 3-5 invited paying pilot tenants, selected for diversity of use case (at least one tenant on the second connector, not just Odoo, to get real-world validation of R-02's closure beyond the internal certification test).

**Exit criteria:** All 3-5 pilots actively using at least the CRM + one GTM Intelligence capability for ≥2 weeks; Stripe billing flipped from test mode to live mode for these specific accounts with at least one real successful charge per pilot; support SLA (defined below) held at ≥95% for the pilot cohort.

**Rollback plan:** Per-capability feature flags allow disabling any single GTM Intelligence capability without affecting the others or the core CRM; a pilot tenant can be reverted to Internal-Beta feature scope (Studio-only, no GTM) via entitlement downgrade without data loss, since GTM objects (`ICPProfile`, etc.) are additive, not destructive to core objects.

**Support plan:** First formal support tier begins here — dedicated Slack/email channel per pilot, **target response time: 4 business hours for P1, 1 business day for P2**, staffed by Program Director + rotating engineering on-call (dedicated Customer Success hire targeted for Phase 5, not yet in place).

---

## 5. Public Beta (Sprint 22)

**Features enabled:** Everything from Partner Beta, plus AI Studio (Prompt Library, AI Policies, AI Memory MVP) and Marketplace (browse/install, ≥3 connectors + ≥1 playbook).

**Features disabled:** Third-party Marketplace submission (first-party listings only through GA); siloed/dedicated-tenant deployment tier (pooled tier only through GA per `SAAS_PLATFORM_ARCHITECTURE.md` §13/A6).

**Target users:** Open self-service signup, but **waitlisted and released in controlled batches** (not a single flood) — batch size determined by Platform Health headroom (CAP-074) at each release wave, not a fixed calendar cadence.

**Exit criteria:** Self-service signup → provision → first-value (a working Company 360 page or a first GTM Intelligence result) achieved by ≥80% of admitted waitlist cohort within 24 hours of signup, unassisted; zero P0 incidents attributable to the open-signup surface across the beta window.

**Rollback plan:** Waitlist release can be paused instantly (stop admitting new signups) without affecting existing Public Beta tenants — this is the primary rollback lever at this stage, cheaper than a feature rollback. Individual feature flags remain the secondary lever if a specific capability (not the signup flow itself) misbehaves.

**Support plan:** Self-service documentation + community/ticket-based support (target: 1 business day response for all self-service tenants), with the Partner Beta cohort's dedicated-channel support continuing unchanged in parallel (they don't get downgraded by Public Beta opening).

---

## 6. Release Candidate (Sprint 25)

**Features enabled:** Full GA feature set, frozen — no new features admitted during this stage, per `PRODUCT_ROADMAP.md` Phase 6 objectives ("no new user-facing features... any finding that requires an architecture change is treated as a blocker").

**Features disabled:** Nothing new disabled — this is a stabilization stage, not a feature-reduction stage.

**Target users:** The full Public Beta population, frozen (no new admits during the RC soak window) — this maximizes real-world signal during the soak without growing the blast radius of an undiscovered issue.

**Exit criteria:** Minimum 2-week soak with **zero P0/P1 regressions**. If any P0/P1 is found, the fix is the only permitted change, it is re-tested, and **the 2-week soak clock restarts from zero** — there is no partial-credit soak.

**Rollback plan:** RC is, by construction, one deploy behind whatever the last stable Public Beta build was — rollback is a straight revert to that last-known-good build, with the specific regression documented before any re-attempt at RC.

**Support plan:** Same as Public Beta, plus a dedicated RC-monitoring rotation (DevOps/SRE + QA-Lead) watching dashboards daily specifically for soak-invalidating regressions.

---

## 7. General Availability (Sprint 26)

**Features enabled:** Everything validated through RC. Pricing goes live in production billing mode for all new signups (Partner Beta pilots already converted in Sprint 19; Public Beta tenants convert to paid at GA per the pricing/grandfathering terms defined in `COMMERCIAL_LAUNCH_PLAN.md`).

**Features disabled:** Same exclusions as Public Beta carry forward as named, tracked post-GA backlog (third-party Marketplace, siloed tenancy tier, cross-session AI memory, tenant sharding) — not silently dropped, explicitly listed in the Sprint 26 GA-day backlog review per `ENGINEERING_ROADMAP.md`.

**Target users:** Open market — no waitlist, no admission gate (beyond normal signup/payment).

**Exit criteria:** All 9 exit criteria in `MASTER_EXECUTION_PLAN.md` §9, satisfied simultaneously, signed off by the full leadership group (CPO, CTO, Chief Architect, Program Director, Release Manager).

**Rollback plan:** GA rollback is the most expensive rollback in this plan and is treated as a last resort — the preference order is (1) feature-flag-disable the specific broken capability, (2) roll forward with a hotfix, (3) full build revert only if (1) and (2) are both infeasible within the incident's severity window (per `OPERATIONS_MANUAL.md` incident response runbook). A full GA rollback requires CTO + Release Manager joint sign-off given the customer-communication and billing implications.

**Support plan:** Full commercial support tiers live per `COMMERCIAL_LAUNCH_PLAN.md` §SLA (Starter/Growth/Enterprise-differentiated response times), dedicated Customer Success function staffed, 24/7 on-call rotation for P0 incidents established per `OPERATIONS_MANUAL.md`.
