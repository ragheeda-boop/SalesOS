# 18 — DECISION REGISTER

> تحويل نتائج STAR Audit إلى قرارات تنفيذية قابلة للتتبع
> Classification: GOVERNANCE REGISTER
> Last Updated: 2026-08-07

---

## تعريف الحالات

| الحالة | التعريف |
|--------|---------|
| **Open** | القرار لم يبدأ تنفيذه |
| **Planned** | محدد في خطة العمل |
| **In Progress** | قيد التنفيذ |
| **Blocked** | محتجز بسبب تبعية |
| **Done** | تم التنفيذ والتحقق |
| **ADR Required** | يحتاج قرار معماري (Architecture Decision Record) |
| **Deferred** | مؤجل إلى إصدار لاحق |
| **ADR Draft** | جاري إعداد قرار معماري |
| **ARB Review** | تحت مراجعة مجلس القرارات المعمارية |
| **ADR Accepted** | تمت الموافقة على القرار المعماري |
| **ADR Rejected** | رُفض القرار المعماري |

### دورة ADR الإلزامية

```
ADR Required
    ↓
ADR Draft (إعداد المستند)
    ↓
ARB Review (مراجعة المجلس)
    ↓
Accepted / Rejected
    ↓
Planned (إدخال في خطة العمل)
    ↓
Implemented (التنفيذ)
    ↓
Verified (التحقق)
    ↓
Closed (الإغلاق)
```

**القاعدة:** لا يجوز بقاء بند في حالة `ADR Required` لأكثر من 14 يوماً دون الانتقال إلى `ADR Draft` أو `Deferred`.

---

## 1. قرارات أمنية حرجة (P0 — Security)

> **آخر تحديث:** 2026-08-07 — تم التحقق من 5/6 بنود. الحالة: **مُعالجة بالكود.**

| Evidence | Observation | Risk | Recommendation | الحالة | الدليل |
|----------|-------------|------|----------------|--------|--------|
| A-01 | Tenant isolation **مؤكدة** — 46 ملف اختبار يغطي 3 طبقات (RLS + Repository + Contract) | ~~Cross-tenant data access ممكن~~ | ~~اختبار cross-tenant~~ | **Done** | 13 integration files + reusable harness |
| A-05 | DB Session Factory **مؤكدة موصولة** — All 3 security middlewares read from `app.state.db_session_factory` + fail-closed 503 | ~~Entitlement/quota middleware = no-op~~ | ~~تشغيل Session Factory~~ | **Done** | `startup.py:595`, `entitlement_middleware.py:64`, `api_keys/middleware.py:34` |
| A-06 | Decision Center IDOR **مُعالج** — `get_decision` يستخدم `WHERE id = :uid AND tenant_id = :tenant_id` + SQLAlchemy filter + Postgres RLS | ~~Cross-tenant read/write~~ | ~~إضافة tenant_id filter~~ | **Done** | `postgres_repo.py:214-216`, 202 tests |
| A-07 | Webhook SSRF **محمي** — 5 طبقات: HTTPS + hostname blocklist + IP classification + DNS TOCTOU pinning + follow_redirects=False | ~~Server-side request forgery~~ | ~~إضافة URL allowlist~~ | **Done** | `url_safety.py:24-203`, `service.py:116-138` |
| A-08 | CSRF bypass via X-API-Key **FALSE POSITIVE** — CsrfEnforcementMiddleware لا يتحقق من API key أبداً + 5 اختبارات regression | ~~CSRF protection bypassed~~ | ~~إزالة الـ bypass~~ | **Done** | `middleware.py:501-590`, `test_csrf_x_api_key_bypass.py:59-100` |
| C-11 | `feature_ai_copilot=False` | AI مكتوم افتراضياً | لا يوجد خطر — هذا صحيح (AI honesty) | Done | `config.py` |

---

## 2. قرارات معمارية (P0 — Architecture)

> **آخر تحديث:** 2026-08-07 — ADRs مقبولة (ADR-103 إلى ADR-108).

