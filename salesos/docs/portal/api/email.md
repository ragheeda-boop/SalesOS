# Email Intelligence API

> **ذكاء البريد الإلكتروني — تحليل المشاعر، استخراج المواضيع، اكتشاف الأولوية**

Base path: `/api/v1/revenue/emails`

---

## List Emails

```
GET /api/v1/revenue/emails
```

**Permissions:** `email:read`

| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Filter by opportunity |
| `sentiment` | string | `positive`, `neutral`, `negative` |
| `urgency` | string | `low`, `medium`, `high` |
| `from` | string | Start date |
| `to` | string | End date |

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/emails?opportunity_id=opp_123&sentiment=positive" \
  -H "Authorization: Bearer <token>"
```

**Response (200):**

```json
{
  "data": [{
    "id": "eml_xyz789",
    "opportunity_id": "opp_8f3a2b1c",
    "subject": "Re: Enterprise License Proposal",
    "from_address": "john@acme.com",
    "from_name": "John Smith",
    "direction": "inbound",
    "received_at": "2026-07-10T16:00:00Z",
    "intelligence": {
      "sentiment": "positive",
      "sentiment_score": 0.72,
      "topics": [
        { "topic": "pricing", "confidence": 0.85 },
        { "topic": "timeline", "confidence": 0.78 }
      ],
      "urgency": "medium",
      "urgency_reason": "Asking about pricing — indicates active evaluation",
      "key_phrases": ["pricing details", "Q3 timeline"]
    }
  }]
}
```

---

## Create Email (Manual Logging)

```
POST /api/v1/revenue/emails
```

**Permissions:** `email:create`

```bash
curl -X POST "..." -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": "opp_8f3a2b1c",
    "subject": "Enterprise License Proposal",
    "from_address": "ahmed@salesos.sa",
    "to_address": "john@acme.com",
    "direction": "outbound",
    "body": "Dear John, ...",
    "sent_at": "2026-07-10T15:00:00Z"
  }'
```

---

## Get Email Intelligence

```
GET /api/v1/revenue/emails/{id}/intelligence
```

Detailed analysis including sentiment breakdown, topic keywords, response suggestions.

---

## Intelligence Fields

| Field | Description |
|-------|-------------|
| `sentiment` | `positive`, `neutral`, `negative` |
| `sentiment_score` | 0.0–1.0 confidence |
| `topics` | Array of detected topics with confidence |
| `urgency` | `low`, `medium`, `high` |
| `key_phrases` | Notable extracted phrases |
| `action_items` | Commitments or tasks identified |
| `response_needed` | Boolean |
| `suggested_response_by` | Recommended deadline |
