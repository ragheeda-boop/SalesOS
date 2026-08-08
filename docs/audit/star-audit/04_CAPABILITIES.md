# 04 — CAPABILITY DISCOVERY: Every Capability Found in Code

> Source: Source code reverse engineering (Phase 4)
> Classification: IMPLEMENTATION ONLY

---

## Methodology

Capabilities were discovered by analyzing:
1. Backend routers (70+ endpoints)
2. Backend modules (33 modules)
3. Backend domains (19 domains)
4. Backend runtime engines (31 engines)
5. Frontend pages (93+ pages)
6. Frontend API modules (37 modules)
7. Frontend feature modules (17 features)

---

## 1. Identity & Access Management

| Attribute | Value |
|-----------|-------|
| **Name** | Identity & Access Management |
| **Purpose** | User registration, authentication, authorization, tenant management |
| **Backend** | `app/modules/identity/` (service, models, repositories, router, signup, invite, jwks) |
| **Frontend** | `/login`, `/register`, `/admin/login` pages; `src/lib/api/identity.ts` |
| **Database** | tenants, users, refresh_token_families, device_sessions, password_reset_tokens, token_blacklists |
| **Dependencies** | PostgreSQL, Redis (rate limiting), RSA keys |
| **Runtime** | FastAPI auth middleware, JWT RS256 |
| **Owner** | Security |
| **Business Value** | Critical — foundation for all multi-tenant operations |
| **Status** | ✅ PRODUCTION-GRADE |

---

## 2. Company Intelligence

| Attribute | Value |
|-----------|-------|
| **Name** | Company Intelligence |
| **Purpose** | Company CRUD, search, enrichment, 360-degree view |
| **Backend** | `app/modules/company/` (service, repositories, pgvector_repository, router) |
| **Frontend** | `/companies`, `/companies/[id]` pages; `src/lib/api/company.ts` |
| **Database** | companies, branches, licenses |
| **Dependencies** | PostgreSQL (pg_trgm, pgvector), scrapers |
| **Runtime** | Feature store (company scores), knowledge graph |
| **Owner** | Product |
| **Business Value** | High — core value proposition |
| **Status** | ✅ FUNCTIONAL |

---

## 3. Contact Management

| Attribute | Value |
|-----------|-------|
| **Name** | Contact Management |
| **Purpose** | Contact CRUD, linking to companies |
| **Backend** | `app/modules/contact/` (service, router) |
| **Frontend** | `/contacts` page; `src/lib/api/contact.ts` |
| **Database** | contacts |
| **Dependencies** | PostgreSQL |
| **Runtime** | None |
| **Owner** | Product |
| **Business Value** | Medium — supporting capability |
| **Status** | ⚠️ BASIC |

---

## 4. Employee 360

| Attribute | Value |
|-----------|-------|
| **Name** | Employee 360 |
| **Purpose** | Employee profiles, signals, scoring, performance, timeline |
| **Backend** | `app/modules/employee_360/`, `domains/employee/` (20+ files) |
| **Frontend** | `/employees`, `/employees/[id]`, `/employees/me` pages; 14 employee-360 components |
| **Database** | employees, employee_signals, employee_scores |
| **Dependencies** | PostgreSQL, feature store |
| **Runtime** | Scoring engine, timeline runtime |
| **Owner** | Product |
| **Business Value** | High — key differentiator |
| **Status** | ✅ FUNCTIONAL |

---

## 5. Pipeline & Opportunities

| Attribute | Value |
|-----------|-------|
| **Name** | Pipeline & Opportunities |
| **Purpose** | Sales pipeline management, opportunity tracking |
| **Backend** | `domains/commercial/opportunity/`, `app/routers/commercial.py` |
| **Frontend** | `/opportunities`, `/opportunities/[id]`, `/pipeline` pages |
| **Database** | opportunities, pipelines, pipeline_stages |
| **Dependencies** | PostgreSQL |
| **Runtime** | Pipeline analytics |
| **Owner** | Product |
| **Business Value** | High — core sales workflow |
| **Status** | ⚠️ BACKEND REAL, FE PARTIAL |

---

## 6. Revenue Intelligence

| Attribute | Value |
|-----------|-------|
| **Name** | Revenue Intelligence |
| **Purpose** | Revenue analytics, forecasting, quotas, territories |
| **Backend** | `domains/revenue/` (analytics, forecast, quota, territory), `app/routers/revenue.py` |
| **Frontend** | `/revenue`, `/revenue/quotas`, `/revenue/territories`, `/forecast` pages |
| **Database** | revenue_analytics, revenue_forecasts, quotas, territories |
| **Dependencies** | PostgreSQL |
| **Runtime** | Pipeline analytics, forecast engine |
| **Owner** | Product |
| **Business Value** | High — executive decision support |
| **Status** | ⚠️ BACKEND EXISTS, FORECAST HARDCODED |

