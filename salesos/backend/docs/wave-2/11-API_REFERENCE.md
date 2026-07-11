# Wave 2 — API Reference

> Last updated: 2026-07-11
> Source: SalesOS Backend v0.1.0
> Auto-generated docs: `GET /docs` (Swagger UI) and `GET /redoc` (ReDoc) — available when `DEBUG=true`.

---

## Table of Contents

1. [Authentication & Headers](#authentication--headers)
2. [Rate Limiting](#rate-limiting)
3. [Opportunity CRUD](#opportunity-crud)
4. [Meeting & Email Intelligence](#meeting--email-intelligence)
5. [Revenue Dashboard](#revenue-dashboard)
6. [NBA Engine](#nba-engine)
7. [Pipeline Analytics](#pipeline-analytics)
8. [Registration Notes](#registration-notes)

---

## Authentication & Headers

Every authenticated endpoint requires:

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer <JWT>` — issued by `/api/v1/identity/login` |
| `X-Tenant-Id` | Yes | Tenant UUID — must match the authenticated user's tenant |
| `X-Request-ID` | No | Auto-generated if absent (via `RequestIDMiddleware`) |

**RBAC**: Permission checks use `require_permission_dep(action, resource)` which validates the user's role against the `PermissionEnforcer` matrix. Roles: `admin` (3) > `manager` (2) > `user` (1) = `api` (1) > `auditor` (0).

---

## Rate Limiting

Two layers of rate limiting:

1. **Global**: 60 req/min per user (via `RateLimitMiddleware`, Redis-backed with in-memory fallback)
2. **Per-resource**: Configured via `rate_limit_dep(resource, limit, window)` — returns `429` with `Retry-After` header

| Resource | Limit | Window | Scope |
|----------|-------|--------|-------|
| `opportunity` | 60 | 60s | Router-level (opportunities.py) |
| `meeting_brief` | 10 | 60s | Per-endpoint |
| `meeting_summary` | 10 | 60s | Per-endpoint |
| `email_analyze` | 20 | 60s | Per-endpoint |
| `revenue` | 15 | 60s | Router-level (revenue.py) |
| `nba` | 30 | 60s | Router-level (nba_engine) |
| `pipeline` | 20 | 60s | Router-level (pipeline_analytics) |

---

## Opportunity CRUD

> Router: `app/routers/opportunities.py`
> Mount: **Not currently registered in `main.py`** (see [Registration Notes](#registration-notes))
> Global rate limit: 60 req/min

---

### GET /opportunities
**Description**: List opportunities with optional filters. Returns paginated results.

**Auth**: `READ` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `stage` | string | null | Filter by pipeline stage |
| `status` | string | null | Filter by status (open, closed, won, lost) |
| `company_id` | string | null | Filter by company |
| `owner_id` | string | null | Filter by owner |
| `limit` | int | 50 | Max results (1–200) |
| `offset` | int | 0 | Pagination offset |

**Response** (200):
```json
[
  {
    "id": "opp-abc-123",
    "company_id": "comp-456",
    "name": "Enterprise License Deal",
    "stage": "proposal",
    "value": 150000.00,
    "currency": "SAR",
    "probability": 0.65,
    "health": "healthy",
    "expected_close_date": "2026-08-15",
    "owner_id": "user-789",
    "status": "open",
    "description": "Multi-year enterprise license",
    "created_at": "2026-07-01T10:00:00Z",
    "updated_at": "2026-07-10T14:30:00Z"
  }
]
```

**Errors**: 401 (unauthorized), 403 (forbidden), 429 (rate limited), 503 (service not initialized)

---

### GET /opportunities/{opportunity_id}
**Description**: Get a single opportunity by ID. Validates tenant ownership.

**Auth**: `READ` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Response** (200):
```json
{
  "id": "opp-abc-123",
  "company_id": "comp-456",
  "name": "Enterprise License Deal",
  "stage": "proposal",
  "value": 150000.00,
  "currency": "SAR",
  "probability": 0.65,
  "health": "healthy",
  "expected_close_date": "2026-08-15",
  "owner_id": "user-789",
  "status": "open",
  "description": "Multi-year enterprise license",
  "created_at": "2026-07-01T10:00:00Z",
  "updated_at": "2026-07-10T14:30:00Z"
}
```

**Errors**: 401, 403, 404 (not found or tenant mismatch), 429, 503

---

### POST /opportunities
**Description**: Create a new opportunity.

**Auth**: `CREATE` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Request Body**:
```json
{
  "company_id": "comp-456",
  "name": "Enterprise License Deal",
  "value": 150000.00,
  "currency": "SAR",
  "expected_close_date": "2026-08-15",
  "owner_id": "user-789",
  "description": "Multi-year enterprise license"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `company_id` | string | Yes | — | Associated company ID |
| `name` | string | Yes | — | Opportunity name |
| `value` | float | No | 0.0 | Deal value |
| `currency` | string | No | "SAR" | Currency code |
| `expected_close_date` | date | No | null | Expected close date |
| `owner_id` | string | No | "" | Assigned owner |
| `description` | string | No | "" | Description |

**Response** (201): `OpportunityResponse` (same shape as GET)

**Errors**: 401, 403, 429, 503

---

### PUT /opportunities/{opportunity_id}
**Description**: Update an existing opportunity. Only provided fields are changed.

**Auth**: `UPDATE` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Request Body**:
```json
{
  "name": "Updated Deal Name",
  "value": 200000.00,
  "expected_close_date": "2026-09-01",
  "description": "Updated description"
}
```

All fields optional. Only non-null values are applied.

**Response** (200): `OpportunityResponse`

**Errors**: 401, 403, 404, 429, 503

---

### PATCH /opportunities/{opportunity_id}/stage
**Description**: Advance or change the pipeline stage of an opportunity.

**Auth**: `UPDATE` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Request Body**:
```json
{
  "stage": "negotiation",
  "reason": "Budget approved by CFO"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stage` | string | Yes | Target stage name |
| `reason` | string | No | Reason for change |

**Response** (200): `OpportunityResponse`

**Errors**: 400 (invalid stage transition), 401, 403, 404, 429, 503

---

### POST /opportunities/{opportunity_id}/close-won
**Description**: Mark an opportunity as won. Optionally specify the final amount.

**Auth**: `UPDATE` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `won_amount` | float | No | Final won amount (defaults to opportunity value) |

**Response** (200): `OpportunityResponse` with `status: "won"`

**Errors**: 400 (invalid close operation), 401, 403, 404, 429, 503

---

### POST /opportunities/{opportunity_id}/close-lost
**Description**: Mark an opportunity as lost with an optional reason.

**Auth**: `UPDATE` on `opportunity`

**Rate Limit**: 60/min (router-level)

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `loss_reason` | string | No | Reason for loss |

**Response** (200): `OpportunityResponse` with `status: "lost"`

**Errors**: 400 (invalid close operation), 401, 403, 404, 429, 503

---

## Meeting & Email Intelligence

> Router: `app/routers/meetings.py`
> Mount: **Not currently registered in `main.py`** (see [Registration Notes](#registration-notes))

---

### GET /meetings/{opportunity_id}
**Description**: List meetings for an opportunity, ordered by date descending. Limited to 50 results.

**Auth**: `READ` on `meeting`

**Rate Limit**: 60/min (global)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Response** (200):
```json
[
  {
    "id": "mtg-001",
    "title": "QBR Review",
    "meeting_date": "2026-07-10T14:00:00Z",
    "duration_minutes": 45,
    "notes": "Discussed roadmap alignment...",
    "status": "completed"
  }
]
```

**Errors**: 401, 403, 500

---

### POST /meetings/{opportunity_id}/brief
**Description**: Generate an AI-powered meeting brief for an upcoming meeting. Aggregates company signals, past interactions, and deal context.

**Auth**: `READ` on `meeting`

**Rate Limit**: 10/min (per-endpoint)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Response** (200):
```json
{
  "opportunity_id": "opp-abc-123",
  "company_name": "ACME Corp",
  "brief": "Key discussion points: budget cycle, technical requirements...",
  "recent_signals": [...],
  "talking_points": [...]
}
```

**Errors**: 401, 403, 404 (opportunity not found), 429, 500

---

### POST /meetings/{opportunity_id}/summary
**Description**: Generate an AI-powered summary from meeting notes.

**Auth**: `CREATE` on `meeting`

**Rate Limit**: 10/min (per-endpoint)

**Request Body**:
```json
{
  "notes": "Full meeting transcript or notes text (max 50,000 chars)",
  "meeting_id": "mtg-001"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notes` | string | Yes | Meeting notes content |
| `meeting_id` | string | No | Associated meeting ID |

**Response** (200):
```json
{
  "summary": "...",
  "action_items": [...],
  "key_decisions": [...]
}
```

**Errors**: 401, 403, 429, 500

---

### GET /emails/{opportunity_id}
**Description**: List emails for an opportunity with body previews (truncated to 200 chars).

**Auth**: `READ` on `email`

**Rate Limit**: 60/min (global)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Response** (200):
```json
[
  {
    "id": "em-001",
    "subject": "RE: Proposal Follow-up",
    "from_address": "buyer@acme.com",
    "to_addresses": ["rep@salesos.com"],
    "direction": "inbound",
    "email_type": "general",
    "sent_at": "2026-07-10T09:15:00Z",
    "body_preview": "Thanks for the proposal. We've reviewed..."
  }
]
```

**Errors**: 401, 403, 500

---

### POST /emails/analyze
**Description**: Analyze an email for sentiment, intent, and key topics without persisting it.

**Auth**: `CREATE` on `email`

**Rate Limit**: 20/min (per-endpoint)

**Request Body**:
```json
{
  "opportunity_id": "opp-abc-123",
  "subject": "RE: Proposal Follow-up",
  "from_address": "buyer@acme.com",
  "to_addresses": ["rep@salesos.com"],
  "body": "Full email body text (max 50,000 chars)",
  "direction": "inbound",
  "email_type": "general"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `opportunity_id` | string | Yes | max 100 chars |
| `subject` | string | Yes | max 500 chars |
| `from_address` | string | Yes | max 254 chars |
| `to_addresses` | string[] | No | max 20 items |
| `body` | string | Yes | max 50,000 chars |
| `direction` | string | No | `"inbound"` or `"outbound"` (default: `"outbound"`) |
| `email_type` | string | No | max 50 chars (default: `"general"`) |

**Response** (200):
```json
{
  "sentiment": "positive",
  "intent": "buying_signal",
  "key_topics": ["budget", "timeline"],
  "urgency": "medium"
}
```

**Errors**: 401, 403, 429, 500

---

## Revenue Dashboard

> Router: `app/routers/revenue.py`
> Mount: **Not currently registered in `main.py`** (see [Registration Notes](#registration-notes))
> Global rate limit: 15 req/min

---

### GET /revenue/dashboard
**Description**: Unified revenue dashboard. Aggregates pipeline summary, active opportunities (top 10 by value), total pipeline value, and recent company signals in a single call.

**Auth**: `READ` on `revenue`

**Rate Limit**: 15/min (router-level)

**Response** (200):
```json
{
  "pipeline_summary": {
    "total_value": 1250000.00,
    "weighted_value": 875000.00,
    "deal_count": 24,
    "avg_deal_size": 52083.33,
    "win_rate": 0.32
  },
  "active_opportunities": [
    {
      "id": "opp-abc-123",
      "name": "Enterprise License Deal",
      "stage": "proposal",
      "value": 150000.00,
      "probability": 0.65,
      "health": "healthy",
      "company_id": "comp-456",
      "owner_id": "user-789"
    }
  ],
  "total_value": 1250000.00,
  "opportunity_count": 24,
  "recent_signals": [
    {
      "id": "sig-001",
      "title": "Funding Round Announced",
      "signal_type": "funding",
      "created_at": "2026-07-10T08:00:00Z",
      "company_name": "ACME Corp"
    }
  ]
}
```

**Errors**: 401, 403, 429, 500

---

## NBA Engine

> Router: `runtime/nba_engine/api/router.py`
> Mount: **Not currently registered in `main.py`** (see [Registration Notes](#registration-notes))
> Global rate limit: 30 req/min

---

### GET /opportunities/{opportunity_id}/nba
**Description**: Get the current Next Best Action recommendation for an opportunity. Returns cached result if available, otherwise computes fresh.

**Auth**: `READ` on `nba`

**Rate Limit**: 30/min (router-level)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Response** (200):
```json
{
  "id": "nba-001",
  "opportunity_id": "opp-abc-123",
  "action": "Schedule technical deep-dive",
  "reason": "Prospect has been comparing competitors for 14 days without a technical evaluation",
  "confidence": 0.82,
  "confidence_label": "high",
  "source": "deal_health + engagement",
  "alternatives": [
    {
      "action": "Send ROI calculator",
      "reason": "Budget stakeholders not yet engaged",
      "confidence": 0.65
    }
  ],
  "evidence": [
    {
      "type": "stage_aging",
      "description": "14 days in evaluation stage (avg: 8 days)",
      "source": "pipeline_analytics",
      "confidence": 0.9
    }
  ],
  "potential_risks": [
    {
      "type": "competitor",
      "level": "medium",
      "description": "Competitor X also in final evaluation"
    }
  ],
  "status": "pending",
  "created_at": "2026-07-10T14:00:00Z",
  "updated_at": "2026-07-10T14:00:00Z"
}
```

**Errors**: 401, 403, 404 (opportunity not found), 429, 503 (engine not initialized)

---

### POST /opportunities/{opportunity_id}/nba/refresh
**Description**: Force recompute the Next Best Action, bypassing cache. Use when context has changed significantly.

**Auth**: `CREATE` on `nba`

**Rate Limit**: 30/min (router-level)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Response** (200): Same shape as `GET /opportunities/{opportunity_id}/nba`

**Errors**: 401, 403, 404, 429, 503

---

### POST /opportunities/{opportunity_id}/nba/feedback
**Description**: Record user feedback on an NBA recommendation (accepted or dismissed). Feeds back into the recommendation engine.

**Auth**: `UPDATE` on `nba`

**Rate Limit**: 30/min (router-level)

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `opportunity_id` | string | Opportunity UUID |

**Request Body**:
```json
{
  "nba_id": "nba-001",
  "action": "accepted",
  "reason": "Scheduled the meeting for next Tuesday"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `nba_id` | string | Yes | max 100 chars |
| `action` | string | Yes | `"accepted"` or `"dismissed"` |
| `reason` | string | No | max 1,000 chars |

**Response** (200):
```json
{
  "status": "ok"
}
```

**Errors**: 401 (user identity required), 403, 429, 503

---

## Pipeline Analytics

> Router: `runtime/pipeline_analytics/router.py`
> Mount: **Not currently registered in `main.py`** (see [Registration Notes](#registration-notes))
> Global rate limit: 20 req/min

---

### GET /pipeline/summary
**Description**: Get pipeline summary with aggregated metrics across all stages.

**Auth**: `READ` on `pipeline`

**Rate Limit**: 20/min (router-level)

**Response** (200):
```json
{
  "total_value": 1250000.00,
  "weighted_value": 875000.00,
  "deal_count": 24,
  "avg_deal_size": 52083.33,
  "win_rate": 0.32,
  "stages": {
    "discovery": { "count": 8, "value": 400000 },
    "proposal": { "count": 6, "value": 500000 },
    "negotiation": { "count": 4, "value": 250000 },
    "closed_won": { "count": 6, "value": 100000 }
  }
}
```

**Errors**: 401, 403, 429, 500

---

### GET /pipeline/velocity
**Description**: Get pipeline velocity metrics — average time in each stage and overall cycle time.

**Auth**: `READ` on `pipeline`

**Rate Limit**: 20/min (router-level)

**Response** (200):
```json
{
  "avg_cycle_days": 42,
  "avg_stage_days": {
    "discovery": 7,
    "qualification": 5,
    "proposal": 12,
    "negotiation": 10
  },
  "velocity_trend": "improving"
}
```

**Errors**: 401, 403, 429, 500

---

### GET /pipeline/conversion
**Description**: Get stage-to-stage conversion rates.

**Auth**: `READ` on `pipeline`

**Rate Limit**: 20/min (router-level)

**Response** (200):
```json
{
  "overall_win_rate": 0.32,
  "stage_conversions": {
    "discovery_to_qualification": 0.75,
    "qualification_to_proposal": 0.60,
    "proposal_to_negotiation": 0.55,
    "negotiation_to_won": 0.45
  },
  "drop_off_points": ["proposal_to_negotiation"]
}
```

**Errors**: 401, 403, 429, 500

---

### GET /pipeline/health
**Description**: Get pipeline health map — per-opportunity health scores aggregated by stage.

**Auth**: `READ` on `pipeline`

**Rate Limit**: 20/min (router-level)

**Response** (200):
```json
{
  "healthy": 16,
  "at_risk": 5,
  "critical": 3,
  "health_by_stage": {
    "proposal": { "healthy": 4, "at_risk": 1, "critical": 1 },
    "negotiation": { "healthy": 2, "at_risk": 1, "critical": 1 }
  },
  "at_risk_opportunities": [
    {
      "id": "opp-xyz",
      "name": "Stale Enterprise Deal",
      "health": "critical",
      "days_in_stage": 28
    }
  ]
}
```

**Errors**: 401, 403, 429, 500

---

### GET /pipeline/forecast
**Description**: Get pipeline forecast with projected revenue scenarios (best, expected, worst case).

**Auth**: `READ` on `pipeline`

**Rate Limit**: 20/min (router-level)

**Response** (200):
```json
{
  "best_case": 1500000.00,
  "expected": 875000.00,
  "worst_case": 450000.00,
  "confidence": 0.72,
  "forecast_date": "2026-07-10",
  "horizon_months": 3
}
```

**Errors**: 401, 403, 429, 500

---

## Registration Notes

### Routers in `main.py` (active)

The following Wave 2 routers are **NOT currently registered** in `app/main.py:register_routers()`. They are defined but not mounted:

| Router File | Prefix | Status |
|-------------|--------|--------|
| `app/routers/opportunities.py` | — | Defined, not registered |
| `app/routers/meetings.py` | — | Defined, not registered |
| `app/routers/revenue.py` | — | Defined, not registered |
| `runtime/nba_engine/api/router.py` | — | Defined, not registered |
| `runtime/pipeline_analytics/router.py` | — | Defined, not registered |

### What IS registered (overlapping endpoints)

These registered routers provide **similar or identical functionality**:

| Registered Router | Prefix | Overlapping Endpoints |
|-------------------|--------|-----------------------|
| `app/routers/commercial.py` | `/api/v1/commercial` | Opportunities CRUD, Pipeline, Activity, Quotes, Proposals, Contracts, Forecast, Analytics, Decision, Workspace |
| `app/modules/revenue_execution/router.py` | `/api/v1` | Opportunities (create, list, stage update), Tasks, Pipeline |

### To register the Wave 2 routers

Add to `register_routers()` in `app/main.py`:

```python
from app.routers.opportunities import router as opportunities_router
from app.routers.meetings import router as meetings_router
from app.routers.revenue import router as revenue_router
from runtime.nba_engine.api.router import router as nba_router
from runtime.pipeline_analytics.router import pipeline_analytics_router as pipeline_router

app.include_router(opportunities_router, prefix="/api/v1", tags=["Opportunities"], dependencies=_auth)
app.include_router(meetings_router, prefix="/api/v1", tags=["Meetings & Emails"], dependencies=_auth)
app.include_router(revenue_router, prefix="/api/v1", tags=["Revenue Dashboard"], dependencies=_auth)
app.include_router(nba_router, prefix="/api/v1", tags=["NBA Engine"], dependencies=_auth)
app.include_router(pipeline_router, prefix="/api/v1", tags=["Pipeline Analytics"], dependencies=_auth)
```

### Swagger / ReDoc

FastAPI auto-generates interactive docs when `DEBUG=true`:

| Endpoint | Description |
|----------|-------------|
| `GET /docs` | Swagger UI |
| `GET /redoc` | ReDoc |

Configured at `app/main.py:269`:
```python
docs_url="/docs" if settings.debug else None,
redoc_url="/redoc" if settings.debug else None,
```

### Global Endpoints (no auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info (name, version, docs link) |
| GET | `/ping` | Simple liveness check |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/health/ready` | Kubernetes readiness probe (checks DB, Neo4j) |
| GET | `/health` | Full health check (DB, Redis, Neo4j) |

---

## Summary: All Wave 2 Endpoints

| # | Method | Path | Auth | Rate | Router |
|---|--------|------|------|------|--------|
| 1 | GET | `/opportunities` | READ:opportunity | 60/min | opportunities.py |
| 2 | GET | `/opportunities/{id}` | READ:opportunity | 60/min | opportunities.py |
| 3 | POST | `/opportunities` | CREATE:opportunity | 60/min | opportunities.py |
| 4 | PUT | `/opportunities/{id}` | UPDATE:opportunity | 60/min | opportunities.py |
| 5 | PATCH | `/opportunities/{id}/stage` | UPDATE:opportunity | 60/min | opportunities.py |
| 6 | POST | `/opportunities/{id}/close-won` | UPDATE:opportunity | 60/min | opportunities.py |
| 7 | POST | `/opportunities/{id}/close-lost` | UPDATE:opportunity | 60/min | opportunities.py |
| 8 | GET | `/meetings/{id}` | READ:meeting | 60/min | meetings.py |
| 9 | POST | `/meetings/{id}/brief` | READ:meeting | 10/min | meetings.py |
| 10 | POST | `/meetings/{id}/summary` | CREATE:meeting | 10/min | meetings.py |
| 11 | GET | `/emails/{id}` | READ:email | 60/min | meetings.py |
| 12 | POST | `/emails/analyze` | CREATE:email | 20/min | meetings.py |
| 13 | GET | `/revenue/dashboard` | READ:revenue | 15/min | revenue.py |
| 14 | GET | `/opportunities/{id}/nba` | READ:nba | 30/min | nba_engine |
| 15 | POST | `/opportunities/{id}/nba/refresh` | CREATE:nba | 30/min | nba_engine |
| 16 | POST | `/opportunities/{id}/nba/feedback` | UPDATE:nba | 30/min | nba_engine |
| 17 | GET | `/pipeline/summary` | READ:pipeline | 20/min | pipeline_analytics |
| 18 | GET | `/pipeline/velocity` | READ:pipeline | 20/min | pipeline_analytics |
| 19 | GET | `/pipeline/conversion` | READ:pipeline | 20/min | pipeline_analytics |
| 20 | GET | `/pipeline/health` | READ:pipeline | 20/min | pipeline_analytics |
| 21 | GET | `/pipeline/forecast` | READ:pipeline | 20/min | pipeline_analytics |

**Total: 21 Wave 2 endpoints across 5 routers.**
