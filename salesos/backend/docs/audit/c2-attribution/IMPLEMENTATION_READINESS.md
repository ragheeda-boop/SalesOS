# ADR-030 Implementation Readiness Check

**Status:** ALL GATES PASS  
**Date:** 2026-08-09  
**Precedes:** ADR-030 Implementation (Alembic migration → ORM → Repository → Service → RLS → Router → Tests)

---

## Gate Results Summary

| # | Gate | Verdict | Key Finding |
|---|------|:-------:|-------------|
| 1 | Canonical Opportunity | **PASS** | `commercial_opportunities` (String(36) PK) is sole target. Router `commercial.py` uses it exclusively. One legit FK exists: `StageEntryModel → commercial_opportunities.id`. |
| 2 | Legacy Isolation | **PASS** | `opportunities` (UUID PK) is fully isolated. 5 production imports only. Commercial domain has zero references. "No New Consumers" rule verified. |
| 3 | Contact Model | **PASS** | `contacts` (UUID PK) is canonical with `company_id` FK. `contact_sync.py` writes directly. Commercial domain references via raw SQL reads only. |
| 4 | Junction Contract | **PASS** | `Index(unique=True)` on `(tenant_id, col_a, col_b)` pattern exists in `company_features` (`feature_store/__init__.py:25-31`). Commercial domain uses `Index` not `UniqueConstraint`. |
| 5 | ID Compatibility | **PASS** | String(36) ↔ UUID mismatch is intentional. No cross-type FK exists anywhere in codebase. Soft references only — consistent with `tasks.opportunity_id`, `quotes.opportunity_id`, etc. |
| 6 | Tenant Isolation | **PASS** | 47 tables in `ALL_TENANT_TABLES`. `generate_policy_sql()` is type-agnostic (`::text` cast). Most recent migration uses inline RLS pattern. Zero infrastructure changes needed. |
| 7 | Odoo Provenance | **PASS** | Zero `odoo_id` columns in any model. Both sync modules (`partner_sync.py`, `opportunity_sync.py`) are in-memory only. ADR-030 exclusion of Odoo ID is consistent with code reality. |
| 8 | Cardinality | **PASS** | M:N junction is intentional divergence from Odoo 1:1. ADR-030 Governance header explicitly documents: "Odoo source cardinality ≠ SalesOS canonical cardinality." |
| 9 | Delete/Update Semantics | **PASS** | CASCADE: `tenant_id`, `contact_id`. DEFERRED FK: `opportunity_id`. No CASCADE in commercial domain currently — junction table is new category. `merge_companies()` must add `opportunity_contacts` handling. |
| 10 | Repository Contract | **PASS** | 12 `PostgresXxxRepository` classes: `__init__(self, session: AsyncSession)`. ABC contracts under `domains/*/contracts/`. DI: `FactoryBoundRepository` + `Depends(get_db)`. No M2M repo exists yet — first of its kind. |
| 11 | Tests | **PASS** | Pattern: `TestPostgresXxxRepository`, mock `AsyncSession` + `MockResult` helpers. Root conftest: real `salesos_test` Postgres DB. Unit conftest: no-op override. Shared `tests/support/tenant_isolation.py` for cross-tenant assertions. |
| 12 | Migration Safety | **PASS** | Each migration in `context.begin_transaction()` (all-or-nothing). Idempotent `_table_exists`/`_index_exists` guards. Downgrade: drop RLS before tables, reverse order. `opportunity_id` index created but FK intentionally deferred per DEC-121. |

---

## Design Decisions Confirmed by Readiness Check

### 1. Junction Unique Constraint Pattern

Use `Index(unique=True)` to match commercial domain convention (no `UniqueConstraint` in any commercial model):

```python
__table_args__ = (
    Index("ix_opportunity_contacts_lookup", "tenant_id", "opportunity_id", "contact_id", unique=True),
    Index("ix_oc_tenant_opp", "tenant_id", "opportunity_id"),
    Index("ix_oc_contact", "contact_id"),
    Index("ix_oc_tenant", "tenant_id"),
)
```

**Evidence:** `company_features` at `runtime/feature_store/__init__.py:25-31` uses identical 3-column tenant-scoped unique index pattern.

### 2. FK Strategy

| Column | FK Target | ON DELETE | Type Match | Status |
|--------|-----------|:---------:|:----------:|:------:|
| `tenant_id` | `tenants.id` (UUID) | CASCADE | UUID ↔ UUID | **Enforced** — matches 5+ existing patterns |
| `contact_id` | `contacts.id` (UUID) | CASCADE | UUID ↔ UUID | **Enforced** — junction rows without parent are meaningless |
| `opportunity_id` | `commercial_opportunities.id` (String(36)) | CASCADE | String(36) ↔ String(36) | **Deferred FK** — pending ID normalization; soft reference only |

**Evidence:** `contact/models.py:23` uses `ondelete="CASCADE"` for `tenant_id`. Commercial domain has zero CASCADE or FK ondelete anywhere — junction table is a new category where CASCADE is correct.

### 3. Application-Level Cleanup

Since `opportunity_id` FK is deferred, `PostgresOpportunityRepository.delete()` must manually clean junction rows:

```python
await session.execute(
    delete(OpportunityContactModel).where(
        OpportunityContactModel.opportunity_id == opportunity_id
    )
)
```

**Evidence:** `postgres_repositories.py:119-125` currently deletes `commercial_opportunities` with no junction awareness.

### 4. Entity Resolution Integration

`EntityResolutionService.merge_companies()` must handle `opportunity_contacts` reassignment alongside existing Contact/Branch/License/Opportunity handling.

