# SalesOS Deep Security Audit — Architecture & Vulnerability Report

> **Date:** 2026-07-13
> **Auditor:** Security Architect (automated + manual deep review)
> **Scope:** Full-stack — identity, SSO, API keys, audit, middleware, JWT, RBAC, secrets, dependencies, OWASP Top 10
> **Method:** READ-ONLY static analysis of every security-relevant file in the codebase
> **Repository:** `salesos` (backend + frontend + infra + docs)

---

## Executive Summary

| Category | Status | Critical | High | Medium | Low |
|----------|--------|----------|------|--------|-----|
| Authentication | 🟡 Needs hardening | 0 | 1 | 3 | 2 |
| Authorization / RBAC | 🟢 Solid | 0 | 0 | 0 | 1 |
| Middleware Security | 🟢 Strong | 0 | 0 | 1 | 1 |
| Input Validation | 🟢 Good | 0 | 0 | 2 | 0 |
| Secrets Management | 🟢 Clean | 0 | 0 | 1 | 2 |
| API Security Posture | 🟢 Mostly secured | 0 | 0 | 1 | 1 |
| OWASP Top 10 | 🟢 7/10 categories scored green | 0 | 1 | 3 | 1 |
| Dependency Security | 🟢 CI/CD + pip-audit in place | 0 | 0 | 0 | 0 |
| Data Encryption | 🟡 Partial | 0 | 1 | 1 | 0 |
| Infrastructure Security | 🟢 Good | 0 | 0 | 1 | 0 |
| Incident Response | 🟡 Immature | 0 | 1 | 1 | 0 |

**Overall: CONDITIONAL PASS for GA** — 0 critical, 4 high-severity issues must be addressed before production. 12 medium-severity issues recommended for sprint backlog.

---

## 1. Authentication Architecture

### 1.1 JWT Token Flow

| Property | Value | Assessment |
|----------|-------|-----------|
| Algorithm | HS256 (symmetric) | ⚠️ **HIGH** — All services share one secret; no key rotation infrastructure; symmetric signing prevents zero-trust service-to-service auth |
| Access token expiry | 30 min | ✅ Adequate |
| Refresh token expiry | 7 days | ✅ Adequate |
| Token type enforcement | `"type": "access"` / `"type": "refresh"` checked at decode | ✅ Good — prevents token type confusion |
| Audience validation | `"aud": "salesos-api"` verified at decode | ✅ Good |
| Issuer validation | `"iss": "salesos"` set but NOT verified | ⚠️ **MEDIUM** — Issuer is set in payload but `decode_access_token` does not validate the `iss` claim |
| JTI-based revocation | SHA-256 hashed JTI stored in blacklist | ✅ Good — prevents replay after logout |
| Refresh rotation | Single-use with reuse detection | ✅ Excellent — reuse marks entire family compromised + revokes all sessions |

**Evidence — `service.py:49-61`:**
```python
def create_access_token(user_id: str, tenant_id: str, jti: str | None = None) -> str:
    expire = _now() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id, "tenant_id": tenant_id, "jti": jti or secrets.token_urlsafe(16),
        "exp": expire, "iat": _now(), "type": "access", "iss": "salesos", "aud": "salesos-api",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

**Evidence — `service.py:79-89` (missing `iss` validation):**
```python
def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], audience="salesos-api")
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    return payload  # NOTE: `iss` claim not validated
```

**Finding H-1: JWT uses HS256 symmetric signing** — In a multi-service architecture, every service that needs to verify tokens must possess the same JWT_SECRET_KEY. This creates a lateral movement target. A compromise of any service exposes the signing key. **Recommendation:** Migrate to RS256/ES256 with public-key verification at the gateway; services behind the gateway use the opaque token or pass claims via headers.

**Finding M-1: Issuer claim (`iss`) not validated** — The `decode_access_token` function does not validate the `iss` claim. An attacker with knowledge of the JWT secret could craft tokens with arbitrary issuers. **Recommendation:** Add `iss="salesos"` to the `jwt.decode()` options parameter.

### 1.2 API Key Authentication

| Property | Value | Assessment |
|----------|-------|-----------|
| Key format | `sos_` + 64 hex chars (68 chars total) | ✅ Good entropy |
| Storage | bcrypt hash (via passlib) | ✅ Strong hashing |
| Key prefix | First 10 chars (`sos_xxxxxx`) stored in `key_prefix` column | ⚠️ **MEDIUM** — Prefix-based lookup to reduce keyspace enables attacker enumeration of key prefixes |
| Expiry | Per-key configurable; default 365 days | ⚠️ **LOW** — Default 1 year is long; recommend 90-day rotation |
| Revocation | Soft-delete via `is_revoked` flag | ✅ Good |
| Middleware position | Runs BEFORE JWT auth — only evaluated when no Bearer header present | ✅ Correct ordering |
| Last-used tracking | `last_used_at` updated on each validation | ✅ Good for audit |

**Evidence — `api_keys/middleware.py:12-27`:**
```python
if api_key and not request.headers.get("Authorization", "").startswith("Bearer "):
    # Validates, sets request.state.api_key_authenticated etc.
