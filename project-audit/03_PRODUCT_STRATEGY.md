# 03 — Product Strategy — استراتيجية المنتج
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Purpose:** أين نأخذ SalesOS في 12 شهراً، بأدلة من الكود الفعلي وأصول البيانات، وليس بتمنيات.

---

## 1. المبدأ الحاكم / Strategic principle

**AR:** انتقلوا من "بناء ميزات" إلى "إثبات تبنِّي" — كل حركة منتج قادمة تحرك واحداً من رقمين فقط: **عدد المستأجرين المدفوعين النشطين أسبوعياً** و**عدد التوصيات AI المُوافق عليها بشرياً في الأسبوع**.

**EN:** Move from "shipping features" to "proving adoption." Every product move over the next 12 months must move exactly one of two numbers: **Paying Weekly Active Tenants** and **Human-Approved AI Recommendations per week**.

Reason from evidence: the codebase is already broad (37 modules, 40+18 domain packages, 24 nav items). It is **not** feature-poor — it is **customer-poor**.

---

## 2. الاستراتيجية في ثلاث طبقات / 3-layer strategy

### Layer 1 — Consolidate (Q4 2026, 90 days)

**Goal:** Turn the CLOSED-on-paper product into ONE working Saudi B2B pilot on real data with one design-partner customer.

**Non-negotiables:**
1. ~~Reconcile `feature_ai_copilot` / `AI_HONESTY.md` / README — one honest posture, sign it~~ → flag reconciled to **False** 2026-09-12/13 (config.py:162, 12 test files/15 asserts `is False`, 101/101 Docker PASS, AI_HONESTY aligned); remaining = rewrite `README.md` Domains table.
2. Sign a production LLM contract (OpenAI Enterprise / Azure OpenAI / hosted-in-KSA) — kill AI Horde in production paths
3. Enable Railway managed backup schedule (row 3b) — DR cannot be BLOCKED-HUMAN in production
4. ~~Repair `fix/login-and-keys` git working tree (4,748 staged deletions)~~ → **index UNPOISONED 2026-09-12** (`git reset HEAD -- .`; 0 staged deletes); remaining = named-path triage of 25 D / 37 M / 512 untracked; never `git add -A`.
5. Complete OAuth staging (Google Cloud Console) — SSO cannot be blocked at pilot start
6. Cut FE scope to v3 shell only — deprecate `/(dashboard)/*` routes visibly
7. **Design-partner pilot** — sign one Saudi B2B customer (BD or investment team) on a 90-day evidence-based pilot with real Muhide subset

**Definition of Done:** one named tenant with real activity + at least one Approved AI recommendation per week + a case study draft.

### Layer 2 — Prove (Q1–Q2 2027, 180 days)

**Goal:** From 1 design partner → 3 paying pilots → first repeatable pricing.

