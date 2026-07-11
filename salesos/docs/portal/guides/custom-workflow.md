# Tutorial: Creating a Custom Workflow

> **إنشاء سير عمل مخصص — أتمتة عملية مبيعات متكررة**

This tutorial creates a "Deal Stagnation Recovery" workflow that automatically detects idle deals and re-engages them.

---

## Step 1: Define the Workflow

```json
{
  "name": "Deal Stagnation Recovery",
  "description": "Auto-detects idle deals and triggers re-engagement sequence",
  "trigger": {
    "type": "event",
    "config": {
      "eventType": "deal_health.changed",
      "filter": {
        "field": "health",
        "operator": "==",
        "value": "critical"
      }
    }
  },
  "steps": [
    {
      "id": "step_notify_owner",
      "type": "action",
      "label": "Notify Deal Owner",
      "config": {
        "actionType": "send_email",
        "params": {
          "template": "deal_stagnation_alert",
          "to": "opportunity.owner.email",
          "subject": "⚠️ Deal Stagnation: {{opportunity.name}}"
        }
      },
      "nextOnSuccess": ["step_create_task"],
      "nextOnFailure": ["step_escalate"]
    },
    {
      "id": "step_create_task",
      "type": "action",
      "label": "Create Recovery Task",
      "config": {
        "actionType": "create_task",
        "params": {
          "title": "Recovery plan for {{opportunity.name}}",
          "description": "This deal has been stagnant for 14+ days. Review and execute recovery plan.",
          "priority": "high",
          "due_in_days": 2
        }
      },
      "nextOnSuccess": ["step_refresh_nba"],
      "nextOnFailure": ["step_escalate"]
    },
    {
      "id": "step_refresh_nba",
      "type": "action",
      "label": "Refresh NBA",
      "config": {
        "actionType": "trigger_nba",
        "params": {}
      }
    },
    {
      "id": "step_escalate",
      "type": "action",
      "label": "Escalate to Manager",
      "config": {
        "actionType": "send_email",
        "params": {
          "template": "deal_escalation",
          "to": "opportunity.owner.manager.email",
          "subject": "🚨 Escalation: {{opportunity.name}}"
        }
      }
    }
  ]
}
```

---

## Step 2: Create via API

```bash
curl -X POST "https://api.salesos.sa/api/v1/workflows" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>" \
  -H "Content-Type: application/json" \
  -d @workflow-definition.json
```

---

## Step 3: Activate the Workflow

```bash
curl -X PUT "https://api.salesos.sa/api/v1/workflows/{id}/activate" \
  -H "Authorization: Bearer <token>"
```

---

## Step 4: Monitor Execution

```bash
curl -X GET "https://api.salesos.sa/api/v1/workflows/{id}/executions?limit=10" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "executions": [
    {
      "id": "exec_abc",
      "state": "completed",
      "steps": [
        { "step_id": "step_notify_owner", "state": "completed", "duration_ms": 450 },
        { "step_id": "step_create_task", "state": "completed", "duration_ms": 320 },
        { "step_id": "step_refresh_nba", "state": "completed", "duration_ms": 1520 },
        { "step_id": "step_escalate", "state": "skipped" }
      ],
      "started_at": "2026-07-11T10:00:00Z",
      "completed_at": "2026-07-11T10:00:03Z"
    }
  ]
}
```

---

## Workflow Templates

| Template | Description |
|----------|-------------|
| Follow-Up Sequence | Auto-follow-up on idle deals |
| Lead Nurturing | Nurture new opportunities |
| Deal Escalation | Escalate at-risk deals |
| Onboarding | Customer onboarding flow |
| Renewal Reminder | Contract renewal automation |

---

## Best Practices

1. **Start from a template** — 80% of workflows begin from a template
2. **Test with dry-run** — Validate before activating
3. **Set timeouts** — Prevent runaway workflows
4. **Monitor failure rates** — Alert on > 10% failure
5. **Use conditions** — Branch logic for different scenarios

---

## Related

| Resource | Link |
|----------|------|
| Workflow Engine API | [API Reference](../api/workflows.md) |
| Workflow Architecture | [Wave 3 Workflow](../../docs/wave-3/03-WORKFLOW_AUTOMATION.md) |
