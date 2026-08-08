# SalesOS Canonical Architecture

> **Single Source of Truth** — Architecture, Capabilities, Objects, and Traceability
>
> **Version:** 1.0.0  
> **Last updated:** 2026-07-30  
> **Authority:** This document supersedes conflicting claims in PRODUCT_BIBLE.md, MASTER_BLUEPRINT.md, FEATURE_STATUS.md, and prior inventory reports.  
> **Validation basis:** Executable code analysis (backend models, API routers, frontend pages, tests) as of commit `6f75e8d`.

---

## 1. Product Vision

**SalesOS** — Enterprise Company Intelligence Platform for the Saudi/GCC market.  
**Tagline:** Bloomberg Terminal for Saudi companies, with AI intelligence at CRM pricing.  
**Parent platform:** Private Governed Institutional Intelligence Platform.

### Vision Horizons

| Horizon | Scope | Status |
|---------|-------|--------|
| **Today** | Company Intelligence Workspace — understand any Saudi company in minutes | Operational (v5.1.0-rc1) |
| **6 Months** | Revenue Intelligence — predict opportunities and risks before they happen | Partial (modules exist, not integrated) |
| **12 Months** | Autonomous Sales Agent — AI sales rep that negotiates and closes deals | Not started |

### Core Principles

1. **AI assists. Humans decide. Evidence governs.**
2. Arabic-first, English-second (RTL layout, Arabic NLP)
3. Multi-tenant by design (every table has `tenant_id`)
4. Modular monolith → extract to microservices when needed
5. Repository pattern: InMemory → PostgreSQL (many still in-memory)

---

## 2. Business Domains

| ID | Domain | Owner | Description |
|----|--------|-------|-------------|
| **DOM-001** | Identity & Access | Platform | Tenant, User, Auth, SSO, RBAC, API Keys |
| **DOM-002** | Company Intelligence | Commercial | Company 360, Golden Record, Entity Resolution, Branches, Licenses |
| **DOM-003** | Contact Management | Commercial | Contact CRUD, Bulk Upsert, Company Linking |
| **DOM-004** | Employee Intelligence | People | Employee 360, Performance, Signals, AI Coach |
| **DOM-005** | Commercial | Revenue | Pipeline, Opportunity, Quote, Proposal, Contract, Activity |
| **DOM-006** | Revenue Intelligence | Revenue | Forecast, Quota, Territory, Revenue Analytics |
| **DOM-007** | Communication Hub | Integration | Gmail Sync, Calendar Sync, Google OAuth |
| **DOM-008** | Meeting & Email Intelligence | Revenue | Meeting Intelligence, Email Intelligence |
| **DOM-009** | Decision Intelligence | AI | Decision Engine, Recommendations, Policies, Scoring |
| **DOM-010** | Search & Discovery | Platform | Universal Search, Semantic Search, Hybrid RRF |
| **DOM-011** | Knowledge & RAG | AI | RAG Pipeline, Document Management, Knowledge Base |
| **DOM-012** | AI Platform | AI | Prompt Registry, AI Providers, Guardrails, Memory |
| **DOM-013** | Analytics & Reporting | Platform | Reports, Cubes, KPIs, Dashboards, Scheduling |
| **DOM-014** | Automation & Workflows | Platform | Workflow Engine, Rules Engine, Webhooks, Jobs |
| **DOM-015** | Signals & Marketplace | Intelligence | Signal Marketplace, Plugin System |
| **DOM-016** | Timeline & Activity | Platform | Event Timeline, Audit Trail, Activity Stream |
| **DOM-017** | Data Fabric | Platform | Data Ingestion, Scrapers, Entity Resolution |
| **DOM-018** | Governance & Admin | Platform | Admin Panel, Monitoring, Telemetry, Feature Flags |
| **DOM-019** | Customer Success | Revenue | Health Scores, Adoption, Engagement |

---

## 3. Canonical Object Model

### 3.1 Core Business Objects

| # | Object | Table | Primary Domain | Key Fields | Status |
|---|--------|-------|----------------|------------|--------|
| OBJ-001 | **Tenant** | `tenants` | Identity | id, name, slug, plan, settings | ✅ |
| OBJ-002 | **User** | `users` | Identity | id, tenant_id, email, password_hash, role | ✅ |
| OBJ-003 | **Company** | `companies` | Company Intelligence | id, tenant_id, name_ar, cr_number, status, city | ✅ |
| OBJ-004 | **Contact** | `contacts` | Contact Management | id, tenant_id, company_id, name, email, phone | ✅ |
| OBJ-005 | **Branch** | `branches` | Company Intelligence | id, company_id, name_ar, branch_number, city | ✅ |
| OBJ-006 | **License** | `licenses` | Company Intelligence | id, company_id, license_number, license_type, status | ✅ |
| OBJ-007 | **Opportunity** | `commercial_opportunities` | Commercial | id, tenant_id, company_id, name, value, stage, probability | ✅ |
| OBJ-008 | **Task** | `tasks` | Revenue Execution | id, tenant_id, company_id, title, priority, completed | ✅ |
| OBJ-009 | **Activity** | `commercial_activities` | Commercial | id, session_id, activity_type, outcome | ✅ |
| OBJ-010 | **ActivitySession** | `commercial_activity_sessions` | Commercial | id, tenant_id, title, target_type, status | ✅ |
| OBJ-011 | **Meeting** | `meetings` | Meeting Intelligence | id, tenant_id, opportunity_id, meeting_date | ✅ |
| OBJ-012 | **Email** | `emails` | Email Intelligence | id, tenant_id, opportunity_id, subject, direction | ✅ |
| OBJ-013 | **Quote** | `commercial_quotes` | Commercial | id, tenant_id, opportunity_id, total_value, status | ✅ |
| OBJ-014 | **Proposal** | `commercial_proposals` | Commercial | id, tenant_id, opportunity_id, status | ✅ |
| OBJ-015 | **Contract** | `commercial_contracts` | Commercial | id, tenant_id, opportunity_id, status, effective_date | ✅ |
| OBJ-016 | **PipelineDefinition** | `commercial_pipeline_definitions` | Commercial | id, tenant_id, name, stages | ✅ |
| OBJ-017 | **ForecastSnapshot** | `commercial_forecast_snapshots` | Revenue | id, tenant_id, horizon_months, lines | ✅ |
| OBJ-018 | **AnalyticsSnapshot** | `commercial_analytics_snapshots` | Revenue | id, tenant_id, period_start, kpis | ✅ |

### 3.2 Intelligence Objects

| # | Object | Table | Domain | Status |
|---|--------|-------|--------|--------|
| OBJ-101 | **Decision** | `decision_center_decisions` | Decision Intelligence | ✅ |
| OBJ-102 | **DecisionTemplate** | `decision_center_templates` | Decision Intelligence | ✅ |
| OBJ-103 | **Recommendation** | `commercial_recommendations` | Decision Intelligence | ✅ |
| OBJ-104 | **Policy** | `commercial_policies` | Decision Intelligence | ✅ |
| OBJ-105 | **DecisionContext** | `commercial_decision_contexts` | Decision Intelligence | ✅ |
| OBJ-106 | **ScoreCard** | `score_cards` | Scoring | ✅ |
| OBJ-107 | **EmployeeSignal** | `employee_signals` | Employee Intelligence | ✅ |
| OBJ-108 | **EmployeeScore** | `employee_scores` | Employee Intelligence | ✅ |
| OBJ-109 | **EmployeeCalendarEvent** | `employee_calendar_events` | Employee Intelligence | ✅ |
| OBJ-110 | **EmployeeEmailEvent** | `employee_email_events` | Employee Intelligence | ✅ |
| OBJ-111 | **TimelineEvent** | `timeline_events` | Timeline | ✅ |

### 3.3 Infrastructure Objects

| # | Object | Table | Domain | Status |
|---|--------|-------|--------|--------|
| OBJ-201 | **Source** | `sources` | Data Fabric | ✅ |
| OBJ-202 | **WebhookSubscription** | `webhook_subscriptions` | Automation | ✅ |
| OBJ-203 | **WebhookDelivery** | `webhook_deliveries` | Automation | ✅ |
| OBJ-204 | **Workflow** | `workflows` | Automation | ✅ |
| OBJ-205 | **WorkflowExecution** | `workflow_executions` | Automation | ✅ |
| OBJ-206 | **ScheduledJob** | `scheduled_jobs` | Automation | ✅ |
| OBJ-207 | **JobExecution** | `job_executions` | Automation | ✅ |
| OBJ-208 | **Notification** | `notifications` | Timeline | ✅ |
| OBJ-209 | **TelemetryEvent** | `telemetry_events` | Governance | ✅ |
| OBJ-210 | **AuditLog** | `audit_logs` | Governance | ✅ |
| OBJ-211 | **ApiKey** | `api_keys` | Identity | ✅ |
| OBJ-212 | **SSOConnection** | `sso_connections` | Identity | ✅ |
| OBJ-213 | **Plugin** | `plugins` | Marketplace | ✅ |
| OBJ-214 | **Report** | `reports` | Analytics | ✅ |
| OBJ-215 | **ReportExecution** | `report_executions` | Analytics | ✅ |
| OBJ-216 | **FeatureDefinition** | `feature_definitions` | Feature Store | ✅ |
| OBJ-217 | **FeatureValue** | `feature_values` | Feature Store | ✅ |
| OBJ-218 | **GoogleAccount** | `google_accounts` | Communication Hub | ✅ |
| OBJ-219 | **CalendarEvent** | `calendar_events` | Communication Hub | ✅ |
| OBJ-220 | **EmailEvent** | `email_events` | Communication Hub | ✅ |
| OBJ-221 | **GoldenRecord** | `golden_records` | Entity Resolution | ✅ |
| OBJ-222 | **EntityConflict** | `entity_conflicts` | Entity Resolution | ✅ |

