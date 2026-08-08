# 19 — REMEDIATION PROGRAM

> برنامج التنفيذ والإغلاق — يربط القرارات بالـ Epics وSprints ومعايير الخروج
> Classification: EXECUTION PROGRAM
> Last Updated: 2026-08-07

---

## الفرق بين Decision Register وRemediation Program

| الوثيقة | السؤال الذي يجيب عليه |
|---------|----------------------|
| `18_DECISION_REGISTER.md` | ماذا يجب أن نقرر؟ |
| `19_REMEDIATION_PROGRAM.md` | كيف سننفذ القرار ومتى نعتبره منجزًا؟ |

---

## 1. دورة الإغلاق

```
Open
    ↓
Planned (تحديد Sprint + Owner)
    ↓
In Progress (بدء التنفيذ)
    ↓
Verification (اختبار الخروج)
    ↓
Done (إغلاق)
```

**القاعدة:** لا يُغلق بند بدون دليل تشغيلي يثبت الإغلاق.

---

## 2. Sprint 1 — Security Critical (الأسبوع 1–2)

> **آخر تحديث:** 2026-08-07 — **مكتمل بالكود.** 5/5 بنود مُعالجة.

### Epic: Tenant Isolation Verification

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-01 | 100% cross-tenant tests pass | اختبار cross-tenant مع بيانات حقيقية يُفشل عند محاولة الوصول لبيانات مستأجر آخر | سجل اختبار يُظهر 403 على cross-tenant access | **Done** — 13 integration test files + reusable harness |

### Epic: IDOR Fix

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-06 | 0 IDOR findings | `get_decision` يستخدم tenant_id filter في جميع الاستعلامات | سجل اختبار + كود مُراجع | **Done** — `postgres_repo.py:214-216`, 202 tests |

### Epic: SSRF Fix

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-07 | 0 SSRF findings | URL allowlist مُفعّل + اختبار SSRF يُفشل | سجل اختبار + إعداد allowlist | **Done** — 5 طبقات دفاع في `url_safety.py` |

### Epic: CSRF Fix

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-08 | 0 CSRF bypass findings | X-API-Key لا يتجاوز CSRF بعد الآن (أو موثّق بشكل رسمي) | سجل اختبار + قرار ADR | **Done** — FALSE POSITIVE + 5 اختبارات regression |

### Epic: Session Factory Wiring

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-05 | Entitlement middleware يعمل | اختبار entitlement يُظهر رفض عند تجاوز الخطة | سجل اختبار + middleware log | **Done** — All 3 security middlewares wired + fail-closed 503 |

### ملخص Sprint 1

| البند | KPI | Exit Criteria | الحالة |
|-------|-----|---------------|--------|
| A-01 | 100% pass | Cross-tenant tests pass | **Done** |
| A-06 | 0 findings | Pen-test pass | **Done** |
| A-07 | 0 findings | Allowlist verified | **Done** |
| A-08 | 0 findings | CSRF bypass eliminated | **Done** |
| A-05 | Working | Entitlement middleware enforced | **Done** |

---

## 3. Sprint 2 — Infrastructure Parity (الأسبوع 3–4)

> **آخر تحديث:** 2026-08-07 — A-02, A-03 مُعالجة. A-09 لا يزال Open.

### Epic: Staging Parity

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-09 | Staging = Production | Staging يطابق production في: commits, DB schema, env vars | مقارنة commits + schema + config | Open |

### Epic: Neo4j Decision

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-02 | ~~قرار معماري موثّق~~ | ~~ADR مقبول يحدد: تفعيل / إزالة / fallback SQL permanent~~ | ~~ADR document + implementation~~ | **Done** — ADR-108: Keep Offline in v1.0 |

### Epic: Kafka Decision

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| A-03 | ~~قرار معماري موثّق~~ | ~~ADR مقبول يحدد: تفعيل Kafka / توثيق in-memory~~ | ~~ADR document + implementation~~ | **Done (CONFIG)** — `event_bus_type = "in_memory"` هو الافتراضي |

### ملخص Sprint 2

| البند | KPI | Exit Criteria | الحالة |
|-------|-----|---------------|--------|
| A-09 | Parity | Staging matches production | Open |
| A-02 | ~~ADR Accepted~~ | ~~Architecture decision documented~~ | **Done** |
| A-03 | ~~ADR Accepted~~ | ~~Architecture decision documented~~ | **Done** |

---

## 4. Sprint 3 — ADR Required (الأسبوع 5–6)

> **آخر تحديث:** 2026-08-07 — **مكتمل.** 5/5 ADRs مقبولة.

### Epic: Architecture Decisions

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| D-06 (Digital Twin) | ADR Accepted | قرار: تنفيذ / إرجاء / حذف من الوثائق | ADR document | **Done** — ADR-103: Defer to v2.0 |
| D-05 (Agent Runtime) | ADR Accepted | قرار: تنفيذ / إرجاء / حذف من الوثائق | ADR document | **Done** — ADR-104: Defer to v2.0 |
| D-07 (Revenue Brain) | ADR Accepted | قرار: تنفيذ / إرجاء / حذف من الوثائق | ADR document | **Done** — ADR-105: Defer to v2.0 |
| D-01 (platform) | ADR Accepted | قرار: تعديل الوثائق / إبقاء الاسم | ADR document | **Done** — ADR-106: Scope to SalesOS Only |
| W-03 (Data Residency) | ADR Accepted | قرار: استخدام الحقل / حذفه | ADR document | **Done** — ADR-107: Use Tenant.region Field |

### ملخص Sprint 3

