# ملحق: خطة الإصلاح المركّزة (Remediation Appendix)

**الحالة:** مدمجة داخل برنامج البرودكشن الكامل.  
**المصدر الرئيسي:** [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md)

هذه الوثيقة ليست برنامجاً مستقلاً بعد الترقية (2026-07-22). استخدمها كفهرس سريع لإغلاق فجوات تدقيق GA فقط؛ للنشر والـ DR والـ Go-Live راجع الخطة الكاملة.

## أين تذهب موجات الإصلاح؟

| موجة إصلاح قديمة | موقعها في PRODUCTION_PLAN |
|------------------|---------------------------|
| Wave 0 Build | §4–5 Wave 0 (`PROD-W0-*`) |
| Wave 1 Alembic | Wave 1 (`PROD-W1-*`) |
| Wave 2 Tests | Wave 3 (`PROD-W3-*`) — بعد Security P0 |
| Security P0 | Wave 2 (`PROD-W2-*`) |
| Runtime/FE image | Wave 4 |
| Auth/API | Wave 5 |
| AI honesty | Wave 6 |
| Docs/governance | Wave 7 |
| Hardening e2e | Waves 8–11 + §13 |

## فهرس سريع P0

| GA ID | بند الإنتاج |
|-------|-------------|
| GA-P0-01 / 02 | PROD-W0-001 / 002 |
| GA-P0-03 | PROD-W1-001 |
| GA-P0-04 | PROD-W3-001 |
| GA-P0-05 | PROD-W2-004 |
| GA-P0-SEC-01/02/03 | PROD-W2-001/002/003 |

للتفاصيل (خطوات، قبول، جهد، مالك، مسار حرج، Go-Live): **[PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md)**.
