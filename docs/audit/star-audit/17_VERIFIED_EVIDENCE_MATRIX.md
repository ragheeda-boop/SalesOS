# 17 — VERIFIED EVIDENCE MATRIX

> هدف هذا الملف: فصل كل استنتاج حسب نوع الدليل ومستوى الثقة وتاريخ التحقق
> Classification: EVIDENCE MATRIX
> Last Updated: 2026-08-07

---

## تعريف فئات الدليل

| الفئة | التعريف | مستوى الثقة |
|-------|---------|------------|
| **CODE** | موجود ومثبت في كود المصدر | High |
| **RUNTIME TEST** | تم اختباره في بيئة تشغيل حية أو اختبار | High |
| **CONFIG** | موجود في ملفات التكوين (docker-compose, .env, alembic) | Medium-High |
| **DOC DRIFT** | مقارنة بين وثيقة وحالة الكود | Medium |
| **ANALYTICAL** | استنتاج تحليلي من قراءة الكود (لم يتم اختباره تشغيلياً) | Medium-Low |
| **DOC ONLY** | موجود في الوثائق فقط، لا يوجد كود | Low |

---

## 1. نتائج مؤكدة بالكود (CODE)

| ID | Last Verified | النتيجة | الملف | السطر/الدالة |
|----|--------------|---------|-------|-------------|
| C-01 | 2026-08-07 | JWT RS256 مع refresh rotation و reuse detection | `app/modules/identity/service.py` | `create_access_token()`, `rotate_refresh_token()` |
| C-02 | 2026-08-07 | 7 طبقات أمان في middleware | `app/common/middleware.py` | الكلاسات السبعة |
| C-03 | 2026-08-07 | RBAC مع 4 أدوار و27 مورد | `sdk/permissions.py` | `PermissionRegistry`, `PermissionEnforcer` |
| C-04 | 2026-08-07 | Dual-engine database (app role + owner role) | `app/database.py` | `engine`, `owner_engine` |
| C-05 | 2026-08-07 | ContextVar tenant pinning عبر set_config | `app/database.py` | `apply_tenant_guc()` |
| C-06 | 2026-08-07 | Brute force protection (5 محاولات → 15 دقيقة) | `app/modules/identity/service.py` | `check_brute_force()` |
| C-07 | 2026-08-07 | CSRF double-submit pattern | `app/common/middleware.py` | `CsrfEnforcementMiddleware` |
| C-08 | 2026-08-07 | Rate limiting (Redis-backed + in-memory fallback) | `app/common/middleware.py` | `RateLimitMiddleware` |
| C-09 | 2026-08-07 | AI guardrails (20+ نمط حقن، PII scrubbing) | `intelligence/guardrails.py` | `Guardrails` class |
| C-10 | 2026-08-07 | 7 حاسبات درجات في Feature Store | `runtime/feature_store/` | 7 score computers |
| C-11 | 2026-08-07 | Copilot مح behind feature flag | `app/config.py` | `feature_ai_copilot=False` |
| C-12 | 2026-08-07 | Frontend Decision Engine = STUB (كل الدوال throw) | `packages/platform/decision/index.ts` | كل الدوال |
| C-13 | 2026-08-07 | Agent Runtime = placeholder string | `runtime/agent_runtime/` | "PLANNED FOR RT3" |
| C-14 | 2026-08-07 | 72+ جدول في قاعدة البيانات | `app/database.py` | 19 model imports |
| C-15 | 2026-08-07 | 70+ مسار API مسجل | `app/boot/routers.py` | `register_routers()` |
| C-16 | 2026-08-07 | 93+ صفحة في الواجهة الأمامية | `src/app/` | App Router structure |
| C-17 | 2026-08-07 | Copilot tool = SearchCompaniesTool فقط | `domains/copilot/tools.py` | `SearchCompaniesTool` |
| C-18 | 2026-08-07 | Billing state machine يعمل بدون Stripe | `app/modules/billing/state_machine.py` | 5 حالات، 7 أحداث |
| C-19 | 2026-08-07 | Entitlements مع 4 خطط | `app/modules/admin/entitlements.py` | `PlanEntitlements` |
| C-20 | 2026-08-07 | PDPL right to erasure (user anonymization) | `app/modules/identity/service.py` | `anonymize_user()` |
| C-21 | 2026-08-07 | Security headers (CSP, HSTS, X-Frame-Options) | `app/common/middleware.py` | `SecurityHeadersMiddleware` |
| C-22 | 2026-08-07 | Grounding service (Postgres + Neo4j retrieval) | `intelligence/grounding.py` | `GroundingService` |
| C-23 | 2026-08-07 | Alembic مسجل 83 إصدار | `app/alembic/versions/` | 83 migration files |

---

## 2. نتائج مؤكدة بالتشغيل (RUNTIME TEST)