```

**Finding M-2: API key prefix enumeration risk** — The `validate()` method queries `WHERE key_prefix == prefix` and then loops through results doing bcrypt comparison. An attacker who learns a valid prefix could send many requests with different suffixes, although the bcrypt cost makes this computationally expensive per-guess. **Recommendation:** Consider hashing the prefix or using a separate lookup table with a random lookup ID.

### 1.3 SSO / OAuth & SAML

| Supported | Implementation | Assessment |
|-----------|---------------|-----------|
| Google OAuth | ✅ `service.py` | Standard OAuth 2.0 flow; state parameter protected |
| Microsoft OAuth | ✅ `service.py` | Same flow as Google |
| GitHub OAuth | ✅ `service.py` | Includes email fetch from `/user/emails` |
| SAML 2.0 | ✅ `saml_service.py` | SP-initiated + IdP-initiated supported |

**Finding H-2: OAuth provider `access_token` and `refresh_token` stored in plaintext** — The `SSOConnection` model stores provider tokens in `Text` columns (`access_token`, `refresh_token`) without encryption. These are valid bearer tokens for the user's Google/Microsoft/GitHub account. If the database is compromised, all SSO provider tokens are exposed. **Recommendation:** Encrypt these columns with AES-256 using a key from Vault/KMS or encrypt the entire column with pgcrypto.

**Evidence — `sso/models.py:19-20`:**
```python
access_token: Mapped[str] = mapped_column(Text, nullable=True)
refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
```

**Finding M-3: SAML configuration stored in-memory only** — `_SAML_CONFIGS` dict is purged on server restart. SAML tenants must reconfigure after each deploy. **Recommendation:** Persist to database.

**Finding L-1: SAML `AuthnRequestsSigned="false"`** — The generated SP metadata sets `AuthnRequestsSigned="false"`. If the IdP expects signed requests, this will fail. **Recommendation:** Sign SAML authn requests.

**Finding L-2: SAML `validUntil` set to 365 days** — `validUntil` in metadata is set to 1 year from generation. IdPs should re-fetch metadata regularly, but a shorter validity is better practice. **Recommendation:** Reduce to 30 days.

### 1.4 Invite & Signup Flow

| Feature | Implementation | Assessment |
|---------|---------------|-----------|
| Invite tokens | `INVITE_TOKENS` in-memory dict | ⚠️ **MEDIUM** — Lost on restart; no persistence |
| Verification tokens | `VERIFICATION_TOKENS` in-memory dict | ⚠️ **MEDIUM** — Same issue as invite |
| Password reset tokens | DB-persisted with SHA-256 hash, 1-hour expiry, single-use | ✅ Good |
| Signup creates new tenant | Auto-creates tenant with free plan | ✅ Good for self-service |

**Finding M-4: Invite and verification tokens stored in in-memory dicts** — Lost on server restart, meaning invited users and unverified users lose their ability to complete onboarding. **Recommendation:** Persist to database like password reset tokens.

**Evidence — `invite_service.py:20`:**
```python
INVITE_TOKENS: dict[str, dict[str, Any]] = {}
```

---

## 2. Authorization & RBAC Analysis

### 2.1 Role Hierarchy

| Role | Level | Access |
|------|-------|--------|
| `admin` | 3 | Full tenant access including billing |
| `manager` | 2 | Manage data and users |
| `user` / `api` | 1 | View and create data |
| `auditor` | 0 | Read-only |

**Evidence — `dependencies.py:63-73`:**
```python
role_hierarchy = {"admin": 3, "manager": 2, "user": 1, "api": 1, "auditor": 0}
```

### 2.2 Permission Registry

Permissions are defined in `sdk/permissions.py:84-121` with a hierarchical default roles system. Admin gets wildcard access; manager, user, api, and auditor have scoped permissions.

**Strengths:**
- ✅ `PermissionEnforcer.check()` raises `PermissionDeniedError` which is caught in dependency
- ✅ Tenant isolation enforced via `X-Tenant-Id` header matching JWT tenant claim
- ✅ Factory functions `require_role_dep()` and `require_permission_dep()` make route-level enforcement clean

**Issues:**

**Finding L-3: No scope-level enforcement** — The `Permission` dataclass has a `scope` field (`all`, `own`, `tenant`) but `PermissionEnforcer.check()` only checks `resource` + `action` and ignores scope. A user with `opportunity:read` can read ALL opportunities, not just their own. **Recommendation:** Implement scope-based filtering in the data layer.

**Finding L-4: Default `api` role has limited permissions** — The `api` role (hierarchy level 1) cannot create opportunities or read pipelines. If API keys are used by integrations, this may be too restrictive. By design but worth documenting.

### 2.3 Tenant Isolation

| Layer | Isolation | Evidence |
|-------|-----------|----------|
| Database | `tenant_id` column on all tables | ✅ Every model |
| API | `X-Tenant-Id` header matched against JWT | ✅ `dependencies.py:37-44` |
| Queries | Tenant-filtered in repositories | ✅ `repositories.py` |
| Neo4j | Tenant-tagged nodes | ✅ Per docs |
| Cache | `{tenant_id}:` key prefix | ✅ Per docs |

---

## 3. Middleware Security Analysis

### 3.1 Middleware Stack (in order)

| # | Middleware | File | Assessment |
|---|-----------|------|-----------|
| 1 | `CORSMiddleware` | `main.py:319` | ✅ Configurable origins from settings |
| 2 | `RequestIDMiddleware` | `common/middleware.py:177` | ✅ UUID generation |
| 3 | `RequestLoggingMiddleware` | `common/middleware.py:209` | ⚠️ See finding below |
| 4 | `SecurityHeadersMiddleware` | `common/middleware.py:124` | ✅ Comprehensive header set |
| 5 | `MetricsMiddleware` | `routers/metrics.py` | ✅ Prometheus scraping |
| 6 | `RateLimitMiddleware` | `common/middleware.py:28` | ✅ Tiered limits |
| 7 | `AuditMiddleware` | `audit/middleware.py:12` | ✅ All mutations logged |
| 8 | `ApiKeyMiddleware` | `api_keys/middleware.py:8` | ✅ Pre-JWT auth |

### 3.2 Security Headers Audit

| Header | Value | Assessment |
|--------|-------|-----------|
| `Content-Security-Policy` | Strict on API; relaxed for /docs | ⚠️ **MEDIUM** — `style-src 'unsafe-inline'` on strict CSP permits CSS injection risks |
| `X-Content-Type-Options` | `nosniff` | ✅ |
| `X-Frame-Options` | `DENY` | ✅ |
| `X-XSS-Protection` | `1; mode=block` | ⚠️ **LOW** — Deprecated; removed from modern browsers; can cause XSS auditors to sanitize incorrectly |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | ✅ |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | ✅ |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | ✅ Minimal surface |

**Finding L-5: `X-XSS-Protection` header is deprecated** — This non-standard header has been removed from Chrome, Edge, and Safari. It can enable cross-site scripting exploits in some configurations. **Recommendation:** Remove it or replace with `0` to disable the auditor.

### 3.3 Rate Limiting Architecture

Two-tier system:

| Tier | Component | Limit | Window |
|------|-----------|-------|--------|
| Global per-IP | `RateLimitMiddleware` (ASGI) | Varies by path category | 60s |
| Per-user per-resource | `rate_limit_dep()` (FastAPI dep) | Configurable | Configurable |

**Rate Limit Tiers (per minute):**

| Tier | Limit | Paths |
|------|-------|-------|
| Health | 120 | `/health`, `/docs`, `/redoc` |
| Identity | 10 | `/api/v1/identity/*` |
| Search | 30 | `/api/v1/search/*` |
| Authenticated | 100 | `/api/v1/*` with Bearer |
| Anonymous | 20 | `/api/v1/*` without Bearer |
| Default | 60 | All other paths |

**Strengths:**
- ✅ Redis-backed with in-memory fallback
- ✅ IP-keyed (prevents path-variation bypass)
- ✅ `Retry-After` header included
- ✅ Sliding window algorithm
- ✅ Stale entry cleanup every 300s

**Weakness:**
- Global per-IP rate limiter runs independent of the per-user rate limiter — an authenticated user could be limited by both tiers

### 3.4 Audit Middleware

**Evidence — `audit/middleware.py:28-29`:**
```python
if method in ("POST", "PUT", "PATCH", "DELETE") and path.startswith("/api/v1/") or response.status_code == 403:
```

**⚠️ Operator precedence bug:** The condition is parsed as `(method in (...) AND path.startswith(...)) OR (status_code == 403)` due to Python operator precedence. This means **every 403 response** (from any path including health checks) triggers audit logging. This is likely the intended behavior (log all access denials), but the `path.startswith("/api/v1/")` filter does NOT apply to 403 logging.

---

## 4. Input Validation & Sanitization Assessment

| Aspect | Implementation | Assessment |
|--------|---------------|-----------|
| Pydantic models | All request bodies use Pydantic with type validation | ✅ Good |
| Email validation | `EmailStr` from pydantic | ✅ |
| Password min length | 8 chars min | ⚠️ **MEDIUM** — No complexity requirements |
| Slug validation | `pattern=r"^[a-z0-9-]+$"` | ✅ Good |
| Phone validation | `pattern=r"^\+?[0-9\s\-()]{7,20}$"` | ✅ Good |
| SQL injection | SQLAlchemy parameterized queries throughout | ✅ |
| XML (SAML) | Standard `xml.etree.ElementTree` parsing | ⚠️ **MEDIUM** — No XML bomb/Billion Laughs protection |
| File uploads | Referenced in docs; no code path found | ⚠️ Cannot verify |
| eval/exec | 3 `__import__()` calls found | ⚠️ See finding below |

**Finding M-5: No password complexity requirements** — Password minimum is 8 characters but no requirement for uppercase, lowercase, digits, or special characters. Passwords like `aaaaaaaa` would pass validation. **Recommendation:** Add complexity validation in `UserCreate`, `PasswordChangeRequest`, `ResetPasswordRequest`, `AcceptInviteRequest`.

**Finding M-6: No XML bomb protection for SAML** — The SAML service parses XML from external IdPs without entity expansion protection or size limits. A malicious IdP could send a Billion Laughs attack causing DoS. **Recommendation:** Use `defusedxml` library or set parser limits.

**Finding L-6: `__import__` in production code** — Three instances in copilot.py and commercial.py. While not direct code injection vectors (they import known module paths), this is an anti-pattern that should be replaced with explicit imports. `commercial.py:426` and `commercial.py:450` are particularly egregious.

---

## 5. Secrets Management Audit

### 5.1 Secrets Scan Results

| Location | Finding | Severity | Status |
|----------|---------|----------|--------|
| Python source (non-test) | 0 hardcoded secrets | — | ✅ Clean |
| Test files | 21 matches with synthetic passwords (`TestP@ss123`, etc.) | None | ✅ Expected |
| `.env.example` | `CHANGE_ME` placeholders | None | ✅ By design |
| `.env.production.template` | `CHANGE_ME` placeholders | None | ✅ By design |
| `infra/k8s/secrets.yaml.template` | `CHANGE_ME` placeholders | None | ✅ By design |
| `backend/alembic.ini` | `CHANGE_ME` in DB URL | None | ✅ By design |

### 5.2 .gitignore Coverage

| Pattern | Status |
|---------|--------|
| `.env`, `.env.local`, `.env.*.local`, `.env.production`, `.env.staging` | ✅ Covered |
| `secrets.yaml`, `secrets.*` | ✅ Covered |
| `*.key`, `*.pem` | ✅ Covered |
| `credentials*` | ✅ Added (per security sweep) |
| `*.tfstate`, `.terraform/` | ✅ Covered |

**Finding M-7: Sentry DSN exposed in logs** — `main.py:67` logs the first 20 chars of the DSN: `logger.info(f"Sentry initialized: dsn={settings.sentry_dsn[:20]}...")`. While this is partial, DSNs are considered sensitive in some environments. **Recommendation:** Log only success/failure, not the DSN prefix.

### 5.3 Pre-Commit Config

The `.pre-commit-config.yaml` runs `ruff`, `mypy`, `prettier`, and basic hooks (`check-yaml`, `check-toml`, `check-json`). **Missing: No secrets scanner in pre-commit** (e.g., `detect-secrets`, `gitleaks`, `trufflehog`). The CI/CD pipeline catches these but pre-commit would provide earlier feedback.

**Finding M-8: No pre-commit secret scanning** — Secrets are caught at CI time (Trivy, Semgrep) but not at commit time. **Recommendation:** Add `detect-secrets` or `gitleaks` to pre-commit hooks.

---

## 6. OWASP Top 10 Assessment

| # | Category | Score | Assessment |
|---|----------|-------|-----------|
| A01 | Broken Access Control | 🟢 8/10 | RBAC enforced; tenant isolation across all layers; 3/48 routers intentionally unauthenticated |
| A02 | Cryptographic Failures | 🟡 6/10 | bcrypt for passwords ✅; HS256 JWT (symmetric) ⚠️; SSO tokens plaintext ⚠️; no key rotation |
| A03 | Injection | 🟢 8/10 | SQL parameterized throughout ✅; XML parsing without bomb protection ⚠️; `__import__` in code ⚠️ |
| A04 | Insecure Design | 🟢 7/10 | Token rotation with reuse detection ✅; no rate limiting on login/forgot-password ⚠️ |
| A05 | Security Misconfiguration | 🟢 7/10 | Security headers set ✅; debug mode disabled in prod docs ✅; `X-XSS-Protection` deprecated ⚠️ |
| A06 | Vulnerable Components | 🟢 8/10 | pip-audit in CI ✅; npm audit in CI ✅; Trivy container scan ✅; no SBOM validation for Python ⚠️ |
| A07 | Auth Failures | 🟡 6/10 | No account lockout ⚠️; no MFA ⚠️; password complexity weak ⚠️; token rotation excellent ✅ |
| A08 | Software & Data Integrity | 🟢 7/10 | Docker image tags pinned (not latest) ✅; no supply chain attestation for PyPI packages ⚠️ |
| A09 | Security Logging & Monitoring | 🟢 7/10 | Audit trail for all mutations ✅; Sentry integration ✅; structured logging ✅; no SIEM integration ⚠️ |
| A10 | SSRF | 🟢 8/10 | httpx used for OAuth token exchange (provider URLs hardcoded) ✅; no user-controlled URLs discovered |

### Detailed OWASP Findings:

**A04 — No rate limiting on login/password-reset endpoints:**
`POST /api/v1/identity/login` and `POST /api/v1/identity/forgot-password` have no endpoint-specific rate limiting beyond the global 10/min for identity paths. Brute-force attacks against login are feasible at 10 attempts per minute from a single IP, but distributed attacks would bypass.

**Recommendation:** Add progressive delays (`n` attempts = `2^n` seconds delay) or per-account lockout after 5 failed attempts.

**A07 — No account lockout mechanism:**
`authenticate()` in `service.py:370-390` has no failed-attempt counter. An attacker can make unlimited login attempts against an account (subject only to IP rate limiting).

**Recommendation:** Track failed attempts in `User` model (`failed_login_attempts`, `locked_until`) and implement exponential backoff.

**A07 — No MFA support:**
No TOTP, SMS, or WebAuthn implementation exists. All authentication is single-factor.

---

## 7. SQL Injection / XSS / CSRF Vulnerability Scan

### 7.1 SQL Injection
**Result: CLEAN** — All database queries use SQLAlchemy ORM parameterized queries or `text()` with bound parameters. No string concatenation of user input into SQL.

### 7.2 XSS (Cross-Site Scripting)
**Result: LOW RISK** — This is primarily an API backend. CSP headers restrict script sources. The `/docs` endpoints (Swagger) use a relaxed CSP but these are disabled in production (`docs_url=None` when `debug=False`).

### 7.3 CSRF (Cross-Site Request Forgery)

**Implementation:**
- CSRF token endpoint: `GET /api/v1/identity/csrf-token`
- Token stored in a non-httponly cookie (`csrf_token`)
- SameSite=Strict on cookies
- CORS restricted to ALLOWED_HOSTS

**Assessment:**
- ✅ CSRF token available for SPAs
- ✅ SameSite=Strict on session cookies
- ⚠️ **MEDIUM** — No CSRF middleware validates the token on state-changing requests. The `/csrf-token` endpoint generates and sets a cookie, but no middleware checks `X-CSRF-Token` header against the cookie. The infrastructure exists but the enforcement is missing.

**Finding M-9: CSRF token generation exists but no enforcement middleware** — The `GET /csrf-token` endpoint creates a CSRF token cookie, and `X-CSRF-Token` is whitelisted in CORS headers. However, there is no middleware or dependency that validates the `X-CSRF-Token` header against the cookie on POST/PUT/PATCH/DELETE requests. **Recommendation:** Add CSRF validation middleware or dependency.

### 7.4 WebSocket Token Security
The WebSocket endpoint `notifications/ws` passes the JWT as a URL query parameter (`?token=...`). This is standard for WebSocket authentication (bearer headers aren't supported in the WebSocket handshake), but it exposes the token in server logs and proxy logs. The security audit script actively scans for this pattern and would flag it.

---

## 8. Dependency Security Audit

| Tool | Configured | Frequency | Findings |
|------|-----------|-----------|----------|
| `pip-audit` | ✅ CI/CD (`security-scan.yml`) | Weekly + on push | Reports via SARIF to GitHub Security tab |
| `npm audit` | ✅ CI/CD + local script | Weekly + on push | Moderate+ vulnerabilities flagged |
| `Trivy` (filesystem) | ✅ CI/CD | Weekly + on push | CRITICAL/HIGH/MEDIUM vulnerabilities |
| `Trivy` (IaC) | ✅ CI/CD | Weekly + on push | K8s config scanning |
| `Bandit` | ✅ CI/CD | Weekly + on push | Python SAST |
| `Semgrep` | ✅ CI/CD | Weekly + on push | Generic SAST |
| `SBOM` | ✅ CI/CD (SPDX-JSON) | Weekly | Backend + Frontend |

**Assessment: Comprehensive CI/CD pipeline.** No blocking issues. The weekly scan cadence is adequate for a pre-GA product.

**Finding L-7: No `pip-audit` or `safety` in pre-commit** — Dependency vulnerabilities are caught at CI time but developers could introduce vulnerable dependencies locally. **Recommendation:** Add `pip-audit` as a pre-commit hook.

---

## 9. Data Encryption Assessment

| State | Claimed | Actual | Assessment |
|-------|---------|--------|-----------|
| At Rest (Database) | AES-256 at disk level | Not verified in code — assumed infra-level | ⚠️ **HIGH** — No application-level field encryption |
| At Rest (Secrets) | Vault / K8s Secrets | Config values from env vars | ✅ Follows standard practice |
| At Rest (SSO Tokens) | Not mentioned | **Plaintext in database** | 🔴 **HIGH** — See Finding H-2 |
| In Transit (API) | TLS 1.3 | HSTS enforced ✅ | ✅ |
| In Transit (Inter-service) | TLS 1.3 | Not verified — Kafka/Redis/Neo4j URLs use non-TLS schemes | ⚠️ **MEDIUM** — Internal services not using TLS |
| Password hashing | bcrypt | ✅ Verified in `service.py` and `sdk/security.py` | ✅ |
| PII masking | Pseudonymization | `mask_pii()` utility exists but no evidence of usage in logs or analytics | ⚠️ Cannot verify |

**Finding H-3 (related to H-2): SSO provider tokens stored plaintext** — Covered above.

**Finding M-10: Internal service connections use non-TLS URLs** — Redis, Neo4j, Kafka, and Meilisearch URLs use non-encrypted schemes (`redis://`, `bolt://`, `kafka:9092`, `http://meilisearch`). In a Kubernetes environment this is acceptable if pod-to-pod traffic is within the CNI, but service mesh TLS (e.g., Istio mTLS) should be used. **Recommendation:** Enable TLS between services or use a service mesh with mTLS.

**Finding M-11: No application-level encryption for PII** — Sensitive fields like `phone` (User model), `email` (User model) are stored in plaintext. While the database may have disk-level encryption, this does not protect against application-level SQL injection or database admin access. **Recommendation:** For KSA PDPL compliance, consider encrypting PII fields at the application level.

---

## 10. API Security Posture — Every Router Checked

### 10.1 Router Authentication Summary

| Router | Auth Method | Status |
|--------|------------|--------|
| Identity (`/api/v1/identity`) | Route-level `Depends(verify_token)` where needed; login/register/forgot-password/refresh/csrf-token intentionally public | ✅ |
| SSO (`/api/v1/auth/sso/*`) | No router-level auth (correct — auth entry points) | ✅ |
| SAML (`/sso/saml/*`) | No router-level auth (correct — auth entry points) | ✅ |
| Demo (`/api/v1/demo`) | `GET /status` **NO AUTH** ⚠️; `GET /scenarios` requires auth; `POST /reset` requires admin | ⚠️ |
| Notifications REST (`/api/v1/notifications`) | Include-level **NO `_auth`** in main.py:659; route-level `Depends(get_current_tenant_id)` provides implicit auth | ⚠️ |
| All other routers (40+) | Include-level `dependencies=_auth` or router-level `Depends(verify_token)` | ✅ |

### 10.2 Intentionally Unauthenticated Endpoints (Verified)

| Endpoint | Reason | Risk |
|----------|--------|------|
| `GET /metrics` | Prometheus scraping | Low (internal network) |
| `GET /api/v1/demo/status` | Public demo status | **HIGH** — Exposes demo data availability to anyone |
| `POST /api/v1/auth/sso/{provider}` | SSO login initiation | None |
| `GET /api/v1/auth/sso/{provider}/callback` | SSO callback | None |
| `POST /sso/saml/login` | SAML login | None |
| `POST /sso/saml/callback` | SAML ACS | None |
| `POST /sso/saml/idp-initiated` | SAML IdP-initiated | None |
| `GET /sso/saml/metadata` | SAML metadata | None |
| `POST /api/v1/identity/register` | New user registration | None |
| `POST /api/v1/identity/login` | Login | None |
| `POST /api/v1/identity/refresh` | Token refresh | None |
| `POST /api/v1/identity/forgot-password` | Password reset request | None |
| `POST /api/v1/identity/reset-password` | Password reset | None |
| `GET /api/v1/identity/csrf-token` | CSRF token | None |

**Finding M-12: Demo status endpoint has no authentication** — `GET /api/v1/demo/status` exposes demo data availability without any auth check. In production, this should be disabled or require auth. **Recommendation:** Protect with `Depends(verify_token)`.

**Finding L-8: Notifications REST router include missing explicit `_auth`** — In `main.py:659`, the notifications router is included without `dependencies=_auth`. However, each route uses `get_current_tenant_id` / `get_current_user_id` which implicitly validates the token. The defense is present at the route level but defense-in-depth recommends router-level auth too.

---

## 11. Frontend Security

| Aspect | Assessment | Notes |
|--------|-----------|-------|
| CSP | Set by backend API (not SPA) | Backend API, so CSP protects API responses; frontend SPA needs its own CSP |
| Token storage | In-memory (not localStorage) assumed | Not verified in frontend code (out of scope for this audit) |
| CORS | `allow_credentials=True` with specific origins | ✅ |
| Cookie security | HttpOnly, Secure, SameSite=Strict | ✅ For refresh/CSRF cookies |

**Note:** Frontend SPA was not in scope for this deep audit. Recommendations:
- Ensure access tokens are stored in memory, never localStorage/sessionStorage
- Frontend should set CSP headers (via meta tag or response headers)
- Implement token refresh interceptor for 401 responses

---

## 12. Infrastructure Security

| Component | Assessment |
|-----------|-----------|
| Docker | Image tags pinned (version-based, not `latest`) ✅ |
| K8s Secrets | Template file with CHANGE_ME placeholders ✅ |
| CI/CD | Security gate pipeline (Trivy + Bandit + Semgrep + pip-audit + npm audit + SBOM) ✅ |
| Network policy | Not verified in audited files |
| Service Mesh | Not configured (internal traffic not encrypted) ⚠️ |

---

## 13. Security Incident Response Readiness

| Capability | Status | Notes |
|-----------|--------|-------|
| Audit logging | ✅ | All mutations logged; 90-day retention |
| Structured logging | ✅ | JSON logs with correlation IDs |
| Error monitoring | ✅ | Sentry integration |
| Alerting | 🔴 Not found | No PagerDuty/OpsGenie integration |
| Incident response playbook | 🔴 Not found | No runbook for security incidents |
| Token revocation | ✅ | API supports blacklisting JWT and revoking sessions |
| Session management | ✅ | Users can view/revoke all active sessions |
| API key rotation | ✅ | Keys can be revoked; new keys generated |

**Finding H-4: No incident response plan or alerting** — While the system has excellent forensic capabilities (audit logs, structured logging, Sentry), there is no security alerting pipeline (PagerDuty, OpsGenie, or similar) and no documented incident response plan. **Recommendation:** Create an incident response playbook and integrate alerting.

---

## 14. Security Debt Register

### HIGH Severity (Must fix before GA)

| ID | Finding | Location | Impact | Effort |
|----|---------|----------|--------|--------|
| SEC-H-01 | JWT uses symmetric HS256 — no key rotation, shared secret | `service.py:61` | Lateral movement after service compromise | 3 days |
| SEC-H-02 | SSO provider tokens stored in plaintext in database | `sso/models.py:19-20` | Full account compromise if DB breached | 2 days |
| SEC-H-03 | No encryption at rest for internal service connections | `config.py:36,27` | Data exposure in transit between services | 2 days |
| SEC-H-04 | No incident response plan or security alerting | N/A | Delayed detection of active breaches | 1 sprint |

### MEDIUM Severity (Fix within 2 sprints)

| ID | Finding | Location | Impact | Effort |
|----|---------|----------|--------|--------|
| SEC-M-01 | JWT `iss` claim not validated | `service.py:81` | Token forgery (requires key access) | 1 hour |
| SEC-M-02 | API key prefix enumeration possible | `api_keys/service.py:73-90` | Brute-force vector (limited by bcrypt) | 2 hours |
| SEC-M-03 | SAML config stored in-memory only | `saml_service.py:43` | Reconfiguration required after restart | 1 day |
| SEC-M-04 | Invite/verification tokens in-memory | `invite_service.py:20`, `signup_service.py:22` | Lost on restart; broken UX | 1 day |
| SEC-M-05 | No password complexity requirements | `schemas.py:26`, multiple | Weak passwords possible | 1 hour |
| SEC-M-06 | No XML bomb protection for SAML | `saml_service.py:150` | DoS via malicious IdP | 1 hour |
| SEC-M-07 | Sentry DSN logged at initialization | `main.py:67` | Partial DSN exposure in logs | 10 min |
| SEC-M-08 | No pre-commit secret scanner | `.pre-commit-config.yaml` | Secrets committed before CI catches them | 1 hour |
| SEC-M-09 | CSRF token generation without enforcement middleware | `router.py:409`, no middleware | CSRF attacks possible despite token | 4 hours |
| SEC-M-10 | Internal services use non-TLS URLs | `config.py` | Unencrypted inter-service traffic | 2 days |
| SEC-M-11 | No application-level PII encryption | Models | KSA PDPL risk for PII exposure | 3 days |
| SEC-M-12 | Demo status endpoint unauthenticated | `routers/demo.py:42` | Information disclosure | 30 min |

### LOW Severity (Backlog)

| ID | Finding | Location | Impact | Effort |
|----|---------|----------|--------|--------|
| SEC-L-01 | SAML authn requests not signed | `saml_service.py:85` | Interop issues with strict IdPs | 1 hour |
| SEC-L-02 | SAML metadata validUntil too long (365 days) | `saml_service.py:78` | Minor best-practice deviation | 10 min |
| SEC-L-03 | No scope-level RBAC enforcement | `permissions.py:128` | Overly broad read access | 3 days |
| SEC-L-04 | `api` role may be too restrictive | `permissions.py:113-116` | Integration limitations | Documentation |
| SEC-L-05 | `X-XSS-Protection` header deprecated | `common/middleware.py:166` | Minor; browser-side concern | 10 min |
| SEC-L-06 | `__import__` in production code | `copilot.py:84`, `commercial.py:426,450` | Anti-pattern | 1 hour |
| SEC-L-07 | No `pip-audit` in pre-commit | `.pre-commit-config.yaml` | Delayed vulnerability detection | 30 min |
| SEC-L-08 | Notifications router missing explicit `_auth` dependency | `main.py:659` | Defense-in-depth only | 10 min |

---

## 15. Summary of Strengths

1. **Refresh token rotation with reuse detection** is world-class — immediate family compromise on reuse, automatic session revocation, structured logging
2. **Tenant isolation** is enforced at every layer: database column, API header validation, query filtering
3. **Audit trail** covers all state-changing operations with structured data, pagination, filtering
4. **CI/CD security pipeline** is comprehensive: 7+ tools scanning weekly + on push, SBOM generation, SARIF reporting
5. **Security headers** are well-configured with proper CSP, HSTS, X-Frame-Options
6. **API key design** uses bcrypt hashing, prefix-based lookup, expiry, and revocation
7. **Password hashing** uses bcrypt throughout (not SHA-256 or MD5)
8. **Rate limiting** has Redis-backed tiered limits with in-memory fallback
9. **Device session management** allows users to view and revoke specific sessions
10. **Forgot-password** endpoint uses constant-time response ("If the email exists...") to prevent email enumeration

---

## 16. Critical Path — Before GA Launch

| # | Action | Severity | Owner | Timeline |
|---|--------|----------|-------|----------|
| 1 | Encrypt SSO provider tokens in database (AES-256) | HIGH | Backend | Before GA |
| 2 | Plan JWT algorithm migration to RS256 | HIGH | Architecture | Sprint +1 |
| 3 | Create incident response plan + alerting | HIGH | DevOps | Before GA |
| 4 | Add password complexity requirements | MEDIUM | Backend | Sprint +1 |
| 5 | Add login rate limiting per account (lockout) | MEDIUM | Backend | Sprint +1 |
| 6 | Add CSRF validation middleware | MEDIUM | Backend | Sprint +1 |
| 7 | Persist invite/verification tokens to database | MEDIUM | Backend | Sprint +1 |
| 8 | Validate `iss` claim in JWT decode | MEDIUM | Backend | 1 hour |
| 9 | Add MFA support planning | MEDIUM | Architecture | Sprint +2 |
| 10 | Protect demo status endpoint with auth | MEDIUM | Backend | 30 min |

---

*Audit completed: 2026-07-13*
*Next scheduled audit: 2026-08-13 (or post-GA launch)*
*Constitution reference: ENGINEERING_CONSTITUTION.md — Article 4 (Security)*