---

## 7. Search

| Attribute | Value |
|-----------|-------|
| **Name** | Unified Search |
| **Purpose** | Cross-entity search with trigram + vector similarity |
| **Backend** | `domains/search/` (engine, ranking, normalization, caching, contracts), `app/routers/search.py` |
| **Frontend** | `/search`, `/search/analytics` pages; `src/lib/api/search.ts` |
| **Database** | pg_trgm indexes, pgvector embeddings |
| **Dependencies** | PostgreSQL (pg_trgm, vector extension), Meilisearch (optional) |
| **Runtime** | Search runtime (multi-executor) |
| **Owner** | Product |
| **Business Value** | High — discovery mechanism |
| **Status** | ✅ FUNCTIONAL |

---

## 8. AI Copilot

| Attribute | Value |
|-----------|-------|
| **Name** | AI Copilot |
| **Purpose** | Natural language interface for data exploration |
| **Backend** | `domains/copilot/` (tools, schemas, feedback, telemetry), `app/routers/copilot.py` |
| **Frontend** | `/copilot` page; `copilot-panel.tsx` component |
| **Database** | copilot_sessions, copilot_feedback |
| **Dependencies** | OpenAI API, PostgreSQL, search |
| **Runtime** | Copilot tools (SearchCompaniesTool only) |
| **Owner** | AI |
| **Business Value** | High — AI differentiation |
| **Status** | ⚠️ GATED (feature_ai_copilot=False), SEARCH-ONLY TOOL |

---

## 9. Decision Center

| Attribute | Value |
|-----------|-------|
| **Name** | Decision Center |
| **Purpose** | Governed decision management (Source of Truth) |
| **Backend** | `domains/decision_center/` (service, postgres_repo, router), `app/routers/source_of_truth.py` |
| **Frontend** | `/decisions`, `/decisions/templates` pages |
| **Database** | decisions, decision_templates |
| **Dependencies** | PostgreSQL |
| **Runtime** | Decision runtime |
| **Owner** | Product |
| **Business Value** | High — governance capability |
| **Status** | ⚠️ FUNCTIONAL BUT IDOR VULNERABILITY |

---

## 10. Workflow Automation

| Attribute | Value |
|-----------|-------|
| **Name** | Workflow Automation |
| **Purpose** | Business process automation with visual builder |
| **Backend** | `domains/workflow/` (engine, event_subscriber, scheduler, templates), `app/routers/workflows.py` |
| **Frontend** | `/automation`, `/automation/workflows/new` pages |
| **Database** | workflows, workflow_steps, workflow_executions |
| **Dependencies** | PostgreSQL, Redis (scheduling) |
| **Runtime** | Workflow runtime |
| **Owner** | Product |
| **Business Value** | High — operational efficiency |
| **Status** | ⚠️ FUNCTIONAL BUT LIMITED |

---

## 11. Rules Engine

| Attribute | Value |
|-----------|-------|
| **Name** | Rules Engine |
| **Purpose** | Business rule definition and execution |
| **Backend** | `app/modules/rules_engine/` (engine), `app/routers/rules.py` |
| **Frontend** | `/rules` page |
| **Database** | rules, rule_definitions |
| **Dependencies** | PostgreSQL |
| **Runtime** | Policy runtime |
| **Owner** | Product |
| **Business Value** | Medium — extensibility |
| **Status** | ⚠️ FUNCTIONAL |

---

## 12. Analytics

| Attribute | Value |
|-----------|-------|
| **Name** | Analytics |
| **Purpose** | Business intelligence, reporting, dashboards |
| **Backend** | `domains/analytics/` (cubes, engine, repository, templates), `app/routers/analytics.py` |
| **Frontend** | `/analytics/*` pages (sales, revenue, pipeline, employees, automation, reports) |
| **Database** | analytics_events, analytics_aggregates |
| **Dependencies** | PostgreSQL |
| **Runtime** | Pipeline analytics, feature store |
| **Owner** | Product |
| **Business Value** | High — decision support |
| **Status** | ⚠️ FUNCTIONAL |

---

## 13. GTM Intelligence

| Attribute | Value |
|-----------|-------|
| **Name** | GTM Intelligence |
| **Purpose** | Go-to-market intelligence (ICP, market sizing, lead discovery, enrichment) |
| **Backend** | `app/modules/gtm/` (9 sub-engines) |
| **Frontend** | `/gtm/*` pages (9 sub-pages) |
| **Database** | icp_profiles, market_sizing_results, leads |
| **Dependencies** | PostgreSQL, external APIs |
| **Runtime** | Feature store, enrichment |
| **Owner** | Product |
| **Business Value** | High — market intelligence |
| **Status** | ⚠️ BACKEND EXISTS, FE PAGES EXIST |

