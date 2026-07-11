# Workflow Engine API

> **محرك سير العمل — أتمتة دورات المبيعات المتكررة**

Base path: `/api/v1/workflows`

---

## Overview

The Workflow Engine executes Directed Acyclic Graphs (DAGs) of actions triggered by events, schedules, or manual actions.

---

## List Workflows

```
GET /api/v1/workflows
```

**Permissions:** `workflow:read`

```bash
curl -X GET "https://api.salesos.sa/api/v1/workflows?state=active" \
  -H "Authorization: Bearer <token>"
```

---

## Create Workflow

```
POST /api/v1/workflows
```

**Permissions:** `workflow:create`

```json
{
  "name": "Lead Nurturing Sequence",
  "description": "Automated follow-up for new opportunities",
  "trigger": {
    "type": "event",
    "config": {
      "eventType": "opportunity.created"
    }
  },
  "steps": [
    {
      "id": "step_1",
      "type": "action",
      "label": "Send Welcome Email",
      "config": {
        "actionType": "send_email",
        "params": {
          "template": "welcome_lead",
          "to": "opportunity.owner.email"
        }
      }
    },
    {
      "id": "step_2",
      "type": "action",
      "label": "Create Follow-up Task",
      "config": {
        "actionType": "create_task",
        "params": {
          "title": "Follow up with {{company.name}}",
          "due_in_days": 2
        }
      }
    }
  ]
}
```

---

## Execute Workflow

```
POST /api/v1/workflows/{id}/execute
```

Manually trigger a workflow for a specific entity.

---

## Get Execution Trace

```
GET /api/v1/workflows/executions/{id}
```

Returns step-by-step execution details including timing, input, output, errors.

---

## Built-in Templates

| Template | Trigger | Steps |
|----------|---------|-------|
| Follow-Up Sequence | `deal_health.stagnation` | Delay → Email → Task → Delay → Email |
| Lead Nurturing | `opportunity.created` | Email → Delay → Task → Check → Branch |
| Deal Escalation | `deal_health.critical` | Update CRM → Alert → Urgent Task → Notify |
| Onboarding | Manual | Welcome → Tasks → Delay → Check → Reminder |
| Renewal Reminder | Schedule: 90d before expiry | Check → Reminder → Delay → Final → Escalate |

---

## Action Types

| Type | Description |
|------|-------------|
| `send_email` | Send via Email Intelligence |
| `update_crm` | Update opportunity stage/field |
| `create_task` | Create task for user |
| `trigger_nba` | Refresh NBA recommendation |
| `webhook` | Call external URL |
| `delay` | Wait before next step |

---

## Related

| Resource | Link |
|----------|------|
| Workflow Architecture | [Wave 3 Workflow](../../docs/wave-3/03-WORKFLOW_AUTOMATION.md) |
| Creating Custom Workflows | [Guide](../guides/custom-workflow.md) |
