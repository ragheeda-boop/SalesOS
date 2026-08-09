# ADR-C1: Canonical Opportunity ↔ Contact Relationship

**Status:** Ready for Ratification  
**Date:** 2026-08-09  
**Deciders:** CTO, Chief Architect, Backend Team  
**Tags:** architecture, data-model, crm, opportunity, contact, junction, relationship  
**Depends On:** ADR-029 (Canonical Opportunity Model)  
**Precedes:** Phase C.2 (Sales Activity Attribution)  
**Scope:** Junction table only — no Odoo sync, no attribution, no legacy migration  
**Governance:** Odoo source cardinality ≠ SalesOS canonical cardinality. `partner_id` (1:1) in Odoo does not constrain SalesOS to 1:1. The M:N junction is a SalesOS architectural decision independent of Odoo's single-contact model.

## C.1 Live Verification (Odoo 17 Online — 2026-08-09)

Verified against live Odoo instance `odoo-ps-psae-ratl-main-14005796` (Muhide CX Team). All C.1 code-audit findings confirmed.

### Verified Facts

| # | Finding | Expected | Actual | Match |
|---|---------|:--------:|:------:|:-----:|
| 1 | `partner_id` exists on `crm.lead` | YES | YES (`many2one → res.partner`, string="Customer") | ✓ |
| 2 | `partner_id` is many2one (single contact) | YES | YES | ✓ |
| 3 | `partner_id` → `res.partner` | YES | YES | ✓ |
| 4 | No M2M contact fields on `crm.lead` | YES | YES (`message_partner_ids` is followers, not contacts) | ✓ |
| 5 | `partner_id` is NOT required | YES | YES (`required=False`) | ✓ |
| 6 | Opportunities can exist without `partner_id` | YES | YES: 27,014/27,266 leads (99.1%) have no `partner_id` | ✓ |
| 7 | No `external_id`/normalized identifier on `crm.lead` | YES | YES — only integer `id` | ✓ |
| 8 | `write_date` available for incremental sync | YES | YES | ✓ |

### New Discoveries (Not in C.1 Code Audit)

| # | Finding | Impact on ADR-030 |
|---|---------|-------------------|
| A | `res.partner.opportunity_ids` (one2many → `crm.lead`) exists | **No impact.** This is Odoo ORM's automatic computed inverse of `partner_id`, not a separate physical column. It does not constitute a persistent Contact→Opportunity back-reference for SalesOS purposes. |
| B | `x_studio_customer` (many2one → `res.partner`) — custom Studio field | **No impact.** A duplicate contact field created via Odoo Studio. `partner_id` remains the canonical relationship. |
| C | `res.partner.function` (char, "Job Position") and `res.partner.title` (many2one → `res.partner.title`) exist | **No impact on junction table.** Both fields were empty in sampled data. Future potential: populate `role` from `function` during Odoo sync. |
| D | `res.partner.child_ids` (one2many → `res.partner`, string="Contact") | **No impact.** Odoo's company→individual hierarchy. SalesOS may use this during contact ingestion but it does not affect the junction table design. |
| E | 6 stages: To Do → in progress → Prospect → Won-Registered → Active → Not interested | **No impact.** Stage vocabulary differs from both `commercial_opportunities` and legacy `opportunities`. Stage mapping remains an Odoo Integration concern. |

### C.1 Live Verification Conclusion

**All architectural findings from C.1 code audit are confirmed by live Odoo data.** No amendments required to ADR-030 schema, cardinality, or integrity decisions. The `opportunity_ids` ORM backref and `x_studio_customer` custom field are noted as Odoo implementation details with zero impact on SalesOS canonical model.

## Context

ADR-029 established `commercial_opportunities` as the canonical Opportunity model and proposed `opportunity_contacts` as a future junction table. The C.1 forensic audit investigated whether this relationship already exists at any level.

### Evidence from C.1 Audit

**The Opportunity↔Contact relationship does not exist at any level in SalesOS:**

| Layer | Status | Evidence |
|-------|--------|----------|
| Junction table | **ABSENT** | No `opportunity_contacts` in any migration, ORM model, or SQL |
| FK column | **ABSENT** | No `contact_id` on `commercial_opportunities` |
| JSONB array | **DEAD** | `related_contact_ids` exists on `employee_email_events` and `employee_calendar_events` but is always `[]` — never populated by any sync code |
| activity_records | **NO FK** | `entity_id` and `target_id` are bare strings with no referential integrity |
| Odoo sync | **IN-MEMORY ONLY** | `partner_sync.py` and `opportunity_sync.py` return batch results but write nothing to any database table |
| Odoo ID persistence | **ABSENT** | No `odoo_id`, `external_id`, or `source_id` column on `contacts` or `commercial_opportunities` |
| Employee 360 | **NO JOINS** | `_get_portfolio()` queries opportunities, contacts, and companies as independent parallel queries with zero cross-references |

