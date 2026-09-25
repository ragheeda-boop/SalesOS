# 04 — Business Model — نموذج العمل
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Reality check:** لا يوجد Pricing model موقَّع، ولا نموذج Unit Economics معتمَد في المستودع. هذا الملف يقترح فرضيات مبنية على السوق السعودي والقدرة التقنية الفعلية، **ليس** حقائق موثَّقة داخل الكود.

**Evidence status:** أغلب الأرقام هنا **RECOMMENDATION / HYPOTHESIS**. لا `FACT` بدون وثيقة تعاقدية.

---

## 1. Monetization thesis / فرضية التسييل

**AR:** SalesOS يُباع كمنصة SaaS مؤسسية بترخيص سنوي للفريق (Team-based license)، على 3 مستويات، مع خدمات تفعيل مدفوعة في السنة الأولى.

**EN:** SalesOS monetizes as an annual, team-licensed B2B SaaS with 3 tiers plus paid onboarding/data services in Year 1.

Rationale from code:
- The billing module (`app/modules/billing/`) + Stripe integration + Alembic `c3a9f12d4e80_story_05_01_subscriptions_table.py` + `plan_entitlements` + `usage_meters` + `dunning_cases` scaffolding exist — SO the mechanics are ready, only pricing and product-market decisions are missing.

---

## 2. Pricing tiers — HYPOTHESIS

| Tier | الاسم / Name | Seats | Muhide access | Copilot | Studio (custom rules, prompts) | HITL Approval | Signal Marketplace | List price (SAR / year) | Notes |
|------|--------------|-------|---------------|---------|-------------------------------|---------------|--------------------|-------------------------|-------|
| Design Partner (pilot) | برنامج شركاء التصميم | 5 | ✔ subset | ✔ preview | Read-only | ✔ | 1 pack | **0** (barter for feedback + case-study rights) | 90-day pilot |
| Team (SMB) | فريق | up to 15 | ✔ full | ✔ | Basic | ✔ | 3 packs | **SAR 60,000** (~USD 16k) | Anchor, first paying tier |
| Business | أعمال | up to 50 | ✔ full + refresh | ✔ | Full Studio | ✔ | All packs + custom | **SAR 180,000** (~USD 48k) | Target enterprise SME |
| Enterprise | مؤسسة | 50+ | ✔ + private ingestion | ✔ + private model | Full Studio + SSO + Audit exports | ✔ + dedicated approver flows | All + priority + private packs | **from SAR 500,000** (~USD 133k) | Custom SLA + PDPL DPO |

**Add-ons (Year-1 professional services):**
- Muhide data-refresh + custom sources ingestion: SAR 100k–300k one-time
- Custom knowledge pack (new vertical): SAR 150k
- Prompt library authoring + AI policy setup: SAR 50k
- Onboarding + Studio configuration: SAR 40k

**Assumptions:**
- KSA SME B2B willingness-to-pay for premium sales-intel tools: SAR 3k–15k/seat/year is the market band (source: analogous CRM pricing benchmarks; no in-repo data)
- LLM cost per active seat/month at grounded usage: SAR 30–120 depending on provider — must be tracked via existing `LLMCostTracker`

---

## 3. Revenue model math (illustrative only)

| Year | # tenants | Mix (Team / Bus / Ent) | Blended ACV (SAR) | ARR (SAR) | Comments |
|------|-----------|-----------------------|-------------------|-----------|----------|
| Y1 (2027) | 3–5 | 3 Team, 1 Business | 84,000 | 336,000–420,000 | Design-partner→paying conversion |
| Y2 (2028) | 10–15 | 6 Team, 3 Business, 1 Ent | 145,000 | 1.45M–2.2M | First reference cases published |
| Y3 (2029) | 25–35 | 12 Team, 8 Business, 3 Ent | 175,000 | 4.4M–6.1M | GTM machine + Studio adoption |

**Not** a hockey-stick claim. Deliberately conservative — reflects that KSA B2B enterprise sales cycles are 3–9 months.

---

## 4. Cost model (rough)

### 4.1 Infrastructure (from `railway.json`, Vercel config, README stack list)

| Item | Est. monthly cost (USD) | Notes |
|------|-------------------------|-------|
| Railway (backend + celery-worker + celery-beat + Postgres + Redis + Neo4j) | 500–2,000 | Grows with tenant count and Neo4j-if-activated |
| Vercel (Next.js FE, region iad1) | 100–400 | Grows with traffic; PoP outside KSA |
| PostgreSQL storage/backups (managed) | 100–400 | Backups schedule pending |
| Meilisearch | 50–200 | Optional per config |
| Sentry / observability | 100–300 | Currently unset — must budget |
| LLM provider (post-signing) | 300–3,000 | Scale with active seats × usage × groundedness |
| **Total infra** | **1,150–6,300/mo** | ≈ SAR 52k–283k / year |

### 4.2 Human capital (evidence: `AGENTS.md` §10 STAR audit A-10 = solo architect)

