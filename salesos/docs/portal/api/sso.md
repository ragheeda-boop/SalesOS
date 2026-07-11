# SSO / Authentication API

> **المصادقة — تسجيل الدخول، SSO، إدارة الجلسات**

Base path: `/api/v1/auth`

---

## Login

```
POST /api/v1/auth/login
```

```bash
curl -X POST "https://api.salesos.sa/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your_password"}'
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_abc123...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "name": "Ahmed Al-Rashid",
    "role": "admin",
    "tenant_id": "tenant_xyz789"
  }
}
```

---

## Refresh Token

```
POST /api/v1/auth/refresh
```

```bash
curl -X POST "https://api.salesos.sa/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "rt_abc123..."}'
```

---

## SSO Login

```
GET /api/v1/auth/sso/{provider}
```

Supported providers: `azure`, `google`, `okta`.

Redirects to the provider's OAuth page. On success, redirects back to `https://app.salesos.sa/auth/callback` with JWT tokens.

---

## Logout

```
POST /api/v1/auth/logout
```

Invalidates the refresh token.

---

## Get Current User

```
GET /api/v1/auth/me
```

Returns current user profile and permissions.

---

## Token Information

| Token | Lifetime | Storage | Use |
|-------|----------|---------|-----|
| Access Token (JWT) | 30 minutes | Memory / HTTP-Only Cookie | API authentication |
| Refresh Token | 7 days | Secure Storage | Get new access tokens |
| API Key | Never expires | Server-side | Programmatic access |

---

## JWT Payload

```json
{
  "sub": "user_abc123",
  "tenant_id": "tenant_xyz789",
  "role": "admin",
  "permissions": ["company:*", "opportunity:*", "nba:*"],
  "exp": 1720720800,
  "iat": 1720719000
}
```