### 3.4 Admin Objects

| # | Object | Table | Domain | Status |
|---|--------|-------|--------|--------|
| OBJ-301 | **Plan** | `plans` | Governance | ✅ |
| OBJ-302 | **License** | `licenses` (admin) | Governance | ✅ |
| OBJ-303 | **Invoice** | `invoices` | Governance | ✅ |
| OBJ-304 | **FeatureFlag** | `feature_flags` | Governance | ✅ |
| OBJ-305 | **Role** | `roles` | Identity | ✅ |
| OBJ-306 | **Permission** | `permissions` | Identity | ✅ |
| OBJ-307 | **AICostRecord** | `ai_cost_records` | Governance | ✅ |
| OBJ-308 | **HealthSnapshot** | `health_snapshots` | Governance | ✅ |
| OBJ-309 | **DeviceSession** | `device_sessions` | Identity | ✅ |
| OBJ-310 | **RefreshTokenFamily** | `refresh_token_families` | Identity | ✅ |
| OBJ-311 | **TokenBlacklist** | `token_blacklist` | Identity | ✅ |
| OBJ-312 | **PasswordResetToken** | `password_reset_tokens` | Identity | ✅ |

### 3.5 Object Relationships

```
Tenant (1) ──→ (N) User
Tenant (1) ──→ (N) Company
Tenant (1) ──→ (N) Opportunity
Company (1) ──→ (N) Branch
Company (1) ──→ (N) License
Company (1) ──→ (N) Contact
Company (1) ──→ (N) Opportunity
Company (1) ──→ (N) Task
Opportunity (1) ──→ (N) Meeting
Opportunity (1) ──→ (N) Email
Opportunity (1) ──→ (N) Quote
Opportunity (1) ──→ (N) Proposal
Opportunity (1) ──→ (N) Contract
Opportunity (1) ──→ (N) StageEntry
User (1) ──→ (N) DeviceSession
User (1) ──→ (N) SSOConnection
User (1) ──→ (N) ApiKey
```

---

## 4. Capability Registry

### Naming Convention
- `CAP-{NNN}` — Unique capability ID (immutable)
- Prefix: `P0`= must-have, `P1`=should-have, `P2`=nice-to-have
- Status: `✅` = code exists and testable, `🟡` = partial/stubbed, `❌` = not started

### 4.1 P0 — Core Platform

| ID | Capability | Domain | Pages | APIs | Services | DB Tables | Widgets | Tests | Status |
|----|-----------|--------|-------|------|----------|----------|---------|-------|--------|
| CAP-001 | **Tenant Management** | Identity | /admin/tenants | 8 | 4 | tenants | TenantList | 12 | ✅ |
| CAP-002 | **User Authentication** | Identity | /login, /register | 18 | 6 | users, device_sessions, refresh_token_families, token_blacklist, password_reset_tokens | — | 45 | ✅ |
| CAP-003 | **Role-Based Access Control** | Identity | /admin | 5 | 3 | roles, permissions, role_permissions | RoleManager | 8 | ✅ |
| CAP-004 | **Company 360** | Company Intelligence | /companies, /companies/[id] | 17 | 5 | companies, branches, licenses, contacts | 11 widgets (Company360, AI Rec, Buying Journey, Company DNA, Decision Makers, Document Intel, Golden Record, Gov Intel, Relationship Graph, Signals Feed, Smart Timeline) | 89 | ✅ |
| CAP-005 | **Universal Search** | Search | /search, /search/analytics | 6 | 4 | — | SearchInput, SearchResult, CommandBar, QuickOverlay | 78 | ✅ |
| CAP-006 | **Contact Management** | Contact Management | /contacts | 7 | 3 | contacts | — | 15 | ✅ |
| CAP-007 | **Dashboard** | Platform | /dashboard | 2 | 2 | — | 13 widgets (Pipeline, Company Health, Company Engagement, Email Intel, Calendar Intel, Decision Queue, Intelligence Feed, Market Pulse, Mission Center, Followup Center, Recent Activity, AI Brief) | 10 | ✅ |

### 4.2 P1 — Commercial & Intelligence

| ID | Capability | Domain | Pages | APIs | Services | DB Tables | Widgets | Tests | Status |
|----|-----------|--------|-------|------|----------|----------|---------|-------|--------|
| CAP-008 | **Pipeline Management** | Commercial | /pipeline, /pipeline/analytics | 6 | 4 | commercial_opportunities, commercial_stage_entries, commercial_pipeline_definitions | PipelineKanban, PipelineIntel | 45 | ✅ |
| CAP-009 | **Opportunity Management** | Commercial | /opportunities, /opportunities/[id] | 7 | 3 | commercial_opportunities | OpportunityDetail, OpportunityList | 52 | ✅ |
| CAP-010 | **Quote Management** | Commercial | — | 5 | 2 | commercial_quotes, commercial_quote_lines | — | 12 | ✅ |
| CAP-011 | **Proposal Management** | Commercial | — | 3 | 2 | commercial_proposals | — | 8 | ✅ |
| CAP-012 | **Contract Management** | Commercial | — | 2 | 2 | commercial_contracts | — | 12 | ✅ |
| CAP-013 | **Activity Management** | Commercial | /activities | 4 | 3 | commercial_activities, commercial_activity_sessions | — | 18 | ✅ |
| CAP-014 | **Employee 360** | Employee Intelligence | /employees, /employees/[id], /employees/me | 21 | 5 | employee_signals, employee_scores, employee_calendar_events, employee_email_events | 7 widgets (Profile, Portfolio, AI Coach, KPI, Activity, Calendar, Email) | 68 | ✅ |
| CAP-015 | **Forecast** | Revenue | /forecast | 8 | 4 | commercial_forecast_snapshots | ForecastIntel | 24 | ✅ |
| CAP-016 | **Quota Management** | Revenue | /revenue/quotas | 6 | 2 | — | — | 8 | ✅ |
| CAP-017 | **Territory Management** | Revenue | /revenue/territories | 9 | 3 | — | TerritoryIntel | 10 | ✅ |
| CAP-018 | **Revenue Dashboard** | Revenue | /revenue | 1 | 1 | revenue_analytics_snapshots | RevenueHealth, ChurnIntel, ExpansionIntel | 6 | ✅ |
| CAP-019 | **Activity Intelligence** | Intelligence | — | 4 | 2 | — | — | 68 | 🟡 |
| CAP-020 | **Meeting Intelligence** | Meeting Intel | /meetings | 3 | 2 | meetings | MeetingIntel | 18 | ✅ |
| CAP-021 | **Email Intelligence** | Email Intel | — | 2 | 2 | emails | EmailIntel | 14 | ✅ |

### 4.3 P2 — AI & Knowledge

| ID | Capability | Domain | Pages | APIs | Services | DB Tables | Widgets | Tests | Status |
|----|-----------|--------|-------|------|----------|----------|---------|-------|--------|
| CAP-022 | **Decision Center** | Decision Intelligence | /decisions, /decisions/templates | 13 | 4 | decision_center_decisions, decision_center_audits, decision_center_feedback, decision_center_templates | DecisionQueue | 42 | ✅ |
| CAP-023 | **AI Prompt Registry** | AI Platform | /ai | 6 | 2 | — | — | 22 | ✅ |
| CAP-024 | **RAG Pipeline** | Knowledge | /rag | 4 | 3 | — | RagChat, RagDocuments | 18 | ✅ |
| CAP-025 | **Workflow Engine** | Automation | /automation, /automation/workflows/new | 6 | 4 | workflows, workflow_executions | WorkflowBuilder | 45 | ✅ |
| CAP-026 | **Rules Engine** | Automation | /rules | 7 | 2 | — | — | 28 | ✅ |
| CAP-027 | **Webhooks** | Automation | — | 7 | 3 | webhook_subscriptions, webhook_deliveries | — | 15 | ✅ |
| CAP-028 | **Scheduled Jobs** | Automation | — | 5 | 2 | scheduled_jobs, job_executions | JobList | 5 | ✅ |
| CAP-029 | **Knowledge Graph** | Knowledge | /graph | 3 | 2 | graph_* | KnowledgeGraphPanel | 10 | 🟡 |
| CAP-030 | **Timeline** | Timeline | — | 5 | 2 | timeline_events | SmartTimeline, ActivityTimeline | 18 | ✅ |
| CAP-031 | **Analytics & Reports** | Analytics | /analytics, /analytics/sales, /analytics/reports/builder | 23 | 5 | reports, report_executions, report_shares, scheduled_reports | — | 24 | ✅ |
| CAP-032 | **Dashboard Widgets** | Platform | /dashboard | — | — | — | 13 widgets | — | ✅ |

