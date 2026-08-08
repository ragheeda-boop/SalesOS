# خطة البرودكشن الكاملة — SalesOS (Production Program)

**التاريخ:** 2026-07-22  
**المصدر:** تدقيق GA الهندسي (`docs/audit/ga-engineering-audit/`)  
**التصنيف الحالي:** **production no-go** (Production Readiness **38/100**, Security **48/100**)  
**المنتج المستهدف للإطلاق:** **SalesOS GA** داخل منصة (نية منصّة؛ الواقع الكودي SalesOS فقط)  
**نوع الوثيقة:** برنامج تنفيذ CTO/Ops — تخطيط فقط (لا تنفيذ في هذه الجولة)

> **مبدأ الحوكمة:** AI assists. Humans decide. Evidence governs.  
> لا يُعلن Production Ready دون أدلة قابلة للتحقق. البنود غير المُثبتة في التدقيق تُعلَّم: **يحتاج تحقق**.

**روابط مرتبطة**

| وثيقة | دور |
|-------|-----|
| [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md) | حكم NO-GO والـ scorecard |
| [MASTER_REPORT.md](./MASTER_REPORT.md) | التدقيق الكامل |
| [APPENDIX-A-BUILD-EVIDENCE.md](./APPENDIX-A-BUILD-EVIDENCE.md) | أوامر وأدلة البناء |
| [APPENDIX-B-CLAIM-VERIFICATION.md](./APPENDIX-B-CLAIM-VERIFICATION.md) | تعارض ادعاءات GO السابقة |
| [APPENDIX-C-FINDINGS-REGISTER.md](./APPENDIX-C-FINDINGS-REGISTER.md) | سجل الإيجاد P0–P4 |
| [REMEDIATION_PLAN.md](./REMEDIATION_PLAN.md) | ملحق إصلاح مركّز (يشير لهذه الخطة) |
| `docs/ops/DR_RUNBOOK.md` | RPO/RTO والنسخ الاحتياطي |
| [`docs/ops/GO_LIVE_RUNBOOK.md`](../../ops/GO_LIVE_RUNBOOK.md) | Wave 13 Go-Live ops spine — **draft landed** (not executed / UNSIGNED / no Production GO) |
| [`docs/ops/HYPERCARE_RUNBOOK.md`](../../ops/HYPERCARE_RUNBOOK.md) | Wave 14 Hypercare ops spine — **draft landed** (clock not started / on-call TBD) |
| [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md) | T-7 to T+1 checklist + human signatures (UNSIGNED) |
| [runbooks/hypercare-14d.md](./runbooks/hypercare-14d.md) | Hypercare 14d template (PREPARE) |
| `salesos/docs/ONCALL_RUNBOOK.md` | On-call |
| `salesos/.github/workflows/deploy-production.yml` | مسار نشر الإنتاج (K8s/GHCR) |

---

## 1. الرؤية والهدف

### الرؤية
إطلاق **Production GA لـ SalesOS** كأول منتج تشغيلي على منصة، بجودة بوابات CI خضراء، عزل مستأجرين مثبت، مخطط قاعدة بيانات عند Alembic head، صور تشغيل متزامنة مع المصدر، ومراقبة/نسخ احتياطي قابلة للتمرين — مع **صدق تسويقي** حول قدرات AI (لا تسويق stubs كمنتج جاهز).

### الهدف القابل للقياس
الانتقال من **NO-GO (38/100)** إلى **قرار GO موثّق بأدلة** لإطلاق SalesOS Production، وفق Definition of Done في §3، بعد إغلاق كل بنود **P0** وبنود **P1 الأمنية/التشغيلية** المحددة في هذه الخطة.

### معايير النجاح (Success criteria)

1. CI: `lint` + `tsc` + `build` + unit tests الحرجة **خضراء** على commit الإطلاق.
2. كل بيئات الإطلاق عند **Alembic head = 0038** (أو أحدث head وقت الإطلاق) مع تحقق آلي.
3. لا IDOR/SSRF/CSRF-bypass معروفة من سجل التدقيق دون إصلاح + اختبارات.
4. صور FE/BE مبنية من commit معتمد؛ مسارات GA الحرجة **200** على staging ثم production smoke.
5. وثائق GO السابقة **مُلغاة/مُستبدَلة**؛ PRC جديد مربوط بأدلة.
6. نطاق الإطلاق معلن صراحة: **SalesOS GA ≠ multi-product GA**.
7. DR: تمرين restore واحد على الأقل **مُنفَّذ وموثّق** قبل GO (أو استثناء CTO موقّع).

### غير الأهداف (Non-goals) لهذه الخطة

- بناء AuditOS / DecisionOS / LocalContentOS كاملة.
- إعادة هندسة كاملة للمنصة أو استخراج `packages/core` قبل استقرار SalesOS.
- تحميل/chaos/pentest كاملين كشرط مسبق لكل موجة (تُجدول في Waves 7–11 و9).
- إصلاح كل تحذيرات Tailwind / دين تقني P3–P4 قبل الإطلاق.
- إثبات «AI-native OS» بينما `feature_ai_copilot=False` والـ runtimes stubs.

---

## 2. الوضع الحالي (Evidence-based)

| البُعد | الدرجة | الحالة |
|--------|------:|--------|
| Production Readiness | **38** | NO-GO |
| Security | **48** | NO-GO للأمان الإنتاجي |
| Testing | **52** | suite موجود؛ التنفيذ الجزئي غير أخضر |
| DevOps | **62** | compose مزدوج؛ drift ترحيل؛ صورة FE متأخرة |
| Product Readiness | **45** | SalesOS واسع؛ منصة غير موجودة كوداً |

**حُكم التدقيق (2026-07-22):** Production GA **NO-GO** · External pilot **NO-GO** · Demo داخلي فقط بشروط بعد إغلاق P0.

### أبرز الأدلة التشغيلية (APPENDIX-A)

| إشارة | النتيجة |
|-------|---------|
| `npm run lint` / `build` في `salesos/frontend` | **FAIL** — hooks في `TenantList.tsx` |
| `npx tsc --noEmit` | **FAIL** — 3 أخطاء |
| Alembic في الحاوية | current **0033** vs heads **0038** |
| `pytest tests/unit` (جزئي) | 213 passed / 4 failed / 16 errors (+ mcp collection) |
| `/health/detailed` | DB ok؛ cache/graph/kafka **not_configured**؛ Neo4j **unhealthy** |
| مسارات FE على الصورة الجارية | `/copilot`, `/analytics`, `/marketplace`, … **404** رغم وجود `page.tsx` في المصدر |
| Auth بدون header | **422** بدل **401** |
| Poetry على Windows host | **FAIL** (asyncpg / Python skew) |
| Browser E2E / load / pentest | **لم تُنفَّذ** — يحتاج تحقق لاحقاً |

### تعارض الحوكمة
`docs/vnext/reports/GO_NO_GO_DECISION.md` و`GA_CHECKLIST.md` يدّعيان GO — **مُناقضان** للأدلة التنفيذية. المصدر الموثوق: هذا التدقيق + أوامر CI/runtime.

---

## 3. تعريف "Production Ready" — Definition of Done

لا يُمنح تصنيف **pilot-ready** أو **production-ready** إلا بعد استيفاء القائمة التالية بأدلة (روابط CI، لقطات health، تقارير اختبار):

### أ) الجودة والبناء
- [ ] Frontend: `npm run lint` و`npx tsc --noEmit` و`npm run build` خضراء على CI
- [ ] Backend unit (+ تكامل حرج) أخضر في Docker/CI؛ لا أخطاء جمع `mcp` غير مُدارة
- [ ] لا أخطاء ESLint مانعة للـ Next production build

### ب) البيانات والمخطط
- [ ] `alembic current == heads` في staging وproduction قبل فتح حركة المرور
- [ ] بوابة نشر تفشل إن كان الـ DB خلف الـ head
- [ ] تحقق جداول 0034–0038 (companies columns, employee_*, marketplace, admin, decision_center)

