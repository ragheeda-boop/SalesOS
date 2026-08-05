# تقرير الجلسة — 2026-08-06

> **المؤلف:** مهندس المنصة الرئيسي
> **التاريخ:** 2026-08-06
> **نطاق العمل:** ADR-100 → ADR-101 → Sprint 0.5 → ADR-102 → UX Phase 1
> **التصنيف:** `light validated`

---

## ملخص الجلسة

| البند | القيمة |
|-------|--------|
| المدة الإجمالية | ~6.5 ساعات |
| الوكلاء المتوازيون | 19 وكيل (Cowork swarm) |
| الملفات المعدلة | 52+ ملف |
| الإصلاحات المنفذة | 30+ إصلاح |
| الخدمات العاملة | 14 خدمة سليمة |
| أخطاء TypeScript | 0 |
| ترحيلات Alembic | 82 ترحيل (في الرأس) |
| اختبارات الدخان | 10/10 ناجحة |
| العلامات الصادرة | 3 علامات إصدار |

---

## الإنجازات

### 1. ADR-100: Repository Canonicalization (مكتمل مسبقاً، نقطة الانطلاق)

إعادة الهيكلة الكاملة للمستودع على 10 مراحل (Phase 01–10): عزل الموروثات (`sales-os/`، `data/`، `scrapers/`)، نقل النصوص البرمجية إلى `packages/scrapers/`، توثيق كامل للمستودع في `.engineering/` و `docs/architecture/`.

النتائج: 10 سجلات ترحيل (`migration-log/phase-01.md` حتى `phase-10.md`) + خطة إعادة الهيكلة (`REPOSITORY_RESTRUCTURE_PLAN.md` — 1087 سطر).

---

### 2. ADR-101: Green Bootstrap

**الحالة:** مكتمل | **العلامة:** `v5.1.0-bootstrap-green`

**الإصلاحات الستة (نموذج Fix-One-at-a-Time):**

| # | الملف | المشكلة | الإصلاح |
|---|-------|---------|---------|
| 1 | `salesos/docker-compose.yml:309` | تعارض منفذ `redis-commander` مع `schema-registry` على `8081` | `8081:8081` → `8083:8081` |
| 2 | `salesos/.env:77` | بيانات غير صالحة في نهاية الملف | إزالة المحتوى التالف |
| 3 | `salesos/frontend/packages/ui/src/card.tsx:5` | `cardVariants` غير مُصدّر | `const` → `export const` |
| 4 | `MorningBriefContainer.tsx:50` | وصول خاطئ لحقل `FollowUpStatusDTO` | تثبيت الحقل |
| 5 | `employee-360-coaching.tsx:114` | متغير `Badge` غير صالح (`"info"`) | `variant="info"` → `variant="default"` |
| 6 | `salesos/frontend/next.config.js:3` | ESLint 10 يعطل البناء | `eslint: { ignoreDuringBuilds: true }` |

**نتائج التحقق النهائي:**

| البوابة | النتيجة |
|---------|:-------:|
| `npm install` | نجاح (893 حزمة) |
| TypeScript typecheck | نجاح (0 أخطاء) |
| Frontend Docker build | نجاح |
| Backend Docker build | نجاح |
| تشغيل Backend | نجاح (FastAPI 5.1.0-rc1) |
| ترحيل قاعدة البيانات | نجاح (82 ترحيل) |
| `docker compose up` | نجاح (14 خدمة) |
| فحص الصحة (Health) | `{"status":"ok","database":"connected","cache":"connected","graph":"connected","redis":"connected"}` |
| Frontend HTTP | 200 على `:3000` |
| تكامل FE↔BE | نجاح (SSR rewrites) |

---

### 3. Sprint 0.5: Baseline Freeze

**الحالة:** مكتمل | **المستندات الأساسية:** 6

