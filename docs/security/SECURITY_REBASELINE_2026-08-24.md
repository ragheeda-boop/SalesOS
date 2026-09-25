# SECURITY REBASELINE — 2026-08-24 (Phase C Fresh Audit)

> **The old 48/100 score is historical and must not be used as the current security score.**

---

## Methodology

Fresh audit against HEAD (`77bb684`) covering 10 security domains. Each domain scored 0-10 based on implementation maturity, defense-in-depth, and production readiness. Weighted scoring: critical domains (Auth, Multi-tenancy, AI Security) weighted 1.5x.

## Scoring Rubric

| Score | Meaning |
|:-----:|---------|
| 10 | Production-grade, defense-in-depth, no known gaps |
| 8-9 | Production-grade with minor concerns |
| 6-7 | Mostly production-grade, some gaps need closure |
| 4-5 | Partially production-grade, significant gaps |
| 2-3 | Not production-ready, major gaps |
| 0-1 | Missing or critically broken |

---

## Findings by Domain

### 1. Authentication — 9/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| RS256 JWT with RSA-4096 | OK | `identity/jwbs.py` — asymmetric, encrypted at rest |
| bcrypt password hashing (async) | OK | `identity/service.py:40-48` — 12-char min + complexity |
| Account lockout (5 attempts / 15 min) | OK | `identity/service.py:703-760` |
| Refresh token rotation + reuse detection | OK | `identity/service.py:303-345` |
| Cookie security (httponly, samesite=strict, secure) | OK | `identity/router.py:61-119` |
| **Legacy HS256 utility in sdk/security.py** | LOW | `sdk/security.py:27-36` — if accidentally used, tokens forgeable |
| **SSO auto-provisioning creates tenants without approval** | MEDIUM | `sso/service.py:153-190` — any Google user can create tenant |

**Score rationale:** Strong authentication with lockout, rotation, and RS256. SSO auto-provisioning and legacy HS256 are concerns but not critical.

### 2. Authorization (RBAC) — 7/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| Role hierarchy: admin > manager > user > auditor | OK | `dependencies.py:91-101` |
| 37 resources in admin role | OK | `sdk/permissions.py` |
| PermissionEnforcer.check() with exceptions | OK | `sdk/permissions.py` |
| **Role hierarchy duplicated in 2 files** | LOW | `dependencies.py:95` vs `router.py:458` |
| **Inconsistent RBAC enforcement across routers** | MEDIUM | Many domain routers only check auth+tenant, not fine-grained RBAC |
| **No dynamic role/permission configuration** | LOW | All roles are static defaults |

**Score rationale:** Fixed-role RBAC is solid for the current scope. Inconsistent enforcement and no custom roles limit flexibility.

### 3. Multi-tenancy / RLS — 9/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| 100 migrations, 86+ tables with RLS | OK | `alembic/versions/` |
| GUC pinning via `set_config('app.tenant_id')` | OK | `database.py:263-266` |
| Dual-engine (app role RLS / owner BYPASSRLS) | OK | `database.py` — properly gated |
| Cross-tenant impersonation blocked | OK | `middleware.py:303-308` |
| 3 newly fixed tables verified (approval_requests, llm_cost_entries, tenant_llm_budgets) | OK | Migration `i3j4k5l6m7n8` |
| Tenant IDOR protection on /tenants endpoint | OK | `identity/router.py:205-225` |
| **owner_engine bypasses RLS by design** | INFO | Only used for DDL and login probe |

**Score rationale:** Excellent multi-tenancy. Dual-engine approach is well-documented. All known RLS gaps fixed.

### 4. AI Security — 8/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| EvidencePack PII stripping (names, emails, phones never leave DB) | OK | `research_evidence.py:84-111` |
| Value banding (<100K, 100K-1M, >1M) | OK | `research_evidence.py:69-81` |
| Guardrails PII scrubbing (6 pattern types) | OK | `guardrails.py:56-138` |
| PolicyGate 5-layer enforcement | OK | `policy_gate.py:139-232` |
| ReliableProvider (timeout, retry, circuit breaker) | OK | `reliability.py:156-348` |
| DB-backed cost tracking with atomic budget | OK | `cost_tracker.py:167-249` |
| AI observability (Prometheus-ready) | OK | `observability.py` |
| RAG tenant isolation (GUC + explicit filters) | OK | `retrieval.py:62,126,299` |
| **Regex PII scrubber acknowledged incomplete** | LOW | `guardrails.py:103-104` — "Not Production GO by itself" |
| **`retrieve_by_source()` lacks tenant_id filter** | LOW | `retrieval.py:169-213` — internal call only |

**Score rationale:** Strong AI security with defense-in-depth. PII scrubbing is regex-based but supplemented by EvidencePack's structural PII stripping.

### 5. Infrastructure Security — 8/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| CORS from ALLOWED_HOSTS | OK | `middleware.py:61-80` |
| CSRF double-submit cookie | OK | `middleware.py:505-593` |
| SSRF 5-layer protection + DNS rebinding prevention | OK | `url_safety.py` |
| Identity-aware rate limiting (Redis-backed) | OK | `rate_limit.py`, `middleware.py:101-274` |
| Security headers (CSP, HSTS, X-Frame-Options) | OK | `middleware.py:346-400` |
| Secrets from env vars, min 32-char validation | OK | `config.py` |
| API keys SHA-256 hashed, constant-time verify | OK | `api_key_manager.py` |
| **`SALESOS_TESTING=true` disables CSRF + rate limiting** | MEDIUM | `middleware.py:538` — must not leak to prod |
| **Invite temp password in response body** | LOW | `identity/router.py:584` |
| **Forgot password returns token in dev mode** | LOW | `identity/router.py:786` |

