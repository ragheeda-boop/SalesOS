# Identity API

> **Base Path:** `/api/v1/identity`

Handles user registration, authentication, session management, password flows, and tenant provisioning. All responses follow standard schema + success/error patterns.

---

## Authentication Methods

| Method | Header |
|--------|--------|
| JWT Token | `Authorization: Bearer <jwt_token>` |
| API Key | `Authorization: Bearer <api_key_raw>` |

Both are supported via the `AuthDependency` dependency injection.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/identity/register` | Register a new user + tenant |
| `POST` | `/identity/login` | Login with email + password |
| `POST` | `/identity/logout` | Logout current session |
| `POST` | `/identity/refresh` | Refresh access token |
| `POST` | `/identity/forgot-password` | Request password reset |
| `POST` | `/identity/reset-password` | Reset password with token |
| `GET` | `/identity/sessions` | List active sessions |
| `DELETE` | `/identity/sessions/{session_id}` | Revoke a specific session |
| `POST` | `/identity/sessions/revoke-all` | Revoke all sessions |
| `POST` | `/identity/tenants` | Create a new tenant |

---

## Register

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "SecureP@ss123",
    "name": "Ahmad Ali",
    "company_name": "Acme Corp"
  }'
```

**Response:** `201 Created`

```json
{
  "id": "user_abc123",
  "email": "admin@company.com",
  "name": "Ahmad Ali",
  "tenant_id": "tenant_xyz",
  "created_at": "2026-07-12T14:30:00.000Z",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 1800
}
```

---

## Login

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "SecureP@ss123"
  }'
```

**Response:** `200 OK`

```json
{
  "id": "user_abc123",
  "email": "admin@company.com",
  "name": "Ahmad Ali",
  "tenant_id": "tenant_xyz",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 1800
}
```

---

## Logout

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/logout \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "message": "Logged out successfully",
  "data": {
    "message": "Session revoked"
  }
}
```

---

## Refresh Token

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ..."
  }'
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 1800
}
```

---

## Forgot Password

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com"
  }'
```

**Response:** `200 OK`

```json
{
  "message": "Password reset code sent"
}
```

---

## Reset Password

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset-token-from-email",
    "new_password": "NewSecureP@ss456"
  }'
```

**Response:** `200 OK`

```json
{
  "message": "Password reset successfully"
}
```

---

## List Sessions

```bash
curl -X GET https://api.salesos.sa/api/v1/identity/sessions \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "sess_123",
        "created_at": "2026-07-12T14:30:00.000Z",
        "last_activity": "2026-07-12T15:00:00.000Z",
        "expires_at": "2026-07-13T14:30:00.000Z",
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.100"
      }
    ],
    "count": 1
  }
}
```

---

## Revoke Session

```bash
curl -X DELETE https://api.salesos.sa/api/v1/identity/sessions/sess_123 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "Session revoked successfully"
  }
}
```

---

## Revoke All Sessions

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/sessions/revoke-all \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "All sessions revoked successfully",
    "revoked_count": 3
  }
}
```

---

## Create Tenant

```bash
curl -X POST https://api.salesos.sa/api/v1/identity/tenants \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "slug": "acme",
    "plan": "professional"
  }'
```

**Response:** `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "tenant_new",
    "name": "Acme Corp",
    "slug": "acme",
    "plan": "professional",
    "created_at": "2026-07-12T14:30:00.000Z"
  }
}
```

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `EMAIL_EXISTS` | 409 | Email already registered |
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `TOKEN_EXPIRED` | 401 | Refresh token has expired |
| `INVALID_TOKEN` | 401 | Malformed or invalid token |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist or already revoked |
| `PASSWORD_TOO_WEAK` | 422 | Password doesn't meet complexity requirements |
| `INVALID_RESET_TOKEN` | 400 | Password reset token is invalid or expired |
| `RATE_LIMITED` | 429 | Too many login attempts |
