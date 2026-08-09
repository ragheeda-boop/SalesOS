# ADR-029: Canonical Opportunity Model

**Status:** Proposed  
**Date:** 2026-08-09  
**Deciders:** CTO, Chief Architect, Backend Team  
**Tags:** architecture, data-model, crm, opportunity, canonical-model, deprecation  
**Supersedes:** A.1 SoT (informal), A.2 dual-table (informal)  
**Precedes:** Phase C.1 (Opportunity ↔ Contact), Phase C.2 (Attribution Model)

## Context

SalesOS contains two independent opportunity tables with no synchronization:

| Table | Created | PK Type | Consumers | Status |
|-------|---------|---------|-----------|--------|
| `commercial_opportunities` | Migration 0007 (2026-07-02) | `String(36)` | 22+ production files, all frontend APIs | Active, canonical |
| `opportunities` | Migration 0046 (2026-07-27) | `UUID` | 5 production files, revenue execution only | Legacy, deprecated |

### Evidence from Phase C.0 Audit

**`commercial_opportunities` consumers:**
- Employee 360 (`employee_360/service.py:205-226`) — reads by `owner_id`
- Company 360 (`company/service.py:446-488`) — reads by `company_id`
- Commercial CRUD (`routers/commercial.py`) — full CRUD at `/api/v1/opportunities`
- GraphQL (`graphql/query.py`, `graphql/mutation.py`) — read + create
- Pipeline Analytics (`pipeline_analytics/`) — 8 raw SQL queries
- NBA Engine (`nba_engine/__init__.py`) — 2 raw SQL queries
- Dashboard Mappers (`dashboard/mappers/`) — 5 raw SQL queries
- Executive Service (`executive/service.py`) — 6 raw SQL queries
- Knowledge Graph (`knowledge_graph_runtime/router.py`) — 2 raw SQL queries
- MCP Server (`mcp_server/salesos_client.py`) — 2 raw SQL queries
- Meeting Intelligence (`meeting/intelligence.py`) — 2 raw SQL queries
- Revenue Dashboard (`routers/revenue.py`) — 2 raw SQL queries

**`opportunities` (revenue_execution) consumers:**
- Revenue Execution Service (`revenue_execution/service.py`) — CRUD
- Revenue Execution Router (`revenue_execution/router.py`) — `/api/v1/revenue-execution/opportunities`
- Entity Resolution (`entity_resolution/service.py:606-619`) — company merge only
- Intelligence Grounding (`intelligence/grounding.py:101-115`) — raw SQL (broken: references non-existent columns `amount`, `probability`)

**No synchronization exists:**
- No Celery task syncs between tables
- No migration transfers data
- No trigger maintains consistency
- No code reads from one and writes to the other

**ID incompatibility:**
- `commercial_opportunities.id` = `String(36)` — app-generated UUID string
- `opportunities.id` = `UUID(as_uuid=True)` — DB-generated native UUID
- No conversion code exists between formats

**Schema divergence:**

| Field | `commercial_opportunities` | `opportunities` |
|-------|---------------------------|-----------------|
| Name | `name` (String 500) | `title` (String 500) |
| Value | `value` (Float) | `estimated_value` (Numeric 15,2) |
| Probability | `probability` (Float) | `win_probability` (Numeric 3,2) |
| Owner | `owner_id` (String 36) | `assignee_id` (UUID) |
| Status | `status` (open/won/lost/abandoned) | — (not present) |
| Stage vocabulary | `prospecting`, `qualification`, `proposal`, `negotiation`, `closed_won`, `closed_lost` | `identified`, `qualifying`, `developing`, `proposing`, `negotiating`, `closing` |

**Known defect revealed by canonicalization audit:**
- `employee_360/service.py:222-223` — `company_name` always `None` because `OpportunityModel` has no `company_name` attribute

**Missing relationship:**
- No `opportunity_contacts` junction table exists
- No FK from contacts to opportunities
- No way to determine which contact belongs to which opportunity

## Decision

### 1. Canonical Opportunity

**`commercial_opportunities` is the single Source of Truth for Opportunity in SalesOS.**

All future code — Employee 360, Company 360, Attribution Engine, AI Coach, Scoring — must read from and write to `commercial_opportunities`. The `opportunities` table in `revenue_execution` is deprecated and must not receive new consumers.

**No New Consumers Rule:** No new production code may introduce a new dependency on the `opportunities` table unless explicitly approved by a subsequent ADR. Any PR that adds `from app.modules.revenue_execution.models import Opportunity` or queries `opportunities` must be rejected during code review unless covered by an approved ADR.