### 4.4 P2 — Integration & Communication

| ID | Capability | Domain | Pages | APIs | Services | DB Tables | Widgets | Tests | Status |
|----|-----------|--------|-------|------|----------|----------|---------|-------|--------|
| CAP-033 | **Google OAuth 2.0** | Communication Hub | — | 2 | 2 | google_accounts | — | 22 | ✅ |
| CAP-034 | **Gmail Sync** | Communication Hub | — | 1 | 2 | email_events | — | 18 | ✅ |
| CAP-035 | **Calendar Sync** | Communication Hub | — | 1 | 2 | calendar_events | CalendarIntel | 14 | ✅ |
| CAP-036 | **Signal Marketplace** | Marketplace | /marketplace | 5 | 3 | plugins | — | 12 | ✅ |
| CAP-037 | **Entity Resolution** | Company Intelligence | — | 5 | 3 | golden_records, entity_conflicts | GoldenRecord | 24 | 🟡 |
| CAP-038 | **Notion Sync** | Integration | — | 1 | 1 | — | — | 4 | ✅ |
| CAP-039 | **Excel Import** | Integration | — | 2 | 2 | — | — | 8 | ✅ |
| CAP-040 | **Data Fabric / Scrapers** | Data Fabric | — | 3 | 4 | sources | — | 45 | 🟡 |

### 4.5 P2 — Governance & Operations

| ID | Capability | Domain | Pages | APIs | Services | DB Tables | Widgets | Tests | Status |
|----|-----------|--------|-------|------|----------|----------|---------|-------|--------|
| CAP-041 | **Admin Panel** | Governance | /admin, /admin/tenants, /admin/flags, /admin/config, /admin/audit | 45 | 8 | plans, licenses, invoices, feature_flags, roles, job | 10 widgets | 15 | ✅ |
| CAP-042 | **Audit Log** | Governance | /admin/audit | 3 | 2 | audit_logs | AuditLog | 18 | ✅ |
| CAP-043 | **AI Cost Tracking** | Governance | /admin | 3 | 1 | ai_cost_records | AICostDashboard | 6 | ✅ |
| CAP-044 | **Monitoring** | Governance | /monitoring | 3 | 2 | health_snapshots | HealthDashboard | 8 | ✅ |
| CAP-045 | **Telemetry** | Governance | — | 6 | 2 | telemetry_events | — | 8 | ✅ |
| CAP-046 | **SSO** | Identity | — | 4 | 2 | sso_connections | — | 6 | ✅ |
| CAP-047 | **API Keys** | Identity | /settings | 3 | 2 | api_keys | — | 8 | ✅ |
| CAP-048 | **Cache Management** | Platform | — | 5 | 2 | — | — | 8 | ✅ |
| CAP-049 | **Demo Mode** | Platform | — | 3 | 2 | — | DemoBadge | 4 | ✅ |
| CAP-050 | **Next-Best-Action** | Decision Intelligence | — | 1 | 2 | — | NBAWidget | 15 | 🟡 |

### 4.6 P3 — Planned / Not Started

| ID | Capability | Domain | Status | Notes |
|----|-----------|--------|--------|-------|
| CAP-051 | **Data Fabric (full)** | Data Fabric | ❌ | Only scrapers exist |
| CAP-052 | **Feature Store (full)** | Feature Store | 🟡 | Partial implementation |
| CAP-053 | **Sales Copilot** | AI Platform | 🟡 | Gated behind feature flag |
| CAP-054 | **Customer Health Engine** | Customer Success | ❌ | Basic health scores only |
| CAP-055 | **Deal Room** | Commercial | ❌ | Not started |
| CAP-056 | **Mobile App** | Platform | ❌ | Not started |
| CAP-057 | **Revenue Brain** | AI Platform | ❌ | Not started |
| CAP-058 | **GTM Intelligence** | Intelligence | ❌ | Not started |
| CAP-059 | **Marketing Intelligence** | Intelligence | ❌ | Not started |
| CAP-060 | **Agent Runtime** | AI Platform | ❌ | Not started |
| CAP-061 | **Digital Twin** | AI Platform | ❌ | Not started |
| CAP-062 | **Company DNA** | Company Intelligence | ❌ | Not started |
| CAP-063 | **AI Memory** | AI Platform | ❌ | Not started |
| CAP-064 | **Simulation Engine** | AI Platform | ❌ | Not started |
| CAP-065 | **Prompt Studio** | AI Platform | ❌ | Not started |
| CAP-066 | **Deal Scoring (advanced)** | Scoring | 🟡 | Basic exists |

---

## 5. Domain Ownership (Capability → Domain)

| Domain | Owned Capabilities |
|--------|-------------------|
| **Identity & Access** (DOM-001) | CAP-001 Tenant, CAP-002 Auth, CAP-003 RBAC, CAP-046 SSO, CAP-047 API Keys |
| **Company Intelligence** (DOM-002) | CAP-004 Company 360, CAP-037 Entity Resolution, CAP-062 Company DNA |
| **Contact Management** (DOM-003) | CAP-006 Contacts |
| **Employee Intelligence** (DOM-004) | CAP-014 Employee 360 |
| **Commercial** (DOM-005) | CAP-008 Pipeline, CAP-009 Opportunity, CAP-010 Quote, CAP-011 Proposal, CAP-012 Contract, CAP-013 Activity, CAP-055 Deal Room |
| **Revenue Intelligence** (DOM-006) | CAP-015 Forecast, CAP-016 Quota, CAP-017 Territory, CAP-018 Revenue Dashboard |
| **Communication Hub** (DOM-007) | CAP-033 Google OAuth, CAP-034 Gmail Sync, CAP-035 Calendar Sync |
| **Meeting & Email Intel** (DOM-008) | CAP-020 Meeting Intel, CAP-021 Email Intel |
| **Decision Intelligence** (DOM-009) | CAP-022 Decision Center, CAP-050 NBA, CAP-066 Scoring |
| **Search & Discovery** (DOM-010) | CAP-005 Universal Search |
| **Knowledge & RAG** (DOM-011) | CAP-024 RAG, CAP-029 Knowledge Graph |
| **AI Platform** (DOM-012) | CAP-023 Prompt Registry, CAP-053 Copilot, CAP-057 Revenue Brain, CAP-060 Agent Runtime, CAP-061 Digital Twin, CAP-063 AI Memory, CAP-064 Simulation, CAP-065 Prompt Studio |
| **Analytics & Reporting** (DOM-013) | CAP-031 Analytics |
| **Automation & Workflows** (DOM-014) | CAP-025 Workflow, CAP-026 Rules, CAP-027 Webhooks, CAP-028 Jobs |
| **Signals & Marketplace** (DOM-015) | CAP-036 Marketplace |
| **Timeline & Activity** (DOM-016) | CAP-030 Timeline, CAP-019 Activity Intel |
| **Data Fabric** (DOM-017) | CAP-038 Notion Sync, CAP-039 Excel Import, CAP-040 Data Fabric, CAP-051 Data Fabric (full), CAP-052 Feature Store |
| **Governance & Admin** (DOM-018) | CAP-041 Admin, CAP-042 Audit, CAP-043 AI Costs, CAP-044 Monitoring, CAP-045 Telemetry, CAP-048 Cache, CAP-049 Demo |
| **Customer Success** (DOM-019) | CAP-054 Health Engine |

---

## 6. UI Registry (Pages)

### 6.1 Active Routes (`(dashboard)` route group)

