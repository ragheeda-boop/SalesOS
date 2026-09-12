# 17 — Next Actions (0–90 days)

**Priority scale:** P0 (blocker for pilot) · P1 (must-have for MVP release) · P2 (fast follow) · P3 (nice-to-have)

**Each item has:** owner-suggested · size-estimate · dependency · evidence gate for closure.

---

## Sprint 0 — Repo hygiene + honesty commit (Week 1)

### P0

1. **Repair git working tree on `fix/login-and-keys`**
   - Size: 0.5 day
   - Owner: Founder + TL
   - Blocker: 4,748 files staged deleted (see AUDIT_INVENTORY §9 / REPO_AUDIT §6)
   - Steps: `git reset HEAD -- .`, verify status, then commit intentional changes
   - Gate: `git status` shows expected diff, not 4,748 deletions

2. **Reconcile `feature_ai_copilot` = True vs AI_HONESTY.md mandate False**
   - Size: 0.5 day
   - Owner: Founder + PO
   - Decision: (a) flip flag → False (safer) OR (b) update AI_HONESTY.md to reflect Phase 3 closure + provider status; OR (c) tie it to `disable_ai_features` env var and default False for external tenants until provider signed
   - Gate: single documented decision + code state matching

3. **Fix `preDeployCommand` drift between `railway.json` and live Railway service**
   - Size: 0.5 day
   - Owner: DevOps
   - Gate: `railway.json` and live service both use `alembic upgrade head`

4. **Enable Railway managed backup schedule**
   - Size: 0.5 day
   - Owner: Platform Owner
   - Blocker: Railway account tier
   - Gate: OPS-01 row 3b signed

5. **Add STALE / SUPERSEDED banners to identified stale docs**
   - Size: 0.5 day
   - Owner: TL
   - Files: `docs/vnext/GO_NO_GO_DECISION.md`, `docs/vnext/GA_CHECKLIST.md`, `docs/audit/current-state/*`
   - Gate: Banners visible; `docs/INDEX.md` codifies

6. **Rewrite `README.md` Domains table to match reality**
   - Size: 0.5 day
   - Owner: TL
   - Reality: SalesOS = Product, others = Vision. AuditOS/DecisionOS/LocalContentOS are NOT active product trees in this repo
   - Gate: README matches AGENTS.md §1

---

## Sprint 1 — Design Partner enablement (Weeks 2-4)

### P0

7. **Draft + sign Design Partner MOU (bilingual)**
   - Size: 1 day + legal review
   - Owner: Founder + external legal
   - Templates: `08_SALES_PLAYBOOK.md` §MOU + §Order Form
   - Gate: PDF signed with at least one Design Partner

8. **Sign production LLM provider contract (OpenAI Enterprise, Azure OpenAI, or Anthropic direct)**
   - Size: 5–15 days (procurement)
   - Owner: Founder / Business Ops
   - Blocker: Contract negotiation + payment method
   - Gate: API key provisioned in Railway; ReliableProvider tested against real provider

9. **Set up Google OAuth staging + production apps**
   - Size: 1 day
   - Owner: DevOps
   - Blocker: Google Cloud Console access
   - Gate: Real OAuth login works end-to-end in staging

10. **Onboard first Design Partner tenant end-to-end**
    - Size: 3–5 days
    - Owner: Founder + TL
    - Blocker: 7, 8, 9 above
    - Gate: One real user in real tenant successfully uses ICP scoring on ≥ 10 real companies, HITL approval on ≥ 3 recommendations, feedback loop closed

### P1

11. **Publish honest public marketing page**
    - Size: 2 days
    - Owner: Founder
    - Content: value prop, WHAT SALESOS IS (Product Core + Master Data + HITL + Grounded Copilot), WHAT IT IS NOT (autonomous agent, magic AI, browser-only)
    - Gate: Live at custom domain OR Vercel URL