**Current reality:** solo founder-engineer + occasional swarm agents (per DEC-107).
**Required for pilot ship + first paying customer:**
- 1 senior FE engineer (Next.js / React / Tailwind)
- 1 senior backend / data engineer (Python / FastAPI / SQLAlchemy / Alembic + KSA data)
- 1 part-time customer-success / Arabic-first
- 1 part-time PDPL / legal counsel (fractional)

Estimated monthly burn (Riyadh market, 2026–2027):
- Founder salary opportunity cost: SAR 30k–50k
- 2 FT senior engineers: SAR 40k–70k each = SAR 80k–140k
- Part-time CS: SAR 15k
- Legal fractional: SAR 5k–10k
- **Total human capital:** SAR 130k–215k/month = **SAR 1.56M–2.58M/year**

**Combined burn:** ≈ **SAR 1.6M–2.9M/year** to run Year 1 seriously.

### 4.3 Unit economics (per Team-tier customer, SAR 60k ACV)

| Line | SAR/year |
|------|----------|
| Gross revenue | 60,000 |
| Direct LLM cost (grounded, ~10 seats × 60 SAR/seat/mo × 12) | (7,200) |
| Direct hosting cost per tenant (share of ~SAR 150k infra ÷ 5 tenants) | (30,000) |
| **Gross margin (Y1)** | **~22,800 (38%)** |
| Support/onboarding cost (share) | (10,000) |
| **Contribution margin** | **~12,800 (21%)** |

**Implication:** Year-1 Team-tier is **NOT** unit-profitable. It becomes profitable only at 15+ tenants sharing infra, or when Business+Enterprise tiers cross-subsidize. This is normal for early SaaS but must be told honestly to investors.

---

## 5. Payment + billing rails — code reality

- **Stripe** integrated (`app/modules/billing/stripe_router.py` + Alembic `e5c1f34a6b02_story_05_02_stripe_webhook_ledger`)
- **Currency:** must be enabled for SAR + USD (Stripe supports)
- **Dunning:** Alembic `b8f4c67d9e15_story_05_04_dunning_cases` — 7-day grace default (`dunning_grace_days: 7`)
- **Portal invoices:** Alembic `f6d2a45b7c03_story_05_02_portal_invoices_catalog`
- **Plan entitlements:** enforced when `entitlement_enforcement_enabled: True` (default)
- **Usage meters:** enforced when `quota_enforcement_enabled: True` (default)
- **Stripe live keys:** empty by default (fail-closed 503). Must be provisioned in Railway env before first paid tenant.

**Verdict:** billing spine is **build validated**. Only pricing setup + Stripe live keys + Terms of Service + legal-review remain.

---

## 6. Contracting / commercial legal (missing)

Not found in-repo:
- Master Services Agreement (MSA) template
- Data Processing Agreement (DPA) template — REQUIRED for PDPL
- Order Form template
- SLA document (uptime commitments, credit policy)
- Terms of Service (ToS) for platform use
- Acceptable Use Policy

**Action:** engage KSA-qualified legal counsel; DO NOT sign first paying customer without at least MSA + DPA + Order Form + SLA-lite.

---

## 7. Risks to business model

| Risk | Severity | Note |
|------|----------|------|
| No pricing signed → founder guesses in-meeting | HIGH | Fix in Q4 2026 |
| Enterprise cycles longer than runway | HIGH | Design partners + Team tier prove faster |
| Muhide data seen as one-time deliverable, not living service | MEDIUM | Add periodic refresh add-on; sell Muhide-as-a-Service later |
| KSA govt customer preference for on-prem / VPC | MEDIUM | Enterprise tier can include VPC deployment (K8s manifests exist but quarantined per DEC-149) |
| LLM cost surge kills gross margin | MEDIUM | Cost tracker + budget enforcement already landed |
| Copilot hallucination case in production | HIGH | Grounded discipline + HITL + Governance Audit mitigate |
| Data breach / tenant leak | HIGH | RLS strict, no external audit yet — schedule pentest |

---

## 8. What "sellable today" would require (honest checklist)

- [ ] Signed pricing tiers (0/4)
- [ ] Stripe live keys provisioned
- [ ] MSA + DPA + Order Form + ToS + SLA-lite drafted and reviewed
- [ ] At least 1 designed reference customer LOI
- [ ] OAuth staging setup (Google Cloud Console)
- [ ] Backup schedule enabled
- [ ] Production LLM contract signed
- [ ] AI_HONESTY.md reconciled (either flag=False or PRC-signed True)
- [ ] Phase 7 human review completed (or defensible sample)
- [ ] External pentest (or SOC2 Type I evidence)
- [ ] Public status page (uptime commitment)
- [ ] Customer support channel (email + response-time commitment)

**Current:** 0/12. Realistic Q4 2026 target: 8/12.

---

*Business model — hypothesis-grounded. See `05_CUSTOMER_SEGMENTATION.md` for who to sell to, `07_GTM_STRATEGY.md` for how to reach them, and `08_SALES_PLAYBOOK.md` for how to close them.*
**File-specific update:** Commercial claims must not imply GA readiness while Stripe, SSO, PDPL and production operations remain open.


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
