# comprehensive-odoo-discovery-prompt.md
# برومت شامل — اكتشاف وربط قاعدة بيانات مصادر مع Odoo Helpdesk

> **الغرض:** نسخ هذا البرومت في مشروع جديد để يستخدمه أي agent أو مطور لإعادة تنفيذ عملية الاكتشاف والربط الكاملة.
> **الحالة:** Read-Only Discovery & Mapping — لا ي Executes أي Write.

---

## 🎯 الهدف العام

لدي قاعدة بيانات مصدر (PostgreSQL) أريد لاحقاً نقل بياناتها إلى Odoo 17.0 Enterprise Helpdesk.
المرحلة الحالية هي **Discovery & Mapping فقط** — أي قراءة وتحليل وتوثيق، بدون أي تعديل.

---

## 📋 ما تم تنفيذه خطوة بخطوة

### المرحلة 1: استكشاف بنية المشروع

```
行动: استكشف المجلد الجذر للمشروع
الأداة: Glob + Read + Task (explore agent)
النتائج:
  - المجلد الرئيسي: C:\Users\raghe\Documents\Muhide
  - المشروع الأساسي: salesos/ (FastAPI backend + Next.js frontend)
  - ملفات البيئة: salesos/.env, salesos/backend/.env
  - Docker: salesos/docker-compose.yml (PostgreSQL على порت 5432)
  - كود Odoo: salesos/backend/runtime/odoo/__init__.py (OdooJsonRpcClient)
  - إعدادات Odoo: salesos/backend/app/config.py (ODOO_URL, ODOO_DATABASE, ODOO_USERNAME, ODOO_API_KEY)
```

**ملفات مهمة تم العثور عليها:**

| الملف | المحتوى |
|-------|---------|
| `salesos/.env` | DATABASE_URL, ODOO_* settings (فارغة حالياً) |
| `salesos/backend/runtime/odoo/__init__.py` | OdooJsonRpcClient — JSON-RPC 2.0 client |
| `salesos/backend/app/config.py` | إعدادات Odoo (سطور 286-290) |
| `salesos/backend/app/modules/integration_hub/odoo_adapter.py` | OdooAdapter — SourceConnector |
| `salesos/backend/app/alembic/versions/b0d0e0f0a0d0_odoo_external_ids.py` | جدول ربط IDs |

---

### المرحلة 2: فحص قاعدة البيانات المصدر

```
行动: الاتصال بـ PostgreSQL عبر Docker
الأداة: docker exec salesos-postgres-1 psql
البروتوكول: Read-Only فقط — SELECT فقط
```

**كيفية الاتصال:**

```bash
# عبر Docker exec (الطريقة المستخدمة)
docker exec salesos-postgres-1 psql -U salesos -d salesos -t -A -F "|" -c "SQL_QUERY"

# أو عبر Python (ملاحظة: يتطلب psycopg2 أو asyncpg على المضيف)
# DATABASE_URL: postgresql+asyncpg://salesos:salesos_dev_password@localhost:5432/salesos
```

**الاستعلامات الأساسية التي تم تنفيذها:**

```sql
-- 1. معلومات قاعدة البيانات
SELECT version();

-- 2. جميع الجداول مع عدد الصفوف
SELECT
    t.table_schema,
    t.table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))) as total_size,
    (SELECT reltuples::bigint FROM pg_class WHERE oid = (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass) as approx_rows
FROM information_schema.tables t
WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
AND t.table_type = 'BASE TABLE'
ORDER BY t.table_schema, t.table_name;

-- 3. جميع الأعمدة مع أنواعها
SELECT
    c.table_schema, c.table_name, c.column_name,
    c.data_type, c.character_maximum_length,
    c.is_nullable, c.column_default,
    CASE WHEN pk.column_name IS NOT NULL THEN 'YES' ELSE 'NO' END as is_primary_key
FROM information_schema.columns c
LEFT JOIN (
    SELECT ku.column_name, ku.table_name, ku.table_schema
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name
WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY c.table_schema, c.table_name, c.ordinal_position;

-- 4. العلاقات الخارجية (Foreign Keys)
SELECT
    tc.table_name as source_table, kcu.column_name as source_column,
    ccu.table_name as target_table, ccu.column_name as target_column,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = ku.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- 5. الفهارس
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename;

-- 6. البيانات╪ العينية (masking للبيانات الحساسة)
SELECT * FROM companies LIMIT 3;
SELECT * FROM contacts LIMIT 3;
SELECT * FROM users LIMIT 3;
```

