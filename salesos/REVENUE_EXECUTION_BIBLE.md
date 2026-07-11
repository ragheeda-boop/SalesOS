# Revenue Execution Bible v1

> **الرؤية:** تحويل ذكاء الشركات إلى إيرادات — من المعرفة إلى التنفيذ.
>
> **تاريخ الإصدار:** 2026-07-10
> **مرحلة المشروع:** Wave 2 — Product Phase
> **الاعتماد:** يعتمد على SalesOS Product Bible v1 (Company Intelligence, Dashboard, Search)

---

## Vision

### الجملة الواحدة

> **Revenue Execution هي الطبقة التي تحوِّل معرفة SalesOS عن الشركات إلى صفقات وإيرادات ملموسة.**

### لماذا Revenue Execution؟

Wave 1 (Company Intelligence) تجيب على السؤال: **"ما هي هذه الشركة؟"**

Wave 2 تجيب على السؤال: **"ماذا أفعل حيال هذه الشركة؟"**

فرق المبيعات في السعودية تعاني من:

- **فجوة المعرفة والتنفيذ:** تعرف الشركة لكن لا تعرف الخطوة التالية.
- **غياب التوجيه الذكي:** ليس هناك "الخطوة التالية الأفضل" لكل فرصة.
- **إدارة الفرص يدويًا:** Excel وملاحظات متفرقة لتتبع الصفقات.
- **اجتماعات بلا تحضير:** تدخل اجتماع مع عميل بدون ذكاء سياقي.
- **عدم وجود Playbooks:** كل مندوب يعيد اختراع عملية البيع.

**Revenue Execution يسد هذه الفجوة — من Company Intelligence إلى Revenue.**

### الرؤية المستقبلية

| Horizon | الوصف |
|---------|-------|
| **Wave 2 (الآن)** | Revenue Execution — Next Best Action, Pipeline Intelligence, Meeting Prep |
| **Wave 3 (3 months)** | Revenue Intelligence — تنبؤ بالفرص والمخاطر قبل حدوثها |
| **Wave 4 (6 months)** | Autonomous Sales Agent — توصيات واستنتاجات استباقية |

### العلاقة مع Product Bible

Revenue Execution هي **ليست CRM**. CRM يسجل ما حدث. Revenue Execution يقرر ما يحدث بعد ذلك.

| Product Bible | Revenue Execution Bible |
|--------------|------------------------|
| Company Intelligence — افهم الشركة | Opportunity Intelligence — افهم الفرصة |
| Signals — ماذا يحدث حول الشركة | Next Best Action — ماذا تفعل الآن |
| Data Fabric — من أين تأتي البيانات | Pipeline Fabric — أين تذهب الصفقات |
| Company 360 — الشركة كاملة | Opportunity Workspace — الفرصة كاملة |

---

## Revenue Execution Workflow

### دورة العمل الكاملة

```
Discover
    │  البحث عن شركات جديدة عبر Search, Signals, Recommendations
    ▼
Understand
    │  تحليل الشركة عبر Company Intelligence (Wave 1)
    ▼
Prioritize
    │  Next Best Action Engine يقرر أي فرصة تتحرك اليوم
    ▼
Engage
    │  أول تواصل: Email, Call, LinkedIn
    ▼
Meet
    │  اجتماع مع العميل — Meeting Intelligence يحضر الملخص
    ▼
Propose
    │  عرض سعر / Proposal — بناءً على احتياجات العميل
    ▼
Negotiate
    │  تفاوض — Deal Health يراقب المخاطر
    ▼
Close
    │  إغلاق الصفقة — تسجيل الإيرادات
    ▼
Expand
    │  توسع في الحساب — فرص إضافية، تجديد، رفع قيمة
```

### المراحل الثلاث الكبرى

```
1. Qualification (Discover → Understand → Prioritize)
   - هل هذه فرصة حقيقية؟
   - هل العميل جاهز؟
   - ما هي الخطوة الأولى؟

2. Progression (Engage → Meet → Propose)
   - تحريك الفرصة عبر مراحل البيع
   - كل مرحلة لها Playbook
   - Meeting Intelligence يحضر لكل لقاء

3. Closure (Negotiate → Close → Expand)
   - تفاوض ذكي
   - Deal Health يراقب علامات الخطر
   - Expansion يكتشف فرصًا إضافية
```

---

## Personas

### 1. مندوب المبيعات — Sales Rep

