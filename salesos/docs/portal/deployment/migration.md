# Database Migration Guide

> **ترحيل قاعدة البيانات — إدارة التغييرات في schema**

---

## Migration Framework

All database migrations use Alembic (SQLAlchemy migrations).

```bash
# Create a new migration
docker compose exec api alembic revision --autogenerate -m "add_opportunity_table"

# Run migrations
docker compose exec api alembic upgrade head

# Rollback one step
docker compose exec api alembic downgrade -1

# Rollback to specific revision
docker compose exec api alembic downgrade <revision_id>

# View history
docker compose exec api alembic history
```

---

## Migration Best Practices

1. **All migrations must be reversible** — every `upgrade()` needs a `downgrade()`
2. **Test migrations on staging first** — never run untested migrations on production
3. **Back up the database** before running migrations on production
4. **Use transactions** — migrations that span multiple tables should be atomic
5. **Avoid locking** — use `CONCURRENTLY` for index creation, `CHECK OPTION` for large tables

---

## Schema Changes

```python
"""add_opportunity_table

Revision ID: abc123
Revises: def456
Create Date: 2026-07-11 10:00:00.000
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'opportunities',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('value', sa.Numeric(15, 2), default=0),
        sa.Column('currency', sa.String(3), default='SAR'),
        sa.Column('probability', sa.Numeric(3, 2), default=0.1),
        sa.Column('health', sa.String(20), default='healthy'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_opportunities_tenant', 'opportunities', ['tenant_id'])
    op.create_index('idx_opportunities_stage', 'opportunities', ['stage'])

def downgrade():
    op.drop_table('opportunities')
```

---

## Data Migrations

For data transformations that need to run alongside schema changes:

```python
def upgrade():
    # Schema change first
    op.add_column('opportunities', sa.Column('health', sa.String(20)))

    # Data migration
    op.execute("""
        UPDATE opportunities
        SET health = CASE
            WHEN days_since_activity < 7 THEN 'healthy'
            WHEN days_since_activity < 14 THEN 'at_risk'
            ELSE 'critical'
        END
    """)
```

---

## Migration Plan Template

```yaml
migration_id: "add_nba_feedback_table"
date: "2026-07-11"
description: "Track NBA recommendation outcomes"
changes:
  - type: create_table
    name: nba_feedback
    columns:
      - id: UUID PRIMARY KEY
      - tenant_id: UUID NOT NULL
      - opportunity_id: UUID NOT NULL
      - nba_id: UUID NOT NULL
      - action: VARCHAR(20) NOT NULL  # accepted / dismissed / completed
      - reason: TEXT
      - created_at: TIMESTAMPTZ DEFAULT NOW()
  - type: create_index
    table: nba_feedback
    columns: [tenant_id, nba_id]
rollback:
  - type: drop_table
    name: nba_feedback
risk: low
estimated_downtime: 30s
```

---

## Production Migration Process

```
1. Announce maintenance window (if required)
2. Back up database
3. Run migration on staging → verify
4. Run migration on production read replica → verify
5. Promote read replica (if zero-downtime needed)
6. Run migration on primary
7. Verify all services healthy
8. Announce completion
```

---

## Related

| Resource | Link |
|----------|------|
| v0.5 to v0.9 Migration | [Migration Guide](../migration-guides/v0.5-to-v0.9.md) |
| Wave 3 Data Warehouse | [Warehouse Schema](../../docs/wave-3/04-ANALYTICS_REPORTING.md#2-data-warehouse-design) |
