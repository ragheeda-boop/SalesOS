# Tutorial: Make Your First API Call

> **دليل تدريبي — أول طلب API مع شرح كامل**

This tutorial walks through a real-world scenario: finding a Saudi company, getting insights, creating an opportunity, and getting a recommendation.

---

## Scenario

You're a sales rep at "ACME Solutions." A new company appears on your radar: **شركة المملكة للتقنية** (Al-Mamlaka Technology). You need to:

1. Find and verify the company
2. Check its health and scores
3. Create an opportunity
4. Get a next-best-action recommendation

---

## Step 1: Authentication

Every request requires two headers:

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `Bearer <api_key>` | Your API key |
| `X-Tenant-Id` | `<tenant_id>` | Your tenant identifier |

```bash
AUTH="Authorization: Bearer sos_your_key"
TENANT="X-Tenant-Id: your-tenant-id"
BASE="https://api.salesos.sa/api/v1"
```

---

## Step 2: Search for the Company

```bash
curl -X GET "$BASE/search?q=%D8%B4%D8%B1%D9%83%D8%A9%20%D8%A7%D9%84%D9%85%D9%85%D9%84%D9%83%D8%A9%20%D9%84%D9%84%D8%AA%D9%82%D9%86%D9%8A%D8%A9&type=company" \
  -H "$AUTH" -H "$TENANT"
```

**Response:**

```json
{
  "results": [{
    "id": "comp_mamlaka_123",
    "name_ar": "شركة المملكة للتقنية",
    "name_en": "Al-Mamlaka Technology Co.",
    "cr_number": "4032156789",
    "city": "الرياض",
    "status": "active",
    "confidence": 0.97
  }]
}
```

Save the company ID: `comp_mamlaka_123`.

---

## Step 3: Get Company Profile

```bash
curl -X GET "$BASE/companies/comp_mamlaka_123" \
  -H "$AUTH" -H "$TENANT"
```

Examine key fields:

| Field | Value | What It Means |
|-------|-------|---------------|
| `status` | `active` | Company is operational |
| `is_golden_record` | `true` | Data verified from 3+ sources |
| `confidence_score` | `0.94` | High data quality |
| `employees_count` | `250` | Growing mid-size company |
| `capital` | `5,000,000 SAR` | Well-capitalized |
| `activity_code` | `6201` | Computer programming activities |

---

## Step 4: Check Scores and DNA

```bash
# Get company scores
curl -X GET "$BASE/companies/comp_mamlaka_123/scores" \
  -H "$AUTH" -H "$TENANT"

# Get company DNA profile
curl -X GET "$BASE/companies/comp_mamlaka_123/dna" \
  -H "$AUTH" -H "$TENANT"
```

Scores returned:

| Score Type | Value | Label |
|-----------|-------|-------|
| Company Strength | 0.82 | Strong |
| Buying Intent | 0.76 | High |
| Relationship | 0.45 | Developing |
| Data Quality | 0.94 | Excellent |
| Risk | 0.12 | Low |

---

## Step 5: Create an Opportunity

```bash
curl -X POST "$BASE/revenue/opportunities" \
  -H "$AUTH" -H "$TENANT" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "comp_mamlaka_123",
    "name": "Cloud Platform License — Al-Mamlaka Technology",
    "value": 350000,
    "currency": "SAR",
    "expected_close_date": "2026-09-30"
  }'
```

**Response** (save the opportunity ID):

```json
{
  "id": "opp_mamlaka_001",
  "stage": "qualification",
  "probability": 0.10,
  "health": "healthy",
  "created_at": "2026-07-11T10:00:00Z"
}
```

---

## Step 6: Get NBA Recommendation

```bash
curl -X GET "$BASE/revenue/opportunities/opp_mamlaka_001/nba" \
  -H "$AUTH" -H "$TENANT"
```

**Response:**

```json
{
  "id": "nba_mamlaka_001",
  "action": "Schedule discovery call",
  "reason": "New opportunity in qualification stage with strong company score (0.82) and high buying intent (0.76). Company is in active growth phase with 250 employees.",
  "confidence": 0.85,
  "confidence_label": "high",
  "source": "hybrid",
  "alternatives": [
    {"action": "Send introduction email", "confidence": 0.72},
    {"action": "Research company further", "confidence": 0.45}
  ]
}
```

---

## Step 7: Submit Feedback

After you act on the recommendation:

```bash
curl -X POST "$BASE/revenue/opportunities/opp_mamlaka_001/nba/accept" \
  -H "$AUTH" -H "$TENANT" \
  -H "Content-Type: application/json" \
  -d '{
    "nba_id": "nba_mamlaka_001",
    "action": "accepted"
  }'
```

---

## Complete Flow Diagram

```
Search → Find Company → Get Profile → Check Scores
                                              │
                                              ▼
                                    Create Opportunity
                                              │
                                              ▼
                                   Get NBA Recommendation
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                              Accept Action       Dismiss & Try
                                                    Alternative
```

---

## Next Steps

| Topic | Link |
|-------|------|
| API conventions | [API Overview](../api/overview.md) |
| All opportunity endpoints | [Opportunities API](../api/opportunities.md) |
| NBA engine details | [NBA API](../api/nba.md) |
| SDK usage | [Workspace SDK](../sdk/workspace-sdk.md) |
