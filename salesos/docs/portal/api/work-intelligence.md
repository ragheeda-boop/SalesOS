# Work Intelligence API

> **Base Path:** `/api/v1/work-intelligence`

Employee work intelligence — activity summaries, focus time analysis, collaboration patterns, and digital exhaust insights. Supports both admin lookup (`/work-intelligence/{employee_id}`) and self-service (`/work-intelligence/me`).

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/work-intelligence/{employee_id}` | Work intelligence for a specific employee |
| `GET` | `/work-intelligence/me` | Current user's own work intelligence |

---

## Employee Work Intelligence

```bash
curl -X GET https://api.salesos.sa/api/v1/work-intelligence/user_abc123 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "employee_id": "user_abc123",
  "period": "last_30_days",
  "activity_summary": {
    "emails_sent": 145,
    "emails_received": 210,
    "meetings_attended": 18,
    "meetings_hosted": 6,
    "calls_made": 42,
    "linkedin_messages": 35,
    "documents_created": 12,
    "documents_reviewed": 28
  },
  "focus_time": {
    "total_hours": 48,
    "avg_daily_hours": 2.4,
    "longest_streak_hours": 4.5,
    "focus_score": 72,
    "interruptions_per_day": 8.2
  },
  "collaboration_patterns": {
    "top_collaborators": [
      {
        "user_id": "user_002",
        "name": "Sara Ahmed",
        "interaction_count": 56,
        "primary_channel": "email"
      }
    ],
    "cross_team_interactions": 23,
    "internal_vs_external_ratio": 0.65
  },
  "digital_exhaust": {
    "tools_used": ["email", "calendar", "crm", "linkedin", "slack"],
    "crm_adoption_score": 0.85,
    "data_freshness_days": 1.2,
    "activity_logging_rate": 0.78
  },
  "workload": {
    "estimated_weekly_hours": 42,
    "meeting负荷": 15,
    "back_to_back_meetings_pct": 0.25,
    "overtime_days": 3
  }
}
```

---

## My Work Intelligence

Self-service endpoint — returns the current authenticated user's own work intelligence data.

```bash
curl -X GET https://api.salesos.sa/api/v1/work-intelligence/me \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "employee_id": "user_abc123",
  "period": "last_30_days",
  "activity_summary": {
    "emails_sent": 145,
    "meetings_attended": 18,
    "calls_made": 42
  },
  "focus_time": {
    "total_hours": 48,
    "focus_score": 72
  },
  "collaboration_patterns": {
    "top_collaborators": [],
    "cross_team_interactions": 23
  }
}
```

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `EMPLOYEE_NOT_FOUND` | 404 | Employee with given ID doesn't exist |
| `UNAUTHORIZED` | 401 | Missing or invalid auth token |
| `FORBIDDEN` | 403 | No permission to view this employee's data |
| `TENANT_MISMATCH` | 403 | Tenant context mismatch |
