# SalesOS (Muhide) — خطة البناء الكاملة V5

> **مراجعة شاملة + تحليل فجوات + خطة بناء مرحلية للوصول للمنتج النهائي**
> تاريخ الإعداد: 2026-07-04 | الإصدار: V5.0

---

## المحتويات
1. [ملخص تنفيذي](#1-ملخص-تنفيذي)
2. [تحليل الوضع الحالي](#2-تحليل-الوضع-الحالي)
3. [المنتج النهائي: ما نبني](#3-المنتج-النهائي-ما-نبني)
4. [خريطة الفجوات (Gap Analysis)](#4-خريطة-الفجوات-gap-analysis)
5. [خطة البناء التفصيلية](#5-خطة-البناء-التفصيلية)
6. [الجدول الزمني والموارد](#6-الجدول-الزمني-والموارد)
7. [المخاطر والتوصيات](#7-المخاطر-والتوصيات)
8. [مؤشرات النجاح](#8-مؤشرات-النجاح)

---

## 1. ملخص تنفيذي

### ما هو SalesOS؟
**نظام تشغيل ذكاء الأعمال المؤسسي (Enterprise BIOS)** — ليس CRM. منصة متكاملة تجمع:
- **البيانات**: سجلات حكومية سعودية موحدة (50K-100K سجل)
- **الذكاء**: ملفات شركات شاملة، تسجيل، تحليلات بصمة ذكاء اصطناعي
- **الأتمتة**: سير عمل، وكلاء ذكاء اصطناعي، أتمتة تسلسلية
- **السوق**: إضافات، حزم معرفية، سوق إشارات

### الوضع الحالي
- **الإنجاز الكلي**: ~12% من نطاق V5
- **التوثيق**: ممتاز (14+ وثيقة معماریة شاملة)
- **Backend SDK**: ~90% مكتمل بجودة إنتاجية
- **Frontend**: ~1% (شبه معدوم)
- **البيانات**: ~5% (السكرابرز تعمل لكن بدون خط أنابيب)
- **AI / ذكاء اصطناعي**: 0% (لا شيء)
- **الاختبارات**: ~20% لكن كلها In-Memory
- **Git**: لم يتم عمل أي Commit

### الفجوة الحرجة
```
ما هو مطلوب: منصة متكاملة بذكاء اصطناعي ← ما هو موجود: SDK + توثيق + سكرابرز
```

---

## 2. تحليل الوضع الحالي

### 2.1 نقاط القوة

| المجال | التفاصيل |
|--------|----------|
| **التوثيق المعماري** | 14+ وثيقة شاملة (Manifest, Blueprint, Status, Backlog, Quality Gate, AI Catalog, Event Catalog, Capability Catalog, Data Contracts, Domain Map, etc.) |
| **SDK** | 25+ وحدة جاهزة (Events, Audit, Cache, Permissions, Security, Queue, Search, Graph, Telemetry, Metadata, Vector) |
| **النمط المعماري** | Modular Monolith + DDD + Event-Driven + CQRS + Repository Pattern — مستوى عالمي |
| **السكرابرز** | 6 مصادر حكومية (بلدى، تقييم، نجز، ريجا، NCNP...) — 50K-100K سجل |
| **اختبارات الوحدات** | ~100 اختبار تغطي 12 كابabilité |
| **هيكلة الفريق** | تصميم معماري متقدم يسمح بالتوسع مستقبلًا |
| **خطط المنتج** | خريطة طريق 5 سنوات، Product Backlog، Capability Catalog |

### 2.2 نقاط الضعف

| المجال | التفاصيل | الخطورة |
|--------|----------|---------|
| **لا تخزين دائم** | كل الـ Repositories In-Memory | 🔴 حرجة |
| **لا واجهة مستخدم** | الـ Frontend شبه معدوم | 🔴 حرجة |
| **لا ذكاء اصطناعي** | AI Copilot, Scoring, Revenue Brain = 0 | 🔴 حرجة |
| **لا Entity Resolution** | تكرار البيانات غير مكتشف | 🔴 حرجة |
| **لا Data Pipeline** | السكرابرز منفصلة عن المنصة | 🟡 عالية |
| **لا CI/CD فعال** | GitHub Actions موجود لكن غير نشط | 🟡 عالية |
| **لا Integration Tests** | كل الاختبارات In-Memory | 🟡 عالية |
| **لا Kafka حقيقي** | EventBus In-Process — الأحداث تضيع عند إعادة التشغيل | 🟡 متوسطة |
| **لا Git History** | لم يتم عمل أول Commit | 🟡 متوسطة |

### 2.3 تحليل الكود الموجود

#### Backend (`salesos/backend/`)
```
app/
├── main.py                    # FastAPI entry point
├── config.py, database.py     # إعدادات جيدة
├── modules/                   # 11 Module 
│   ├── identity/              # ~90% - 12 endpoints, Auth, JWT
│   ├── company/               # ~90% - Organization, Contact, License
│   ├── search/                # ~95% - QueryParser, Planner, Ranking
│   ├── contact/               # Module structure
│   ├── entity_resolution/     # Skeleton only
│   ├── employee_360/          # Skeleton only
│   ├── executive/             # Skeleton only
│   ├── work_intelligence/     # Partial
│   ├── excel_import/          # Partial
│   ├── notion_sync/           # Partial
│   └── tenant/                # Basic
├── domains/                   # 7 bounded contexts
│   ├── commercial/            # pipeline, quote, proposal, contract, opportunity, activity
│   ├── revenue/               # forecast, analytics
│   ├── decision/              # recommendation, context
│   └── search/                # models, parser, planner, ranking
├── runtime/                   # 28 engines (mostly skeletons)
├── sdk/                       # ✅ Production quality
└── intelligence/              # 13 modules (all skeletons)
```

#### Frontend (`salesos/frontend/`)
```
src/
├── app/
│   ├── page.tsx, layout.tsx   # Basic layout
│   ├── (auth)/login, register  # Pages exist
│   └── companies/             # Basic list + detail
├── components/
│   ├── copilot-panel.tsx       # Stub
│   ├── search-panel.tsx        # Stub
│   ├── company-workspace.tsx   # Stub
│   └── ...
└── lib/
    ├── api.ts                 # API client
    └── hooks/                 # React Query hooks
```

---

## 3. المنتج النهائي: ما نبني

### 3.1 الرؤية (Vision)

**SalesOS V5** هو نظام تشغيل ذكاء أعمال متكامل يقدم:

```
┌─────────────────────────────────────────────────────────┐
│                    LAYER 4: APPLICATIONS                   │
│  Company 360 │ Deal Room │ AI Copilot │ Revenue Dashboard  │
│  ICP Builder │ GTM Builder │ Rules Studio │ Prompt Studio  │
├─────────────────────────────────────────────────────────┤
│                 LAYER 3: BUSINESS CAPABILITIES              │
│  Company Intel │ Pipeline │ Forecast │ Analytics │ Scoring │
│  GTM │ Marketing │ Success │ Partner │ Talent │ Activity   │
├─────────────────────────────────────────────────────────┤
│                  LAYER 2: PLATFORM SERVICES                 │
│  Data Fabric │ Intelligence Fabric │ Workflow │ Events      │
│  Feature Store │ Semantic Cache │ Knowledge Graph           │
│  OS API: REST + GraphQL + MCP + Agent SDK                  │
├─────────────────────────────────────────────────────────┤
│                   LAYER 1: KERNEL (Frozen)                   │
│  Identity │ Company │ Search │ Timeline │ SDK │ Events     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 الميزات الأساسية للمنتج النهائي

| # | الميزة | الوصف |
|---|--------|-------|
| 1 | **Company 360** | ملف شركة موحد بكل البيانات + AI + Timeline |
| 2 | **Search AI** | بحث ذكي بالعربية والإنجليزية (Keyword + Semantic + Graph) |
| 3 | **AI Copilot** | مساعد ذكي يجيب على أسئلة عن الشركات والأسواق |
| 4 | **Entity Resolution** | كشف وتوحيد الشركات المكررة |
| 5 | **Pipeline Intelligence** | إدارة صفقات مع تحليلات و AI |
| 6 | **Forecast + Analytics** | توقعات المبيعات مع 16+ KPI |
| 7 | **Feature Store** | 10+ ميزة محسوبة (نمو، توظيف، تمويل، ICP...) |
| 8 | **Revenue Brain** | Next Best Action لكل مستخدم |
| 9 | **Digital Twin** | نسخة رقمية لكل مساحة عمل |
| 10 | **MCP Server** | SalesOS متاح لجميع وكلاء AI |
| 11 | **Deal Room** | مساحة عمل الصفقات مع AI coaching |
| 12 | **Scoring Engine** | ICP fit + Engagement + Intent scoring |
| 13 | **Knowledge Packs** | حزم معرفية صناعية (صحة، إنشاءات، مالية...) |
| 14 | **Signal Marketplace** | سوق للإشارات والإضافات |

### 3.3 المكدس التكنولوجي النهائي

| الطبقة | التقنية | الحالة النهائية |
|--------|---------|-----------------|
| Backend | FastAPI + Python 3.12 | ✅ |
| ORM | SQLAlchemy 2.0 async | ✅ |
| DB | PostgreSQL 16 + pgvector | ✅ |
| Graph | Neo4j 5.x | ✅ |
| Events | Kafka + CloudEvents 1.0 | ✅ |
| Cache | Redis 7 | ✅ |
| Frontend | Next.js 15 + React 19 | ✅ |
| UI | shadcn/ui + Radix + Tailwind 4 | ✅ |
| State | Zustand + TanStack Query | ✅ |
| AI | OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3) | ✅ |
| CI/CD | GitHub Actions | ✅ |
| Infra | Docker Compose → K8s | ✅ |

---

## 4. خريطة الفجوات (Gap Analysis)

### 4.1 مصفوفة الفجوات الكاملة

| الكابabilité | الحالي | المطلوب | الفجوة | الجهد |
|-------------|--------|---------|--------|-------|
| **CAP-001: Identity** | 90% backend, in-memory | PostgreSQL + UI | وسط | 2 أسبوع |
| **CAP-002: Company** | 90% backend, in-memory | PostgreSQL + UI | وسط | 2 أسبوع |
| **CAP-003: Search** | 95%, partial UI | Full UI + Semantic Cache | صغيرة | 1 أسبوع |
| **CAP-004: Timeline** | 90%, in-memory | PostgreSQL + UI Widget | وسط | 1.5 أسبوع |
| **CAP-005: Data Fabric** | 5% (scrapers only) | Full pipeline | **ضخمة** | 10-12 أسبوع |
| **CAP-006: Feature Store** | 0% | Schema + 10 features + computation | ضخمة | 6-8 أسبوع |
| **CAP-007: Knowledge Graph** | 5% (Neo4j empty) | Schema + population + queries | ضخمة | 4-6 أسبوع |
| **CAP-008: Revenue Graph** | 0% | Full graph schema | ضخمة | 4-6 أسبوع |
| **CAP-009: Workflow Engine** | 0% | Trigger → Condition → Action | ضخمة | 8-10 أسبوع |
| **CAP-010: Semantic Cache** | 0% | Embedding cache | كبيرة | 3-4 أسبوع |
| **CAP-011: Company Intel** | 30% partial | Full surface | كبيرة | 6-8 أسبوع |
| **CAP-012: Opportunity** | 85% in-memory | PostgreSQL + UI | وسط | 3-4 أسبوع |
| **CAP-013: Pipeline Intel** | 85% in-memory | PostgreSQL + UI | وسط | 3-4 أسبوع |
| **CAP-014: Forecast** | 85% in-memory | PostgreSQL + UI | وسط | 3-4 أسبوع |
| **CAP-015: Analytics** | 85% in-memory | PostgreSQL + UI | وسط | 3-4 أسبوع |
| **CAP-016: Recommendation** | 90% in-memory | PostgreSQL + UI | وسط | 3-4 أسبوع |
| **CAP-017→020** | 0% | Full capabilities | ضخمة | 12-16 أسبوع |
| **CAP-021: Revenue Brain** | 0% | Full brain | **ضخمة جدًا** | 12-16 أسبوع |
| **CAP-022: AI Copilot** | 0% | Full copilot | ضخمة | 8-12 أسبوع |
| **CAP-023: Scoring Engine** | 0% | ML scoring | كبيرة | 6-8 أسبوع |
| **CAP-024: Company DNA** | 0% | DNA profile | كبيرة | 6-8 أسبوع |
| **CAP-025: AI Memory** | 0% | Memory system | كبيرة | 4-6 أسبوع |
| **CAP-026: Agent Runtime** | 0% | Agent OS | ضخمة | 12-16 أسبوع |
| **CAP-027: Prompt Studio** | 0% | Prompt management | كبيرة | 6-8 أسبوع |
| **CAP-028: AI Governance** | 0% | Governance portal | كبيرة | 6-8 أسبوع |
| **CAP-029→030** | 0% | Playground + Experiments | كبيرة | 8-12 أسبوع |
| **CAP-031: Simulation** | 0% | Sim engine | ضخمة | 8-10 أسبوع |
| **CAP-032: Digital Twin** | 0% | Full digital twin | **ضخمة جدًا** | 16-20 أسبوع |
| **CAP-033: Entity Resolution** | 0% | Matching + golden record | كبيرة | 6-8 أسبوع |
| **CAP-034: Company 360** | 0% | Full page | كبيرة | 6-8 أسبوع |
| **CAP-035: Deal Room** | 0% | Full app | كبيرة | 8-10 أسبوع |
| **CAP-036: AI Copilot UI** | 0% | Chat interface | وسط | 3-4 أسبوع |
| **CAP-037: REST API** | 50% partial | All endpoints | وسط | 4-6 أسبوع |
| **CAP-038: GraphQL API** | 0% | Schema + resolvers | كبيرة | 6-8 أسبوع |
| **CAP-039: MCP Server** | 0% | MCP tools | كبيرة | 4-6 أسبوع |
| **CAP-040: Agent SDK** | 0% | Python SDK | كبيرة | 6-8 أسبوع |

### 4.2 الفجوات الحرجة (P0)

```
1. ❌ لا PostgreSQL persistence ←  المنصة لا تحفظ البيانات
2. ❌ لا Entity Resolution ←  البيانات مكررة بدون كشف
3. ❌ لا Frontend حقيقي ←  لا يوجد واجهة مستخدم
4. ❌ لا Data Pipeline ←  السكرابرز معزولة عن المنصة
5. ❌ لا Git History ←  لا يوجد تحكم بالنسخ

هذه الفجوات تمنع المنتج من العمل نهائيًا
```

---

## 5. خطة البناء التفصيلية

### 5.1 نظرة عامة

```
PHASE 0:  التأسیس (Foundation)     — 4 أسابيع
PHASE 1:  التخزين (Storage)        — 4 أسابيع  
PHASE 2:  الواجهة (Frontend MVP)   — 6 أسابيع
PHASE 3:  البيانات (Data Fabric)   — 8 أسابيع
PHASE 4:  الذكاء (Intelligence)    — 10 أسابيع
PHASE 5:  التكامل (Integration)    — 6 أسابيع
PHASE 6:  الإطلاق (Launch)         — 4 أسابيع
─────────────────────────────────────────
المجموع:                           ~42 أسبوع (10.5 شهور)
```

---

### PHASE 0: التأسیس (Foundation) — Weeks 1-4

**الهدف**: بناء أساس متين يمكن البناء عليه

| الأسبوع | المهمة | التفاصيل | المخرجات |
|---------|--------|----------|----------|
| W1 | **Git Init + CI/CD** | أول Commit، تفعيل GitHub Actions، Quality Gates | Repo with history, CI passes |
| W1 | **Alembic Migrations** | إنشاء baseline migration لكل الجداول | `alembic upgrade head` يعمل |
| W2 | **PostgreSQL: Identity** | تنفيذ PostgresIdentityRepository + اختبارات التكامل | Identity يخزن في PG |
| W2 | **PostgreSQL: Company** | تنفيذ PostgresCompanyRepository + اختبارات التكامل | Company يخزن في PG |
| W3 | **PostgreSQL: Domains** | Timeline, Opportunity, Pipeline, Forecast, Analytics, Recommendation | 6 domains في PG |
| W3 | **Integration Tests** | 50+ اختبار تكامل ضد PostgreSQL | اختبارات حقيقية |
| W4 | **Docker Compose كامل** | التأكد من كل الخدمات تعمل معًا | `docker compose up` كامل |
| W4 | **Feature Flags** | تفعيل نظام Feature Flags لكل الكابabilities | Flags جاهزة |

**مخرجات Phase 0:**
- ✅ Git History مع CI/CD
- ✅ PostgreSQL لجميع الكابabilities الأساسية
- ✅ 50+ Integration Tests
- ✅ Docker Compose يعمل بالكامل

---

### PHASE 1: واجهة المستخدم (Frontend MVP) — Weeks 5-10

**الهدف**: بناء أول واجهة مستخدم تفاعلية

| الأسبوع | المهمة | التفاصيل | المخرجات |
|---------|--------|----------|----------|
| W5 | **Design System** | shadcn/ui: Button, Input, Card, Table, Dialog, Sheet | 20+ component |
| W5 | **RTL Support** | Arabic layout, i18n setup | واجهة عربية كاملة |
| W6 | **Auth UI** | Login, Register, Forgot Password, Reset Password | 4 صفحات |
| W6 | **Dashboard Layout** | Sidebar, Header, User Menu, Tenant Switcher | Layout أساسي |
| W7 | **Search UI** | Search bar + results page + filters | بحث يعمل |
| W7 | **Company List** | جدول شركات + فرز + ترقيم + فلترة | قائمة شركات |
| W8 | **Company 360 v1** | Company profile page (basic info + contacts + licenses) | أول صفحة كاملة |
| W8 | **Company Timeline** | Timeline widget on Company 360 | Timeline مرئي |
| W9 | **Pipeline UI** | Kanban board + List view for opportunities | Pipeline Viewer |
| W9 | **Dashboard Page** | KPIs, charts, recent activity | لوحة معلومات |
| W10 | **Polish + Testing** | Responsive, loading, empty, error states | UX كامل |

**مخرجات Phase 1:**
- ✅ Design System عربي/إنجليزي
- ✅ تسجيل دخول + Dashbaord
- ✅ Company 360 (أول تطبيق كامل)
- ✅ Search + Pipeline + Timeline

---

### PHASE 2: خط أنابيب البيانات (Data Fabric) — Weeks 11-18

**الهدف**: ربط السكرابرز بالمنصة وبناء خط البيانات

| الأسبوع | المهمة | التفاصيل | المخرجات |
|---------|--------|----------|----------|
| W11 | **Pipeline Framework** | Extract → Normalize → Validate → Load | Pipeline engine |
| W11 | **Data Contracts** | Schema لكل مصدر حكومي | Contracts معتمدة |
| W12 | **Normalizers** | City normalization, CR format, Arabic/English standardization | Normalizer engine |
| W12 | **Entity Resolution v1** | Blocking + Matching + Classification (Splink) | ER pipeline |
| W13 | **Entity Resolution v2** | Golden Record store + merge + provenance | Golden records |
| W13 | **Balady Integration** | ربط scraper الـ Balady بالـ Pipeline | بيانات بلدى تتدفق |
| W14 | **Taqeem Integration** | ربط scraper الـ Taqeem | بيانات تقييم تتدفق |
| W14 | **NCNP Integration** | ربط scraper الـ NCNP | بيانات NCNP تتدفق |
| W15 | **Najiz + REGA Integration** | ربط باقي السكرابرز | 6 مصادر متصلة |
| W15 | **Knowledge Graph v1** | Schema: Company → Contact → License, population | Neo4j فيه بيانات |
| W16 | **City/Region Master** | توحيد 200+ variant لأسماء المدن | Reference table |
| W16 | **Data Quality Dashboard** | Coverage %, dedup rate, source freshness | QI dashboard |
| W17 | **Feature Store v1** | 10 features: Growth Rate, Hiring Velocity, ICP Score, ... | Feature registry |
| W17 | **Feature Computation** | Scheduled + event-driven | Features تُحسب |
| W18 | **Testing + Optimization** | Benchmark, performance tuning | Pipeline stable |

**مخرجات Phase 2:**
- ✅ 6 مصادر حكومية تتدفق إلى المنصة
- ✅ Entity Resolution يكتشف ويكتشف التكرارات
- ✅ 50K-100K سجل موحد في Golden Records
- ✅ Knowledge Graph فيه بيانات
- ✅ Feature Store مع 10 Features

---

### PHASE 3: الذكاء الاصطناعي (Intelligence) — Weeks 19-28

**الهدف**: بناء طبقة الذكاء الاصطناعي كاملة

| الأسبوع | المهمة | التفاصيل | المخرجات |
|---------|--------|----------|----------|
| W19 | **RAG Pipeline** | Semantic Cache → SearchPlanner → Retrieve → RRF → Rerank → LLM | Search AI |
| W19 | **Semantic Cache v1** | Embedding cache with pgvector | 40-70% LLM cost saving |
| W20 | **Arabic NLP** | Arabic tokenizer, stop words, thesaurus | بحث عربي دقيق |
| W20 | **Company Intelligence v1** | Company profile enrichment + insights | Company Intel API |
| W21 | **AI Copilot v1** | "Ask about any company" — natural language → answer | AI Chat API |
| W21 | **Compare Companies** | AI side-by-side comparison | Compare feature |
| W22 | **Scoring Engine v1** | ICP Fit + Engagement + Intent + Revenue scores | Scoring API |
| W22 | **Company DNA** | Multi-dimensional profile: Size, Digital, Culture, Buying | DNA profile |
| W23 | **Revenue Brain Design** | Architecture, data flow, NBA algorithm | Design doc |
| W23 | **Revenue Brain v1** | State Manager → NBA computation | First NBA |
| W24 | **Recommendation Engine v2** | Enhanced with Revenue Brain input | Smart recommendations |
| W24 | **AI Memory** | Company memory with importance decay | Memory system |
| W25 | **Prompt Studio v1** | Versioning, testing, eval | Prompt management |
| W25 | **AI Governance v1** | Cost tracking, latency, accuracy | Governance dashboard |
| W26 | **Workflow Engine v1** | Trigger → Condition → Action (basic) | First workflows |
| W26 | **Business Rules v1** | Simple no-code rules | Rules builder |
| W27 | **Simulation Engine v1** | "What if" for email campaigns | Simulation API |
| W27 | **Digital Twin v1** | State Manager + basic predictions | Twin engine |
| W28 | **AI Playground v1** | Experiment: Prompt × Model × Temperature | Playground UI |

**مخرجات Phase 3:**
- ✅ AI Copilot (Search → Summarize → Compare → Recommend)
- ✅ Scoring Engine (ICP, Engagement, Intent, Revenue)
- ✅ Revenue Brain مع Next Best Action
- ✅ Semantic Cache (توفير 40-70% من تكاليف LLM)
- ✅ Prompt Studio + AI Governance
- ✅ Workflow Engine + Business Rules v1
- ✅ Digital Twin v1

---

### PHASE 4: التكامل والتوسع (Integration & Expansion) — Weeks 29-34

**الهدف**: ربط كل القطع وتوسيع المنصة

| الأسبوع | المهمة | التفاصيل | المخرجات |
|---------|--------|----------|----------|
| W29 | **MCP Server v1** | Company search + profile tools | AI Agent integration |
| W29 | **GraphQL API v1** | Schema + resolvers for core capabilities | GraphQL endpoint |
| W30 | **Deal Room** | Pipeline + AI coaching + timeline | Full deal workspace |
| W30 | **Revenue Dashboard** | KPIs + Forecasts + Trends + AI insights | Executive dashboard |
| W31 | **Customer Health v1** | Health scores for companies + deals | Health engine |
| W31 | **Email Studio v1** | Multi-channel sequence builder | Sequences |
| W32 | **Agent Runtime v1** | Planner → Memory → Executor → Tools | AI agents |
| W32 | **Agent SDK v1** | Python SDK for agent developers | SDK |
| W33 | **Knowledge Packs framework** | Pack structure: Ontology + Signals + Scoring + Prompts | Pack system |
| W33 | **Healthcare Pack v1** | First industry pack | أول حزمة معرفية |
| W34 | **Signal Marketplace v1** | Browse + purchase + install signals | Marketplace UI |

**مخرجات Phase 4:**
- ✅ MCP Server + GraphQL API
- ✅ Deal Room كامل
- ✅ Agent Runtime مع SDK
- ✅ Knowledge Packs (Healthcare)
- ✅ Signal Marketplace

---

### PHASE 5: الإطلاق والتشغيل (Launch & Operations) — Weeks 35-42

**الهدف**: تجهيز المنتج للإطلاق التجاري

| الأسبوع | المهمة | التفاصيل | المخرجات |
|---------|--------|----------|----------|
| W35 | **Security Audit** | Penetration testing, compliance check | Security report |
| W35 | **Performance Testing** | Load test, stress test, benchmark | Performance report |
| W36 | **Staging Environment** | Full staging with CI/CD auto-deploy | Staging live |
| W36 | **Production Environment** | K8s + Terraform + monitoring | Production ready |
| W37 | **Documentation** | API docs, user guide, admin guide | Docs complete |
| W37 | **Onboarding** | Developer onboarding + training | Team ready |
| W38 | **Beta Program** | 5-10 enterprise customers | Beta feedback |
| W38 | **Bug Fixes** | Based on beta feedback | Stable |
| W39 | **GA Release v1.0** | Public launch | 🚀 |
| W39 | **Monitoring** | Sentry, Datadog, SLA dashboard | Observability |
| W40 | **Post-Launch Support** | Hotfixes, scaling | Support |
| W41 | **Retrospective** | Lessons learned, roadmap update | Retro doc |
| W42 | **V2 Planning** | Next phase based on feedback | V2 plan |

**مخرجات Phase 5:**
- ✅ Production environment live
- ✅ Beta customers
- ✅ GA Release v1.0 🚀
- ✅ Full observability

---

### 5.2 خريطة الإصدارات (Release Map)

```
v0.1  — PostgreSQL Persistence + Git Init       [Q3 2026 - W4]
v0.2  — Frontend MVP + Data Ingestion            [Q3 2026 - W10]  
v0.3  — Entity Resolution + Search UI            [Q3/Q4 2026 - W14]
v0.4  — Feature Store + Knowledge Graph          [Q4 2026 - W18]
v0.5  — AI Copilot + Semantic Cache              [Q4 2026/Q1 2027 - W22]
v0.6  — Revenue Brain + Scoring                  [Q1 2027 - W26]
v0.7  — Digital Twin + Workflow Engine           [Q1/Q2 2027 - W30]
v0.8  — MCP + GraphQL + Agents                   [Q2 2027 - W34]
v1.0  — GA Launch 🚀                             [Q3 2027 - W42]
```

---

## 6. الجدول الزمني والموارد

### 6.1 الجدول الزمني الكامل

```
Q3 2026 (Jul-Sep)
├── Phase 0: Foundation (W1-W4)
│   ├── Git + CI/CD
│   ├── PostgreSQL Persistence
│   └── Integration Tests
├── Phase 1 Part 1: Frontend MVP (W5-W10)
│   ├── Design System + RTL
│   ├── Auth + Dashboard
│   └── Company 360 v1
└── Release v0.1 + v0.2

Q4 2026 (Oct-Dec)
├── Phase 1 Part 2: More UI
│   ├── Search + Pipeline + Timeline
│   └── Company 360 complete
├── Phase 2: Data Fabric (W11-W18)
│   ├── Pipeline Framework + Normalizers
│   ├── Entity Resolution
│   ├── Scraper Integration
│   └── Feature Store v1
└── Release v0.3 + v0.4

Q1 2027 (Jan-Mar)
├── Phase 3 Part 1: AI (W19-W24)
│   ├── RAG + Semantic Cache
│   ├── AI Copilot + Scoring
│   ├── Revenue Brain + NBA
│   └── AI Memory
└── Release v0.5 + v0.6

Q2 2027 (Apr-Jun)
├── Phase 3 Part 2: More AI (W25-W28)
│   ├── Prompt Studio + Governance
│   ├── Workflow + Business Rules
│   ├── Simulation + Digital Twin
│   └── AI Playground
├── Phase 4: Integration (W29-W34)
│   ├── MCP + GraphQL + Agents
│   ├── Deal Room + Revenue Dashboard
│   ├── Knowledge Packs + Marketplace
│   └── Agent Runtime + SDK
└── Release v0.7 + v0.8

Q3 2027 (Jul-Sep)
├── Phase 5: Launch (W35-W42)
│   ├── Security + Performance
│   ├── Staging + Production
│   ├── Beta Program
│   └── GA Launch 🚀
└── Release v1.0
```

### 6.2 الموارد المطلوبة

| الدور | العدد | المدة | ملاحظات |
|-------|-------|-------|---------|
| **Backend Engineer (Senior)** | 1-2 | مستمر | Python, FastAPI, PostgreSQL, DDD |
| **Frontend Engineer** | 1-2 | مستمر | Next.js, React, TypeScript, shadcn/ui |
| **AI/ML Engineer** | 1 | W19-W34 | RAG, LLMs, Scoring, NLP |
| **DevOps** | 1 | W0-W42 | Docker, K8s, CI/CD, Monitoring |
| **Data Engineer** | 1 | W11-W18 | Pipelines, ETL, Entity Resolution |
| **UI/UX Designer** | 1 | W5-W20 | Design system, RTL, user research |
| **QA Engineer** | 1 | مستمر | Integration tests, E2E, performance |

### 6.3 التكاليف التقديرية (شهرية)

| البند | التكلفة الشهرية | ملاحظات |
|-------|----------------|---------|
| **الفريق** (5-7 أشخاص) | $50K-$80K | حسب الموقع |
| **البنية التحتية** (Dev/Staging/Prod) | $2K-$5K | PostgreSQL, Neo4j, Redis, K8s |
| **OpenAI API** | $1K-$3K | يزيد مع Phase 3 |
| **Neo4j License** | $500-$2K | Community مجاني |
| **Sentry + Monitoring** | $500-$1K | |
| **المجموع الشهري** | **$54K-$91K** | |
| **المجموع الكلي (10.5 أشهر)** | **$567K-$955K** | |

---

## 7. المخاطر والتوصيات

### 7.1 المخاطر الرئيسية

| الخطر | الاحتمال | التأثير | خطة التخفيف |
|-------|----------|---------|-------------|
| **الفريق صغير جدًا** | عالي | 🔴 حرج | تحديد أولويات صارمة (P0 فقط أولًا) |
| **AI Cost يخرج عن السيطرة** | متوسط | 🟡 عالي | Semantic Cache إلزامي، استخدام GPT-4o-mini |
| **Entity Resolution دقته منخفضة** | عالي | 🔴 حرج | البدء بـ 3 مصادر فقط، تقييم مستمر |
| **Neo4j صعب التشغيل** | متوسط | 🟡 عالي | البدء بـ PostgreSQL فقط، Neo4j في RT2 |
| **Frontend معقد جدًا** | عالي | 🔴 حرج | Company 360 أولًا، باقي التطبيقات لاحقًا |
| **جودة البيانات منخفضة** | عالي | 🟡 عالي | Normalizers قوية قبل Entity Resolution |
| **Kafka معقد للتشغيل** | متوسط | 🟡 متوسط | In-process EventBus يكفي أول 6-12 شهر |
| **توقف التطوير** | متوسط | 🟡 عالي | مطلوب موظف واحد على الأقل متفرغ |

### 7.2 التوصيات الإستراتيجية

```
1. 🥇 P0 أولًا — تجاهل كل ما ليس P0 حتى يكتمل
   PostgreSQL > Frontend > Entity Resolution > Data Pipeline > Git

2. 🥇 Frontend MVP محدود — Company 360 فقط
   لا تبني 14 تطبيق. طبق واحد كامل أفضل من 7 نصف مكتملة.

3. 🥇 AI يمكن تأجيله — لا AI حتى Phase 3 (W19+)
   بدون Data Fabric، الـ AI ليس لديه بيانات يعمل عليها.

4. 🥇 استخدم In-Memory EventBus أول 12 شهر
   Kafka يمكن إضافته لاحقًا بدون تغيير الكود.

5. 🥇 ابدأ بـ 3 سكرابرز فقط (بلدي، تقييم، NCNP)
   الباقي يمكن إضافته بعد الإطلاق.

6. 🥇 لا تنشر Production حتى Phase 5
   Staging يكفي لاختبار الـ MVP مع العملاء.

7. 🥇 Git Commit فورًا — حتى لو الكود غير كامل
   التحكم بالنسخ أهم من الكمال.
```

### 7.3 توصيات عاجلة (هذا الأسبوع)

| # | المهمة | السبب |
|---|--------|-------|
| 1 | **git init + git add + git commit** | لا يوجد تحكم بالنسخ |
| 2 | **إنشاء `.env` من `.env.example`** | بدون `POSTGRES_PASSWORD` و `JWT_SECRET_KEY` لا شيء يعمل |
| 3 | **تشغيل `docker compose up`** | التحقق أن النظام يعمل |
| 4 | **تشغيل `poetry run pytest`** | التحقق أن الاختبارات تمر |
| 5 | **تثبيت Pre-commit hooks** | `pre-commit install` |

---

## 8. مؤشرات النجاح (Success Metrics)

### 8.1 لكل Phase

| Phase | مؤشر النجاح | القياس |
|-------|-------------|--------|
| **P0: Foundation** | PostgreSQL يخزن ويسترجع البيانات | `pytest` يمر مع PostgreSQL |
| **P1: Frontend** | Company 360 صفحة تعرض بيانات حقيقية | Page load < 2s |
| **P2: Data Fabric** | 50K+ سجل موحد بدون تكرارات | Dedup rate > 90% |
| **P3: Intelligence** | AI Copilot يجيب على أسئلة الشركات | Accuracy > 85% |
| **P4: Integration** | MCP Server متاح لوكلاء AI | Tools callable |
| **P5: Launch** | GA Release v1.0 | 10+ enterprise customers |

### 8.2 KPIs المنتج النهائي

| المؤشر | الهدف |
|--------|-------|
| **عدد الشركات في المنصة** | 100K+ |
| **Entity Resolution Precision** | > 95% |
| **Search Latency p95** | < 500ms |
| **AI Query Latency** | < 3s (مع Semantic Cache) |
| **Semantic Cache Hit Rate** | > 40% |
| **Frontend Page Load** | < 2s |
| **Test Coverage** | > 85% |
| **Uptime** | > 99.9% |
| **Integration Test Count** | 200+ |
| **Feature Store Features** | 10+ |

---

## ملخص التوصيات النهائية

```
1. PK: بدء Git Commit اليوم — ليس الغد
2. أولوية قصوى: PostgreSQL Repositories — بدونها المنصة لا تحفظ البيانات
3. أولوية عالية: Frontend MVP — تطبيق Company 360 أولًا
4. لا تبدأ AI قبل Phase 3 — ليس لديك بيانات كافية بعد
5. اختصر النطاق: 3 سكرابرز → Entity Resolution → Company 360 → AI Copilot
6. الفريق: مطور Backend + Frontend = الحد الأدنى للإطلاق
7. الميزانية: $60K-$90K/شهر للفريق الكامل
8. الوقت: 10.5 أشهر للـ GA Release
```

---

*هذه الخطة مبنية على التحليل الكامل للمشروع بتاريخ 2026-07-04.*
*جميع الأولويات والتقديرات قابلة للتعديل حسب الموارد المتاحة.*
*المرجع: PROJECT_MANIFEST.md, MASTER_BLUEPRINT.md, PROJECT_STATUS.md, PRODUCT_BACKLOG.md, CAPABILITY_CATALOG.md*
