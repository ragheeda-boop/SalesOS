# Security Architecture

> **الأمان — المصادقة، الصلاحيات، عزل المستأجرين، التشفير**

---

## 1. Authentication

### API Key Authentication

Every request requires a Bearer token:

```bash
curl -X GET "https://api.salesos.sa/api/v1/companies/comp_123" \
  -H "Authorization: Bearer sos_abc123..." \
  -H "X-Tenant-Id: tenant_xyz789"
```

### JWT Token Flow

```
User Login
    │
    ▼
┌──────────────────┐
│ POST /auth/login │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ Verify credentials → Generate access token    │
│ • Access token: 30 min expiry (JWT)          │
│ • Refresh token: 7 day expiry (opaque)       │
│ • Token contains: user_id, tenant_id, role   │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│ POST /auth/refresh │
└──────────────────┘
```

### SSO / OAuth

Supported providers: Azure AD, Google Workspace, Okta.

See [SSO Setup Guide](../guides/sso-setup.md) for configuration.

---

## 2. Authorization (RBAC)

### Role Hierarchy

| Role | Permissions | Access |
|------|-------------|--------|
| `admin` | All permissions | Full tenant access including billing |
| `manager` | CRUD except billing | Manage data and users |
| `user` | Read + Create | View and create data |
| `api` | API read/write | Programmatic access only |
| `auditor` | Read-only | Compliance and auditing |

### Permission Resources

| Resource | Actions |
|----------|---------|
| `company` | read, create, update, delete |
| `opportunity` | read, create, update, delete |
| `pipeline` | read |
| `nba` | read, update |
| `meeting` | read, create, update |
| `email` | read, create |
| `workflow` | read, create, update, delete |
| `analytics` | read, export |
| `admin` | settings, billing, users |
| `audit` | read |

### Permission Check Flow

```
API Request
    │
    ▼
┌──────────────────────────────────────────────┐
│ 1. Extract JWT → user_id, tenant_id, role    │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│ 2. Match resource + action against role      │
│    e.g., user wants POST /opportunities      │
│    → check: can role `user` do               │
│      `opportunity:create`?                    │
└──────────────────┬───────────────────────────┘
                   │
              ┌────┴────┐
              ▼         ▼
          ✅ Allow    ❌ 403
```

---

## 3. Tenant Isolation

**Critical:** No cross-tenant data access is permitted under any circumstance.

### Implementation

| Layer | Isolation Mechanism |
|-------|-------------------|
| **Database** | Every table has `tenant_id` column |
| **API** | `X-Tenant-Id` header must match JWT tenant |
| **Queries** | Every query includes `WHERE tenant_id = ?` |
| **Neo4j** | Graph nodes tagged with `tenant_id` property |
| **Kafka** | Each topic partitioned; consumers filter by `tenant_id` |
| **Cache** | Keys prefixed with `{tenant_id}:` |

### Validation

```python
# FastAPI middleware
async def verify_tenant_isolation(request: Request):
    jwt_tenant = request.state.user.tenant_id
    header_tenant = request.headers.get("X-Tenant-Id")
    body_tenant = request.path_params.get("tenant_id")

    if header_tenant and header_tenant != jwt_tenant:
        raise HTTPException(403, "Tenant mismatch")
    if body_tenant and body_tenant != jwt_tenant:
        raise HTTPException(403, "Tenant mismatch")
```

---

## 4. API Security

### Rate Limiting

| Endpoint Group | Limit | Window |
|---------------|-------|--------|
| GET endpoints | 100 requests | per minute |
| POST/PUT/PATCH | 30 requests | per minute |
| DELETE | 10 requests | per minute |
| NBA refresh | 5 requests | per minute |
| AI endpoints | 10 requests | per minute |

Headers included in every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 97
X-RateLimit-Reset: 1720720800
```

### Input Validation

- All input validated via Pydantic models
- SQL injection prevented via parameterized queries
- No eval/exec on user input
- File uploads: type check, size limit (10MB), virus scan

### CSRF Protection

- Stateful CSRF tokens for browser-based clients
- SameSite=Strict on session cookies
- CORS restricted to `ALLOWED_HOSTS`

---

## 5. Data Encryption

| State | Standard | Details |
|-------|----------|---------|
| **At Rest** | AES-256 | Database encryption at disk level |
| **In Transit** | TLS 1.3 | All API traffic, inter-service traffic |
| **Secrets** | Vault / K8s Secrets | API keys, DB passwords, JWT secrets |
| **PII** | Pseudonymization | Personal data masked in logs and analytics |

---

## 6. Secrets Management

**Never store secrets in code, configuration files, or environment files committed to git.**

- API keys → Vault or Kubernetes Secrets
- Database credentials → Environment variables from secrets manager
- JWT signing key → Generated at deploy time, stored in Vault
- Third-party tokens → OAuth 2.0 flow, short-lived

---

## 7. Audit Logging

Every state-changing operation is logged:

```json
{
  "id": "audit_uuid",
  "tenant_id": "tenant_xyz",
  "actor_id": "user_abc",
  "action": "opportunity.stage_changed",
  "resource_id": "opp_123",
  "details": {
    "from": "qualification",
    "to": "discovery",
    "reason": "Discovery call completed"
  },
  "timestamp": "2026-07-11T10:00:00Z"
}
```

Audit logs are immutable and retained for 7 years (KSA PDPL compliance).

---

## 8. Security Checklist for Deployment

| Item | Status |
|------|--------|
| TLS 1.3 enabled | ✅ Required |
| HSTS header | ✅ Required |
| CSP header | ✅ Required |
| CORS restricted | ✅ Required |
| Rate limiting enabled | ✅ Required |
| SQL injection protection | ✅ Required |
| Secret scanning in CI | ✅ Required |
| Dependency audit | ✅ Weekly |
| Penetration testing | ✅ Quarterly |
| Bug bounty program | 🟡 Planned |

---

## 9. Compliance

| Regulation | Scope | Status |
|-----------|-------|--------|
| KSA PDPL | Saudi citizen data stored in KSA | ✅ Compliant |
| Data retention | Max 7 years | ✅ Enforced |
| User data deletion | Right to be forgotten | ✅ API available |
| Saudi data residency | All data in KSA data centers | ✅ Enforced |
| ZATCA e-invoicing | Tax compliance data | ✅ Supported |

---

## Related Documents

| Document | Link |
|----------|------|
| Engineering Constitution - Security | [Article 4](../../../engineering-os/ENGINEERING_CONSTITUTION.md#-4) |
| Production Audit Report | [Audit](../../docs/PRODUCTION_AUDIT_REPORT.md) |
| SSO Setup Guide | [SSO Guide](../guides/sso-setup.md) |