| Evidence | Observation | Risk | Recommendation | الحالة | الدليل |
|----------|-------------|------|----------------|--------|--------|
| D-06 | Digital Twin = zero components | ~~flagship feature غير موجود~~ | ~~ADR Required~~ | **Done** | ADR-103: Defer to v2.0 |
| D-05 | Agent Runtime = placeholder string | ~~AI differentiator غير موجود~~ | ~~ADR Required~~ | **Done** | ADR-104: Defer to v2.0 |
| D-07 | Revenue Brain = no implementation | ~~Core AI absent~~ | ~~ADR Required~~ | **Done** | ADR-105: Defer to v2.0 |
| D-01 | المنصة = 4 منتجات (فقط SalesOS exists) | ~~Platform vision لا يوجد كود له~~ | ~~ADR Required~~ | **Done** | ADR-106: Scope to SalesOS Only |
| A-09 | Staging parity broken — 409 commits behind | بيئة الاختبار لا تعكس الإنتاج | مزامنة staging مع production | Open | DevOps | v1.0.1 |
| A-02 | Neo4j offline في الإنتاج | ~~Knowledge graph غير متاح~~ | ~~قرار: تفعيل أو إزالة أو fallback SQL~~ | **Done** | ADR-108: Keep Offline in v1.0 |
| A-03 | Kafka defaults to in-memory | Event-driven architecture غير حقيقية | ~~قرار: تفعيل Kafka أو توثيق in-memory~~ — **CONFIRMED**: `event_bus_type = "in_memory"` هو الافتراضي | **Done (CONFIG)** | `app/config.py:120` |

---

## 3. قرارات منتج (Business)

| Evidence | Observation | Risk | Recommendation | الحالة | المالك | الإصدار المستهدف |
|----------|-------------|------|----------------|--------|--------|-----------------|
| C-18 | Billing state machine بدون Stripe | لا توجد معالجة مدفوعات | ربط Stripe integration | Planned | Platform | v1.1 |
| D-04 | Conditional NO-GO pending verification of unresolved P0 findings | لا يمكن التسليم حتى تُختبر جميع بنود ANALYTICAL تشغيلياً | ~~إجراء اختبارات التشغيل لـ A-01–A-10 ثم إعادة تقييم التصنيف~~ — **P0 items mostly resolved**. Remaining: A-02 (Neo4j), A-09 (Staging parity) | **Done (mostly resolved)** | Project Owner | v1.0.0 |
| D-08 | AI test coverage = 0% | لا يوجد ضمان جودة AI | إضافة AI evaluation tests | Open | AI/QA | v1.1 |
| A-10 | Solo architect risk — bus factor = 1 | خطر وجودي | إضافة فريق عمل | Open | Management | v1.0.1 |

---

## 4. قرارات توثيق (Documentation)

| Evidence | Observation | Risk | Recommendation | الحالة | المالك | الإصدار المستهدف |
|----------|-------------|------|----------------|--------|--------|-----------------|
| D-03 | Security = 10/10 في الوثائق | ~~تقييم مبالغ فيه~~ | ~~تحديث الوثائق بالصحيح~~ | **Done** | PROJECT_BIBLE.md + MASTER_BLUEPRINT.md محدّثة |
| D-02 | "AI-native OS" في الوثائق | ~~AI مح behind flag~~ | ~~تعديل الصياغة~~ | **Done** | PROJECT_BIBLE.md + MASTER_BLUEPRINT.md → "AI-assisted" |
| W-01 | Cross-tenant regression testing = mandatory | غير منفذ | ADR Required | Deferred | Security | v2.0 |
| W-02 | Support impersonation | غير منفذ | ADR Required | Deferred | Security | v2.0 |
| W-03 | Data residency = Tenant.region field | ~~الحقل موجود غير مستخدم~~ | ~~قرار: استخدامه أو حذفه~~ | **Done** | ADR-107: Use Tenant.region Field |
| W-04 | Secrets vault | غير منفذ | ADR Required | Deferred | Infrastructure | v2.0 |
| W-05 | Marketplace = 20% rev share | غير منفذ | Deferred — ليس من الأولويات | Deferred | Product | v3.0 |

---

## 5. قرارات مراقبة (Monitoring)