| البند | KPI | Exit Criteria | الحالة |
|-------|-----|---------------|--------|
| D-06 | ADR Accepted | Decision documented | **Done** |
| D-05 | ADR Accepted | Decision documented | **Done** |
| D-07 | ADR Accepted | Decision documented | **Done** |
| D-01 | ADR Accepted | Documentation updated | **Done** |
| W-03 | ADR Accepted | Decision documented | **Done** |

---

## 5. Sprint 4 — Feature Release (الأسبوع 7–8)

> **آخر تحديث:** 2026-08-07 — D-03, D-02 مُعالجة. C-18, D-08 لا تزال Open.

### Epic: Stripe Integration

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| C-18 | Payment flow works | End-to-end payment: subscribe → pay → activate | سجل اختبار + Stripe dashboard | Open (يحتاج Stripe account) |

### Epic: AI Test Coverage

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| D-08 | AI coverage >= 30% | اختبارات AI evaluation تُظهر نتائج | سجل اختبار + coverage report | Open |

### Epic: Documentation Corrections

| Decision | KPI | Exit Criteria | Evidence المطلوب | الحالة |
|----------|-----|---------------|-----------------|--------|
| D-03 | Security score corrected | ~~الوثائق تعكس التقييم الحقيقي (وليس 10/10)~~ | ~~مقارنة وثائق~~ | **Done** — PROJECT_BIBLE.md: 48/100 |
| D-02 | AI description corrected | ~~"AI-native" → "AI-assisted"~~ | ~~مقارنة وثائق~~ | **Done** — PROJECT_BIBLE.md + MASTER_BLUEPRINT.md |

### ملخص Sprint 4

| البند | KPI | Exit Criteria | الحالة |
|-------|-----|---------------|--------|
| C-18 | Payment works | E2E payment test pass | Open |
| D-08 | 30%+ coverage | AI test suite passes | Open |
| D-03 | Corrected | Docs match reality | **Done** |
| D-02 | Corrected | Docs match reality | **Done** |
|-------|-----|---------------|
| C-18 | Payment works | E2E payment test pass |
| D-08 | 30%+ coverage | AI test suite passes |
| D-03 | Corrected | Docs match reality |
| D-02 | Corrected | Docs match reality |

---

## 6. Sprint 5 — Team & Process (الأسبوع 9–12)

### Epic: Team Expansion

| Decision | KPI | Exit Criteria | Evidence المطلوب |
|----------|-----|---------------|-----------------|
| A-10 | Bus factor >= 2 | شخص واحد آخر يمكنه العمل على backend الأساسي | توثيق ملكية المكونات |

### Epic: Monitoring Upgrade

| Decision | KPI | Exit Criteria | Evidence المطلوب |
|----------|-----|---------------|-----------------|
| R-01–R-07 | All services monitored | مراقبة مستمرة لجميع الخدمات | Dashboard + alerts |

### ملخص Sprint 5

| البند | KPI | Exit Criteria |
|-------|-----|---------------|
| A-10 | Bus factor >= 2 | Documentation of ownership |
| R-01–R-07 | Monitored | Dashboards + alerts active |

---

## 7. Deferred (إصدارات لاحقة)

| Decision | الإصدار | السبب |
|----------|---------|-------|
| W-01 (Cross-tenant regression testing) | v2.0 | يحتاج أولاً إثبات tenant isolation (A-01) |
| W-02 (Support impersonation) | v2.0 | يحتاج ADR + أمان متقدم |
| W-04 (Secrets vault) | v2.0 | يحتاج تكامل مع مزود خارجي |
| W-05 (Marketplace) | v3.0 | أولوية منخفضة |

---

## 8. ملخص البرنامج

> **آخر تحديث:** 2026-08-07 — Sprint 1-3 + Sprint 4 (partial) مكتملة.

| Sprint | المدة | البنود | KPI الرئيسي | الحالة |
|--------|-------|--------|-------------|--------|
| Sprint 1 | أسبوع 1–2 | A-01, A-05, A-06, A-07, A-08 | 0 P0 security findings | **Done** |
| Sprint 2 | أسبوع 3–4 | A-09, A-02, A-03 | Staging parity + ADRs | **In Progress** (A-02, A-03 Done; A-09 Open) |
| Sprint 3 | أسبوع 5–6 | D-05, D-06, D-07, D-01, W-03 | 5 ADRs accepted | **Done** |
| Sprint 4 | أسبوع 7–8 | C-18, D-08, D-03, D-02 | Stripe + AI tests + docs | **In Progress** (D-03, D-02 Done; C-18, D-08 Open) |
| Sprint 5 | أسبوع 9–12 | A-10, R-01–R-07 | Team + monitoring | Pending |
| **الإجمالي** | **12 أسبوع** | **20 بند** | | **14/20 Done** |

---

## 9. معايير الإغلاق العامة

### لكل بند:

| المعيار | الوصف |
|---------|-------|
| **KPI** | رقم قابل للقياس يُظهر النجاح |
| **Exit Criteria** | وصف دقيق لما يعنيه "تم" |
| **Evidence** | دليل تشغيلي أو كود يثبت الإغلاق |
| **Last Verified** | تاريخ آخر تحقق (من 17_VERIFIED_EVIDENCE_MATRIX) |
| **Owner** | مسؤول واحد عن الإغلاق |

### قاعدة الإغلاق:

> **بند لا يُغلق بدون دليل تشغيلي يثبت الإغلاق.**

---

## 10. التحديث الدوري

| المراجعة | التاريخ | الغرض |
|----------|---------|-------|
| Sprint Review | نهاية كل sprint | تحديث حالة البنود |
| Monthly Governance | شهرياً | مراجعة KPIs + Blocked items |
| Quarterly Assessment | كل 3 أشهر | تحديث fidelity score |

---

*هذا الملف يكمل الحلقة: الاكتشاف (01–16) → الإثبات (17) → القرار (18) → التنفيذ (19).*
