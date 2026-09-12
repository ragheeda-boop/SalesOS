# 18 — Project Strategy (how to actually run this project)

**Author perspective:** experienced founder-technical-leader assuming a solo builder + AI-first workflow. Bilingual (Arabic executive layer + English technical layer).

---

## 1. Operating principles

1. **AI assists. Humans decide. Evidence governs.** (Core principle — non-negotiable.)
2. **Documentation is not proof of implementation. Code is not proof of production.**
3. **Sequential closure > parallel excitement.** Follow `SALESOS_MASTER_CLOSURE_SEQUENCE.md`.
4. **Every claim must have executable evidence.** No verbal / doc-only wins.
5. **When in doubt, degrade honestly.** UNKNOWN > fabricated.
6. **The gate is customer money, not code progress.** Green tests ≠ paid invoice.
7. **Never weaken security, auth, RLS, RBAC, or audit logging without ADR + explicit approval.**
8. **Feature flags are checkpoints, not switches.** Only flip when the corresponding evidence gate closes.

---

## 2. Weekly cadence (recommended)

### Monday — WBR + Planning

- 30-min WBR (Weekly Business Review) on last week's numbers
  - New Design Partner conversations, MOU pipeline, product usage
  - Grounded eval scores, INSUFFICIENT-EVIDENCE %, HITL SLA
  - System health (uptime, migrations OK, DR OK, backups green)
- Assign week's P0 + P1s from `17_NEXT_ACTIONS.md`
- Update board in `AGENTS.md` §current session

### Tuesday–Thursday — Deep work

- 3-hour focus blocks
- Ship minimally, in small commits with real evidence in commit body
- Each significant PR: attach test evidence + verification screenshots + honesty label
- Do NOT touch parallel-work files (TenantList, security P0 endpoints) unless assigned

### Friday — Ship + Reflect

- Deploy to staging first, canary if needed
- Manual QA of the week's shipped path
- Write session summary in `AGENTS.md` §NNN with:
  - Action | Result | Details table
  - Files changed this session
  - Remaining human actions
  - Session status label (READY / IN_PROGRESS / BLOCKED)

### Monthly — MBR + Cleanup

- MBR (Monthly Business Review) on last month
- Sprint review + retro (even solo — write it down)
- Docs hygiene pass (STALE / SUPERSEDED banners)
- Fitness gates audit (are they passing? new gates needed?)

---

## 3. Product decision framework

**Every scope decision must answer:**

1. Is this in the current gate? (Product Core → Intelligence → AI → Platform per master sequence)
2. What real user problem does this solve? (Design Partner voice, not internal preference)
3. What evidence would falsify the hypothesis? (Not "success" — falsification)
4. What is the honest name of this? (Not the marketing name)
5. What breaks if we don't do this?
6. Does this violate a prior ADR? (If yes → ADR update required)
7. Does this touch security / RLS / audit? (If yes → security review required)

**Reject the request if:**
- It's for a new module while an earlier gate is OPEN
- It's for autonomous AI while HITL isn't proven
- It's for AuditOS/DecisionOS/LocalContentOS product claims while SalesOS isn't paying
- It's for scale (multi-region / K8s) before Design Partner MOU signed
- It comes with marketing language ("AI-native", "autonomous") without evidence

---

## 4. Team org (as scale grows)

### Month 0 (solo founder-builder)

- Wear all hats: Founder, PM, TL, Sales, Support, Ops
- Use AI subagents (Cursor Task tool, Claude / GPT / Gemini) for parallel exploration
- Do NOT hire yet
- Every hour is on: (a) shipping product, (b) closing pilots, (c) writing evidence
- Nothing else

### Month 3 (post first Design Partner)

- Consider **fractional Business Lead** (contract, SAR 20-40k/month) for sales cycle discipline
- Founder remains PM + TL
- Do NOT hire full-time engineer yet

### Month 6 (post 3 Design Partners → Team Tier launch)

