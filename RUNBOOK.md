# SalesOS — Runbook

**كيف تشغل النظام كامل من الصفر**

---

## 1. المتطلبات

| الأداة | أقل إصدار |用途 |
|--------|-----------|------|
| Docker | 24+ | تشغيل الخدمات (PostgreSQL, Neo4j, Redis, Kafka...) |
| Docker Compose | 2.24+ | إدارة الخدمات المتعددة |
| Python | 3.12 | تشغيل الـ Data Pipelines (اختياري) |
| Node.js | 20+ | تشغيل Frontend خارج Docker (اختياري) |
| Poetry | 1.8 | إدارة حزم Python (اختياري) |

---

## 2. الإعداد الأول (مرة واحدة)

### 2.1 استنساخ المستودع

```bash
git clone <repo-url>
cd Muhide
```

### 2.2 إعداد متغيرات البيئة

```bash
cd salesos
cp .env.example .env
```

عدّل `.env` واملأ القيم المطلوبة:

```
POSTGRES_PASSWORD=                # مطلوب — لا قيمة افتراضية
JWT_SECRET_KEY=                   # مطلوب — لا قيمة افتراضية
OPENAI_API_KEY=                   # مطلوب لتشغيل AI Copilot
NOTION_TOKEN=                     # مطلوب لـ Data Pipeline
```

لتوليد `JWT_SECRET_KEY`:

```bash
openssl rand -hex 32
```

---

## 3. تشغيل النظام الأساسي (Docker)

### 3.1 تشغيل كل الخدمات

```bash
cd salesos
docker compose up --build
```

هذا يشغل:

| الخدمة | المنفذ |用途 |
|--------|--------|------|
| **PostgreSQL** (pgvector) | 5432 | قاعدة البيانات الرئيسية |
| **PgBouncer** | 6432 | Connection Pooling |
| **Neo4j** | 7474, 7687 | Knowledge Graph |
| **Redis** | 6379 | Cache + Rate Limiting |
| **ZooKeeper** | 2181 | Kafka coordination |
| **Kafka** | 9092 | Event Bus |
| **Backend** (FastAPI) | 8000 | API |
| **Frontend** (Next.js) | 3000 | Web App |

### 3.2 تشغيل الترحيلات (Migrations)

في terminal ثاني:

```bash
cd salesos
docker compose exec backend alembic upgrade head
```

### 3.3 التحقق

```bash
# Health check
curl http://localhost:8000/health
# → {"status":"ok","version":"0.1.0","database":"connected","cache":"connected"}

# API docs
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

---

## 4. تشغيل الخدمات بشكل منفصل (Development)

### 4.1 تشغيل الخدمات المساعدة فقط

```bash
cd salesos

# بدون Backend + Frontend
docker compose up postgres neo4j redis zookeeper kafka pgbouncer -d
```

### 4.2 Backend خارج Docker

```bash
cd salesos/backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.3 Frontend خارج Docker

```bash
cd salesos/frontend
npm install
npm run dev
```

---

## 5. إدارة الخدمات

### 5.1 إيقاف

```bash
cd salesos
docker compose down
```

### 5.2 إعادة تشغيل كامل (مسح البيانات)

```bash
cd salesos
docker compose down -v   # يحذف volumes (جميع البيانات)
docker compose up --build
```

### 5.3 عرض السجلات

```bash
cd salesos
docker compose logs -f          # كل الخدمات
docker compose logs -f backend  # Backend فقط
```

### 5.4 أوامر Make

```bash
make install    # تثبيت الاعتماديات
make dev        # تشغيل (docker compose up --build)
make test       # تشغيل الاختبارات
make lint       # فحص الكود
make migrate    # ترحيل قاعدة البيانات
make reset      # إعادة تشغيل كامل
make logs       # عرض السجلات
```

---

## 6. نقاط النهاية (Endpoints)

### 6.1 API

| المسار | الوصف |
|--------|-------|
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc |
| `http://localhost:8000/health` | Health Check |
| `POST /api/v1/identity/register` | تسجيل مستخدم |
| `POST /api/v1/identity/login` | تسجيل دخول |
| `POST /api/v1/identity/refresh` | تجديد التوكن |
| `POST /api/v1/identity/forgot-password` | نسيت كلمة المرور |
| `POST /api/v1/identity/reset-password` | إعادة تعيين كلمة المرور |
| `GET /api/v1/companies` | البحث في الشركات |
| `POST /api/v1/copilot/query` | المساعد الذكي |

### 6.2 Frontend

| المسار | الوصف |
|--------|-------|
| `http://localhost:3000` | Landing Page |
| `http://localhost:3000/login` | تسجيل الدخول |
| `http://localhost:3000/register` | إنشاء حساب |
| `http://localhost:3000/dashboard` | لوحة المعلومات |
| `http://localhost:3000/companies` | الشركات |

### 6.3 الخدمات