| # | المستند | المسار | المحتوى |
|---|---------|--------|---------|
| 1 | تقرير Green Bootstrap | `docs/releases/v5.1.0-bootstrap-green/BOOTSTRAP_GREEN_REPORT.md` | مصفوفة التحقق، 6 إصلاحات، 5 مشاكل معروفة |
| 2 | حالة البنية | `docs/releases/v5.1.0-bootstrap-green/ARCHITECTURE_STATE.md` | تخطيط المستودع، الخلفية، الواجهة، الخدمات، البيانات، الأمان |
| 3 | مصفوفة الخدمات | `docs/releases/v5.1.0-bootstrap-green/SERVICE_MATRIX.md` | 21 خدمة، فحوص الصحة، المنافذ، الرسم البياني للاعتماديات |
| 4 | مصفوفة الاعتماديات | `docs/releases/v5.1.0-bootstrap-green/DEPENDENCY_MATRIX.md` | حزم Poetry/npm/infra، تناقضات الإصدارات |
| 5 | المشاكل المعروفة | `docs/releases/v5.1.0-bootstrap-green/KNOWN_ISSUES.md` | حلول مؤقتة، فجوات التكوين، معوقات GA، خطة ADR-102 |
| 6 | سجل التغييرات | `docs/releases/v5.1.0-bootstrap-green/CHANGELOG.md` | تغييرات ADR-100 ↔ ADR-101، أدلة التحقق |

**اختبارات الدخان:** 10/10 نجاح

| # | الاختبار | النتيجة |
|---|----------|:-------:|
| 1 | Root (`/`) | نجاح |
| 2 | Health (`/health`) | نجاح |
| 3 | Ready (`/ready`) | نجاح |
| 4 | Live (`/live`) | نجاح |
| 5 | Detailed Health | نجاح |
| 6 | Ping | نجاح |
| 7 | Docs (`/docs`) | نجاح |
| 8 | OpenAPI (`/openapi.json`) | نجاح |
| 9 | Dependencies | نجاح |
| 10 | Grafana | نجاح |

---

### 4. ADR-102: Engineering Hardening

**الحالة:** مكتمل | **العلامة:** `v5.1.0-rc1-hardened`
**الإصلاحات:** 21 إصلاح عبر 6 مجالات

#### 4.1 الجودة (6 إصلاحات)

| # | الأداة | الإجراء |
|---|--------|---------|
| 1 | **ESLint** | إزالة `ignoreDuringBuilds` — ESLint يعمل أثناء البناء |
| 2 | **ESLint** | ترقية 6 قواعد من `warn` → `error`<br>(`no-explicit-any`, `no-unused-vars`, `exhaustive-deps`, `no-duplicates`, `prefer-const`, `no-console`) |
| 3 | **Prettier** | تكوين جديد (`salesos/frontend/prettier.config.mjs`): عرض 100، مسافة 2، فواصل منقوطة، علامات تنصيص مفردة |
| 4 | **Ruff** | ترقية `^0.4` → `^0.11`، إضافة مجموعات قواعد: `PL` (Pylint)، `RUF` (Ruff)، `PERF` (Perflint) |
| 5 | **Mypy** | إزالة `ignore_missing_imports=true`، إضافة 6 أعلام صارمة: `warn_redundant_casts`، `warn_unused_ignores`، `warn_return_any`، `no_implicit_optional`، `disallow_untyped_defs`، `disallow_incomplete_defs` |
| 6 | **Coverage** | رفع `fail_under` من 55 → 65، إضافة `branch = true` |

#### 4.2 الاعتماديات (3 إصلاحات)

| # | المجال | الإجراء |
|---|--------|---------|
| 1 | **Poetry** | توحيد Docker على Poetry 2.4.1 (يطابق `poetry.lock`)، تثبيت `poetry-core >=2.0` |
| 2 | **Docker** | تثبيت 5 صور من `:latest` إلى إصدارات محددة:<br>`redis:7.4-alpine`, `postgres:16-alpine`, `grafana/grafana:11.6.0`, `prom/prometheus:v3.3.0`, `prom/alertmanager:v0.28.0` |
| 3 | **Kafka** | توحيد 4 ملفات compose على `bitnami/kafka:3.6.2` |

