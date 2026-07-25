# 09 — Screen Inventory (Current State)

> Last verified: 2026-07-15
> Method: Static analysis of all 30 `page.tsx` files + workspace components in `salesos/frontend/src/app/`
> Frontend framework: Next.js 14 App Router, `@salesos/ui`, TanStack Query, i18n (`useTranslation`)

---

## Summary

| Metric | Count |
|--------|-------|
| Total screens (page.tsx) | 30 |
| Auth screens | 3 (landing, login, register) |
| Dashboard screens | 27 (inside `(dashboard)` route group) |
| Feature workspace components delegated | 14 |
| DecisionProvider-wrapped screens | 3 (opportunities/[id], pipeline, revenue) |
| Screens with modals/inline forms | 10 |
| Screens with real-time / polling | 2 (monitoring, copilot) |

---

## Route Map

```
/                                    — Landing page (public)
/login                               — Login
/register                            — Register

── (dashboard) layout (auth required) ──

/(dashboard)/                        — Dashboard (widget grid)
/(dashboard)/activities              — Activity feed
/(dashboard)/admin                   — Admin console
/(dashboard)/ai                      — AI Prompt Manager
/(dashboard)/analytics               — Analytics & charts
/(dashboard)/automation              — Automation engine
/(dashboard)/companies               — Company list
/(dashboard)/companies/[id]          — Company detail (360°)
/(dashboard)/contacts                — Contact list
/(dashboard)/copilot                 — AI Copilot (standalone)
/(dashboard)/customer-success        — Customer success
/(dashboard)/decisions               — Decision center
/(dashboard)/employees/me            — My 360°
/(dashboard)/employees/[id]          — Employee 360°
/(dashboard)/forecast                — Revenue forecast
/(dashboard)/graph                   — Knowledge graph
/(dashboard)/meetings                — Meeting prep
/(dashboard)/monitoring              — System monitoring
/(dashboard)/opportunities           — Pipeline kanban
/(dashboard)/opportunities/[id]      — Opportunity detail
/(dashboard)/pipeline                — Pipeline workspace
/(dashboard)/rag                     — RAG chat + docs
/(dashboard)/revenue                 — Revenue workspace
/(dashboard)/rules                   — Business rules
/(dashboard)/search                  — Full-text search
/(dashboard)/settings                — User settings
/(dashboard)/signals                 — Signals marketplace
```

---

## Screen Details

### 1. Landing Page — `/`

| Field | Value |
|-------|-------|
| **File** | `src/app/page.tsx` |
| **Component** | Inline — Hero section + feature cards |
| **Auth required** | No (public) |
| **Layout** | Minimal (no sidebar) |
| **Data displayed** | Static marketing content, Arabic/English feature descriptions |
| **API calls** | None |
| **Interactive elements** | Login button → `/login`, Register button → `/register` |
| **i18n** | `useTranslation()` — full AR/EN support |
| **State** | Production-ready |

---

### 2. Login — `/login`

| Field | Value |
|-------|-------|
| **File** | `src/app/(auth)/login/page.tsx` |
| **Component** | `LoginForm` |
| **Auth required** | No |
| **Data displayed** | Login form (email, password) |
| **API calls** | `useLogin()` mutation → `POST /api/v1/auth/login` |
| **Interactive elements** | Email input, password input, submit button, link to register |
| **State** | Production-ready |

---

### 3. Register — `/register`

| Field | Value |
|-------|-------|
| **File** | `src/app/(auth)/register/page.tsx` |
| **Component** | `RegisterForm` |
| **Auth required** | No |
| **Data displayed** | Registration form (name, email, password, company) |
| **API calls** | `useRegister()` mutation → `POST /api/v1/auth/register` |
| **Interactive elements** | Name, email, password, company inputs, submit, link to login |
| **State** | Production-ready |

---