**The C.1 audit also established:**

1. **No Odoo ID is persisted anywhere** — cannot map SalesOS records back to Odoo `res.partner` or `crm.lead`
2. **Odoo `crm.lead` has single `partner_id`** — one contact per opportunity in the pulled fields; no M2M relationship is extracted
3. **No role semantics available from Odoo** — `partner_id` is a many2one reference with no role classification
4. **Contact dedup is email-only and application-level** — no DB-level unique constraint on `(tenant_id, email)`
5. **The `contacts` table has no external identity mechanism** — no `odoo_id`, no `source_id`, no reverse-lookup from Odoo

## Decision

### 1. Create `opportunity_contacts` Junction Table

Establish the missing many-to-many relationship between opportunities and contacts. This is a **canonical SalesOS relationship**, not an Odoo-synchronized relationship.

### 2. No Odoo Identity in This ADR

The junction table does not include `odoo_id`, `source_id`, `source_system`, or any Odoo-specific field. Odoo ID persistence is a separate concern (see Deferred Decisions).

### 3. No Attribution in This ADR

The junction table does not include confidence, attribution metadata, algorithm version, or activity linkage. Attribution is Phase C.2 scope.

### 4. No Automatic Synchronization

No Celery task, trigger, or background job populates the junction table from Odoo data. Population is via manual CRUD or future Odoo integration implementation.

### 5. No Legacy Migration

No data is migrated from existing tables. The junction table starts empty.

## Minimum Contract

### Schema

```sql
CREATE TABLE opportunity_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    opportunity_id VARCHAR(36) NOT NULL,
    contact_id UUID NOT NULL REFERENCES contacts(id),
    role VARCHAR(50),
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

### Field Classification

| Field | Type | Classification | Rationale |
|-------|------|:--------------:|-----------|
| `id` | UUID PK | **REQUIRED** | Every SalesOS table has UUID PK (pattern from C.1 evidence) |
| `tenant_id` | UUID FK→tenants | **REQUIRED** | All tenant tables carry this; RLS depends on it (C.1 evidence: `alembic/lib/rls.py`) |
| `opportunity_id` | VARCHAR(36) | **REQUIRED** | References `commercial_opportunities.id` (ADR-029 Decision #1). FK constraint deferred to ID normalization ADR. |
| `contact_id` | UUID FK→contacts | **REQUIRED** | References `contacts.id` (C.1 evidence: `contact/models.py:14`) |
| `role` | VARCHAR(50) nullable | **OPTIONAL** | C.1 audit found no role semantics in Odoo source data (`partner_id` is single reference). Included for future extensibility. |
| `is_primary` | BOOLEAN default FALSE | **RECOMMENDED** | Useful for Employee 360 display (C.1 evidence: `_get_portfolio()` shows flat lists). No Odoo evidence but practical need. |
| `created_at` | TIMESTAMPTZ | **REQUIRED** | All SalesOS tables have timestamps (pattern from C.1 evidence) |
| `updated_at` | TIMESTAMPTZ | **REQUIRED** | All SalesOS tables have timestamps (pattern from C.1 evidence) |
| `UNIQUE (tenant_id, opportunity_id, contact_id)` | constraint | **REQUIRED** | C.1 evidence: `contacts` has no unique constraints; duplicate prevention must be at DB level |

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

### Not Included (Not Justified by C.1 Evidence)

| Field | Reason Not Included |
|-------|-------------------|
| `odoo_id` | No Odoo ID persistence exists on any SalesOS model (C.1 evidence: Section 6) |
| `source_system` | No provenance mechanism on contacts (C.1 evidence: `source` column is unvalidated free-text) |
| `source_id` | No external identity mechanism exists (C.1 evidence: Section 2) |
| `confidence` | No confidence model for relationship quality (C.1 evidence: `confidence_score` on contacts is always 0.0) |
| `valid_from` / `valid_to` | No temporal relationship data in Odoo source (C.1 evidence: Section 5) |
| `deleted_at` | Soft delete not needed at junction level; removal is DELETE |
| `algorithm_version` | Attribution is C.2 scope (C.1 evidence: Section 13) |

## Cardinality

### Verified from C.1 Evidence

| Question | Answer | Evidence |
|----------|--------|----------|
| Can one Opportunity have multiple Contacts? | **YES** — junction table supports N:M | Odoo `crm.lead` has `partner_id` (single) but also supports `message_follower_ids` (M2M); SalesOS should support the general case |
| Can one Contact participate in multiple Opportunities? | **YES** — no uniqueness constraint prevents this | No existing junction table; `contacts` has no `opportunity_id` column |
| Can an Opportunity exist without a Contact? | **YES** — `contact_id` is NOT NULL but row may not exist | Odoo `partner_id` can be `False` (C.1 evidence: `opportunity_sync.py:89-97`) |
| Can a Contact exist without an Opportunity? | **YES** — `contacts` has no `opportunity_id` column | C.1 evidence: `contact/models.py` — no opportunity reference |
| Can same Contact belong to multiple Opportunities for same Company? | **YES** — UNIQUE constraint is `(tenant_id, opportunity_id, contact_id)`, not `(tenant_id, contact_id)` | Design choice: one contact can be on many deals |

### Cardinality Diagram

```
commercial_opportunities          contacts
        │                            │
        │ 0..N                       │ 0..N
        ▼                            ▼
   opportunity_contacts
   (junction table)
        │
        │ UNIQUE (tenant_id, opportunity_id, contact_id)