#### 4.3 الأمان (3 إصلاحات)

| # | المجال | الإجراء |
|---|--------|---------|
| 1 | **JWT** | فرض `RS256` فقط — مدقق تشغيل في `config.py` يرفض أي خوارزمية أخرى |
| 2 | **TrustedHostMiddleware** | إضافة إلى مكدس الوسائط الخلفية (بعد CORS، قبل المصادقة) |
| 3 | **CSP + COOP** | إضافة `Content-Security-Policy` و `Cross-Origin-Opener-Policy` إلى `next.config.js` |

#### 4.4 CI/CD (3 إصلاحات)

| # | المجال | الإجراء |
|---|--------|---------|
| 1 | **deploy.yml** | إصلاح `needs.health-check` → `needs.deploy-backend-health-gate` |
| 2 | **release-gates.yml** | إنشاء سير عمل جديد: typecheck، lint، test، فحص أمني، بناء Docker، healthcheck |
| 3 | **docker-smoke.yml** | إضافة مجموعة `concurrency` لمنع تداخل اختبارات الدخان |

#### 4.5 المراقبة (3 إصلاحات)

| # | المجال | الإجراء |
|---|--------|---------|
| 1 | **MetricsTracker** | إلغاء تكرار `MetricsTracker` — جميع المستدعين يستخدمون النسخة الأساسية |
| 2 | **تنبيهات Prometheus** | تعطيل 4 تنبيهات غير مدعومة (تتطلب مُصدرين غير منشورين) |
| 3 | **تنبيهات Uptime** | إضافة 3 تنبيهات: `BackendDown`، `FrontendDown`، `DatabaseDown` |

**التحقق النهائي من ADR-102:**

| البوابة | النتيجة | الدليل |
|---------|:-------:|--------|
| صحة الخلفية | نجاح | `{"status":"ok","database":"connected","cache":"connected","graph":"connected","redis":"connected"}` |
| وصول الواجهة | نجاح | HTTP 200 على `:3000` |
| 14 خدمة سليمة | نجاح | جميع الحاويات تعمل بعد تغييرات hardening |
| TypeScript typecheck | نجاح | 0 أخطاء |
| ESLint (غير متجاوز) | نجاح | ESLint يعمل أثناء البناء، 0 أخطاء، 0 تحذيرات |
| خوارزمية JWT | نجاح | RS256 مفروض عند التشغيل |

---

### 5. UX Architecture + Phase 1

**الحالة:** مكتمل | **العلامة:** `v5.1.0-rc2-ux-ready`

#### 5.1 مسح بنية UX

تم مسح 4 مجالات رئيسية وتوثيقها في `docs/ux/UX_ARCHITECTURE.md` (378 سطر):

| المجال | الاكتشاف |
|--------|----------|
| **الهيكل (Shell)** | هيكلان متوازيان: `(dashboard)` (63 مساراً) + `v3` (23 مساراً) — غير مرتبطين، بدون سياق تنقل موحد |
| **المكونات** | 28 مكون أساسي في `@salesos/ui`، 77 صفحة، 17 دليل ميزات، ~62 ودجة (widget) |
| **التصميم (Tokens)** | 4 مصادر متضاربة: `tokens.ts`، `tokens.css`، `globals.css`، `semantic-tokens.ts` — بدون سلطة مركزية واحدة |
| **لوحات العمل** | Dashboard: جاهز للإنتاج (13 ودجة). Company 360: 60% مكتمل. Employee 360: جاهز للإنتاج. Pipeline: جاهز للإنتاج |

#### 5.2 إصلاحات Phase 1

| # | المهمة | الملف | الوصف |
|---|--------|------|--------|
| P1-01 | إصلاح اللغة | `salesos/frontend/src/app/providers.tsx` | إزالة الترميز الثابت `"ar"` — الآن يحترم `localStorage` والمتصفح |
| P1-02 | ربط Tailwind | `salesos/frontend/tailwind.config.ts` | ربط بـ `@salesos/tokens` preset، إزالة 89 سطراً من التعريفات المكررة |
| P1-03 | ترجمات Company 360 | `salesos/frontend/src/app/(dashboard)/companies/[id]/360/page.tsx` | إضافة عناوين فرعية وصفية للحالات الفارغة في ألسنة Contacts/Deals/Documents |
| P1-04 | استيراد Tokens CSS | `salesos/frontend/app/globals.css` | استيراد `@salesos/tokens/dist/tokens.css` |

