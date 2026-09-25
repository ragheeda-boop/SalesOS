# 19 — Risk Register
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

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
| **R-10** | Repo | ~~4,748 staged deletions on `fix/login-and-keys` merged accidentally~~ → **MITIGATED 2026-09-12** (`git reset HEAD -- .`; index == HEAD, 0 staged deletes). Residual LOW: 25 D / 37 M / 512 untracked need named-path triage; plain `git status` breaks on `engineering-os` submodule | 5 | 2 | 10→2 | `git commit -am` / `git add -A` from current branch state | Branch protection on master; named-path staging only | Founder | **CLOSED** |
| **R-11** | Provider | AI Copilot enabled to external tenants while DEV-only provider still active → **CONTROLLED 2026-09-12/13**: `feature_ai_copilot` default **False** (config.py:162), gated; flags laboratory-only; provider stays DEV-ONLY | 5 | 2 | 10→2 | `feature_ai_copilot=True` + real prospect uses production | Council gate on any `True` flip (18 §5); explicit env-var gate for external tenants | Founder + PO | **MITIGATED** |
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

## Google Maps source/provider gate — 2026-09-21

Current Google Maps terms prohibit scraping/extracting Maps content for use outside Maps and prohibit use of Maps Core Services for a listings/directory service or to create/augment an advertising product. Places API output also cannot be retained as a durable SalesOS lead dataset; the persistent place_id exception does not extend to company fields. The standalone business/google-maps-scraper-kit is therefore **not approved as a SalesOS lead source**, and its CSV/JSON output must not feed Master Data, Fact Review, or CRM. SalesOS already rejects google_maps as an Agent Reach research channel; a new explicit proposal-classifier regression locks that boundary. No Maps provider was called. Durable spend reservations have since been implemented and verified only on salesos_test; they remain unconfigured, so no provider can run. See [report 30](30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md) and [report 29](29_GOOGLE_MAPS_PROVIDER_GATE_2026-09-21.md). Phase 7 remains BLOCKED, production NOT APPROVED, and roadmap remains **46%** (52/113 last full census; not re-censused).


## Evidence relevance control update — 2026-09-21

The risk of attaching an unrelated value to valid Agent Reach evidence is reduced by a whole-phrase lexical gate. Residual risk remains: captured summaries can be inaccurate and lexical presence is not semantic verification. Keep cited-claim trust, human review, and no-auto-apply boundary. See report 31.
**File-specific update:** Highest risks are Phase 7 data promotion, dependency/toolchain integrity, provider credentials, backups/DR, SSO/Stripe and PDPL.


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