**النتائج الرئيسية:**

| الجدول | عدد الصفوف | الصلة |
|--------|-----------|-------|
| tenants | 30 | معظمها test/probe |
| users | 18 | 17 اختبار + 1 admin |
| companies | 5 | بيانات حقيقيةmostly |
| contacts | 3 | |
| tasks | 0 | فارغ |
| commercial_opportunities | 1 | |
| activity_records | 120 | سجل أحداث |
| domain_events | 127 | |
| signal_catalog | 22 | محتوى منصة |
| odoo_external_ids | 0 | لم يحدث مزامنة |

---

### المرحلة 3: فحص اتصال Odoo

```
行动: الاتصال بـ Odoo عبر XML-RPC
الأداة: Python xmlrpc.client
البروتوكول: Read-Only فقط — لا أي Write
```

**تفاصيل الاتصال:**

```python
import xmlrpc.client
import ssl

ODOO_URL = "https://odoo-ps-psae-ratl.odoo.com"
ODOO_DB = "odoo-ps-psae-ratl-main-14005796"
ODOO_USER = "ragheed.a@muhide.com"
ODOO_KEY = "5974d5f2e79bd188c43484dd2c55af1184b53bab"

# إنشاء سياق SSL (مهم لـ odoo.com hosting)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# الاتصال
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', context=ctx)
models_rpc = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', context=ctx)

# المصادقة
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_KEY, {})
print(f"uid = {uid}")  # النتيجة: 43
```

**ملاحظات مهمة:**
- JSON-RPC (`/jsonrpc`) **لا يعمل** مع odoo.com hosting — يسبب TypeError
- يجب استخدام XML-RPC (`/xmlrpc/2/common` + `/xmlrpc/2/object`)
- `ir.model` **مرفوض** للمستخدم العادي — requires "Administration/Access Rights" group
- `res.company` **مرفوض** partial — field-level security restriction

**الاستعلامات المستخدمة لاكتشاف Odoo:**

```python
def search_read(model, domain, fields=None, limit=None):
    """بحث وقراءة سجلات من Odoo"""
    kw = {}
    if fields: kw["fields"] = fields
    if limit: kw["limit"] = limit
    return models_rpc.execute_kw(ODOO_DB, uid, ODOO_KEY, model, 'search_read', [domain], kw)

def count(model, domain):
    """عدّ سجلات"""
    return models_rpc.execute_kw(ODOO_DB, uid, ODOO_KEY, model, 'search_count', [domain], {})

def fields_get(model):
    """الحصول على metadata جميع الحقول"""
    return models_rpc.execute_kw(ODOO_DB, uid, ODOO_KEY, model, 'fields_get', [],
        {"attributes": ["string", "type", "required", "readonly", "help",
                        "relation", "selection", "size"]})
```

**استعلامات الاكتشاف:**

```python
# معلومات المستخدم المتصل
search_read("res.users", [["id", "=", uid]],
    ["id", "name", "email", "login", "company_id"])

# جميع فرق الHelpdesk
search_read("helpdesk.team", [])

# جميع مراحل Helpdesk
search_read("helpdesk.stage", [])

# جميع أنواع التذاكر
search_read("helpdesk.ticket.type", [])

# جميع الوسوم
search_read("helpdesk.tag", [])

# عدد التذاكر
count("helpdesk.ticket", [])

# تفاصيل فريق Muhide CX
search_read("helpdesk.team", [["id", "=", 1]])

# تذاكر فريق معين
search_read("helpdesk.ticket", [["team_id", "=", 1]], limit=10)

# جميع المستخدمين
search_read("res.users", [], ["id","name","email","login","active","company_id"])

# حقول مخصصة (x_studio_*)
fields_get("helpdesk.ticket")  # ثم فلترة x_ fields

# عدد المرفقات على التذاكر
count("ir.attachment", [["res_model", "=", "helpdesk.ticket"]])

# عدد الرسائل على التذاكر
count("mail.message", [["model", "=", "helpdesk.ticket"]])
```