### 2. No Synchronization

We do not build a synchronization mechanism between the two tables. The tables serve different purposes, have incompatible schemas, and the legacy table is being deprecated. Synchronization would add complexity with no clear benefit.

### 3. Opportunity ↔ Contact Relationship

Create `opportunity_contacts` junction table to establish the missing many-to-many relationship between opportunities and contacts. This is a prerequisite for Sales Activity Attribution (Phase C).

### 4. ID Normalization

`commercial_opportunities.id` remains `String(36)` for this ADR's scope. ID migration to native UUID is a separate concern (see Migration Concerns below) and must not block canonicalization.

### 5. Stage Vocabulary

The two tables use different stage vocabularies. This is recorded as a migration concern. No stage mapping is created in this ADR. The revenue_execution module's stage vocabulary (`identified`, `qualifying`, etc.) is deprecated along with its table.

### 6. Deprecation

`opportunities` table enters deprecation. Removal occurs only after consumer migration and data-transition validation. No data is deleted in this ADR.

## Opportunity ↔ Contact Junction Table

### Schema

```sql
CREATE TABLE opportunity_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    opportunity_id VARCHAR(36) NOT NULL,  -- references commercial_opportunities.id
    contact_id UUID NOT NULL REFERENCES contacts(id),
    role VARCHAR(50),                     -- 'decision_maker', 'influencer', 'champion', 'observer'
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_id, opportunity_id, contact_id)
);

CREATE INDEX idx_oc_tenant ON opportunity_contacts(tenant_id);
CREATE INDEX idx_oc_opportunity ON opportunity_contacts(opportunity_id);
CREATE INDEX idx_oc_contact ON opportunity_contacts(contact_id);
CREATE INDEX idx_oc_tenant_opp ON opportunity_contacts(tenant_id, opportunity_id);
```

### Design Rationale

| Choice | Rationale |
|--------|-----------|
| `opportunity_id VARCHAR(36)` | Matches `commercial_opportunities.id` type. No FK constraint yet due to String→UUID type mismatch; FK addition is a separate migration after ID normalization. |
| `contact_id UUID REFERENCES contacts(id)` | Proper FK to canonical contacts table. |
| `role VARCHAR(50)` | Supports stakeholder classification without over-engineering. Extensible via CHECK constraint or lookup table if needed. |
| `is_primary BOOLEAN` | Allows marking one contact as the primary stakeholder per opportunity. Defaults to FALSE; application logic enforces at most one primary per opportunity. |
| `tenant_id UUID REFERENCES tenants(id)` | Required for RLS (Row-Level Security). All tenant tables in SalesOS carry this column. |
| `UNIQUE (tenant_id, opportunity_id, contact_id)` | Prevents duplicate associations within a tenant. |
| No `deleted_at` | Soft delete not needed at junction level; removal is simply DELETE. |

### ORM Model

```python
class OpportunityContact(Base):
    __tablename__ = "opportunity_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    opportunity_id = Column(String(36), nullable=False, index=True)  # FK deferred to ID normalization
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True)
    role = Column(String(50), nullable=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "opportunity_id", "contact_id", name="uq_oc_tenant_opp_contact"),
        Index("idx_oc_tenant_opp", "tenant_id", "opportunity_id"),
    )
```

## Deprecation Strategy

```
Stage 1: Canonicalize (this ADR)
    ├── commercial_opportunities = canonical
    ├── opportunities = deprecated
    └── No new consumers for opportunities

Stage 2: Opportunity ↔ Contact (Phase C.1)
    └── Create opportunity_contacts junction table

Stage 3: Migrate consumers (future ADR)
    ├── Move revenue_execution logic to commercial domain
    ├── Migrate entity_resolution to use commercial_opportunities
    └── Fix intelligence/grounding.py broken query

Stage 4: Migrate/verify data (future ADR)
    ├── Identify any data in opportunities not in commercial_opportunities
    ├── Migrate or archive as needed
    └── Validate no consumer reads from opportunities

Stage 5: Freeze legacy writes (future ADR)
    ├── Remove INSERT/UPDATE paths to opportunities
    └── Keep SELECT for read-only audit if needed

Stage 6: Observe (future ADR)
    ├── Monitor for any runtime errors referencing opportunities
    └── Confirm zero reads for 30 days

Stage 7: Remove legacy (future ADR)
    ├── DROP TABLE opportunities
    └── Remove ORM model and migration references
```

**This ADR covers Stage 1 only.** Stages 3-7 require separate ADRs after consumer migration analysis.

## Known Defects Revealed by Canonicalization Audit

