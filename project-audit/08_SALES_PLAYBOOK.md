# 08 — Sales Playbook — كتاب المبيعات التنفيذي

**Purpose:** كيف نبيع SalesOS بالفعل — من discovery إلى close، بدون تضليل، وبنبرة تتفق مع `AI_HONESTY.md`.

**Buying persona (primary):** Head of Sales / Head of BD in a Saudi B2B SME. Secondary: VP Sales / CEO of SMB, Head of Deal Flow at a VC.

---

## 1. Discovery — الأسئلة الحاسمة

Ask these, in this order. Do not demo before you've asked them.

1. **كم شركة يبحث عنها فريقك أسبوعياً؟ في أي قطاع؟**
   (Signals ICP size + vertical → matches shipped signal packs?)

2. **ما مصدر بيانات الشركات لديك اليوم؟ (Excel / وزارة التجارة / أدوات دولية / بحث يدوي؟)**
   (Signals pain scope + willingness to pay)

3. **كيف تخزن نتائج البحث والتفاعلات مع العملاء الحاليين؟ (CRM / Excel / Notion / بريد؟)**
   (Signals CRM incumbency + migration difficulty)

4. **هل جربتم أدوات AI مثل ChatGPT؟ ما شعوركم عندما تعطي معلومة خاطئة؟**
   (Opens the door to grounded/HITL differentiation)

5. **من يوقّع على شراء أدوات SaaS في شركتك؟ وما ميزانية 12 شهر لأدوات فريق المبيعات؟**
   (Qualify decision maker + budget)

6. **هل عندك مسؤول قانوني/امتثال يراجع اتفاقيات معالجة البيانات (DPA)؟**
   (Signals PDPL sensitivity + Enterprise-tier fit)

**Qualification score (out of 6):**
- 5–6 → HIGH fit (proceed to demo)
- 3–4 → MEDIUM (nurture; educate on PDPL/AI honesty)
- 0–2 → LOW (not now; add to nurture email list)

---

## 2. Demo — 25-minute script

### Minute 0–2: Frame

> "SalesOS يفهم الشركات السعودية بلغتك، ويعطيك توصيات بيع دائماً معها مصدر — لكن **أنت** الذي تقرر."

Set expectation: this is not a chatbot demo. Show the **evidence trail** first, product second.

### Minute 2–8: `/v3/companies` + Company 360

- Search by Arabic name → open a real Muhide company profile
- Show CR + normalized industry + segment + owner_id
- Click Company 360 → show Activities, Timeline, Signals, Effectiveness cohort
- Say honestly: "This data is from our Muhide Saudi master data — 296,746 companies. Anything not signed off by our data steward gets flagged for human review, never auto-merged."

### Minute 8–14: `/v3/crm` + deal + `/v3/my-day`

- Open a deal → show pipeline stage, qualification, activities
- Open `/v3/my-day` → show today's queue

### Minute 14–20: Copilot with Evidence

- Ask Copilot "Summarize this account's health"
- Copilot returns 3 evidence-cited sentences with `[E1] [E2] [E3]` clickable links
- Click through — show real source items
- Now ask: "Recommend a next action"
- Copilot returns → **creates an ApprovalRequest** in `/v3/approvals`
- Say honestly: "Copilot is opt-in per tenant. Cannot execute. Always human-approved. In today's demo, our LLM provider is a dev-only stack — for your pilot we sign OpenAI Enterprise (or equivalent) before your data touches it."

### Minute 20–23: Master Data + HITL

- Open `/v3/data/review-queue`
- Show 2,661 fuzzy pairs pending human decision (P3), never auto-merged
- Show government-ID veto policy in action
- Say: "This is our defensive edge. No global CRM does this."

### Minute 23–25: Q&A + next step

> "خطوتنا التالية إن كانت هذه الأداة تستحق: نوقّع اتفاقية شريك تصميم 90 يوماً بلا مقابل مالي، على شريحة مختارة من بياناتك — ونشترط منك ملاحظات صريحة + الحق في نشر دراسة حالة إذا نجحت التجربة."

---

## 3. Objection handling — الاعتراضات الشائعة

