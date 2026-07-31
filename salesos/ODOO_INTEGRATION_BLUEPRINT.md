# Odoo Integration Blueprint — Extension to CANONICAL_ARCHITECTURE.md

> **يمتد على:** `CANONICAL_ARCHITECTURE.md` v1.0.0 (2026-07-30) — لا يُناقضها، بل يضيف موديول جديد ضمن نفس السجل (Registries) بنفس القواعد المعلنة في القسم 16 (Authority & Maintenance).
> **الأساس:** بيانات Odoo الإنتاجية الحقيقية (`odoo-ps-psae-ratl-main-14005796`) المفحوصة حياً + السجل التنفيذي الفعلي لكود SalesOS كما وثّقه `CANONICAL_ARCHITECTURE.md` نفسه — وليس افتراضات.

---

## 0. أهم تصحيح قبل أي شيء: Odoo لا يحتاج معماراً جديداً — يحتاج تعبئة معمار موجود أصلاً فارغ

بمراجعة القسمين **14 (Current Gaps)** و**17 (Health Scorecard)** من وثيقتكم نفسها، تبيّن أن أغلب "الطموحات المعمارية" التي افترضتها في التقرير السابق (Kafka، Neo4j، Event-Driven) هي **بنية تحتية مُهيّأة لكن فارغة فعلياً**، وليست جاهزة إنتاجياً:

| ما افترضته سابقاً | ما تقوله وثيقتكم الفعلية (القسم 13، 17) |
|---|---|
| "Kafka جاهز كناقل أحداث" | `Event Bus: Kafka (in-memory fallback) — Default in_memory for dev; Kafka optional` + `Event-Driven Adoption: D (5 من 60 موديول فقط)` |
| "Neo4j جاهز لتمثيل العلاقات" | `Graph DB: Neo4j 5 — لكن zero data currently` |
| "Webhooks آمنة SSRF" | القسم 14 يذكر صراحة: `Webhook SSRF (no URL allowlist) — app/routers/workflows.py:493` كـ **Security P0 غير محلول** |
| "55 من 60 موديول CRUD متزامن فقط، بدون أحداث" | هذا يعني: **كل الموديولات الناجحة فعلياً اليوم (Company 360, Contacts, Employee 360) تعمل بأسلوب متزامن عبر PostgreSQL مباشرة، وليس عبر Event Bus** |

**الخلاصة المعمارية المُصحَّحة:** تكامل Odoo يجب أن يتبع **نفس النمط الناجح الموجود فعلياً** (متزامن، PostgreSQL-first، شبيه بـ `notion_sync`/`excel_import`)، وليس نمطاً طموحاً جديداً يعتمد على بنية تحتية غير مُفعّلة بعد. هذا فعلياً **أسهل وأسرع تنفيذاً** مما اقترحته سابقاً.

---

## 1. مصفوفة الكائنات: Odoo ↔ الكائنات القياسية الموجودة أصلاً

الخبر الجيد: **معظم الكائنات المطلوبة موجودة فعلاً في القسم 3.1** ولا تحتاج إنشاء من الصفر — فقط Repository جديد يقرأ من Odoo بدل الإدخال اليدوي.

| Odoo Model | Odoo → SalesOS Canonical Object | الحالة |
|---|---|---|
| `res.partner` | **OBJ-003 Company** (`name_ar`, `cr_number` ← `x_studio_cr_number` الموجود فعلاً في Odoo!, `city`, `status`) | ✅ مطابقة مباشرة |
| `res.partner` (جهة اتصال فردية) | **OBJ-004 Contact** | ✅ مطابقة مباشرة |
| `crm.lead` | **OBJ-007 Opportunity** (`value`←expected_revenue, `stage`←stage_id, `probability`) | ✅ مطابقة مباشرة |
| `calendar.event` | **OBJ-011 Meeting** | ✅ مطابقة مباشرة |
| `mail.message` (message_type=email) | **OBJ-012 Email** | ✅ مطابقة (لكن الحجم صغير جداً فعلياً — 82 سجل فقط شركة-كاملة كما أثبتنا) |
| `mail.message` (message_type=comment, ملاحظات داخلية) | **لا يوجد كائن قياسي مطابق حالياً** | ⚠️ **فجوة حقيقية** — انظر القسم 2 |
| `sale.order` | **OBJ-013 Quote** / **OBJ-015 Contract** | ✅ مطابقة، لكن أولوية منخفضة (3 سجلات فقط) |
| `project.task` (عام) | **OBJ-008 Task** | ✅ مطابقة جزئية — لكن Odoo أغنى بكثير (انظر القسم 2) |
| `helpdesk.ticket` | **لا يوجد** | ⚠️ **فجوة حقيقية** — انظر القسم 2 |
| `account.move` | **لا يوجد كائن مناسب** — يوجد `OBJ-303 Invoice` لكنه تحت **Governance domain** ويمثّل فوترة SalesOS **لعملائها هي (tenants)**، وليس فواتير عملاء Muhide في Odoo | ⚠️ **تصادم تسمية** — انظر القسم 2 |

