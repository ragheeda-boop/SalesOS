# SalesOS Platform Roadmap

> آخر تحديث: RT1 — آذار 2026
> الحالة: Platform Kernel Frozen ✅ → Commercial Platform In Progress

---

## 1. Platform State

| Platform | Status |
|----------|--------|
| **Platform Kernel** | ✅ **Frozen** |
| **Commercial Platform** | 🟡 **In Progress** |
| Intelligence Platform | ⏳ Planned |
| Automation Platform | ⏳ Planned |
| Enterprise Platform | ⏳ Planned |

### Kernel Freeze — رسمي اعتبارًا من RT1

لا يضاف كود مباشر داخل:

- `identity/`
- `company/`
- `search/`
- `timeline/`
- `sdk/`
- `events/`
- `metadata/`
- `capability_registry/`

أي تعديل على Kernel يتطلب: ADR + Benchmark + Architecture Review.

---

## 2. Release Trains

### RT1 — Commercial Platform

**Goal:** Sales Workspace MVP

**Key Domains:**
- `commercial/opportunity/` — الفرص التجارية
- `commercial/pipeline/` — خط المبيعات والمراحل
- `commercial/account/` — إدارة الحسابات
- `commercial/forecast/` — توقعات المبيعات
- `commercial/activity/` — أنشطة البيع

**Exit Criteria:**
- Opportunity management (create, stage progression, won/lost)
- Pipeline visualization (kanban or table)
- Forecast rollup from pipeline
- Activity logging per opportunity
- Integration with Company domain
- All tests pass with InMemory repos
- Frozen Interfaces preserved

---

### RT2 — Intelligence Platform

**Goal:** Customer Intelligence

**Key Domains:**
- `intelligence/graph/` — Knowledge Graph (Neo4j)
- `intelligence/embedding/` — Vector embeddings
- `intelligence/recommendation/` — Recommendations
- `intelligence/insight/` — Automated insights
- `intelligence/score/` — Scoring & prediction

**Key Architecture:**
- `SearchPlanner` → `GraphSearchRepository` + `PgVectorRepository`
- Timeline data feeds into recommendations
- Company resolution graph

---

### RT3 — Automation Platform

**Goal:** AI Agents & Workflows

**Key Domains:**
- `automation/workflow/` — Workflow engine
- `automation/agent/` — AI Agent runtime
- `automation/integration/` — External connectors
- `automation/rule/` — Business rules

---

### RT4 — Enterprise Platform

**Goal:** Marketplace & Multi-region

**Key Domains:**
- `enterprise/marketplace/` — Capability marketplace
- `enterprise/multi_tenant/` — Enterprise multi-tenancy
- `enterprise/api_gateway/` — External API management
- `enterprise/audit/` — Enterprise audit & compliance

---

## 3. Architecture Milestones

```
Kernel Freeze ————————————————— ✅ RT1 Start

Commercial MVP ——————————————— 🎯 RT1 End

Customer 360 —————————————————— 🎯 RT2 End

AI Copilot ———————————————————— 🎯 RT3 End

Marketplace —————————————————— 🎯 RT4 End

Enterprise GA ————————————————— 🎯 RT4 End
```

---

## 4. Rules

### Frozen Interfaces

| Interface | Status |
|-----------|--------|
| `SearchQuery` | Frozen |
| `SearchResult` | Frozen |
| `SearchPlanner` | Frozen |
| `SearchRepository[T]` | Frozen |
| `TimelineEvent` | Frozen |
| `TimelineRepository` | Frozen |
| `Actor → Activity → Target → Outcome` | Frozen |
| `DomainEvent` (CloudEvents 1.0) | Frozen |

### Kernel Stability Policy

أي تغيير في Kernel يتطلب:
1. ADR جديد يشرح Rationale
2. Benchmark إذا كان يؤثر على Performance
3. Architecture Review (مراجعة معمارية)
4. إثبات أن التغيير لا يكسر الـ Frozen Interfaces

### Benchmark First

لا تُضاف تقنية جديدة (Index, Cache, Vector Store, AI Model, Queue) إلا بعد Benchmark يثبت الحاجة.

### Constitution Compliance

كل Capability جديدة يجب أن تلتزم بـ 10 مواد الدستور التقني.
المرجع: `/platform/CONSTITUTION.md`

### New Capability Over Kernel Modification

قبل أي تعديل على Kernel، اسأل:
> هل يمكن تحقيق الهدف من خلال Capability جديدة فوق الـ Kernel؟

إذا كانت الإجابة نعم، فلا تعدّل الـ Kernel.

---

## Capability First Policy

اعتبارًا من RT1، أي Feature جديد يجب أن يجيب أولًا:

> **أي Capability قائمة سأعيد استخدامها؟**

وليس:

> "أي كود جديد سأكتبه؟"

مثال: Opportunity يجب أن يستخدم:
- **Search** → `OpportunitySearchRepository implements SearchRepository[T]` (لا تبني Search جديد)
- **Timeline** → كل عملية تنتج TimelineEvent عبر EventBus (لا تبني Audit خاص)
- **Events** → `OpportunityCreated`, `OpportunityStageChanged` (موجودة في Domain Events Library)
- **SDK** → كل شيء عبر SDK (Permissions, Metadata, Telemetry)

هذه السياسة تمنع تكرار الكود وتحافظ على تماسك المنصة مع نموها.

---

*Roadmap updated at RT1 start. Next review at RT1 exit.*