12. **Provision Sentry DSN + enable live error stream**
    - Size: 0.5 day
    - Owner: DevOps
    - Gate: Errors visible in Sentry dashboard

13. **Public status page (statuspage.io or self-hosted)**
    - Size: 1 day
    - Owner: DevOps
    - Gate: Live status page, subscribed users receive updates

14. **First WBR / MBR dashboard admin page**
    - Size: 2 days
    - Owner: TL
    - Location: `/v3/admin/kpis` or new page
    - KPIs from `10_KPI_FRAMEWORK.md` §Reporting cadence
    - Gate: WBR-ready screenshot every Monday

### P2

15. **Documentation hygiene sprint (nested duplicates cleanup)**
    - Size: 5 days
    - Owner: TL
    - Items: `packages/packages/`, `archive/archive/`, `infrastructure/infrastructure/`, `docs/docs/`, `engineering-os/engineering-os/`, `migration-log/migration-log/`
    - Gate: All nested duplicates resolved

---

## Sprint 2 — Master Data value delivery (Weeks 5-8)

### P0

16. **Human PO review of 54,185 Phase 6 candidates (BLOCKED gate)**
    - Size: 3–6 weeks (P1 + P2 + P3 buckets)
    - Owner: Data + PO (Ragheb)
    - Blocker: PO capacity
    - Gate: `docs/data/phase6/PHASE6_HUMAN_REVIEW_PO_GATE.md` closed
    - Note: this unblocks the shift from Phase 7-A capture-only → Phase 7-B write-through to production

17. **DI P1/P2 methodology reproducibility confirmation**
    - Size: 2 days
    - Owner: PO + TL
    - Blocker: DI (Data Intelligence) mark P1=23,306 / P2=37,719 formulas as NOT RECONCILED per §38 (implied)
    - Gate: Signed reproducibility report

18. **Adjudicate 36 SUSPICIOUS_SHORT separator-list accounts (real short CR vs artifact)**
    - Size: 1 day
    - Owner: Data + PO
    - Gate: All 36 classified

### P1

19. **Populate first real production tenant (Design Partner) in `salesos` production DB**
    - Size: 3 days
    - Owner: Data + DevOps + PO
    - Blocker: 16 + 17 + 18 + 4 (backup)
    - Gate: One real tenant fully live with real data

20. **Enable Signal Marketplace subscriptions for first Design Partner**
    - Size: 2 days
    - Owner: TL + PO
    - Gate: Subscribed to ≥ 1 signal from ≥ 1 pack; first event fires and appears in feed

21. **Populate RAG corpus for first Design Partner**
    - Size: 2 days
    - Owner: PO + Data
    - Gate: Real corpus > 20 documents; grounded retrieval cites real sources

22. **Populate ICP profile for first Design Partner**
    - Size: 1 day + business input
    - Owner: PO + Founder + Design Partner
    - Gate: Real ICP profile (industry + size + geo + tier) scoring real companies with `fit != UNKNOWN`

---

## Sprint 3 — Pricing readiness (Weeks 9-12)

### P0

23. **Sign 3 Design Partner MOUs**
    - Size: 4-8 weeks
    - Owner: Founder
    - Gate: 3 MOUs signed

24. **Complete 3 Design Partner onboardings**
    - Size: 2-3 weeks per partner
    - Owner: Founder + Success (Founder-hat)
    - Gate: 3 tenants active, 3 WBR cadences running

25. **Collect 3 written case studies + testimonials**
    - Size: 1 day per partner (mid-Sprint 3)
    - Owner: Founder
    - Gate: 3 case studies published or ready for enterprise deck

### P1