**الاسم الوظيفي:** مندوب مبيعات / Account Executive
**الشركات المستهدفة:** شركات المبيعات B2B (تقنية، خدمات، استشارات)

**المهام اليومية:**
- يتواصل مع العملاء المحتملين
- يدير الفرص في مراحل البيع المختلفة
- يحضر للاجتماعات مع العملاء
- يحدّث Pipeline

**نقاط الألم:**
- لا يعرف أي فرصة يتابع أولًا
- يقضي ساعات في التحضير للاجتماعات (بحث، تقارير)
- ينسى متابعة الفرص القديمة
- لا يملك Playbook واضح لكل مرحلة بيع

**مقياس النجاح:** كم صفقة يغلق شهريًا؟

### 2. مدير المبيعات — Sales Manager

**الاسم الوظيفي:** مدير مبيعات / Head of Sales
**الشركات المستهدفة:** جميع

**المهام اليومية:**
- يراجع Pipeline مع الفريق
- يحلل أداء الفرص
- يدرب المندوبين
- يقدم توقعات للإدارة

**نقاط الألم:**
- لا يملك رؤية فورية عن صحة كل صفقة
- يصعب عليه تحديد أي صفقة تحتاج تدخله
- لا يعرف لماذا تخسر الصفقات
- صعوبة في توقع الإيرادات بدقة

**مقياس النجاح:** دقة التوقعات الشهرية

### 3. مدير نجاح العملاء — Customer Success Manager

**الاسم الوظيفي:** CSM / Account Manager
**الشركات المستهدفة:** العملاء الحاليون

**المهام اليومية:**
- يتابع العملاء الحاليين
- يحدد فرص التوسع
- يدير التجديدات

**نقاط الألم:**
- لا يعرف أي عميل معرض للخسارة
- يصعب عليه اكتشاف فرص البيع الإضافي
- لا يملك رؤية عن صحة العلاقة

**مقياس النجاح:** نسبة التجديد (Retention Rate)

### 4. المسؤول التنفيذي للمبيعات — VP of Sales

**الاسم الوظيفي:** VP Sales / CRO
**الشركات المستهدفة:** جميع

**المهام اليومية:**
- يشرف على استراتيجية المبيعات
- يتخذ قرارات توزيع الموارد
- يحلل أداء القنوات والمنتجات

**نقاط الألم:**
- معلومات Pipeline تصل متأخرة
- لا توجد رؤية عن صحة الصفقات الكبيرة
- صعوبة في قياس فعالية Playbooks

**مقياس النجاح:** نمو الإيرادات ربع السنوي

---

## Core Entities

### Entity Diagram

```
Opportunity
    │
    ├── Playbook (what to do at each stage)
    ├── Task (follow-ups, reminders)
    ├── Meeting (customer interactions)
    ├── Email (communications)
    ├── Activity (calls, notes, events)
    ├── Pipeline (stage, probability, velocity)
    ├── Revenue Goal (target, forecast)
    └── Next Best Action (recommended step)
```

### 1. Opportunity

**الفرصة — قلب Revenue Execution.**

| الحقل | الوصف | مثال |
|-------|-------|------|
| `id` | معرف فريد | `opp_a1b2c3d4` |
| `companyId` | الشركة المرتبطة | `comp_xyz` |
| `name` | اسم الفرصة | "تطبيق نظام محاسبة لشركة الأمل" |
| `stage` | مرحلة البيع | `qualification | discovery | proposal | negotiation | closed_won | closed_lost` |
| `value` | قيمة الصفقة | 500,000 SAR |
| `probability` | احتمال الإغلاق (%) | 60% |
| `expectedCloseDate` | تاريخ الإغلاق المتوقع | 2026-09-15 |
| `ownerId` | مسؤول الفرصة | `user_abc` |
| `playbookId` | Playbook المطبق | `pb_enterprise_saas` |
| `health` | صحة الصفقة | `healthy | at_risk | critical` |
| `signals` | إشارات مرتبطة | `[signal_1, signal_2]` |
| `nextBestAction` | الخطوة التالية المقترحة | `schedule_demo` |
| `score` | درجة الأولوية | 85/100 |

### 2. Playbook

**دليل الإجراءات لكل مرحلة بيع.**

| الحقل | الوصف |
|-------|-------|
| `id` | معرف فريد |
| `name` | اسم Playbook |
| `description` | وصف الحالة المناسبة |
| `stages` | قائمة Stages مع إجراءات محددة لكل Stage |
| `triggers` | متى يُفعّل هذا Playbook |
| `tasks` | مهام تلقائية عند التفعيل |
| `templates` | قوالب Emails, Proposals, Meeting Agenda |

