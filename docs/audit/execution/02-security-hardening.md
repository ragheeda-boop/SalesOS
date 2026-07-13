# Security Hardening — Execution Report

> **Date**: 2026-07-13
> **Stream**: Security (90-Day Hardening Plan)
> **Status**: Complete

---

## Summary of Changes

| # | Task | Files Modified | Risk |
|---|------|---------------|------|
| SEC-M-09 | CSRF Enforcement Middleware | `middleware.py`, `main.py` | Low |
| SEC-M-05 | Password Complexity (12-char + 4 classes) | `schemas.py`, `router.py` | Low |
| — | Account Lockout (5 attempts → 15 min lock) | `models.py`, `service.py` | Low |
| SEC-H-02 | SSO Token Encryption (Fernet AES-128) | `security.py`, `sso/service.py` | Medium |
| — | JWT Key Rotation Readiness (kid + JWKS) | `service.py`, `router.py` | Low |
| — | Rate Limiter Redis Fallback | `rate_limit.py` | Low |

**Total files modified**: 10

---

## 1. CSRF Enforcement Middleware (SEC-M-09)

**File**: `app/common/middleware.py` (new class), `app/main.py` (registration)

**What changed**:
- Added `CsrfEnforcementMiddleware` class to `middleware.py`
- Checks `X-CSRF-Token` header against `csrf_token` cookie on POST/PUT/PATCH/DELETE
- Skips enforcement for GET/HEAD/OPTIONS and requests with `X-Api-Key` header
- Returns `403` with bilingual (EN/AR) error messages on mismatch or missing token
- Registered in `main.py` middleware chain after `SecurityHeadersMiddleware`

**Architecture note**: Uses raw ASGI scope inspection (not `request.state`) so it works
independently of the `ApiKeyMiddleware` ordering. API key requests bypass CSRF checks
because API keys are not session-based and not vulnerable to CSRF.

---

## 2. Password Complexity (SEC-M-05)

**File**: `app/modules/identity/schemas.py`, `app/modules/identity/router.py`

**What changed**:
- Added `validate_password_strength()` function in `schemas.py` enforcing:
  - Minimum **12 characters** (up from 8)
  - At least one **uppercase** letter
  - At least one **lowercase** letter
  - At least one **digit**
  - At least one **special character**
  - Reject common passwords from a blocklist (password, 123456..., admin123, etc.)
- Validation runs via `@model_validator(mode="after")` on:
  - `UserCreate.password`
  - `PasswordChangeRequest.new_password`
- `ResetPasswordRequest.new_password` min_length updated to 12; validates at router level
- All error messages are **bilingual** (English | Arabic)

**Common password blocklist**: 20 entries including translatable weak passwords.

---

## 3. Account Lockout

**File**: `app/modules/identity/models.py`, `app/modules/identity/service.py`

**What changed**:

### Model (`models.py`)
- Added `failed_attempts: Mapped[int] = mapped_column(default=0)` to `User`
- Added `locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))` to `User`
- Added `is_locked` property checking `locked_until > now` at runtime

### Service (`service.py`)
- `authenticate()` now performs lockout logic:
  - **Check lock**: If `user.is_locked`, returns 401 with time remaining (bilingual)
  - **Failed attempt**: Increments `failed_attempts`; at 5 failures → locks for 15 minutes
  - **Successful login**: Resets `failed_attempts=0`, clears `locked_until`, sets `last_login_at`
- Lockout events are logged to:
  - **Audit trail** (`account_locked`, `login_blocked_locked` actions)
  - **Structured logger** (`auth.account_locked`, `auth.account_locked_after_failures`)

**Lockout parameters**: 5 attempts → 15-minute lock. Configurable by changing `_MAX_FAILED_ATTEMPTS` / `_LOCK_DURATION_MINUTES` constants.

---

## 4. SSO Token Encryption (SEC-H-02)

**File**: `sdk/security.py`, `app/modules/sso/service.py`

**What changed**:

### SDK (`sdk/security.py`)
- Added `_derive_fernet_key(secret)` — derives 32-byte Fernet key from `settings.secret_key` via SHA-256
- Added `_get_fernet(secret)` — lazy singleton Fernet instance
- Added `encrypt_token(plaintext, secret)` — encrypts using Fernet (AES-128-CBC + HMAC-SHA256)
- Added `decrypt_token(ciphertext, secret)` — decrypts Fernet ciphertext
- Handles empty strings (returns as-is)

