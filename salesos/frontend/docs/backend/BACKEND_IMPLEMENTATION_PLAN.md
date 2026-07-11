# SalesOS Backend Implementation Plan

> خطة بناء الباك إند الكاملة — جميع النقاط المطلوبة حسب الأولوية

---

## الأولوية الأولى: البنية التحتية الأساسية

### 1.1 قاعدة البيانات

| المكون | التقنية | الحالة |
|--------|---------|--------|
| PostgreSQL | Companies, People, Opportunities, Tasks | 🆕 |
| pgvector | Embeddings للبحث الدلالي | 🆕 |
| Neo4j | Knowledge Graph (علاقات الشركات) | 🆕 |
| Redis | Cache + Session + Search History | 🆕 |

### 1.2 Authentication & Authorization

| المهمة | التفاصيل |
|--------|---------|
| JWT Authentication | تسجيل دخول + Refresh Tokens |
| Multi-tenant | كل Tenant له بياناته المنفصلة (`X-Tenant-Id` header) |
| RBAC | أدوار: Admin, Sales, Marketing, Executive, Legal |
| Permission check | لكل endpoing: `has_permission(user_id, resource, action)` |
| Rate Limiting | لكل مستخدم, لكل IP, لكل endpoint |
| API Keys | للتكاملات الخارجية (Wave 4) |

### 1.3 البنية التحتية للـ API

| المهمة | التفاصيل |
|--------|---------|
| Express.js / FastAPI | اختيار الإطار المناسب |
| Middleware | Auth → Tenant → Rate Limit → Logging |
| Error handling | موحد لكل endpoints |
| Validation | Zod / Pydantic لكل request |
| Request logging | لكل request مع timing |
| Health check | `GET /api/v1/health` |

---

## الأولوية الثانية: API Endpoints

### 2.1 Dashboard API

| # | Endpoint | Method | الوصف |
|---|----------|--------|-------|
| 1 | `/api/v1/dashboard` | GET | البيانات المجمعة للـ Dashboard (6 ويدجت) |
| 2 | `/api/v1/dashboard/mission-center` | GET | Mission Center فقط |
| 3 | `/api/v1/dashboard/decision-queue` | GET | Decision Queue فقط |

**متطلبات**: تجميع بيانات من 6 مصادر مختلفة في استجابة واحدة. استخدام PostgreSQL Aggregations.

### 2.2 Company Intelligence API

| # | Endpoint | Method | الوصف |
|---|----------|--------|-------|
| 4 | `/api/v1/companies` | GET | قائمة الشركات مع Pagination, Filter, Sort |
| 5 | `/api/v1/companies/{id}` | GET | تفاصيل شركة واحدة |
| 6 | `/api/v1/companies/{id}/intelligence` | GET | **الـ endpoint الأهم** — كل ذكاء الشركة (10 ويدجت) |
| 7 | `/api/v1/companies/{id}/timeline` | GET | الجدول الزمني للشركة |
| 8 | `/api/v1/companies/{id}/signals` | GET | إشارات الشركة |
| 9 | `/api/v1/companies/{id}/relationships` | GET | علاقات الشركة (من Neo4j) |
| 10 | `/api/v1/companies/{id}/documents` | GET | مستندات الشركة |
| 11 | `/api/v1/companies/{id}/government` | GET | السجلات الحكومية |
| 12 | `/api/v1/companies/compare` | POST | مقارنة شركتين أو أكثر |

**نموذج البيانات — Company**

```sql
CREATE TABLE companies (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  name_ar VARCHAR(500),
  name_en VARCHAR(500),
  cr_number VARCHAR(20) UNIQUE,
  city VARCHAR(100),
  region VARCHAR(100),
  status VARCHAR(50),
  industry VARCHAR(100),
  employees INTEGER,
  founded_year INTEGER,
  business_model VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Full text search index
CREATE INDEX idx_companies_fts ON companies 
  USING GIN(to_tsvector('arabic', coalesce(name_ar,'') || ' ' || coalesce(name_en,'')));
```

**نموذج البيانات — Intelligence**

```sql
CREATE TABLE company_intelligence (
  company_id UUID PRIMARY KEY REFERENCES companies(id),
  dna JSONB,                    -- Company DNA (جميع الأبعاد)
  ai_recommendation JSONB,      -- توصية AI الحالية
  buying_journey JSONB,         -- رحلة الشراء
  golden_record JSONB,          -- السجل الذهبي
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes'
);
```

### 2.3 Opportunity / Pipeline API

| # | Endpoint | Method | الوصف |
|---|----------|--------|-------|
| 13 | `/api/v1/opportunities` | GET, POST | قائمة الفرص + إنشاء فرصة |
| 14 | `/api/v1/opportunities/{id}` | GET, PUT, DELETE | تفاصيل فرصة + تحديث + حذف |
| 15 | `/api/v1/opportunities/{id}/stage` | PUT | تغيير مرحلة الفرصة |
| 16 | `/api/v1/opportunities/{id}/notes` | POST | إضافة ملاحظة |
| 17 | `/api/v1/pipeline` | GET | Pipeline Intelligence (مجمعة) |
| 18 | `/api/v1/pipeline/stalled` | GET | الصفقات المتوقفة |

