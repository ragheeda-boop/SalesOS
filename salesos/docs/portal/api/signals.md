# Signal Marketplace API

> **سوق الإشارات — تصفح واشتراك وتكوين إشارات الطرف الثالث**
> Base path: `/api/v1/signals`

---

## Authentication

All endpoints require `Authorization: Bearer <token>` and `X-Tenant-Id` headers.

---

## List Available Signals

```
GET /api/v1/signals
```

**Permissions:** `signals:read`

Returns all available signal providers in the marketplace.

```bash
curl -X GET "https://api.salesos.sa/api/v1/signals" \
  -H "Authorization: Bearer <token>"
```

Response:

```json
{
  "signals": [
    {
      "id": "sig-company-intent",
      "name": "Company Intent Signals",
      "provider": "IntentData Inc.",
      "category": "intent",
      "description": "Real-time buying intent signals for target accounts",
      "tier": "premium",
      "price_monthly": 499,
      "features": ["Web traffic analysis", "Job posting detection", "Tech stack changes"]
    }
  ],
  "total": 12
}
```

**Categories:** `intent`, `financial`, `news`, `regulatory`, `competitive`, `technographic`

---

## Get Signal Details

```
GET /api/v1/signals/{signal_id}
```

---

## Subscribe to Signal

```
POST /api/v1/signals/{signal_id}/subscribe
```

**Permissions:** `signals:write`

```json
{
  "config": {
    "frequency": "daily",
    "severity_threshold": "medium",
    "delivery_channels": ["in-app", "email"],
    "filters": {
      "industries": ["healthcare", "financial-services"],
      "regions": ["saudi-arabia", "uae"],
      "min_confidence": 0.7
    }
  }
}
```

---

## List Subscriptions

```
GET /api/v1/signals/subscriptions
```

Returns the tenant's active signal subscriptions with status and usage.

---

## Update Subscription

```
PUT /api/v1/signals/subscriptions/{subscription_id}
```

---

## Unsubscribe

```
DELETE /api/v1/signals/subscriptions/{subscription_id}
```

---

## Get Signal Events

```
GET /api/v1/signals/events?from=2026-07-01&to=2026-07-14&limit=50
```

Returns signal events for subscribed signals with severity, entity, and action recommendations.

---

## Related

| Resource | Link |
|----------|------|
| NBA Decision Platform | [NBA API](nba.md) |
| API Portal | [README.md](README.md) |
