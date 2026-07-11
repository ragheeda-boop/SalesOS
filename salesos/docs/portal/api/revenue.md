# Revenue Dashboard API

> **لوحة الإيرادات — نظرة شاملة على أداء الفريق وخط الأنابيب**

Base path: `/api/v1/revenue/dashboard`

---

## Get Revenue Dashboard

```
GET /api/v1/revenue/dashboard
```

**Permissions:** `pipeline:read` + `opportunity:read`

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/dashboard" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>"
```

**Response (200):**

```json
{
  "target": {
    "period": "Q3_2026",
    "target_revenue": 5000000,
    "current_revenue": 1200000,
    "achievement_pct": 0.24
  },
  "forecast": {
    "pipeline": 2850000,
    "best_case": 1650000,
    "commit": 980000,
    "closed_won": 1200000
  },
  "pipeline_summary": {
    "total_value": 2850000,
    "weighted_value": 1650000,
    "total_count": 42,
    "win_rate": 0.32,
    "velocity_days": 67
  },
  "health_map": {
    "healthy": 28,
    "at_risk": 10,
    "critical": 4
  },
  "nba_stats": {
    "total_recommendations": 156,
    "accepted": 98,
    "acceptance_rate": 0.63
  },
  "team_performance": [
    {
      "name": "Ahmed Al-Rashid",
      "open_opportunities": 8,
      "total_value": 620000,
      "closed_won_value": 450000,
      "win_rate": 0.38
    }
  ],
  "at_risk_deals": [...],
  "communication_summary": {
    "meetings_this_week": 12,
    "emails_this_week": 34,
    "avg_sentiment": 0.68
  }
}
```

---

## Related

| Resource | Link |
|----------|------|
| Pipeline Analytics | [Pipeline API](pipeline.md) |
| Team performance | [Analytics API](analytics.md) |