| Route | Page File | Capability | Layout | Auth | CSR/SSR |
|-------|-----------|------------|--------|------|---------|
| `/` | `app/page.tsx` | Landing | Root | None | SSR |
| `/login` | `app/(auth)/login/page.tsx` | CAP-002 | Auth | None | CSR |
| `/register` | `app/(auth)/register/page.tsx` | CAP-002 | Auth | None | CSR |
| `/dashboard` | `app/(dashboard)/dashboard/page.tsx` | CAP-007 | Dashboard | JWT | CSR |
| `/companies` | `app/(dashboard)/companies/page.tsx` | CAP-004 | Dashboard | JWT | CSR |
| `/companies/[id]` | `app/(dashboard)/companies/[id]/page.tsx` | CAP-004 | Dashboard | JWT | CSR |
| `/companies/[id]/360` | `app/(dashboard)/companies/[id]/360/page.tsx` | CAP-004 | Dashboard | JWT | CSR |
| `/contacts` | `app/(dashboard)/contacts/page.tsx` | CAP-006 | Dashboard | JWT | CSR |
| `/opportunities` | `app/(dashboard)/opportunities/page.tsx` | CAP-009 | Dashboard | JWT | CSR |
| `/opportunities/[id]` | `app/(dashboard)/opportunities/[id]/page.tsx` | CAP-009 | Dashboard | JWT | CSR |
| `/employees` | `app/(dashboard)/employees/page.tsx` | CAP-014 | Dashboard | JWT | CSR |
| `/employees/[id]` | `app/(dashboard)/employees/[id]/page.tsx` | CAP-014 | Dashboard | JWT | CSR |
| `/employees/me` | `app/(dashboard)/employees/me/page.tsx` | CAP-014 | Dashboard | JWT | CSR |
| `/activities` | `app/(dashboard)/activities/page.tsx` | CAP-013 | Dashboard | JWT | CSR |
| `/revenue` | `app/(dashboard)/revenue/page.tsx` | CAP-018 | Dashboard | JWT | CSR |
| `/revenue/territories` | `app/(dashboard)/revenue/territories/page.tsx` | CAP-017 | Dashboard | JWT | CSR |
| `/revenue/quotas` | `app/(dashboard)/revenue/quotas/page.tsx` | CAP-016 | Dashboard | JWT | CSR |
| `/pipeline` | `app/(dashboard)/pipeline/page.tsx` | CAP-008 | Dashboard | JWT | CSR |
| `/pipeline/analytics` | `app/(dashboard)/pipeline/analytics/page.tsx` | CAP-008 | Dashboard | JWT | CSR |
| `/forecast` | `app/(dashboard)/forecast/page.tsx` | CAP-015 | Dashboard | JWT | CSR |
| `/search` | `app/(dashboard)/search/page.tsx` | CAP-005 | Dashboard | JWT | CSR |
| `/search/analytics` | `app/(dashboard)/search/analytics/page.tsx` | CAP-005 | Dashboard | JWT | CSR |
| `/decisions` | `app/(dashboard)/decisions/page.tsx` | CAP-022 | Dashboard | JWT | CSR |
| `/decisions/templates` | `app/(dashboard)/decisions/templates/page.tsx` | CAP-022 | Dashboard | JWT | CSR |
| `/meetings` | `app/(dashboard)/meetings/page.tsx` | CAP-020 | Dashboard | JWT | CSR |
| `/graph` | `app/(dashboard)/graph/page.tsx` | CAP-029 | Dashboard | JWT | CSR |
| `/automation` | `app/(dashboard)/automation/page.tsx` | CAP-025 | Dashboard | JWT | CSR |
| `/automation/workflows/new` | `app/(dashboard)/automation/workflows/new/page.tsx` | CAP-025 | Dashboard | JWT | CSR |
| `/analytics` | `app/(dashboard)/analytics/page.tsx` | CAP-031 | Dashboard | JWT | CSR |
| `/analytics/sales` | `app/(dashboard)/analytics/sales/page.tsx` | CAP-031 | Dashboard | JWT | CSR |
| `/analytics/reports/builder` | `app/(dashboard)/analytics/reports/builder/page.tsx` | CAP-031 | Dashboard | JWT | CSR |
| `/signals` | `app/(dashboard)/signals/page.tsx` | CAP-036 | Dashboard | JWT | CSR |
| `/rules` | `app/(dashboard)/rules/page.tsx` | CAP-026 | Dashboard | JWT | CSR |
| `/monitoring` | `app/(dashboard)/monitoring/page.tsx` | CAP-044 | Dashboard | JWT | CSR |
| `/knowledge` | `app/(dashboard)/knowledge/page.tsx` | CAP-024 | Dashboard | JWT | CSR |
| `/ai` | `app/(dashboard)/ai/page.tsx` | CAP-023 | Dashboard | JWT | CSR |
| `/copilot` | `app/(dashboard)/copilot/page.tsx` | CAP-053 | Dashboard | JWT | CSR |
| `/rag` | `app/(dashboard)/rag/page.tsx` | CAP-024 | Dashboard | JWT | SSR |
| `/customer-success` | `app/(dashboard)/customer-success/page.tsx` | CAP-054 | Dashboard | JWT | CSR |
| `/settings` | `app/(dashboard)/settings/page.tsx` | CAP-002 | Dashboard | JWT | CSR |
| `/admin` | `app/(dashboard)/admin/page.tsx` | CAP-041 | Dashboard | Admin | CSR |
| `/marketplace` | `app/(dashboard)/marketplace/page.tsx` | CAP-036 | Dashboard | JWT | CSR |

### 6.2 v3 Preview Routes

| Route | Purpose | Status |
|-------|---------|--------|
| `/v3` | Home | 🟡 Preview |
| `/v3/companies`, `/v3/companies/[id]` | Companies | 🟡 Preview |
| `/v3/crm`, `/v3/crm/[id]` | Opportunities | 🟡 Preview |
| `/v3/contacts`, `/v3/contacts/[id]` | Contacts | 🟡 Preview |
| `/v3/people`, `/v3/people/[id]` | People/Employee | 🟡 Preview |
| `/v3/activities` | Activities | 🟡 Preview |
| `/v3/tasks`, `/v3/tasks/[id]` | Tasks | 🟡 Preview |
| `/v3/analytics` | Analytics | 🟡 Preview |
| `/v3/settings` | Settings | 🟡 Preview |
| `/v3/admin` | Admin | 🟡 Preview |
| `/v3/cs` | Customer Success | 🟡 Preview |

---

## 7. API Registry

### 7.1 API Surface Summary

| Group | Prefix | Endpoints | Capabilities |
|-------|--------|-----------|-------------|
| Identity | `/api/v1/identity` | 18 | CAP-001, CAP-002 |
| Companies | `/api/v1/companies` | 17 | CAP-004 |
| Contacts | `/api/v1/contacts` | 7 | CAP-006 |
| Commercial | `/api/v1/*` | 24 | CAP-008–013, CAP-015, CAP-018 |
| Opportunities | `/api/v1/opportunities` | 7 | CAP-009 |
| Meetings | `/api/v1/meetings` | 5 | CAP-020, CAP-021 |
| Revenue | `/api/v1/revenue` | 1 | CAP-018 |
| Forecast/Quota/Territory | `/api/v1/*` | 22 | CAP-015, CAP-016, CAP-017 |
| Search | `/api/v1/search` | 4 | CAP-005 |
| RAG | `/api/v1/rag` | 4 | CAP-024 |
| Analytics | `/api/v1/analytics` | 23 | CAP-031 |
| AI | `/api/v1/ai` | 6 | CAP-023 |
| Copilot | `/api/v1/copilot` | 12 | CAP-053 |
| Decisions | `/api/v1/decisions` | 13 | CAP-022 |
| Decision Platform | `/api/v1/decision` | 14 | CAP-022 |
| Workflows | `/api/v1/workflows` | 24 | CAP-025 |
| Administration | `/api/v1/admin` | 45 | CAP-041–045 |
| Employee | `/api/v1/employees` | 21 | CAP-014 |
| Entity Resolution | `/api/v1/entity-resolution` | 7 | CAP-037 |
| Timeline | `/api/v1/timeline` | 5 | CAP-030 |
| Marketplace | `/api/v1/marketplace` | 10 | CAP-036 |
| Communication Hub | `/api/v1/integrations/google` | 5 | CAP-033, CAP-034, CAP-035 |
| Notifications | `/api/v1/notifications` | 5 | — |
| Webhooks | `/api/v1/webhooks` | 7 | CAP-027 |
| Rules | `/api/v1/rules` | 7 | CAP-026 |
| Signals | `/api/v1/signals` | 5 | CAP-036 |
| SSO | `/api/v1/auth/sso` | 4 | CAP-046 |
| API Keys | `/api/v1/api-keys` | 3 | CAP-047 |
| Data Fabric | `/api/v1/data-fabric` | 4 | CAP-040 |
| Knowledge Graph | `/api/v1/graph` | 3 | CAP-029 |
| Capability Framework | `/api/v1/capabilities` | 9 | Platform |
| UX Runtime | `/api/v1/ux` | 15 | Platform |
| Activity Runtime | `/api/v1/activities` | 8 | CAP-019 |
| **Total API endpoints** | | **~300+** | |

Full endpoint details for each group are documented in `docs/api/OPENAPI.md` and the OpenAPI specification at `/openapi.json`.

### 7.2 Auth Patterns

| Auth Type | Usage |
|-----------|-------|
| **None (public)** | `/ping`, `/health/*`, `/`, `/api/v1/identity/register`, `/api/v1/identity/login`, `/api/v1/identity/refresh`, `/api/v1/identity/forgot-password`, `/api/v1/identity/reset-password`, `/api/v1/identity/.well-known/jwks.json`, `/api/v1/auth/sso/{provider}/callback`, `/api/v1/integrations/google/callback` |
| **JWT Bearer** | All authenticated endpoints (extracts user_id + tenant_id from token) |
| **Admin role** | `/api/v1/admin/*`, `/api/v1/admin/demo-mode/*`, `/api/v1/metrics/app`, `/api/v1/cache/flush` |
| **Permission-based** | `company.read`, `company.create`, `opportunity.update`, `employee.read`, etc. |
| **Feature-flagged** | Copilot endpoints gated by `feature_ai_copilot` flag |

---

## 8. Event Registry