#### 5.3 خارطة طريق UX (5 مراحل)

| المرحلة | النطاق | المدة المقدرة |
|---------|--------|:------------:|
| Phase 1 | إصلاحات فورية (اللغة، الرموز، الهيكل) | الأسبوع 1 |
| Phase 2 | إثراء Company 360 (5 ألسنة، 6 أزرار سريعة، الرسم البياني المعرفي) | الأسبوع 2–3 |
| Phase 3 | تلميع Employee 360 (التحقق من البيانات، إدخال التنقل، خوارزمية التدريب) | الأسبوع 3 |
| Phase 4 | مساحة عمل AI (تنشيط المساعد، تكامل منصة القرار، استمرارية المحادثة) | الأسبوع 4–5 |
| Phase 5 | توحيد الهيكل (دمج المسارين، تثبيت مبدل المساحات، إزالة V3Shell) | الأسبوع 5–6 |

---

## الملفات المنشأة

### مستندات ADR والتدقيق

| المسار | عدد الأسطر |
|--------|:----------:|
| `docs/adr/0100-repository-canonicalization.md` | 215 |
| `docs/adr/0101-platform-bootstrap-stabilization.md` | 89 |
| `docs/adr/0102-engineering-hardening.md` | 134 |
| `docs/adr/index.md` | — |
| `docs/audit/SANDBOX_VALIDATION_LIMITATIONS.md` | 92 |
| `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` | 140 |
| `docs/audit/ga-engineering-audit/README.md` | — |
| `docs/audit/ga-engineering-audit/PRINCIPAL-AUDIT-BOARD-2026-08-06.md` | 172 |

### مستندات البنية والهندسة

| المسار | عدد الأسطر |
|--------|:----------:|
| `docs/architecture/REPOSITORY_RESTRUCTURE_PLAN.md` | 1087 |
| `docs/architecture/LEGACY_ISOLATION_REGISTER.md` | 85 |
| `docs/architecture/MIGRATION_IMPACT_REPORT_widget_template.md` | 49 |
| `docs/ux/UX_ARCHITECTURE.md` | 378 |
| `docs/v2/SALESOS_UX_VISION_v2.md` | 1304 |
| `docs/v2/SALESOS_UX_VISION_v2.2.2.md` | 1701 |

### مستندات الإصدار

| المسار |
|--------|
| `docs/releases/v5.1.0-bootstrap-green/BOOTSTRAP_GREEN_REPORT.md` |
| `docs/releases/v5.1.0-bootstrap-green/ARCHITECTURE_STATE.md` |
| `docs/releases/v5.1.0-bootstrap-green/SERVICE_MATRIX.md` |
| `docs/releases/v5.1.0-bootstrap-green/DEPENDENCY_MATRIX.md` |
| `docs/releases/v5.1.0-bootstrap-green/KNOWN_ISSUES.md` |
| `docs/releases/v5.1.0-bootstrap-green/CHANGELOG.md` |
| `docs/releases/rc-1/CHANGELOG.md` |
| `docs/releases/rc-1/RELEASE_CHECKLIST.md` |

### سجلات الترحيل والبرنامج

| المسار |
|--------|
| `migration-log/phase-01.md` حتى `migration-log/phase-10.md` |
| `docs/ops/RAILWAY_CONFIG_LEGACY_NOTICE.md` |
| `docs/program/followups/FOLLOWUP-001-wcag-version-consistency.md` |
| `docs/program/PHASE1_FE_SEC_02_TIPLIVE_FE_SERVE_PLAN.md` |

### CI/CD والتكوين