### 4. Dashboard — `/(dashboard)/`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/page.tsx` |
| **Workspace** | `features/dashboard/_layout/dashboard-page.tsx` |
| **Auth required** | Yes |
| **Components** | `DashboardPage` — widget registry grid, `MetricsHeader` |
| **Data displayed** | Aggregated KPI widgets (revenue, pipeline, activities, score), metric cards |
| **API calls** | `GET /api/v1/dashboard/metrics` (via TanStack Query), widget-specific queries |
| **Interactive elements** | Widget grid (customizable layout), metric cards with drill-down |
| **Widgets** | Configurable via `WIDGET_REGISTRY` — each widget is a self-contained container |
| **State** | Production-ready |

---

### 5. Activities — `/(dashboard)/activities`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/activities/page.tsx` |
| **Auth required** | Yes |
| **Components** | `ActivityFeed`, `ActivityFilters` |
| **Data displayed** | Global activity feed — calls, emails, meetings, notes, documents |
| **API calls** | `useGlobalActivities()` → `GET /api/v1/activities` (paginated) |
| **Interactive elements** | Search bar, type filter dropdown, date range picker, infinite scroll |
| **Filters** | Activity type, date range, entity (company/contact) |
| **State** | Production-ready |

---

### 6. Admin Console — `/(dashboard)/admin`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/admin/page.tsx` |
| **Workspace** | `features/admin/AdminWorkspace.tsx` |
| **Auth required** | Yes (admin role) |
| **Components** | 8-tab layout |
| **Data displayed** | Tenant management, plan management, user management, feature flags, background jobs, AI cost tracking, system health |
| **API calls** | Multiple — `GET /api/v1/admin/tenants`, `GET /api/v1/admin/plans`, `GET /api/v1/admin/users`, `GET /api/v1/admin/flags`, `GET /api/v1/admin/jobs`, `GET /api/v1/admin/ai-costs`, `GET /api/v1/admin/health` |
| **Tabs** | overview, tenants, plans, users, flags, jobs, ai-costs, health |
| **Interactive elements** | Tab navigation, create/edit/delete modals per section |
| **State** | Production-ready |

---

### 7. AI Prompt Manager — `/(dashboard)/ai`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/ai/page.tsx` |
| **Auth required** | Yes |
| **Components** | `PromptList`, `PromptEditor`, `PromptTestPanel` |
| **Data displayed** | List of registered AI prompts, versions, status |
| **API calls** | `GET /api/v1/ai/prompts`, `POST /api/v1/ai/prompts/{id}/test`, `POST /api/v1/ai/prompts/{id}/activate` |
| **Interactive elements** | Create prompt, edit prompt, test prompt (run with sample input), activate prompt, version toggle |
| **State** | Production-ready |

---

### 8. Analytics — `/(dashboard)/analytics`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/analytics/page.tsx` |
| **Workspace** | `features/analytics/AnalyticsWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `ExecutiveDashboard`, `BarChart`, `PieChart`, `MetricCard` |
| **Data displayed** | Revenue trends, pipeline breakdown, activity distribution, conversion rates |
| **API calls** | `GET /api/v1/analytics/executive` |
| **Interactive elements** | Date range picker, chart type toggle, export button |
| **State** | Production-ready |

---

### 9. Automation — `/(dashboard)/automation`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/automation/page.tsx` |
| **Workspace** | `features/automation/workspace/automation/AutomationWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `WorkflowList`, `TemplateGallery`, `ExecutionHistory` |
| **Data displayed** | Active workflows, templates, execution history, success/failure rates |
| **API calls** | `GET /api/v1/automation/workflows`, `GET /api/v1/automation/templates`, `GET /api/v1/automation/history` |
| **Tabs** | workflows, templates, history |
| **Interactive elements** | Create workflow, activate/deactivate, view execution logs, template selection |
| **State** | Production-ready |

---

### 10. Company List — `/(dashboard)/companies`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/companies/page.tsx` |
| **Auth required** | Yes |
| **Components** | `CompanyList`, `CompanyFilters`, `CompanyCreateModal` |
| **Data displayed** | Table of companies — name (AR/EN), CR number, city, region, status, employee count |
| **API calls** | `useCompanySearch()` → `GET /api/v1/companies` (paginated, filterable) |
| **Interactive elements** | Search bar (AR/EN), city filter, region filter, status filter, create company modal, row click → `/companies/{id}` |
| **Pagination** | Server-side, page_size configurable |
| **State** | Production-ready |