| Objection | Honest response |
|-----------|-----------------|
| "لدينا HubSpot أصلاً." | "ممتاز. SalesOS ليس بديلاً لـHubSpot، بل طبقة ذكاء فوقه. Comm Hub يقرأ بريدك في Gmail ويربطه بشركاتك السعودية — HubSpot لا يفعل ذلك." |
| "ChatGPT يكفينا." | "ChatGPT قد يعطيك اسم شركة غير موجود، أو رقم CR مخترع. Copilot لدينا يرفض الرد بدون مصدر معتمَد. الفرق: أنت لا تخسر صفقة بسبب هلوسة." |
| "بياناتنا حساسة، لا يمكن أن تخرج من المملكة." | "PDPL هو أولوية عندنا. Enterprise tier يشمل نشر VPC داخل المملكة (Terraform manifests جاهزة). في مرحلة Team tier نستخدم Railway + Vercel، والبيانات محفوظة مع RLS صارم — نشرح تفاصيل الأمان في مراجعة تقنية." |
| "الذكاء الاصطناعي لا يمكن الوثوق به قانونياً." | "لهذا كل توصية AI في SalesOS تمر بموافقة بشرية عبر HITL Approval. يوجد audit trail كامل يبيّن من وافق ومتى ولماذا. هذا يتفق مع سياسات SAMA الحديثة." |
| "كم ستستغرق التركيبة (onboarding)؟" | "أسبوع لـ Team tier. ندعم SSO عبر Google Workspace. اتصال Gmail عبر OAuth. استيراد شركاتك من ملف Excel لمرة واحدة، ثم البيانات المرجعية تأتي من Muhide." |
| "لماذا يجب أن نصدّقكم؟" | "لأننا لا نعدك بشيء لم نُثبته. الوثيقة الحاكمة عندنا (AI_HONESTY) تقول بوضوح: 'AI يساعد. الإنسان يقرر. الدليل يحكم.' — ونطبقها في الكود قبل التسويق." |
| "ما هو ARR أو عدد عملائكم؟" | "برنامج شركاء التصميم بدأ للتو. نحن نبني معك، وأنت أول 3 عملاء تجريبيين — بلا مقابل — لأن دراسة الحالة الحقيقية أثمن من إيراد سريع مبتور." |

---

## 4. Close — العرض المكتوب

### Design Partner MOU (90-day pilot)

- Term: 90 days
- Tenant: 1 tenant, up to 10 seats
- Data: subset of Muhide + tenant's own CRM/Comm data
- Support: direct founder Slack/WhatsApp
- Deliverable: HITL-approved AI recommendation → booked activity (at least 1 per week)
- Cost: SAR 0
- In exchange: (a) weekly 30-min feedback call, (b) right to publish case study upon success, (c) right of first refusal on paid Team-tier at anchor SAR 60k after pilot

### Team Tier Order Form (SAR 60,000 / year)

- Term: 12 months, auto-renew unless 30-day notice
- Seats: up to 15
- Includes: all Product Core + Grounded Copilot + Studio (basic) + HITL + Master Data + 1 signal pack + Gmail Comm Hub
- Support: business-hours email, 24-hour response SLA-lite
- SLA-lite: 99.5% uptime target (no credit obligation at Team tier)
- Data: hosted on Railway + Vercel; DPA signed; PDPL-aligned
- Payment: Stripe SAR annual invoice

---

## 5. Post-sale — Onboarding runbook

**Week 1:**
- Kickoff call
- Tenant provisioned; SSO configured
- Muhide subset ingested for tenant vertical
- Users invited (up to 15)
- ICP profile authored + persisted (`/api/v1/icp/profiles`)

**Week 2:**
- Gmail OAuth connected; incremental sync begins
- 1 signal pack subscribed
- First Copilot demo with tenant's real deal
- HITL approver role assigned

**Week 3:**
- First HITL-approved recommendation → booked activity
- Weekly effectiveness cohort baseline captured
- Feedback session

**Week 4:**
- Onboarding retrospective
- Playbook adjustment
- Success metrics dashboard walkthrough with executive sponsor

**Ongoing:**
- Weekly 30-min check-in for first 90 days
- Monthly business review after that

---

## 6. Reference-cycle upgrades

Convert Design Partner → Team tier requires:
- 3 successful case-study interviews
- Signed reference letter
- LinkedIn / Twitter shareability rights
- Speaker slot at 1 event

---

## 7. Sales team ramp — when to hire

Do NOT hire salespeople until 3 conditions all TRUE:
1. First paid customer > 30 days active
2. First case study published
3. > 20 qualified inbound requests / month

Then hire in this order:
1. Head of Sales (Riyadh-based, KSA B2B network, 8+ years)
2. 1 AE (bilingual, closer)
3. 1 SDR (Arabic-native, outbound)

---

## 8. Sales meta — what NOT to do

- Do NOT overpromise Copilot autonomy
- Do NOT hide the DEV-ONLY LLM status pre-signing
- Do NOT skip DPA
- Do NOT rush a deal that requires modifying tenant isolation
- Do NOT undercut price below SAR 50k (destroys anchor)
- Do NOT sell to an anti-persona (see `05_CUSTOMER_SEGMENTATION.md` §4)

---

*Sales playbook — executable. See `10_KPI_FRAMEWORK.md` for what to track weekly.*
