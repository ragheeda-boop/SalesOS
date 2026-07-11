# NBA API Mapping

> **الهدف:** تصميم REST APIs لمحرك NBA
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 6 — API Mapping

---

## REST Endpoints

### Base Path: `/api/v1/revenue`

### NBA Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/opportunities/{id}/nba` | Get current NBA for opportunity | `nba:read` |
| `POST` | `/opportunities/{id}/nba/refresh` | Force recompute NBA | `nba:update` |
| `POST` | `/opportunities/{id}/nba/accept` | Accept NBA recommendation | `nba:update` |
| `POST` | `/opportunities/{id}/nba/dismiss` | Dismiss NBA recommendation | `nba:update` |
| `GET` | `/opportunities/{id}/nba/history` | Get NBA history for opportunity | `nba:read` |
| `GET` | `/nba/stats` | Get NBA engine statistics | `nba:admin` |
| `POST` | `/nba/bulk-refresh` | Force recompute NBA for all open opportunities | `nba:admin` |

### Opportunity Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/opportunities` | List opportunities (filterable) | `opportunity:read` |
| `GET` | `/opportunities/{id}` | Get opportunity detail | `opportunity:read` |
| `POST` | `/opportunities` | Create opportunity | `opportunity:create` |
| `PUT` | `/opportunities/{id}` | Update opportunity | `opportunity:update` |
| `PATCH` | `/opportunities/{id}/stage` | Advance/revert stage | `opportunity:update` |
| `DELETE` | `/opportunities/{id}` | Delete opportunity | `opportunity:delete` |

### Pipeline Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/pipeline` | Get pipeline summary | `pipeline:read` |
| `GET` | `/pipeline/stages` | Get stage metrics | `pipeline:read` |
| `GET` | `/pipeline/health` | Get pipeline health map | `pipeline:read` |
| `GET` | `/pipeline/velocity` | Get pipeline velocity | `pipeline:read` |

---

## DTOs

### NBA Response

```python
class NBAEvidenceDTO(BaseModel):
    id: str
    type: str  # business_rule | signal | ai_analysis | company_score | activity | risk_factor
    description: str
    source: str
    confidence: float
    timestamp: datetime
    data: dict | None = None

class NBAAlternativeDTO(BaseModel):
    action: str
    reason: str
    confidence: float
    expected_impact: ImpactDTO | None = None

class ImpactDTO(BaseModel):
    description: str
    estimated_revenue: float | None = None
    estimated_probability: float | None = None
    category: str  # revenue | relationship | risk_mitigation | information_gathering

class RiskDTO(BaseModel):
    type: str
    level: str  # low | medium | high
    description: str
    detected_at: datetime

class NBAResponse(BaseModel):
    id: str
    opportunity_id: str
    action: str
    reason: str
    evidence: list[NBAEvidenceDTO]
    confidence: float
    confidence_label: str  # high | medium | low
    source: str  # rule | ai | hybrid
    alternatives: list[NBAAlternativeDTO]
    expected_impact: ImpactDTO
    potential_risks: list[RiskDTO]
    due_by: str | None = None
    status: str  # pending | accepted | dismissed | completed
    created_at: datetime
    updated_at: datetime
```

### NBA Feedback Request

```python
class NBAFeedbackRequest(BaseModel):
    nba_id: str
    action: Literal["accepted", "dismissed"]
    reason: str | None = None
```

### Opportunity DTO

```python
class OpportunityCreateRequest(BaseModel):
    company_id: str
    name: str
    value: float = 0.0
    currency: str = "SAR"
    expected_close_date: date | None = None
    playbook_id: str | None = None

class OpportunityUpdateRequest(BaseModel):
    name: str | None = None
    value: float | None = None
    expected_close_date: date | None = None
    playbook_id: str | None = None

class OpportunityStageChangeRequest(BaseModel):
    stage: OpportunityStage
    reason: str | None = None

class OpportunityResponse(BaseModel):
    id: str
    company_id: str
    name: str
    stage: OpportunityStage
    value: float
    currency: str
    probability: float
    health: str
    expected_close_date: date | None = None
    owner_id: str
    playbook_id: str | None = None
    nba: NBAResponse | None = None
    created_at: datetime
    updated_at: datetime
```

### Pipeline DTOs

```python
class PipelineSummaryResponse(BaseModel):
    total_value: float
    weighted_value: float
    total_count: int
    by_stage: dict[str, StageMetrics]
    win_rate: float
    avg_deal_size: float
    velocity_days: float

class StageMetrics(BaseModel):
    count: int
    value: float
    conversion_rate: float

class HealthMapResponse(BaseModel):
    healthy: int
    at_risk: int
    critical: int
    opportunities: list[HealthMapItem]

class HealthMapItem(BaseModel):
    opportunity_id: str
    name: str
    health: str
    owner: str
    value: float
    stage: str
```

---

## Application Layer

### Query Handlers

```python
class GetNBAQuery:
    async def handle(self, opportunity_id: str, tenant_id: str) -> NBAResponse:
        engine = NBAEngine(...)
        nba = await engine.get_or_compute(opportunity_id, tenant_id)
        return self._to_dto(nba)

class ListOpportunitiesQuery:
    async def handle(self, filters: OpportunityFilters, tenant_id: str) -> list[OpportunityResponse]:
        repo = OpportunityRepository(...)
        opportunities = await repo.find_all(tenant_id, filters)
        return [self._to_dto(o) for o in opportunities]
```

### Command Handlers

```python
class RefreshNBACommand:
    async def handle(self, opportunity_id: str, tenant_id: str) -> NBAResponse:
        engine = NBAEngine(...)
        nba = await engine.recompute(opportunity_id, tenant_id)
        return self._to_dto(nba)

class AcceptNBACommand:
    async def handle(self, opportunity_id: str, nba_id: str, user_id: str, tenant_id: str):
        engine = NBAEngine(...)
        await engine.record_feedback(opportunity_id, nba_id, user_id, "accepted")
```

---

## Caching

| Endpoint | Cache | TTL | Invalidation |
|----------|-------|-----|-------------|
| `GET /opportunities/{id}/nba` | Per-opportunity NBA result | Until next trigger | On stage change, activity, signal |
| `GET /opportunities/{id}` | Opportunity detail | 5 minutes | On opportunity update |
| `GET /pipeline` | Pipeline summary | 5 minutes | On any opportunity change |
| `GET /pipeline/health` | Health map | 5 minutes | On health change event |

---

## Versioning

All NBA endpoints are at `/api/v1/revenue/...`. When the NBA engine evolves:

- **Backward-compatible changes** (new evidence types, new action types) — no version bump
- **Breaking changes** (confidence model changes, output format changes) — new `/api/v2/revenue/...`
- Deprecated endpoints maintained for 2 sprints with deprecation header

---

*NBA API Mapping complete. Ready for Phase 7: NBA Component Catalog.*