- Consider **first FTE**: Business Owner OR Product Owner OR Full-stack Engineer (pick one)
- Founder retains veto on ADRs and evidence gates
- All hires must read AGENTS.md + PRODUCT_BIBLE.md + `.cursor/rules/` day-1

### Month 9 (post first Enterprise LOI)

- Second FTE: infra/DevOps or Security specialist
- Third FTE: Sales rep with KSA network
- Establish weekly all-hands + async writing culture

---

## 5. Founder / PO decision boundaries

**Founder decides (never delegate):**
- Product vision, product boundaries (SalesOS-only), Not-Do list
- Pricing, contract terms, sales priorities
- Hiring, culture, security posture

**PO decides (with founder consent):**
- Feature backlog priority within current gate
- HITL SLA thresholds, sales-readiness score interpretation
- ICP profile updates, review-queue disposition rules

**TL decides (with founder + PO consent):**
- Architecture choices within ADRs
- Migration ordering, refactor timing
- Provider selection, observability tooling

**No individual decides (require council):**
- ADR overrides (deferred features going live)
- Flipping `feature_ai_copilot=True` for external tenants
- Removing PII enforcement
- Weakening RLS, RBAC, or audit logging
- Cross-tenant data access (even for support)

---

## 6. Business + product balance

**60/40 rule:** 60% shipping product + evidence, 40% talking to real prospects (or reading their words).

**When shipping:**
- Ruthlessly minimal
- Match existing patterns
- Real evidence in PR body
- Honesty label ("build validated", "pilot-ready with conditions", "production no-go")

**When selling:**
- Design Partner ≠ paying customer (yet)
- Every conversation is a discovery, not a demo
- Honest scope > overpromise + underdeliver
- Reject prospects that ask for autonomous AI / features that violate not-do list

---

## 7. Risk & governance protocol

### Weekly risk log update

Every WBR reviews `19_RISK_REGISTER.md` and updates:
- New risks
- Retired risks
- Risk-adjusted priorities

### Monthly ADR audit

Every MBR reviews:
- ADRs deferred that should now be revisited (Digital Twin, Agent Runtime, Revenue Brain — currently DEFERRED)
- ADR conflicts (feature_ai_copilot vs AI_HONESTY.md — currently OPEN)
- New ADRs needed

### Quarterly compliance review

- PDPL residency compliance (currently NON-COMPLIANT for KSA Enterprise)
- Data handling audit
- Audit log retention (currently 90 days)
- Third-party sub-processor list

---

## 8. Financial discipline

### Runway management

- Track burn monthly. Aim for 18-24 months runway at all times.
- Cost buckets:
  - Infra (Railway + Vercel + LLM provider + Sentry + Meilisearch)
  - Human capital (founder salary + fractional + FTE)
  - Legal / accounting (KSA business setup + contracts)
  - Marketing (Q2 2027+ only, minimal)

### Revenue milestones

| Month | Revenue target | What that unlocks |
|-------|----------------|-------------------|
| 3 | SAR 0 (Design Partner free) | Product validation |
| 6 | SAR 60k ARR (1 Team) | Cost coverage of infra |
| 9 | SAR 240k ARR (4 Team) | First hire viability |
| 12 | SAR 500k ARR (Team + Enterprise pilot) | Second hire + long runway |
| 18 | SAR 1.5M ARR | Series A optionality |

### No aggressive discounting

- Design Partner: SAR 0 always
- Team Tier: SAR 60k/year minimum (or 40 SAR/user/month × 5 min)
- Enterprise: SAR 500k+ (never below 500k for KSA VPC)

---

## 9. Communication protocol

### External communication

- **Public marketing:** honest labels, no "AI-native" without evidence, no autonomous claims
- **Sales pitch:** honest scope, honest gaps, "here's what works today, here's what's coming, here's what we won't do"
- **Investor updates:** monthly one-pager with honest ARR, honest usage, honest risks

### Internal / agent communication

- Every commit: honesty label
- Every PR: evidence attached
- Every session: `AGENTS.md` §NNN summary
- Every ADR: status + supersession chain