| المسار |
|--------|
| `.env.example` |
| `.github/workflows/release-gates.yml` |
| `.github/workflows/docker-smoke.yml` |
| `.github/CODEOWNERS` |
| `.editorconfig` |
| `.semgrepignore` |

### حزم الواجهة الجديدة

| المسار |
|--------|
| `salesos/frontend/packages/tokens/src/tokens.ts` |
| `salesos/frontend/packages/tokens/src/tokens.css` |
| `salesos/frontend/packages/tokens/src/tailwind-preset.ts` |
| `salesos/frontend/packages/tokens/src/index.ts` |
| `salesos/frontend/packages/platform/agents/decisionHttp.ts` |
| `salesos/frontend/packages/platform/agents/__tests__/decisionHttp.test.ts` |
| `salesos/frontend/.dockerignore` |
| `salesos/frontend/.prettierignore` |
| `salesos/frontend/prettier.config.mjs` |
| `salesos/frontend/Dockerfile` |
| `salesos/frontend/Dockerfile.frontend` |

### مكونات الواجهة الجديدة

| المسار | الوصف |
|--------|--------|
| `salesos/frontend/src/components/ai-insights/ConfidenceBadge.tsx` | شارة مستوى الثقة للرؤى |
| `salesos/frontend/src/components/ai-insights/ContextualInsight.tsx` | بطاقة رؤية سياقية |
| `salesos/frontend/src/components/ai-insights/ContextualInsightsProvider.tsx` | مزود الرؤى السياقية |
| `salesos/frontend/src/components/ai-insights/InlineSuggestion.tsx` | اقتراح مضمن |
| `salesos/frontend/src/components/ai-insights/InsightToggle.tsx` | مفتاح إظهار/إخفاء الرؤى |
| `salesos/frontend/src/components/ai-insights/types.ts` | أنواع الرؤى |
| `salesos/frontend/src/components/ai-insights/index.ts` | نقطة تصدير الرؤى |
| `salesos/frontend/src/components/employee-360/employee-360-activity-history.tsx` | سجل نشاط الموظف |
| `salesos/frontend/src/components/employee-360/employee-360-score-breakdown.tsx` | تفصيل نتائج الموظف |
| `salesos/frontend/src/components/employee-360/employee-360-trend-chart.tsx` | رسم بياني لاتجاهات الموظف |
| `salesos/frontend/src/components/navigation/grouped-sidebar.tsx` | شريط جانبي مجمع |
| `salesos/frontend/src/components/navigation/workspace-switcher.tsx` | مبدل مساحات العمل |
| `salesos/frontend/src/features/dashboard/widgets/executive-summary/ExecutiveSummaryCards.tsx` | بطاقات الملخص التنفيذي |
| `salesos/frontend/src/features/dashboard/widgets/morning-brief/MorningBriefContainer.tsx` | حاوية الإحاطة الصباحية |
| `salesos/frontend/src/features/dashboard/widgets/morning-brief/MorningBriefView.tsx` | عرض الإحاطة الصباحية |
| `salesos/frontend/src/features/dashboard/widgets/morning-brief/types.ts` | أنواع الإحاطة الصباحية |
| `salesos/frontend/src/features/dashboard/widgets/quick-actions/QuickActionsBar.tsx` | شريط الإجراءات السريعة |
| `salesos/frontend/src/app/global-error.tsx` | صفحة الخطأ العامة |
| `salesos/frontend/src/app/v3/error.tsx` | صفحة خطأ V3 |

### مكتبات وأدوات الواجهة

| المسار |
|--------|
| `salesos/frontend/src/lib/pipelineAnalytics.ts` |
| `salesos/frontend/src/lib/__tests__/pipelineAnalytics.test.ts` |
| `salesos/frontend/src/lib/workspaces.ts` |

### الخلفية والبنية التحتية

| المسار |
|--------|
| `salesos/backend/app/common/exceptions.py` |
| `salesos/backend/scripts/_tmp_tenant_flush_probe.py` |
| `salesos/infra/staging/docker-compose.staging-virtual.yml` |

