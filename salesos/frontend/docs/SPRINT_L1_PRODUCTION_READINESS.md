# Sprint L1 — Production Readiness

> الهدف: تحويل SalesOS من مشروع Build إلى Release Candidate
> المدة: 2-3 أسابيع

---

## L1.1 — API Contract Alignment

### Frontend → Backend Mapping

| # | Frontend Call | Backend Endpoint | الحالة |
|---|---------------|------------------|--------|
| 1 | `GET /api/v1/dashboard` | → `GET /dashboard` | 🟡 |
| 2 | `GET /api/v1/companies/{id}/intelligence` | → `GET /companies/{id}/360` | 🔴 مختلف |
| 3 | `GET /api/v1/companies/{id}` | → `GET /companies/{id}` | 🟢 متطابق |
| 4 | `GET /api/v1/companies` | → `GET /companies` | 🟢 متطابق |
| 5 | `POST /api/v1/search` | → `POST /search` | 🟡 |
| 6 | `POST /api/v1/search/suggest` | → missing | 🔴 |
| 7 | `POST /api/v1/search/ai` | → missing | 🔴 |
| 8 | `POST /api/v1/opportunities` | → missing | 🔴 |
| 9 | `PUT /api/v1/opportunities/{id}/stage` | → missing | 🔴 |
| 10 | `GET /api/v1/tasks` | → missing | 🔴 |

### الإجراءات

1. **إضافة الـ 6 Endpoints المفقودة** إلى backend
2. **توحيد الاسم**: `/intelligence` ← `/360` في frontend (أو إضافة alias في backend)
3. **تحديث frontend API hooks** لتستخدم الـ endpoints الصحيحة
4. **إزالة** `localStorage` من `opportunity.store.ts` واستبدالها بـ API calls

---

## L1.2 — Remove localStorage + Mocks

| الملف | الاستخدام | الإجراء |
|-------|----------|--------|
| `opportunity.store.ts` | localStorage للفرص | استبدال بـ API |
| `task.store.ts` | localStorage للمهام | استبدال بـ API |
| `PipelineContainer.tsx` | حساب الأنابيب محليًا | استبدال بـ API |
| `src/mocks/handlers.ts` | Mock API للـ dev | إبقاء للـ dev فقط |

---

## L1.3 — Docker Production Validation

- [ ] `docker compose up --build` يعمل بدون أخطاء
- [ ] Frontend يخدم على port 3000
- [ ] Backend يخدم على port 8000
- [ ] API calls تصل من frontend إلى backend
- [ ] PostgreSQL متصل وقاعد البيانات مهاجرة
- [ ] Health checks كلها pass

---

## L1.4 — Monitoring & Error Tracking

- [ ] إضافة Sentry (Raven) للـ frontend
- [ ] Sentry للـ backend
- [ ] Health endpoint: `GET /health` ← `{ status: "ok", services: {...} }`
- [ ] Request logging (Morgan للـ backend)
- [ ] Performance metrics (Prometheus)

---

## L1.5 — Security Review

- [ ] JWT authentication على جميع endpoints
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Helmet headers
- [ ] Input validation (Zod / Pydantic)
- [ ] SQL injection protection (parameterized queries)
- [ ] `X-Tenant-Id` مطلوب لكل request

---

## L1.6 — Performance Baseline

| Endpoint | Target | Current |
|----------|--------|---------|
| Dashboard | <200ms | — |
| Company 360 | <500ms | — |
| Search | <800ms | — |
| Opportunities | <200ms | — |

---

## L1.7 — Release Candidate (RC1)

المخرجات المطلوبة:
- [ ] `docker compose up --build` يعمل
- [ ] جميع الـ API endpoints متطابقة
- [ ] جميع الـ 1129 اختبار pass
- [ ] Pilot-ready مع seed data
- [ ] التوثيق كامل
- [ ] Docker image منشور على registry