---

## 2. الكائنات والقدرات الجديدة المقترحة (بنفس نظام الترقيم الثابت في وثيقتكم)

بما أن القسم 16.2 يشترط أن أي كائن/قدرة جديدة تُضاف بمعرّف ثابت لا يتغيّر، هذه المعرّفات التالية الفارغة في تسلسلكم الحالي:

### كائنات جديدة (Objects)

| # المقترح | Object | Table المقترح | Domain | الحقول الأساسية | المصدر في Odoo |
|---|---|---|---|---|---|
| **OBJ-019** | **SupportTicket** | `support_tickets` | Contact Management أو domain جديد "Support" | tenant_id, company_id, subject, stage, priority, sla_deadline, assignee_id | `helpdesk.ticket` |
| **OBJ-020** | **FinancingCase** | `financing_cases` | Commercial (DOM-005) | tenant_id, company_id, financing_amount_requested, approved_amount, coverage_value, case_status, counterparty_id | `project.task` (حقول Studio: `x_studio_financing_amount_requested`, `x_studio_approved_financing_amount`, `x_studio_coverage_value`, `x_studio_unified_agreement_status`) |
| **OBJ-021** | **CustomerInvoice** | `commercial_invoices` | Commercial (DOM-005) | tenant_id, company_id, amount_total, amount_residual, invoice_date_due, payment_state | `account.move` — **مقصوداً منفصل تماماً عن OBJ-303 Invoice الحالي** لتفادي تصادم "فاتورة SalesOS لعميلها" مع "فاتورة Odoo لعميل Muhide" |
| **OBJ-022** | **InteractionNote** | `interaction_notes` | Timeline & Activity (DOM-016) | tenant_id, company_id, source_model, author_id, body, logged_at | `mail.message` (comment/internal) — **هذا أهم كائن جديد على الإطلاق** لأنه المصدر الفعلي للـ Sentiment/Root-Cause كما أثبتنا هذا الأسبوع (2,416+ ملاحظة حقيقية غنية بالمحتوى) |

### قدرة جديدة (Capability)

| ID المقترح | Capability | Domain | الحالة المقترحة |
|---|---|---|---|
| **CAP-067** | **Odoo ERP Connector** | Data Fabric (DOM-017) — بنفس مستوى CAP-038 Notion Sync وCAP-039 Excel Import | `in_dev` |

### تكامل جديد (Integration Registry، القسم 10)

| Integration | ID | Type | Direction | Auth |
|---|---|---|---|---|
| **Odoo XML-RPC** | **INT-013** | XML-RPC | Inbound (سحب) | API Key (Odoo API Key) |
| **Odoo Studio Webhook** | **INT-014** | Webhook | Inbound (دفع) | Secret (مثل INT-012 الموجود) — **مشروط بإصلاح P0 في `app/routers/workflows.py:493` أولاً** |

---

## 3. لماذا `mail.message` (OBJ-022 الجديد) هو أعلى نقطة استفادة قصوى على الإطلاق

هذا ليس رأياً — بل استنتاج مباشر من مقارنة بيانات Odoo الحقيقية بفجوات SalesOS الموثّقة في وثيقتكم:

- وثيقتكم تقول صراحة إن **CAP-019 Activity Intelligence حالته 🟡 (partial)**، وإن **"55 من 60 موديول بدون أحداث حقيقية"**.
- بيانات Odoo الحقيقية (فحصناها هذا الأسبوع) تحتوي **2,416 ملاحظة داخلية حقيقية** بمحتوى غني جداً (أسباب توقف صفقات، أسباب رفض تمويل، نتائج مكالمات) — وهذا **بالضبط** نوع البيانات التي تحتاجها Activity Intelligence لتتحول من 🟡 إلى ✅.
- **لا يوجد أي مصدر بيانات آخر في SalesOS اليوم بهذا الحجم والغنى النصي** (Gmail Sync حقيقي لكن حجمه صغير جداً لدى Muhide كما أثبتنا: 82 إيميل فقط شركة-كاملة).

**التوصية المباشرة:** OBJ-022 (InteractionNote) يجب أن يكون **أول شيء يُبنى**، ليس Company أو Contact — لأنه الفجوة الأعلى قيمة والأسهل تحقيقاً (قراءة `mail.message` عبر XML-RPC بسيطة جداً تقنياً، أثبتناها فعلياً هذا الأسبوع بأقل من 30 سطر بايثون).

---

## 4. نقطة استفادة قصوى ثانية: `x_studio_cr_number` = مفتاح الربط المجاني مع 141,221 شركة موجودة أصلاً في SalesOS

هذه أهم نقطة تقنية اكتشفتها من مطابقة الوثيقتين معاً:

- **CAP-004 Company 360** في SalesOS يعتمد على `cr_number` (السجل التجاري السعودي) كحقل أساسي في **OBJ-003 Company**، ومبني عليه بالكامل **CAP-037 Entity Resolution** (دمج السجلات المكررة) و**WDG-108 Golden Record**.
- فحصنا اليوم أن Odoo (تحديداً `project.task`) يحتوي فعلياً حقل **`x_studio_cr_number`** ("CR Number") — أي أن **رقم السجل التجاري لعملاء Muhide الحقيقيين مُخزَّن فعلاً في Odoo**.
- SalesOS يملك أصلاً **141,221 شركة حقيقية** من الـ Scrapers الحكومية (Balady/Najiz/REGA/Taqeem) مربوطة بنفس المفتاح (`cr_number`).

**النتيجة العملية:** بمجرد ربط Odoo، **كل عميل حقيقي في Odoo يُطابَق تلقائياً وفورياً** (join بسيط على `cr_number`) مع بيانات حكومية غنية جاهزة أصلاً — بدون أي عمل Entity Resolution إضافي، وبدون انتظار أي Scraping جديد. هذا يُفعّل **WDG-108 Golden Record** و**WDG-109 Government Intelligence** لأول مرة ببيانات عملاء حقيقيين، فوراً.

---

## 5. نقطة استفادة قصوى ثالثة: `crm.team` = بيانات CAP-017 Territory الحقيقية المفقودة

وثيقتكم (القسم 17.1) تقول صراحة: **"Revenue Territory, Quota, Forecast (all InMemory)"** — أي أن **CAP-017 Territory Management لا يملك بيانات حقيقية أبداً اليوم**.

Odoo عندكم فعلياً يحتوي **6 فرق مبيعات إقليمية حقيقية جاهزة**: Northern/Eastern/Central/Western/Southern Region Team + CS Team (`crm.team`)، مع فرص CRM حقيقية موزّعة عليها فعلياً.

**النتيجة العملية:** ربط `crm.team` مباشرة يُحوّل CAP-017 من جدول فارغ في الذاكرة إلى قدرة حقيقية تعرض توزيع الأداء الفعلي بين المناطق الخمس — بدون أي تصميم بيانات جديد، فقط استيراد مباشر.

---

## 6. نقطة استفادة قصوى رابعة: Odoo هو أول بيانات حقيقية لـ Neo4j (Knowledge Graph) الفارغ تماماً اليوم

وثيقتكم تقول حرفياً: **"Neo4j 5 (community) | Relationship traversals (but zero data currently)"** و**CAP-029 Knowledge Graph حالته 🟡**.