```

**Many-to-Many:** One opportunity can have many contacts; one contact can be on many opportunities.

## Integrity

### Foreign Keys

| Column | FK Target | Status |
|--------|-----------|--------|
| `tenant_id` | `tenants.id` | **ENFORCED** — standard RLS pattern |
| `contact_id` | `contacts.id` | **ENFORDED** — proper FK to canonical contacts |
| `opportunity_id` | `commercial_opportunities.id` | **DEFERRED** — String(36) vs UUID type mismatch; FK addition requires ID normalization ADR |

### Uniqueness

| Constraint | Columns | Purpose |
|-----------|---------|---------|
| `UNIQUE (tenant_id, opportunity_id, contact_id)` | 3 columns | Prevents duplicate associations within a tenant |
| PK `id` | UUID | Global uniqueness |

### Tenant Isolation

`tenant_id` is required and indexed. RLS policies will be added via `alembic/lib/rls.py` following the pattern used for all tenant tables (C.1 evidence: `rls.py:30` lists `ALL_TENANT_TABLES`).

### Deduplication

The UNIQUE constraint prevents duplicate `(tenant_id, opportunity_id, contact_id)` tuples at the DB level. Application-level upsert should use `ON CONFLICT (tenant_id, opportunity_id, contact_id) DO UPDATE` pattern (following the pattern in `feature_store/__init__.py:307`).

## Source-of-Truth

### This ADR Establishes

```
opportunity_contacts
    │
    │ canonical SalesOS relationship
    │
    ├── opportunity_id → commercial_opportunities.id (SalesOS canonical)
    └── contact_id → contacts.id (SalesOS canonical)
