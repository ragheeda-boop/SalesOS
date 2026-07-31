# SalesOS — Source of Truth

> **المرجع الموحد لكل منتج، موديول، صفحة، وودجت في المنصة**
> Unified reference for AI agents to understand what exists, where it lives, and how things connect.
> Last updated: 2026-07-30 | API: `GET /api/v1/source-of-truth`

---

## 1. What is the Source of Truth?

SalesOS has **four separate registries** that were never connected:

| Registry | Location | Holds | Items |
|----------|----------|-------|-------|
| `@Capability` decorator | `runtime/capability_framework/` | Product capability manifests | 13 |
| `FeatureRegistry` | `sdk/feature_registry.py` | Backend feature modules (sprint-tracked) | 7 |
| `SDKCapabilityRegistry` | `sdk/capability_registry.py` | SDK-level capabilities with executors | 21 |
| `WidgetRegistry` | `runtime/widget_engine/` | Widget definitions for the UI | 19+ |

**The Source of Truth API** `GET /api/v1/source-of-truth` merges all four into one unified response, so any AI agent or developer can ask a single question and learn everything about the platform.

---

## 2. API Reference

| Endpoint | Returns | Use case |
|----------|---------|----------|
| `GET /api/v1/source-of-truth` | All products + modules + pages + widgets | Full platform scan |
| `GET /api/v1/source-of-truth/products` | Products only | "What products/capabilities does SalesOS offer?" |
| `GET /api/v1/source-of-truth/modules` | Modules only | "What backend modules exist?" |
| `GET /api/v1/source-of-truth/pages` | Pages only | "What routes does the frontend have?" |
| `GET /api/v1/source-of-truth/widgets` | Widgets only | "What widgets can be placed on a page?" |

**Auth:** Optional token (`get_optional_token`) — works for testing without auth.

---

## 3. Products — Capability Framework (@Capability decorator)

13 products, each with its contract (entities, APIs, events, permissions) and UI definition (tabs, routes, sidebar, icon).

| ID | Name | Version | Status | Dependencies | Icon | Routes | Tabs |
|----|------|---------|--------|-------------|------|--------|------|
| `identity` | Identity & Access Management | 1.0.0 | STABLE | — | shield | `/settings`, `/settings/users` | Settings, Users, Roles, Audit |
| `company` | Company Intelligence | 1.0.0 | STABLE | identity, data-fabric | building | `/companies`, `/companies/{id}` | Overview, Timeline, Contacts, Revenue, Signals, Products, Documents, Recommendations, Graph, Audit |
| `data-fabric` | Data Fabric | 1.0.0 | STABLE | identity | database | `/data-fabric` | Sources, Pipeline, Schedule, Logs |
| `search` | Universal Search | 1.0.0 | STABLE | company, identity | search | `/search` | — |
| `timeline` | Universal Timeline | 1.0.0 | STABLE | event-runtime | clock | — | Activity, History |
| `knowledge-graph` | Knowledge Graph | 1.0.0 | BETA | company | share2 | — | Graph View, Relationships, Path Finder |
| `feature-store` | Feature Store | 1.0.0 | STABLE | company | bar-chart | — | Features, Scores, History |
| `decision-engine` | Decision Intelligence Engine | 1.0.0 | BETA | feature-store, context-runtime, policy-runtime | zap | `/decisions` | Next Best Action, Decisions, History, Metrics |
| `event-runtime` | Event Runtime | 1.0.0 | STABLE | — | — | — | — |
| `activity-intelligence` | Activity Intelligence | 1.0.0 | STABLE | company, identity, timeline, search | activity | — | Dashboard, Emails, Calendar, Follow-ups |
| `workflow` | Workflow Engine | 0.9.0 | BETA | identity, company, event-runtime, decision-engine | settings | `/automation` | Builder, Templates, Executions, Jobs, Webhooks |
| `marketplace` | Marketplace | 0.1.0 | DRAFT | capability-framework | shopping-cart | `/marketplace` | Browse, Installed, Updates |
| `capability-framework` | Capability Framework | 1.0.0 | STABLE | — | grid | `/capabilities` | All Capabilities, Health, Registry |