| Event | Producer | Consumer(s) | Capability | Status |
|-------|----------|-------------|------------|--------|
| `company.created` | Company Service | Timeline, Search, Entity Resolution | CAP-004 | 🟡 |
| `company.updated` | Company Service | Timeline, Search | CAP-004 | 🟡 |
| `company.deleted` | Company Service | — | CAP-004 | 🟡 |
| `contact.created` | Contact Service | Timeline | CAP-006 | 🟡 |
| `opportunity.created` | Commercial | Timeline, Search | CAP-009 | 🟡 |
| `opportunity.stage_changed` | Commercial | Timeline, Revenue | CAP-009 | 🟡 |
| `opportunity.closed_won` | Commercial | Timeline, Revenue, Forecast | CAP-009 | 🟡 |
| `opportunity.closed_lost` | Commercial | Timeline, Revenue | CAP-009 | 🟡 |
| `decision.created` | Decision Center | Timeline | CAP-022 | 🟡 |
| `decision.feedback` | Decision Center | Learning Engine | CAP-022 | 🟡 |
| `workflow.executed` | Workflow Engine | Timeline | CAP-025 | 🟡 |
| `notification.created` | Notification Service | WebSocket | — | ✅ |
| `telemetry.event` | Telemetry Service | Analytics | CAP-045 | ✅ |
| `google.email_synced` | Communication Hub | — | CAP-034 | 🟡 |
| `google.calendar_synced` | Communication Hub | — | CAP-035 | 🟡 |

**Note:** Kafka is configured but defaults to `in_memory` in dev. Events listed as 🟡 exist in code but may not be wired end-to-end.

---

## 9. Widget Registry

### 9.1 Dashboard Widgets (13)

| Widget | ID | Capability | Feature Package | Container | View | Status |
|--------|----|------------|-----------------|-----------|------|--------|
| Pipeline | WDG-001 | CAP-007 | dashboard | PipelineContainer | PipelineView | ✅ |
| Company Health | WDG-002 | CAP-007 | dashboard | CompanyHealthContainer | CompanyHealthView | ✅ |
| Company Engagement | WDG-003 | CAP-007 | dashboard | CompanyEngagementContainer | CompanyEngagementView | ✅ |
| Email Intelligence | WDG-004 | CAP-007 | dashboard | EmailIntelligenceContainer | EmailIntelligenceView | ✅ |
| Calendar Intelligence | WDG-005 | CAP-007 | dashboard | CalendarIntelligenceContainer | CalendarIntelligenceView | ✅ |
| Decision Queue | WDG-006 | CAP-007 | dashboard | DecisionQueueContainer | DecisionQueueView | ✅ |
| Intelligence Feed | WDG-007 | CAP-007 | dashboard | IntelligenceFeedContainer | IntelligenceFeedView | ✅ |
| Market Pulse | WDG-008 | CAP-007 | dashboard | MarketPulseContainer | MarketPulseView | ✅ |
| Mission Center | WDG-009 | CAP-007 | dashboard | MissionCenterContainer | MissionCenterView | ✅ |
| Follow-up Center | WDG-010 | CAP-007 | dashboard | FollowupCenterContainer | FollowupCenterView | ✅ |
| Recent Activity | WDG-011 | CAP-007 | dashboard | RecentActivityContainer | RecentActivityView | ✅ |
| AI Brief | WDG-012 | CAP-007 | dashboard | — | — | ✅ |
| Widget Card (base) | WDG-013 | CAP-007 | dashboard | — | — | ✅ |

### 9.2 Company Intelligence Widgets (11)

| Widget | ID | Capability | Container | View | Status |
|--------|----|------------|-----------|------|--------|
| Company 360 | WDG-101 | CAP-004 | Company360Container | Company360View | ✅ |
| Smart Timeline | WDG-102 | CAP-004 | SmartTimelineContainer | SmartTimelineView | ✅ |
| AI Recommendation | WDG-103 | CAP-004 | — | — | ✅ |
| Buying Journey | WDG-104 | CAP-004 | — | — | ✅ |
| Company DNA | WDG-105 | CAP-004 | — | — | ✅ |
| Decision Makers | WDG-106 | CAP-004 | — | — | ✅ |
| Document Intelligence | WDG-107 | CAP-004 | — | — | ✅ |
| Golden Record | WDG-108 | CAP-004 | — | GoldenRecordPanel | ✅ |
| Government Intelligence | WDG-109 | CAP-004 | — | — | ✅ |
| Relationship Graph | WDG-110 | CAP-004 | — | KnowledgeGraphPanel | ✅ |
| Signals Feed | WDG-111 | CAP-004 | — | — | ✅ |

### 9.3 Employee 360 Widgets (7)

| Widget | ID | Capability | Status |
|--------|----|------------|--------|
| Profile | WDG-201 | CAP-014 | ✅ |
| Portfolio | WDG-202 | CAP-014 | ✅ |
| AI Coach | WDG-203 | CAP-014 | ✅ |
| KPIs | WDG-204 | CAP-014 | ✅ |
| Activity | WDG-205 | CAP-014 | ✅ |
| Calendar | WDG-206 | CAP-014 | ✅ |
| Email | WDG-207 | CAP-014 | ✅ |

### 9.4 Admin Widgets (10)

| Widget | ID | Capability | Status |
|--------|----|------------|--------|
| TenantList | WDG-301 | CAP-041 | ✅ |
| UserList | WDG-302 | CAP-041 | ✅ |
| PlanManager | WDG-303 | CAP-041 | ✅ |
| FeatureFlagManager | WDG-304 | CAP-041 | ✅ |
| HealthDashboard | WDG-305 | CAP-044 | ✅ |
| AuditLog | WDG-306 | CAP-042 | ✅ |
| RoleManager | WDG-307 | CAP-003 | ✅ |
| AIAuditLog | WDG-308 | CAP-043 | ✅ |
| AICostDashboard | WDG-309 | CAP-043 | ✅ |
| JobList | WDG-310 | CAP-028 | ✅ |

### 9.5 Revenue Execution Widgets (20)

| Widget | ID | Capability | Status |
|--------|----|------------|--------|
| Opportunity Detail | WDG-401 | CAP-009 | ✅ |
| Opportunity List | WDG-402 | CAP-009 | ✅ |
| Pipeline Intelligence | WDG-403 | CAP-008 | ✅ |
| Forecast Intelligence | WDG-404 | CAP-015 | ✅ |
| Territory Intelligence | WDG-405 | CAP-017 | ✅ |
| Churn Intelligence | WDG-406 | CAP-018 | ✅ |
| Expansion Intelligence | WDG-407 | CAP-018 | ✅ |
| Meeting Intelligence | WDG-408 | CAP-020 | ✅ |
| Email Intelligence | WDG-409 | CAP-021 | ✅ |
| Task Intelligence | WDG-410 | CAP-013 | ✅ |
| Revenue Health | WDG-411 | CAP-018 | ✅ |
| Revenue Timeline | WDG-412 | CAP-018 | ✅ |
| Playbook Engine | WDG-413 | CAP-008 | ✅ |
| Next Best Action | WDG-414 | CAP-050 | ✅ |
| NBA Widget | WDG-415 | CAP-050 | ✅ |
| API Platform | WDG-416 | — | ✅ |
| Multi-Workspace | WDG-417 | — | ✅ |
| Enterprise Security | WDG-418 | — | ✅ |
| Marketplace | WDG-419 | CAP-036 | ✅ |
| MCP Integration | WDG-420 | — | ✅ |

---

## 10. Integration Registry

| Integration | ID | Type | Direction | Capability | Auth | Status |
|-------------|----|------|-----------|------------|------|--------|
| Google OAuth 2.0 | INT-001 | OAuth | Outbound | CAP-033 | OAuth 2.0 | ✅ |
| Gmail API | INT-002 | REST | Inbound | CAP-034 | OAuth 2.0 | ✅ |
| Google Calendar API | INT-003 | REST | Inbound | CAP-035 | OAuth 2.0 | ✅ |
| Balady Scraper | INT-004 | Scraper | Inbound | CAP-040 | Public | ✅ |
| Najiz Scraper | INT-005 | Scraper | Inbound | CAP-040 | Public | ✅ |
| Rega Scraper | INT-006 | Scraper | Inbound | CAP-040 | Public | ✅ |
| Taqeem Scraper | INT-007 | Scraper | Inbound | CAP-040 | Public | ✅ |
| NCNP Scraper | INT-008 | Scraper | Inbound | CAP-040 | Public | ✅ |
| Notion API | INT-009 | REST | Inbound | CAP-038 | Token | ✅ |
| OpenAI API | INT-010 | REST | Outbound | CAP-023/024 | API Key | ✅ |
| Webhook (outgoing) | INT-011 | Webhook | Outbound | CAP-027 | HMAC | ✅ |
| Webhook (incoming) | INT-012 | Webhook | Inbound | CAP-027 | Secret | ✅ |

---

## 11. AI Registry

### 11.1 AI Providers

| Provider | Models | Capability | Status |
|----------|--------|------------|--------|
| OpenAI | GPT-4o, GPT-4o-mini | All AI | ✅ |
| (Extensible) | Provider interface | CAP-023 | ✅ |

### 11.2 AI Agents

| Agent | ID | Capability | Status | Notes |
|-------|----|------------|--------|-------|
| RAG Agent | AI-AG-001 | CAP-024 | ✅ | LangChain-based, streaming |
| NBA Reasoner | AI-AG-002 | CAP-050 | ✅ | Decision recommendations |
| Recommendation Engine | AI-AG-003 | CAP-022 | ✅ | Evaluation + scoring |
| AI Coach | AI-AG-004 | CAP-014 | ✅ | Employee coaching |
| Sales Copilot | AI-AG-005 | CAP-053 | 🟡 | Gated behind feature flag |
| Revenue Brain | AI-AG-006 | CAP-057 | ❌ | Not started |
| Digital Twin | AI-AG-007 | CAP-061 | ❌ | Not started |
| Agent Runtime | AI-AG-008 | CAP-060 | ❌ | Not started |

