# SalesOS Pilot Launch — Customer Validation Program

> المدة: 30 يومًا
> المشاركون: 3–5 شركات، 10–15 مستخدمًا
> الهدف: إثبات أن SalesOS يزيد من إيرادات المبيعات

---

## 1. معايير اختيار الشركات

| المعيار | الوصف |
|---------|-------|
| قطاع | شركات مبيعات B2B في السعودية |
| الحجم | 10–50 مندوب مبيعات |
| التقنية | يستخدمون CRM حاليًا (Salesforce, HubSpot, Odoo) |
| الاستعداد | لديهم بيانات عن العملاء والشركات |
| اللغة | العربية |

---

## 2. المقاييس الأساسية

| المقياس | التعريف | طريقة القياس | الهدف |
|---------|---------|-------------|-------|
| **Time to Insight** | الوقت من فتح الشركة إلى فهم وضعها | Telemetry: company_dna_view → أول NBA | < 60s |
| **Time to Next Action** | الوقت من فهم الشركة إلى اتخاذ إجراء | Telemetry: nba_view → opportunity_create | < 5min |
| **Daily Active Users** | عدد المستخدمين النشطين يوميًا | Login events | > 80% |
| **Widget Usage** | نسبة استخدام كل Widget | Widget render events | توزيع متساوٍ |
| **Search Usage** | عدد مرات البحث لكل مستخدم | Search query events | > 5/day |
| **AI Acceptance** | نسبة تنفيذ توصيات AI | nba_shown → nba_executed | > 40% |
| **NBA Conversion** | NBA → فرصة | nba_executed → opportunity_created | > 25% |
| **NPS** | صافي نقاط الترويج | استبيان أسبوعي | > 40 |

---

## 3. الجدول الزمني

| الأسبوع | النشاط |
|---------|--------|
| **الأسبوع 1** | الإعداد: إضافة الشركات، استيراد البيانات، تدريب المستخدمين |
| **الأسبوع 2** | المراقبة: متابعة الاستخدام، حل المشكلات، جمع feedback |
| **الأسبوع 3** | التعديل: تحسين الـ widgets بناءً على feedback |
| **الأسبوع 4** | التقييم: قياس المقاييس، تقرير نهائي، قرار الإطلاق |

---

## 4. قياس المقاييس

كل widget يرسل telemetry event عند:

| الحدث | البيانات |
|-------|---------|
| `widget.rendered` | widgetId, companyId, userId, durationMs |
| `widget.interacted` | widgetId, action, companyId |
| `nba.executed` | nbaId, actionType, confidence |
| `opportunity.created` | source, companyId, value |
| `search.performed` | query, resultCount, durationMs |

---

## 5. استبيان المستخدمين (أسبوعي)

```
1. ما أكثر شيء أعجبك هذا الأسبوع؟
2. ما أصعب شيء واجهته؟
3. هل أوصتيك الشركة لزميلك؟ (0-10)
4. أي Widget استخدمته أكثر؟
5. هل التوصيات كانت مفيدة؟
6. ماذا تنقصك؟
```