---

## 14. Tenant Studio

| Attribute | Value |
|-----------|-------|
| **Name** | Tenant Studio |
| **Purpose** | No-code configuration (custom fields, workflows, scoring, territories, permissions, branding) |
| **Backend** | `app/modules/tenant_studio/` (10+ sub-engines) |
| **Frontend** | `/studio/*` pages (11 sub-pages) |
| **Database** | custom_field_definitions, scoring_rules, territory_rules, notification_rules |
| **Dependencies** | PostgreSQL |
| **Runtime** | Form engine, UI schema engine |
| **Owner** | Product |
| **Business Value** | High — customization |
| **Status** | ⚠️ BACKEND EXISTS, FE PAGES EXIST |

---

## 15. Admin Platform

| Attribute | Value |
|-----------|-------|
| **Name** | Admin Platform |
| **Purpose** | Platform administration (tenants, users, plans, billing, feature flags) |
| **Backend** | `app/modules/admin/` (entitlements, quota enforcement, services, repositories) |
| **Frontend** | `/admin/*` pages (tenants, billing, flags, audit, config, integrations) |
| **Database** | plans, feature_flags, entitlements |
| **Dependencies** | PostgreSQL |
| **Runtime** | Entitlement middleware |
| **Owner** | Platform |
| **Business Value** | Critical — platform operations |
| **Status** | ✅ FUNCTIONAL |

---

## 16. Knowledge Graph

| Attribute | Value |
|-----------|-------|
| **Name** | Knowledge Graph |
| **Purpose** | Entity relationship mapping, graph queries |
| **Backend** | `runtime/knowledge_graph_runtime/` (connectors, hybrid_retrieval, repository, service) |
| **Frontend** | `/graph` page |
| **Database** | Neo4j + SQL fallback |
| **Dependencies** | Neo4j (offline in production), PostgreSQL |
| **Runtime** | Knowledge graph runtime |
| **Owner** | AI |
| **Business Value** | Medium — relationship intelligence |
| **Status** | ⚠️ PARTIAL (Neo4j offline) |

---

## 17. Feature Store

| Attribute | Value |
|-----------|-------|
| **Name** | Feature Store |
| **Purpose** | Computed feature values (ICP, funding, hiring, growth, intent, expansion, revenue) |
| **Backend** | `domains/feature_store/`, `runtime/feature_store/` (7 score computers) |
| **Frontend** | Feature values displayed in company/employee views |
| **Database** | feature_values |
| **Dependencies** | PostgreSQL |
| **Runtime** | Feature computation pipeline |
| **Owner** | AI |
| **Business Value** | High — intelligence foundation |
| **Status** | ✅ FUNCTIONAL |

---

## 18. Entity Resolution

| Attribute | Value |
|-----------|-------|
| **Name** | Entity Resolution |
| **Purpose** | Golden record merging, conflict detection |
| **Backend** | `app/modules/entity_resolution/` (service, models) |
| **Frontend** | Admin golden-records viewer |
| **Database** | golden_records, entity_resolution_conflicts, entity_resolution_logs |
| **Dependencies** | PostgreSQL |
| **Runtime** | None |
| **Owner** | Data |
| **Business Value** | Medium — data quality |
| **Status** | ⚠️ FUNCTIONAL |

---

## 19. Webhooks & Integration Hub

| Attribute | Value |
|-----------|-------|
| **Name** | Webhooks & Integration Hub |
| **Purpose** | External system integration, webhook management |
| **Backend** | `app/modules/webhooks/`, `app/modules/integration_hub/` |
| **Frontend** | `/integrations` page |
| **Database** | webhook_subscriptions, webhook_deliveries, integration_connections |
| **Dependencies** | PostgreSQL, httpx |
| **Runtime** | Event runtime |
| **Owner** | Platform |
| **Business Value** | High — extensibility |
| **Status** | ⚠️ FUNCTIONAL BUT SSRF VULNERABILITY |

---

## 20. Notifications

| Attribute | Value |
|-----------|-------|
| **Name** | Notifications |
| **Purpose** | Real-time notifications via WebSocket |
| **Backend** | `domains/notifications/`, `app/routers/notifications.py` |
| **Frontend** | WebSocket connection in providers |
| **Database** | notifications |
| **Dependencies** | PostgreSQL, Redis, WebSocket |
| **Runtime** | Event runtime |
| **Owner** | Product |
| **Business Value** | Medium — user engagement |
| **Status** | ⚠️ PARTIAL |

---

## 21. Audit Trail

| Attribute | Value |
|-----------|-------|
| **Name** | Audit Trail |
| **Purpose** | Request-level audit logging |
| **Backend** | `app/modules/audit/` (middleware, models), `sdk/audit.py` |
| **Frontend** | `/admin/audit` page |
| **Database** | audit_logs |
| **Dependencies** | PostgreSQL |
| **Runtime** | None |
| **Owner** | Security |
| **Business Value** | High — compliance |
| **Status** | ✅ FUNCTIONAL |