**نموذج البيانات — Opportunity**

```sql
CREATE TABLE opportunities (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  company_id UUID REFERENCES companies(id),
  title VARCHAR(500) NOT NULL,
  stage VARCHAR(20) NOT NULL DEFAULT 'identified',
  estimated_value DECIMAL(15,2),
  confidence DECIMAL(3,2),
  win_probability DECIMAL(3,2),
  source VARCHAR(20) DEFAULT 'manual',
  source_action_id VARCHAR(100),
  buying_intent DECIMAL(3,2),
  relationship_strength DECIMAL(3,2),
  risk_level VARCHAR(10),
  assignee_id UUID,
  expected_close_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  stage_changed_at TIMESTAMPTZ,
  last_activity_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE opportunity_notes (
  id UUID PRIMARY KEY,
  opportunity_id UUID REFERENCES opportunities(id),
  text TEXT NOT NULL,
  author_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.4 Tasks API

| # | Endpoint | Method | الوصف |
|---|----------|--------|-------|
| 19 | `/api/v1/tasks` | GET, POST | قائمة المهام + إنشاء |
| 20 | `/api/v1/tasks/{id}` | PUT, DELETE | تحديث + حذف |
| 21 | `/api/v1/tasks/{id}/complete` | PUT | إكمال مهمة |

### 2.5 Meetings API

| # | Endpoint | Method | الوصف |
|---|----------|--------|-------|
| 22 | `/api/v1/meetings` | GET, POST | قائمة الاجتماعات |
| 23 | `/api/v1/meetings/{id}/brief` | GET | إيجاز الاجتماع (Meeting Intelligence) |

### 2.6 Emails API

| # | Endpoint | Method | الوصف |
|---|----------|--------|-------|
| 24 | `/api/v1/emails` | GET | قائمة الإيميلات (مع AI Summaries) |
| 25 | `/api/v1/emails/{id}/summary` | GET | تلخيص إيميل بالذكاء الاصطناعي |
| 26 | `/api/v1/emails/{id}/reply` | POST | اقتراح رد |

---

## الأولوية الثالثة: Search Backend (Hybrid Search)

### 3.1 Full Text Search

| المهمة | التفاصيل |
|--------|---------|
| PostgreSQL FTS | `to_tsvector('arabic', ...)` عبر جميع الجداول |
| pgroonga (optional) | محسن للبحث العربي (أسرع + أفضل) |
| Search across entities | Companies, People, Signals, Documents, Opportunities |
| Ranking | TF-IDF + recency + authority |

### 3.2 Semantic Search (pgvector)

| المهمة | التفاصيل |
|--------|---------|
| Embedding model | `intfloat/multilingual-e5-large` (يدعم العربية) |
| Embedding generation | توليد embeddings عند إنشاء/تحديث كل كيان |
| Vector search | `CREATE INDEX ON companies USING ivfflat (embedding vector_cosine_ops)` |
| Hybrid ranking | `score = 0.5 * fts_score + 0.5 * vector_score` |

### 3.3 Knowledge Graph Search (Neo4j)

| المهمة | التفاصيل |
|--------|---------|
| Neo4j connection | `apoc` لتحسين الاستعلامات |
| Graph traversal | "companies similar to X", "suppliers of Y" |
| Cypher queries | استعلامات مسار بين الكيانات |

### 3.4 AI Search (LLM)

| المهمة | التفاصيل |
|--------|---------|
| LLM integration | OpenAI / Anthropic / Local LLM (Llama) |
| RAG pipeline | Retrieve → Augment → Generate |
| Query interpretation | تحويل اللغة الطبيعية إلى استعلام هجين |
| AI Answer | تلخيص + تفسير + توصيات |

---

## الأولوية الرابعة: Data Ingestion & Pipelines

### 4.1 المصادر

| المصدر | البيانات | التحديث |
|--------|---------|--------|
| **وزارة التجارة** (API) | CR numbers, company status | يومي |
| **بلدية** (API) | Municipality licenses, expiry | يومي |
| **ZATCA / هيئة الزكاة** | Tax records, compliance | أسبوعي |
| **MISA** | Foreign investment licenses | أسبوعي |
| **منصة اعتماد** | Tenders, government contracts | يومي |
| **LinkedIn** (Scraping) | Hiring signals, employee count | أسبوعي |
| **News APIs** | Company news, signals | مستمر |
| **Social Media** | Sentiment analysis | مستمر |

### 4.2 ETL Pipelines

| المهمة | التفاصيل |
|--------|---------|
| CRON scheduler | جدولة استيراد كل مصدر |
| Data normalization | توحيد التنسيقات |
| Entity matching | مطابقة الكيانات عبر المصادر |
| Deduplication | إزالة التكرارات |
| Golden Record merge | دمج السجلات الذهبية |

### 4.3 Signals Engine

| المهمة | التفاصيل |
|--------|---------|
| Signal detection | استخراج الإشارات من البيانات الأولية |
| Signal classification | نوع الإشارة (توظيف، توسع، شراكة، ...) |
| Severity scoring | `severity = f(recency, source_reliability, entity_importance)` |
| AI confidence | LLM يقيم دقة الإشارة |

---

## الأولوية الخامسة: AI/ML Pipeline

### 5.1 Next Best Action Engine

| المهمة | التفاصيل |
|--------|---------|
| NBA scoring | `0.35*buying_intent + 0.20*relationship + 0.15*signals + 0.15*ai + 0.10*decision_makers + 0.05*revenue` |
| LLM reasoning | توليد تفسير طبيعي للإجراء |
| Trigger detection | تحديد الحدث الذي حفز الـ NBA |
| A/B testing | مقارنة أداء الـ NBA مع فرق المبيعات |

### 5.2 AI Recommendation Engine

| المهمة | التفاصيل |
|--------|---------|
| Action generation | LLM يولد الإجراء الموصى به |
| Revenue prediction | توقع الإيرادات بناءً على بيانات مشابهة |
| Risk assessment | تحديد المخاطر من البيانات التاريخية |
| Confidence calibration | معايرة الثقة بناءً على النتائج الفعلية |

### 5.3 Forecast Intelligence

| المهمة | التفاصيل |
|--------|---------|
| Time series forecasting | ARIMA / Prophet / LSTM |
| Pipeline weighting | `weighted_value = sum(deal_value * stage_probability)` |
| Risk modeling | تحديد مخاطر عدم تحقيق الهدف |
| What-if analysis | سيناريوهات مختلفة |

### 5.4 Churn Detection

| المهمة | التفاصيل |
|--------|---------|
| Churn scoring | `churn_score = f(engagement_decline, contract_expiry, support_tickets)` |
| Early warning | تنبيه قبل 30 يوم من التوقف المحتمل |
| Save recommendations | إجراءات مقترحة لمنع التوقف |

---

## الأولوية السادسة: Background Jobs

| الـ Job | التكرار | الوصف |
|---------|--------|-------|
| `refresh-intelligence` | 5 min | تحديث ذكاء الشركات (كل شركة) |
| `import-government-data` | 1 hour | استيراد البيانات الحكومية |
| `generate-signals` | 15 min | اكتشاف الإشارات الجديدة |
| `run-nba-engine` | 10 min | إعادة حساب NBA لكل شركة |
| `refresh-forecast` | 1 hour | تحديث التوقعات |
| `clean-expired-cache` | 1 hour | حذف الكاش المنتهي |
| `sync-neo4j-graph` | 5 min | مزامنة Neo4j مع PostgreSQL |
| `generate-embeddings` | 1 hour | توليد embeddings جديدة |

---

## الأولوية السابعة: Infrastructure

### 7.1 التكامل مع البنية الحالية

| المكون | التقنية |
|--------|---------|
| Docker | حاوية API + Postgres + Neo4j + Redis |
| Docker Compose | تشغيل كل الخدمات بأمر واحد |
| Health Checks | لكل خدمة |
| Logging | structured JSON logs |
| Metrics | Prometheus + Grafana ready |

### 7.2 Caching Strategy

| المستوى | التقنية | TTL |
|---------|--------|-----|
| Application | In-memory LRU | 10s |
| Redis | Company intelligence, search results | 30s–5min |
| CDN | Static assets | 1h |
| Database | Materialized views | 5min |

### 7.3 Performance Budgets

| Endpoint | Target (p95) |
|----------|-------------|
| GET /api/v1/dashboard | <200ms |
| GET /api/v1/companies/{id}/intelligence | <500ms |
| POST /api/v1/search | <800ms |
| POST /api/v1/search/ai | <3s |
| GET /api/v1/pipeline | <200ms |
| POST /api/v1/opportunities | <100ms |

---

## ملخص الأولويات للفريق الخلفي

```
الأسبوع 1-2:
  □ PostgreSQL schema (companies, opportunities, tasks, signals, documents)
  □ Authentication + Authorization + Multi-tenant
  □ Dashboard API endpoint

الأسبوع 3-4:
  □ Company Intelligence API (الـ 10 ويدجت)
  □ Opportunities CRUD API
  □ Tasks CRUD API

الأسبوع 5-6:
  □ Full Text Search + pgvector semantic search
  □ Search API endpoint (hybrid)
  □ Neo4j Graph integration

الأسبوع 7-8:
  □ Government data connectors
  □ Signals engine
  □ ETL pipelines

الأسبوع 9-10:
  □ AI/ML pipeline (NBA, Recommendations, Forecast)
  □ Churn detection
  □ Email + Meeting intelligence

الأسبوع 11-12:
  □ Background jobs
  □ Caching optimization
  □ Performance tuning
  □ Monitoring & logging
```