---

### المرحلة 4: اكتشاف فريق Muhide CX تحديداً

```
行动: قراءة تفاصيل الفريق وتكوينه
```

**النتائج:**

```json
{
  "id": 1,
  "name": "Muhide CX Team",
  "active": true,
  "company_id": [1, "Ratl Technology Ltd"],
  "alias_email": "customer-team@support.muhide.com",
  "assign_method": "randomly",
  "member_ids": [2],
  "stage_ids": [1, 6, 4, 5, 3],
  "use_sla": true,
  "use_rating": true,
  "ticket_ids": [/* 359 IDs */],
  "open_ticket_count": 12,
  "unassigned_tickets": 3,
  "privacy_visibility": "portal",
  "resource_calendar_id": [1, "Standard 48 hours/week"]
}
```

**المراحل في الفريق:** New(1) → In Progress(6) → Solved(4) / Canceled(5) / On Hold(3)

---

### المرحلة 5: بناء خريطة البيانات (Data Mapping)

```
行动: مقارنة حقول المصدر مع حقول Odoo
```

**الخريطة الأساسية:**

| المصدر | نوع المصدر | Odoo Model | Odoo Field | نوع Odoo | الطريقة |
|--------|-----------|------------|------------|----------|---------|
| `companies.id` | uuid | `res.partner` | `x_studio_muhide_user_id` | many2one | حقل مخصص للربط |
| `companies.name_ar` | varchar | `res.partner` | `name` | char | مباشر |
| `companies.cr_number` | varchar | `res.partner` | `x_studio_cr_number` | char | حقل مخصص |
| `companies.city` | varchar | `res.partner` | `city` | char | مباشر |
| `companies.phone` | varchar | `res.partner` | `phone` | char | مباشر |
| `companies.email` | varchar | `res.partner` | `email` | char | مباشر |
| `companies.is_active` | boolean | `res.partner` | `active` | boolean | مباشر |
| `contacts.name` | varchar | `res.partner` | `name` | char | مباشر |
| `contacts.email` | varchar | `res.partner` | `email` | char | مباشر |
| `contacts.company_id` | uuid | `res.partner` | `parent_id` | many2one | بحث عبر company mapping |
| `tasks.title` | varchar | `helpdesk.ticket` | `name` | char | مباشر |
| `tasks.status` | varchar | `helpdesk.ticket` | `stage_id` | many2one | جدول تحويل |
| `tasks.priority` | varchar | `helpdesk.ticket` | `priority` | selection | تحويل: low→0, high→2, urgent→3 |
| `tasks.assignee_id` | uuid | `helpdesk.ticket` | `user_id` | many2one | بحث عبر email |
| `tasks.company_id` | uuid | `helpdesk.ticket` | `partner_id` | many2one | بحث عبر company mapping |

**جدول تحويل الحالات (Status → Stage):**

| حالة المصدر | مرحلة Odoo | Stage ID |
|-------------|-----------|----------|
| `new` / `pending` | New | 1 |
| `in_progress` / `open` | In Progress | 6 |
| `completed` / `done` | Solved | 4 |
| `cancelled` | Canceled | 5 |
| `on_hold` | On Hold | 3 |

---

### المرحلة 6: اكتشاف مشاكل البيانات

**مشاكل في Odoo:**

| المشكلة | الخطورة | العدد | التفاصيل |
|---------|---------|-------|----------|
| تكرار بريدpartners | عالية | 71+ مجموعة | مثلاً `ebtehal.m@ratlfintech.com`: 5 سجلات |
| نص عربي في حقول email | عالية | 50+ | "مصانع"، "مقاولين" — ليست بريدإلكتروني |
| تذاكر بدون عميل | متوسطة | 37 | 37 تذكرة بدون `partner_id` |
| تذاكر بدون مسؤول | متوسطة | 104 | 104 تذكرة `user_id` فارغ |

**مشاكل في المصدر:**

| المشكلة | الخطورة | العدد |
|---------|---------|-------|
| شركات بدون جهات اتصال | متوسطة | 3 من 5 |
| معظم المستخدمين اختبار | منخفضة | 17 من 18 |
| لا توجد تذاكر | N/A | 0 tasks |

---

### المرحلة 7: حساب حجم البيانات