### 11.3 AI Prompts (Registry)

| Prompt | ID | Category | Status |
|--------|----|----------|--------|
| Company Summary | AI-PR-001 | Intelligence | ✅ |
| Opportunity Analysis | AI-PR-002 | Sales | ✅ |
| Meeting Brief | AI-PR-003 | Meeting | ✅ |
| Meeting Summary | AI-PR-004 | Meeting | ✅ |
| Email Analysis | AI-PR-005 | Email | ✅ |
| Employee Coaching | AI-PR-006 | Employee | ✅ |
| Decision Evaluation | AI-PR-007 | Decision | ✅ |
| NBA Recommendation | AI-PR-008 | Decision | ✅ |
| Search AI Answer | AI-PR-009 | Search | ✅ |

### 11.4 AI Guardrails

| Guardrail | ID | Status |
|-----------|----|--------|
| Input Sanitization | AI-GR-001 | ✅ |
| Output Moderation | AI-GR-002 | ✅ |
| Output Validation | AI-GR-003 | ✅ |
| JSON Extraction | AI-GR-004 | ✅ |
| Faithfulness Check | AI-GR-005 | ✅ |
| Agent Grounding | AI-GR-006 | ✅ |

---

## 12. Traceability Matrix

### Vision → Capability → Code → Tests

```
VISION: Company Intelligence
  └── DOM-002: Company Intelligence
       └── CAP-004: Company 360
            ├── UI: /companies, /companies/[id], /companies/[id]/360
            ├── FEATURE PACKAGE: features/company-intelligence/
            ├── WIDGETS: WDG-101 to WDG-111 (11 widgets)
            ├── SERVICES: CompanyService (app/modules/company/)
            ├── API: 17 endpoints at /api/v1/companies/
            ├── DB: companies, branches, licenses, sources
            ├── TESTS:
            │   ├── unit: test_company_matcher.py
            │   ├── module: company/tests/test_service.py, company/tests/test_bulk_operations.py, company/tests/test_company_extended.py
            │   ├── e2e: test_critical_paths.py
            │   └── TOTAL: ~89 tests
            └── STATUS: ✅ Operational

VISION: Revenue Intelligence
  └── DOM-005 + DOM-006: Commercial + Revenue
       ├── CAP-008: Pipeline
       ├── CAP-009: Opportunity
       ├── CAP-015: Forecast
       ├── CAP-016: Quota
       ├── CAP-017: Territory
       └── CAP-018: Revenue Dashboard
           ├── UI: /opportunities, /opportunities/[id], /pipeline, /forecast, /revenue
           ├── FEATURE PACKAGE: features/revenue-execution/
           ├── WIDGETS: WDG-401 to WDG-420 (20 widgets)
           ├── API: ~50 endpoints across commercial, revenue, forecast routers
           ├── DB: commercial_opportunities, commercial_* (10+ tables)
           ├── TESTS: ~180 tests across domains/commercial/*, tests/unit/test_revenue_*
           └── STATUS: ✅ Operational (in-memory for some services)

VISION: AI & Knowledge
  └── DOM-009 + DOM-011 + DOM-012: Decision + Knowledge + AI Platform
       ├── CAP-022: Decision Center
       ├── CAP-023: AI Prompt Registry
       ├── CAP-024: RAG Pipeline
       ├── CAP-029: Knowledge Graph
       └── CAP-053: Sales Copilot (🟡)
           ├── UI: /decisions, /ai, /rag, /graph, /copilot (gated)
           ├── API: ~30 endpoints
           ├── TESTS: ~100 tests
           └── STATUS: ✅ (except Copilot 🟡)

VISION: Automation
  └── DOM-014: Automation & Workflows
       ├── CAP-025: Workflow Engine
       ├── CAP-026: Rules Engine
       ├── CAP-027: Webhooks
       └── CAP-028: Scheduled Jobs
           ├── UI: /automation, /rules
           ├── API: ~45 endpoints
           ├── TESTS: ~98 tests
           └── STATUS: ✅

VISION: Integration & Data
  └── DOM-007 + DOM-017: Communication Hub + Data Fabric
       ├── CAP-033: Google OAuth
       ├── CAP-034: Gmail Sync
       ├── CAP-035: Calendar Sync
       ├── CAP-040: Data Fabric
       └── CAP-037: Entity Resolution
           ├── API: ~20 endpoints
           ├── TESTS: ~130 tests
           └── STATUS: ✅ (Data Fabric partial)
```

---

## 13. Architecture Decisions (Current)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Pattern** | Modular Monolith (DDD) | Team size 5-7; extract to microservices later |
| **Primary DB** | PostgreSQL 16 + pgvector + pg_trgm | ACID + JSON + Arabic/English FTS + vectors |
| **Graph DB** | Neo4j 5 (community) | Relationship traversals (but **zero data** currently) |
| **Cache** | Redis 7 | Sessions, rate limiting, OAuth state |
| **Search** | Meilisearch + pgvector (hybrid RRF) | Full-text + semantic fusion |
| **Event Bus** | Kafka (in-memory fallback) | Default `in_memory` for dev; Kafka optional |
| **AI** | OpenAI (GPT-4o, GPT-4o-mini) + LangChain | RAG pipeline, configurable routing |
| **Frontend** | Next.js 15 + React 19 + Radix UI + Tailwind | App Router, RTL, dark mode |
| **API** | REST (primary) + GraphQL (partial) + MCP (stub) | Multi-surface access |
| **Auth** | JWT + OAuth 2.0 (Google) + RBAC | Multi-tenant isolation |
| **i18n** | Arabic-first, English-second | RTL layout; Arabic NLP pipeline |
| **AI Copilot** | Feature-flagged OFF by default | Honesty: stub/gated, not production |

---

## 14. Current Gaps (as of 2026-07-30)

### Critical Gaps

| Gap | Impact | Location |
|-----|--------|----------|
| Cross-tenant IDOR in Decision Center | Security P0 | `domains/decision_center/postgres_repo.py` |
| Webhook SSRF (no URL allowlist) | Security P0 | `app/routers/workflows.py:493` |
| CSRF bypass via `X-API-Key` header | Security P0 | `app/common/csrf.py` |
| Knowledge graph queries missing tenant filters | Security P1 | `runtime/knowledge_graph_runtime/` |
| Frontend build fails (TypeScript + ESLint) | Dev velocity | `salesos/frontend/` |
| Alembic schema drift (5 revisions behind) | Data integrity | `app/alembic/` |
| Kafka defaults to in-memory | Reliability | `app/celery_app.py` |
| Neo4j configured with zero data | Feature gap | `infra/docker/` |

### Architecture Gaps

| Gap | Finding |
|-----|---------|
| **Canonical naming not unified** | Company 360 vs Company Intelligence vs Golden Record used interchangeably |
| **Domain ≠ Module ≠ Engine** | `workflow` exists as module, domain, runtime, and page — undefined relationship |
| **In-memory repositories** | Many services still use InMemoryRepository (not PostgreSQL) |
| **No middleware.ts** | Auth protection is client-side only (localStorage check in useEffect) |
| **Multi-product** | No code exists for AuditOS, DecisionOS, or LocalContentOS |

### Test Gaps

| Area | Gap |
|------|-----|
| Runtime engines (25 of 31) | Zero dedicated tests |
| App modules (10 of 27) | No co-located `tests/` directories |
| E2E coverage | 149 tests for 40+ capabilities (thin) |
| Contract tests | Only 31 tests covering basic schemas |

---

## 15. Terminology Guide (Canonical Names)

| Term | Definition | Used In | Not to be confused with |
|------|------------|---------|------------------------|
| **Company 360** | The full detail page for a company with all intelligence widgets | `/companies/[id]/360` | Company Intelligence (the domain) |
| **Company Intelligence** | The domain responsible for company data and insights | DOM-002 | Company 360 (the page) |
| **Golden Record** | The single source-of-truth entity after deduplication | Entity Resolution | Company (the raw data) |
| **Employee 360** | Full employee detail page with all widgets | `/employees/[id]` | Employee Intelligence (the domain) |
| **Work Intelligence** | Employee productivity/activity analysis | Domain module | Employee 360 (the page) |
| **Activity Intelligence** | Analysis of business activities across entities | Runtime engine | Activities (the page) |
| **Communication Hub** | Google integration (Gmail + Calendar sync) | Module | Email Intelligence (analysis) |
| **Revenue Execution** | The operational CRM layer (Opportunities, Tasks) | Module | Revenue Intelligence (analysis) |
| **Decision Center** | The AI decision platform (evaluate, recommend) | Domain | Decision (the runtime engine) |

---

## 16. Authority & Maintenance

### 16.1 Document Hierarchy