**Key for AI agents:**
- Use `products` to discover what entities a capability owns (e.g., `company` owns: company, contact, license, branch)
- Use `contract.apis` to know what API paths belong to each capability
- Use `ui.tabs` to know what UI sections each capability provides
- A status of `DRAFT` means not shipped; `BETA` means functional but not hardened

---

## 4. Modules — FeatureRegistry + SDK CapabilityRegistry

23 modules merged from both registries. SDK entries override FeatureRegistry entries when names conflict.

### FeatureRegistry Modules (7)

| Name | Label | Label (AR) | Status | API Prefix | Sprint | Owner | Entities |
|------|-------|-----------|--------|-----------|-------|-------|---------|
| `identity` | Identity & Access | الهوية والوصول | IN_PROGRESS | `/api/v1` | 1 | platform | Tenant, User, Role |
| `company` | Company Intelligence | ذكاء الشركات | IN_PROGRESS | `/api/v1` | 1 | platform | Company, Branch, License, Contact, GoldenRecord |
| `timeline` | Timeline & Activity | الجدول الزمني والنشاط | PLANNED | `/api/v1` | 4 | platform | Activity, Timeline |
| `opportunity` | Pipeline & Opportunities | خطة المبيعات والفرص | PLANNED | `/api/v1` | 5 | crm | Opportunity, Pipeline, Stage |
| `search` | Search & Discovery | البحث والاكتشاف | COMPLETED | `/api/v1` | 3 | platform | SearchIndex, SavedSearch, SearchHistory |
| `signal_marketplace` | Signal Marketplace | سوق الإشارات | IN_PROGRESS | `/api/v1/signals` | 10 | platform | Signal, SignalSubscription, SignalEvent |
| `entity_resolution` | Entity Resolution | حل الكيانات | IN_PROGRESS | `/api/v1/entity-resolution` | 2 | platform | GoldenRecord, EntityResolutionConflict, EntityResolutionLog |

### SDK CapabilityRegistry Modules (21)

| Name | Label | Label (AR) | Type | Executors |
|------|-------|-----------|------|-----------|
| `company` | Company Intelligence | ذكاء الشركات | DOMAIN | CompanySearchRepository (POSTGRES_BTREE), CompanyTrigramRepository (POSTGRES_TRIGRAM) |
| `search` | Search & Discovery | البحث والاكتشاف | SEARCH | SearchPlanner (HYBRID) |
| `timeline` | Timeline & Activity | الجدول الزمني والنشاط | TIMELINE | (empty) |
| `contract` | Contract Management | إدارة العقود | DOMAIN | — |
| `proposal` | Proposal Management | إدارة العروض | DOMAIN | — |
| `quote` | Quote Management | إدارة عروض الأسعار | DOMAIN | — |
| `activity` | Activity Management | إدارة النشاطات | DOMAIN | — |
| `pipeline` | Pipeline Management | إدارة خط المبيعات | DOMAIN | — |
| `opportunity` | Opportunity Management | إدارة الفرص | DOMAIN | — |
| `email` | Email Intelligence | ذكاء البريد الإلكتروني | DOMAIN | — |
| `quota` | Quota Management | إدارة الحصص | DOMAIN | — |
| `territory` | Territory Management | إدارة المناطق | DOMAIN | — |
| `analytics` | Revenue Analytics | تحليلات الإيرادات | DOMAIN | — |
| `forecast` | Revenue Forecasting | التوقعات الإيرادية | DOMAIN | — |
| `context` | Decision Context | سياق القرارات | DOMAIN | — |
| `recommendation` | Recommendation Engine | محرك التوصيات | DOMAIN | — |
| `entity_resolution` | Entity Resolution | حل الكيانات | DOMAIN | (empty) |
| `infrastructure` | Infrastructure | البنية التحتية | DOMAIN | (empty) |
| `meeting` | Meeting Intelligence | ذكاء الاجتماعات | DOMAIN | — |
| `playbook` | Sales Playbook | دليل المبيعات | DOMAIN | — |
| `ai_copilot` | AI Copilot | المساعد الذكي | AI | PgVectorCompanyRepository (PGVECTOR_HNSW) |

