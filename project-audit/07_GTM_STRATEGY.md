# 07 — GTM Strategy — استراتيجية الوصول للسوق
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Reality check:** لا يوجد GTM موثَّق في المستودع اليوم. هذا الملف يقترح خطة قابلة للتنفيذ مبنية على قدرات المنتج الحقيقية والسوق السعودي — **RECOMMENDATION**، ليست حقائق موقَّعة.

---

## 1. GTM Motion — Founder-Led Design-Partner First

**AR:** لا Product-Led Growth. لا Marketing-Led. لا Channel-Led. الحركة الوحيدة التي تنجح في هذه المرحلة: **مؤسس يبني علاقة مباشرة مع 5 قادة مبيعات سعوديين ويقدم أطرَ تجريبية 90 يوماً بأدلة، ثم يحوّلهم إلى مدفوعين بمرجعية علنية.**

**EN:** Not PLG. Not marketing-led. Not channel-led yet. The **only** motion that works at this stage: **founder-direct outbound to 5 named Saudi sales leaders, offer 90-day evidence-based pilots, convert to paid + reference.**

---

## 2. Motion timeline

| Phase | Duration | Motion | Team touch |
|-------|----------|--------|------------|
| Design Partner | Q4 2026 (90 days) | Founder outbound → 3 signed pilots | Founder only |
| First Paid | Q1 2027 (90 days) | Convert 1–2 pilots → paid Team tier | Founder + 1 fractional CS |
| Reference-Led | Q2 2027 (90 days) | Publish 2 case studies → warm outbound to lookalikes | Founder + 1 CS + 1 sales generalist |
| Repeatable | Q3–Q4 2027 | First hire dedicated sales; template playbook | Founder + Head of Sales + 2 AEs |

---

## 3. Target list — Design Partners (build first)

**Selection criteria:**
- KSA-registered legal entity
- 30–200 employees
- Active B2B sales function ≥ 5 seats
- Vertical ∈ {construction supply, healthcare services, financial services} — matches shipped signal packs
- Founder or Head of Sales reachable via warm intro or Saudi B2B network
- Willing to sign a 90-day pilot MOU with case-study rights

**Suggested prospecting sources:**
- Founder's own KSA network + LinkedIn
- Riyadh, Jeddah, DMM chambers of commerce member lists
- Saudi VC portfolio companies (introduction via investors)
- MISK / Founder / Monsha'at ecosystem partners
- Vision 2030 program vendor lists (RCJY / RCU / NEOM sub-vendors)
- Sales-club events (Sales Force KSA, RiyadhSales meetup — verify current groups)

**Target list size:** 30 named prospects → 10 first-conversations → 5 pilot pitches → 3 signed design partnerships.

---

## 4. Value proposition per persona (short-form)

### To BD Director
> "توفّر عليك 3 ساعات يومياً في البحث عن الشركات السعودية. كل معلومة معها مصدر. توصيات ذكية تُوافق عليها أنت — لا يقرر AI نيابةً عنك."

### To Sales Manager
> "ترى صحة كل صفقة مبنيّة على بيانات حقيقية، لا على تخمينات مندوبك. توقّع Commit / Best Case / Pipeline / Risk من واقع الأنشطة الفعلية."

### To Investment Analyst
> "ملف شركة سعودية ذكي في دقائق — CR، النشاط، الحجم، الإشارات، القرابات الاستثمارية — مع تسلسل مصادر يمكنك عرضه على لجنة الاستثمار."

### To Executive
> "أول لوحة قيادة مبيعات سعودية بالعربية، بمستوى ذكاء أعمال يستحق قرار المجلس، بدون اعتماد على أدوات عالمية لا تفهم السوق."

---

## 5. Positioning against alternatives

| Alternative | Their strength | Our angle |
|-------------|---------------|-----------|
| **Excel + WhatsApp** | Free, ubiquitous | "Excel is your memory today. SalesOS is your memory tomorrow — with evidence." |
| **HubSpot / Salesforce** | Big brand, complete features | "Great CRMs. Zero Saudi data. Weak Arabic. Chatbot AI without sources." |
| **Bloomberg / Crunchbase** | Deep data | "Global. English-only. Too expensive per seat. No CRM, no Copilot, no signals." |
| **LinkedIn Sales Navigator** | Network reach | "No government data. No Arabic-first. No entity resolution. No forecast." |
| **Zaubee / Fenq** | Local price | "Local, but shallow — no AI, no evidence, no HITL." |
| **In-house build** | Custom | "You'll spend 12–18 months + SAR 3M+. We built it. Rent it for 60k/year." |