### 3. Task

| الحقل | الوصف |
|-------|-------|
| `id` | معرف فريد |
| `opportunityId` | الفرصة المرتبطة |
| `type` | `call | email | meeting | follow_up | review` |
| `title` | عنوان المهمة |
| `dueDate` | تاريخ الاستحقاق |
| `assignedTo` | المسؤول |
| `status` | `pending | completed | skipped` |
| `source` | `manual | playbook | ai` |

### 4. Meeting

| الحقل | الوصف |
|-------|-------|
| `id` | معرف فريد |
| `opportunityId` | الفرصة المرتبطة |
| `title` | عنوان الاجتماع |
| `date` | تاريخ الاجتماع |
| `attendees` | قائمة الحضور |
| `agenda` | جدول الأعمال |
| `notes` | ملاحظات ما بعد الاجتماع |
| `actionItems` | بنود متابعة |
| `intelligence` | Meeting Intelligence — تحليل قبل وبعد الاجتماع |
| `recordingUrl` | رابط التسجيل (إن وجد) |

### 5. Email

| الحقل | الوصف |
|-------|-------|
| `id` | معرف فريد |
| `opportunityId` | الفرصة المرتبطة |
| `subject` | عنوان البريد |
| `from` | المرسل |
| `to` | المستلم |
| `body` | نص البريد |
| `sentAt` | تاريخ الإرسال |
| `type` | `outbound | inbound | template` |
| `intelligence` | Email Intelligence — تحليل المشاعر، المواضيع |

### 6. Activity

| الحقل | الوصف |
|-------|-------|
| `id` | معرف فريد |
| `opportunityId` | الفرصة المرتبطة |
| `type` | `call | note | event | task_completed` |
| `description` | وصف النشاط |
| `timestamp` | وقت النشاط |
| `createdBy` | من قام بالنشاط |

### 7. Pipeline

| الحقل | الوصف |
|-------|-------|
| `opportunityId` | الفرصة |
| `stage` | المرحلة الحالية |
| `stageHistory` | تاريخ المراحل وتواريخ الانتقال |
| `velocity` | سرعة التقدم (أيام لكل مرحلة) |
| `probability` | احتمال الإغلاق |
| `health` | صحة الصفقة |

### 8. Revenue Goal

| الحقل | الوصف |
|-------|-------|
| `id` | معرف فريد |
| `period` | `monthly | quarterly | yearly` |
| `target` | الهدف |
| `forecast` | التوقعات الحالية |
| `achieved` | المحقق |
| `ownerId` | المسؤول |

### 9. Next Best Action

**القلب النابض لـ Revenue Execution.**

| الحقل | الوصف |
|-------|-------|
| `opportunityId` | الفرصة |
| `action` | الإجراء المقترح |
| `reason` | سبب الاقتراح |
| `confidence` | درجة الثقة بالاقتراح |
| `source` | مصدر التوصية (AI / Rule / Playbook) |
| `dueBy` | الوقت المقترح للتنفيذ |
| `status` | `pending | completed | dismissed` |

---

## Workspaces

### 1. Opportunity Workspace

صفحة متكاملة لكل فرصة.

```
Opportunity Workspace
│
├── Header: Name, Value, Stage, Health, Probability
│
├── Next Best Action (أهم عنصر)
│   └── الإجراء المقترح التالي + سبب + زر تنفيذ
│
├── Timeline (نشاطات الفرصة)
│   └── Meetings, Emails, Tasks, Stage Changes
│
├── Playbook (ما يجب فعله الآن)
│   └── الخطوات حسب Stage + نسبة الإنجاز
│
├── Intelligence
│   ├── Deal Health — صحة الصفقة + تحذيرات
│   ├── Competitors — منافسون في هذه الفرصة
│   ├── Signals — إشارات مرتبطة بالشركة
│   └── Company Snapshot — من Company Intelligence
│
├── Activities
│   ├── Meetings — سجل الاجتماعات
│   ├── Emails — سجل المراسلات
│   └── Tasks — المهام المعلقة
│
└── Actions
    ├── Schedule Meeting
    ├── Send Email
    ├── Create Task
    └── Update Stage
```

### 2. Pipeline Workspace

لوحة قيادة لجميع الفرص.

