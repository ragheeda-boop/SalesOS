# Audit Log API

> **سجل التدقيق — تتبع جميع التغييرات في النظام**

Base path: `/api/v1/audit`

---

## Query Audit Logs

```
GET /api/v1/audit
```

**Permissions:** `audit:read` (admin or auditor role)

| Param | Type | Description |
|-------|------|-------------|
| `actor_id` | string | Filter by user |
| `action` | string | Filter by action type |
| `resource_id` | string | Filter by resource |
| `from` | string | Start date |
| `to` | string | End date |
| `page` | number | Page number |
| `limit` | number | Results per page |

```bash
curl -X GET "https://api.salesos.sa/api/v1/audit?action=opportunity.stage_changed&from=2026-07-01" \
  -H "Authorization: Bearer <token>"
```

**Response (200):**

```json
{
  "items": [{
    "id": "audit_uuid",
    "tenant_id": "tenant_xyz",
    "actor_id": "user_abc",
    "actor_name": "Ahmed Al-Rashid",
    "action": "opportunity.stage_changed",
    "resource_id": "opp_123",
    "resource_type": "opportunity",
    "details": {
      "from": "qualification",
      "to": "discovery"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "SalesOS Web",
    "timestamp": "2026-07-11T10:00:00Z"
  }],
  "total": 1234
}
```

---

## Action Types Captured

| Category | Actions |
|----------|---------|
| Authentication | `user.login`, `user.logout`, `user.login_failed` |
| Companies | `company.created`, `company.updated`, `company.merged` |
| Opportunities | `opportunity.created`, `opportunity.stage_changed`, `opportunity.won`, `opportunity.lost` |
| NBA | `nba.generated`, `nba.accepted`, `nba.dismissed` |
| Workflows | `workflow.created`, `workflow.executed`, `workflow.failed` |
| Admin | `user.invited`, `user.role_changed`, `api_key.created` |
| Decisions | `decision.evaluated`, `feedback.submitted`, `rule.created` |

---

## Retention

Audit logs are retained for **7 years** (KSA PDPL compliance). Logs are immutable and cannot be deleted.