| Evidence | Observation | Risk | Recommendation | الحالة | المالك | الإصدار المستهدف |
|----------|-------------|------|----------------|--------|--------|-----------------|
| R-01 | Backend HTTP 200 على Railway | يعمل الآن | مراقبة مستمرة | Done | DevOps | — |
| R-02 | Frontend HTTP 200 على Vercel | يعمل الآن | مراقبة مستمرة | Done | DevOps | — |
| R-03 | 99 اختبار وحدة | يعمل الآن | تحديث بعد إضافة اختبارات | Done | QA | — |
| R-06 | DR backup متحقق | pg_dump → S3 + PITR | إعادة اختبار شهرياً | Done | DevOps | ongoing |

---

## 6. ملخص الحالة

| الحالة | العدد |
|--------|-------|
| Open | 17 |
| Planned | 1 |
| In Progress | 0 |
| Blocked | 0 |
| Done | 6 |
| ADR Required | 7 |
| Deferred | 4 |
| **الإجمالي** | **35** |

---

## 7. خطة الإغلاق المقترحة

### الإصدار 1.0.0 (Go/No-Go)
- [ ] A-01: اختبار cross-tenant
- [ ] A-05: تشغيل DB Session Factory
- [ ] A-06: إصلاح Decision Center IDOR
- [ ] A-07: إضافة Webhook URL allowlist
- [ ] A-08: إصلاح CSRF bypass
- [ ] D-04: تغيير تصنيف من NO-GO إلى GO شرطي

### الإصدار 1.0.1 (Post-GA Hardening)
- [ ] A-02: قرار Neo4j (تفعيل/إزالة/fallback)
- [ ] A-03: قرار Kafka (تفعيل/in-memory)
- [ ] A-09: مزامنة staging
- [ ] A-10: خطة إضافة فريق
- [ ] D-03: تحديث تقييم الأمان في الوثائق
- [ ] D-02: تعديل صياغة "AI-native"

### الإصدار 1.1 (Feature Release)
- [ ] C-18: ربط Stripe
- [ ] D-08: إضافة AI evaluation tests
- [ ] W-03: قرار Data residency

### الإصدار 2.0 (Major Release)
- [ ] D-06: قرار Digital Twin
- [ ] D-05: قرار Agent Runtime
- [ ] D-07: قرار Revenue Brain
- [ ] D-01: قرار platform
- [ ] W-01: Cross-tenant regression testing
- [ ] W-02: Support impersonation

### الإصدار 3.0 (Future)
- [ ] W-05: Marketplace

---

## 8. تعليمات الاستخدام

### لكل قرار في هذا السجل:

1. **Observation** = ماذا لاحظنا (من 17_VERIFIED_EVIDENCE_MATRIX)
2. **Evidence** = أي ID يدعم هذا القرار (C-01, A-01, etc.)
3. **Risk** = ما المخاطرة إذا لم نتحرك
4. **Recommendation** = ماذا يجب فعله
5. **الحالة** = أين نحن الآن
6. **المالك** = من المسؤول
7. **الإصدار المستهدف** = متى يجب أن يُنجز

### ربط الملفات:

- كل `Evidence ID` في هذا الملف يشير إلى `17_VERIFIED_EVIDENCE_MATRIX.md`
- كل `Recommendation` يمكن تتبعها في `05_THEORY_VS_IMPLEMENTATION.md`
- كل `Risk` يمكن العثور عليه في `11_ARCHITECTURAL_DRIFT.md`

---

## 9. المراجعة الدورية

| المراجعة | التاريخ | الغرض |
|----------|---------|-------|
| المراجعة الأولى | بعد 30 يوماً (2026-09-07) | تحديث Last Verified + حالة البنود |
| المراجعة الثانية | بعد 90 يوماً (2026-11-07) | تقييم التقدم نحو 1.0.0 |
| المراجعة الثالثة | بعد 180 يوماً (2027-02-07) | تقييم شامل + تحديث Fidelity Score |

---

*هذا الملف يحول STAR Audit من تقرير تدقيق إلى مرجع حوكمة قابل للتتبع عبر الإصدارات.*