### ج) الأمن متعدد المستأجرين
- [ ] Decision Center by-ID يفلتر `(id, tenant_id)` → 404 عند عدم التطابق
- [ ] Webhooks: منع SSRF (RFC1918/metadata) + تخزين Postgres (لا InMemory افتراضي للإنتاج)
- [ ] KG SQL fallback معطّل في prod أو مُقيَّد بـ `tenant_id`
- [ ] CSRF لا يُتخطى إلا بعد مصادقة API key ناجحة؛ rate-limit لا يثق ببادئة Bearer وحدها
- [ ] Auth failures → **401/403** وليس 422 للغياب
- [ ] Forecast لا يستخدم `demo-1` خارج `DEMO_MODE=true`

### د) التشغيل والصور
- [ ] صور FE/BE من commit الإطلاق؛ smoke routes تطابق جرد GA
- [ ] مصفوفة degraded موقّعة إن بقي Kafka/Neo4j اختياريين
- [ ] Redis/cache مُهيأ إن كان ضمن نطاق GA؛ وإلا موثّق كـ out-of-scope

### هـ) المراقبة وDR
- [ ] Prometheus scrape لـ `/metrics` بدون إجبار JWT مستخدم (مسار شبكة/bearer منفصل)
- [ ] تنبيهات S1/S2 مربوطة (راجع `salesos/infra/monitoring/alerts.yml` — **يحتاج تحقق** على staging)
- [ ] تمرين restore واحد موثّق؛ RPO/RTO معلنة ومقبولة من CTO

### و) الحوكمة والمنتج
- [ ] `AGENTS.md` موجود ويعرّف حدود المنصة / SalesOS
- [ ] وثائق GO القديمة موسومة **superseded**
- [ ] Feature flags صادقة؛ لا تسويق copilot إن `feature_ai_copilot=False`
- [ ] نطاق الإطلاق: **SalesOS GA فقط**

### ز) Go-Live
- [ ] Staging soak ≥ 48–72 ساعة بدون P0 جديدة
- [ ] Runbook Go-Live (Wave 13) مكتمل وتوقيعات بشرية — **draft landed** (ops + checklist; not executed / UNSIGNED / no Production GO): [`docs/ops/GO_LIVE_RUNBOOK.md`](../../ops/GO_LIVE_RUNBOOK.md) · [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md)
- [ ] خطة Hypercare (Wave 14) بمالك on-call — **draft landed** (template ready; on-call owner **TBD**; clock post-GO only): [`docs/ops/HYPERCARE_RUNBOOK.md`](../../ops/HYPERCARE_RUNBOOK.md) · [runbooks/hypercare-14d.md](./runbooks/hypercare-14d.md)

**تصنيف بعد الاستيفاء المتوقع:** يُعاد تقييم Production Readiness بأدلة جديدة — **لا يُفترض سلفاً رقم معين**.

---

## 4. برنامج التنفيذ الكامل (Waves 0–14)

> موجات 0–7 تغطي إغلاق فجوات التدقيق. موجات 8–14 تحوّل النظام إلى برنامج إنتاج تشغيلي.  
> الأوامر الثقيلة (`npm run build/test` الكامل، `prisma`/`alembic` على إنتاج، `npm install`) تتطلب **موافقة صريحة**.

### ملخص الموجات

| Wave | الاسم | التركيز | مخرجات القبول | تقدير (1–2 مهندس) |
|------|-------|---------|---------------|-------------------|
| **0** | Unblock build | lint/tsc/build FE | CI stage-1 أخضر | 1–2 يوم |
| **1** | Alembic | 0033→0038 + بوابة | DB = head | 0.5–1 يوم + تحقق |
| **2** | Security P0 | IDOR/SSRF/KG/Forecast | اختبارات عزل + harden | 4–7 أيام |
| **3** | Test green | unit/admin/mcp/intelligence | pytest unit أخضر (أو حجر صحي) | 2–4 أيام |
| **4** | Runtime/infra | Neo4j/cache/kafka/FE image | health + route parity | 2–4 أيام |
| **5** | Auth/API | 401، CSRF، rate-limit، metrics | عقود HTTP صحيحة | 1–2 يوم |
| **6** | AI honesty | flags، stubs، قرار منتج | لا تسويق كاذب | 1–3 أيام (+ قرار) |
| **7** | Governance | AGENTS.md، supersede GO | مصدر حقيقة واحد | 1–2 يوم |
| **8** | Observability & SLOs | logs/traces/alerts | SLIs حية على staging | 3–5 أيام |
| **9** | Security prod | secrets، scanners، OWASP | checklist موقّع | 3–5 أيام |
| **10** | Data/backup/DR drill | seed، backup، restore | تقرير drill | 2–4 أيام |
| **11** | Staging parity + soak | بيئات متماثلة | soak report | 1–1.5 أسبوع |
| **12** | Deploy strategy | rolling/BG، rollback، flags | runbook نشر | 2–3 أيام |
| **13** | Go-Live | T-7…T+1 | قرار GO بشري | 1 أسبوع تقويمي |
| **14** | Hypercare | 14 يوم أول | تقرير استقرار | 2 أسابيع تقويمية |

**ملاحظة ترقيم:** أُدرجت **Wave 2 = Security P0** قبل اخضرار الاختبارات لأن IDOR/SSRF يحجبان أي GO حتى لو كان البناء أخضر. Wave «Test green» أصبحت **3** (كانت 2 في المسودة الأولية).

---

## 5. بنود العمل التفصيلية

ترقيم البرنامج: `PROD-W{n}-{seq}` مع ربط `GA-*` من APPENDIX-C.

---

### Wave 0 — Unblock build (P0)

#### PROD-W0-001 — إصلاح ESLint المانع للبناء
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W0-001 |
| **Severity** | P0 |
| **المشكلة** | أخطاء ESLint تمنع `npm run lint` و`npm run build` |
| **الدليل** | APPENDIX-A؛ `salesos/frontend/src/features/admin/widgets/TenantList.tsx:28` يستدعي `useUpdateAdminTenant(id)` داخل `handleToggleActive`؛ أيضاً `admin-queries.test.tsx` display-name؛ `dashboard-metrics-header.tsx` raw `<a>`؛ `SearchHeader.tsx` unescaped entities |
| **السبب الجذري** | انتهاك Rules of Hooks؛ مخالفات ESLint أخرى تُعامل كأخطاء في بناء Next |
| **خطوات الإصلاح** | 1) نقل منطق التحديث لمستوى المكوّن (مثلاً mutation بمعرّف ديناميكي عبر `mutate({ id, … })` أو خريطة hooks وفق نمط `adminQueries` الحالي — **يحتاج تحقق** من توقيع الـ hook). 2) إصلاح display-name في الاختبار. 3) استبدال `<a>` بـ `Link` من Next. 4) تهريب علامات الاقتباس في `SearchHeader`. 5) إعادة `npm run lint` (بموافقة). |
| **معيار القبول** | `npm run lint` exit 0 في `salesos/frontend` |
| **الجهد** | S (0.5–1 يوم) |
| **المخاطر/الاعتماديات** | قد يظهر أن توقيع `useUpdateAdminTenant` يحتاج تعديلاً بسيطاً في `@/lib/hooks/adminQueries` |
| **المالك** | Frontend |
| **ربط التدقيق** | GA-P0-01 |

#### PROD-W0-002 — إصلاح أخطاء TypeScript الثلاثة
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W0-002 |
| **Severity** | P0 |
| **المشكلة** | `tsc --noEmit` يفشل بـ 3 أخطاء |
| **الدليل** | `automation/analytics/page.tsx:278` (Workflow كنوع)؛ `ExecutionTimeline.tsx:89` cast غير آمن؛ `dashboard-loading.tsx:13` prop `style` على Skeleton |
| **السبب** | سوء استخدام أنواع / عدم تطابق props |
| **خطوات** | 1) استيراد/تعريف نوع Workflow الصحيح. 2) تضييق أو تحويل آمن لـ `StepResultEntry[]`. 3) توسيع `SkeletonProps` أو إزالة `style`. 4) `npx tsc --noEmit` أخضر. |
| **قبول** | tsc exit 0 |
| **الجهد** | S (≤0.5 يوم) |
| **المالك** | Frontend |
| **ربط** | GA-P0-02 |