---

### 11. Company Detail — `/(dashboard)/companies/[id]`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/companies/[id]/page.tsx` |
| **Workspace** | `components/company-workspace.tsx` → `CompanyWorkspace` |
| **Auth required** | Yes |
| **Components** | `CompanyWorkspace` — 7-tab layout with 10 intelligence widgets |
| **Data displayed** | Company header (name, CR, city, status), health score ring, AI action bar, metric cards, overview/intelligence/contacts/government/documents/timeline/AI tabs |
| **API calls** | `useCompany(companyId)` → `GET /api/v1/companies/{id}`, `useCompany360(companyId)` → `GET /api/v1/companies/{id}/360` |
| **Widgets (Overview tab)** | `CompanyDNAWidget`, `AIRecommendationWidget`, `BuyingJourneyWidget`, `RelationshipGraphWidget` |
| **Widgets (Intelligence tab)** | `SignalsFeedWidget`, `SmartTimelineWidget` |
| **Widgets (Contacts tab)** | `DecisionMakersWidget`, `RelationshipGraphWidget` |
| **Widgets (Government tab)** | `GovernmentIntelligenceWidget`, `GoldenRecordWidget` |
| **Widgets (Documents tab)** | `DocumentIntelligenceWidget` |
| **Widgets (Timeline tab)** | `SmartTimelineWidget`, `TimelineWidget` |
| **Widgets (AI tab)** | `AIRecommendationWidget`, `BuyingJourneyWidget`, `CompanyDNAWidget` |
| **Interactive elements** | Tab navigation, edit/delete/add-contact modals, AI action buttons (explain/analyze/predict/summarize/recommend), health score ring |
| **State** | Production-ready |

---

### 12. Contacts — `/(dashboard)/contacts`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/contacts/page.tsx` |
| **Auth required** | Yes |
| **Components** | `ContactList`, `ContactFilters`, `ContactCreateModal`, `ContactEditModal` |
| **Data displayed** | Table of contacts — name, email, phone, company, title, status |
| **API calls** | `GET /api/v1/contacts` (paginated), `POST /api/v1/contacts`, `PUT /api/v1/contacts/{id}`, `DELETE /api/v1/contacts/{id}` |
| **Interactive elements** | Search, filter by company/status, create modal, edit modal, delete confirmation, company linking |
| **State** | Production-ready |

---

### 13. Copilot (Standalone) — `/(dashboard)/copilot`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/copilot/page.tsx` |
| **Workspace** | `components/copilot-panel.tsx` → `CopilotPanel` |
| **Auth required** | Yes |
| **Components** | `CopilotPanel` — chat interface, message history, input bar |
| **Data displayed** | AI chat messages, welcome message, typing indicator |
| **API calls** | `POST /api/v1/copilot/query` (per message) |
| **Interactive elements** | Text input, send button, clear chat, collapse/expand, fullscreen toggle, escape to close |
| **Modes** | collapsed, expanded, fullscreen |
| **Layout** | Floating panel (420px wide, 560px tall) or embedded in page |
| **State** | Production-ready |

---

### 14. Customer Success — `/(dashboard)/customer-success`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/customer-success/page.tsx` |
| **Workspace** | `features/customer-success/workspace/.../CustomerSuccessWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `TelemetryOverview`, `TenantsView` |
| **Data displayed** | Tenant health scores, churn risk indicators, NPS, engagement metrics |
| **API calls** | `GET /api/v1/customer-success/telemetry`, `GET /api/v1/customer-success/tenants` |
| **Interactive elements** | Tenant search, health score drill-down, date range filter |
| **State** | Production-ready |

---

### 15. Decision Center — `/(dashboard)/decisions`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/decisions/page.tsx` |
| **Auth required** | Yes |
| **Components** | `DecisionList`, `DecisionCard`, `DecisionActions` |
| **Data displayed** | Pending decisions (AI-generated), decision history, rationale, confidence score |
| **API calls** | `GET /api/v1/decision/history` |
| **Interactive elements** | Accept button, dismiss button, view rationale, filter by type/status |
| **State** | Production-ready |