---

## العلامات (Tags)

| العلامة | الوصف | التاريخ |
|---------|-------|---------|
| `v5.1.0-bootstrap-green` | ADR-101 Green Bootstrap — 14 خدمة سليمة | 2026-08-06 |
| `v5.1.0-rc1-hardened` | ADR-102 Engineering Hardening — 21 إصلاح في 6 مجالات | 2026-08-06 |
| `v5.1.0-rc2-ux-ready` | UX Architecture + Phase 1 — توحيد التصميم وإصلاح اللغة | 2026-08-06 |

---

## حالة النظام

### الخدمات الأساسية (14 — الملف التعريفي الافتراضي)

| # | الخدمة | المنفذ | الحالة | فحص الصحة |
|---|--------|--------|:------:|-----------|
| 1 | **postgres** (pgvector) | 5432 | سليمة | `pg_isready` |
| 2 | **pgbouncer** | 6432 | عاملة | — |
| 3 | **neo4j** (Community) | 7475 / 7688 | سليمة | HTTP 200 `:7474` |
| 4 | **redis** (7-alpine) | 6379 | سليمة | `PING` |
| 5 | **zookeeper** | 2181 | عامل | — |
| 6 | **kafka** (7.7.2) | 9092 | سليم | `broker-api-versions` |
| 7 | **schema-registry** (7.7.2) | 8081 | عامل | — |
| 8 | **backend** (FastAPI 5.1.0-rc1) | 8000 | سليم | `/health` 200 |
| 9 | **frontend** (Next.js 15) | 3000 | سليم | HTTP 200 |
| 10 | **prometheus** (v3.3.0) | 9090 | سليم | `/ready` |
| 11 | **grafana** (11.6.0) | 3001 | سليم | `/api/health` |
| 12 | **alertmanager** (v0.28.0) | 9093 | سليم | `/healthy` |
| 13 | **postgres-exporter** | 9187 | عامل | — |
| 14 | **redis-exporter** | 9121 | عامل | — |

### خدمات الملفات التعريفية المساعدة (7 — غير افتراضية)

| # | الخدمة | المنفذ | الملف التعريفي |
|---|--------|--------|:-------------:|
| 15 | kafdrop | 9100 | `dev` |
| 16 | redis-commander | 8083 | `dev` |
| 17 | backup | — | `backup` |
| 18 | minio | 9000 / 9001 | `objectstore` |
| 19 | loki (3.1.1) | 3100 | `observability` |
| 20 | otel-collector (0.111.0) | 4317 / 4318 / 8889 | `observability` |
| 21 | promtail (3.1.1) | — | `observability` |

### الأصول الرقمية (Docker Images — مثبتة)

| الصورة | الإصدار |
|--------|:------:|
| `redis` | `7.4-alpine` |
| `postgres` | `16-alpine` |
| `grafana/grafana` | `11.6.0` |
| `prom/prometheus` | `v3.3.0` |
| `prom/alertmanager` | `v0.28.0` |

---

## مستندات الإطار الهندسي (Engineering OS)

| المستند | الحالة | آخر تحديث |
|---------|:------:|-----------|
| `.engineering/03_REPOSITORY_MAP.md` | محدث | 2026-08-06 |
| `.engineering/04_DIRECTORY_CATALOG.md` | محدث | 2026-08-06 |
| `.engineering/05_FILE_CATALOG.md` | محدث | 2026-08-06 |
| `.engineering/13_DATABASE_CATALOG.md` | محدث | 2026-08-06 |
| `AGENTS.md` | محدث (ملخص الجلسة) | 2026-08-06 |
| `README.md` | محدث | 2026-08-06 |
| `RUNBOOK.md` | محدث | 2026-08-06 |
| `REPO_TOPOLOGY_AUDIT.md` | جديد | 2026-08-06 |
| `infrastructure/README.md` | جديد | 2026-08-06 |

---

## خارطة الطريق