#### PROD-W0-003 — إنتاج artifact أمامي
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W0-003 |
| **Severity** | P0 |
| **المشكلة** | لا يوجد بناء إنتاج موثوق من المصدر الحالي |
| **الدليل** | `npm run build` FAIL بسبب ESLint |
| **خطوات** | بعد W0-001/002: `npm run build` بموافقة؛ أرشفة hash الـ build في PRC |
| **قبول** | build أخضر؛ صورة قابلة للدفع لاحقاً |
| **الجهد** | S |
| **اعتمادية** | W0-001، W0-002 |
| **المالك** | Frontend / DevOps |

---

### Wave 1 — Schema & Alembic (P0)

#### PROD-W1-001 — ترقية 0033 → 0038 في بيئة غير إنتاجية أولاً
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W1-001 |
| **Severity** | P0 |
| **المشكلة** | DB التشغيلي متأخر 5 مراجعات عن head |
| **الدليل** | `alembic current=0033`, `heads=0038`؛ ملفات: `0034_add_missing_company_columns.py` … `0038_consolidate_init_db_tables.py` تحت `salesos/backend/app/alembic/versions/` |
| **السبب** | ترحيلات مكتوبة وغير مُطبَّقة على البيئة الجارية |
| **خطوات** | 1) نسخة احتياطية `pg_dump`. 2) في staging/local: `alembic upgrade head` داخل حاوية backend. 3) التحقق من الجداول/الأعمدة الجديدة. 4) smoke API للمسارات المعتمدة على المخطط. 5) توثيق أوامر الإنتاج لـ Wave 10/13. |
| **قبول** | `alembic current` = `0038` (أو head الحالي) |
| **الجهد** | S–M (0.5–1 يوم) |
| **المخاطر** | فشل ترحيل على بيانات حقيقية؛ قفل جداول — نفّذ أولاً على نسخة |
| **المالك** | Backend / DevOps |
| **ربط** | GA-P0-03 |

#### PROD-W1-002 — بوابة «migrate before traffic»
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W1-002 |
| **Severity** | P1 (تشغيلي حرج لـ GA) |
| **المشكلة** | لا يوجد إنفاذ آلي يمنع التشغيل بـ schema متأخر |
| **الدليل** | بيئة تدقيق وصلت 0033 بينما الكود 0038 |
| **خطوات** | 1) Job pre-deploy: `alembic upgrade head` + `alembic check`/`heads` مقارنة. 2) خيار: health/readiness يفشل إن `current != head` في الإنتاج. 3) ربط بـ `deploy-production.yml` / staging compose. |
| **قبول** | نشر يفشل عند drift؛ وثيقة runbook محدّثة |
| **الجهد** | M (1–2 يوم) |
| **المالك** | DevOps |
| **ربط** | GA-P0-03 |

---

### Wave 2 — Security P0 (حجب GO)

#### PROD-W2-001 — Decision Center IDOR
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W2-001 |
| **Severity** | P0 |
| **المشكلة** | قراءة قرار بالمعرّف فقط بدون `tenant_id` |
| **الدليل** | `salesos/backend/domains/decision_center/postgres_repo.py` — `get_decision` يفلتر `DecisionModel.id` فقط؛ بينما `list_decisions` يستخدم tenant في metadata |
| **السبب** | نقص تفويض على مسارات by-ID (قرار/تغذية/تدقيق — مشابه حسب التدقيق) |
| **خطوات** | 1) تعديل `get_decision` (وإخوة by-ID) لشرط `(id, tenant_id)`. 2) تمرير `tenant_id` من سياق المصادقة في الراوتر. 3) إرجاع 404 عند عدم التطابق. 4) اختبارات تكامل مستأجرين A/B. |
| **قبول** | مستأجر A لا يقرأ قرار B؛ اختبار أخضر |
| **الجهد** | M (1–2 يوم) |
| **المالك** | Backend |
| **ربط** | GA-P0-SEC-01 |

#### PROD-W2-002 — Webhook SSRF + Postgres persistence
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W2-002 |
| **Severity** | P0 |
| **المشكلة** | نشر إلى `sub.url` عبر httpx بلا allowlist؛ افتراضي InMemory |
| **الدليل** | `modules/webhooks/service.py`؛ مستودعات `InMemoryWebhook*Repository` |
| **خطوات** | 1) تحقق URL: HTTPS فقط، حظر RFC1918/link-local/metadata، حماية DNS rebinding حيث ممكن. 2) مستودع Postgres + wiring في factory/router. 3) اختبارات وحدة للرفض على IPs خاصة. |
| **قبول** | لا توصيل لـ 169.254.169.254 / 10.x؛ الاشتراكات تبقى بعد إعادة التشغيل |
| **الجهد** | M–L (2–3 أيام) |
| **المالك** | Backend |
| **ربط** | GA-P0-SEC-02 |

#### PROD-W2-003 — Knowledge graph SQL بدون tenant + DIE memory
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W2-003 |
| **Severity** | P0 |
| **المشكلة** | مسارات SQL fallback تقرأ `companies`/`contacts`/`graph_edges` بدون `tenant_id`؛ DIE memory-primary حسب التدقيق |
| **الدليل** | `runtime/knowledge_graph_runtime/repository.py` (استعلامات `sa_text` بدون tenant)؛ قرار DIE — **جزء static؛ لم يُستغل وقت التشغيل في التدقيق** |
| **خطوات** | 1) في prod: تعطيل SQL fallback أو إضافة predicates مستأجر. 2) مراجعة `decision_runtime` accept/execute لتمر عبر Postgres بـ `(id, tenant_id)`. 3) اختبارات عزل. |
| **قبول** | لا استعلام GA-path بدون tenant في prod؛ DIE لا يعتمد الذاكرة كمصدر حقيقة |
| **الجهد** | L (3–5 أيام) |
| **ملاحظة** | يحتاج تحقق تشغيلي إضافي بعد الإصلاح |
| **المالك** | Backend / Security |
| **ربط** | GA-P0-SEC-03 |

#### PROD-W2-004 — Forecast لا يستخدم demo في الإنتاج
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W2-004 |
| **Severity** | P0 |
| **المشكلة** | بعد فحص `DEMO_MODE` ما زال المسار يبني `CommercialInput(opportunity_id="demo-1", …)` |
| **الدليل** | `app/routers/commercial.py` ~302–310 |
| **خطوات** | 1) فرع صارم: إن لم يكن demo → تحميل فرص حقيقية للمستأجر. 2) رفض/خطأ واضح إن لا بيانات. 3) اختبار وحدة لفرعي demo/prod. |
| **قبول** | مع `DEMO_MODE=false` لا يظهر `demo-1` في المدخلات |
| **الجهد** | S–M (1 يوم) |
| **المالك** | Backend |
| **ربط** | GA-P0-05 |

---

### Wave 3 — Test green (P0)

#### PROD-W3-001 — استقرار مجموعة unit
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W3-001 |
| **Severity** | P0 |
| **المشكلة** | unit غير أخضر: فشل intelligence؛ أخطاء admin AttributeError؛ جمع mcp يكسر بدون الحزمة |
| **الدليل** | APPENDIX-A: 213 passed, 4 failed, 16 errors؛ `ModuleNotFoundError: mcp` |
| **خطوات** | 1) إضافة `mcp` اختياري في extras أو حجر `test_mcp_server.py` إن خارج نطاق GA. 2) إصلاح `tests/unit/test_admin_api.py` AttributeError. 3) إصلاح 4 اختبارات intelligence grounding/LLM. 4) إعادة تشغيل unit في Docker بموافقة. |
| **قبول** | `pytest tests/unit` أخضر (أو سياسة حجر موثّقة + suite حرج أخضر 100%) |
| **الجهد** | M–L (2–4 أيام) |
| **المالك** | Backend |
| **ربط** | GA-P0-04 |

#### PROD-W3-002 — عقد اختبارات أمن الانحدار
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W3-002 |
| **Severity** | P1 |
| **المشكلة** | إصلاحات Wave 2 بلا حماية من الانحدار |
| **خطوات** | اختبارات IDOR/SSRF/CSRF/401 ضمن CI |
| **قبول** | اختبارات جديدة خضراء في CI |
| **الجهد** | M (1–2 يوم) |
| **اعتمادية** | Wave 2 |
| **المالك** | Backend |