بيانات Odoo (خصوصاً حقول Studio في `project.task` مثل `x_studio_linked_opportunity`, `x_studio_counterparty_name`) تمثّل فعلياً **علاقة بيانية حقيقية** (بائع↔مشتري↔ممول) لا يمكن تمثيلها بشكل صحيح في جدول علائقي مسطّح.

**النتيجة العملية:** ربط Odoo لا يُضيف فقط بيانات — بل **يُشغّل Neo4j لأول مرة بمعنى حقيقي** منذ إنشائه في البنية التحتية، محوّلاً WDG-110 (Relationship Graph) من widget فارغ إلى أداة عمل فعلية.

---

## 7. Employee 360 تحديداً (كما سألت سابقاً) — التطابق مع الـ Widget Registry الفعلي (القسم 9.3)

وثيقتكم توثّق **CAP-014 Employee 360 بدقة شديدة**: 21 API endpoint، 5 خدمات، 4 جداول (`employee_signals`, `employee_scores`, `employee_calendar_events`, `employee_email_events`)، و**7 widgets محددة بالاسم**:

| Widget موجود فعلاً | ID | تغذيته من Odoo |
|---|---|---|
| Profile (WDG-201) | ✅ | `res.users` + `res.partner` |
| Portfolio (WDG-202) | ✅ | `crm.lead` (فرص الموظف) — **جاهز فوراً**، بالضبط كما حسبناه يدوياً لإبراهيم هادي (465 فرصة، 52 مكسوبة) |
| AI Coach (WDG-203) | ✅ | يحتاج OBJ-022 (InteractionNote) كمُدخل — تحليل جودة التواصل من الملاحظات الفعلية |
| KPIs (WDG-204) | ✅ | مزيج CRM + Tasks + Tickets |
| Activity (WDG-205) | ✅ | **هذا الـ widget بالضبط هو مكان OBJ-022 (InteractionNote)** — ليس "Email" |
| Calendar (WDG-206) | ✅ | `calendar.event` — لكن حجم البيانات صغير جداً فعلياً (24 حدث كامل الشركة) |
| Email (WDG-207) | ✅ | `mail.message` (message_type=email) فقط — **توقّع بيانات قليلة جداً** (كما أثبتنا: 0 إيميل حقيقي لإبراهيم هادي رغم كونه الأفضل أداءً) |

**ملاحظة تصميم مهمة اكتشفناها فعلياً:** لا تبنِ "Email widget" (WDG-207) بتوقع أنه المصدر الرئيسي — **الحقيقة الميدانية أن قناة التواصل الفعلية عند Muhide هي مكالمات/واتساب موثّقة كملاحظات (OBJ-022)**، وWDG-205 (Activity) هو الـ widget الذي يجب أن يحمل الثقل الأكبر، وليس WDG-207 (Email) كما قد يُفترض للوهلة الأولى من اسمه.

**فجوة حقيقية في الـ widgets الحالية:** لا يوجد widget مخصص لـ "Tickets" أو "Financing Cases" ضمن الـ 7 الحالية — يُنصح بإضافة widget ثامن (مثلاً WDG-208 "Support & Cases") ليعرض `OBJ-019 SupportTicket` و`OBJ-020 FinancingCase` الخاصين بالموظف، بدل حشرهما داخل KPIs فقط.

---

## 8. التصميم التقني المُصحَّح (بعد معرفة الحالة الفعلية للبنية التحتية)

```
Odoo (XML-RPC)
   │
   ▼
CAP-067 Odoo ERP Connector  (موديول مستقل — بنفس نمط notion_sync/excel_import)
   │  (متزامن، مجدوَل عبر الوظائف الموجودة أصلاً: CAP-028 Scheduled Jobs)
   ▼
PostgreSQL مباشرة  (Repository حقيقي — ليس InMemory، حسب القسم 17.1 "45 Postgres-backed" هو النمط الناجح)
   │
   ├──→ OBJ-003 Company / OBJ-004 Contact   (عبر cr_number matching → Entity Resolution)
   ├──→ OBJ-007 Opportunity                  (Pipeline/Dashboard مباشرة)
   ├──→ OBJ-022 InteractionNote (جديد)       (Activity Intelligence + AI Coach)
   ├──→ OBJ-019 SupportTicket (جديد)         (Employee 360 + Customer Success)
   ├──→ OBJ-020 FinancingCase (جديد)         (Commercial + Risk Scoring)
   └──→ OBJ-021 CustomerInvoice (جديد)       (Revenue Dashboard + Churn Intelligence)

(اختياري لاحقاً، وليس شرطاً للإطلاق): بث أحداث company.*/opportunity.* الموجودة أصلاً في القسم 8 — لكن فقط بعد أن يثبت الفريق أن Kafka انتقل من in_memory إلى وضع فعلي، وليس قبل ذلك.
```

