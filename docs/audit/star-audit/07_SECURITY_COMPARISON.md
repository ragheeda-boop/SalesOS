# 07 — SECURITY MODEL: Documented vs Implemented

> Source: Cross-referencing security documentation with code (Phase 7)
> Classification: VERIFIED, ARCHITECTURAL DRIFT, DOCUMENTATION ONLY

---

## Executive Summary

The security foundation is **surprisingly strong** in code — RS256 JWT, refresh rotation, brute force protection, CSRF, rate limiting, RBAC, security headers, AI guardrails. However, **critical gaps exist**: tenant isolation unverified in production, Decision Center IDOR, webhook SSRF, and CSRF bypass via API key.

---

## 1. Authentication

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| JWT Algorithm | RS256 | RS256 hardcoded, HS256 rejected | ✅ VERIFIED |
| JWKS | RSA key management | RSA-4096 JWKS with rotation | ✅ VERIFIED |
| Refresh Rotation | Token rotation with reuse detection | Full implementation with family tracking | ✅ VERIFIED |
| Device Sessions | Per-device tracking | DeviceSession model with revocation | ✅ VERIFIED |
| Token Blacklist | JTI-based revocation | TokenBlacklist model | ✅ VERIFIED |
| Brute Force | Account lockout | 5 attempts → 15min lockout, bilingual messages | ✅ VERIFIED |
| Password Reset | Token-based with expiry | SHA-256 hash, 1-hour expiry | ✅ VERIFIED |
| SSO/OAuth | Google, Microsoft, GitHub, SAML | Module exists but partial | ⚠️ PARTIALLY IMPLEMENTED |

**Assessment:** Authentication is **production-grade**. The RS256 enforcement, refresh rotation with reuse detection, and brute force protection are world-class implementations.

---

## 2. Authorization

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| RBAC | Role-based access | 4 roles, 27 resources, 7 actions | ✅ VERIFIED |
| Role Hierarchy | admin > manager > user > auditor | Hierarchy enforced in code | ✅ VERIFIED |
| Permission Enforcer | Centralized permission checks | PermissionEnforcer.check() | ✅ VERIFIED |
| Owner Platform | Separate admin auth | Separate audience, separate auth module | ✅ VERIFIED |
| Entitlements | Plan-based feature gating | 4 tiers, domain gating, quota enforcement | ✅ VERIFIED |

**Assessment:** Authorization is **production-grade**. RBAC, entitlements, and plan-based gating are well-implemented.

---

## 3. Tenant Isolation

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| Row-level Security | RLS on every tenant-scoped table | Dual-engine pattern, ContextVar pinning | ✅ VERIFIED (in code) |
| 72/77 tables with tenant_id | Documented | Verified in code | ✅ VERIFIED |
| Tenant GUC | `app.tenant_id` via `set_config()` | Implemented (never SET LOCAL — DEC-085) | ✅ VERIFIED |
| Cross-tenant header mismatch | 403 on mismatch | TenantContextMiddleware fail-closed | ✅ VERIFIED |
| Cross-tenant regression testing | Mandatory merge gate | Not implemented | ❌ NOT IMPLEMENTED |
| Support impersonation | Time-boxed, tenant-consented | Not implemented | ❌ NOT IMPLEMENTED |
| **Production verification** | **Expected** | **UNVERIFIED — single shared tenant in prod** | 🔴 ARCHITECTURAL DRIFT |

**Assessment:** The tenant isolation **architecture is production-grade** but **unverified in production**. The single shared tenant in production means cross-tenant isolation has never been tested with real data.

---

## 4. CSRF Protection

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| Double-submit pattern | Documented | X-CSRF-Token header + cookie matching | ✅ VERIFIED |
| Public path exemptions | Documented | Login, register, refresh, webhook exempt | ✅ VERIFIED |
| Auto-retry on 403 | Documented | Frontend retries with fresh token | ✅ VERIFIED |
| **API key bypass** | **Not documented** | **X-API-Key header bypasses CSRF** | 🔴 ARCHITECTURAL DRIFT |

**Assessment:** CSRF is **production-grade** except for the API key bypass, which is a **P0 security vulnerability** (DEC-127).