```
Pipeline Workspace
│
├── Kanban View
│   └── Stages with Opportunities (drag & drop)
│
├── List View
│   └── Sortable, filterable table
│
├── Analytics
│   ├── Total Pipeline Value
│   ├── Win Rate
│   ├── Average Deal Size
│   ├── Velocity (days per stage)
│   └── Conversion Rate per Stage
│
├── Health Map
│   └── كل فرصة مع Health Indicator (traffic light)
│
└── Forecast vs Target
    └── Revenue Goal progress
```

### 3. Meeting Workspace

قبل وأثناء وبعد الاجتماع.

```
Meeting Workspace
│
├── Pre-Meeting Intelligence
│   ├── Company Brief (AI Summary)
│   ├── Recent Signals
│   ├── Open Opportunities
│   ├── Key Contacts
│   ├── Talking Points (مقترحة)
│   └── Questions to Ask (مقترحة)
│
├── During Meeting
│   ├── Agenda
│   ├── Notes (بصري)
│   └── Action Items
│
└── Post-Meeting
    ├── AI Summary
    ├── Action Items Auto-Extraction
    ├── Email Follow-Up Draft
    └── Opportunity Stage Update
```

### 4. Revenue Workspace

اللوحة التنفيذية.

```
Revenue Workspace
│
├── Executive Summary
│   ├── Target vs Forecast
│   ├── Month/Quarter Progress
│   └── Year-to-Date
│
├── Pipeline Intelligence
│   ├── Total Pipeline
│   ├── Weighted Pipeline
│   ├── New Opportunities
│   └── Lost/Stalled
│
├── Team Performance
│   ├── Per-rep metrics
│   ├── Win rates
│   └── Activity levels
│
├── Forecast
│   ├── Best Case
│   ├── Commit
│   └── Pipeline
│
└── AI Insights
    ├── At-Risk Deals
    ├── Top Opportunities
    ├── Coaching Recommendations
    └── Market Trends
```

---

## User Journeys

### Journey 1: متابعة فرصة جديدة

```
1️⃣ مندوب المبيعات يفتح Dashboard → يرى Next Best Action
2️⃣ يقترح AI: "فرصة جديدة لشركة الأمل — تواصل مع صاحب القرار"
3️⃣ يفتح Opportunity Workspace → يقرأ ملخص الشركة
4️⃣ Playbook يوجه: "المرحلة: Qualification — أرسل بريد تعريف"
5️⃣ AI يكتب مسودة البريد → المندوب يراجع ويرسل
6️⃣ ينشئ Task متابعة لمدة 3 أيام
7️⃣ الفرصة تدخل Pipeline في مرحلة Qualification
```

### Journey 2: تحضير اجتماع

```
1️⃣ المندوب لديه اجتماع خلال ساعة
2️⃣ يفتح Meeting Workspace
3️⃣ AI يولد:
   - Company Brief (من Company Intelligence)
   - آخر Signals
   - Talking Points للاجتماع
   - أسئلة مقترحة للعميل
4️⃣ أثناء الاجتماع: يسجل Notes و Action Items
5️⃣ بعد الاجتماع: AI يولد ملخص + متابعة بريد
```

### Journey 3: مراجعة Pipeline أسبوعية

```
1️⃣ مدير المبيعات يفتح Pipeline Workspace
2️⃣ يرى Health Map — 3 فرص في "At Risk"
3️⃣ يضغط على فرصة At Risk → يقرأ سبب التحذير
4️⃣ Deal Health يشرح: "تأخر في الرد، منافس جديد في السوق"
5️⃣ يضغط Recommend Action → AI يقترح تدخل المدير
6️⃣ ينشئ Task للمدير: تواصل مع العميل
```

### Journey 4: تقرير الإيرادات الربعي

```
1️⃣ VP Sales يفتح Revenue Workspace
2️⃣ يرى Forecast vs Target — 85% من الهدف
3️⃣ يفحص Team Performance — مندوبان أقل من المتوقع
4️⃣ AI Insights يقترح: تدريب على Negotiation للمندوبين
5️⃣ يقرر إعادة توزيع الفرص بين الفريق
6️⃣ يصدر التقرير التنفيذي
```

---

## Intelligence Engines

### 1. Next Best Action Engine

**القلب — ما هي الخطوة التالية لكل فرصة؟**