- Deliver `Muhide production ingestion` (with human review of 54,185 candidates completed as paid workstream)
- Ship Sales Playbook v1 (documented in `08_SALES_PLAYBOOK.md`)
- Publish first case study + reference (Design Partner #1)
- Convert Design Partner #1 to paying customer at anchor price
- Add Design Partners #2, #3
- SOC2 Type I evidence pack (leverage STORY-14-05)
- External pentest (residual open per `FINAL_GO_NOGO_ASSESSMENT.md`)
- Data Processing Agreement (DPA) template + Saudi PDPL alignment doc

### Layer 3 — Scale (Q3–Q4 2027)

- 10 paying tenants at ARR mixed anchor + SMB tier
- Signal Marketplace expansion beyond the 3 shipped knowledge packs (construction, healthcare, financial services) — add: government/e-gov, education, retail, real-estate, logistics, energy
- Formal Saudi Data-Residency posture (`ADR-0107` operationalized in region)
- Vertical modules productized (e.g., **SalesOS for GovTech Suppliers**, **SalesOS for VC Deal Flow**)
- Consider (only then) hiring beyond founder + minimal engineering — until then, do NOT scale team faster than customers

---

## 3. Product-Market-Fit Hypothesis (explicit)

**Hypothesis:**
> Saudi B2B business-development teams (5–50 seat orgs) will pay **SAR 50k–200k/year per team** for a bilingual, evidence-grounded, HITL-controlled sales-intelligence platform that includes trusted Saudi master data + Copilot + audit-safe AI trail, provided they trust the data hygiene and the AI does not hallucinate.

**Falsification:** If, after 3 design partners over 6 months, none convert to paid at anchor price ≥ SAR 50k/year, hypothesis is invalidated → pivot required (options: (a) become pure Master-Data-as-a-Service, (b) become AI-Copilot-add-on for existing CRMs, (c) sell to Saudi government-services integrators as embedded engine).

---

## 4. What we optimize FOR

Ordered priority (top wins in every trade-off):
1. **Evidence over polish** — never ship an AI answer without cited source
2. **Trust over speed** — never break tenant isolation; never merge without human decision
3. **Depth over breadth** — Saudi-specific > global-generic; local moat > mass appeal
4. **Human-in-loop over automation** — every write requires named approver
5. **Design partner intimacy over marketing** — 3 loved customers > 30 curious ones

## What we DE-prioritize

- Mobile app (P4 per Product Bible — keep parked)
- Multi-language beyond AR/EN
- Non-Saudi Middle East expansion until KSA is proven
- Vertical microservice architecture (K8s quarantined per DEC-149; Railway is enough)
- Any AuditOS / DecisionOS / LocalContentOS product surface

---

## 5. Strategic risk × mitigation

| Risk | Mitigation |
|------|------------|
| Founder burn-out (solo architect per STAR audit A-10) | Sign design partner first, hire 1 senior FE + 1 senior data engineer only after first paying customer |
| LLM cost blow-up | ADR-102 F2 cost-tracking + budget enforcement already landed; keep enforcement ON |
| Data-provider dependency | Muhide is one-time-imported dataset, not a live provider; own it in-house |
| Regulatory: PDPL / NCA / SAMA | Bring in KSA privacy counsel before first paying customer; document DPO role |
| Competition from Salesforce/HubSpot bilingual expansion | Speed to depth on Saudi CR + gov data + Arabic UX is our moat — protect it |
| Neo4j governance gap (deployed but offline) | Either activate v2.0 formally, or remove from Railway to close ADR-108 governance drift |
| Repository fragmentation (dual FE shells, nested duplicates) | 2-week hygiene sprint before next design partner |

---

## 6. Portfolio management — what stays, what parks

**KEEP + INVEST:**
- Product Core (all 9 areas)
- Master Data + Entity Resolution + Phase 6/7 pipeline (biggest moat)
- Copilot **grounded** path (not auto-execute)
- HITL ApprovalService
- Tenant Studio (Studio-mode features like Prompt Library, Scoring Rules, Territories, Permissions) — these enable enterprise sale
- Communication Hub (Gmail/Calendar) — activity data feed
- Signal Marketplace — 3 verticals shipped, keep and extend

**PARK (freeze work; do not delete):**
- GTM Intelligence 11-story pack (`icp_router`, `market_sizing`, `lead_discovery`, `enrichment`, `verification`, `lookalike`, `website_intelligence`, `outreach`, `sequencing`) — heavy scaffolding, low validated demand; defrost after first paying tenant proves the base workflow
- Marketplace listings + Employee 360 — narrow scope for now
- Neo4j Knowledge Graph — ADR-108 offline; keep offline until v2 signal
- Multi-region DR — single-region acceptable at pilot scale

**RETIRE / DEPRECATE (visibly mark, do not delete):**
- UBOM domain (already DEPRECATED per Phase 1)
- Legacy `(dashboard)` FE shell (78 pages) — put "legacy" banner and reroute to v3
- `frontend/packages/platform/decision/` STUB — keep as history; do not import
- AI Horde provider in production paths — hard-remove after real LLM contract

---

## 7. Public narrative for the next 12 months

**Q4 2026:** "SalesOS is running its first Saudi design partnership on real 296,746-company data — with evidence-grounded, human-approved AI."

**Q1 2027:** "SalesOS has 3 paying pilots in KSA. First reference customer. Muhide production ingestion complete."

**Q2 2027:** "SalesOS is Saudi Arabia's first grounded-AI sales intelligence platform with SOC2 Type I + external pentest + PDPL alignment."

**Q3 2027:** "SalesOS is the trusted sales-intelligence backbone for Saudi B2B, integrated with Gmail/Calendar/Odoo/Notion, priced per team."

**Q4 2027:** "SalesOS is expanding into vertical editions (GovTech Suppliers, VC Deal Flow), with SAR X million ARR run-rate and 10 named customers."

---

## 8. Explicit non-goals — 2026-2027

- No B2C surface
- No open marketplace (developers building on SalesOS) until 10 tenants
- No mobile-native app
- No non-Saudi geographic expansion
- No AuditOS/DecisionOS/LocalContentOS product launches
- No public LLM chat mode
- No agentic auto-execute mode (always HITL per ADR-113/115)

---

## 9. Final principle — the founder's promise

> **"We will not ship what we cannot prove. We will not sell what we would not use. We will not automate what a human should decide."**

This is already the operating principle in `AGENTS.md` and `AI_HONESTY.md`. It is genuinely differentiated and MUST become the product's public voice.

---

*Strategy — evidence-grounded. See `06_MVP_SCOPE.md` for exact scope cut and `09_PRODUCT_ROADMAP.md` for calendar.*
**File-specific update:** Strategy remains conditional on closing data trust, staging proof and operating controls before commercial scale.


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
