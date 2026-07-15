# SalesOS API Portal

> **بوابة API — التوثيق الكامل لواجهات برمجة التطبيقات**
> Base URL: `https://api.salesos.sa/api/v1`

---

## Authentication

All endpoints (except login, register, health) require:

```
Authorization: Bearer <jwt_or_api_key>
X-Tenant-Id: <your_tenant_id>
```

See [Authentication Overview](overview.md) for full details.

---

## API Index

### 🏢 Core Platform

| API | File | Description |
|-----|------|-------------|
| **Overview & Auth** | [overview.md](overview.md) | Authentication, pagination, errors, rate limits |
| **Identity** | [identity.md](identity.md) | User management, roles, SSO, password reset |
| **Admin** | [admin.md](admin.md) | Tenant settings, users, plans, features |

### 📊 Dashboard & Analytics

| API | File | Description |
|-----|------|-------------|
| **Dashboard** | [dashboard.md](dashboard.md) | Main dashboard aggregation, KPIs, activity |
| **Analytics** | [analytics.md](analytics.md) | Standard & custom reports, exports |
| **Executive** | [executive.md](executive.md) | Executive-level dashboards and metrics |

### 💰 Revenue

| API | File | Description |
|-----|------|-------------|
| **Revenue Dashboard** | [revenue.md](revenue.md) | Revenue KPIs, targets, pipeline value |
| **Pipeline Analytics** | [pipeline.md](pipeline.md) | Deal velocity, conversion rates, forecasts |
| **Opportunities** | [opportunities.md](opportunities.md) | CRM opportunity CRUD, stage management |
| **NBA (Next Best Action)** | [nba.md](nba.md) | Decision intelligence, AI recommendations |

### 🏢 Company Intelligence

| API | File | Description |
|-----|------|-------------|
| **Companies** | [companies.md](companies.md) | Company CRUD, search, DNA profile |
| **Contacts** | [contacts.md](contacts.md) | Contact management, decision makers |
| **Entity Resolution** | [entity-resolution.md](entity-resolution.md) | Duplicate detection, fuzzy matching, merge |
| **Knowledge Graph** | [knowledge-graph.md](knowledge-graph.md) | Neo4j entity relationships, graph traversal |

### 🔍 Search

| API | File | Description |
|-----|------|-------------|
| **Search** | [search.md](search.md) | Full-text, semantic, hybrid search with RRF |

### 🤖 AI & Intelligence

| API | File | Description |
|-----|------|-------------|
| **RAG (AI Copilot)** | [rag.md](rag.md) | Retrieval-Augmented Generation, AI queries |
| **Feature Store** | [feature-store.md](feature-store.md) | Entity features, scoring, ML pipeline |
| **Data Fabric** | [data-fabric.md](data-fabric.md) | End-to-end data processing pipeline |

### 👥 People

| API | File | Description |
|-----|------|-------------|
| **Employee 360** | [employee-360.md](employee-360.md) | Employee intelligence, 360-degree views |
| **Work Intelligence** | [work-intelligence.md](work-intelligence.md) | Activity, focus time, collaboration patterns |

### 🔔 Notifications & Communication

| API | File | Description |
|-----|------|-------------|
| **Notifications** | [notifications.md](notifications.md) | In-app and email notifications |
| **Email** | [email.md](email.md) | Email integration, correspondence history |
| **Meetings** | [meetings.md](meetings.md) | Meeting scheduling, calendar integration |

### 🛠️ Platform

| API | File | Description |
|-----|------|-------------|
| **SSO** | [sso.md](sso.md) | Single Sign-On (Google, Microsoft, GitHub) |
| **Audit** | [audit.md](audit.md) | Audit log query, compliance events |
| **Workflows** | [workflows.md](workflows.md) | Workflow automation, triggers |
| **Dashboard Widgets** | [dashboard.md](dashboard.md) | Widget configuration and data |

### 🆕 v1.6.0 — New APIs

| API | File | Description |
|-----|------|-------------|
| **GraphQL** | [graphql.md](graphql.md) | `/graphql` — Schema-first GraphQL API, Apollo Federation-ready |
| **Rules Engine** | [rules.md](rules.md) | `/rules/*` — Business rules CRUD, evaluation, batch execution |
| **Signal Marketplace** | [signals.md](signals.md) | `/signals/*` — Third-party signal browsing, subscription, configuration |
| **Knowledge Packs** | [knowledge-packs.md](knowledge-packs.md) | `/knowledge-packs/*` — Domain knowledge package management |

---

## Common Headers

| Header | Description |
|--------|-------------|
| `Authorization: Bearer <token>` | JWT or API key |
| `X-Tenant-Id: <id>` | Your tenant identifier |
| `Content-Type: application/json` | Request body format |
| `Accept-Language: ar` or `en` | Response language |

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — missing/invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found — resource doesn't exist |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error |

## Pagination

List endpoints return paginated results:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

Query params: `?page=2&per_page=50` (max per_page: 100)

---

*Last updated: 2026-07-14*
*Files: 30 API docs (4 new: GraphQL, Rules Engine, Signal Marketplace, Knowledge Packs)*