**Evidence:** `entity_resolution/service.py:572-639` currently handles contacts (596-598) and legacy opportunities (606-619) but not opportunity_contacts (table doesn't exist yet). DEF-003.

### 5. RLS Strategy

Add `"opportunity_contacts"` to `ALL_TENANT_TABLES` in `alembic/lib/rls.py:20-82` (Path A, batch) OR apply inline `generate_policy_sql("opportunity_contacts")` in the migration (Path B, inline — preferred per recent pattern).

**Evidence:** Most recent migration `f7a1b82c3d09` uses inline `_apply_rls(table)` pattern.

### 6. Test Strategy

| Layer | File | Pattern |
|-------|------|---------|
| Unit (mock) | `tests/unit/test_opportunity_contact_repos.py` | `TestPostgresOpportunityContactRepository` with mock `AsyncSession` + `MockResult` helpers |
| Tenant isolation | Same file or separate | `assert_cross_tenant_read_blocked` + `assert_cross_tenant_listing_excludes` from `tests/support/tenant_isolation.py` |
| Integration | `tests/e2e/test_opportunity_contacts.py` | Real DB, CRUD + uniqueness violation + cross-tenant |

**Evidence:** `test_meeting_email_repos.py` for mock pattern. `tenant_isolation.py` for cross-tenant helpers.

### 7. Migration Strategy

```python
# upgrade()
def upgrade():
    conn = op.get_bind()
    if not _table_exists(conn, "opportunity_contacts"):
        op.create_table("opportunity_contacts",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("opportunity_id", sa.String(36), nullable=False),
            sa.Column("contact_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("role", sa.String(50), nullable=True),
            sa.Column("is_primary", sa.Boolean, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if not _index_exists(conn, "opportunity_contacts", "ix_opportunity_contacts_lookup"):
        op.create_index("ix_opportunity_contacts_lookup", "opportunity_contacts",
                       ["tenant_id", "opportunity_id", "contact_id"], unique=True)
    if not _index_exists(conn, "opportunity_contacts", "ix_oc_tenant"):
        op.create_index("ix_oc_tenant", "opportunity_contacts", ["tenant_id"])
    if not _index_exists(conn, "opportunity_contacts", "ix_oc_tenant_opp"):
        op.create_index("ix_oc_tenant_opp", "opportunity_contacts", ["tenant_id", "opportunity_id"])
    if not _index_exists(conn, "opportunity_contacts", "ix_oc_contact"):
        op.create_index("ix_oc_contact", "opportunity_contacts", ["contact_id"])
    _apply_rls("opportunity_contacts")

# downgrade()
def downgrade():
    conn = op.get_bind()
    _drop_rls_policy("opportunity_contacts")
    if _table_exists(conn, "opportunity_contacts"):
        op.drop_table("opportunity_contacts")
```

**Evidence:** `0044_create_calendar_email_events.py:38-130` for create table + index + downgrade pattern. `f7a1b82c3d09` for inline RLS pattern.

---

## Pre-Implementation Checklist

| # | Prerequisite | Status |
|---|-------------|:------:|
| 1 | `commercial_opportunities` table exists | ✓ |
| 2 | `contacts` table exists with UUID PK | ✓ |
| 3 | `tenants` table exists with UUID PK | ✓ |
| 4 | RLS infrastructure (`generate_policy_sql`, `_apply_rls`) available | ✓ |
| 5 | `PostgresOpportunityRepository` exists with `delete()` method | ✓ |
| 6 | `EntityResolutionService.merge_companies()` handles company merge | ✓ (will need amendment) |
| 7 | Test infrastructure: real Postgres `salesos_test` DB + mock helpers | ✓ |
| 8 | Tenant isolation test helpers available | ✓ |
| 9 | Alembic migration environment with transaction wrapping | ✓ |
| 10 | ADR-030 ratified | ✓ |

---

## Risks Noted (During Readiness Check)

| Risk | Mitigation |
|------|-----------|
| `opportunity_id` has no FK (String(36) deferred) | Application-level cleanup in repository delete. FK added when ID normalization addresses type mismatch. |
| `opportunity_contacts` must be added to `merge_companies()` | Documented as DEF-003 extension. Added to implementation checklist. |
| No existing M2M/junction table repository — no precedent | Use standard `PostgresXxxRepository` pattern. Simple CRUD: create, delete, list_by_opportunity, list_by_contact. |
| Junction table stays empty if no CRUD API built | ADR-030 scope includes CRUD API. Frontend components deferred. |
| Odoo sync is in-memory-only — cannot auto-populate | Expected. Manual CRUD first. Auto-population requires Odoo Identity ADR. |
| `role` field may stay empty | Acceptable — nullable, optional. Future: populate from Odoo `res.partner.function` (Job Position) when Odoo ID sync is implemented. |

---

## Verdict

**ALL 12 GATES PASS. ADR-030 is ready for implementation.**

No architectural blockers. No code changes to existing tables required. No new dependencies. All patterns (junction index, RLS, migration, repository, testing) have established precedents in the codebase.

**Proceed to ADR-030 implementation sequence:**

1. Alembic migration
2. ORM model (`OpportunityContactModel`)
3. Repository (`PostgresOpportunityContactRepository`)
4. Service layer
5. RLS policy addition
6. CRUD router
7. `PostgresOpportunityRepository.delete()` orphan cleanup
8. `EntityResolutionService.merge_companies()` amendment
9. Unit tests (mock + tenant isolation)
10. Integration tests