**البيانات في Odoo (الهدف):**

| الكيان | العدد |
|--------|-------|
| إجمالي التذاكر | 417 |
| تذاكر Muhide CX Team | 359 |
| تذاكر Users Onboarding | 56 |
| شركاء (partners) | 1,078 |
| شركات | 450 |
| أفراد | 628 |
| مستخدمين | 19 |
| مراحل | 16 |
| أنواع تذاكر | متعددة |
| وسوم | متعددة |
| سياسات SLA | 7 |
| سجلات SLA | 10 |
| رسائل على التذاكر | 3,652 |
| مرفقات | 497 (101 على التذاكر) |

**البيانات في المصدر (SalesOS):**

| الكيان | العدد |
|--------|-------|
| شركات | 5 |
| جهات اتصال | 3 |
| مستخدمين | 18 |
| تذاكر | 0 |
| أنشطة | 120 |
| أحداث نطاق | 127 |

---

### المرحلة 8: تقييم الاستعداد

| الفئة | التقييم | ملاحظات |
|-------|---------|---------|
| توفر بيانات المصدر | 3/10 | بيانات محدودة جداً |
| جاهزية الهدف | 9/10 | Odoo 17.0 جاهز بالكامل |
| تغطية خريطة الحقول | 7/10 | الحقول الأساسية مربوطة |
| جودة البيانات | 4/10 | تكرار ونصوص خاطئة |
| التقييم الإجمالي | **5/10** | **YELLOW** |

---

## 📁 الملفات المُنشأة

```
scripts/
  discover_source_db.py        # اكتشاف قاعدة البيانات المصدر
  discover_source_deep.py      # تفاصيل الجداول الرئيسية
  discover_odoo.py             # اكتشاف Odoo عبر JSON-RPC (فشل)
  discover_odoo_xmlrpc.py      # اكتشاف Odoo عبر XML-RPC (نجح)
  discover_odoo_quality.py     # فحص جودة البيانات في Odoo

docs/
  ODOO_MUHIDE_CX_DISCOVERY_REPORT.md  # التقرير النهائي الشامل
```

---

## 🔧 برومت مختصر لإعادة التنفيذ

إذا أعدت تنفيذ هذا في مشروع جديد، انسخ هذا البرومت:

```
أريد منك تنفيذ مرحلة Discovery & Mapping فقط، بدون أي تعديل أو كتابة على أي قاعدة بيانات.

الهدف:
لدي قاعدة بيانات مصدر PostgreSQL أريد لاحقاً نقل بياناتها إلى Odoo 17.0 Enterprise Helpdesk.

المعلومات المتاحة:
- قاعدة البيانات المصدر: PostgreSQL 16 على Docker (salesos-postgres-1)
- DATABASE_URL: postgresql+asyncpg://salesos:salesos_dev_password@localhost:5432/salesos
- Odoo URL: https://odoo-ps-psae-ratl.odoo.com
- Odoo Database: odoo-ps-psae-ratl-main-14005796
- Odoo User: ragheed.a@muhide.com
- Odoo API Key: 5974d5f2e79bd188c43484dd2c55af1184b53bab
- Odoo Version: 17.0 Enterprise
- Protocol: XML-RPC (JSON-RPC لا يعمل مع odoo.com hosting)

مهم جداً:
- Read-Only فقط — لا Create / Write / Update / Delete
- لا Import — لا تعديل Schema أو البيانات
- لا ترسل بيانات حساسة كاملة — استخدم samples masked
- لا تفترض أسماء الحقول — اكتشفها فعلياً

نفّذ على المراحل التالية:

1. فحص قاعدة البيانات المصدر:
   - عبر Docker: docker exec salesos-postgres-1 psql -U salesos -d salesos -t -A -F "|" -c "SQL"
   - اكتشف جميع الجداول والأعمدة والعلاقات
   - حدد الجداول المرشحة لنقلها

2. فحص اتصال Odoo:
   - عبر Python xmlrpc.client (لا urllib — XML-RPC فقط)
   - ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
   - common.authenticate(DB, USER, KEY, {}) → uid
   - models_rpc.execute_kw(DB, uid, KEY, model, method, args, kwargs)

3. اكتشاف نماذج Helpdesk:
   - helpdesk.ticket (جميع الحقول + x_studio_* المخصصة)
   - helpdesk.team (جميع الفرق)
   - helpdesk.stage (جميع المراحل)
   - res.partner (العملاء)
   - res.users (المستخدمين)
   - helpdesk.tag, helpdesk.ticket.type
   - helpdesk.sla, helpdesk.sla.status
   - ir.attachment (المرفقات)
   - mail.message (الرسائل)

4. فحص فريق Muhide CX تحديداً:
   - team_id = 1
   - التفاصيل الكاملة
   - التذاكر المرتبطة

5. بناء خريطة البيانات:
   - جدول Mapping: Source Table.Column → Odoo Model.Field
   - Mapping confidence
   - Transformation required?
   - Potential issues

6. اكتشاف مشاكل البيانات:
   - تكرارpartners في Odoo (checking by email)
   - نصوص عربية في حقول email
   - تذاكر بدون عميل أو مسؤول
   - تحقق من صحة الإيميلات

7. حساب الأحجام:
   - عدد كل كيان في المصدر والهدف

8. تقييم الاستعداد:
   - GREEN / YELLOW / RED لكل فئة

9. التقرير النهائي:
   - اكتب تقرير شامل في docs/ODOO_MUHIDE_CX_DISCOVERY_REPORT.md

10. القائمة النهائية:
    - ما الذي يمكن ترحيله
    - ما الذي لا يمكن ترحيله بعد
    - ما يحتاج تحويل
    - ما يحتاج خريطة يدوية
    - ما الصلاحيات المفقودة
    - الخطوة التالية قبل أول Import
```