**Key for AI agents:**
- `status: PLANNED` = not yet built; `IN_PROGRESS` = partially built; `COMPLETED` = shipped
- SDK modules with executors have live implementation; those without executors are stubs
- Entity names in FeatureRegistry are the database entity types
- Arabic labels (`label_ar`) exist for bilingual UI

---

## 5. Pages — Frontend Routes

31 pages aggregated from 3 sources: capability UI routes (12), core hardcoded pages (9), and v3 pages (13).

### Capability-Defined Routes

| Route | Capability | Icon | Tabs Available |
|-------|-----------|------|---------------|
| `/companies` | company | building | Overview, Timeline, Contacts, Revenue, Signals, Products, Documents, Recommendations, Graph, Audit |
| `/companies/{id}` | company | building | (same as above) |
| `/settings` | identity | shield | Settings, Users, Roles, Audit |
| `/settings/users` | identity | shield | — |
| `/data-fabric` | data-fabric | database | Sources, Pipeline, Schedule, Logs |
| `/search` | search | search | — |
| `/decisions` | decision-engine | zap | Next Best Action, Decisions, History, Metrics |
| `/automation` | workflow | settings | Builder, Templates, Executions, Jobs, Webhooks |
| `/marketplace` | marketplace | shopping-cart | Browse, Installed, Updates |
| `/capabilities` | capability-framework | grid | All Capabilities, Health, Registry |

### Core Pages

| Route | Label | Capability |
|-------|-------|-----------|
| `/login` | Login | identity |
| `/register` | Register | identity |
| `/dashboard` | Dashboard | company |
| `/admin` | Admin | identity |
| `/admin/tenants` | Admin Tenants | identity |
| `/admin/audit` | Admin Audit | identity |
| `/admin/flags` | Admin Flags | identity |
| `/admin/config` | Admin Config | identity |
| `/settings` | Settings | identity |

### v3 Pages (Next-Gen UI)

| Route | Label | Capability |
|-------|-------|-----------|
| `/v3` | V3 Shell | capability-framework |
| `/v3/activities` | Activities (v3) | activity-intelligence |
| `/v3/admin` | Admin (v3) | identity |
| `/v3/analytics` | Analytics (v3) | feature-store |
| `/v3/companies` | Companies (v3) | company |
| `/v3/contacts` | Contacts (v3) | company |
| `/v3/crm` | CRM (v3) | company |
| `/v3/cs` | Customer Success (v3) | company |
| `/v3/employee` | Employee (v3) | activity-intelligence |
| `/v3/people` | People (v3) | company |
| `/v3/settings` | Settings (v3) | identity |
| `/v3/shell` | Shell (v3) | capability-framework |
| `/v3/tasks` | Tasks (v3) | workflow |

### Additional Frontend Routes (from codebase, not in API)

These exist in the Next.js app but are **not yet registered** in the Source of Truth API:

| Route Group | Routes |
|-------------|--------|
| **Detail pages** | `/companies/[id]/360`, `/opportunities/[id]`, `/contacts`, `/employees`, `/employees/me`, `/employees/[id]` |
| **Revenue** | `/revenue`, `/revenue/quotas`, `/revenue/territories` |
| **Pipeline** | `/pipeline`, `/pipeline/analytics` |
| **Forecast** | `/forecast` |
| **Search** | `/search/analytics` |
| **Decisions** | `/decisions/templates` |
| **Meetings** | `/meetings` |
| **Graph** | `/graph` |
| **Signals** | `/signals` |
| **Analytics** | `/analytics`, `/analytics/automation`, `/analytics/employees`, `/analytics/pipeline`, `/analytics/reports/builder`, `/analytics/revenue`, `/analytics/sales` |
| **Automation** | `/automation/analytics`, `/automation/workflows/new` |
| **Rules** | `/rules` |
| **Monitoring** | `/monitoring` |
| **Customer Success** | `/customer-success` |
| **AI/Copilot** | `/ai`, `/copilot`, `/copilot/telemetry`, `/rag` |
| **Knowledge** | `/knowledge`, `/knowledge/connectors` |
| **Marketplace** | `/marketplace/[pluginId]/config` |

**Key for AI agents:**
- Capability routes are defined in `@Capability` decorator's `ui.routes`
- Core/v3 pages are hardcoded in `source_of_truth.py` — needs periodic sync with actual frontend
- Additional routes exist in `src/app/` and `src/app/v3/` that should eventually be registered

---

## 6. Widgets — WidgetRegistry

19 built-in widgets, plus auto-generated widgets from capability tabs.

| ID | Name | Capability | Renderer | Slots | Icon |
|----|------|-----------|----------|-------|------|
| `overview` | Overview | company | OverviewWidget | CENTER, TOP | layout-dashboard |
| `timeline` | Timeline | timeline | TimelineWidget | CENTER, LEFT, RIGHT | clock |
| `signals` | Signals | company | SignalWidget | CENTER, RIGHT | activity |
| `buying_committee` | Buying Committee | company | BuyingCommitteeWidget | CENTER, LEFT, RIGHT | users |
| `revenue` | Revenue | company | RevenueWidget | CENTER, RIGHT, TOP | trending-up |
| `knowledge_graph_view` | Graph | knowledge-graph | GraphWidget | CENTER, FULL | share2 |
| `company_products` | Products | company | ProductsWidget | CENTER, RIGHT | package |
| `company_branches` | Branches | company | BranchesWidget | CENTER, RIGHT | map-pin |
| `company_licenses` | Licenses | company | LicensesWidget | CENTER, RIGHT | file-text |
| `documents` | Documents | company | DocumentsWidget | CENTER, RIGHT | file |
| `meetings` | Meetings | company | MeetingsWidget | CENTER, RIGHT | calendar |
| `emails` | Emails | company | EmailsWidget | CENTER, RIGHT | mail |
| `recommendations` | Recommendations | decision-engine | RecommendationWidget | CENTER, RIGHT, TOP | zap |
| `tasks` | Tasks | company | TasksWidget | CENTER, LEFT, RIGHT | check-square |
| `ai_copilot` | AI Copilot | decision-engine | AICopilotWidget | LEFT, RIGHT | sparkles |
| `audit_log` | Audit | identity | AuditWidget | BOTTOM, CENTER | clipboard-list |
| `entity_settings` | Settings | company | SettingsWidget | CENTER | settings |
| `feature_scores` | Scores | feature-store | FeatureScoreWidget | CENTER, TOP, RIGHT | bar-chart |
| `company_contacts` | Contacts | company | ContactsWidget | CENTER, RIGHT | user |

**Key for AI agents:**
- Each widget belongs to a `capability_id` — use this to know what capability a widget surfaces
- `slots` define where the widget can be placed in a layout (LEFT, RIGHT, CENTER, TOP, BOTTOM, FULL)
- Auto-generated widgets are created via `generate_from_capabilities()` for capability tabs not covered by builtins

---

## 7. How AI Agents Should Use This Document

### Discovery Flow

```
You (AI) → GET /api/v1/source-of-truth → Full platform map
```