---

### Wave 4 — Runtime / infra (P1)

#### PROD-W4-001 — إعادة بناء صورة Frontend ومطابقة المسارات
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W4-001 |
| **Severity** | P1 |
| **المشكلة** | الصورة الجارية تُرجع 404 لمسارات موجودة في المصدر |
| **الدليل** | HTTP 404: `/copilot`, `/analytics`, `/marketplace`, `/employees`, `/knowledge`, `/signals`, `/rules`, `/activities` |
| **خطوات** | 1) بعد Wave 0: بناء صورة من commit. 2) نشر staging. 3) جدول smoke للمسارات. |
| **قبول** | المسارات ضمن نطاق GA = 200 (أو redirect مقصود) |
| **الجهد** | S–M (1 يوم) |
| **اعتمادية** | W0-003 |
| **المالك** | DevOps / Frontend |
| **ربط** | GA-P1-01 |

#### PROD-W4-002 — Redis/cache و Neo4j و Kafka
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W4-002 |
| **Severity** | P1 |
| **المشكلة** | `/health/detailed`: cache/graph/kafka **not_configured**؛ Neo4j unhealthy |
| **خطوات** | 1) إصلاح healthcheck/اتصال Neo4j. 2) تهيئة Redis URL وطبقة الكاش. 3) قرار منتج: Kafka مطلوب لـ GA أم `in_memory` مقبول مع إعلان degraded. 4) تنبيه عند degraded. |
| **قبول** | مصفوفة صحة موقّعة؛ لا «healthy» كاذب للمكونات المطلوبة |
| **الجهد** | M (2–3 أيام) |
| **المالك** | DevOps / Backend |
| **ربط** | GA-P1-02 |

#### PROD-W4-003 — توحيد Compose للمراقبة (جزئي)
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W4-003 |
| **Severity** | P2 |
| **المشكلة** | Loki/OTel في root compose وليست في `salesos/docker-compose.yml` |
| **خطوات** | إما دمج المكدس أو وثيقة «stack التشغيلي المعتمد» واحد |
| **قبول** | بيئة staging تطابق وثيقة المراقبة المعتمدة |
| **الجهد** | M (2–3 أيام) — يمكن تأجيل جزء لـ Wave 8 |
| **المالك** | DevOps |
| **ربط** | GA-P2-03 |

#### PROD-W4-004 — استقرار healthcheck Postgres
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W4-004 |
| **Severity** | P2 |
| **المشكلة** | postgres flapping unhealthy→healthy أثناء التدقيق |
| **خطوات** | مراجعة فترة/أوامر healthcheck؛ **يحتاج تحقق** إن كان عارضاً لـ Docker Desktop |
| **قبول** | لا رفرفة مستمرة على staging Linux |
| **الجهد** | S |
| **المالك** | DevOps |
| **ربط** | GA-P2-04 |

---

### Wave 5 — Auth / API contracts (P1)

#### PROD-W5-001 — CSRF لا يُتخطى بمجرد وجود X-API-Key
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W5-001 |
| **Severity** | P1 |
| **المشكلة** | أي قيمة غير فارغة في `x-api-key` تتخطى CSRF بلا تحقق |
| **الدليل** | `common/middleware.py:388-391` |
| **خطوات** | تخطي CSRF فقط بعد مصادقة مفتاح ناجحة وكتابة حالة الطلب |
| **قبول** | مفتاح وهمي لا يتخطى CSRF؛ مفتاح صالح يفعل |
| **الجهد** | S (0.5 يوم) |
| **المالك** | Backend |
| **ربط** | GA-P1-SEC-01 |

#### PROD-W5-002 — Rate-limit لا يثق ببادئة Bearer فقط
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W5-002 |
| **Severity** | P1 |
| **المشكلة** | وجود `Authorization: Bearer ` يرفع الطبقة دون تحقق JWT |
| **الدليل** | `common/middleware.py` (فحوصات بادئة Bearer) |
| **خطوات** | ربط الطبقة بحالة مصادقة موثّقة أو فشل التحقق |
| **قبول** | Bearer مزيف ≠ طبقة authenticated |
| **الجهد** | S (0.5 يوم) |
| **المالك** | Backend |
| **ربط** | GA-P1-SEC-02 |

#### PROD-W5-003 — 401 بدل 422 عند غياب التوثيق
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W5-003 |
| **Severity** | P1 |
| **المشكلة** | غياب `authorization` → 422 validation |
| **الدليل** | APPENDIX-A probes |
| **خطوات** | اعتمادية/exception handler مخصّص يعيد 401/403؛ الإبقاء على 422 لأخطاء جسم حقيقية |
| **قبول** | مسار محمي بدون header → 401؛ GraphQL يبقى متسقاً |
| **الجهد** | S–M (1 يوم) |
| **المالك** | Backend |
| **ربط** | GA-P1-07 |

#### PROD-W5-004 — مسار `/metrics` للـ scrape
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W5-004 |
| **Severity** | P1 |
| **المشكلة** | `/metrics` يتطلب Authorization كمسارات المستخدم |
| **خطوات** | مسار scrape منفصل: شبكة داخلية + bearer تشغيلي أو إلغاء JWT للمستخدم؛ سياسة شبكة K8s |
| **قبول** | Prometheus يجمع بدون JWT مستخدم؛ غير معرّض علناً |
| **الجهد** | M (1 يوم) |
| **المالك** | DevOps / Backend |
| **ربط** | GA-P1-09 |

#### PROD-W5-005 — DX للمطورين على Windows
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W5-005 |
| **Severity** | P1 |
| **المشكلة** | Poetry/asyncpg يفشل على host؛ Python 3.11 vs CI 3.12 |
| **خطوات** | وثيقة: Docker-only أو WSL + Python 3.12؛ لا يعتمد الإنتاج على host Windows |
| **قبول** | README/AGENTS يوضح المسار المعتمد |
| **الجهد** | S–M (1–2 يوم وثائق/أداة) |
| **المالك** | Docs / DevOps |
| **ربط** | GA-P1-08 |

---

### Wave 6 — AI readiness / صدق الأعلام (P1)

#### PROD-W6-001 — قرار سطح Decision Engine في الواجهة
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W6-001 |
| **Severity** | P1 |
| **المشكلة** | ستة `throw new Error('Not implemented')` في `@salesos` decision package |
| **الدليل** | `frontend/packages/platform/decision/index.ts` |
| **خطوات** | ربط بـ Decision Center API **أو** إخفاء المسارات من GA + تحديث الاختبارات التي تتوقع Not implemented |
| **قبول** | لا مسار GA يستدعي stubs؛ أو stubs خارج التنقل |
| **الجهد** | M (2–4 أيام إن ربط؛ 0.5 يوم إن إخفاء) |
| **المالك** | Frontend / Product |
| **ربط** | GA-P1-PROD-01 |

#### PROD-W6-002 — أعلام AI وstubs التشغيل
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W6-002 |
| **Severity** | P1 |
| **المشكلة** | `feature_ai_copilot=False`؛ agent/workflow/scheduler/execution/simulation stubs |
| **الدليل** | `app/config.py`؛ خريطة runtime في MASTER_REPORT |
| **خطوات** | 1) إبقاء الأعلام false للإطلاق ما لم يُثبَت. 2) إزالة مسارات التسويق. 3) خارطة طريق منفصلة بعد GA. |
| **قبول** | بيان إطلاق صادق؛ لا «AI-native GA» في الملاحظات |
| **الجهد** | S–M (قرار منتج + 1 يوم وثائق/إخفاء) |
| **المالك** | Product / AI / Docs |
| **ربط** | GA-P1-06 |

#### PROD-W6-003 — قرار نطاق المنصة
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W6-003 |
| **Severity** | P1 |
| **المشكلة** | لا كود/وثائق لمنتجات المنصة الأخرى |
| **خطوات** | قرار CTO موقّع: **SalesOS GA فقط**؛ platform لاحقاً |
| **قبول** | جملة نطاق في PRC وAGENTS.md |
| **الجهد** | S (قرار) |
| **المالك** | Product / CTO |
| **ربط** | GA-P1-05 |

