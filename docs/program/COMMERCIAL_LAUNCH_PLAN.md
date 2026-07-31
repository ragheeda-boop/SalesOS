# Commercial Launch Plan

> **Reads with:** `SAAS_PLATFORM_ARCHITECTURE.md` §14-16 (Marketplace/Licensing/Subscription architecture), `RELEASE_PLAN.md` (which stage each commercial motion activates in).
> **Market:** Saudi/GCC-first (per SalesOS's existing Arabic-first positioning and government-data moat), expanding regionally post-GA.

---

## 1. Pricing

| Tier | Monthly price (per tenant, USD equivalent, SAR-denominated for GCC customers) | Seats included | Overage model |
|---|---|---|---|
| **Starter** | $499/mo (≈ SAR 1,870) | 5 seats | $49/seat beyond 5 |
| **Growth** | $1,999/mo (≈ SAR 7,495) | 25 seats | $59/seat beyond 25 |
| **Enterprise** | Custom (starts ≈ $6,000/mo) | Negotiated | Negotiated |

**Rationale for this banding:** Starter is priced to be a credible alternative to a single point-tool subscription in the iSkala-stack sense (i.e., cheaper than running Apollo + Clay + SmartLead + Debounce separately, per the cost comparison in the iSkala reverse-engineering report), not to be a loss-leader. Growth is priced for a team that has outgrown a single-tool stack and needs the native CRM + GTM + Studio combination. Enterprise is relationship-priced because it includes negotiated items (siloed tenancy tier, custom entitlements, dedicated support SLA) that don't fit a fixed-price shelf.

**Annual discount:** 15% for annual pre-payment, standard SaaS practice, improves cash-flow predictability for the billing/dunning model in `PROGRAM_PLAN.md` EPIC-05.

---

## 2. Packaging

Directly maps to the Entitlement Engine (CAP-070) `Plan.entitlements` schema — this is not a marketing document disconnected from the technical gate, it is the source sales quotes against and engineering enforces:

| Domain/Capability | Starter | Growth | Enterprise |
|---|---|---|---|
| DOM-001–006 (Core CRM, Revenue) | ✅ | ✅ | ✅ |
| DOM-011/012 (AI/RAG, AI Studio) | ❌ | ✅ | ✅ |
| DOM-021 (Integration Hub) | 1 connector | 5 connectors | Unlimited |
| DOM-022 (Tenant Studio) | Limited (Branding + Permissions only) | Full | Full |
| DOM-023 (GTM Intelligence) | ❌ | ✅ | ✅ |
| DOM-024 (Marketplace — install rights) | ✅ (browse/install) | ✅ | ✅ (+ publish rights, post-GA) |
| AI token allotment/month | 10K | 500K | Negotiated |
| Deployment tier | Pooled | Pooled | Pooled or siloed (§13 of `SAAS_PLATFORM_ARCHITECTURE.md`) |
| Support SLA | Community/ticket, 1 business day | 4 business hours (P1) | 1 hour (P0), dedicated CSM |

---

## 3. Plans

Plan changes (upgrade/downgrade) take effect per the proration logic in `PROGRAM_PLAN.md` EPIC-05 STORY-05-05 — upgrades are immediate with prorated charge, downgrades take effect at the next billing cycle boundary (to avoid mid-cycle entitlement clawback disputes) unless the tenant explicitly requests immediate downgrade with prorated credit.

**Grandfathering:** Partner Beta and Public Beta tenants who converted to paid before GA keep their beta-era pricing for a minimum of 12 months post-GA — this is a deliberate loyalty/reference-customer incentive, not an oversight.

---

## 4. Marketplace

Revenue model (per `SAAS_PLATFORM_ARCHITECTURE.md` §14): first-party (Owner-built) connectors/playbooks are bundled into plan tiers at no additional charge (they're the product, not an upsell). Third-party listings — explicitly post-GA (`PRODUCTION_READINESS_CHECKLIST.md` §Marketplace) — will carry a 20% platform revenue share on paid listings, consistent with standard platform-marketplace economics (Salesforce AppExchange / HubSpot Marketplace precedent), set now so the number exists before any partner conversation needs it, even though enforcement code ships post-GA.

**At GA:** ≥3 first-party connector listings (Odoo + the second connector + a generic REST/CSV adapter), ≥1 first-party playbook, all included in Growth/Enterprise tiers at no additional charge.

---

## 5. Licensing

Licensing is entitlement-based, not seat-count-based alone (per `SAAS_PLATFORM_ARCHITECTURE.md` §15's two-layer model: `Plan.entitlements` gates DOM/CAP visibility, feature flags gate rollout within an entitled capability). This means:

- A Starter customer's contract explicitly names which DOM/CAP they do **not** have — sales must never verbally promise a capability the signed plan doesn't entitle, since the Entitlement Engine will enforce the contract technically regardless of what was said in a sales call.
- Enterprise custom entitlements are captured in a structured addendum to the standard contract (not a side-letter that engineering never sees) — feeding directly into `Plan.entitlements` for that specific tenant.

---

## 6. Customer Onboarding

| Stage | Owner | SLA |
|---|---|---|
| Signed contract → provisioned tenant | Program Director (sales-assisted) or self-service (Public Beta+) | ≤10 minutes self-service, ≤1 business day sales-assisted |
| First admin login → first Studio configuration (custom field, branding) | Customer Success (or Program Director pre-CS-hire) | Guided within first week |
| First Integration Hub connection (e.g., Odoo) | Customer Success + Backend on-call for complex ERP mappings | Within first 2 weeks |
| First GTM Intelligence capability used (ICP defined, first Lead Discovery run) | Customer Success | Within first 30 days |
| "First value" milestone (a working Company 360 page populated from real data) | Tracked as the core activation metric | ≤24 hours for self-service, per `RELEASE_PLAN.md` Public Beta exit criteria |

---

## 7. Customer Success

Dedicated Customer Success hire targeted for onboarding before Public Beta (Sprint 22, per `ENGINEERING_ROADMAP.md` team roster note — flagged as not-yet-staffed through Partner Beta, where Program Director covers the function). CS responsibilities:

- Own the onboarding checklist (§6) and activation metrics.
- Monitor tenant health signals (distinct from the tenant's *own* customer-health scoring in DOM-019 — this is SalesOS-the-vendor's health-of-*its own customer*, per `SAAS_PLATFORM_ARCHITECTURE.md` §1 CAP-080 Tenant Lifecycle & Success).
- Own renewal conversations for Growth/Enterprise tiers.
- Feed product feedback into `PROGRAM_PLAN.md`'s post-GA backlog.

---

## 8. Support

| Tier | Channel | P0 response | P1 response | P2 response |
|---|---|---|---|---|
| Starter | Ticket/community | Best-effort | 1 business day | 3 business days |
| Growth | Dedicated channel | 4 business hours | 1 business day | 3 business days |
| Enterprise | Dedicated CSM + channel | 1 hour, 24/7 | 4 business hours | 1 business day |

Support Console (CAP-075) is the operational backbone (see `OPERATIONS_MANUAL.md` §6) — every tier's tickets flow through the same system, differentiated by SLA and routing priority, not by a different tool per tier.

---

## 9. SLA

**Uptime commitment (published, contractual for Growth/Enterprise):** 99.5% monthly uptime, measured against the Platform Health rollup (CAP-074). Credits: 5% of monthly fee per 0.5% below commitment, capped at 50% of monthly fee — standard SaaS credit structure, not punitive beyond what keeps the incentive aligned without threatening the business's ability to invest in the fix.

**Incident communication commitment:** P0 incidents affecting a tenant get a status update within 30 minutes of detection and every 30 minutes thereafter until resolved, per the Incident Response runbook (`OPERATIONS_MANUAL.md` §3).

---

## 10. Sales Process

| Stage | Activity | Owner |
|---|---|---|
| Lead → Qualified | Inbound (marketing site, Marketplace visibility) or outbound (using SalesOS's own GTM Intelligence capabilities — dogfooding the product to sell the product) | Sales (contracted/hired closer to Public Beta) |
| Qualified → Demo | Live demo using a sandboxed demo tenant (never a real customer's data) | Sales + Program Director (pre-hire) |
| Demo → Pilot (Partner Beta only) | Structured 2-4 week pilot with defined success criteria per `RELEASE_PLAN.md` §4 | Program Director |
| Pilot → Signed contract | Standard contract + Enterprise addendum if custom entitlements needed | CPO / Legal (external) |
| Signed → Onboarded | Per §6 | Customer Success |

**Self-service motion (Public Beta+):** Starter/Growth tiers support a no-sales-touch signup → provision → pay path — sales process above applies primarily to Enterprise and any Growth deal requesting a pilot.

---

## 11. Partner Strategy

| Partner type | Role | Timing |
|---|---|---|
| **Systems integrators (SIs)** | Implementation partners for Enterprise Tenant Studio configuration (custom objects, complex workflows) — a services layer around the product, not a resale channel initially | Post-GA |
| **Connector-certified ISVs** | Third parties building certified connectors (SAP, Dynamics, HubSpot, etc.) via the Marketplace certification pipeline (`PROGRAM_PLAN.md` EPIC-13) | Post-GA — pipeline itself proven pre-GA with first-party listings only |
| **Odoo (as an ecosystem, not a vendor relationship)** | No formal partnership required — Odoo is a certified connector target, not a business relationship SalesOS depends on | Live from Phase 2 |
| **Regional GCC data providers** | Potential enrichment-provider partnerships behind the Integration Hub, addressing the same Arabic/GCC contact-coverage gap the iSkala report identified as a genuine moat opportunity | Evaluated post-GA, tracked as a GTM Intelligence provider-expansion backlog item |

**Explicit non-strategy:** SalesOS does not pursue a reseller/channel-partner discount model at GA — the self-service + direct-sales motion is sufficient at the target scale (dozens of tenants), and channel economics are deferred until Public Beta/GA data shows where the actual demand is coming from, rather than guessed at now.
