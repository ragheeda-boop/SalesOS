# Pipeline Analytics API

> **تحليلات خط الأنابيب — سرعة الصفقات، معدلات التحويل، التوقعات**

Base path: `/api/v1/revenue/pipeline`

---

## Get Pipeline Summary

```
GET /api/v1/revenue/pipeline
```

**Permissions:** `pipeline:read`

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/pipeline" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>"
```

**Response (200):**

```json
{
  "total_value": 2850000,
  "weighted_value": 1650000,
  "total_count": 42,
  "win_rate": 0.32,
  "avg_deal_size": 185000,
  "velocity_days": 67,
  "by_stage": {
    "qualification": { "count": 12, "value": 720000, "conversion_rate": 0.42 },
    "discovery": { "count": 10, "value": 650000, "conversion_rate": 0.55 },
    "proposal": { "count": 8, "value": 800000, "conversion_rate": 0.63 },
    "negotiation": { "count": 5, "value": 480000, "conversion_rate": 0.80 },
    "closed_won": { "count": 4, "value": 1200000, "conversion_rate": 1.0 },
    "closed_lost": { "count": 3, "value": 0, "conversion_rate": 0.0 }
  }
}
```

---

## Get Stage Metrics

```
GET /api/v1/revenue/pipeline/stages
```

Detailed metrics per stage: count, value, weighted_value, avg_days_in_stage, conversion_rate.

---

## Get Health Map

```
GET /api/v1/revenue/pipeline/health
```

Returns health distribution + list of opportunities with health status:

```json
{
  "healthy": 28,
  "at_risk": 10,
  "critical": 4,
  "opportunities": [...]
}
```

---

## Get Pipeline Velocity

```
GET /api/v1/revenue/pipeline/velocity
```

| Metric | Description |
|--------|-------------|
| `avg_cycle_days` | Average days from creation to close |
| `avg_days_per_stage` | Days per stage breakdown |
| `velocity_trend` | Monthly velocity history |
| `fastest_close_days` | Fastest deal |
| `slowest_close_days` | Slowest deal |

---

## Forecast Model

| Type | Calculation |
|------|-------------|
| **Pipeline** | Total value of all open opportunities |
| **Best Case** | Sum of (value × probability) for all open |
| **Commit** | Sum of (value × probability) for health >= at_risk, stage >= proposal |

---

## Related

| Resource | Link |
|----------|------|
| Revenue Dashboard | [Revenue API](revenue.md) |
| Opportunities | [Opportunities API](opportunities.md) |
