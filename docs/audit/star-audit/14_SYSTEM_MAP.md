# 14 — SYSTEM MAP: Complete Architecture Diagram

> Source: Source code analysis (all phases)
> Classification: IMPLEMENTATION ONLY

---

## 1. High-Level System Architecture

```
+---------------------------------------------------------------------+
|                        CLIENTS                                        |
|  +----------+  +----------+  +----------+  +----------+             |
|  | Browser   |  | Mobile   |  | API      |  | MCP      |             |
|  | (Next.js) |  | (Future) |  | Consumer |  | Agent    |             |
|  +-----+----+  +-----+----+  +-----+----+  +-----+----+             |
|        |              |              |              |                  |
+--------+--------------+--------------+--------------+-----------------+
         |              |              |              |
         v              v              v              v
+---------------------------------------------------------------------+
|                     API GATEWAY                                       |
|  +--------------------------------------------------------------+   |
|  |  Next.js Middleware (Auth, CSRF, Tenant)                      |   |
|  |  -> API Rewrite (/api/* -> backend)                           |   |
|  +------------------------------+-------------------------------+   |
|                                  |                                   |
|  +------------------------------v-------------------------------+   |
|  |  FastAPI Middleware Stack                                     |   |
|  |  1. RequestID -> 2. Logging -> 3. BodyCache -> 4. Security  |   |
|  |  -> 5. CSRF -> 6. RateLimit -> 7. TenantContext              |   |
|  +------------------------------+-------------------------------+   |
+----------------------------------+-----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
|                     APPLICATION LAYER                                 |
|  +--------------------------------------------------------------+   |
|  |  FastAPI App (app/main.py)                                    |   |
|  |  |-- 70+ Routers (app/routers/, app/modules/)                |   |
|  |  |-- GraphQL (app/graphql/)                                   |   |
|  |  +-- MCP Server (mcp_server/)                                 |   |
|  +------------------------------+-------------------------------+   |
+----------------------------------+-----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
|                     DOMAIN LAYER                                      |
|  +--------------------------------------------------------------+   |
|  |  19 Domains (domains/)                                        |   |
|  |  |-- ai, analytics, commercial, copilot                       |   |
|  |  |-- decision, decision_center, employee                      |   |
|  |  |-- feature_store, marketplace, notifications                |   |
|  |  |-- rag, revenue, scoring, search                            |   |
|  |  +-- timeline, ubom, workflow                                 |   |
|  +------------------------------+-------------------------------+   |
+----------------------------------+-----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
|                     RUNTIME LAYER                                     |
|  +--------------------------------------------------------------+   |
|  |  31 Engines (runtime/)                                        |   |
|  |  |-- event, feature_store, search, knowledge_graph            |   |
|  |  |-- decision, policy, recommendation, context                |   |
|  |  |-- activity, timeline, data_fabric, nba                     |   |
|  |  |-- pipeline_analytics, capability, workflow                 |   |
|  |  |-- agent, memory, simulation, action                        |   |
|  |  |-- form, ui_schema, widget, plugin_sandbox                  |   |
|  |  +-- extension, ux, scheduler                                 |   |
|  +------------------------------+-------------------------------+   |
+----------------------------------+-----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
|                     SDK LAYER                                         |
|  +--------------------------------------------------------------+   |
|  |  30 Packages (sdk/)                                           |   |
|  |  |-- security, permissions, database, audit                   |   |
|  |  |-- cache, events, telemetry, vector                         |   |
|  |  |-- pagination, graph, search, queue                         |   |
|  |  |-- capability_registry, feature_registry                    |   |
|  |  |-- agent_sdk, backend_sdk, frontend_sdk                     |   |
|  |  |-- commercial, company_sdk, integration_sdk                 |   |
|  |  +-- plugin_sdk, scoring, theme_sdk, widget_sdk               |   |
|  +------------------------------+-------------------------------+   |
+----------------------------------+-----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
|                     INFRASTRUCTURE                                    |
|  +----------+  +----------+  +----------+  +----------+             |
|  |PostgreSQL |  |  Redis   |  |  Neo4j   |  |  Kafka   |             |
|  | (Primary) |  | (Cache)  |  | (Graph)  |  | (Events) |             |
|  | 72+ tables|  | Rate lim |  | Offline  |  | In-memory|             |
|  | RLS       |  | Session  |  | in prod  |  | fallback |             |
|  +----------+  +----------+  +----------+  +----------+             |
|                                                                      |
|  +----------+  +----------+  +----------+                            |
|  |Meilisearch|  |  Celery  |  |  Sentry  |                            |
|  | (Search)  |  | (Tasks)  |  | (Errors) |                            |
|  +----------+  +----------+  +----------+                            |
+---------------------------------------------------------------------+
```

