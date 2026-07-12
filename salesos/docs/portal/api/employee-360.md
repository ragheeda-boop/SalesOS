# Employee 360 API

> **Base Path:** `/api/v1/employees`

Employee intelligence — 360-degree views with activity summaries, performance indicators, and work patterns. Supports both admin lookup (`/employees/{id}/360`) and self-service (`/employees/me/360`).

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/employees/{employee_id}/360` | Full 360 view of a specific employee |
| `GET` | `/employees/me/360` | Current user's own 360 view |

---

## Employee 360 View

```bash
curl -X GET https://api.salesos.sa/api/v1/employees/user_abc123/360 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "employee": {
    "id": "user_abc123",
    "name": "Ahmad Ali",
    "email": "ahmad@acme.com",
    "title": "Account Executive",
    "department": "Sales",
    "manager_id": "user_mgr001",
    "hire_date": "2024-03-15",
    "location": "Riyadh"
  },
  "activity_summary": {
    "period": "last_30_days",
    "emails_sent": 145,
    "emails_received": 210,
    "meetings_attended": 18,
    "meetings_hosted": 6,
    "calls_made": 42,
    "linkedin_messages": 35,
    "proposals_sent": 5,
    "deals_closed": 2,
    "total_revenue": 185000
  },
  "performance": {
    "quota_attainment": 0.82,
    "pipeline_coverage": 2.1,
    "win_rate": 0.35,
    "avg_deal_size": 92500,
    "avg_sales_cycle_days": 45,
    "activity_score": 85
  },
  "work_patterns": {
    "peak_activity_hours": ["09:00-11:00", "14:00-16:00"],
    "avg_response_time_hours": 2.3,
    "preferred_channel": "email",
    "most_active_days": ["Monday", "Tuesday", "Wednesday"]
  },
  "recent_activities": [
    {
      "id": "act_001",
      "type": "meeting",
      "subject": "Demo with Acme Corp",
      "date": "2026-07-11T10:00:00.000Z",
      "related_company": "Acme Corp"
    },
    {
      "id": "act_002",
      "type": "email",
      "subject": "Proposal follow-up — Globex deal",
      "date": "2026-07-10T16:30:00.000Z",
      "related_company": "Globex Corp"
    }
  ],
  "open_opportunities": [
    {
      "id": "opp_789",
      "name": "Acme Enterprise License",
      "value": 120000,
      "stage": "negotiation",
      "close_date": "2026-08-15"
    }
  ]
}
```

---

## My 360 View

Self-service endpoint — returns the current authenticated user's own employee 360 view.

```bash
curl -X GET https://api.salesos.sa/api/v1/employees/me/360 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "employee": {
    "id": "user_abc123",
    "name": "Ahmad Ali",
    "email": "ahmad@acme.com",
    "title": "Account Executive",
    "department": "Sales"
  },
  "activity_summary": {
    "period": "last_30_days",
    "emails_sent": 145,
    "meetings_attended": 18,
    "deals_closed": 2,
    "total_revenue": 185000
  },
  "performance": {
    "quota_attainment": 0.82,
    "win_rate": 0.35,
    "activity_score": 85
  },
  "recent_activities": [],
  "open_opportunities": []
}
```

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `EMPLOYEE_NOT_FOUND` | 404 | Employee with given ID doesn't exist |
| `UNAUTHORIZED` | 401 | Missing or invalid auth token |
| `FORBIDDEN` | 403 | No permission to view this employee's data |
| `TENANT_MISMATCH` | 403 | Employee belongs to different tenant |