---

### Wave 7 — Governance docs (P1)

#### PROD-W7-001 — إنشاء AGENTS.md (+ قواعد Cursor اختيارية)
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W7-001 |
| **Severity** | P1 |
| **المشكلة** | لا يوجد `AGENTS.md` / `.cursor/rules` |
| **الدليل** | Glob = 0؛ APPENDIX-B |
| **خطوات** | كتابة AGENTS.md: حدود المنتجات، بروتوكول أوامر ثقيلة، evidence gates، SalesOS-first |
| **قبول** | الملف في جذر المستودع |
| **الجهد** | S–M (1 يوم) |
| **المالك** | Docs |
| **ربط** | GA-P1-04 |

#### PROD-W7-002 — إلغاء تعارض GO/NO-GO
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W7-002 |
| **Severity** | P1 |
| **المشكلة** | وثائق vnext تتعارض |
| **الدليل** | APPENDIX-B |
| **خطوات** | وسم `GO_NO_GO_DECISION.md` / `GA_CHECKLIST.md` كـ **superseded by 2026-07-22 audit**؛ PRC جديد بعد Waves الحرجة |
| **قبول** | لا مهندس يقرأ GO قديم كمصدر حقيقة |
| **الجهد** | S (1 يوم) |
| **المالك** | Docs / CTO |
| **ربط** | GA-P1-03 |

---

### Wave 8 — Observability & SLOs

#### PROD-W8-001 — تفعيل مكدس المراقبة على بيئة الإطلاق المعتمدة
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W8-001 |
| **Severity** | P1 (تشغيلي) |
| **المشكلة** | انقسام observability؛ latencies عالية لـ `/health` و`/metrics` في السجلات |
| **الدليل** | root vs salesos compose؛ logs حتى ~1.8s `/health` و~3.5s `/metrics` |
| **خطوات** | 1) اعتماد stack واحد (compose أو K8s: Prometheus/Grafana/Alertmanager؛ OTel/Loki حسب الهدف). 2) لوحات حداً أدنى: error rate، latency، DB، queue. 3) **يحتاج تحقق** لروابط `monitoring.salesos.com` في ONCALL إن كانت حية. |
| **قبول** | مقاييس حية على staging ≥ 72 ساعة |
| **الجهد** | M–L (3–5 أيام) |
| **المالك** | DevOps |

#### PROD-W8-002 — تعريف SLI/SLO واقعية (مقترحة)
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W8-002 |
| **Severity** | P2 |
| **المشكلة** | لا شهادة أداء GA؛ لا load test في التدقيق |
| **SLOs مقترحة (ابتدائية — تُراجع بعد soak)** | Availability API `/ping` ≥ 99.5% شهرياً؛ نجاح كتابة أعمال حرجة ≥ 99%； p95 لـ `/health/live` < 200ms؛ p95 APIs قائمة شركات < 1s على بيانات staging؛ Error rate 5xx < 1% |
| **خطوات** | ترميز قواعد في `infra/monitoring/alerts.yml`؛ مراجعة بعد Wave 11 |
| **قبول** | وثيقة SLO موقّعة + تنبيهات مربوطة |
| **الجهد** | M |
| **المالك** | DevOps / Backend |
| **ملاحظة** | القيم **مقترحة** وليست مُقاسة إنتاجياً — يحتاج تحقق |

---

### Wave 9 — Security hardening & secrets (إنتاج)

#### PROD-W9-001 — إدارة الأسرار
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W9-001 |
| **Severity** | P1 |
| **المشكلة** | قوالب أسرار/نشر تحتاج انضباط إنتاج |
| **الدليل** | إشارات `secrets.yaml` قوالب؛ GitHub `environment: production` في workflow — **يحتاج تحقق** اكتمال الأسرار الفعلية |
| **خطوات** | 1) أسرار فقط عبر GH Secrets / K8s secrets / ASM — لا في git. 2) تدوير JWT وDB. 3) فصل مفاتيح staging/prod. |
| **قبول** | checklist أسرار مكتمل قبل T-0 |
| **الجهد** | M (2–3 أيام) |
| **المالك** | DevOps / Security |

#### PROD-W9-002 — إعادة تشغيل ماسحات الاعتماديات
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W9-002 |
| **Severity** | P1 |
| **المشكلة** | CI يملك pip-audit/npm audit/Bandit/Trivy/Semgrep لكن **لم تُعد تشغيلها** في تدقيق 2026-07-22 |
| **خطوات** | تشغيل على فرع الإطلاق بموافقة؛ معالجة Critical/High أو قبول مخاطر موقّع |
| **قبول** | تقرير scan مرفق بـ PRC |
| **الجهد** | M (1–3 أيام حسب النتائج) |
| **المالك** | Security / DevOps |
| **ملاحظة** | يحتاج تحقق — النتائج غير معروفة الآن |

#### PROD-W9-003 — قائمة OWASP تنفيذية قبل GO
انظر §9 أدناه كقائمة عمل؛ بند التتبع هنا.
| **قبول** | كل بند Critical/High مُغلق أو مستثنى بتوقيع CTO |
| **الجهد** | جزء من Waves 2+5+9 |
| **المالك** | Security |

---

### Wave 10 — Data migration / seed / backup / restore

#### PROD-W10-001 — خطة بيانات القطع (cutover)
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W10-001 |
| **Severity** | P1 |
| **المشكلة** | ترحيلات + بيانات Notion/identity في `data/` منفصلة عن مسار GA التشغيلي |
| **خطوات** | 1) تحديد إن كان الإنتاج يبدأ فارغاً أم باستيراد. 2) إن استيراد: سكربت معتمد + dry-run على staging. 3) عدم خلط scrapers الجذر مع مسار الإنتاج دون مراجعة. |
| **قبول** | وثيقة cutover بيانات بتوقيع |
| **الجهد** | M–L حسب حجم البيانات |
| **المالك** | Backend / Data |
| **ملاحظة** | كثير من `data/` **خارج** نطاق SalesOS runtime — يحتاج قرار |

#### PROD-W10-002 — تمرين النسخ والاستعادة
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W10-002 |
| **Severity** | P0 للثقة التشغيلية قبل GO |
| **المشكلة** | DR runbook موجود؛ **التمرين غير مُثبت** في التدقيق |
| **الدليل** | `docs/ops/DR_RUNBOOK.md`؛ خدمة `backup` في compose |
| [`docs/ops/GO_LIVE_RUNBOOK.md`](../../ops/GO_LIVE_RUNBOOK.md) | Wave 13 Go-Live ops spine — **draft landed** (not executed / UNSIGNED / no Production GO) |
| [`docs/ops/HYPERCARE_RUNBOOK.md`](../../ops/HYPERCARE_RUNBOOK.md) | Wave 14 Hypercare ops spine — **draft landed** (clock not started / on-call TBD) |
| [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md) | T-7 to T+1 checklist + human signatures (UNSIGNED) |
| [runbooks/hypercare-14d.md](./runbooks/hypercare-14d.md) | Hypercare 14d template (PREPARE) |
| **خطوات** | 1) `backup-db` على staging. 2) استعادة على DB نظيف. 3) مقارنة تعدادات/ smoke. 4) تسجيل الوقت الفعلي vs RTO. |
| **قبول** | تقرير drill بتاريخ ومالك |
| **الجهد** | M (2–3 أيام) |
| **المالك** | DevOps |
| **ملاحظة** | RPO الحالي في الـ runbook حتى 24 ساعة بدون WAL — فجوة معلنة |

#### PROD-W10-003 — قرار WAL/PITR قبل أو بعد GA
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W10-003 |
| **Severity** | P2 (أو P1 إن اشترط CTO RPO <1h) |
| **المشكلة** | الهدف RPO <1h غير متحقق بدون WAL |
| **خطوات** | إما تفعيل WAL قبل GO أو قبول RPO يومي بتوقيع |
| **قبول** | قرار مكتوب في PRC |
| **الجهد** | L إن التفعيل؛ S للقبول الرسمي |
| **المالك** | CTO / DevOps |

---

### Wave 11 — Staging parity + soak

