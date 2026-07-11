# Wave 2 API Reference

> **Base Path:** `/api/v1/revenue`
> **Version:** v0.6.0
> **Authentication:** Bearer token (JWT) required on all endpoints

---

## Table of Contents

1. [Opportunities](#1-opportunities)
2. [NBA — Next Best Action](#2-nba--next-best-action)
3. [Pipeline Intelligence](#3-pipeline-intelligence)
4. [Meeting Intelligence](#4-meeting-intelligence)
5. [Email Intelligence](#5-email-intelligence)
6. [Revenue Dashboard](#6-revenue-dashboard)
7. [Common Schemas](#7-common-schemas)
8. [Error Responses](#8-error-responses)
9. [Rate Limiting](#9-rate-limiting)

---

## 1. Opportunities

### 1.1 List Opportunities

```
GET /api/v1/revenue/opportunities
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stage` | string | — | Filter by stage: `qualification`, `discovery`, `proposal`, `negotiation`, `closed_won`, `closed_lost` |
| `health` | string | — | Filter by health: `healthy`, `at_risk`, `critical` |
| `owner_id` | string | — | Filter by owner |
| `min_value` | number | — | Minimum opportunity value |
| `max_value` | number | — | Maximum opportunity value |
| `sort` | string | `created_at` | Sort field: `created_at`, `value`, `probability`, `updated_at` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | number | `1` | Page number |
| `limit` | number | `20` | Results per page (max 100) |

**Permissions:** `opportunity:read`

**Request:**

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/opportunities?stage=proposal&health=healthy&sort=value&order=desc&limit=10" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "data": [
    {
      "id": "opp_8f3a2b1c",
      "company_id": "comp_4d5e6f7g",
      "name": "Enterprise License — ACME Corp",
      "stage": "proposal",
      "value": 250000,
      "currency": "SAR",
      "probability": 0.65,
      "health": "healthy",
      "expected_close_date": "2026-08-15",
      "owner_id": "user_abc123",
      "owner_name": "Ahmed Al-Rashid",
      "playbook_id": "pb_9x8y7z",
      "nba": {
        "id": "nba_1a2b3c",
        "action": "Send proposal document",
        "reason": "Opportunity is in proposal stage with high engagement",
        "confidence": 0.87,
        "confidence_label": "high",
        "source": "hybrid"
      },
      "created_at": "2026-06-20T09:00:00Z",
      "updated_at": "2026-07-10T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 42,
    "total_pages": 5
  }
}
```

---

### 1.2 Get Opportunity

```
GET /api/v1/revenue/opportunities/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Opportunity ID |

**Permissions:** `opportunity:read`

**Request:**

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/opportunities/opp_8f3a2b1c" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "id": "opp_8f3a2b1c",
  "company_id": "comp_4d5e6f7g",
  "name": "Enterprise License — ACME Corp",
  "stage": "proposal",
  "value": 250000,
  "currency": "SAR",
  "probability": 0.65,
  "health": "healthy",
  "expected_close_date": "2026-08-15",
  "owner_id": "user_abc123",
  "owner_name": "Ahmed Al-Rashid",
  "playbook_id": "pb_9x8y7z",
  "playbook_name": "Enterprise Sales Playbook",
  "nba": {
    "id": "nba_1a2b3c",
    "action": "Send proposal document",
    "reason": "Opportunity is in proposal stage with high engagement and no recent proposal sent",
    "evidence": [
      {
        "id": "ev_001",
        "type": "business_rule",
        "description": "Stage is proposal — recommended to send proposal document",
        "source": "Rule: stage_based (proposal → send_proposal)",
        "confidence": 0.9,
        "timestamp": "2026-07-11T08:00:00Z"
      },
      {
        "id": "ev_002",
        "type": "signal",
        "description": "Company signed new government contract — budget increase likely",
        "source": "Signal: government_tender (ACME Corp)",
        "confidence": 0.75,
        "timestamp": "2026-07-09T10:15:00Z"
      },
      {
        "id": "ev_003",
        "type": "ai_analysis",
        "description": "High engagement in last 7 days (3 meetings, 5 emails). Decision maker actively involved.",
        "source": "NBA Reasoner — GPT-4 analysis",
        "confidence": 0.85,
        "timestamp": "2026-07-11T08:00:05Z"
      }
    ],
    "confidence": 0.87,
    "confidence_label": "high",
    "source": "hybrid",
    "alternatives": [
      {
        "action": "Schedule technical demo",
        "reason": "Technical team has not yet seen the product",
        "confidence": 0.72,
        "expected_impact": {
          "description": "Increases technical confidence and reduces evaluation risk",
          "estimated_revenue": null,
          "estimated_probability": 0.10,
          "category": "relationship"
        }
      },
      {
        "action": "Send competitive brief",
        "reason": "Competitor signal detected — ACME comparing solutions",
        "confidence": 0.65,
        "expected_impact": {
          "description": "Addresses competitive concern proactively",
          "estimated_revenue": null,
          "estimated_probability": 0.05,
          "category": "risk_mitigation"
        }
      }
    ],
    "expected_impact": {
      "description": "Proposal delivery moves deal to negotiation stage",
      "estimated_revenue": 250000,
      "estimated_probability": 0.15,
      "category": "revenue"
    },
    "potential_risks": [
      {
        "type": "competition",
        "level": "medium",
        "description": "Competitor signal detected — ACME is evaluating alternatives",
        "detected_at": "2026-07-09T10:15:00Z"
      }
    ],
    "due_by": "2026-07-14",
    "status": "pending",
    "created_at": "2026-07-11T08:00:00Z",
    "updated_at": "2026-07-11T08:00:00Z"
  },
  "stage_history": [
    { "stage": "qualification", "entered_at": "2026-06-20T09:00:00Z", "exited_at": "2026-06-25T14:00:00Z" },
    { "stage": "discovery", "entered_at": "2026-06-25T14:00:00Z", "exited_at": "2026-07-05T11:00:00Z" },
    { "stage": "proposal", "entered_at": "2026-07-05T11:00:00Z", "exited_at": null }
  ],
  "created_at": "2026-06-20T09:00:00Z",
  "updated_at": "2026-07-10T14:30:00Z"
}
```

---

### 1.3 Create Opportunity

```
POST /api/v1/revenue/opportunities
```

**Permissions:** `opportunity:create`

**Request Body:**

```json
{
  "company_id": "comp_4d5e6f7g",
  "name": "Cloud Migration — Saudi Telecom",
  "value": 500000,
  "currency": "SAR",
  "expected_close_date": "2026-09-30",
  "playbook_id": "pb_9x8y7z",
  "owner_id": "user_abc123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_id` | string | Yes | Company this opportunity belongs to |
| `name` | string | Yes | Opportunity name |
| `value` | number | No | Deal value (default: 0) |
| `currency` | string | No | Currency code (default: SAR) |
| `expected_close_date` | string | No | Expected close date (ISO 8601) |
| `playbook_id` | string | No | Playbook to assign |
| `owner_id` | string | No | Opportunity owner (default: authenticated user) |

**Request:**

```bash
curl -X POST "https://api.salesos.sa/api/v1/revenue/opportunities" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "comp_4d5e6f7g",
    "name": "Cloud Migration — Saudi Telecom",
    "value": 500000,
    "currency": "SAR",
    "expected_close_date": "2026-09-30"
  }'
```

**Response (201 Created):**

```json
{
  "id": "opp_new123",
  "company_id": "comp_4d5e6f7g",
  "name": "Cloud Migration — Saudi Telecom",
  "stage": "qualification",
  "value": 500000,
  "currency": "SAR",
  "probability": 0.10,
  "health": "healthy",
  "expected_close_date": "2026-09-30",
  "owner_id": "user_abc123",
  "owner_name": "Ahmed Al-Rashid",
  "playbook_id": null,
  "nba": null,
  "created_at": "2026-07-11T10:00:00Z",
  "updated_at": "2026-07-11T10:00:00Z"
}
```

---

### 1.4 Update Opportunity

```
PUT /api/v1/revenue/opportunities/{id}
```

**Permissions:** `opportunity:update`

**Request Body:**

```json
{
  "name": "Cloud Migration — Saudi Telecom (Phase 2)",
  "value": 750000,
  "expected_close_date": "2026-10-15"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New opportunity name |
| `value` | number | New deal value |
| `expected_close_date` | string | New expected close date |
| `playbook_id` | string | New playbook assignment |

**Response (200 OK):**

```json
{
  "id": "opp_new123",
  "company_id": "comp_4d5e6f7g",
  "name": "Cloud Migration — Saudi Telecom (Phase 2)",
  "stage": "qualification",
  "value": 750000,
  "currency": "SAR",
  "probability": 0.10,
  "health": "healthy",
  "expected_close_date": "2026-10-15",
  "owner_id": "user_abc123",
  "created_at": "2026-07-11T10:00:00Z",
  "updated_at": "2026-07-11T10:05:00Z"
}
```

---

### 1.5 Advance/Revert Stage

```
PATCH /api/v1/revenue/opportunities/{id}/stage
```

**Permissions:** `opportunity:update`

**Request Body:**

```json
{
  "stage": "negotiation",
  "reason": "Proposal accepted, entering contract negotiations"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stage` | string | Yes | Target stage: `qualification`, `discovery`, `proposal`, `negotiation`, `closed_won`, `closed_lost` |
| `reason` | string | No | Reason for stage change |

**Response (200 OK):**

```json
{
  "id": "opp_8f3a2b1c",
  "stage": "negotiation",
  "probability": 0.80,
  "stage_changed": true,
  "previous_stage": "proposal",
  "nba_recomputed": true,
  "updated_at": "2026-07-11T10:10:00Z"
}
```

> **Note:** Stage changes automatically trigger NBA recomputation and are logged to the Activity Runtime.

---

### 1.6 Delete Opportunity

```
DELETE /api/v1/revenue/opportunities/{id}
```

**Permissions:** `opportunity:delete`

**Response (204 No Content):**

```
(no body)
```

---

## 2. NBA — Next Best Action

### 2.1 Get NBA Recommendation

```
GET /api/v1/revenue/opportunities/{id}/nba
```

Returns the current NBA recommendation for an opportunity. Returns cached result if available, computes fresh if not.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Opportunity ID |

**Permissions:** `nba:read`

**Request:**

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/opportunities/opp_8f3a2b1c/nba" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "id": "nba_1a2b3c",
  "opportunity_id": "opp_8f3a2b1c",
  "action": "Send proposal document",
  "reason": "Opportunity is in proposal stage with high engagement and no recent proposal sent. Company recently signed a new government contract indicating budget availability.",
  "evidence": [
    {
      "id": "ev_001",
      "type": "business_rule",
      "description": "Stage is proposal — send proposal document",
      "source": "Rule: stage_based (proposal → send_proposal)",
      "confidence": 0.9,
      "timestamp": "2026-07-11T08:00:00Z",
      "data": { "rule_name": "stage_proposal_send_proposal", "rule_version": "1.2" }
    },
    {
      "id": "ev_002",
      "type": "signal",
      "description": "Company signed new government contract — budget increase likely",
      "source": "Signal: government_tender (ACME Corp, 2026-07-09)",
      "confidence": 0.75,
      "timestamp": "2026-07-09T10:15:00Z",
      "data": { "signal_category": "government_tender", "source_url": "https://..." }
    },
    {
      "id": "ev_003",
      "type": "ai_analysis",
      "description": "High engagement in last 7 days (3 meetings, 5 emails). Decision maker actively involved. No competitor signals in last 48h.",
      "source": "NBA Reasoner — GPT-4o analysis",
      "confidence": 0.85,
      "timestamp": "2026-07-11T08:00:05Z"
    },
    {
      "id": "ev_004",
      "type": "company_score",
      "description": "ICP score: 0.82 — Strong fit for enterprise tier",
      "source": "Feature Store: icp_score",
      "confidence": 0.82,
      "timestamp": "2026-07-10T00:00:00Z"
    },
    {
      "id": "ev_005",
      "type": "activity",
      "description": "3 meetings and 5 emails in the last 7 days — above engagement threshold",
      "source": "Activity Runtime: opportunity=opp_8f3a2b1c",
      "confidence": 0.9,
      "timestamp": "2026-07-10T16:00:00Z"
    }
  ],
  "confidence": 0.87,
  "confidence_label": "high",
  "source": "hybrid",
  "alternatives": [
    {
      "action": "Schedule technical demo",
      "reason": "Technical team has not yet seen the product demo",
      "confidence": 0.72,
      "expected_impact": {
        "description": "Increases technical confidence, reduces evaluation risk",
        "estimated_revenue": null,
        "estimated_probability": 0.10,
        "category": "relationship"
      }
    },
    {
      "action": "Send competitive brief",
      "reason": "Competitor signal detected on 2026-07-09 — ACME comparing solutions",
      "confidence": 0.65,
      "expected_impact": {
        "description": "Addresses competitive concern proactively",
        "estimated_revenue": null,
        "estimated_probability": 0.05,
        "category": "risk_mitigation"
      }
    },
    {
      "action": "Request referral from existing customer",
      "reason": "ACME Corp is in same industry as customer XYZ Ltd",
      "confidence": 0.45,
      "expected_impact": {
        "description": "Social proof increases conversion likelihood",
        "estimated_revenue": null,
        "estimated_probability": 0.08,
        "category": "relationship"
      }
    }
  ],
  "expected_impact": {
    "description": "Proposal delivery moves deal to negotiation stage, expected 15% probability increase",
    "estimated_revenue": 250000,
    "estimated_probability": 0.15,
    "category": "revenue"
  },
  "potential_risks": [
    {
      "type": "competition",
      "level": "medium",
      "description": "Competitor signal detected — ACME is evaluating alternatives",
      "detected_at": "2026-07-09T10:15:00Z"
    }
  ],
  "due_by": "2026-07-14",
  "status": "pending",
  "pipeline_trace": {
    "normalization_ms": 35,
    "rules_ms": 12,
    "scoring_ms": 18,
    "ai_ms": 1250,
    "risk_ms": 22,
    "confidence_ms": 5,
    "total_ms": 1342
  },
  "created_at": "2026-07-11T08:00:00Z",
  "updated_at": "2026-07-11T08:00:05Z"
}
```

**Response (404 Not Found):**

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "No NBA recommendation found for this opportunity",
    "details": "Opportunity opp_unknown does not exist or has no NBA computed"
  }
}
```

---

### 2.2 Refresh NBA

```
POST /api/v1/revenue/opportunities/{id}/nba/refresh
```

Force recompute NBA for an opportunity. Returns the new recommendation.

**Permissions:** `nba:update`

**Request:**

```bash
curl -X POST "https://api.salesos.sa/api/v1/revenue/opportunities/opp_8f3a2b1c/nba/refresh" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "id": "nba_4d5e6f",
  "opportunity_id": "opp_8f3a2b1c",
  "action": "Send follow-up email",
  "reason": "Last activity was 10 days ago — opportunity showing signs of stagnation",
  "confidence": 0.78,
  "confidence_label": "medium",
  "source": "hybrid",
  "status": "pending",
  "pipeline_trace": {
    "normalization_ms": 32,
    "rules_ms": 15,
    "scoring_ms": 20,
    "ai_ms": 1180,
    "risk_ms": 18,
    "confidence_ms": 4,
    "total_ms": 1269
  },
  "created_at": "2026-07-11T10:15:00Z",
  "updated_at": "2026-07-11T10:15:01Z"
}
```

---

### 2.3 Accept NBA

```
POST /api/v1/revenue/opportunities/{id}/nba/accept
```

Record user acceptance of the NBA recommendation.

**Permissions:** `nba:update`

**Request Body:**

```json
{
  "nba_id": "nba_1a2b3c",
  "action": "accepted",
  "reason": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nba_id` | string | Yes | The NBA recommendation ID |
| `action` | string | Yes | Must be `"accepted"` |
| `reason` | string | No | Optional user note |

**Response (200 OK):**

```json
{
  "success": true,
  "nba_id": "nba_1a2b3c",
  "status": "accepted",
  "recorded_at": "2026-07-11T10:20:00Z"
}
```

---

### 2.4 Dismiss NBA

```
POST /api/v1/revenue/opportunities/{id}/nba/dismiss
```

Record user dismissal of the NBA recommendation.

**Permissions:** `nba:update`

**Request Body:**

```json
{
  "nba_id": "nba_1a2b3c",
  "action": "dismissed",
  "reason": "I have a different plan for this opportunity"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nba_id` | string | Yes | The NBA recommendation ID |
| `action` | string | Yes | Must be `"dismissed"` |
| `reason` | string | No | Dismissal reason |

**Predefined dismissal reasons:**

- `"Not my target opportunity"`
- `"Opportunity is not ready yet"`
- `"I have a different plan"`
- `"Other"`

**Response (200 OK):**

```json
{
  "success": true,
  "nba_id": "nba_1a2b3c",
  "status": "dismissed",
  "recorded_at": "2026-07-11T10:20:00Z"
}
```

---

### 2.5 Get NBA History

```
GET /api/v1/revenue/opportunities/{id}/nba/history
```

Returns the history of NBA recommendations for an opportunity.

**Permissions:** `nba:read`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | `20` | Max history entries |
| `offset` | number | `0` | Pagination offset |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "nba_1a2b3c",
      "action": "Send proposal document",
      "status": "accepted",
      "confidence": 0.87,
      "source": "hybrid",
      "created_at": "2026-07-11T08:00:00Z",
      "decided_at": "2026-07-11T10:20:00Z"
    },
    {
      "id": "nba_prev456",
      "action": "Schedule discovery call",
      "status": "completed",
      "confidence": 0.82,
      "source": "rule",
      "created_at": "2026-07-05T09:00:00Z",
      "decided_at": "2026-07-05T11:30:00Z"
    },
    {
      "id": "nba_prev789",
      "action": "Send introduction email",
      "status": "completed",
      "confidence": 0.90,
      "source": "rule",
      "created_at": "2026-06-20T09:30:00Z",
      "decided_at": "2026-06-20T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 3,
    "limit": 20,
    "offset": 0
  }
}
```

---

## 3. Pipeline Intelligence

### 3.1 Get Pipeline Summary

```
GET /api/v1/revenue/pipeline
```

Returns aggregate pipeline metrics.

**Permissions:** `pipeline:read`

**Request:**

```bash
curl -X GET "https://api.salesos.sa/api/v1/revenue/pipeline" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "total_value": 2850000,
  "weighted_value": 1650000,
  "total_count": 42,
  "win_rate": 0.32,
  "avg_deal_size": 185000,
  "velocity_days": 67,
  "by_stage": {
    "qualification": {
      "count": 12,
      "value": 720000,
      "conversion_rate": 0.42
    },
    "discovery": {
      "count": 10,
      "value": 650000,
      "conversion_rate": 0.55
    },
    "proposal": {
      "count": 8,
      "value": 800000,
      "conversion_rate": 0.63
    },
    "negotiation": {
      "count": 5,
      "value": 480000,
      "conversion_rate": 0.80
    },
    "closed_won": {
      "count": 4,
      "value": 1200000,
      "conversion_rate": 1.0
    },
    "closed_lost": {
      "count": 3,
      "value": 0,
      "conversion_rate": 0.0
    }
  }
}
```

---

### 3.2 Get Stage Metrics

```
GET /api/v1/revenue/pipeline/stages
```

Returns detailed metrics per pipeline stage.

**Permissions:** `pipeline:read`

**Response (200 OK):**

```json
{
  "stages": [
    {
      "stage": "qualification",
      "count": 12,
      "value": 720000,
      "weighted_value": 72000,
      "avg_days_in_stage": 8,
      "conversion_rate": 0.42,
      "conversion_count": 5
    },
    {
      "stage": "discovery",
      "count": 10,
      "value": 650000,
      "weighted_value": 195000,
      "avg_days_in_stage": 12,
      "conversion_rate": 0.55,
      "conversion_count": 6
    },
    {
      "stage": "proposal",
      "count": 8,
      "value": 800000,
      "weighted_value": 320000,
      "avg_days_in_stage": 15,
      "conversion_rate": 0.63,
      "conversion_count": 5
    },
    {
      "stage": "negotiation",
      "count": 5,
      "value": 480000,
      "weighted_value": 384000,
      "avg_days_in_stage": 10,
      "conversion_rate": 0.80,
      "conversion_count": 4
    }
  ]
}
```

---

### 3.3 Get Health Map

```
GET /api/v1/revenue/pipeline/health
```

Returns health distribution across all open opportunities.

**Permissions:** `pipeline:read`

**Response (200 OK):**

```json
{
  "healthy": 28,
  "at_risk": 10,
  "critical": 4,
  "opportunities": [
    {
      "opportunity_id": "opp_8f3a2b1c",
      "name": "Enterprise License — ACME Corp",
      "health": "healthy",
      "owner": "Ahmed Al-Rashid",
      "value": 250000,
      "stage": "proposal"
    },
    {
      "opportunity_id": "opp_9g8h7i",
      "name": "Cloud Migration — STC",
      "health": "at_risk",
      "owner": "Sara Al-Harbi",
      "value": 500000,
      "stage": "negotiation"
    },
    {
      "opportunity_id": "opp_6j5k4l",
      "name": "Data Platform — Aramco",
      "health": "critical",
      "owner": "Mohammed Al-Fahad",
      "value": 1200000,
      "stage": "proposal"
    }
  ]
}
```

---

### 3.4 Get Pipeline Velocity

```
GET /api/v1/revenue/pipeline/velocity
```

Returns pipeline velocity metrics.

**Permissions:** `pipeline:read`

**Response (200 OK):**

```json
{
  "avg_cycle_days": 67,
  "avg_days_per_stage": {
    "qualification": 8,
    "discovery": 12,
    "proposal": 15,
    "negotiation": 10
  },
  "velocity_trend": [
    { "period": "2026-04", "days": 72 },
    { "period": "2026-05", "days": 69 },
    { "period": "2026-06", "days": 65 },
    { "period": "2026-07", "days": 67 }
  ],
  "fastest_close_days": 21,
  "slowest_close_days": 134
}
```

---

## 4. Meeting Intelligence

### 4.1 List Meetings

```
GET /api/v1/revenue/meetings
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `opportunity_id` | string | Filter by opportunity |
| `type` | string | `pre_meeting`, `during_meeting`, `post_meeting` |
| `from` | string | Start date (ISO 8601) |
| `to` | string | End date (ISO 8601) |
| `limit` | number | Results per page |
| `offset` | number | Pagination offset |

**Permissions:** `meeting:read`

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "mtg_abc123",
      "opportunity_id": "opp_8f3a2b1c",
      "title": "Discovery Meeting — ACME Corp",
      "type": "during_meeting",
      "scheduled_at": "2026-07-10T14:00:00Z",
      "duration_minutes": 45,
      "attendees": [
        { "name": "Ahmed Al-Rashid", "email": "ahmed@salesos.sa", "role": "sales" },
        { "name": "John Smith", "email": "john@acme.com", "role": "prospect" }
      ],
      "intelligence": {
        "summary": "Discussed ACME's cloud migration needs. Decision maker confirmed Q3 budget. Technical team needs demo.",
        "sentiment": "positive",
        "sentiment_score": 0.78,
        "action_items": [
          { "text": "Schedule technical demo", "owner": "Ahmed Al-Rashid", "due_date": "2026-07-15" },
          { "text": "Send proposal draft", "owner": "Ahmed Al-Rashid", "due_date": "2026-07-12" }
        ],
        "key_decisions": ["Budget confirmed for Q3", "Decision by end of August"]
      },
      "created_at": "2026-07-10T14:45:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

---

### 4.2 Create Meeting

```
POST /api/v1/revenue/meetings
```

**Permissions:** `meeting:create`

**Request Body:**

```json
{
  "opportunity_id": "opp_8f3a2b1c",
  "title": "Proposal Review — ACME Corp",
  "type": "during_meeting",
  "scheduled_at": "2026-07-15T10:00:00Z",
  "duration_minutes": 60,
  "attendees": [
    { "name": "Ahmed Al-Rashid", "email": "ahmed@salesos.sa" },
    { "name": "John Smith", "email": "john@acme.com" },
    { "name": "Jane Doe", "email": "jane@acme.com" }
  ],
  "notes": null
}
```

**Response (201 Created):**

```json
{
  "id": "mtg_def456",
  "opportunity_id": "opp_8f3a2b1c",
  "title": "Proposal Review — ACME Corp",
  "type": "during_meeting",
  "scheduled_at": "2026-07-15T10:00:00Z",
  "duration_minutes": 60,
  "attendees": [
    { "name": "Ahmed Al-Rashid", "email": "ahmed@salesos.sa" },
    { "name": "John Smith", "email": "john@acme.com" },
    { "name": "Jane Doe", "email": "jane@acme.com" }
  ],
  "intelligence": null,
  "created_at": "2026-07-11T10:30:00Z"
}
```

---

### 4.3 Generate Pre-Meeting Brief

```
POST /api/v1/revenue/meetings/{id}/brief
```

AI-generates a pre-meeting intelligence brief.

**Permissions:** `meeting:update`

**Response (200 OK):**

```json
{
  "meeting_id": "mtg_def456",
  "brief": {
    "company_overview": "ACME Corp is a leading construction company in Saudi Arabia with 500+ employees. Recent government contract win signals growth phase.",
    "contact_background": {
      "john_smith": "CTO, technical decision maker. Previously evaluated 3 cloud solutions.",
      "jane_doe": "CFO, budget approval authority. Attended last meeting."
    },
    "previous_interactions": [
      { "date": "2026-07-10", "type": "meeting", "summary": "Discovery meeting — confirmed Q3 budget" },
      { "date": "2026-07-05", "type": "email", "summary": "Sent introduction materials" }
    ],
    "talking_points": [
      "Reference Q3 budget confirmation from last meeting",
      "Lead with ROI analysis for cloud migration",
      "Address technical concerns from CTO evaluation",
      "Propose phased rollout to reduce perceived risk"
    ],
    "risks": [
      "CTO is evaluating competing solutions — differentiation is critical",
      "Budget approval still needs CFO sign-off"
    ]
  },
  "generated_at": "2026-07-11T10:35:00Z"
}
```

---

### 4.4 Generate Post-Meeting Summary

```
POST /api/v1/revenue/meetings/{id}/summary
```

AI-generates a post-meeting summary from notes and transcript.

**Permissions:** `meeting:update`

**Request Body:**

```json
{
  "notes": "Discussed cloud migration roadmap. CTO approved technical architecture. CFO approved budget. Decision by end of August. Need to send proposal by Friday.",
  "transcript": null
}
```

**Response (200 OK):**

```json
{
  "meeting_id": "mtg_def456",
  "summary": {
    "executive_summary": "Positive meeting with both technical and budget approval. Deal progressing to proposal stage.",
    "key_points": [
      "CTO approved technical architecture",
      "CFO approved budget allocation",
      "Decision timeline: end of August"
    ],
    "action_items": [
      { "text": "Send proposal by Friday", "owner": "Ahmed Al-Rashid", "due_date": "2026-07-14" },
      { "text": "Schedule technical deep-dive", "owner": "Ahmed Al-Rashid", "due_date": "2026-07-20" }
    ],
    "sentiment": "positive",
    "sentiment_score": 0.85,
    "next_steps": [
      "Move opportunity to proposal stage",
      "Send proposal document",
      "Schedule technical deep-dive"
    ]
  },
  "generated_at": "2026-07-10T15:30:00Z"
}
```

---

## 5. Email Intelligence

### 5.1 List Emails

```
GET /api/v1/revenue/emails
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `opportunity_id` | string | Filter by opportunity |
| `sentiment` | string | `positive`, `neutral`, `negative` |
| `urgency` | string | `low`, `medium`, `high` |
| `from` | string | Start date |
| `to` | string | End date |
| `limit` | number | Results per page |
| `offset` | number | Pagination offset |

**Permissions:** `email:read`

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "eml_xyz789",
      "opportunity_id": "opp_8f3a2b1c",
      "subject": "Re: Enterprise License Proposal",
      "from_address": "john@acme.com",
      "from_name": "John Smith",
      "to_address": "ahmed@salesos.sa",
      "direction": "inbound",
      "received_at": "2026-07-10T16:00:00Z",
      "intelligence": {
        "sentiment": "positive",
        "sentiment_score": 0.72,
        "topics": [
          { "topic": "pricing", "confidence": 0.85 },
          { "topic": "timeline", "confidence": 0.78 },
          { "topic": "technical_requirements", "confidence": 0.65 }
        ],
        "urgency": "medium",
        "urgency_reason": "Prospect asking about pricing details — indicates active evaluation",
        "key_phrases": ["pricing details", "Q3 timeline", "enterprise license"],
        "action_items": [
          "Send pricing breakdown by EOD tomorrow"
        ]
      },
      "created_at": "2026-07-10T16:00:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

---

### 5.2 Create Email (Manual Logging)

```
POST /api/v1/revenue/emails
```

Manually log an email to an opportunity.

**Permissions:** `email:create`

**Request Body:**

```json
{
  "opportunity_id": "opp_8f3a2b1c",
  "subject": "Enterprise License Proposal — ACME Corp",
  "from_address": "ahmed@salesos.sa",
  "from_name": "Ahmed Al-Rashid",
  "to_address": "john@acme.com",
  "direction": "outbound",
  "body": "Dear John,\n\nPlease find attached the enterprise license proposal for ACME Corp...",
  "sent_at": "2026-07-10T15:00:00Z"
}
```

**Response (201 Created):**

```json
{
  "id": "eml_new456",
  "opportunity_id": "opp_8f3a2b1c",
  "subject": "Enterprise License Proposal — ACME Corp",
  "from_address": "ahmed@salesos.sa",
  "to_address": "john@acme.com",
  "direction": "outbound",
  "sent_at": "2026-07-10T15:00:00Z",
  "intelligence": {
    "sentiment": "neutral",
    "sentiment_score": 0.50,
    "topics": [
      { "topic": "proposal", "confidence": 0.92 },
      { "topic": "pricing", "confidence": 0.70 }
    ],
    "urgency": "low",
    "urgency_reason": "Outbound proposal — waiting for response",
    "key_phrases": ["enterprise license", "proposal", "pricing"],
    "action_items": []
  },
  "created_at": "2026-07-11T10:40:00Z"
}
```

---

### 5.3 Get Email Intelligence

```
GET /api/v1/revenue/emails/{id}/intelligence
```

Returns detailed intelligence analysis for a specific email.

**Permissions:** `email:read`

**Response (200 OK):**

```json
{
  "email_id": "eml_xyz789",
  "intelligence": {
    "sentiment": "positive",
    "sentiment_score": 0.72,
    "sentiment_breakdown": {
      "positive_phrases": ["looks great", "very interested", "good timeline"],
      "negative_phrases": ["concerned about"],
      "neutral_phrases": ["please send", "let me know"]
    },
    "topics": [
      { "topic": "pricing", "confidence": 0.85, "keywords": ["pricing details", "cost", "budget"] },
      { "topic": "timeline", "confidence": 0.78, "keywords": ["Q3", "timeline", "by August"] },
      { "topic": "technical_requirements", "confidence": 0.65, "keywords": ["integration", "API", "deployment"] }
    ],
    "urgency": "medium",
    "urgency_reason": "Prospect asking about pricing details — indicates active evaluation phase",
    "key_phrases": ["pricing details", "Q3 timeline", "enterprise license", "very interested"],
    "action_items": [
      "Send pricing breakdown by EOD tomorrow",
      "Include Q3 implementation timeline in proposal"
    ],
    "response_needed": true,
    "suggested_response_by": "2026-07-11T17:00:00Z"
  },
  "analyzed_at": "2026-07-10T16:05:00Z"
}
```

---

## 6. Revenue Dashboard

### 6.1 Get Revenue Dashboard

```
GET /api/v1/revenue/dashboard
```

Returns the unified Revenue Workspace dashboard data.

**Permissions:** `pipeline:read` + `opportunity:read`

**Response (200 OK):**

```json
{
  "target": {
    "period": "Q3_2026",
    "target_revenue": 5000000,
    "current_revenue": 1200000,
    "achievement_pct": 0.24
  },
  "forecast": {
    "pipeline": 2850000,
    "best_case": 1650000,
    "commit": 980000,
    "closed_won": 1200000
  },
  "pipeline_summary": {
    "total_value": 2850000,
    "weighted_value": 1650000,
    "total_count": 42,
    "win_rate": 0.32,
    "velocity_days": 67
  },
  "health_map": {
    "healthy": 28,
    "at_risk": 10,
    "critical": 4
  },
  "nba_stats": {
    "total_recommendations": 156,
    "accepted": 98,
    "dismissed": 38,
    "completed": 12,
    "acceptance_rate": 0.63,
    "avg_time_to_accept_hours": 4.2
  },
  "team_performance": [
    {
      "user_id": "user_abc123",
      "name": "Ahmed Al-Rashid",
      "open_opportunities": 8,
      "total_value": 620000,
      "closed_won_value": 450000,
      "win_rate": 0.38,
      "avg_cycle_days": 58
    },
    {
      "user_id": "user_def456",
      "name": "Sara Al-Harbi",
      "open_opportunities": 6,
      "total_value": 480000,
      "closed_won_value": 320000,
      "win_rate": 0.35,
      "avg_cycle_days": 62
    }
  ],
  "at_risk_deals": [
    {
      "opportunity_id": "opp_6j5k4l",
      "name": "Data Platform — Aramco",
      "value": 1200000,
      "health": "critical",
      "days_stagnant": 18,
      "risks": ["stagnation", "timeline_slip"]
    }
  ],
  "communication_summary": {
    "meetings_this_week": 12,
    "emails_this_week": 34,
    "avg_sentiment": 0.68,
    "response_rate": 0.82
  }
}
```

---

## 7. Common Schemas

### Opportunity

```typescript
interface Opportunity {
  id: string
  company_id: string
  name: string
  stage: 'qualification' | 'discovery' | 'proposal' | 'negotiation' | 'closed_won' | 'closed_lost'
  value: number
  currency: string
  probability: number
  health: 'healthy' | 'at_risk' | 'critical'
  expected_close_date: string | null
  owner_id: string
  owner_name: string
  playbook_id: string | null
  nba: NBAResponse | null
  created_at: string
  updated_at: string
}
```

### NBAResponse

```typescript
interface NBAResponse {
  id: string
  opportunity_id: string
  action: string
  reason: string
  evidence: Evidence[]
  confidence: number
  confidence_label: 'high' | 'medium' | 'low'
  source: 'rule' | 'ai' | 'hybrid'
  alternatives: Alternative[]
  expected_impact: Impact
  potential_risks: Risk[]
  due_by: string | null
  status: 'pending' | 'accepted' | 'dismissed' | 'completed'
  pipeline_trace: PipelineTrace
  created_at: string
  updated_at: string
}

interface Evidence {
  id: string
  type: 'business_rule' | 'signal' | 'ai_analysis' | 'company_score' | 'activity' | 'risk_factor'
  description: string
  source: string
  confidence: number
  timestamp: string
  data: Record<string, unknown> | null
}

interface Alternative {
  action: string
  reason: string
  confidence: number
  expected_impact: Impact | null
}

interface Impact {
  description: string
  estimated_revenue: number | null
  estimated_probability: number | null
  category: 'revenue' | 'relationship' | 'risk_mitigation' | 'information_gathering'
}

interface Risk {
  type: 'stagnation' | 'competition' | 'engagement_drop' | 'stakeholder_change' | 'budget_concern' | 'timeline_slip'
  level: 'low' | 'medium' | 'high'
  description: string
  detected_at: string
}

interface PipelineTrace {
  normalization_ms: number
  rules_ms: number
  scoring_ms: number
  ai_ms: number
  risk_ms: number
  confidence_ms: number
  total_ms: number
}
```

### Pagination

```typescript
interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    total_pages: number
  }
}
```

---

## 8. Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context (optional)"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NOT_FOUND` | 404 | Resource does not exist |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `AI_TIMEOUT` | 504 | AI reasoning timed out (NBA falls back to rule-only) |

### Validation Error Example

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request body validation failed",
    "details": [
      {
        "field": "value",
        "message": "Must be a positive number"
      },
      {
        "field": "expected_close_date",
        "message": "Must be a future date"
      }
    ]
  }
}
```

---

## 9. Rate Limiting

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| GET endpoints | 100 requests | per minute |
| POST/PUT/PATCH endpoints | 30 requests | per minute |
| DELETE endpoints | 10 requests | per minute |
| NBA refresh | 5 requests | per minute |
| AI-powered endpoints (brief, summary) | 10 requests | per minute |

**Headers:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1720700460
```

**429 Response:**

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "retry_after": 60
  }
}
```

---

*Wave 2 API Reference — SalesOS v0.6.0*