---

### 16. My 360° — `/(dashboard)/employees/me`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/employees/me/page.tsx` |
| **Workspace** | Inline — wraps `Employee360View` with `useMy360()` |
| **Auth required** | Yes |
| **Components** | `Employee360View` (5-tab layout) |
| **Data displayed** | Profile header (avatar, name, role, email, phone), KPI cards (revenue, pipeline, win rate, productivity), activity intelligence, email intelligence, calendar intelligence, sales performance, portfolio, AI coach, suggested outreach, timeline |
| **API calls** | `useMy360()` → `GET /api/v1/employees/me/360` |
| **Tabs** | overview, activity, pipeline, AI coach, timeline |
| **State** | Production-ready |

---

### 17. Employee 360° — `/(dashboard)/employees/[id]`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/employees/[id]/page.tsx` |
| **Workspace** | Inline — wraps `Employee360View` with `useEmployee360(id)` |
| **Auth required** | Yes |
| **Components** | `Employee360View` (same as My 360° but for any employee) |
| **Data displayed** | Same as My 360° — profile, KPIs, activity/email/calendar intelligence, performance, portfolio, AI coach, timeline |
| **API calls** | `useEmployee360(id)` → `GET /api/v1/employees/{id}/360` |
| **Tabs** | overview, activity, pipeline, AI coach, timeline |
| **State** | Production-ready |

---

### 18. Revenue Forecast — `/(dashboard)/forecast`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/forecast/page.tsx` |
| **Auth required** | Yes |
| **Components** | `ForecastDashboard`, `ScenarioCard`, `ForecastChart` |
| **Data displayed** | Revenue forecast scenarios (best/expected/worst), projected values, confidence intervals |
| **API calls** | `GET /api/v1/forecast` |
| **Interactive elements** | Scenario selection, date range filter, export |
| **State** | Production-ready |

---

### 19. Knowledge Graph — `/(dashboard)/graph`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/graph/page.tsx` |
| **Auth required** | Yes |
| **Components** | `GraphCanvas` — SVG-based node/edge visualization |
| **Data displayed** | Interactive graph of companies, contacts, relationships as nodes/edges |
| **API calls** | `GET /api/v1/graph/nodes`, `GET /api/v1/graph/edges` |
| **Interactive elements** | Drag nodes, zoom/pan, click node for detail, search/filter by entity type, fullscreen toggle |
| **Rendering** | SVG canvas with D3-like layout algorithm (force-directed) |
| **State** | Production-ready |

---

### 20. Meetings — `/(dashboard)/meetings`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/meetings/page.tsx` |
| **Auth required** | Yes |
| **Components** | `MeetingBriefList`, `MeetingBriefCard` |
| **Data displayed** | Upcoming meeting briefs — attendee list, company context, talking points, recent activity, AI suggestions |
| **API calls** | `GET /api/v1/meetings/brief` |
| **Interactive elements** | Select meeting to view full brief, refresh, link to company detail |
| **State** | Production-ready |

---

### 21. System Monitoring — `/(dashboard)/monitoring`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/monitoring/page.tsx` |
| **Auth required** | Yes (admin) |
| **Components** | `MetricsPanel`, `SystemHealthCard`, `AlertList` |
| **Data displayed** | Real-time system metrics — CPU, memory, response times, error rates, active connections |
| **API calls** | `GET /api/v1/monitoring/metrics` (auto-refresh every 5s) |
| **Interactive elements** | Auto-refresh toggle, manual refresh, time range selector, alert acknowledgment |
| **State** | Production-ready |

---