#### PROD-W11-001 — تماثل Staging مع Production
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W11-001 |
| **Severity** | P1 |
| **المشكلة** | local Docker ≠ بالضرورة staging/prod (K8s workflows موجودة) |
| **الدليل** | `deploy-staging.yml` (compose staging)؛ `deploy-production.yml` (K8s/GHCR) — **يحتاج تحقق** أن البيئات فعلاً مُدارة |
| **خطوات** | 1) جرد فروقات env/صور/أسرار/مراقبة. 2) نفس image digest من staging→prod. 3) نفس سياسات الترحيل. |
| **قبول** | جدول parity موقّع؛ صفر اختلافات حرجة مفتوحة |
| **الجهد** | M–L (3–5 أيام) |
| **المالك** | DevOps |

#### PROD-W11-002 — Soak test
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W11-002 |
| **Severity** | P1 |
| **المشكلة** | لا soak/load في التدقيق |
| **خطوات** | 48–72 ساعة staging: traffic اصطناعي خفيف + مراقبة أخطاء/ذاكرة/اتصالات DB؛ تسجيل الحوادث |
| **قبول** | تقرير soak بلا P0 جديدة؛ أو قائمة أعطال مُغلقة |
| **الجهد** | 3–5 أيام تقويمية (وقت جدار) |
| **المالك** | DevOps / Backend |
| **ملاحظة** | load كامل k6 **اختياري** لكن مُستحسن — يحتاج موافقة |

---

### Wave 12 — استراتيجية النشر والـ Rollback

#### PROD-W12-001 — اعتماد نموذج النشر
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W12-001 |
| **Severity** | P1 |
| **المشكلة** | يوجد workflow إنتاج وon-call rollback عبر `kubectl rollout undo`؛ blue/green غير مؤكد كافتراضي |
| **الدليل** | `deploy-production.yml`؛ `ONCALL_RUNBOOK.md` rollback |
| **خطوات** | 1) اعتماد **rolling update** على K8s كافتراضي GA (موجود عملياً). 2) إن لزم: canary بسيط (نسبة pods). 3) حظر نشر بدون gate CI أخضر + migrate. 4) Feature flags لقطع الميزات الخطرة. |
| **قبول** | Runbook نشر/rollback مُجرَّب على staging |
| **الجهد** | M (2–3 أيام) |
| **المالك** | DevOps |

#### PROD-W12-002 — بروتوكول Rollback
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W12-002 |
| **Severity** | P1 |
| **خطوات** | 1) معايير الإرجاع: 5xx>عتبة، فشل migrate، أمن P0. 2) `kubectl rollout undo` للخدمات. 3) سياسة ترحيل عكسية: **لا downgrade schema** إلا بخطة؛ فضّل forward-fix. 4) تبليغ Slack `#salesos-deployments`. |
| **قبول** | تدريب طاولة جافة مرة واحدة |
| **الجهد** | S–M |
| **المالك** | DevOps |

---

### Wave 13 — Go-Live runbook (T-7 / T-1 / T-0 / T+1)

> **Sprint-26 prep (2026-08-03):** ops draft **draft landed** — [`docs/ops/GO_LIVE_RUNBOOK.md`](../../ops/GO_LIVE_RUNBOOK.md). Execution + human signatures still **residual**. No cutover / Production GO claim.


#### PROD-W13-001 — جدول الإطلاق
| الزمن | الأنشطة |
|-------|---------|
| **T-7** | تجميد ميزات غير GA؛ مراجعة P0=0؛ scans؛ DR drill مكتمل؛ موافقة أصحاب المصلحة |
| **T-3** | نشر مرشح على staging؛ soak جارٍ؛ مراجعة أعلام الميزات |
| **T-1** | تغييرات مجمّدة؛ نسخة احتياطية إنتاجية (إن بيانات موجودة)؛ قائمة تحقق Go/No-Go النهائية؛ on-call معيَّن |
| **T-0** | migrate → deploy images → smoke (§13) → فتح DNS/traffic تدريجي → مراقبة مكثفة ساعة |
| **T+1** | مراجعة حوادث؛ قرار استمرار/rollback؛ بدء Hypercare رسمياً |

| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W13-001 |
| **Severity** | P0 (إجرائي) |
| **قبول** | توقيع CTO + Tech Lead على قائمة T-0 |
| **الجهد** | أسبوع تقويمي للتنسيق |
| **المالك** | CTO / DevOps / TL |
| **ops draft** | [`docs/ops/GO_LIVE_RUNBOOK.md`](../../ops/GO_LIVE_RUNBOOK.md) — **draft landed** / not executed |
| **evidence checklist** | [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md) — UNSIGNED |

---

### Wave 14 — Hypercare (14 يوماً)

> **Sprint-26 prep (2026-08-03):** ops draft **draft landed** — [`docs/ops/HYPERCARE_RUNBOOK.md`](../../ops/HYPERCARE_RUNBOOK.md). Clock **not started**; on-call names **TBD**. No GA / Production GO claim.


#### PROD-W14-001 — نافذة Hypercare
| الحقل | المحتوى |
|-------|---------|
| **ID** | PROD-W14-001 |
| **Severity** | P1 |
| **خطوات** | 1) On-call أساسي/احتياطي. 2) مراجعة يومية لـ 5xx والـ latency والترحيل. 3) حظر تغييرات غير إصلاحية أول 72 ساعة. 4) تقرير يوم 7 و14. 5) تسليم لعمليات عادية بعد استقرار. |
| **قبول** | تقريران Hypercare؛ لا P0 مفتوحة دون خطة |
| **الجهد** | 14 يوم تقويمي × تغطية on-call |
| **المالك** | DevOps / Backend / Frontend |
| **ops draft** | [`docs/ops/HYPERCARE_RUNBOOK.md`](../../ops/HYPERCARE_RUNBOOK.md) — **draft landed** / clock not started |
| **audit template** | [runbooks/hypercare-14d.md](./runbooks/hypercare-14d.md) — PREPARE |

---

### بنود P2 المتبقية (تُجدول ضمن الموجات أو الدين بعد GA)

| ID | GA ID | الملخص | الموجة المقترحة | جهد | مالك |
|----|-------|--------|-----------------|-----|------|
| PROD-P2-01 | GA-P2-01 | تحذيرات ألوان Tailwind vs tokens | بعد GA أو Wave 0 إن صارت أخطاء | L | Frontend |
| PROD-P2-02 | GA-P2-02 | `service_version` = 0.1.0 vs CHANGELOG | Wave 7/12 | S | Backend |
| PROD-P2-05 | GA-P2-05 | تسجيل مزدوج لراوتر admin | بعد GA | M | Backend |
| PROD-P2-06 | GA-P2-06 | `modules/admin/router.py` ضخم | بعد GA | L | Backend |
| PROD-P2-07 | GA-P2-07 | تعقيد KG/data fabric | بعد GA | L | Backend |
| PROD-P2-08 | GA-P2-08 | rate limit أثناء CSRF probe | Wave 5 تحقق | S | Backend |

### ملخص P3–P4 (لا تحجب GA)

| المجموعة | البنود | القرار |
|----------|--------|--------|
| **P3** | `utcnow` deprecation؛ `<img>` في TourOverlay؛ exhaustive-deps؛ نقص وثائق عربية | إصلاح تدريجي بعد الإطلاق |
| **P4** | scrapers جذر؛ التباس `sales-os/` vs `salesos/`؛ ملفات zip للتصميم | نظافة مستودع لاحقة |

---

## 6. المسار الحرج والاعتماديات

```text
W0 Build ──► W1 Alembic ──► W4 FE image/routes
    │              │
    │              ▼
    ├────────► W2 Security P0 ──► W3 Tests (+ أمن انحدار)
    │              │
    ▼              ▼
W5 Auth/API ◄──────┘
    │
    ▼
W6 AI honesty + W7 Governance (متوازيان جزئياً)
    │
    ▼
W8 Observability ──► W9 Secrets/Scans
    │
    ▼
W10 Backup/DR drill ──► W11 Staging soak
    │
    ▼
W12 Deploy/Rollback ──► W13 Go-Live ──► W14 Hypercare
```