**لماذا هذا أفضل من التصميم السابق المعتمد على Kafka/Webhooks كخط أساسي:** لأنه **يطابق النمط الوحيد المُثبَت نجاحه فعلياً في كودكم اليوم** (Postgres-backed synchronous)، بدل الاعتماد على بنية تحتية موثّقة رسمياً في وثيقتكم كـ"معطّلة افتراضياً" (Kafka) أو "فارغة تماماً" (Neo4j) أو "بها ثغرة أمنية P0 غير محلولة" (Webhooks).

---

## 9. القيد الأمني الوحيد الذي يمنع استخدام Webhooks (INT-014) اليوم تحديداً

القسم 14 يذكر بدقة الملف والسطر: **`app/routers/workflows.py:493` — Webhook SSRF (no URL allowlist)**، بالإضافة إلى **CSRF bypass via `X-API-Key` header في `app/common/csrf.py`**.

بما أن أي Webhook قادم من Odoo Studio سيمر عبر نفس مسار الـ Webhooks الموجود (`CAP-027`)، **لا يجوز تفعيل INT-014 (Odoo Webhook) قبل إغلاق هذين البندين تحديداً** — هذا ليس تحفظاً عاماً بل يشير لنفس الكود الذي سيُستخدم حرفياً.

**الحل المؤقت العملي:** ابدأ بـ INT-013 (XML-RPC السحب المجدوَل عبر CAP-028 Scheduled Jobs الموجودة أصلاً وتعمل ✅) فقط، وأجّل INT-014 (Webhook الفوري) حتى إغلاق الثغرتين. هذا لا يؤخر أي قيمة حقيقية — كل نقاط الاستفادة القصوى في الأقسام 3-6 أعلاه تتحقق بالكامل بالسحب المجدوَل وحده.

---

## 10. خارطة تنفيذ مُصححة (مبنية على القدرات الموجودة فعلاً، لا الطموحة)

| المرحلة | المدة | المحتوى |
|---|---|---|
| **Phase 1** | 1-2 أسبوع | بناء CAP-067 (Odoo Connector) كموديول مستقل + Repository لـ OBJ-003/004/007 عبر XML-RPC، مجدوَل بـ CAP-028 الموجودة. مطابقة `cr_number` فورية مع الـ 141,221 شركة الموجودة (القسم 4). |
| **Phase 2** | 1 أسبوع فقط | إضافة OBJ-022 (InteractionNote) — **أعلى عائد لأقل جهد** كما في القسم 3، يُفعّل CAP-019 Activity Intelligence و WDG-205/AI Coach مباشرة. |
| **Phase 3** | 1-2 أسبوع | إضافة OBJ-019 (SupportTicket) و OBJ-020 (FinancingCase) — يحتاج تصميم schema جديد (migration، مع مراعاة أن Alembic متأخر 5 إصدارات حسب القسم 14 — يجب اللحاق أولاً). |
| **Phase 4** | 1 أسبوع | إضافة OBJ-021 (CustomerInvoice) + ربط `crm.team`→ CAP-017 Territory (القسم 5). |
| **Phase 5** | مستمر، بالتوازي مع إغلاق P0 الأمنية | تفعيل INT-014 (Webhook) بعد إغلاق `workflows.py:493` و`csrf.py`، ثم تفعيل Neo4j الفعلي (القسم 6) وربط الأحداث الحقيقية عندما ينتقل Kafka من in_memory. |

---

*ملحق لوثيقة `CANONICAL_ARCHITECTURE.md` — يُقترح دمجه رسمياً بعد مراجعة CTO/Architect حسب قاعدة القسم 16.2 (أي تحديث يتطلب موافقة + دليل من الكود التنفيذي).*