```

### This ADR Does NOT Establish

| Concern | Status | Deferred To |
|---------|--------|------------|
| Odoo → SalesOS relationship sync | Not implemented | Odoo Integration ADR |
| Odoo ID persistence | Not implemented | Odoo Identity ADR |
| Activity → Opportunity attribution | Not implemented | Phase C.2 |
| Email → Contact resolution | Not implemented | Phase C.2 |
| Calendar → Contact resolution | Not implemented | Phase C.2 |

### Population Sources (Future)

| Source | Mechanism | Status |
|--------|-----------|--------|
| Manual CRUD | REST API `/opportunity-contacts` | **TO BE IMPLEMENTED** |
| Odoo sync | Celery task via `opportunity_sync.py` | **NOT IMPLEMENTED** — sync is in-memory-only |
| Email/calendar inference | Attribution engine | **NOT IMPLEMENTED** — Phase C.2 |
| Entity resolution | Company merge | **NOT IMPLEMENTED** — DEF-003 |

## Consequences

### Positive

1. **Missing relationship created** — Opportunity↔Contact now exists at DB level
2. **Attribution-ready** — C.2 can use junction to resolve which contacts belong to which opportunities
3. **Employee 360 enrichable** — `_get_portfolio()` can join through junction to show contacts per opportunity
4. **DB-level integrity** — UNIQUE constraint prevents duplicate associations
5. **Tenant-isolated** — RLS-compatible from creation
6. **N:M cardinality** — supports the general case (one contact on many deals, one deal with many contacts)

### Negative

1. **Manual population only** — no automated sync from Odoo or any other source
2. **Empty table initially** — requires CRUD API + UI before useful
3. **No Odoo identity** — cannot auto-populate from Odoo until identity persistence is implemented
4. **FK deferred** — `opportunity_id` has no FK constraint until ID normalization

### Risks

| Risk | Mitigation |
|------|-----------|
| Table stays empty if no CRUD API is built | ADR-C1 scope includes CRUD API recommendation; implementation is separate |
| `role` field stays empty forever | Role is optional; can be populated manually or via future AI classification |
| Odoo sync implemented later may conflict with manual entries | UNIQUE constraint prevents duplicates; upsert pattern handles coexistence |

## Deferred Decisions

The following decisions are explicitly OUT OF SCOPE for ADR-C1 and require separate ADRs:

| Decision | Deferred To | Blocked By |
|----------|------------|-----------|
| Odoo ID persistence (`odoo_id` column) | Odoo Identity ADR | Odoo sync write path implementation |
| Odoo → SalesOS relationship sync | Odoo Integration ADR | Odoo ID persistence |
| `role` enum or free-text | Future ADR if needed | Usage data from manual CRUD |
| Activity → Opportunity attribution | Phase C.2 ADR | ADR-C1 ratification |
| Email → Contact resolution | Phase C.2 ADR | `related_contact_ids` population |
| Calendar → Contact resolution | Phase C.2 ADR | `related_contact_ids` population |
| Automatic deletion from Odoo | Product decision | Odoo sync write path |
| Historical relationship tracking | Future ADR if needed | Temporal data availability |

## Relationship to ADR-029

| Aspect | ADR-029 | ADR-C1 |
|--------|---------|--------|
| Scope | Canonical Opportunity Model | Opportunity ↔ Contact Relationship |
| `opportunity_contacts` | Proposed in Section "Opportunity ↔ Contact Junction Table" | **RATIFIED** with exact schema |
| `opportunities` deprecation | 7-stage strategy | No impact — junction uses `commercial_opportunities` only |
| No New Consumers Rule | Applies to `opportunities` table | Applies to `opportunity_contacts` — no Odoo-specific columns |
| Known Defects | DEF-001, DEF-002, DEF-003 documented | No new defects; DEF-003 remains open |

**ADR-C1 implements Stage 2 of ADR-029's deprecation strategy.**

## Migration / Implementation Boundary

### This ADR Covers

1. `opportunity_contacts` table schema (DDL + ORM)
2. UNIQUE constraint definition
3. Index definitions
4. Field classification (REQUIRED / RECOMMENDED / OPTIONAL)
5. Cardinality specification
6. Integrity rules

### This ADR Does NOT Cover (Implementation Boundary)

| Item | Boundary |
|------|----------|
| Alembic migration file | **IMPLEMENTATION** — write after ADR ratification |
| RLS policy addition | **IMPLEMENTATION** — add to `ALL_TENANT_TABLES` in `alembic/lib/rls.py` |
| CRUD API router | **IMPLEMENTATION** — new router for opportunity_contacts |
| Employee 360 enrichment | **IMPLEMENTATION** — join in `_get_portfolio()` |
| Frontend components | **IMPLEMENTATION** — contact association UI |
| Tests | **IMPLEMENTATION** — unit + integration tests |
| OpenAPI schema updates | **IMPLEMENTATION** — schema registration |

### Implementation Sequence (Post-Ratification)

```
1. Alembic migration: CREATE TABLE opportunity_contacts
2. Add to ALL_TENANT_TABLES in alembic/lib/rls.py
3. Create ORM model in domains/commercial/infrastructure/models.py
4. Create repository in domains/commercial/infrastructure/postgres_repositories.py
5. Create service in domains/commercial/opportunity/engine/service.py
6. Create router in app/routers/opportunity_contacts.py
7. Register router in app/boot/routers.py
8. Enrich Employee360Service._get_portfolio() with junction join
9. Add unit tests
10. Add integration tests
```

## References

- ADR-029: Canonical Opportunity Model (2026-08-09)
- C.1 Forensic Audit Report (2026-08-09) — all evidence sections
- `commercial_opportunities` model — `domains/commercial/infrastructure/models.py:22-46`
- `contacts` model — `app/modules/contact/models.py:11-57`
- `employee_email_events` JSONB fields — `domains/employee/intelligence_models.py:92-94`
- `activity_records` schema — `runtime/activity_runtime/__init__.py:46-69`
- Odoo adapter field constants — `integration_hub/odoo_adapter.py:154-231`
- Partner sync (in-memory) — `integration_hub/partner_sync.py:45-107`
- Opportunity sync (in-memory) — `integration_hub/opportunity_sync.py:100-193`
- Contact sync (Google only) — `communication_hub/contact_sync.py:48-147`
- Employee 360 service — `employee_360/service.py:198-290`
