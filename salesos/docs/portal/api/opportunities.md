# Opportunities API

> **إدارة الفرص — دورة حياة الصفقة من التأهيل إلى الإغلاق**

Base path: `/api/v1/revenue/opportunities`

---

## List Opportunities

```
GET /api/v1/revenue/opportunities
```

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `stage` | string | — | Filter: `qualification`, `discovery`, `proposal`, `negotiation`, `closed_won`, `closed_lost` |
| `health` | string | — | Filter: `healthy`, `at_risk`, `critical` |
| `owner_id` | string | — | Filter by owner |
| `min_value` | number | — | Minimum deal value |
| `max_value` | number | — | Maximum deal value |
| `sort` | string | `created_at` | Sort field |
| `order` | string | `desc` | `asc` or `desc` |
| `page` | number | `1` | Page number |
| `limit` | number | `20` | Results per page |

**Permissions:** `opportunity:read`

**Request:**

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/opportunities?stage=proposal&sort=value&order=desc" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>"
```

**Response (200):**

```json
{
  "data": [
    {
      "id": "opp_8f3a2b1c",
      "company_id": "comp_4d5e6f7g",
      "name": "Enterprise License — ACME Corp",
      "stage": "proposal",
      "value": 250000,
      "currency": "SAR",
      "probability": 0.65,
      "health": "healthy",
      "expected_close_date": "2026-08-15",
      "owner_id": "user_abc123",
      "owner_name": "Ahmed Al-Rashid",
      "playbook_id": "pb_9x8y7z",
      "nba": { "id": "nba_1a2b3c", "action": "Send proposal document", "confidence": 0.87 },
      "created_at": "2026-06-20T09:00:00Z",
      "updated_at": "2026-07-10T14:30:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 42, "total_pages": 3 }
}
```

---

## Get Opportunity

```
GET /api/v1/revenue/opportunities/{id}
```

**Permissions:** `opportunity:read`

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/opportunities/opp_8f3a2b1c" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>"
```

Returns full opportunity detail with stage history, NBA, and company snapshot.

---

## Create Opportunity

```
POST /api/v1/revenue/opportunities
```

**Permissions:** `opportunity:create`

```bash
curl -X POST "https://api.salesos.sa/api/v1/revenue/opportunities" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "comp_4d5e6f7g",
    "name": "Cloud Migration — Saudi Telecom",
    "value": 500000,
    "currency": "SAR",
    "expected_close_date": "2026-09-30"
  }'
```

**Response (201):**

```json
{
  "id": "opp_new123",
  "stage": "qualification",
  "probability": 0.10,
  "health": "healthy",
  "created_at": "2026-07-11T10:00:00Z"
}
```

---

## Update Opportunity

```
PUT /api/v1/revenue/opportunities/{id}
```

**Permissions:** `opportunity:update`

```bash
curl -X PUT "..." -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "value": 750000}'
```

---

## Change Stage

```
PATCH /api/v1/revenue/opportunities/{id}/stage
```

**Permissions:** `opportunity:update`

```bash
curl -X PATCH "..." -H "Content-Type: application/json" \
  -d '{"stage": "negotiation", "reason": "Proposal accepted"}'
```

Stage transitions trigger:
- NBA recomputation
- Activity log entry
- Health recalculation
- Pipeline metrics update

---

## Delete Opportunity

```
DELETE /api/v1/revenue/opportunities/{id}
```

**Permissions:** `opportunity:delete`

Returns `204 No Content`.

---

## Common Schemas

```typescript
interface Opportunity {
  id: string
  company_id: string
  name: string
  stage: 'qualification' | 'discovery' | 'proposal' | 'negotiation' | 'closed_won' | 'closed_lost'
  value: number
  currency: string
  probability: number       // 0.0–1.0
  health: 'healthy' | 'at_risk' | 'critical'
  expected_close_date: string | null
  owner_id: string
  owner_name: string
  playbook_id: string | null
  nba: NBAResponse | null
  created_at: string
  updated_at: string
}
```

---

## Deal Health Model

| Health | Conditions | Color |
|--------|-----------|-------|
| Healthy | Activity in last 7d, stage progressing, no risks | 🟢 |
| At Risk | Activity 7–14d old, or 1+ medium risks | 🟡 |
| Critical | No activity 14d+, or 1+ high risks, close date passed | 🔴 |
