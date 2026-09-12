# 02 — Product Brief — تعريف المنتج

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
