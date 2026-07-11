# Analytics & Reporting API

> **التحليلات والتقارير — تقارير قياسية ومخصصة مع التصدير**

Base path: `/api/v1/analytics`

---

## Get Standard Report

```
GET /api/v1/analytics/reports/{report_name}
```

**Permissions:** `analytics:read`

| Report | Description |
|--------|-------------|
| `pipeline_health` | Pipeline value by stage, weighted pipeline, deal count |
| `team_performance` | Per-rep metrics: pipeline, win rate, activity |
| `forecast_accuracy` | Forecast vs actual by rep, category |
| `activity_analysis` | Activity types, trends, per-rep comparison |
| `velocity` | Avg days per stage, bottleneck detection |
| `win_loss` | Win rate by industry, product, region |

```bash
curl -X GET "https://api.salesos.sa/api/v1/analytics/reports/pipeline_health?from=2026-01-01&to=2026-07-11" \
  -H "Authorization: Bearer <token>"
```

---

## Get Report as CSV

```
GET /api/v1/analytics/reports/{report_name}/export?format=csv
```

| Format | Extension | Notes |
|--------|-----------|-------|
| `csv` | .csv | UTF-8 BOM for Excel Arabic |
| `pdf` | .pdf | RTL support, company branding |
| `xlsx` | .xlsx | Multi-sheet with formatting |

---

## Custom Reports

```
POST /api/v1/analytics/reports/custom
```

Build a custom report with selected dimensions, measures, and filters.

```json
{
  "dimensions": ["stage", "owner"],
  "measures": ["total_value", "deal_count"],
  "filters": {
    "date_from": "2026-01-01",
    "date_to": "2026-07-11"
  }
}
```

---

## Scheduled Reports

```
POST /api/v1/analytics/reports/schedule
```

```json
{
  "report_config": { "dimensions": ["stage"], "measures": ["total_value"] },
  "format": "pdf",
  "schedule_cron": "0 9 * * 1",
  "recipients": ["manager@salesos.sa"]
}
```

---

## Related

| Resource | Link |
|----------|------|
| Analytics Architecture | [Wave 3 Analytics](../../docs/wave-3/04-ANALYTICS_REPORTING.md) |
| Revenue Dashboard | [Revenue API](revenue.md) |