1. **"What capabilities exist?"** → `GET /api/v1/source-of-truth/products`
2. **"What backend modules are implemented?"** → `GET /api/v1/source-of-truth/modules`
3. **"Where do I navigate for X?"** → `GET /api/v1/source-of-truth/pages`
4. **"What widgets can I place on a page?"** → `GET /api/v1/source-of-truth/widgets`

### Common Questions Answered

| Question | Where to Look |
|----------|--------------|
| What entities does Company Intelligence manage? | `products[].contract.entities` for `id=company` |
| What API endpoints are available? | `products[].contract.apis` |
| Is this module built or planned? | `modules[].status` (COMPLETED vs PLANNED) |
| What pages exist for a capability? | `pages[].capability_id` filter |
| What widgets show company data? | `widgets[].capability_id == "company"` |
| Does this capability depend on others? | `products[].dependencies` |
| Is there Arabic support? | `modules[].label_ar` |
| What events does this module emit? | `modules[].events.produces` |

---

## 8. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Source of Truth API                           │
│              GET /api/v1/source-of-truth                        │
│                                                                │
│  ┌────────────┐  ┌────────────┐  ┌────────┐  ┌────────────┐   │
│  │ Capability │  │   SDK     │  │ Widget │  │ Frontend   │   │
│  │ Framework  │  │ Capability│  │ Registry│  │ Routes     │   │
│  │ Decorator  │  │ Registry  │  │         │  │ (hardcoded)│   │
│  └────────────┘  └────────────┘  └────────┘  └────────────┘   │
│       │               │              │              │          │
│       ▼               ▼              ▼              ▼          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Unified JSON Response                     │    │
│  │  { products: [...], modules: [...],                    │    │
│  │    pages: [...], widgets: [...] }                      │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### Code Location

- **Router:** `salesos/backend/app/routers/source_of_truth.py`
- **Registered at:** `salesos/backend/app/boot/routers.py` (line 151)
- **Registries consumed:**
  - `runtime/capability_framework/` — Product capabilities
  - `runtime/widget_engine/` — Widget definitions
  - `sdk/capability_registry.py` — SDK capability registry
  - `sdk/feature_registry.py` — Feature module registry

---

## 9. Extending the Source of Truth

### Adding a New Product

```python
from runtime.capability_framework import Capability

@Capability(
    id="my-feature",
    name="My New Feature",
    version="1.0.0",
    status="DRAFT",
    ...
)
class MyFeature:
    pass
```

The Source of Truth API picks it up automatically from `CapabilityDecorator.all()`.

### Adding a New Module

```python
from sdk.feature_registry import register_feature
# or use the decorator
```

### Adding a New Widget

```python
from runtime.widget_engine import WidgetRegistry, WidgetDefinition, WidgetSlot

WidgetRegistry.register(WidgetDefinition(
    id="my_widget",
    name="My Widget",
    capability_id="company",
    ...
))
```

### Adding New Hardcoded Pages

Edit `_get_all_pages()` in `source_of_truth.py` and add to `core_pages` or `v3_pages` lists.

---

## 10. Current Limitations

- **Pages list is partially hardcoded** — core and v3 pages are hand-maintained lists in `source_of_truth.py`. They should eventually be auto-discovered from the Next.js app directory.
- **~50 frontend routes are not registered** — the detailed pages (e.g., `/opportunities/[id]`, `/revenue/quotas`) exist in the Next.js app but are not yet in the Source of Truth API.
- **SDK modules without executors are stubs** — modules like `contract`, `proposal`, `quote` are registered but have no live backend implementation.
- **No capability-to-module cross-reference** — the API does not explicitly link which products use which modules (inferred through matching names).
- **Auth is optional** — `get_optional_token` is used for testing; production should use `verify_token`.

---

*This document is the human-readable companion to the Source of Truth API. AI agents should prefer the live API (`GET /api/v1/source-of-truth`) for the most current data. This document provides context, tables, and explanation the API response does not.*

*For API-level documentation, see `docs/api/OPENAPI.md` → "Source of Truth" section.*