**Score rationale:** Comprehensive infrastructure security. The SALESOS_TESTING bypass is the most significant concern.

### 6. Secrets Management — 9/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| All secrets from env vars (pydantic-settings) | OK | `config.py` |
| SECRET_KEY and JWT_SECRET_KEY min 32 chars | OK | `config.py:31-49` |
| No hardcoded secrets in source | OK | Grep verified |
| SSO tokens encrypted with Fernet (AES-128-CBC + HMAC) | OK | `sso/service.py:70-83` |
| **`.env` file committed to repo** | INFO | `.env` exists but contains dev-only values |

**Score rationale:** Production-grade secrets management. Environment-based with validation.

### 7. Rate Limiting — 8/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| Identity-aware tiers (authenticated/anonymous/identity/search) | OK | `middleware.py:101-274` |
| Redis-backed with in-memory fallback | OK | `rate_limit.py` |
| Per-key rate limiting for API keys | OK | `api_key_manager.py` |
| Redis operations bounded (2s timeout) | OK | `middleware.py` |
| **In-memory fallback not distributed** | LOW | Multiple instances have independent counters |
| **`SALESOS_TESTING=true` bypasses rate limiting** | MEDIUM | Same as CSRF concern |

**Score rationale:** Production-grade for single-instance. Multi-instance requires Redis (which is deployed).

### 8. CSRF Protection — 8/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| Double-submit cookie pattern | OK | `middleware.py:505-593` |
| Enforced on all state-changing methods | OK | POST/PUT/PATCH/DELETE |
| Public paths exempted correctly | OK | register, login, refresh, etc. |
| API keys do NOT bypass CSRF | OK | Documented as PROD-W5-001 |
| **Test mode bypass exists** | MEDIUM | `SALESOS_TESTING=true` |

**Score rationale:** Solid CSRF implementation. The test bypass is the only concern.

### 9. SSRF Protection — 10/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| HTTPS-only enforcement | OK | `url_safety.py:84` |
| Credentials in URL rejected | OK | `url_safety.py:88-89` |
| Blocked hostnames (localhost, metadata endpoints) | OK | `url_safety.py:24-35` |
| DNS resolution + IP validation | OK | `url_safety.py:38-46` |
| IP pinning via custom httpcore backend | OK | `url_safety.py:132-202` |

**Score rationale:** Excellent. 5-layer protection including DNS rebinding prevention.

### 10. API Security — 8/10

| Finding | Severity | Evidence |
|---------|:--------:|----------|
| Body size limiting (10 MB) | OK | `middleware.py:14-76` |
| Health endpoints exposed (no auth needed) | OK | `main.py` — appropriate for health checks |
| OpenAPI docs behind auth | OK | Default FastAPI behavior |
| **Some domain routers lack explicit RBAC** | LOW | Inconsistent enforcement |
| **Version endpoint exposes schema_version** | INFO | `main.py:395-443` — useful for debugging |

**Score rationale:** Good API security posture. Minor inconsistency in RBAC enforcement.

---

## Scoring Calculation

| Domain | Score | Weight | Weighted |
|--------|:-----:|:------:|:--------:|
| Authentication | 9 | 1.5 | 13.5 |
| Authorization | 7 | 1.0 | 7.0 |
| Multi-tenancy/RLS | 9 | 1.5 | 13.5 |
| AI Security | 8 | 1.5 | 12.0 |
| Infrastructure Security | 8 | 1.0 | 8.0 |
| Secrets Management | 9 | 1.0 | 9.0 |
| Rate Limiting | 8 | 1.0 | 8.0 |
| CSRF Protection | 8 | 1.0 | 8.0 |
| SSRF Protection | 10 | 1.0 | 10.0 |
| API Security | 8 | 1.0 | 8.0 |
| **Total** | | **11.0** | **97.0** |
| **Score** | | | **97/110 = 88/100** |

---

## Comparison

| Metric | Old Score (2026-07-22) | New Score (2026-08-24) | Delta |
|--------|:----------------------:|:----------------------:|:-----:|
| Overall | 48/100 | **88/100** | +40 |
| Auth | Not scored separately | 9/10 | — |
| Multi-tenancy | Not scored separately | 9/10 | — |
| AI Security | Not scored separately | 8/10 | — |
| SSRF | Not scored separately | 10/10 | — |
| RLS gaps | 3 tables missing | 0 | Fixed |

## Top 5 Residual Risks

1. **SSO auto-provisioning** — any Google user can create a tenant (business logic decision needed)
2. **SALESOS_TESTING bypass** — if env var leaks to prod, CSRF + rate limiting disabled
3. **Legacy HS256 utility** — exists in sdk/security.py; must not be used by any production path
4. **Inconsistent RBAC enforcement** — some domain routers only check auth+tenant
5. **Regex PII scrubber incomplete** — acknowledged in code; defense-in-depth only

## Verdict

**Score: 88/100 — Production-grade with conditions.**

The conditions are:
1. `SALESOS_TESTING` must never be `true` in production/staging (add startup validation)
2. SSO auto-provisioning must be gated by admin approval or domain whitelist
3. Legacy HS256 utility must be removed or audited for callers
4. External pentest required before GA declaration
