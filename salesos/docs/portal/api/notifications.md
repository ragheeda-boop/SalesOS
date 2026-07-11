# Notifications & WebSocket API

> **الإشعارات — WebSocket والتنبيهات في الوقت الفعلي**

---

## WebSocket Connection

```
wss://api.salesos.sa/ws?token=<jwt>&tenant_id=<tenant_id>
```

### Events

| Event Type | Payload | Description |
|-----------|---------|-------------|
| `nba.generated` | `{ opportunity_id, action, confidence }` | New NBA recommendation |
| `deal_health.changed` | `{ opportunity_id, from, to }` | Health status change |
| `workflow.completed` | `{ workflow_id, state }` | Workflow execution done |
| `pipeline.updated` | `{ total_value, weighted_value }` | Pipeline metrics changed |
| `signal.detected` | `{ company_id, signal_type }` | New company signal |

### Client-Side (TypeScript)

```typescript
const ws = new WebSocket(`wss://api.salesos.sa/ws?token=${jwt}&tenant_id=${tenantId}`)

ws.onmessage = (event) => {
  const { type, payload } = JSON.parse(event.data)
  switch (type) {
    case 'nba.generated':
      // Show notification badge
      break
    case 'deal_health.changed':
      // Update deal health indicator
      break
  }
}
```

---

## Push Notifications (REST)

```
POST /api/v1/notifications/send
```

**Permissions:** Requires admin

```json
{
  "type": "nba_ready",
  "recipients": ["user_abc123"],
  "title": "New recommendation for ACME Corp",
  "body": "Send proposal document — 87% confidence"
}
```

---

## Notification Preferences

```
GET /api/v1/notifications/preferences
PUT /api/v1/notifications/preferences
```

Configure which event types trigger notifications and channels (in-app, email, Slack).