26. **Activate Stripe live billing (Team Tier)**
    - Size: 2 days
    - Owner: Business Ops + DevOps
    - Blocker: Business bank + Stripe KYC
    - Gate: First test invoice sent (can be to Founder's alt entity)

27. **Draft standard MSA + DPA (Arabic + English)**
    - Size: 3 days + legal review
    - Owner: Founder + external legal
    - Gate: Signed templates ready for Team Tier sales cycle

28. **First Team Tier customer conversion**
    - Size: 3-6 weeks sales cycle
    - Owner: Founder
    - Gate: One SAR-priced invoice paid

### P1 — Provider policy hardening

29. **Wire real LLM provider to ReliableProvider + PolicyGate**
    - Size: 2 days
    - Owner: TL
    - Depends on: 8
    - Gate: Live cost tracking > 0 SAR/tokens, live groundedness eval > 0.8

30. **Reach groundedness > 0.85 target on Design Partner traffic**
    - Size: continuous
    - Owner: TL + PO
    - Gate: Groundedness rolling 7-day > 0.85 in `/metrics`

---

## Sprint 4+ — Growth conditions (Months 4-6+)

### P1

31. **Custom domain (aqliya.sa / salesos.sa / decisionos.sa TBD)**
    - Size: 1 day + DNS
    - Owner: DevOps
    - Gate: Live at custom domain with valid TLS

32. **First Enterprise pilot LOI**
    - Size: 3-6 months sales cycle
    - Owner: Founder
    - Gate: LOI signed with clear scope, timeline, VPC requirements

33. **KSA data residency architecture design**
    - Size: 2 weeks
    - Owner: TL + DevOps
    - Blocker: Enterprise LOI (pull-based, not push)
    - Gate: Architecture doc; unquarantine K8s manifests

34. **First hire: PO / Business (if traction warrants)**
    - Size: 8-12 weeks recruit + onboard
    - Owner: Founder
    - Blocker: Runway or first Enterprise contract signed
    - Gate: Hire + 30-day plan executed

### P2

35. **First 90-day Enterprise pilot**
    - Size: 3 months delivery
    - Owner: Founder + PO + TL
    - Gate: Success metrics per Enterprise SOW

36. **SOC 2 Type I audit start**
    - Size: 6-9 months
    - Owner: DevOps + Founder + external auditor
    - Gate: Auditor engaged, evidence collection begun

37. **Un-quarantine K8s manifests + Terraform** for Enterprise
    - Size: 2 weeks
    - Owner: DevOps
    - Blocker: 34 or first Enterprise contract
    - Gate: DEC-149 revised; K8s live in staging

---

## Backlog (do NOT start unless Sprint 4 completes)

- Mobile app (iOS + Android)
- SAML / SSO / SCIM
- Third-country hosting
- Marketplace / plugin ecosystem
- WhatsApp / SMS integration
- ZATCA compliance module
- ISO 27001 / SAMA / PCI
- International expansion (UAE, GCC)
- Multi-currency (KWD, AED, QAR, USD, EUR)
- Video meeting integration
- CRM data import wizards for HubSpot / Salesforce / Zoho
- Salesforce AppExchange listing
- Standalone AuditOS / DecisionOS / LocalContentOS products

---

## Not-doing list (deliberate)

- Autonomous AI agents (per ADR-0104)
- Digital Twin (per ADR-0103)
- Revenue Brain autonomous (per ADR-0105)
- Neo4j online (per ADR-108)
- Big paid ads before 3 Design Partner wins
- Analyst engagements before Design Partner case studies
- Marketing without a story that beats "just use ChatGPT + Notion"

---

## Non-negotiable evidence gates

1. **AI on / production**: only after real provider signed + groundedness > 0.85 + PII 0 violations over 500 test prompts + AI_HONESTY.md updated
2. **Charge first invoice**: only after production DB has real tenant with real data, backup schedule live, DPA signed
3. **Public GA claim**: only after 3 Design Partners in production + WBR cadence + status page + Sentry live
4. **Enterprise sale**: only after case studies + SOC 2 Type I audit started + KSA-hosting architecture design
5. **Adding scope**: only via ADR update + fitness-gate update + explicit gate closure

---

*Next-actions list — priority-ordered, evidence-gated, dependency-aware.*