---

## 10. When to say NO

**Say NO to:**
- Enterprise prospect asking for full custom development before signed contract
- Investor asking for hockey-stick revenue plot without customers
- Feature request that adds a new product layer while a gate is OPEN
- Contractor asking to "just refactor" a stable module
- Anyone asking to flip AI feature flags without evidence
- Anyone asking to weaken RLS / audit / security "for demo"
- Anyone asking to backdate an ADR

**Say YES to:**
- Design Partner asking for a small honest feature that unblocks their pilot
- Investor asking for evidence-based projections + honest risks
- Contributor bringing an ADR + failing test + minimal patch
- Sales prospect willing to sign design-partner MOU with real time investment
- Enterprise LOI with clear scope and paid-pilot commitment

---

## 11. Bilingual discipline

**Arabic-primary content (must be first-class):**
- Public marketing
- Sales scripts
- Executive summaries in board decks
- ICP-related content for Saudi buyers
- MSA / DPA / MOU templates

**English-primary content:**
- Code, comments, ADRs
- Technical docs (still bilingual key sections)
- Investor decks (bilingual, English primary if VC is US/UK)
- Public status page

**Bilingual (both sides at same quality):**
- Product screens (RTL/LTR flipping)
- Session summaries
- Executive audits
- Case studies

---

## 12. Automation vs manual

**Automate:**
- CI (already done — 9 workflows)
- Fitness gates (already done — FF-07/AIGOV/FF-14/FF-DUP-01)
- Schema drift detection
- Signal seeding at boot
- Backup schedule (once enabled)
- Cost tracking (already done)
- Sentry alerting (once activated)

**Manual (deliberately):**
- HITL approvals (product design — never automate)
- ICP profile updates (business judgment)
- Master data candidate review (PO decision)
- Design Partner MOU signing (founder + partner)
- Public release announcements
- ADR authorship

---

## 13. Rituals to establish

1. **Every ship = commit + evidence + session summary**
2. **Every week = WBR + Monday plan**
3. **Every month = MBR + ADR audit**
4. **Every quarter = risk review + compliance review + strategy re-check against `03_PRODUCT_STRATEGY.md`**
5. **Every Design Partner win = case study + testimonial + reference-call scheduled**
6. **Every risk retirement = evidence attached + risk register updated**
7. **Every gate closure = evidence pack + AI_HONESTY update + AGENTS.md session**

---

## 14. Emergency protocols

**If pilot Design Partner cancels:**
- Retro: was it product? was it sales? was it execution?
- Do NOT immediately re-prospect. Re-check ICP.
- Update `05_CUSTOMER_SEGMENTATION.md`

**If provider fails / production incident:**
- Circuit breaker triggers → dev provider path (still DEV-ONLY warning to users)
- Sentry alert + status page update within 5 minutes
- RCA within 48 hours (per SOAK RCA template)

**If security incident:**
- Immediate lockdown per RUNBOOK.md
- Notify affected tenants within 24 hours
- Follow PDPL breach notification if in-scope
- RCA + ADR + code fix + regression test

**If runway drops below 6 months:**
- Freeze new hires
- Freeze infra scale-up
- Convert Design Partners to paid immediately
- Fundraise or bridge

**If honest score / evidence review demands descoping:**
- Do it. Descope publicly. Update AI_HONESTY.md.
- Prioritize keeping trust over keeping features.

---

## 15. Success is measurable

- **Product-Market Fit:** 3 Design Partners actively using the product weekly, 6-month retention rate > 80%, 2-3 case studies with quantified value
- **Business viability:** first paid invoice, SAR 500k ARR, 24-month runway
- **Product integrity:** 0 critical security incidents, groundedness > 0.85, HITL SLA < 24h p95
- **Engineering discipline:** all gates closed with evidence, all ADRs live, all fitness gates green
- **Public trust:** honest scoreboard, no overclaim, community + prospect testimonials

---

*Project strategy — solo-founder, evidence-first, KSA-first, honest-first.*