**المسار الحرج (أطول سلسلة):**  
W0 → W2 → W3 → W4 → W8 → W10 → W11 → W13 ≈ **6–9 أسابيع** بمهندسين 1–2 (انظر §15).

**لا يمكن اختصاره بأمان:** Security P0 (W2) وMigrate (W1) وBuild (W0) وSoak (W11).

---

## 7. استراتيجية البيئات

| البيئة | الغرض | الوضع من التدقيق | المطلوب توحيده |
|--------|-------|------------------|----------------|
| **Local** | تطوير | compose يعمل؛ FE image متأخرة؛ Alembic drift؛ Poetry host مكسور | Docker-only backend؛ بناء FE من المصدر؛ migrate عند الإقلاع الاختياري |
| **Staging** | شهادة ما قبل الإنتاج | workflow موجود — **يحتاج تحقق** تشغيل فعلي | نفس image digest وmigrate gate والمراقبة |
| **Production** | حركة حقيقية | workflow K8s/GHCR — **يحتاج تحقق** | أسرار منفصلة؛ بدون DEMO_MODE؛ flags صادقة |

**قواعد:**
1. لا نشر إنتاج من محطة Windows مباشرة.
2. Staging = بروفة الإنتاج (صور + مخطط + أعلام).
3. فروقات env موثّقة في جدول parity (W11).

---

## 8. استراتيجية النشر والـ Rollback

### النشر (GA الافتراضي)
1. Tag `v*.*.*` أو `workflow_dispatch` → `deploy-production.yml`.
2. Gate: CHANGELOG + CI أخضر + `alembic upgrade` ناجح.
3. بناء/دفع صور GHCR بالـ SHA.
4. تطبيق K8s manifests (`infra/k8s`) — **rolling**.
5. Smoke آلي ثم يدوي (§13).
6. Feature flags: إبقاء AI/marketplace غير الجاهز مغلقاً.

### Rollback
| السيناريو | الإجراء |
|-----------|---------|
| خطأ تطبيق بعد deploy | `kubectl rollout undo` للخدمات المتأثرة |
| ترحيل فاشل قبل traffic | أوقف الإطلاق؛ أصلح؛ لا تفتح DNS |
| ترحيل نجح ثم خلل منطقي | forward-fix مفضّل؛ reverse migration فقط بخطة بيانات |
| حادثة أمن P0 | قطع المسار/العلم + rollback صورة + إشعار |

**Blue/Green كامل:** اختياري لاحق — ليس شرطاً إن كان rolling + rollback مُجرَّبين.

---

## 9. الأمان والامتثال للإنتاج (OWASP — قابل للتنفيذ)

| # | فئة OWASP | حالة التدقيق | إجراء إلزامي قبل GO |
|---|-----------|--------------|---------------------|
| 1 | Broken Access Control | IDOR قرار؛ KG SQL | PROD-W2-001/003 |
| 2 | Cryptographic Failures | JWT length + JWKS موجودان | تدوير أسرار W9؛ لا أسرار في git |
| 3 | Injection | SQLAlchemy غالب؛ نص خام في KG/admin | تقييد text() + tenant |
| 4 | XSS | غير مُتحقق بالمتصفح | يحتاج تحقق E2E/a11y لاحقاً؛ React default |
| 5 | CSRF | موجود لكن bypass بمفتاح | PROD-W5-001 |
| 6 | SSRF | webhooks | PROD-W2-002 |
| 7 | Security Misconfig | docs مع debug؛ CORS localhost افتراضي | ضبط CORS إنتاج؛ debug=False |
| 8 | Vulnerable Components | scanners في CI **لم تُعد** | PROD-W9-002 |
| 9 | Auth Failures | 422؛ rate-limit Bearer | PROD-W5-002/003 |
| 10 | Logging/Monitoring | جزئي | Wave 8؛ لا تسريب PII في السجلات — **يحتاج تحقق** |

**Pentest خارجي:** مُستحسن قبل إعلان أمني قوي؛ غير منفّذ في التدقيق.

---

## 10. المراقبة والتنبيه (SLI/SLO مقترحة)

| SLI | قياس | عتبة تنبيه مقترحة | مصدر |
|-----|------|-------------------|------|
| Availability | نجاح `/ping` أو blackbox | < 99% خلال 15 د → S1 | Prometheus |
| Error ratio | 5xx / requests | > 2% لـ 5 د → S2؛ > 5% → S1 | metrics |
| Latency | p95 مسارات حرجة | > 2s مستمر → S2 | metrics |
| DB | up + pool | PostgresDown → S1 | exporter |
| Migrate drift | current vs head | أي drift في prod → S1 | job مخصص |
| Neo4j/Redis | إن ضمن GA | unhealthy → S2 | health/detailed |
| Queue | Celery/Kafka depth | حسب خط الأساس بعد soak | **يحتاج تحقق** |

الرجوع إلى `salesos/infra/monitoring/alerts.yml` و`ONCALL_RUNBOOK.md` لأسماء التنبيهات — التحقق من التفعيل الفعلي **مطلوب**.

---

## 11. النسخ الاحتياطي والتعافي

من `docs/ops/DR_RUNBOOK.md` (موثّق؛ التمرين **يحتاج تنفيذ**):
| [`docs/ops/GO_LIVE_RUNBOOK.md`](../../ops/GO_LIVE_RUNBOOK.md) | Wave 13 Go-Live ops spine — **draft landed** (not executed / UNSIGNED / no Production GO) |
| [`docs/ops/HYPERCARE_RUNBOOK.md`](../../ops/HYPERCARE_RUNBOOK.md) | Wave 14 Hypercare ops spine — **draft landed** (clock not started / on-call TBD) |
| [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md) | T-7 to T+1 checklist + human signatures (UNSIGNED) |
| [runbooks/hypercare-14d.md](./runbooks/hypercare-14d.md) | Hypercare 14d template (PREPARE) |

| المقياس | الهدف الموثّق | القدرة الحالية المعلنة | فجوة |
|---------|---------------|-------------------------|------|
| **RPO** | < 1 ساعة | حتى 24 ساعة (لقطة يومية) | WAL/PITR |
| **RTO** | < 4 ساعات | ~2 ساعات من S3 (معلن) | يحتاج إثبات بـ drill |
| **Failover متعدد المناطق** | < 30 دقيقة | غير منفّذ | خارج نطاق GA الأول ما لم يطلب CTO |

**قبل GO الأدنى:** PROD-W10-002 (drill) + قرار صريح حول قبول RPO اليومي أو تفعيل WAL (PROD-W10-003).

---

## 12. بيانات الإطلاق (migrations / seeds / cutover)

1. **Migrations:** سلسلة Alembic حتى head؛ ممنوع init_db كبديل في الإنتاج.
2. **Seeds:** حسابات تشغيل/إدارة فقط؛ لا بيانات demo إن `DEMO_MODE=false`.
3. **استيراد `data/`:** اختياري ومنفصل — dry-run على staging إن لزم.
4. **Cutover:**  
   - نافذة صيانة قصيرة للترحيل إن لزم قفل.  
   - التحقق: `alembic current`، تعداد جداول حرجة، login smoke.  
5. **Rollback بيانات:** من آخر `pg_dump`/S3 — لا يُفترض PITR ما لم يُفعَّل.

---

## 13. خطة الاختبار قبل GO

| الطبقة | النطاق | متى | حالة التدقيق |
|--------|--------|-----|--------------|
| **Smoke HTTP** | `/ping`, `/health/*`, login page, 10 مسارات GA | كل نشر | جزئي سابقاً |
| **Regression unit** | backend unit + FE Jest حرج | CI | غير أخضر الآن |
| **Security smoke** | IDOR A/B، CSRF، SSRF URL، 401 | بعد Wave 2/5 | لم يُنفَّذ كحزمة |
| **E2E Playwright** | رحلة login→شركة→فرصة | قبل W13 | **لم تُنفَّذ** — يحتاج موافقة وتشغيل |
| **Browser UI** | console/a11y | قبل GO | MCP فشل — يحتاج تحقق |
| **Load** | k6 على search/companies | Wave 11 اختياري | غير منفّذ |