```
Business Vision (PRODUCT_BIBLE.md / MCOS)
        │
        ▼
CANONICAL_ARCHITECTURE.md  ←  THIS DOCUMENT (Architecture SSOT)
        │
        ▼
Architecture Decision Records (docs/adr/ + engineering-os/adr/)
        │
        ▼
Capability Registry (CAP-xxx — verified by CI)
        │
        ▼
Executable Code (the ground truth)
```

1. **Business Vision** (MCOS / PRODUCT_BIBLE.md) defines *why* — the strategic intent.
2. **This document** defines *what* — the canonical architecture, capabilities, objects, and traceability.
3. **ADRs** define *why that way* — architectural decisions with rationale and alternatives.
4. **Capability Registry** is the operational index — can be extracted to a script or database.
5. **Code** is the *executable evidence* — any claim in this document must be verifiable in code.

### 16.2 Maintenance Rules

1. **Conflicts** with PRODUCT_BIBLE.md, FEATURE_STATUS.md, MASTER_BLUEPRINT.md, or prior inventory reports are resolved in favor of this document.
2. **Updates** require: (a) evidence from executable code, (b) approval from CTO/Architect.
3. **Review cycle:** Every 2 weeks or after any sprint that changes >5% of the capability surface.
4. **Canonical IDs** (CAP-*, OBJ-*, WDG-*) are **immutable** once assigned. Deprecated capabilities keep their ID with a lifecycle status change.
5. **CI enforcement**: A CI check MUST compare this document against actual code every PR and report mismatches (planned in Wave 8).

---

## 17. Architecture Health Scorecard

> **Current Grade: B- / "Needs Improvement"** — measured from executable code at commit `6f75e8d` (2026-07-30).

| Metric | Value | Grade | Trend |
|--------|-------|-------|-------|
| **Persistence Ratio** | 45 PostgreSQL : 35 InMemory : 8 Other | **B+** | Improving (X-SPRINT added 15+ Postgres repos) |
| **Multi-Tenant Coverage** | 100% Tenant Workspace (72/72 tenant-scoped tables); 4 Owner-Platform-scoped + 1 root (`tenants`, §17.2) | **A** | Stable (no §17.2 tenant-isolation gaps) |
| **Event-Driven Adoption** | 5 of ~60 modules actively emit/subscribe | **D** | Stalled (infra is ready, adoption is not) |
| **Test-to-Source Ratio** | 13.8% (277 test files / 2,009 source files) | **D** | Coverage artifact is stale/broken |
| **Feature Flag Maturity** | 6 seed flags + unlimited runtime flags, per-tenant override, gradual rollout | **A** | Mature |
| **API Versioning** | 1 version (v1), no v2, no deprecation strategy | **C** | No backward-compat strategy visible |
| **Circular Dependency Risk** | 1 HIGH (Company ↔ Entity Resolution), 0 CRITICAL | **B** | Low risk overall |
| **AI Copilot Honesty** | Gated behind `feature_ai_copilot=False` | **A** | Honest about stub status |

### 17.1 Persistence Detail

**PostgreSQL-backed (production-ready):** 45 repositories across:
- Identity (TenantRepository, UserRepository)
- Company (CompanyRepository, PgVectorCompanyRepository)
- Contact (ContactRepository, ContactSearchRepository)
- Commercial (PostgresOpportunityRepository, PostgresPipelineRepository, etc.)
- Workflow (PostgresWorkflowRepository, PostgresWebhookRepository, etc.)
- Admin (PostgresPlanRepository, PostgresFeatureFlagRepository, etc.)
- Decision Center (PostgresDecisionCenterRepository)
- Analytics (PostgresReportRepository)
- Notifications (PostgresNotificationRepository)
- Communication Hub (GoogleAccountRepository)
- Employee (PostgresEmployeeSignalRepository)

**InMemory-only (test/dev only, no production path):** 35 repositories including:
- Signal Marketplace (SignalRepository, SignalSubscriptionRepository)
- Decision Context (InMemoryDecisionRepository)
- Decision Recommendation (InMemoryRecommendationRepository)
- Revenue Territory, Quota, Forecast (all InMemory)
- Scoring, Timeline, Feature Store partial

### 17.2 Multi-Tenant Coverage Detail

> **Scope note:** Tables without `tenant_id` below are not tenant-isolation gaps. Under the two-plane model (`SAAS_PLATFORM_ARCHITECTURE.md` §2, §11.3), four tables are **Owner-Platform-scoped** by design (queried cross-tenant by Owner-role principals only); `tenants` is the root entity.

| Table | Domain | Scope |
|-------|--------|-------|
| tenants | Identity | Root entity (not tenant-scoped) |
| users | Identity | Tenant-scoped (`tenant_id`) |
| companies | Company Intelligence | Tenant-scoped (`tenant_id`) |
| contacts | Contact Management | Tenant-scoped (`tenant_id`) |
| branches | Company Intelligence | Tenant-scoped (via company) |
| commercial_opportunities | Commercial | Tenant-scoped (`tenant_id`) |
| commercial_* (all 10+ tables) | Commercial | Tenant-scoped (`tenant_id`) |
| workflows | Automation | Tenant-scoped (`tenant_id`) |
| decision_center_decisions | Decision Intelligence | Tenant-scoped (`tenant_id`) |
| audit_logs | Governance | Tenant-scoped (`tenant_id`) |
| telemetry_events | Governance | Tenant-scoped (`tenant_id`) |
| reports | Analytics | Tenant-scoped (`tenant_id`) |
| sso_connections | Identity | Owner-Platform-scoped (by design) |
| marketplace_plugins | Marketplace | Owner-Platform-scoped (by design; superseded by `marketplace_listings` per `SAAS_PLATFORM_ARCHITECTURE.md` §11.3) |
| feature_definitions | Feature Store | Owner-Platform-scoped (by design) |
| feature_values | Feature Store | Owner-Platform-scoped (by design) |

### 17.3 Event-Driven Adoption Detail

| Module | Events | Status |
|--------|--------|--------|
| Workflow Engine | WorkflowCompleted, WorkflowFailed, WorkflowTimedOut | ✅ Active |
| Decision Context | Decision creation events | 🟡 Active |
| Decision Recommendation | Recommendation events | 🟡 Active |
| Timeline Recorder | Subscribes to domain events | ✅ Active |
| Company Service | company.* events (defined, subscription?) | 🟡 Partial |
| Opportunity Service | opportunity.* events (defined, subscription?) | 🟡 Partial |

**Gap:** 55 of ~60 modules are pure synchronous CRUD with no event emission.

---

## 18. Dependency Graph

### 18.1 Module Dependency Map

```
                    ┌──────────────────────────┐
                    │       IDENTITY           │  ← Foundation (8 dependents)
                    │  (self-contained)        │
                    └──────────┬───────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                   ▼
     ┌──────────┐      ┌──────────────┐     ┌──────────┐
     │  ADMIN   │      │    AUDIT     │     │   SSO    │
     └──────────┘      └──────────────┘     └──────────┘

                    ┌──────────────────────────┐
                    │        COMPANY           │  ← Central Hub (5 dependents)
                    │  depends on: Contact,    │
                    │  EntityResolution,       │
                    │  domains.search.*,       │
                    │  domains.commercial.*    │
                    └──────────┬───────────────┘
                               │
            ┌──────────────────┼──────────┬───────────────┐
            ▼                  ▼          ▼               ▼
     ┌──────────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐
     │  EMPLOYEE_360 │  │ ENTITY_   │  │ EXCEL_   │  │ NOTION_  │
     │               │  │ RESOLUTION│  │ IMPORT   │  │ SYNC     │
     └──────────────┘  └────────────┘  └──────────┘  └──────────┘

                    ┌──────────────────────────┐
                    │     DOMAIN LAYER         │
                    ├──────────────────────────┤
                    │ commercial → revenue     │  (one-way)
                    │ commercial → decision    │  (one-way)
                    │ copilot → search         │  (one-way)
                    │ employee → identity      │  (one-way)
                    │ employee → audit         │  (one-way)
                    └──────────────────────────┘

                    ┌──────────────────────────┐
                    │     RUNTIME LAYER        │
                    ├──────────────────────────┤
                    │ data_fabric → Company    │
                    │ data_fabric → EntityRes  │
                    │ data_fabric → search     │
                    │ nba_engine → commercial  │
                    │ pipeline_analytics → comm│
                    └──────────────────────────┘
```

### 18.2 Independent Modules (no cross-module deps)

These 12 modules are fully self-contained (import only from self, `app.common`, `sdk.*`):

- api_keys
- cache
- communication_hub
- decision
- demo_mode
- executive
- monitoring
- rules_engine
- search (module)
- signal_marketplace
- telemetry
- tenant
- webhooks
- work_intelligence

### 18.3 Circular Dependency Risk

| Risk Level | Pair | Detail |
|-----------|------|--------|
| **HIGH** | company ↔ entity_resolution | Both import each other's models (lazy, inside functions — safe at import time, fragile conceptually) |
| **NONE** | All other pairs | All one-way dependencies |

### 18.4 Capability Dependency Chain