| المصدر | المخرجات |
|--------|---------|
| Opportunity Stage | الإجراء المناسب للمرحلة |
| Deal Health | توصيات لتحسين الصحة |
| Playbook | الخطوات التالية من Playbook |
| AI | تحليل سياقي (آخر نشاط، مشاعر البريد) |
| Signals | تفعيل على إشارة جديدة |
| Time | متابعة تلقائية للفرص الخاملة |

**مثال:** فرصة في مرحلة Proposal منذ 14 يومًا دون حركة. NBA يقرر: "أرسل بريد متابعة للعميل."

### 2. Playbook Engine

**أي Playbook ينطبق على هذه الفرصة؟**

| العوامل | المخرجات |
|---------|---------|
| Industry | Playbook مخصص للقطاع |
| Deal Size | Playbook للصفقات الكبيرة/المتوسطة/الصغيرة |
| Stage | إجراءات المرحلة الحالية |
| Company Type | Enterprise / SMB |
| Product | Playbook حسب المنتج |

### 3. Opportunity Scoring

**تصنيف الفرص حسب أهميتها.**

| العامل | الوزن |
|--------|-------|
| Deal Value | 30% |
| Stage | 20% |
| Engagement Level | 15% |
| Company Fit (ICP) | 15% |
| Decision Maker Access | 10% |
| Timeline | 10% |

**النتيجة:** 0-100 — تحدد أولوية المتابعة اليومية.

### 4. Deal Health

**صحة الصفقة — هل هناك خطر؟**

| المؤشر | الوصف |
|--------|-------|
| Stagnation | لا نشاط منذ X يومًا |
| Competition | منافس ظهر في Signals |
| Engagement Drop | انخفاض في التواصل |
| Stakeholder Change | تغير في صانع القرار |
| Budget Concern | إشارات عن ميزانية |
| Timeline Slip | تأجيل متكرر للمواعيد |

**النتيجة:** Healthy 🟢 | At Risk 🟡 | Critical 🔴

### 5. Meeting Intelligence

**ذكاء الاجتماعات — قبل وأثناء وبعد.**

| المرحلة | المخرجات |
|---------|---------|
| **قبل** | Company Brief, Talking Points, Questions, Recent Signals |
| **أثناء** | Note-taking, Action Item Extraction (AI) |
| **بعد** | AI Summary, Follow-up Draft, Opportunity Update |

### 6. Email Intelligence

**تحليل المراسلات.**

| الميزة | الوصف |
|--------|-------|
| Sentiment Analysis | إيجابي/محايد/سلبي |
| Topic Extraction | مواضيع رئيسية من البريد |
| Action Item Detection | استخراج بنود متابعة تلقائيًا |
| Follow-up Reminder | تذكير بالرد إذا لم يجب العميل |
| Template Suggestions | اقتراح ردود بناءً على السياق |

---

## Product Principles

### Principle 1: Actionable at Every Step
> **كل شاشة تنتهي بإجراء يمكن للمستخدم اتخاذه الآن.**

لا توجد شاشة عرض فقط. كل فرصة تعرض "الخطوة التالية". كل اجتماع ينتج "بنود متابعة". كل بريد يولد "إجراء".

### Principle 2: Intelligence Before Data
> **قبل أن ترى أرقام Pipeline، يجب أن تفهم صحته.**

البيانات وصفية. الذكاء توجيهي. Pipeline يعرض الصحة أولًا، الأرقام ثانيًا. الفرصة تعرض التوصية أولًا، التفاصيل ثانيًا.

### Principle 3: NBA-First
> **Next Best Action هو أول ما يراه المستخدم عند فتح أي فرصة.**

إذا فتحت Opportunity Workspace، أول شيء تراه هو: "ما الذي يجب أن تفعله الآن؟" — وليس جدولًا أو أرقامًا.

### Principle 4: Moments That Matter
> **الذكاء يظهر في اللحظات الحاسمة، ليس في كل لحظة.**

قبل الاجتماع → Meeting Intelligence. عندما تخمد فرصة → NBA. عندما يدخل منافس → Deal Health Warning. عندما يحين وقت التجديد → Expansion Alert.

### Principle 5: Continuity with Wave 1
> **Revenue Execution لا يستبدل Company Intelligence — يبنى عليه.**

كل فرصة مرتبطة بشركة. كل شركة لها Intelligence (Signals, Health, Relationships). كل Pipeline مبني على Company Data Fabric.

---

## Sprint Plan: Wave 2

### Sprint 5 — Next Best Action Engine

**الهدف:** بناء محرك NBA الذي يقرر الخطوة التالية لكل فرصة.