| ID | Last Verified | النتيجة | الدليل |
|----|--------------|---------|--------|
| R-01 | 2026-08-06 | Backend يخدم HTTP 200 على Railway | GA Audit: production verification evidence |
| R-02 | 2026-08-06 | Frontend يخدم HTTP 200 على Vercel | GA Audit: production verification evidence |
| R-03 | 2026-08-06 | 99 اختبار وحدة يعمل بنجاح | GA Audit: "99 tests passing" |
| R-04 | 2026-08-06 | Alembic migration 0051 مطبق | GA Audit: "Alembic at migration 0051" |
| R-05 | 2026-08-06 | 141,221 شركة في قاعدة بيانات الإنتاج | GA Audit: production data evidence |
| R-06 | 2026-08-06 | pg_dump → S3 + pgBackRest PITR متحقق | EAB-2026-08-06-003: ops01 evidence |
| R-07 | 2026-08-06 | Celery worker + beat يعمل على Railway | GA Audit: operational evidence |

---

## 3. نتائج مؤكدة بالتكوين (CONFIG)

| ID | Last Verified | النتيجة | الملف |
|----|--------------|---------|-------|
| G-01 | 2026-08-07 | Docker Compose = 14 خدمة | `salesos/docker-compose.yml` |
| G-02 | 2026-08-07 | Kafka مكون لكن defaults to in-memory | `app/config.py` |
| G-03 | 2026-08-07 | Neo4j مكون في docker-compose | `salesos/docker-compose.yml` |
| G-04 | 2026-08-07 | OpenAI هو مزود الذكاء商وي الوحيد | `app/config.py` |
| G-05 | 2026-08-07 | Poetry 2.4.1 (متوافق مع Docker) | `salesos/backend/pyproject.toml` |
| G-06 | 2026-08-07 | Python 3.12+ مطلوب | `salesos/backend/pyproject.toml` |
| G-07 | 2026-08-07 | Next.js 15 + React 19 | `salesos/frontend/package.json` |

---

## 4. نتائج انحراف توثيقي (DOC DRIFT)

| ID | Last Verified | الوثيقة | الكود يقول | الفجوة |
|----|--------------|---------|-----------|--------|
| D-01 | 2026-08-07 | المنصة = 4 منتجات | فقط SalesOSExists | وثيقة فقط |
| D-02 | 2026-08-07 | "AI-native OS" | `feature_ai_copilot=False` | انحراف كبير |
| D-03 | 2026-08-07 | Security = 10/10 | GA audit = 48/100 | انحراف في التقييم |
| D-04 | 2026-08-07 | Production GO | production NO-GO | انحراف حرج |
| D-05 | 2026-08-07 | Agent Runtime = دورة حياة كاملة | placeholder string | انحراف كبير |
| D-06 | 2026-08-07 | Digital Twin = مرآة حسابية | zero components | انحراف كبير |
| D-07 | 2026-08-07 | Revenue Brain = ذكاء مركزي | no implementation | انحراف كبير |
| D-08 | 2026-08-07 | AI test coverage = 85% | 0% AI-specific | انحراف حرج |

---

## 5. نتائج تحليلية (ANALYTICAL) — تم التحقق منها في 2026-08-07

| ID | Last Verified | النتيجة | التحليل | التصنيف الجديد | الدليل |
|----|--------------|---------|---------|---------------|-------|
| A-01 | 2026-08-07 | Tenant isolation **مؤكدة بالكود** | 46 ملف اختبار: 13 integration (real PostgreSQL RLS) + 27 unit + 2 contract + 4 harness | **CODE (MITIGATED)** | 13 integration test files + reusable harness |
| A-02 | 2026-08-07 | Neo4j offline في الإنتاج | GA audit أكّد ذلك | ANALYTICAL (بانتظار اختبار تشغيلي) | — |
| A-03 | 2026-08-07 | Kafka defaults to in-memory | `event_bus_type = "in_memory"` في config | **CONFIG (CONFIRMED)** | `app/config.py:120` |
| A-04 | 2026-08-07 | Conditional NO-GO | تصنيف GA audit — يعتمد على A-02 و A-09 | ANALYTICAL (بانتظار اختبار) | — |
| A-05 | 2026-08-07 | DB Session Factory **مؤكدة موصولة** | All 3 security middlewares read from `app.state.db_session_factory` + fail-closed 503 | **CODE (VERIFIED)** | `startup.py:595`, `entitlement_middleware.py:64`, `api_keys/middleware.py:34` |
| A-06 | 2026-08-07 | Decision Center IDOR **مُعالج** | `get_decision` يستخدم `WHERE id = :uid AND tenant_id = :tenant_id` | **CODE (MITIGATED)** | `postgres_repo.py:214-216` |
| A-07 | 2026-08-07 | Webhook SSRF **محمي** | 5 طبقات: HTTPS + hostname blocklist + IP classification + DNS TOCTOU pinning + follow_redirects=False | **CODE (PROTECTED)** | `url_safety.py:24-203`, `service.py:116-138` |
| A-08 | 2026-08-07 | CSRF bypass via X-API-Key ** FALSE POSITIVE** | CsrfEnforcementMiddleware لا يتحقق من API key أبداً + 5 اختبارات regression | **CODE (FALSE POSITIVE)** | `middleware.py:501-590`, `test_csrf_x_api_key_bypass.py:59-100` |
| A-09 | 2026-08-07 | Staging parity broken | "409 commits behind" | ANALYTICAL (بانتظار اختبار تشغيلي) | — |
| A-10 | 2026-08-07 | Solo architect risk | تحليل هيكل الفريق | ANALYTICAL (ملاحظة تنظيمية) | — |

