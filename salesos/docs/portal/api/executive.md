# Executive API

> **Base Path:** `/api/v1/executive`

Executive-level dashboards — aggregated KPIs, team performance, pipeline health, and forecast data for C-suite and leadership views.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/executive/dashboard` | Executive dashboard summary |

---

## Executive Dashboard

```bash
curl -X GET https://api.salesos.sa/api/v1/executive/dashboard \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "revenue": {
    "closed_won_ytd": 2450000,
    "pipeline_value": 8200000,
    "forecast": 3100000,
    "quota_attainment": 0.78,
    "avg_deal_size": 85000,
    "win_rate": 0.32
  },
  "pipeline": {
    "total_deals": 142,
    "by_stage": {
      "discovery": 45,
      "proposal": 38,
      "negotiation": 22,
      "closed_won": 28,
      "closed_lost": 9
    },
    "avg_sales_cycle_days": 52,
    "velocity_score": 78
  },
  "team_performance": [
    {
      "user_id": "user_001",
      "name": "Ahmad Ali",
      "deals_closed": 8,
      "revenue": 680000,
      "quota_attainment": 0.91,
      "activity_score": 85
    },
    {
      "user_id": "user_002",
      "name": "Sara Ahmed",
      "deals_closed": 6,
      "revenue": 520000,
      "quota_attainment": 0.74,
      "activity_score": 72
    }
  ],
  "alerts": [
    {
      "type": "at_risk_deal",
      "message": "3 deals worth $450K at risk — no activity in 14+ days",
      "severity": "high"
    },
    {
      "type": "quota_gap",
      "message": "Team needs $1.2M more to hit quarterly target",
      "severity": "medium"
    }
  ],
  "trends": {
    "revenue_growth_mom": 0.12,
    "pipeline_growth_mom": 0.08,
    "win_rate_trend": "improving"
  }
}
```

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid auth token |
| `FORBIDDEN` | 403 | Insufficient permissions (requires leadership role) |
| `TENANT_MISMATCH` | 403 | Tenant context mismatch |