---

## 6. Content / Trust building (first 90 days)

**Deliver, in order (before publishing marketing):**
1. **One evidence-based blog post:** "Why we refuse to let AI hallucinate on Saudi sales data" — explain the grounded EvidencePack pattern
2. **One product tour video (bilingual):** 8-minute walkthrough of `/v3/companies` + `/v3/sales-dashboard` + `/v3/approvals`
3. **One case-study template** (empty; to be filled after Design Partner #1)
4. **One data sheet (1 page):** what SalesOS is, what it isn't
5. **One PDPL alignment statement** (draft)
6. **One security whitepaper draft** (RLS, salesos_app role, HITL, JWT RS256, audit_logs)

**Do NOT publish before at least 1 case study exists.**

---

## 7. Channels — sequenced

### Q4 2026: Design Partner acquisition
- Founder LinkedIn outbound
- Warm intros via KSA VCs (MISK / STV / Sanabil-adjacent portfolio)
- 1:1 coffee at Riyadh SaaS founder circles

### Q1 2027: First paying customer
- Design-partner reference intros
- Content: 2 blog posts + 1 case study + 1 webinar in Arabic
- Attend 1 vertical event (Saudi Construction Expo or Global Health Exhibition Riyadh)

### Q2–Q3 2027: Repeatable
- Ecosystem partnerships (Riyadh Chamber, Saudi CIT / SDAIA if suitable)
- Referral program for existing paying tenants
- Attend / speak at 2 events

### DO NOT DO YET
- Paid ads (Google / LinkedIn) — burns cash without PMF signal
- Cold outbound at scale — reputation risk in KSA market
- Reseller channel — premature
- Ecosystem app-store presence — premature

---

## 8. Sales enablement (build in parallel)

- Discovery deck (bilingual, 10 slides)
- Demo script (v3 walkthrough + Copilot-with-evidence live demo + HITL flow)
- Objection-handling FAQ (see `08_SALES_PLAYBOOK.md`)
- Reference architecture 1-pager
- Security FAQ 1-pager
- Pricing tier explanation 1-pager
- Onboarding runbook (for post-sale first 30 days)

---

## 9. Marketing spend guidance

**Y1 (2026–2027):**
- Content + design + video: SAR 50k
- Event participation (2 events): SAR 40k
- LinkedIn Sales Navigator + tooling: SAR 15k
- **Total marketing:** SAR 100k–120k (< 5% of Y1 burn)

**Do NOT:**
- Pay for programmatic ads
- Hire a marketing agency
- Buy an inflated logo
- Attend expensive conferences without a customer meeting on calendar

---

## 10. Success metrics for GTM (leading indicators)

| Metric | Target (Q4 2026) | Target (Q2 2027) |
|--------|------------------|------------------|
| Named prospects contacted | 30 | 100 |
| First-conversation booked | 10 | 40 |
| Product tour delivered | 5 | 20 |
| Design Partner MOUs signed | 3 | maintained + 3 paid |
| Paid tenants | 0 | 3 |
| ARR (SAR) | 0 | 300k |
| Case studies published | 0 | 2 |
| NPS (design partners) | measurable | ≥ 40 |
| First tenant referral | — | ≥ 1 |

---

## 11. Sales cycle assumption

For **Team tier** (SAR 60k):
- Discovery → 1st demo: 1–2 weeks
- 1st demo → tech / security review: 2–4 weeks
- Security → contract negotiation: 3–6 weeks
- Contract → onboarding: 1–2 weeks
- **Total cycle:** 7–14 weeks

For **Business tier** (SAR 180k): +50% (10–21 weeks).
For **Enterprise** (SAR 500k+): 4–9 months.

**Implication:** with 90-day design-partner cadence, first paid contract lands earliest Q2 2027 (assuming design partnership begins Q4 2026).

---

*GTM — RECOMMENDATION-labeled. See `08_SALES_PLAYBOOK.md` for how to actually close.*
**File-specific update:** GTM execution remains pilot-first until the staging connector and production approval sequence closes.


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