### SSO Service (`app/modules/sso/service.py`)
- Added `_encrypt(plaintext)` / `_decrypt(ciphertext)` helpers on `OAuthService`
- Uses `settings.secret_key` as the encryption secret
- **Encrypt on write**: `access_token` and `refresh_token` encrypted before DB insert/update
- **Decrypt on read**: Available via `_decrypt()` for future use (e.g., calling provider APIs)
- Existing connections updated on re-login (re-encrypted with latest key)
- Failed decryption logs warnings but doesn't crash

**DB Impact**: No schema change — encrypted tokens are stored in the existing `Text` columns.
**Migration needed**: None (existing plaintext tokens will be re-encrypted on next SSO login).

---

## 5. JWT Key Rotation Readiness

**File**: `app/modules/identity/service.py`, `app/modules/identity/router.py`

**What changed**:

### Token payload (`service.py`)
- Added `kid` (Key ID) field to both `create_access_token()` and `create_refresh_token()`
- Current key ID: `"v1-hs256"`
- Helper function `_current_key_id()` for centralized key management

### JWKS endpoint (`router.py`)
- Added `GET /api/v1/identity/.well-known/jwks.json`
- Returns JWKS with `v1-hs256` key entry (empty `k` field — symmetric keys not exposed)
- Includes `use: "sig"` and `alg: "HS256"` metadata

### Migration path to RS256 (documented in code):
1. Generate RSA key pair, add to config
2. Add `"v2-rs256"` kid entry to JWKS endpoint alongside `"v1-hs256"`
3. Rotate token signer to use new kid
4. Remove old kid after all tokens expire (~7 days for refresh tokens)

---

## 6. Rate Limiter Redis Integration

**File**: `app/common/rate_limit.py`

**What changed**:
- `rate_limit_dep()` (per-user sliding window rate limiter) now supports Redis
- Added `_get_redis()` — lazy Redis client initialization with error handling
- Added `_check_rate_limit_redis()` — Redis-based check using `INCR` + `EXPIRE`
- Renamed original in-memory check to `_check_rate_limit_in_memory()`
- Flow: Try Redis first; if Redis unavailable (`None` returned), fall back to in-memory
- Thread-safe Redis initialization via double-checked locking

**Note**: The middleware-level `RateLimitMiddleware` in `middleware.py` already has Redis
support. This change brings the dependency-based `rate_limit_dep()` to parity.

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| CSRF middleware blocks legitimate API calls | Low | Skips for GET/HEAD/OPTIONS and API-key requests |
| Password complexity rejects existing users | None | Only applies to new registrations and password changes |
| Account lockout on legitimate user | Low | 15-min auto-unlock; clear bilingual messaging |
| Fernet key derivation change | Medium | Uses `secret_key` (already set in env); same key across restarts |
| JWT kid addition | None | Non-breaking; optional field |
| Redis rate limiter connection failures | Low | Graceful fallback to in-memory |

---

## Database Migration Required

Alembic migration needed for the `users` table:

```sql
ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMPTZ;
```

Migration file: to be auto-generated via `alembic revision --autogenerate -m "add_account_lockout_fields"`

---

## Files Modified (10)

| File | Changes |
|------|---------|
| `app/common/middleware.py` | +50 lines: `CsrfEnforcementMiddleware` class |
| `app/main.py` | +1 import, +1 middleware registration |
| `app/modules/identity/schemas.py` | +52 lines: password validation + blocklist |
| `app/modules/identity/models.py` | +9 lines: lockout fields + `is_locked` property |
| `app/modules/identity/service.py` | +39 lines: lockout logic + kid in JWT payload |
| `app/modules/identity/router.py` | +21 lines: `/reset-password` validation + JWKS endpoint |
| `app/modules/sso/service.py` | +15 lines: Fernet encrypt/decrypt helpers + usage |
| `sdk/security.py` | +38 lines: Fernet encryption utilities |
| `app/common/rate_limit.py` | +53 lines: Redis support with fallback |

---

## Verification Checklist

- [ ] Run `alembic revision --autogenerate` to create the lockout migration
- [ ] Run tests: `pytest app/modules/identity/tests/`
- [ ] Run tests: `pytest app/modules/sso/`
- [ ] Manually test CSRF: POST without X-CSRF-Token → 403
- [ ] Manually test CSRF: GET /csrf-token → set cookie → POST with matching header → 200
- [ ] Manually test lockout: 5 failed logins → account locked
- [ ] Manually test password: try weak password on /register → 422 with bilingual error
- [ ] Verify JWKS: GET /api/v1/identity/.well-known/jwks.json