---

## 22. Billing & Subscriptions

| Attribute | Value |
|-----------|-------|
| **Name** | Billing & Subscriptions |
| **Purpose** | Subscription management, usage metering |
| **Backend** | `app/modules/billing/` (service, state_machine, stripe_client) |
| **Frontend** | `/admin/billing` page |
| **Database** | subscriptions, usage_meters, invoices |
| **Dependencies** | PostgreSQL, Stripe (not connected) |
| **Runtime** | None |
| **Owner** | Platform |
| **Business Value** | Critical — revenue |
| **Status** | ⚠️ STATE MACHINE ONLY, NO STRIPE |

---

## 23. SSO/OAuth

| Attribute | Value |
|-----------|-------|
| **Name** | SSO/OAuth |
| **Purpose** | Single sign-on via Google, Microsoft, GitHub, SAML |
| **Backend** | `app/modules/sso/` |
| **Frontend** | SSO login buttons |
| **Database** | sso_connections |
| **Dependencies** | External OAuth providers |
| **Runtime** | None |
| **Owner** | Security |
| **Business Value** | Medium — enterprise feature |
| **Status** | ⚠️ PARTIAL |

---

## 24. MCP Server

| Attribute | Value |
|-----------|-------|
| **Name** | MCP Server |
| **Purpose** | AI agent interface to SalesOS capabilities |
| **Backend** | `mcp_server/` (server, tools, resources, salesos_client) |
| **Frontend** | None (API-only) |
| **Database** | None |
| **Dependencies** | FastMCP, SalesOS API |
| **Runtime** | MCP protocol |
| **Owner** | AI |
| **Business Value** | Medium — developer ecosystem |
| **Status** | ⚠️ BASIC BUT FUNCTIONAL |

---

## 25. Monitoring & Telemetry

| Attribute | Value |
|-----------|-------|
| **Name** | Monitoring & Telemetry |
| **Purpose** | System monitoring, usage telemetry, client-side metrics |
| **Backend** | `app/modules/monitoring/`, `app/modules/telemetry/`, `app/metrics/` |
| **Frontend** | `/monitoring` page; `src/lib/monitoring.ts` |
| **Database** | monitoring_events, telemetry_events |
| **Dependencies** | PostgreSQL, Redis |
| **Runtime** | Metrics collector, SLA monitor |
| **Owner** | Platform |
| **Business Value** | Medium — operational visibility |
| **Status** | ⚠️ FUNCTIONAL |

---

## 26. Communication Hub

| Attribute | Value |
|-----------|-------|
| **Name** | Communication Hub |
| **Purpose** | Email/calendar sync via Google OAuth |
| **Backend** | `app/modules/communication_hub/` (tasks, calendar_sync, email_service) |
| **Frontend** | Communication views in employee 360 |
| **Database** | email_accounts, calendar_events |
| **Dependencies** | Google OAuth, PostgreSQL |
| **Runtime** | Celery beat (15-min sync) |
| **Owner** | Product |
| **Business Value** | Medium — data enrichment |
| **Status** | ⚠️ FUNCTIONAL |

---

## 27. Data Fabric

| Attribute | Value |
|-----------|-------|
| **Name** | Data Fabric |
| **Purpose** | Data import, scraping, ETL pipelines |
| **Backend** | `runtime/data_fabric_runtime/`, scrapers (Balady, Taqeem, Najiz, Rega) |
| **Frontend** | Data fabric views |
| **Database** | scraper_runs, import_jobs |
| **Dependencies** | External scrapers, PostgreSQL |
| **Runtime** | Data fabric runtime |
| **Owner** | Data |
| **Business Value** | High — data acquisition |
| **Status** | ⚠️ SCRAPERS EXIST, ETL MOCK |

---

## 28. Resilience Harnesses

| Attribute | Value |
|-----------|-------|
| **Name** | Resilience Harnesses |
| **Purpose** | Load testing, chaos testing, DR drills, AI failover, LLM regression |
| **Backend** | `app/modules/chaos_resilience/`, `app/modules/load_slo/`, `app/modules/dr_drill/` |
| **Frontend** | `/monitoring` page |
| **Database** | chaos_runs, load_test_results, dr_drill_logs |
| **Dependencies** | PostgreSQL, Redis |
| **Runtime** | Various harnesses |
| **Owner** | Platform |
| **Business Value** | Medium — reliability |
| **Status** | ⚠️ FUNCTIONAL |

---

*This document catalogs every capability discovered in the source code. Theory vs implementation comparison is in 05_THEORY_VS_IMPLEMENTATION.md.*
