# Domain Model

> **نموذج المجالات — شرح كل Bounded Context مع الكيانات والعلاقات**

SalesOS is organized into 13 bounded contexts following Domain-Driven Design principles. This page describes each domain, its aggregates, and how they interact.

---

## Domain Classification

| Type | Domains | Strategy |
|------|---------|----------|
| **Core** | Company Intelligence, Entity Resolution, Knowledge Graph, AI Platform | Differentiator. Build in-house, invest heavily. |
| **Supporting** | CRM, Scoring, DNA, Activity Engine | Important but not unique. Standard patterns. |
| **Generic** | Identity, Workflow, Marketplace, Billing, Search | Commodity. Best practices, consider off-the-shelf. |

---

## BC-01: Identity & Access

**Purpose:** Multi-tenant authentication, authorization, and user management.

```
Tenant (1) ──has──> User (N)
  │                    │
  │                    ├── Role (1)
  │                    └── Permissions (N)
  │
  └── Plan (1)
```

| Aggregate | Key Fields | Events |
|-----------|-----------|--------|
| **Tenant** | id, name, slug, plan, features | `tenant.created`, `tenant.activated` |
| **User** | id, email, role, permissions | `user.registered`, `user.role_changed` |

**Roles:** `admin`, `manager`, `user`, `api`, `auditor`

**Endpoints:** See [SSO/OAuth API](../api/sso.md)

---

## BC-02: Company Intelligence [CORE]

**Purpose:** The golden record for every company — the competitive advantage of SalesOS.

```
Company (1) ──has──> Branch (N)
  │                   
  ├──has──> License (N)
  │
  ├──has──> Contact (N)
  │
  └──has──> Tag (N)
```

| Aggregate | Key Fields | Events |
|-----------|-----------|--------|
| **Company** | id, name_ar, name_en, cr_number, status, city, region | `company.created`, `company.updated`, `company.status_changed` |
| **License** | id, license_number, type, status, issue_date, expiry_date | `license.added`, `license.expired`, `license.renewed` |
| **Contact** | id, name, email, phone, position, is_primary | — |

**Value Objects:** `CrNumber`, `CompanyStatus`, `Address`, `Money`

**Unique constraint:** CR number must be unique within a tenant.

---

## BC-03: Entity Resolution

**Purpose:** Match, merge, and deduplicate company records from multiple sources.

```
GoldenRecord (1) ──resolves──> SourceRecord (N)
```

**Key feature:** Event sourcing for full audit trail of merge/split decisions.

---

## BC-04: CRM

**Purpose:** Pipeline management and opportunity lifecycle.

```
Pipeline (1) ──has──> Stage (N)
   │
   └──tracks──> Opportunity (N)
                    │
                    ├── Company (1)
                    ├── Owner (1)
                    └── Notes (N)
```

| Aggregate | Key Fields | Events |
|-----------|-----------|--------|
| **Pipeline** | id, stages, is_default | — |
| **Opportunity** | id, name, value, stage, probability, health | `opportunity.created`, `opportunity.stage_changed`, `opportunity.won` |

**Stages:** `qualification → discovery → proposal → negotiation → closed_won / closed_lost`

---

## BC-05: Activity Engine

**Purpose:** Record all interactions with companies and contacts.

| Type | Examples |
|------|----------|
| `EMAIL_SENT` | Outbound email logged |
| `MEETING_HELD` | Meeting completed |
| `CALL_MADE` | Phone call logged |
| `NOTE_ADDED` | Manual note |
| `STATUS_CHANGE` | Auto-generated from license changes |

---

## BC-06: Scoring Engine

**Purpose:** Compute normalized scores (0–1) for companies, opportunities, and relationships.

| Score Type | Factors |
|-----------|---------|
| Company | financial_health (0.3), growth_trend (0.2), digital_presence (0.15), hiring_trend (0.15), procurement_maturity (0.2) |
| Opportunity | stage_weight (0.3), estimated_value (0.15), buying_intent (0.25), relationship_strength (0.2), confidence (0.1) |
| Intent | signal_activity (0.3), hiring_trend (0.2), government_exposure (0.15), expansion_potential (0.2), digital_engagement (0.15) |
| Risk | risk_level_raw (0.3), financial_volatility (0.2), market_volatility (0.15), competitive_threat (0.15), regulatory_exposure (0.2) |

---

## BC-07: Company DNA

**Purpose:** Multi-dimensional company profile from 50+ signals.

**Data sources:** Firmographics, financial health, hiring signals, government contracts, news, social media, web presence.

---

## BC-08: Knowledge Graph

**Purpose:** Entity relationships stored in Neo4j.

```
(Company) ──[OWNS]──> (Company)
(Company) ──[EMPLOYS]──> (Contact)
(Company) ──[COMPETES_WITH]──> (Company)
(Company) ──[SUPPLIES]──> (Company)
(Company) ──[LOCATED_AT]──> (Address)
```

---

## BC-09: AI Platform [CORE]

**Purpose:** RAG pipeline, AI agents, and natural language querying.

| Component | Description |
|-----------|-------------|
| Document Ingestion | PDF, DOCX, HTML, email parsing |
| Chunking | Semantic, heading-based, sentence-based |
| Embedding | multilingual-e5-large (1024 dims) |
| Vector Store | pgvector with HNSW index |
| Hybrid Search | Semantic + BM25 with RRF fusion |
| Generation | GPT-4o-mini with citations |

See [RAG Pipeline API](../api/rag.md)

---

## BC-10: Workflow Engine

**Purpose:** Event-driven automation of sales processes.

| Trigger Type | Examples |
|-------------|----------|
| Event | `opportunity.stage_changed`, `deal_health.critical` |
| Schedule | Daily 9am, Weekly Monday |
| Manual | User clicks "Run Workflow" |

| Action Type | Description |
|-------------|-------------|
| `send_email` | Send via Email Intelligence |
| `update_crm` | Update opportunity stage/field |
| `create_task` | Create task for user |
| `trigger_nba` | Refresh NBA recommendation |
| `webhook` | Call external URL |

See [Workflow Engine API](../api/workflows.md)

---

## Event Catalog

Every domain event follows this structure:

```json
{
  "event_id": "uuid",
  "event_type": "company.company_created",
  "event_version": 1,
  "aggregate_id": "uuid",
  "aggregate_type": "Company",
  "tenant_id": "uuid",
  "occurred_at": "2026-07-11T10:00:00Z",
  "data": {},
  "metadata": {
    "correlation_id": "uuid",
    "causation_id": "uuid",
    "user_id": "uuid"
  }
}
```

Major events: `company.created`, `company.merged`, `opportunity.stage_changed`, `opportunity.won`, `workflow.completed`, `nba.generated`.

---

## Repository Pattern

Every domain service depends on a repository interface. Implementations live in the infrastructure layer only.

```python
class CompanyRepository(Repository[Company, CompanyId]):
    async def get(self, id: CompanyId) -> Company
    async def save(self, company: Company) -> None
    async def find_by_cr_number(self, tenant_id: TenantId, cr_number: CrNumber) -> Optional[Company]
    async def find_by_name(self, tenant_id: TenantId, name: str, limit: int) -> list[Company]
    async def find_expiring_licenses(self, tenant_id: TenantId, within_days: int) -> list[Company]
```

See the full [Domain Driven Design specification](../../docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md) for complete details.