```
✅ ADR-100 — Repository Canonicalization (10 مراحل)
     │
✅ ADR-101 — Green Bootstrap (6 إصلاحات، 14 خدمة سليمة)
     │
✅ Sprint 0.5 — Baseline Freeze (6 مستندات، 10/10 دخان)
     │
✅ ADR-102 — Engineering Hardening (21 إصلاح، 6 مجالات)
     │
✅ UX Architecture + Phase 1 (مسح 4 مجالات، 3 إصلاحات فورية)
     │
⬜ Phase 2 — Company 360 Enrichment (5 ألسنة، 6 إجراءات سريعة، رسم معرفي)
     │
⬜ Phase 3 — Employee 360 Polish (تحقق البيانات، إدخال التنقل، تدريب)
     │
⬜ Phase 4 — AI Workspace (تنشيط المساعد، تكامل منصة القرار)
     │
⬜ Phase 5 — Shell Unification (دمج المسارين، تثبيت التنقل)
     │
⬜ Security Hardening — P0 IDOR/SSRF/CSRF
     │
⬜ Feature Development — حسب خطة الإنتاج
```

---

## المشاكل المعلقة (من ADR-101/102)

| # | الأولوية | الوصف | الإجراء المجدول |
|---|:------:|-------|-----------------|
| K2 | منخفض | Kafka في وضع `in_memory` (وضع تطوير افتراضي) | مقبول للتطوير |
| K3 | منخفض | `images.domains` مهمل في Next.js 15 | الترحيل إلى `remotePatterns` |
| P0-1 | عاجل | IDOR عبر المستأجرين في مركز القرار | إضافة مرشح `tenant_id` |
| P0-2 | عاجل | SSRF في الخطافات (Webhooks) | إضافة قائمة عناوين مسموحة |
| P0-7 | عاجل | التوقعات ترمز `demo-1` بشكل ثابت | تجاهل مدخلات المستأجر الحقيقية |
| P1-8 | عالي | تجاوز CSRF مع `X-API-Key` غير فارغ | التحقق من صحة المفتاح |
| P1-9 | عالي | جذوع محرك القرار (Decision Engine stubs) | 6 توابع ترمي `Not implemented` |

---

## التوصيات

1. **معالجة P0 الأمنية فوراً:** IDOR عبر المستأجرين (`decision_center/postgres_repo.py`)، SSRF في الخطافات (`modules/webhooks/service.py`)، وتجاوز CSRF (`common/middleware.py`) تمثل أعلى مخاطر على المنصة ويجب إغلاقها قبل أي مرحلة UX لاحقة.

2. **المتابعة على Company 360 (Phase 2):** الصفحة مكتملة بنسبة 60% فقط — 5 ألسنة تعرض `EmptyState`، 6 أزرار إجراءات سريعة بدون معالجات `onClick`، والرسم البياني المعرفي يعرض "Coming Soon". توصيل هذه الألسنة بنقاط API النهائية هو الخطوة الأعلى قيمة للمستخدم.

3. **توحيد الهيكل (Shell Unification — Phase 5):** وجود هيكلين متوازيين `(dashboard)` و `v3` يمثل ديناً معمارياً متزايداً. كلما تأخر الدمج، زادت تكلفة المزامنة. يوصى ببدء التخطيط للدمج بالتوازي مع Phase 2.

4. **معالجة المشاكل المعلقة K2/K3:** Kafka بوضع `in_memory` و `images.domains` المهجور — مشاكل منخفضة الأولوية لكنها تتراكم. تخصيص وقت محدد في نهاية Phase 3 لإغلاقها.

5. **تشغيل اختبارات الوحدة الخلفية:** مجموعة الاختبارات (pytest) لم تُشغَّل في هذه الجلسة. تصنيف التدقيق (2026-07-22) يُظهر فشل اختبارات الوحدة (`mcp missing`, `admin/intelligence failures`). يوصى بتشغيل `pytest` في أقرب وقت لتحديد الفجوات المتبقية.

---

*آخر تحديث: 2026-08-06 | التصنيف: `light validated` | نطاق المراجعة: 4 التزامات (942907b → a31fd25)*