---

## 5. Rate Limiting

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| Sliding window | Documented | Redis-backed with in-memory fallback | ✅ VERIFIED |
| Identity-aware | Documented | IP+tenant+user+path bucket | ✅ VERIFIED |
| Tiered limits | Documented | Configurable per endpoint category | ✅ VERIFIED |

**Assessment:** Rate limiting is **production-grade**.

---

## 6. Security Headers

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| CSP | Documented | Strict CSP with docs relaxation | ✅ VERIFIED |
| HSTS | Documented | Included in SecurityHeadersMiddleware | ✅ VERIFIED |
| X-Frame-Options | Documented | DENY | ✅ VERIFIED |
| X-Content-Type-Options | Documented | nosniff | ✅ VERIFIED |
| XSS Protection | Documented | Included | ✅ VERIFIED |
| Permissions-Policy | Documented | Camera/mic/geo disabled | ✅ VERIFIED |

**Assessment:** Security headers are **production-grade**.

---

## 7. Known Security Vulnerabilities

### P0 — Critical

| ID | Vulnerability | Status | Impact |
|----|--------------|--------|--------|
| S01 | DB Session Factory not wired → middleware no-op | OPEN | Entitlement/quota/API-key middleware are bypasses |
| S02 | Tenant isolation fails open — AsyncSession singletons with BYPASSRLS | OPEN | Cross-tenant data access possible |
| S03 | Decision Center IDOR — no tenant_id filter | OPEN | Cross-tenant read/write on decisions |
| S04 | Webhook SSRF — httpx posts to user URLs with no allowlist | OPEN | Server-side request forgery |
| S05 | Knowledge Graph SQL without tenant filters | OPEN | Cross-tenant graph data access |
| CSRF-01 | CSRF bypass via X-API-Key header | OPEN | CSRF protection bypassed |

### P1 — High

| ID | Vulnerability | Status | Impact |
|----|--------------|--------|--------|
| FE-01 | Access token in localStorage (XSS vulnerable) | OPEN (httpOnly mode OFF by default) | Token theft via XSS |
| AUTH-01 | Owner Platform admin routes return 401 for ALL | OPEN | Owner console non-functional |
| AUTH-02 | Both test accounts share same tenant | OPEN | Tenant isolation inconclusive |

---

## 8. AI Security

| Dimension | Documented | Implemented | Classification |
|-----------|-----------|-------------|----------------|
| Prompt Injection | Documented | 20+ harmful patterns detected | ✅ VERIFIED |
| PII Scrubbing | Documented | Emails, phones, national ID, IBAN, credit cards | ✅ VERIFIED |
| Input Sanitization | Documented | Special tokens, escape sequences stripped | ✅ VERIFIED |
| Output Validation | Documented | JSON schema validation, confidence bounds | ✅ VERIFIED |
| Rate Limiting | Documented | Per-tenant, per-model | ⚠️ PARTIALLY IMPLEMENTED |
| Budget Caps | Documented | Cost tracker exists | ⚠️ PARTIALLY IMPLEMENTED |
| Hallucination Check | Documented | LLM-as-judge | ❌ NOT IMPLEMENTED |
| Human-in-the-Loop | Documented | Not implemented | ❌ NOT IMPLEMENTED |

**Assessment:** AI guardrails are **production-grade** for input/output safety. Governance and monitoring are partial.

---

## 9. Overall Security Assessment

| Area | Score | Notes |
|------|-------|-------|
| Authentication | 9/10 | World-class RS256 + refresh rotation |
| Authorization | 8/10 | RBAC + entitlements solid |
| Tenant Isolation | 5/10 | Architecture solid; unverified in production |
| CSRF | 7/10 | Good pattern; API key bypass is P0 |
| Rate Limiting | 9/10 | Production-grade |
| Security Headers | 9/10 | Comprehensive |
| AI Security | 7/10 | Guardrails strong; governance partial |
| **Overall** | **7/10** | **Strong foundation; critical gaps in tenant isolation and SSRF** |

---

*This comparison reveals the security reality. Drift analysis is in 11_ARCHITECTURAL_DRIFT.md.*
