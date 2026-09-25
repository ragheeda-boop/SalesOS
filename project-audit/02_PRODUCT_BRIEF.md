# 02 — Product Brief — تعريف المنتج
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Purpose:** ما هو SalesOS بلغة يفهمها المؤسس، مجلس الإدارة، المستثمر، ومدير المبيعات — بدون تسويق زائد وبدون تصغير.

---

## 1. الجملة الواحدة / One-line pitch

**AR (المدعوم بالأدلة):**
> **SalesOS منصة ذكاء مبيعات سعودية أوّلاً، ثنائية اللغة، تُحوِّل بيانات الشركات السعودية إلى قرارات مبيعات موثَّقة، مع مسار عمل بشري في القرار (Human-in-the-loop).**

**EN (evidence-grounded):**
> **SalesOS is a Saudi-first, bilingual (AR/EN) B2B sales intelligence platform that turns Saudi company data into evidence-cited sales decisions, with a strict human-in-the-loop control plane over every AI action.**

مصدر: `PRODUCT_BIBLE.md` §Vision + `SALESOS_MASTER_CLOSURE_SEQUENCE.md` + `AI_HONESTY.md`.

---

## 2. المشكلة التي نحلّها فعلاً / The real problem

**AR:** فرق تطوير الأعمال والمبيعات والاستثمار في السوق السعودي:
- تُهدر 3–4 ساعات يومياً في البحث اليدوي عن الشركات المستهدفة (وزارة التجارة، المنشآت، الغرف التجارية، هيئة السوق المالية، بلدي، تقييم، الأنظمة الحكومية) — لا يوجد **مصدر واحد موحَّد**.
- تعتمد على Excel وملفات شخصية لإدارة آلاف الشركات — **لا يوجد ذاكرة تنظيمية**.
- إذا استخدموا أدوات عالمية (Bloomberg / Crunchbase / LinkedIn Sales Nav / HubSpot)، فإنها **لا تدعم العربية جيداً**، **لا تحتوي على بيانات حكومية سعودية**، **لا تفهم السياق السعودي (CR / MENA / اللغة العربية / أسماء الجهات)**.
- عند اعتمادها على AI عام (ChatGPT مثلاً)، تحصل على إجابات **بلا مصدر ولا سياق**، وتقع في مشكلات هلوسة (hallucination) لا تحتملها بيانات مالية أو استثمارية.

مصدر: `PRODUCT_BIBLE.md` §"لماذا يوجد SalesOS" + `AGENTS.md` §36 (CR normalization edge cases 15,178 valid / 4,202 suspicious).

---

## 3. ما هو المنتج فعلاً — three lenses

### 3.1 عدسة المستخدم / User lens

| المستخدم | يستخدم SalesOS ليفعل ماذا فعلاً |
|----------|-------------------------------|
| مسؤول تطوير الأعمال | يفتح `/v3/companies`، يبحث عن شركة سعودية، يرى ملف Company 360 (CR، النشاط، الحجم، العلاقات) + إشارات محدَّثة (تراخيص/مناقصات/تغيرات) + توصية عمل ذات مصدر |
| مدير المبيعات | يفتح `/v3/crm` أو `/v3/sales-dashboard`، يرى صحة صفقاته، يفتح `/v3/my-day` لطابور اليوم، يقبل/يرفض توصيات Copilot عبر `/v3/approvals` |
| المحلل الاستثماري | يستخدم Company 360 + Signal Marketplace + Relationships + Effectiveness لبناء أطروحة استثمار مع مسار مصادر واضح |
| المسؤول التنفيذي | يفتح `/v3/analytics` أو `/v3/effectiveness` — يرى Cohorts / Lift / Funnel / Pipeline بدل تقارير Excel |
| مسؤول الاستيراد / البيانات | يفتح `/v3/data/*` — يُدير Master Data، مراجعة الازدواج (Review Queue)، Entity Resolution، Imports |
| مسؤول إدارة الأنظمة | يفتح `/v3/admin` — يُدير التبعية، الأدوار، الأدلة، حالة الرحلات |

### 3.2 عدسة الكود / Engineering lens (proven)

37 backend module + 18 domain package + 40 v3 page + 78 legacy dashboard page + 20 top-level router + 109 alembic migration + 22 platform signals + 13 grounded Copilot agents + shared EvidencePack loader + HITL ApprovalService + AIGovernanceAudit + `salesos_app` RLS role + persistent DLQ.

**Real, running, tested. Not fiction.**

### 3.3 عدسة التسويق الصادقة / Honest marketing lens

- **YES:** "Saudi-first bilingual B2B commercial OS with evidence-grounded AI copilot in preview mode"
- **YES:** "Full Product-Core CRM stack (Companies, Contacts, Deals, Pipeline, Activities, Revenue, Proposals, Reviews, Approvals)"
- **YES:** "296,746-company Saudi Master Data foundation with government-ID-safe deduplication policy" — *when Phase 7 completes*
- **NO:** "AI-native GA production" (per `AI_HONESTY.md`)
- **NO:** "Autonomous Sales Agent" (12-month vision, zero code today)
- **NO:** "Multi-product platform" (only SalesOS exists)

---

## 4. المميز التنافسي الفعلي / Real, defensible moats