**بوابة GO اختبارية:** Smoke + unit حرج + security smoke إلزامية؛ E2E إلزامية إن وُجدت مواصفات للمسارات المكشوفة؛ load مُستحسن.

---

## 14. مصفوفة مخاطر الإنتاج

| الخطر | احتمال | أثر | تخفيف | بند |
|-------|--------|-----|-------|-----|
| إطلاق مع CI أحمر | عالٍ إن اتُبعت وثائق GO القديمة | حرج | إنفاذ CI | W0/W7 |
| Schema drift في prod | عالٍ (حدث محلياً) | حرج | migrate gate | W1 |
| تسريب عبر المستأجرين | متوسط/عالٍ حتى الإصلاح | حرج | W2 | W2 |
| SSRF عبر webhooks | متوسط | حرج | allowlist | W2-002 |
| تسويق AI غير موجود | متوسط | عالٍ (سمعة) | flags | W6 |
| صورة FE متأخرة | عالٍ | عالٍ | rebuild | W4-001 |
| RPO 24h غير مقبول للأعمال | متوسط | عالٍ | WAL أو قبول | W10 |
| Staging غير مطابق | متوسط | عالٍ | parity | W11 |
| غياب pentest | متوسط | متوسط | W9 + قبول مخاطر | W9 |
| Windows DX يعطّل الإصلاحات | عالٍ | متوسط | Docker/WSL | W5-005 |

---

## 15. التقدير الزمني الواقعي

**افتراض:** 1–2 مهندسين بدوام أساسي؛ موافقات أوامر ثقيلة؛ لا pentest مطوّل ضمن النافذة.

| المرحلة | أسابيع تقويمية |
|---------|----------------|
| Waves 0–3 (بناء + ترحيل + أمن + اختبارات) | 2–3 |
| Waves 4–7 (تشغيل + عقود + AI صدق + حوكمة) | 1.5–2 |
| Waves 8–10 (مراقبة + أسرار/scans + DR) | 1.5–2 |
| Waves 11–12 (soak + نشر) | 1.5–2 |
| Wave 13 تنسيق إطلاق | 1 |
| Wave 14 Hypercare | 2 (بعد الإطلاق) |
| **إلى قرار GO / يوم الإطلاق** | **≈ 7–10 أسابيع** |
| **حتى نهاية Hypercare** | **≈ 9–12 أسبوعاً** |

تسريع بموازاة W6∥W7 وW8∥W9 بعد إغلاق P0 ممكن؛ لا تختصر W2 أو W11.

---

## 16. بوابات GO/NO-GO بعد كل موجة

| بعد Wave | GO الجزئي؟ | معيار |
|----------|------------|--------|
| 0 | نعم للمتابعة فقط | lint/tsc/build خضراء |
| 1 | نعم | DB head على بيئة العمل |
| 2 | **إلزامي** | لا P0 أمني مفتوح من السجل |
| 3 | إلزامي | unit حرج أخضر |
| 4 | إلزامي للتجربة الخارجية | صور ومسارات وhealth وفق المصفوفة |
| 5 | إلزامي | 401/CSRF/rate-limit/metrics |
| 6–7 | إلزامي للحوكمة | نطاق + وثائق متسقة |
| 8–10 | إلزامي تشغيلي | مراقبة + أسرار + drill |
| 11 | إلزامي | soak بلا P0 |
| 12 | إلزامي | rollback مُجرَّب |
| 13 | **قرار CTO** | كل ما سبق + توقيعات |
| 14 | إغلاق hypercare | استقرار |

أي P0 جديدة تُكتشف → **NO-GO تلقائي** حتى الإغلاق.

---

## 17. Quick wins مقابل طويل الأمد

### Quick wins (≤ يوم واحد لكل منها)
1. إصلاح hooks في `TenantList.tsx` + بقية أخطاء ESLint الأربعة.
2. إصلاح 3 أخطاء tsc.
3. `alembic upgrade head` على نسخة غير إنتاجية.
4. حجر أو تثبيت `mcp` للاختبارات.
5. وسم وثائق GO كـ superseded + مسودة AGENTS.md.
6. إصلاح CSRF API-key وBearer rate-limit (نصف يوم لكل).

### طويل الأمد (بعد أو خارج مسار GA الضيق)
- استخراج Core مشترك لـ multi-product.
- تنفيذ runtimes stubs (agent/workflow/…).
- تفكيك `admin/router.py` الضخم.
- WAL متعدد المناطق وblue/green كامل.
- برنامج pentest ودورات chaos.

---

## 18. خارج النطاق / مؤجل (مع تبرير)

| البند | التبرير |
|-------|---------|
| بناء AuditOS/DecisionOS/LocalContentOS | لا أساس كودي؛ قرار منتج منفصل |
| إثبات «AI-native GA» | الأعلام false والـ stubs؛ صدق أفضل من ادعاء |
| Load/chaos كامل كشرط أول يوم | غير منفّذ؛ soak أخف يكفي لقرار مشروط |
| إصلاح كل تحذيرات Tailwind | P2/P3؛ لا تحجب البناء إن بقيت warnings |
| تنظيف scrapers/zip/`sales-os` | P4 نظافة |
| Prisma | غير مستخدم في نواة SalesOS (Alembic) |
| اعتماد أرقام أمنية 10/10 قديمة | مناقضة؛ مرفوضة |

---

## 19. ملحق: ربط بنود التدقيق (APPENDIX-C)

| GA ID | Severity | بند البرنامج |
|-------|----------|--------------|
| GA-P0-SEC-01 | P0 | PROD-W2-001 |
| GA-P0-SEC-02 | P0 | PROD-W2-002 |
| GA-P0-SEC-03 | P0 | PROD-W2-003 |
| GA-P0-01 | P0 | PROD-W0-001 |
| GA-P0-02 | P0 | PROD-W0-002 |
| GA-P0-03 | P0 | PROD-W1-001 / W1-002 |
| GA-P0-04 | P0 | PROD-W3-001 |
| GA-P0-05 | P0 | PROD-W2-004 |
| GA-P1-SEC-01 | P1 | PROD-W5-001 |
| GA-P1-SEC-02 | P1 | PROD-W5-002 |
| GA-P1-PROD-01 | P1 | PROD-W6-001 |
| GA-P1-01 | P1 | PROD-W4-001 |
| GA-P1-02 | P1 | PROD-W4-002 |
| GA-P1-03 | P1 | PROD-W7-002 |
| GA-P1-04 | P1 | PROD-W7-001 |
| GA-P1-05 | P1 | PROD-W6-003 |
| GA-P1-06 | P1 | PROD-W6-002 |
| GA-P1-07 | P1 | PROD-W5-003 |
| GA-P1-08 | P1 | PROD-W5-005 |
| GA-P1-09 | P1 | PROD-W5-004 |
| GA-P2-01…08 | P2 | PROD-P2-* / W4-003/004 |
| GA-P3-* / GA-P4-* | P3–P4 | ملخّصة §5 — مؤجلة |

---

## إحصاءات البرنامج (للـ CTO)

| الشدة | عدد بنود العمل التفصيلية في هذه الخطة |
|-------|--------------------------------------|
| **P0** | 8 إصلاحات تدقيق + بوابات إجرائية (W10 drill / W13) |
| **P1** | 11 من السجل + بنود تشغيل Waves 8–14 |
| **P2** | 8 من السجل (+ SLO/PITR قرارات) |
| **P3–P4** | ملخّصة (7) — غير مُفصّلة كمسار حرج |

**أولى 5 إجراءات غداً**
1. إصلاح `TenantList.tsx` hooks (PROD-W0-001).  
2. إصلاح أخطاء tsc الثلاثة (PROD-W0-002).  
3. نسخة احتياطية + `alembic upgrade head` على بيئة غير إنتاجية (PROD-W1-001).  
4. بدء تصحيح `get_decision` بفلتر tenant (PROD-W2-001).  
5. وسم `GO_NO_GO_DECISION.md` كـ superseded وبدء مسودة `AGENTS.md` (PROD-W7-*).

---

*نهاية خطة البرودكشن الكاملة. أي ادعاء «جاهز للإنتاج» بعد هذا التاريخ يتطلب PRC جديداً بأدلة أوامر وليس تحديثMarkdown وحده.*
