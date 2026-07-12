# Dashboard API

> **Base Path:** `/api/v1/dashboard`

Main dashboard aggregation — provides a summarized view of key metrics, activity feed, and widget data for the primary sales dashboard.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/dashboard` | Dashboard summary with KPIs and activity feed |

---

## Get Dashboard

```bash
curl -X GET https://api.salesos.sa/api/v1/dashboard \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "kpis": {
    "open_deals": 42,
    "total_pipeline_value": 3200000,
    "deals_closed_this_month": 8,
    "revenue_this_month": 680000,
    "activities_today": 24,
    "meetings_this_week": 12,
    "conversion_rate": 0.28
  },
  "recent_activities": [
    {
      "id": "act_101",
      "type": "email",
      "subject": "Re: Enterprise proposal",
      "company": "Acme Corp",
      "time": "2026-07-12T14:30:00.000Z"
    },
    {
      "id": "act_102",
      "type": "meeting",
      "subject": "Discovery call — Globex",
      "company": "Globex Corp",
      "time": "2026-07-12T13:00:00.000Z"
    }
  ],
  "upcoming_tasks": [
    {
      "id": "task_001",
      "title": "Follow up with Initech",
      "due": "2026-07-13T10:00:00.000Z",
      "priority": "high"
    }
  ],
  "pipeline_summary": {
    "total_value": 3200000,
    "weighted_value": 1440000,
    "by_stage": {
      "discovery": 800000,
      "proposal": 1200000,
      "negotiation": 600000,
      "closing": 400000
    }
  },
  "alerts": [
    {
      "type": "stale_deal",
      "message": "5 deals have had no activity for 7+ days",
      "severity": "medium"
    }
  ]
}
```

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid auth token |
| `TENANT_MISMATCH` | 403 | Tenant context mismatch |