---

## 6. نتائج وثائق فقط (DOC ONLY)

| ID | Last Verified | النتيجة | المصدر | الحالة |
|----|--------------|---------|--------|--------|
| W-01 | 2026-08-07 | Cross-tenant regression testing = mandatory merge gate | CANONICAL_ARCHITECTURE.md | غير منفذ |
| W-02 | 2026-08-07 | Support impersonation = time-boxed, audited | CANONICAL_ARCHITECTURE.md | غير منفذ |
| W-03 | 2026-08-07 | Data residency = Tenant.region field | MODEL EXISTS | الحقل موجود غير مستخدم |
| W-04 | 2026-08-07 | Secrets vault = dedicated manager | CANONICAL_ARCHITECTURE.md | غير منفذ |
| W-05 | 2026-08-07 | Marketplace = 20% rev share | ROADMAP_5_YEARS.md | غير منفذ |

---

## 7. ملخص توزيع الدليل

| الفئة | العدد | نسبة الثقة | Last Verified Range |
|-------|-------|-----------|---------------------|
| CODE | 23 | High | 2026-08-07 |
| RUNTIME TEST | 7 | High | 2026-08-06 |
| CONFIG | 7 | Medium-High | 2026-08-07 |
| DOC DRIFT | 8 | Medium | 2026-08-07 |
| ANALYTICAL | 10 | Medium-Low | 2026-08-07 |
| DOC ONLY | 5 | Low | 2026-08-07 |
| **الإجمالي** | **60** | | |

---

## 8. ملاحظات وتوصيات منفصلة

### ملاحظة: لا توجد اختبارات تشغيلية لـ P0

| Observation | Evidence | Risk | Recommendation |
|-------------|----------|------|----------------|
| 10 نتائج ANALYTICAL تحتاج اختبار تشغيلي | A-01 إلى A-10 | قرارات إدارية مبنية على استنتاجات غير مثبتة | تشغيل اختبارات لكل بند A-01–A-10 قبل اعتماد التقرير كقرار Go/No-Go |

### ملاحظة: الاعتماد على GA Audit القديم

| Observation | Evidence | Risk | Recommendation |
|-------------|----------|------|----------------|
| نتائج RUNTIME TEST مؤرخة بـ 2026-08-06 | R-01 إلى R-07 | الحالة التشغيلية قد تغيرت منذ التاريخ | تحديث اختبارات التشغيل قبل كل قرار إداري |

### ملاحظة: لا يوجد ملكية للبنود

| Observation | Evidence | Risk | Recommendation |
|-------------|----------|------|----------------|
| لا يوجد مالك محدد لكل بند | جميع البنود | صعوبة تتبع المسؤولية | ربط كل ID بمالك في 18_DECISION_REGISTER |

---

## 9. خلاصة

هذا الملف يُظهر أن:

- **23 نتيجة مؤكدة بالكود** — يمكن الدفاع عنها في أي مراجعة هندسية
- **7 نتائج مؤكدة بالتشغيل** — أدلة حية من الإنتاج (مؤرخة)
- **8 نتائج انحراف توثيقي** — فروقات موثقة بين الوثائق والكود
- **10 نتائج تحليلية** — تحتاج اختبارات تشغيلية قبل استخدامها في قرارات إدارية
- **5 نتائج وثائق فقط** — لا يمكن الاعتماد عليها بدون كود

**القاعدة:** لا تستخدم نتيجة ANALYTICAL أو DOC ONLY كقرار إداري بدون إرفاق دليل تشغيلي.

**القاعدة الثانية:** كل نتيجة يجب أن تحمل `Last Verified` تاريخاً واضحًا — إذامر أكثر من 30 يوماً، يجب إعادة التحقق.

---

*هذا الملف يكمل STAR Audit بفصل واضح بين ما هو مؤكد وما هو استنتاجي. التحويل إلى قرارات تنفيذية في 18_DECISION_REGISTER.md.*