### 22. Pipeline Kanban — `/(dashboard)/opportunities`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/opportunities/page.tsx` |
| **Workspace** | `components/pipeline-kanban.tsx` → `PipelineKanban` |
| **Auth required** | Yes |
| **Components** | `PipelineKanban`, `PipelineColumn`, `OpportunityCard`, `CreateOpportunityModal`, won/lost confirmation dialogs |
| **Data displayed** | 6-column kanban (prospecting, qualification, proposal, negotiation, closed won, closed lost), opportunity cards with value/company/status |
| **API calls** | `useOpportunities()` → `GET /api/v1/opportunities`, `useAdvanceOpportunity()`, `useCloseWon()`, `useCloseLost()`, `useCreateOpportunity()`, `useCompanySearch()` |
| **Interactive elements** | Drag-and-drop between columns, create opportunity modal (company search + name + value), won confirmation (enter amount), lost confirmation (enter reason) |
| **Stages** | prospecting → qualification → proposal → negotiation → closed_won / closed_lost |
| **State** | Production-ready |

---

### 23. Opportunity Detail — `/(dashboard)/opportunities/[id]`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/opportunities/[id]/page.tsx` |
| **Workspace** | `DecisionProvider` wrapper + `OpportunityWorkspace` |
| **Auth required** | Yes |
| **Components** | `OpportunityWorkspace`, `DecisionMakersWidget`, `NextBestActionWidget` |
| **Data displayed** | Opportunity details (name, value, stage, company), decision history, NBA (next best action) suggestions |
| **API calls** | `GET /api/v1/opportunities/{id}`, `GET /api/v1/decisions?opportunity_id={id}` |
| **Interactive elements** | Edit opportunity, advance stage, view decision history, accept/dismiss NBA |
| **State** | Production-ready |

---

### 24. Pipeline Workspace — `/(dashboard)/pipeline`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/pipeline/page.tsx` |
| **Workspace** | `DecisionProvider` wrapper + `features/revenue-execution/workspace/pipeline/PipelineWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `PipelineWorkspace` — kanban/list views, forecast summary |
| **Data displayed** | Pipeline overview with kanban and list toggle, forecast summary, stage-level metrics |
| **API calls** | `GET /api/v1/pipeline`, `GET /api/v1/forecast/summary` |
| **Interactive elements** | View toggle (kanban/list), drag-and-drop, forecast drill-down |
| **State** | Production-ready |

---

### 25. RAG — `/(dashboard)/rag`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/rag/page.tsx` |
| **Workspace** | `features/rag/workspace/rag/RagWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `RagChatWidget`, `RagDocumentManager` |
| **Data displayed** | Split view — left: AI chat over documents; right: document list with upload/delete |
| **API calls** | `POST /api/v1/rag/query` (chat), `GET /api/v1/rag/documents`, `POST /api/v1/rag/documents`, `DELETE /api/v1/rag/documents/{id}` |
| **Interactive elements** | Chat input, document upload (drag-and-drop), document delete, source citation links |
| **State** | Production-ready |

---

### 26. Revenue Workspace — `/(dashboard)/revenue`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/revenue/page.tsx` |
| **Workspace** | `DecisionProvider` wrapper + `features/revenue-execution/workspace/revenue/RevenueWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `RevenueWorkspace` — overview, pipeline, opportunity sub-views |
| **Data displayed** | Revenue summary, pipeline breakdown, opportunity list, trend charts |
| **API calls** | `GET /api/v1/revenue/overview`, `GET /api/v1/revenue/pipeline`, `GET /api/v1/revenue/opportunities` |
| **Tabs/Views** | overview, pipeline, opportunity |
| **Interactive elements** | Sub-view switching, filter by date/stage, export |
| **State** | Production-ready |

---

### 27. Rules — `/(dashboard)/rules`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/rules/page.tsx` |
| **Workspace** | `features/rules/RulesWorkspace.tsx` |
| **Auth required** | Yes |
| **Components** | `RuleList`, `RuleEditor`, `RuleCreateEditModal` |
| **Data displayed** | Business rules by domain — trigger, condition, action, status |
| **API calls** | `GET /api/v1/rules`, `POST /api/v1/rules`, `PUT /api/v1/rules/{id}`, `DELETE /api/v1/rules/{id}` |
| **Tabs** | Domain tabs (all domains) |
| **Interactive elements** | Create rule modal, edit rule modal, toggle rule status, delete rule, domain filter |
| **State** | Production-ready |

---

