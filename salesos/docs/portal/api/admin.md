# Admin API

> **إدارة النظام — إعدادات المستأجر، المستخدمين، خطط الاشتراك**

Base path: `/api/v1/admin`

**All endpoints require `admin` role.**

---

## Tenant Settings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/tenant` | Get tenant configuration |
| `PUT` | `/admin/tenant` | Update tenant settings |
| `GET` | `/admin/tenant/features` | List enabled feature flags |
| `PUT` | `/admin/tenant/features` | Toggle feature flags |

---

## User Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/users` | List tenant users |
| `POST` | `/admin/users` | Invite new user |
| `PUT` | `/admin/users/{id}/role` | Change user role |
| `DELETE` | `/admin/users/{id}` | Remove user |

---

## API Keys

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/api-keys` | List API keys |
| `POST` | `/admin/api-keys` | Generate new key |
| `DELETE` | `/admin/api-keys/{id}` | Revoke key |

---

## Billing

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/billing/plan` | Current plan details |
| `PUT` | `/admin/billing/plan` | Change plan |
| `GET` | `/admin/billing/invoices` | Invoice history |
