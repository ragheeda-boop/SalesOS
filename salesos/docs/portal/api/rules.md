# Rules Engine API

> **محرك قواعد الأعمال — إدارة وتقييم قواعد الأعمال**
> Base path: `/api/v1/rules`

---

## Authentication

All endpoints require `Authorization: Bearer <token>` and `X-Tenant-Id` headers.

---

## List Rules

```
GET /api/v1/rules?domain=company
```

**Permissions:** `rules:read`

Query params:

| Param | Type | Description |
|-------|------|-------------|
| `domain` | string | Filter by domain: `company`, `opportunity`, `scoring`, `workflow` |

```bash
curl -X GET "https://api.salesos.sa/api/v1/rules" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: t-123"
```

---

## Create Rule

```
POST /api/v1/rules
```

**Permissions:** `rules:write`

```json
{
  "name": "High-value deal alert",
  "description": "Notify when deal exceeds $100K",
  "enabled": true,
  "domain": "opportunity",
  "conditions": {
    "type": "and",
    "conditions": [
      { "field": "value", "operator": "gte", "value": 100000 },
      { "field": "stage", "operator": "eq", "value": "proposal" }
    ]
  },
  "actions": [
    { "type": "send_notification", "params": { "channel": "in-app", "priority": "high" } },
    { "type": "trigger_nba", "params": { "recommendation": "accelerate_review" } }
  ],
  "priority": 1
}
```

**Supported conditions:**

| Field | Operators |
|-------|-----------|
| `value`, `probability` | `eq`, `neq`, `gt`, `gte`, `lt`, `lte` |
| `stage`, `industry`, `owner` | `eq`, `neq`, `in`, `not_in` |
| `name`, `description` | `contains`, `starts_with` |
| `created_at`, `expected_close` | `before`, `after`, `between` |

**Supported actions:**

| Type | Description |
|------|-------------|
| `send_notification` | In-app or email notification |
| `trigger_nba` | Trigger NBA recommendation |
| `update_crm` | Update field value |
| `create_task` | Create follow-up task |
| `webhook` | Call external webhook |

---

## Get Rule

```
GET /api/v1/rules/{rule_id}
```

---

## Update Rule

```
PUT /api/v1/rules/{rule_id}
```

Partial update — only include fields to change.

---

## Delete Rule

```
DELETE /api/v1/rules/{rule_id}
```

---

## Evaluate Rule

```
POST /api/v1/rules/{rule_id}/evaluate
```

```json
{
  "entity_type": "opportunity",
  "entity_id": "opp-123",
  "data": {
    "value": 150000,
    "stage": "proposal",
    "owner": "user-456"
  }
}
```

Returns evaluation result with matched conditions and triggered actions.

---

## Batch Evaluate

```
POST /api/v1/rules/evaluate-batch
```

Evaluate all enabled rules against the given context.

---

## Related

| Resource | Link |
|----------|------|
| Rules Engine Guide | [Rule Engine Guide](../../RULE_ENGINE_GUIDE.md) |
| API Portal | [README.md](README.md) |