### 28. Search — `/(dashboard)/search`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/search/page.tsx` |
| **Auth required** | Yes |
| **Components** | `SearchBar`, `SearchResults`, `SearchFacets` |
| **Data displayed** | Search results across companies, contacts, opportunities — faceted filters |
| **API calls** | `POST /api/v1/search` (full-text, semantic, or hybrid mode) |
| **Interactive elements** | Search input, mode toggle (full-text/semantic/hybrid), facet filters (type, city, status, date range), result click → entity detail |
| **Search modes** | fulltext (PostgreSQL), semantic (pgvector), hybrid (RRF fusion) |
| **State** | Production-ready |

---

### 29. Settings — `/(dashboard)/settings`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/settings/page.tsx` |
| **Auth required** | Yes |
| **Components** | `SettingsTabs` — 5 tab panels |
| **Data displayed** | Profile info, security settings, notification preferences, API keys, data management |
| **API calls** | `GET /api/v1/settings/profile`, `PUT /api/v1/settings/profile`, `GET /api/v1/settings/api-keys`, `POST /api/v1/settings/api-keys` |
| **Tabs** | profile, security, notifications, api keys, data |
| **Interactive elements** | Edit profile, change password, toggle notifications, create/revoke API keys, export/delete data |
| **State** | Production-ready |

---

### 30. Signals Marketplace — `/(dashboard)/signals`

| Field | Value |
|-------|-------|
| **File** | `src/app/(dashboard)/signals/page.tsx` |
| **Auth required** | Yes |
| **Components** | `SignalFeed`, `SignalSubscriptions`, `SignalCategories` |
| **Data displayed** | Signal feed (news, filings, social), signal categories, subscribed signals |
| **API calls** | `GET /api/v1/signals/feed`, `GET /api/v1/signals/subscriptions` |
| **Interactive elements** | Browse signals, subscribe/unsubscribe, filter by category, click signal → source detail |
| **State** | Production-ready |

---

## Cross-Reference: Workspace Components

| Workspace Component | File | Used By |
|---------------------|------|---------|
| `DashboardPage` | `features/dashboard/_layout/dashboard-page.tsx` | Dashboard |
| `AdminWorkspace` | `features/admin/AdminWorkspace.tsx` | Admin |
| `AnalyticsWorkspace` | `features/analytics/AnalyticsWorkspace.tsx` | Analytics |
| `AutomationWorkspace` | `features/automation/workspace/automation/AutomationWorkspace.tsx` | Automation |
| `CustomerSuccessWorkspace` | `features/customer-success/workspace/.../CustomerSuccessWorkspace.tsx` | Customer Success |
| `RevenueWorkspace` | `features/revenue-execution/workspace/revenue/RevenueWorkspace.tsx` | Revenue |
| `PipelineWorkspace` | `features/revenue-execution/workspace/pipeline/PipelineWorkspace.tsx` | Pipeline |
| `OpportunityWorkspace` | `features/revenue-execution/workspace/OpportunityWorkspace.tsx` | Opportunity Detail |
| `RulesWorkspace` | `features/rules/RulesWorkspace.tsx` | Rules |
| `RagWorkspace` | `features/rag/workspace/rag/RagWorkspace.tsx` | RAG |
| `CompanyWorkspace` | `components/company-workspace.tsx` | Company Detail |
| `PipelineKanban` | `components/pipeline-kanban.tsx` | Opportunities |
| `Employee360View` | `components/employee-360-view.tsx` | My 360°, Employee 360° |
| `CopilotPanel` | `components/copilot-panel.tsx` | Copilot (standalone + embeddable) |

---

## Cross-Reference: Company Intelligence Widgets

