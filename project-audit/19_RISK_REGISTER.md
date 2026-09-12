# 19 — Risk Register

**Rating scale:** Impact 1-5, Likelihood 1-5, Score = Impact × Likelihood. **Higher score = higher priority.**

| ID | Category | Risk | I | L | Score | Trigger | Mitigation | Owner | Status |
|----|----------|------|---|---|-------|---------|------------|-------|--------|
| **R-01** | Business | No paying customer within 6 months | 5 | 3 | 15 | Design Partner conversion fails; no first invoice by month 6 | Design Partner MOU discipline; force-conversion timeline; drop features not tied to first paid | Founder | OPEN |
| **R-02** | Provider | LLM provider unavailable / degraded / cost spike | 5 | 3 | 15 | Cydonia stays DEV-only forever; no real provider signed | Sign OpenAI/Azure/Anthropic contract in Sprint 1; keep CircuitBreaker + fallback provider | Founder + DevOps | OPEN |
| **R-03** | Compliance | PDPL enforcement / KSA hosting requirement blocks Enterprise sales | 5 | 3 | 15 | KSA prospect requires in-KSA data residency; Railway US blocks contract | Design KSA-hosting architecture; keep K8s manifests + Terraform ready | TL + DevOps | OPEN (mitigation started but paused) |
| **R-04** | Security | Data breach or cross-tenant leak | 5 | 2 | 10 | RLS bypass; app-role privilege escalation; audit log tampering | Dual DB roles enforced; RLS on all 51 tenant tables; monthly security review; audit log immutability | Founder + DevOps | OPEN — controls active |
| **R-05** | Business | Founder single point of failure (health / focus / burnout) | 5 | 2 | 10 | Founder unavailable > 2 weeks | Documented every decision (AGENTS.md); fractional Business Lead by month 3; hire by month 6 | Founder | OPEN |
| **R-06** | Financial | Runway shorter than 12 months | 5 | 2 | 10 | Cash drop below 12 months burn | Monthly burn tracking; convert Design Partners to paid; consider bridge funding | Founder | OPEN |
| **R-07** | Product | Design Partner churn (or all three cancel) | 4 | 3 | 12 | Pilot fails to demonstrate value at 90-day mark | Weekly check-ins with each partner; document success criteria upfront; drop early if wrong ICP | Founder + PO | OPEN |
| **R-08** | Technical | Master Data / ER quality degrades on real production tenant vs `salesos_test` | 4 | 3 | 12 | Phase 7-A → 7-B write-through reveals gaps not seen in test | Phase 6 dry-run + 12 safety validation checks; phase-gated production write | TL + Data | OPEN — controls active |
| **R-09** | Documentation | Dual-source-of-truth drift (PROJECT_BIBLE vs PRODUCT_BIBLE, README vs reality, AI_HONESTY vs feature flag) | 3 | 4 | 12 | Public claims diverge from code state; enforcement gap | Sprint 0 P0 items 2 + 5 + 6; monthly ADR audit | TL | OPEN |
| **R-10** | Repo | 4,748 staged deletions on `fix/login-and-keys` merged accidentally | 5 | 2 | 10 | `git commit -am` from current branch state | Sprint 0 P0 item 1; branch protection on master | Founder | OPEN |
| **R-11** | Provider | AI Copilot enabled to external tenants while DEV-only provider still active | 5 | 2 | 10 | `feature_ai_copilot=True` + real prospect uses production | Sprint 0 P0 item 2; add explicit env-var gate for external tenants | Founder + PO | OPEN |
| **R-12** | Ops | Production backup schedule not enabled (data loss on incident) | 5 | 2 | 10 | Production DB corruption before backup schedule live | Sprint 0 P0 item 4; verify Railway managed backup + external offsite | DevOps | OPEN — human blocked |
| **R-13** | Compliance | HITL SLA breach on production tenant | 3 | 3 | 9 | Approvals queue > 24h p95 | Assign back-up reviewer; SLA dashboard; alert on breach | PO | OPEN — controls partial |
| **R-14** | Business | Marketing overclaim ("AI-native" or "autonomous") triggering credibility damage | 4 | 2 | 8 | Prospect asks "does it really do X?" and it doesn't | Sprint 1 P1 item 11 (honest marketing page); AI_HONESTY.md enforcement in copy | Founder | OPEN |
| **R-15** | Product | Legacy `(dashboard)` shell (78 pages) drift confuses users | 3 | 3 | 9 | Users navigate to legacy pages; broken links; mismatched auth | Product decision Sprint 2; nav-based inventory | PO + TL | OPEN |
| **R-16** | Technical | Alembic drift between staging/production/local | 4 | 2 | 8 | Migration missed on deploy; DB schema differ | Schema-drift-gate in CI (already live); `preDeployCommand` fix (P0 item 3) | DevOps | OPEN — partial |
| **R-17** | Technical | 56 pre-existing unit test failures accumulate more failures | 3 | 3 | 9 | New commits break tests without noticing | CI pytest-asyncio isolation fix; monthly triage doc | TL | OPEN — controls in place |
| **R-18** | Compliance | PII leaked in LLM prompts (regression) | 5 | 2 | 10 | New agent bypass PolicyGate; PII in structured fields | Live-tested 0 violations; fitness gate FF-07; monthly grep audit | TL | OPEN — controls active |
| **R-19** | Business | Wrong ICP — building for the wrong buyer | 4 | 3 | 12 | Design Partners are wrong-fit; conversion fails | Sprint 1 explicit ICP capture per partner; refine `05_CUSTOMER_SEGMENTATION.md` monthly | Founder + PO | OPEN |
| **R-20** | Business | Product too broad; can't deliver quality on all fronts | 4 | 3 | 12 | 40 v3 pages + 78 legacy pages + 13 agents + Master Data all trying to be primary | Sprint 1 explicit MVP scope closure per `06_MVP_SCOPE.md`; Not-Do list enforced | Founder | OPEN |
| **R-21** | Compliance | GDPR / PDPL data subject request not fulfillable | 4 | 2 | 8 | Prospect asks for data-export or delete; delay > 30 days | Design data-export + delete APIs; document DSR process | TL | OPEN — not yet designed |
| **R-22** | Business | Investor / market expects hockey-stick growth that isn't real | 3 | 3 | 9 | Fundraise conversation misaligned; damaged reputation | Honest monthly investor updates; conservative forecasting | Founder | OPEN |
| **R-23** | Technical | Migration failure locks production DB | 5 | 1 | 5 | Alembic upgrade fails on production | Backup schedule (R-12); staged rollout; test in staging first | DevOps | OPEN — partial |
| **R-24** | Product | Feature request debt (Design Partners want features that fragment scope) | 3 | 4 | 12 | Partners each push different feature; scope creeps | Roadmap discipline (`09_PRODUCT_ROADMAP.md`); Not-Do list enforced; parking-lot for out-of-gate | Founder + PO | OPEN |
| **R-25** | Technical | Neo4j runtime becomes required despite ADR-108 offline | 3 | 1 | 3 | Requirement change forces graph queries | Currently controlled by ADR; if needed, revisit ADR + implement online | TL | OPEN — controls |
| **R-26** | Business | Local KSA competitor emerges with better ICP fit | 4 | 3 | 12 | Competitor with faster PMF captures Design Partners | Speed of Design Partner conversion; case studies published; positioning defensibility | Founder | OPEN |
| **R-27** | Business | International competitor (HubSpot / Salesforce / Zoho) adds Arabic-first + KSA-focused features | 4 | 2 | 8 | Big-vendor cross-sell into our target base | Depth in Saudi-specific master data + regulatory + HITL is defensible moat | Founder | OPEN |
| **R-28** | Financial | Real LLM cost per tenant higher than pricing model assumes | 3 | 3 | 9 | Cost tracking shows per-tenant SAR > pricing gross margin | Pricing model reconsidered; token budget per tenant; deterministic-first design | Founder + TL | OPEN — controls partial |
| **R-29** | Compliance | Grounded EvidencePack fails on real (non-test) tenant data (encoding / corner cases) | 4 | 2 | 8 | Real tenant data has different edge cases than test data | Phase 7-A capture-only rollout; PII regression suite; expand tests | TL + PO | OPEN |
| **R-30** | Business | Design Partners come from Founder's network, not repeatable | 3 | 4 | 12 | 3/3 wins from personal network → no cold outbound proof | Force at least 1/3 Design Partners from cold outbound | Founder | OPEN |

---

## Top-5 focus (highest risk-adjusted priority)

1. **R-01 (15)** — No paying customer within 6 months → Sprint 1 P0 focus on Design Partner conversion
2. **R-02 (15)** — LLM provider unavailable → Sprint 1 P0 item 8 (sign contract)
3. **R-03 (15)** — PDPL blocks Enterprise → Design architecture, pull-based execution
4. **R-08 (12)** — MD/ER production quality → Phase 7-A capture-only + safety validation
5. **R-07 (12)** — Design Partner churn → weekly check-ins + upfront success criteria

---

## Retired risks (none yet — this audit is fresh)

*After each risk-mitigation, move retired risks here with evidence link + retirement date.*

---

## Governance for this register

- **Update:** Every WBR (weekly)
- **Full audit:** Every MBR (monthly)
- **New risks:** captured within 24h of discovery, defer scoring to next WBR
- **Retirement:** requires evidence link + owner sign-off

---

*Risk register — 30 items, priority-ordered, honest, actionable.*