**المخرجات:**
- NBA Engine Service (backend)
- قواعد NBA الأساسية (Stage-based, Time-based, Signal-based)
- NBA API: `GET /opportunities/:id/next-best-action`
- NBA Widget في Opportunity Workspace
- اختبارات NBA Engine

**المدة:** 2 أسابيع

### Sprint 6 — Opportunity Workspace

**الهدف:** أول إصدار لـ Opportunity Workspace مع تكامل NBA و Company Intelligence.

**المخرجات:**
- Opportunity Workspace صفحة كاملة
- Opportunity Service (CRUD + Stage Management)
- Playbook Engine (إصدار أول)
- Health Indicators
- تكامل مع Company Intelligence (Company Snapshot)
- Timeline للنشاطات

**المدة:** 3 أسابيع

### Sprint 7 — Pipeline Intelligence

**الهدف:** Pipeline Workspace مع تحليلات و Health Map.

**المخرجات:**
- Pipeline Workspace (Kanban + List View)
- Pipeline Analytics (Velocity, Win Rate, Conversion)
- Health Map (Traffic Light لكل فرصة)
- Forecast Engine
- Pipeline Export (PDF, CSV)

**المدة:** 3 أسابيع

### Sprint 8 — Meeting & Email Intelligence

**الهدف:** Meeting Intelligence قبل وأثناء وبعد الاجتماع + Email Intelligence.

**المخرجات:**
- Meeting Workspace (Pre/During/Post)
- Meeting Intelligence Engine (Brief, Talking Points, AI Summary)
- Email Intelligence (Sentiment, Topics, Actions)
- Email Integration (Gmail API, Outlook API)
- AI توليد مسودات البريد

**المدة:** 3 أسابيع

### Sprint 9 — Revenue Workspace & Integration

**الهدف:** Revenue Workspace التنفيذي + تكامل Wave 2 كامل.

**المخرجات:**
- Revenue Workspace (Target vs Forecast, Team Performance)
- Revenue Goals CRUD + Tracking
- Executive Reports
- تكامل NBA + Pipeline + Meeting + Email
- Playbook Engine كامل
- اختبارات تكامل Wave 2

**المدة:** 3 أسابيع

---

## Success Metrics

### Product Metrics

| المقياس | المستهدف | كيفية القياس |
|---------|---------|-------------|
| NBA Acceptance Rate | > 60% | نسبة NBA التي ينفذها المستخدم |
| Time to Next Action | < 24 ساعة | من آخر نشاط إلى الإجراء التالي |
| Opportunity to Close Time | تقليل 30% | متوسط أيام من الإنشاء إلى الإغلاق |
| Pipeline Accuracy | > 80% | الفرق بين التوقع والإغلاق الفعلي |
| Meeting Prep Time | تقليل 50% | وقت تحضير الاجتماع قبل وبعد |

### Engineering Metrics

| المقياس | المستهدف |
|---------|---------|
| NBA Engine Latency | < 200ms |
| Pipeline Load Time | < 2s |
| Meeting Intelligence Gen Time | < 3s |
| Email Sync Latency | < 30s |

---

## Definition of Done (Wave 2)

| المعيار | الوصف |
|---------|-------|
| 🎨 **Design** | التصميم معتمد — يستخدم Design Language و Foundation Components من Wave 1 |
| 📱 **Responsive** | يعمل على 1280px+ |
| 🌙 **Dark Mode** | يدعم Light و Dark |
| 🇸🇦 **Bilingual** | المحتوى عربي وإنجليزي |
| 🧠 **AI Ready** | NBA و Meeting Intelligence و Email Intelligence مبنية كخدمات قابلة للتوسع |
| ❌ **Empty State** | رسالة مفيدة عند عدم وجود بيانات |
| ⏳ **Loading State** | Skeleton screen |
| ⚠️ **Error State** | رسالة خطأ + إعادة محاولة |
| 🧪 **Tests** | Unit لكل Service + Integration لكل API |
| 🔒 **Permissions** | RBAC لكل Workspace |
| ⚡ **Performance** | < 2s page load, < 200ms NBA |
| 🔗 **Wave 1 Integration** | يستخدم Company Intelligence و Search و Dashboard |

---

> **آخر تحديث:** 2026-07-10
>
> **المرحلة:** Wave 2 — Revenue Execution — Sprint Zero
>
> **الخطوة التالية:** Sprint 5 — Next Best Action Engine
