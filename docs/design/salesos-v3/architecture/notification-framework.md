# Notification Framework

| Channel | Use |
|---------|-----|
| Toast | Ephemeral confirmations/errors |
| Inbox | Persistent notifications |
| Activity Feed | Object/workspace stream |
| Mention | @user |
| Approval | Contract/workflow |
| Reminder | Tasks/meetings |
| Escalation | SLA breach |
| Digest | Email/push summary |
| Realtime | WebSocket/SSE when available |

## Rules

- Prefer Inbox for actionable items; Toast for feedback.
- Group by object; deep link to L3/L5.
- Respect Settings → Notifications + quiet hours.
- AI notifications labeled Preview + confidence when applicable.
