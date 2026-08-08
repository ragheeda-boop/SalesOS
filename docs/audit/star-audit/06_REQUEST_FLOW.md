# 06 — REQUEST FLOW: Frontend to Database Trace

> Source: Source code tracing (Phase 6)
> Classification: IMPLEMENTATION ONLY

---

## 1. Typical Request Flow: Company Search

```
Frontend (Browser)
  │
  ├── User types in search box
  ├── useUnifiedSearch() hook triggered
  │
  ▼
Next.js Middleware (middleware.ts)
  │
  ├── Check cookie for access token
  ├── If missing → redirect to /login
  ├── If present → continue
  │
  ▼
API Client (src/lib/api/client.ts)
  │
  ├── Axios request interceptor
  ├── Attach Authorization: Bearer <token>
  ├── Attach X-Tenant-Id (from localStorage or JWT)
  ├── Attach X-CSRF-Token (from cookie)
  │
  ▼
Next.js Rewrite (next.config.js)
  │
  ├── /api/* → backend URL (API_REWRITE_URL)
  │
  ▼
FastAPI Middleware Stack (app/boot/middleware.py)
  │
  ├── RequestIDMiddleware → assigns X-Request-ID
  ├── RequestLoggingMiddleware → structured log
  ├── BodyCacheMiddleware → 10MB limit
  ├── SecurityHeadersMiddleware → CSP, HSTS, etc.
  ├── CsrfEnforcementMiddleware → validates X-CSRF-Token
  ├── RateLimitMiddleware → sliding window check
  ├── TenantContextMiddleware → resolves tenant from header/JWT
  │
  ▼
FastAPI Router (app/routers/search.py)
  │
  ├── Depends(verify_token) → JWT validation
  ├── Depends(require_permission("search:read")) → RBAC check
  │
  ▼
Search Runtime (runtime/search_runtime/)
  │
  ├── Multi-executor search
  ├── PostgresSearchRepository (pg_trigram)
  ├── PgVectorStore (vector similarity)
  ├── MeilisearchConnector (optional)
  │
  ▼
PostgreSQL Database
  │
  ├── SET app.tenant_id = '<tenant-uuid>' (via set_config)
  ├── RLS policy filters rows by tenant_id
  ├── SELECT with pg_trgm similarity + vector distance
  │
  ▼
Response Flow
  │
  ├── Results ranked by relevance
  ├── Cached in Redis (optional)
  ├── Returned to frontend
  ├── TanStack Query caches result
  └── UI renders search results
```

---

## 2. Authentication Flow

```
Login Request:
  Frontend → POST /api/v1/identity/login → Backend
  
  Backend:
  ├── Validate email/password (bcrypt)
  ├── Check brute force (5 attempts → 15min lockout)
  ├── Create JWT (RS256, JWKS)
  ├── Create refresh token family
  ├── Create device session
  ├── Publish event (best-effort, 2s timeout)
  └── Return {access_token, refresh_token, tenant_id}

Token Refresh:
  Frontend → POST /api/v1/identity/refresh → Backend
  
  Backend:
  ├── Find refresh token family
  ├── Check if compromised (reuse detection)
  ├── Rotate: new refresh token, revoke old
  ├── Create new access token
  └── Return {access_token, refresh_token}

Owner Login:
  Frontend → POST /api/v1/identity/owner/login → Backend
  
  Backend:
  ├── Separate audience validation (salesos-owner-platform)
  ├── No tenant_id in JWT
  ├── X-Tenant-Id header required for scoped operations
  └── Return {access_token, refresh_token}
```

---

## 3. Company CRUD Flow

```
Create Company:
  Frontend → POST /api/v1/companies → Backend
  
  Backend:
  ├── verify_token → JWT validation
  ├── require_role("admin" or "manager") → role check
  ├── require_permission("companies:create") → RBAC check
  ├── TenantContextMiddleware → pin tenant_id
  ├── CompanyService.create()
  │   ├── Validate input (Pydantic)
  │   ├── Generate embedding (OpenAI)
  │   ├── INSERT INTO companies (with tenant_id)
  │   └── Publish domain event
  └── Return 201 with company data

Read Company:
  Frontend → GET /api/v1/companies/{id} → Backend
  
  Backend:
  ├── verify_token → JWT validation
  ├── require_permission("companies:read") → RBAC check
  ├── TenantContextMiddleware → pin tenant_id
  ├── RLS policy filters by tenant_id
  ├── CompanyService.get(id)
  │   ├── SELECT * FROM companies WHERE id = ? AND tenant_id = ?
  │   └── Return company data
  └── Return 200 with company data

Search Companies:
  Frontend → GET /api/v1/companies?q=... → Backend
  
  Backend:
  ├── verify_token → JWT validation
  ├── require_permission("companies:read") → RBAC check
  ├── TenantContextMiddleware → pin tenant_id
  ├── RLS policy filters by tenant_id
  ├── PostgresSearchRepository.search()
  │   ├── SELECT * FROM companies
  │   ├── WHERE tenant_id = ?
  │   ├── AND name % ? (pg_trgm similarity)
  │   ├── ORDER BY similarity DESC
  │   └── LIMIT 20
  └── Return 200 with search results
```

---

## 4. AI Copilot Flow (When Enabled)

```
Copilot Query:
  Frontend → POST /api/v1/copilot/query → Backend
  
  Backend:
  ├── verify_token → JWT validation
  ├── Feature gate: feature_ai_copilot must be True
  ├── CopilotService.query()
  │   ├── Detect language (Arabic/English)
  │   ├── GroundingService.retrieve_context()
  │   │   ├── Query Postgres (companies, contacts, opportunities)
  │   │   └── Query Neo4j (relationships)
  │   ├── Execute CopilotTool (SearchCompaniesTool)
  │   │   └── PostgresSearchRepository.search()
  │   ├── Guardrails.check()
  │   │   ├── Prompt injection detection
  │   │   ├── PII scrubbing
  │   │   └── Input sanitization
  │   ├── Call OpenAI API (GPT-4o-mini)
  │   ├── Validate output (JSON schema)
  │   └── Record telemetry
  └── Return response with tool calls + answer
```

---

## 5. Middleware Security Stack (Order)

```
1. RequestIDMiddleware          → X-Request-ID
2. RequestLoggingMiddleware     → Structured log
3. BodyCacheMiddleware          → 10MB limit
4. SecurityHeadersMiddleware    → CSP, HSTS, X-Frame-Options
5. CsrfEnforcementMiddleware    → CSRF token validation
6. RateLimitMiddleware          → Sliding window rate limit
7. TenantContextMiddleware      → Tenant resolution + pinning
```

---

## 6. Database Connection Flow

```
Request arrives:
  ├── get_db() dependency
  ├── Checkout connection from pool (bounded: 8s)
  ├── Create AsyncSession
  ├── apply_tenant_guc()
  │   └── SET LOCAL app.tenant_id = '<uuid>' (via set_config)
  ├── Yield session to route handler
  ├── Route handler executes
  ├── Session commits (bounded: 10s)
  ├── Session closes
  └── Connection returned to pool

On timeout:
  ├── abort_db_session() called
  ├── Force-terminates asyncpg connection
  └── Prevents pool poisoning
```

---

*This document traces the actual request flows through the codebase. Security details are in 07_SECURITY_COMPARISON.md.*