---

## 🔑 مرجع API سريع

### Odoo XML-RPC

```python
# الاتصال
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', context=ctx)
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', context=ctx)

# المصادقة
uid = common.authenticate(DB, USER, KEY, {})

# بحث وقراءة
results = models.execute_kw(DB, uid, KEY, MODEL, 'search_read',
    [[DOMAIN]], {"fields": [FIELDS], "limit": LIMIT})

# عدّ
count = models.execute_kw(DB, uid, KEY, MODEL, 'search_count',
    [[DOMAIN]], {})

# metadata الحقول
fields = models.execute_kw(DB, uid, KEY, MODEL, 'fields_get', [],
    {"attributes": ["string","type","required","readonly","help",
                    "relation","selection","size"]})

# قراءة سجلات محددة
records = models.execute_kw(DB, uid, KEY, MODEL, 'read',
    [IDs], {"fields": [FIELDS]})
```

### PostgreSQL ( عبر Docker)

```bash
# بحث بسيط
docker exec salesos-postgres-1 psql -U salesos -d salesos -t -A -F "|" -c "SELECT * FROM companies;"

# مع فلتر
docker exec salesos-postgres-1 psql -U salesos -d salesos -t -A -F "|" -c "SELECT COUNT(*) FROM contacts WHERE email IS NOT NULL;"

# معلومات جدول
docker exec salesos-postgres-1 psql -U salesos -d salesos -t -A -F "|" -c "
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'companies' ORDER BY ordinal_position;"
```

---

## ⚠️ تحذيرات مهمة

1. **JSON-RPC لا يعمل** مع odoo.com hosting — استخدم XML-RPC دائماً
2. **ir.model مرفوض** للمستخدم العادي — لا تحاول enumerate جميع النماذج
3. **res.company مرفوض** partial — field-level security
4. **SSL verification** يجب تعطيله لـ odoo.com hosting
5. **البيانات الحساسة** — لا تطبع كلمات سر أو API keys كاملة في التقارير
6. **Read-Only** — لا تنفيذ أي write operation في هذه المرحلة

---

## 📊 النتيجة النهائية

**OD Muhide CX Team:**
- 359 تذكرة نشطة
- 4 فرق عمل
- 16 مرحلة
- 1,078 شريك
- 3,652 رسالة
- 497 مرفق
- 7 سياسات SLA
- 60+ حقل مخصص

**SalesOS Source:**
- 5 شركات، 3 جهات اتصال، 0 تذاكر
- معظم البيانات اختبارية

**التقييم: CONDITIONAL GO (Yellow)**
- جاهز بنيوياً
- يحتاج حل مشاكل التكرار والبيانات قبل الاستيراد
