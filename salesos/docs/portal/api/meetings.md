# Meeting Intelligence API

> **ذكاء الاجتماعات — ملخصات ما قبل وبعد الاجتماع مع استخراج بنود العمل**

Base path: `/api/v1/revenue/meetings`

---

## List Meetings

```
GET /api/v1/revenue/meetings
```

**Permissions:** `meeting:read`

| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Filter by opportunity |
| `type` | string | `pre_meeting`, `during_meeting`, `post_meeting` |
| `from` | string | Start date (ISO 8601) |
| `to` | string | End date |
| `limit` | number | Results per page |

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/meetings?opportunity_id=opp_123" \
  -H "Authorization: Bearer <token>"
```

**Response (200):**

```json
{
  "data": [{
    "id": "mtg_abc123",
    "opportunity_id": "opp_8f3a2b1c",
    "title": "Discovery Meeting — ACME Corp",
    "type": "during_meeting",
    "scheduled_at": "2026-07-10T14:00:00Z",
    "duration_minutes": 45,
    "attendees": [
      { "name": "Ahmed Al-Rashid", "role": "sales" },
      { "name": "John Smith", "role": "prospect" }
    ],
    "intelligence": {
      "summary": "Discussed cloud migration needs. Budget confirmed for Q3.",
      "sentiment": "positive",
      "sentiment_score": 0.78,
      "action_items": [
        { "text": "Schedule technical demo", "owner": "Ahmed", "due_date": "2026-07-15" }
      ],
      "key_decisions": ["Budget confirmed for Q3"]
    }
  }]
}
```

---

## Create Meeting

```
POST /api/v1/revenue/meetings
```

**Permissions:** `meeting:create`

```bash
curl -X POST "..." -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": "opp_8f3a2b1c",
    "title": "Proposal Review — ACME Corp",
    "scheduled_at": "2026-07-15T10:00:00Z",
    "duration_minutes": 60,
    "attendees": [
      { "name": "Ahmed", "email": "ahmed@salesos.sa" },
      { "name": "John Smith", "email": "john@acme.com" }
    ]
  }'
```

---

## Generate Pre-Meeting Brief

```
POST /api/v1/revenue/meetings/{id}/brief
```

AI-generated brief with company overview, contact background, talking points, risks.

---

## Generate Post-Meeting Summary

```
POST /api/v1/revenue/meetings/{id}/summary
```

AI-generated summary with decisions, action items, sentiment, next steps.

---

## Meeting Intelligence Output

| Field | Description |
|-------|-------------|
| `summary` | AI-generated meeting summary |
| `sentiment` | `positive`, `neutral`, `negative` |
| `sentiment_score` | 0.0–1.0 |
| `action_items` | Extracted commitments |
| `key_decisions` | Decisions made during meeting |
| `next_steps` | Recommended follow-up actions |
