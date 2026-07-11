# NBA — Next Best Action API

> **Next Best Action — محرك القرار الذكي الذي يوصي بالخطوة التالية**

Base path: `/api/v1/revenue/opportunities/{id}/nba`

The NBA Engine is SalesOS's decision intelligence layer. It converts opportunity context into an actionable recommendation with full explainability.

---

## Get NBA Recommendation

```
GET /api/v1/revenue/opportunities/{id}/nba
```

**Permissions:** `nba:read`

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/opportunities/opp_8f3a2b1c/nba" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-Id: <tenant_id>"
```

**Response (200):**

```json
{
  "id": "nba_1a2b3c",
  "opportunity_id": "opp_8f3a2b1c",
  "action": "Send proposal document",
  "action_label": "Send Proposal",
  "reason": "Opportunity is in proposal stage with high engagement. Company signed new government contract indicating budget.",
  "evidence": [
    {
      "id": "ev_001",
      "type": "business_rule",
      "description": "Stage is proposal — recommended action: send proposal",
      "source": "Rule: stage_based",
      "confidence": 0.9,
      "timestamp": "2026-07-11T08:00:00Z"
    },
    {
      "id": "ev_002",
      "type": "signal",
      "description": "Company signed new government contract — budget increase likely",
      "source": "Signal: government_tender",
      "confidence": 0.75,
      "timestamp": "2026-07-09T10:15:00Z"
    },
    {
      "id": "ev_003",
      "type": "ai_analysis",
      "description": "High engagement in last 7 days (3 meetings, 5 emails)",
      "source": "NBA Reasoner",
      "confidence": 0.85,
      "timestamp": "2026-07-11T08:00:05Z"
    }
  ],
  "confidence": 0.87,
  "confidence_label": "high",
  "source": "hybrid",
  "alternatives": [
    { "action": "Schedule technical demo", "confidence": 0.72 },
    { "action": "Send competitive brief", "confidence": 0.65 }
  ],
  "expected_impact": {
    "description": "Proposal delivery moves deal to negotiation",
    "estimated_revenue": 250000,
    "estimated_probability": 0.15
  },
  "potential_risks": [
    { "type": "competition", "level": "medium", "description": "Competitor signal detected" }
  ],
  "due_by": "2026-07-14",
  "status": "pending",
  "pipeline_trace": {
    "normalization_ms": 35,
    "rules_ms": 12,
    "scoring_ms": 18,
    "ai_ms": 1250,
    "total_ms": 1342
  },
  "created_at": "2026-07-11T08:00:00Z"
}
```

---

## Refresh NBA

```
POST /api/v1/revenue/opportunities/{id}/nba/refresh
```

**Permissions:** `nba:update`

Force recompute the NBA recommendation. Returns the new result.

---

## Accept NBA

```
POST /api/v1/revenue/opportunities/{id}/nba/accept
```

**Permissions:** `nba:update`

```json
{ "nba_id": "nba_1a2b3c", "action": "accepted" }
```

---

## Dismiss NBA

```
POST /api/v1/revenue/opportunities/{id}/nba/dismiss
```

**Permissions:** `nba:update`

```json
{ "nba_id": "nba_1a2b3c", "action": "dismissed", "reason": "I have a different plan" }
```

---

## Get NBA History

```
GET /api/v1/revenue/opportunities/{id}/nba/history
```

Returns all NBA recommendations for this opportunity with status.

---

## Action Types

| Action | When | Min Thresholds |
|--------|------|---------------|
| `meeting` | High intent + relationship | intent >= 0.6, relationship >= 0.5 |
| `send_proposal` | Strong relationship | relationship >= 0.6, intent >= 0.5 |
| `call` | Medium intent (re-engagement) | intent 0.3–0.75 |
| `follow_up` | Any positive intent | intent >= 0.2 |
| `demo` | Qualified entity | intent >= 0.4, company >= 0.4 |
| `nurture` | Early stage | intent <= 0.5, relationship <= 0.6 |
| `escalate` | High-value + risk | revenue >= 0.6, risk >= 0.4 |
| `research` | Low data quality | data_quality <= 0.6 |

---

## Confidence Model

```python
confidence = ruleScore × 0.4 + opportunityScore × 0.25
           + urgencyScore × 0.2 + effortScore × 0.15
           + riskAdjustment (-0.3 to 0)
```

| Label | Threshold |
|-------|-----------|
| High | >= 0.8 |
| Medium | >= 0.5 |
| Low | < 0.5 |

---

## Evidence Types

| Type | Description |
|------|-------------|
| `business_rule` | Deterministic rule match |
| `signal` | Real-time signal (hiring, contract, news) |
| `ai_analysis` | LLM-generated analysis |
| `company_score` | Feature store score |
| `activity` | Recent engagement metrics |
| `risk_factor` | Detected risk |

---

## Pipeline Trace

Every NBA returns performance timing:

| Field | Description |
|-------|-------------|
| `normalization_ms` | Context normalization |
| `rules_ms` | Rule evaluation |
| `scoring_ms` | Score computation |
| `ai_ms` | AI reasoning (0 if rule-only) |
| `risk_ms` | Risk assessment |
| `total_ms` | Total pipeline time |