| الخدمة | الرابط | المستخدم |
|--------|--------|----------|
| Neo4j Browser | `http://localhost:7474` | `neo4j` / `salesos_neo4j_dev` |

---

## 7. تشغيل Data Pipeline

### 7.1 تنشيط Python Environment

```bash
cd Muhide
python -m venv venv
pip install openpyxl httpx python-dotenv
```

### 7.2 تشغيل الـ CRM Enrichment

```bash
# 1. نظف وأغني بيانات CRM
python crm_enrichment.py

# 2. تحقق من جودة البيانات
python crm_pipeline.py

# 3. تصنيف وتحليل ذكي
python sales_intel_pipeline.py

# 4. تحقق من المواقع + LinkedIn
python website_li_pipeline.py
```

### 7.3 تشغيل Scraper (مثال: Balady)

```bash
# أولاً: عيّن التوكن
export NOTION_TOKEN=ntn_your_token_here

# شغّل السكرابر
cd balady_scraper
python main.py
```

### 7.4 تشغيل Notion Automation

```bash
cd sales-os
# تأكد من وجود .env
cp .env.example .env
# عدّل .env مع NOTION_TOKEN الصحيح

python main.py
# القائمة:
# 1. فحص التكرارات
# 2. تسجيل الاكتمال
# 3. تحديد الأولويات
# 4. كشف الراكد
# 5. متابعة التراخيص
# 6. تشغيل الكل
```

---

## 8. تشغيل الاختبارات

### 8.1 Backend

```bash
cd salesos/backend
poetry run pytest -v

# مع تغطية
poetry run pytest -v --cov=app --cov-report=term-missing
```

### 8.2 Frontend

```bash
cd salesos/frontend
npm test
```

### 8.3 Architecture Fitness Tests

```bash
cd salesos/backend
poetry run pytest tests/test_architecture.py -v
```

---

## 9. استكشاف الأخطاء

| المشكلة | السبب | الحل |
|---------|-------|------|
| `POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD` | البيئة ناقصة | أضف `POSTGRES_PASSWORD` إلى `.env` |
| `JWT_SECRET_KEY` not set | البيئة ناقصة | أضف `JWT_SECRET_KEY` إلى `.env` |
| Backend لا يتصل بقاعدة البيانات | PostgreSQL لم يكتمل Health Check | `docker compose logs postgres` |
| Copilot يعيد رسالة "لم يتم تكوين مفتاح OpenAI" | `OPENAI_API_KEY` فارغ | أضف المفتاح في `.env` |
| Frontend يعرض `—` في الإحصائيات | لا توجد بيانات | استورد شركات أولاً |
| Scraper يفشل بـ `NOTION_TOKEN` | التوكن ناقص | `export NOTION_TOKEN=...` |

---

## 10. النشر (Production)

### 10.1 Kubernetes

```bash
cd salesos/infra/k8s

# عدّل secrets.yaml
kubectl apply -f secrets.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
```

### 10.2 Terraform (AWS me-south-1)

```bash
cd salesos/infra/terraform
terraform init
terraform plan
terraform apply
```

---

## 11. هيكل المجلدات المهمة

```
Muhide/
├── salesos/                         # ★ المنصة الرئيسية
│   ├── docker-compose.yml           # تشغيل كل الخدمات
│   ├── .env.example                 # قالب المتغيرات
│   ├── Makefile                     # أوامر مختصرة
│   ├── backend/                     # FastAPI + DDD + Intelligence
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py              # نقطة الدخول
│   │       ├── modules/             # Identity, Company, Entity Resolution
│   │       ├── routers/             # Copilot, Commercial
│   │       └── alembic/versions/    # الترحيلات
│   ├── frontend/                    # Next.js 15
│   │   ├── Dockerfile
│   │   ├── src/app/                 # الصفحات
│   │   ├── src/components/          # CopilotPanel, SearchPanel
│   │   ├── src/lib/                 # API, Hooks, Queries
│   │   └── packages/                # @salesos/ui, runtime, hooks...
│   ├── intelligence/agents/         # AI Agents (Research, News...)
│   ├── runtime/                     # 24 Runtime engines
│   ├── pipeline/                    # Shared pipeline utilities
│   └── infra/                       # K8s, Terraform
│
├── balady_scraper/                  # حكومي — المكاتب الهندسية
├── najiz_scraper/                   # حكومي — المحامين
├── rega_scraper/                    # حكومي — العقارات
├── taqeem_scraper/                  # حكومي — التقييم
├── crm_enrichment.py                # تنقية CRM
├── crm_pipeline.py                  # استرجاع البيانات
├── sales_intel_pipeline.py          # تحليل ذكي
└── website_li_pipeline.py           # تحقق المواقع
```

---

> **أمر التشغيل السريع (للمطورين):**
> ```bash
> cd salesos
> cp .env.example .env
> # املأ POSTGRES_PASSWORD, JWT_SECRET_KEY
> docker compose up --build
> # افتح http://localhost:3000
> ```