---

## 2. Data Flow

```
User Action -> Browser -> Next.js Middleware -> API Rewrite -> FastAPI Middleware Stack
    -> Router -> Domain Service -> Runtime Engine -> SDK Utility -> Database
    -> Response -> Frontend State (TanStack Query) -> UI Render
```

---

## 3. Security Layers

```
Layer 1: Next.js Middleware (route gating, cookie check)
Layer 2: FastAPI CSRF (double-submit pattern)
Layer 3: FastAPI Rate Limit (Redis-backed sliding window)
Layer 4: FastAPI Tenant Context (ContextVar pinning)
Layer 5: FastAPI Auth (JWT RS256 verification)
Layer 6: FastAPI RBAC (role + permission check)
Layer 7: PostgreSQL RLS (row-level security)
```

---

## 4. AI Stack

```
+-------------------------------------+
|  Frontend: Copilot Panel, AI Insights|
|  (Feature-gated: feature_ai_copilot) |
+-------------------------------------+
|  Backend: Copilot Service            |
|  |-- SearchCompaniesTool (only)      |
|  |-- Grounding Service               |
|  |-- Guardrails (injection, PII)     |
|  +-- OpenAI API (GPT-4o-mini)        |
+-------------------------------------+
|  Intelligence Layer                  |
|  |-- Providers (OpenAI only)         |
|  |-- Prompts (templates)             |
|  |-- RAG Pipeline                    |
|  +-- Cost Tracker                    |
+-------------------------------------+
|  Storage                             |
|  |-- pgvector (embeddings)           |
|  |-- Neo4j (graph) -- OFFLINE        |
|  +-- PostgreSQL (memory)             |
+-------------------------------------+
```

---

## 5. Frontend Architecture

```
+---------------------------------------------------------------------+
|  Next.js 15 App Router                                               |
|  +--------------------------------------------------------------+   |
|  |  93+ Pages                                                     |   |
|  |  |-- Auth (3): login, register, admin/login                    |   |
|  |  |-- Dashboard (75): companies, employees, pipeline, etc.      |   |
|  |  +-- V3 (18): workspace shell redesign                         |   |
|  +------------------------------+-------------------------------+   |
|                                  |                                   |
|  +------------------------------v-------------------------------+   |
|  |  37 API Client Modules (src/lib/api/)                        |   |
|  |  40 React Query Hooks (src/lib/hooks/)                       |   |
|  |  6 Mutation Hooks                                             |   |
|  +------------------------------+-------------------------------+   |
|                                  |                                   |
|  +------------------------------v-------------------------------+   |
|  |  21 @salesos/* Packages                                       |   |
|  |  |-- ui (31 primitives), tokens, design-language              |   |
|  |  |-- runtime (9 subsystems), hooks, forms                     |   |
|  |  |-- search, workspace, platform (STUB), widget-sdk           |   |
|  |  +-- charts, icons, theme, config, renderer                   |   |
|  +--------------------------------------------------------------+   |
+---------------------------------------------------------------------+
```

---

*This document provides the complete system map. The CEO report is in 15_CEO_REALITY_REPORT.md.*