### DEF-001: Employee 360 `company_name` Always None

**File:** `employee_360/service.py:222-223`

```python
company_name=getattr(o, "company_name", None)
or getattr(o, "account_name", None),
```

`OpportunityModel` has no `company_name` or `account_name` attribute. This field always resolves to `None` in `EmployeePortfolioItem`.

**Fix scope:** Separate from this ADR. Requires joining `commercial_opportunities.company_id` → `companies.name_en` in `_get_portfolio()`.

### DEF-002: Intelligence Grounding Broken Query

**File:** `intelligence/grounding.py:106-109`

```sql
SELECT id::text, title, stage, amount, probability, expected_close_date
FROM opportunities WHERE company_id::text = :cid
```

References columns `amount` and `probability` which do not exist on the `opportunities` table (actual columns: `estimated_value`, `win_probability`). This query fails at runtime.

**Fix scope:** Part of Stage 3 consumer migration. Must rewrite to use `commercial_opportunities` with correct column names.

### DEF-003: Entity Resolution Company Merge Skips commercial_opportunities

**File:** `entity_resolution/service.py:606-619`

Company merge updates `opportunities.company_id` but does not update `commercial_opportunities.company_id`. After a merge, `commercial_opportunities` retains stale `company_id` references.

**Fix scope:** Part of Stage 3 consumer migration. Must add `commercial_opportunities` to merge logic.

## Migration Concerns

| Concern | Scope | Blocks This ADR? |
|---------|-------|:-----------------:|
| `commercial_opportunities.id` is String(36), not UUID | ID normalization | No — deferred to separate ADR |
| No FK from `commercial_opportunities.company_id` to `companies.id` | FK addition | No — deferred to separate ADR |
| No FK from `commercial_opportunities.tenant_id` to `tenants.id` | FK addition | No — deferred to separate ADR |
| No FK from `commercial_opportunities.owner_id` to `users.id` | FK addition | No — deferred to separate ADR |
| Stage vocabulary mismatch between tables | Stage mapping | No — legacy table deprecated |
| `opportunities` table has data | Data migration | No — legacy table preserved until Stage 4 |
| RLS policies for `opportunity_contacts` | Security | Must be added in Phase C.1 migration |

## Consequences

### Positive
1. **Single Source of Truth** — eliminates ambiguity about which opportunity table to use
2. **Attribution-ready** — `opportunity_contacts` junction enables Contact→Opportunity linking required for Phase C
3. **No sync complexity** — avoiding synchronization between incompatible schemas reduces operational risk
4. **Clear deprecation path** — 7-stage strategy with separate ADRs for each decision gate
5. **Defect visibility** — 3 known defects documented and scoped for resolution

### Negative
1. **Dual tables persist** — `opportunities` table remains in the database until Stage 7
2. **ID type inconsistency** — String(36) vs UUID remains until separate ID normalization ADR
3. **FK constraints deferred** — `commercial_opportunities` remains referentially orphaned until separate FK migration
4. **Revenue Execution module** — must be migrated to use `commercial_opportunities` in Stage 3 (future ADR)

### Risks
- **Data drift** — if any code path writes to `opportunities` after deprecation, data will diverge. Mitigated by: no Celery tasks touch the table, and the only write path is `RevenueService` which is explicitly deprecated.
- **Broken grounding query** — `intelligence/grounding.py` will fail at runtime. Mitigated by: low-traffic path, and fix is scoped to Stage 3.

## Compliance

- [x] Uses repository pattern — `PostgresOpportunityRepository` interface in domain, PostgreSQL implementation in infrastructure
- [x] Tenant isolation — all queries scoped by `tenant_id`
- [x] RLS — `commercial_opportunities` registered in `ALL_TENANT_TABLES` (`alembic/lib/rls.py:30`)
- [x] Audit logging — opportunity CRUD logged via `audit_logs` table
- [x] Deprecation clearly documented — this ADR + code comments
- [x] No secrets or credentials exposed
- [x] ADR precedes implementation — no code changes in this ADR

## References

- Phase C.0 Audit Report (2026-08-09) — canonical opportunity discovery
- A.1 SoT (informal) — `boot/routers.py:112-115`
- A.2 dual-table (informal) — `revenue_execution/models.py:43-45`
- `commercial_opportunities` model — `domains/commercial/infrastructure/models.py:22-46`
- `opportunities` model — `app/modules/revenue_execution/models.py:9-35`
- `contacts` model — `app/modules/contact/models.py:14-57`
- Phase C Prompt (2026-08-09) — Sales Activity Attribution audit scope