1. **السياق السعودي في العمق** — CR normalization (`entity_resolution/resolution_policy.py` `normalize_cr` handles `;` `|` `,` `/` `؛` `،` separators + RTL control chars + short-CR classification (`SAFE` / `SUSPICIOUS_SHORT` / `SUSPICIOUS_MULTI` / `AMBIGUOUS`)) — this is **not** in HubSpot, not in Salesforce, not in Crunchbase.
2. **ثنائية اللغة كأصل** — Arabic-first UX + Arabic normalized industry map + Copilot outputs بالعربية. Real Arabic handling, not machine translation.
3. **Evidence-first AI** — every Copilot answer cites `[E1]…[Ei]` items from a bounded EvidencePack; agents refuse to hallucinate. This is **very rare** in commercial AI products; typical vendors ship "trust me" LLM outputs.
4. **Government-ID hard-veto merges** — same-name + different-CR → SEPARATE always (per PO decision 2026-09-09). This is a **real Saudi regulatory hygiene** feature that a Silicon Valley CRM will not build.
5. **Tenant-isolation as first-class** — dedicated `salesos_app` RLS-respecting DB role + fail-closed empty-password in prod + RLS on `signal_events`, `rag_documents`, `icp_profiles`, `commercial_events` — this is enterprise-grade posture.
6. **Bilateral engineering-governance culture** — `SALESOS_MASTER_CLOSURE_SEQUENCE.md` (build → prove → close gate → advance) is best-in-class governance; investors will notice.

---

## 5. أضعف الحلقات / Weakest links (must be told honestly)

1. **زبون واحد حقيقي مفقود** — no live paying tenant proven in this audit. This is the single most important gap.
2. **LLM provider dev-only** — production AI depends on signing OpenAI Enterprise / Azure OpenAI / Anthropic / hosted-in-KSA equivalent.
3. **Muhide data خارج الإنتاج** — 296,746-company asset sits in `salesos_test`; production `salesos` has 141,221 rows (older population). Uplift path blocked by Phase 7 human review.
4. **Backup schedule off** — Railway managed backup not enabled = real DR risk today.
5. **Marketing overclaim in README** — must be corrected to match `AI_HONESTY.md`.
6. **Dual FE shell** — v3 vs legacy dashboard both routable; product decision needed.

---

## 6. Positioning statement (draft, board-ready)

> **For** Saudi Arabian B2B sales, business-development, and investment teams
> **Who** waste hours per day reconciling company data from fragmented government + commercial sources and cannot trust generic AI tools with regulated business decisions,
> **SalesOS** is a bilingual, Saudi-first sales-intelligence platform
> **That** turns Saudi company data into evidence-cited, human-approved sales decisions
> **Unlike** Bloomberg (too generic + English-only + $$$$) / Crunchbase (shallow on Saudi) / LinkedIn Sales Navigator (no gov data, weak Arabic) / HubSpot (no intelligence, weak Arabic) / Salesforce (US-first, no Saudi CR logic),
> **SalesOS** is built on 296,746-company Saudi master data with government-ID-safe entity resolution, tenant-isolated RLS, and a **grounded, HITL-controlled AI Copilot that refuses to hallucinate**.

---

## 7. Definition of the product's **north star**

**Sole primary metric candidate:**
> **Number of paying tenants where at least one AI recommendation was Approved via HITL and led to a booked sales activity per week.**

Rationale: this metric collapses tech + product + market + trust into one number. It cannot be gamed by demo mode, cannot be inflated by seed data, and cannot be reached without every phase functioning.

Runner-ups (secondary):
- **Time-to-Insight** (open app → first evidence-cited insight): target < 30s (per Product Bible)
- **Groundedness score** on Copilot outputs (already instrumented per Phase 3): target ≥ 0.85
- **Weekly Active Reviewers** in Master Data Review Queue: target = staffed FTE ≥ 1

---

## 8. What SalesOS is NOT

- Not a chatbot
- Not a generic CRM (Salesforce / HubSpot substitute)
- Not a marketing automation platform
- Not a customer-success helpdesk
- Not a payment or invoicing platform (Stripe integrations exist for billing, not for commerce)
- Not an AuditOS / DecisionOS / LocalContentOS product
- Not a production-GA AI copilot (yet)
- Not sellable as pure SaaS today (see `04_BUSINESS_MODEL.md`)

---

## 9. Product one-pager (Arabic — sharable with founders / partners)

> **SalesOS — ذكاء المبيعات السعودي**
>
> منصة تُحوّل بيانات 296,746 شركة سعودية إلى قرارات بيع موثَّقة، بالعربية والإنجليزية، مع إنسان في المسار على كل توصية.
>
> **لمن؟** فرق تطوير الأعمال، المبيعات، والاستثمار في السوق السعودي والخليج.
>
> **ماذا يميّزها؟** بيانات حكومية سعودية + معيار CR سعودي دقيق (لا دمج بلا برهان) + Copilot لا يُهلوس (كل إجابة معها مصدر) + عزل مستأجرين بمستوى مؤسسي.
>
> **الحالة:** جاهز للتجربة التجريبية مع 1–3 شركاء أوائل مختارين — ليست منصة SaaS مفتوحة بعد.
>
> **الخطوة التالية:** اتفاقية تجريب مع شركة سعودية واحدة على بيانات حقيقية، مقابل ملاحظات + دراسة حالة.

---

*Product brief — evidence anchored. See `03_PRODUCT_STRATEGY.md` for where to take it next.*
**File-specific update:** Product narrative remains valid; current implementation must be read with the 75% code-scope and production gate status.


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