```
CAP-001 Tenant    ──→ CAP-002 Auth ──→ (everything)
CAP-002 Auth      ──→ (all authenticated endpoints)
CAP-004 Company   ──→ CAP-005 Search, CAP-030 Timeline, CAP-037 Entity Resolution
CAP-005 Search    ──→ (standalone)
CAP-007 Dashboard ──→ CAP-004 Company, CAP-008 Pipeline, CAP-009 Opportunity, CAP-014 Employee
CAP-008 Pipeline  ──→ CAP-009 Opportunity
CAP-009 Opp       ──→ CAP-010 Quote, CAP-011 Proposal, CAP-012 Contract, CAP-020 Meeting, CAP-021 Email
CAP-015 Forecast  ──→ CAP-008 Pipeline, CAP-009 Opportunity
CAP-022 Decision  ──→ CAP-024 RAG, CAP-023 AI
CAP-024 RAG       ──→ CAP-023 AI
CAP-025 Workflow  ──→ CAP-026 Rules, CAP-027 Webhooks
CAP-031 Analytics ──→ CAP-007 Dashboard, CAP-008 Pipeline, CAP-009 Opportunity
```

---

## 19. Capability Lifecycle

### 19.1 Lifecycle States

| State | Definition | Example |
|-------|------------|---------|
| **proposed** | Idea, not yet planned | CAP-058 GTM Intelligence |
| **planned** | In roadmap, not started | CAP-056 Mobile App |
| **in_dev** | Active development, partial code | CAP-051 Data Fabric (full) |
| **beta** | Code exists but gated/stubbed | CAP-053 Sales Copilot |
| **ga** | General availability, production | CAP-004 Company 360 |
| **deprecated** | Replaced, kept for backward compat | — |
| **removed** | Deleted from codebase | — |

### 19.2 Current Lifecycle Distribution

| State | Count | Capabilities |
|-------|-------|-------------|
| **ga** | 41 | CAP-001–022, CAP-024–032, CAP-036–049 (except those marked partial) |
| **beta** | 4 | CAP-019 Activity Intel, CAP-029 Knowledge Graph, CAP-037 Entity Resolution, CAP-053 Sales Copilot |
| **in_dev** | 3 | CAP-040 Data Fabric, CAP-050 NBA, CAP-052 Feature Store |
| **planned** | 7 | CAP-051, CAP-054, CAP-055, CAP-056, CAP-058, CAP-059, CAP-063 |
| **proposed** | 7 | CAP-057, CAP-060, CAP-061, CAP-062, CAP-064, CAP-065, CAP-066 |

---

## 20. ADR Mapping

### 20.1 ADR Catalog

| ADR | Title | Date | Status | Affected Capabilities |
|-----|-------|------|--------|----------------------|
| **ADR-001** | Modular Monolith Foundation | 2025-Q4 | ✅ Accepted | All |
| **ADR-002** | Executive Intelligence Workspace | 2025-Q4 | ✅ Accepted | CAP-007 Dashboard |
| **ADR-003** | Widget SDK v1 Freeze | 2025-Q4 | ✅ Accepted | All Widgets |
| **ADR-025** | Entity Resolution Pipeline | 2026-Q2 | ✅ Accepted | CAP-037 Entity Resolution, CAP-004 Company |
| **ADR-026** | Hybrid Search (Full-text + Semantic) | 2026-Q2 | ✅ Accepted | CAP-005 Search |
| **ADR-027** | Feature Store Implementation | 2026-Q2 | ✅ Accepted | CAP-052 Feature Store |
| **ADR-028** | Knowledge Graph Integration | 2026-Q2 | ✅ Accepted | CAP-029 Knowledge Graph |
| **ADR-030** | Unified LLM Provider Architecture | 2026-07-16 | ✅ Accepted | CAP-023 AI Platform, CAP-024 RAG |
| **ADR-031** | Webhook Auth API Key Assessment | 2026-07-09 | ✅ Accepted | CAP-027 Webhooks |
| **ADR-032** | Widget SDK Reconciliation | 2026-07-16 | ✅ Accepted | All Widgets |
| **ADR-033** | Decision Engine Lifecycle | 2026-07-17 | 📝 Proposed | CAP-022 Decision Center, CAP-050 NBA |
| **ADR-034** | Repository Pattern Compliance | 2026-07-17 | 📝 Proposed | CAP-002 Auth (Identity domain) |
| **ADR-035** | Sprint 0 Architecture Reconciliation | 2026-07-17 | 📝 Proposed | All (governance) |

### 20.2 Capability → ADR Mapping

| Capability | Relevant ADRs |
|------------|---------------|
| CAP-001 Tenant, CAP-002 Auth | ADR-001 (Modular Monolith), ADR-034 (Repository Pattern) |
| CAP-004 Company 360 | ADR-001, ADR-025 (Entity Resolution) |
| CAP-005 Search | ADR-001, ADR-026 (Hybrid Search) |
| CAP-007 Dashboard | ADR-002 (Executive Workspace) |
| CAP-022 Decision Center | ADR-001, ADR-033 (Decision Lifecycle) |
| CAP-023 AI Platform | ADR-030 (Unified LLM Provider) |
| CAP-024 RAG | ADR-001, ADR-030 (Unified LLM Provider) |
| CAP-027 Webhooks | ADR-031 (Webhook Auth) |
| CAP-029 Knowledge Graph | ADR-028 (KG Integration) |
| CAP-037 Entity Resolution | ADR-025 (ER Pipeline) |
| CAP-052 Feature Store | ADR-027 (Feature Store) |
| Widgets (all) | ADR-003 (SDK v1 Freeze), ADR-032 (SDK Reconciliation) |

---

## 21. Data Flow Diagrams

### 21.1 Google Integration Data Flow

```
Google Gmail API  ──→  Communication Hub (OAuth 2.0)
                            │
                     GoogleAccount (tokens stored, Fernet-encrypted)
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              Gmail Sync      Calendar Sync
                    │               │
                    ▼               ▼
              email_events    calendar_events
              (PostgreSQL)    (PostgreSQL)
                    │               │
                    ▼               ▼
              Email Intelligence   Timeline
              (sentiment, topics,  (event recorded)
               action items)
                    │
                    ▼
              Activity Model → Company 360 → Dashboard
```

### 21.2 Company Intelligence Data Flow

```
Government Scrapers (Balady, Najiz, Rega, Taqeem, NCNP)
        │
        ▼
  Data Fabric (scrape → normalize → validate)
        │
        ▼
  Entity Resolution (dedup → Golden Record → conflicts)
        │
        ▼
  Company Service (companies, branches, licenses)
        │
        ├──→ Search Index (pgvector + Meilisearch)
        │
        ├──→ Knowledge Graph (Neo4j — currently empty)
        │
        ├──→ Timeline (events recorded)
        │
        └──→ Company 360 Page → Dashboard Widgets
```

### 21.3 Opportunity → Revenue Data Flow

```
User Input / External Source
        │
        ▼
  Opportunity (created in pipeline)
        │
        ├──→ Stage Entries (pipeline analytics)
        ├──→ Activities (calls, meetings, emails)
        ├──→ Quotes → Proposals → Contracts
        ├──→ Meetings (recorded + analyzed)
        ├──→ Emails (analyzed for sentiment/topics)
        │
        ▼
  Revenue Intelligence
        ├──→ Forecast (weighted pipeline + scenarios)
        ├──→ Quota (attainment tracking)
        ├──→ Territory (assignment + coverage)
        └──→ Revenue Dashboard
```

### 21.4 Decision Intelligence Data Flow

```
Context (Company, Opportunity, Employee data)
        │
        ▼
  Decision Engine (evaluate)
        ├──→ Policies (business rules)
        ├──→ Recommendations (AI-generated)
        ├──→ Scoring (computed scores)
        │
        ▼
  Decision Center (record + audit)
        │
        ├──→ Decision Queue (dashboard widget)
        ├──→ Feedback Loop (accept/reject → learning)
        └──→ Timeline (event recorded)
```

### 21.5 Authentication Flow

```
User → /login (email + password)
        │
        ▼
  Identity Service (verify password → JWT tokens)
        │
        ├──→ access_token (15min, JWT)
        ├──→ refresh_token (7d, rotation family)
        ├──→ device_session (recorded)
        │
        ▼
  Authenticated Request
        ├──→ verify_token middleware
        ├──→ extract tenant_id + user_id + role
        ├──→ permission check (RBAC)
        └──→ route handler
```

---

## 22. CI Architecture Validation (Planned)

### 22.1 Validation Rules

| Rule | What It Checks | Status |
|------|---------------|--------|
| R-001 | Every CAP-xxx has at least one page.tsx or API endpoint | 🟡 Planned |
| R-002 | Every OBJ-xxx corresponds to a SQLAlchemy model file | 🟡 Planned |
| R-003 | Every API endpoint in registry exists in router files | 🟡 Planned |
| R-004 | Every page.tsx in registry exists on disk | 🟡 Planned |
| R-005 | No tenant_id missing on tables that should have it | 🟡 Planned |
| R-006 | Architecture Health Scorecard regenerated per PR | 🟡 Planned |
| R-007 | Coverage percentage reported per PR | 🟡 Planned |

### 22.2 Implementation

A CI script (`scripts/arch-validate.ps1` or similar) will:
1. Parse this document's registries
2. Scan the codebase for verification
3. Report mismatches as PR comments
4. Regenerate the Health Scorecard

Target: Wave 8 of the GA remediation plan.