| Widget | File | Tab |
|--------|------|-----|
| `CompanyDNAWidget` | `features/company-intelligence/widgets/company-dna/CompanyDNAContainer.tsx` | Overview, AI |
| `AIRecommendationWidget` | `features/company-intelligence/widgets/ai-recommendation/AIRecommendationContainer.tsx` | Overview, AI |
| `BuyingJourneyWidget` | `features/company-intelligence/widgets/buying-journey/BuyingJourneyContainer.tsx` | Overview, AI |
| `RelationshipGraphWidget` | `features/company-intelligence/widgets/relationship-graph/RelationshipGraphContainer.tsx` | Overview, Contacts |
| `SignalsFeedWidget` | `features/company-intelligence/widgets/signals-feed/SignalsFeedContainer.tsx` | Intelligence |
| `SmartTimelineWidget` | `features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer.tsx` | Intelligence, Timeline |
| `DecisionMakersWidget` | `features/company-intelligence/widgets/decision-makers/DecisionMakersContainer.tsx` | Contacts |
| `GovernmentIntelligenceWidget` | `features/company-intelligence/widgets/government-intelligence/GovernmentIntelligenceContainer.tsx` | Government |
| `GoldenRecordWidget` | `features/company-intelligence/widgets/golden-record/GoldenRecordContainer.tsx` | Government |
| `DocumentIntelligenceWidget` | `features/company-intelligence/widgets/document-intelligence/DocumentIntelligenceContainer.tsx` | Documents |

---

## Cross-Reference: API Endpoints Hit by Screens

| Endpoint | Method | Screen |
|----------|--------|--------|
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/auth/register` | POST | Register |
| `/api/v1/dashboard/metrics` | GET | Dashboard |
| `/api/v1/activities` | GET | Activities |
| `/api/v1/admin/tenants` | GET | Admin |
| `/api/v1/admin/plans` | GET | Admin |
| `/api/v1/admin/users` | GET | Admin |
| `/api/v1/admin/flags` | GET | Admin |
| `/api/v1/admin/jobs` | GET | Admin |
| `/api/v1/admin/ai-costs` | GET | Admin |
| `/api/v1/admin/health` | GET | Admin |
| `/api/v1/ai/prompts` | GET/POST | AI Prompt Manager |
| `/api/v1/analytics/executive` | GET | Analytics |
| `/api/v1/automation/workflows` | GET | Automation |
| `/api/v1/automation/templates` | GET | Automation |
| `/api/v1/automation/history` | GET | Automation |
| `/api/v1/companies` | GET | Companies |
| `/api/v1/companies/{id}` | GET | Company Detail |
| `/api/v1/companies/{id}/360` | GET | Company Detail |
| `/api/v1/contacts` | GET/POST/PUT/DELETE | Contacts |
| `/api/v1/copilot/query` | POST | Copilot |
| `/api/v1/customer-success/telemetry` | GET | Customer Success |
| `/api/v1/customer-success/tenants` | GET | Customer Success |
| `/api/v1/decision/history` | GET | Decisions |
| `/api/v1/employees/me/360` | GET | My 360° |
| `/api/v1/employees/{id}/360` | GET | Employee 360° |
| `/api/v1/forecast` | GET | Forecast |
| `/api/v1/graph/nodes` | GET | Knowledge Graph |
| `/api/v1/graph/edges` | GET | Knowledge Graph |
| `/api/v1/meetings/brief` | GET | Meetings |
| `/api/v1/monitoring/metrics` | GET | Monitoring |
| `/api/v1/opportunities` | GET | Pipeline Kanban |
| `/api/v1/opportunities/{id}` | GET | Opportunity Detail |
| `/api/v1/pipeline` | GET | Pipeline Workspace |
| `/api/v1/rag/query` | POST | RAG |
| `/api/v1/rag/documents` | GET/POST/DELETE | RAG |
| `/api/v1/revenue/overview` | GET | Revenue |
| `/api/v1/revenue/pipeline` | GET | Revenue |
| `/api/v1/revenue/opportunities` | GET | Revenue |
| `/api/v1/rules` | GET/POST/PUT/DELETE | Rules |
| `/api/v1/search` | POST | Search |
| `/api/v1/settings/profile` | GET/PUT | Settings |
| `/api/v1/settings/api-keys` | GET/POST | Settings |
| `/api/v1/signals/feed` | GET | Signals |
| `/api/v1/signals/subscriptions` | GET | Signals |

---

## Screenshots

No screenshots exist in the repository. Screenshots should be captured for each screen as part of the visual audit.
