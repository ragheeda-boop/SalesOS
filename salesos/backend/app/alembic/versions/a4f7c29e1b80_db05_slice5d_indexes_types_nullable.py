"""DB-05 Slice 5d: additive indexes + contacts widen (criterion 7.6).

Revision ID: a4f7c29e1b80
Revises: e2b9d46f8a10
Create Date: 2026-08-01

DEC-130d / DB-05 Slice 5d:
  - Idempotent CREATE INDEX for 37 ORM-declared indexes missing in live DB
  - Safe widen contacts.name / name_ar VARCHAR(255) → VARCHAR(500)

Does NOT DROP indexes/tables/columns (KEEP companies residual = 5e).
Does NOT SET NOT NULL (needs null inventory).
Does NOT touch get_db() / DEC-085 set_config.
Type/nullable ORM↔DB alignments are metadata-only in companion ORM edits.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4f7c29e1b80"
down_revision: Union[str, None] = "e2b9d46f8a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (name, table, columns) — additive only; keep legacy rename twins
_CREATE_INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_audit_logs_outcome", "audit_logs", ["outcome"]),
    ("ix_activities_owner", "commercial_activities", ["owner_id"]),
    ("ix_activities_type_status", "commercial_activities", ["activity_type", "status"]),
    ("ix_activity_sessions_target", "commercial_activity_sessions", ["target_id", "target_type"]),
    ("ix_activity_sessions_tenant_status", "commercial_activity_sessions", ["tenant_id", "status"]),
    ("ix_commercial_contracts_expiry", "commercial_contracts", ["expiry_date"]),
    ("ix_commercial_contracts_tenant_status", "commercial_contracts", ["tenant_id", "status"]),
    ("ix_commercial_proposals_tenant_status", "commercial_proposals", ["tenant_id", "status"]),
    ("ix_commercial_quotes_tenant_status", "commercial_quotes", ["tenant_id", "status"]),
    ("ix_commercial_recs_target", "commercial_recommendations", ["target_id", "target_type"]),
    ("ix_commercial_recs_tenant_status", "commercial_recommendations", ["tenant_id", "status"]),
    ("ix_stage_entries_opportunity", "commercial_stage_entries", ["opportunity_id"]),
    ("ix_stage_entries_tenant_entered", "commercial_stage_entries", ["tenant_id", "entered_at"]),
    ("ix_companies_industry", "companies", ["industry"]),
    ("ix_companies_tenant_confidence", "companies", ["tenant_id", "confidence_score"]),
    ("ix_companies_tenant_created", "companies", ["tenant_id", "created_at"]),
    ("ix_companies_tenant_golden", "companies", ["tenant_id", "is_golden_record"]),
    ("ix_companies_tenant_status", "companies", ["tenant_id", "status"]),
    ("ix_contacts_email", "contacts", ["email"]),
    ("ix_contacts_name", "contacts", ["name"]),
    ("ix_contacts_tenant_id", "contacts", ["tenant_id"]),
    ("ix_dead_letter_queue_tenant_id", "dead_letter_queue", ["tenant_id"]),
    ("ix_device_sessions_expires", "device_sessions", ["expires_at"]),
    ("ix_device_sessions_tenant", "device_sessions", ["tenant_id"]),
    ("ix_emails_direction", "emails", ["direction"]),
    ("ix_emails_tenant_sent", "emails", ["tenant_id", "sent_at"]),
    ("ix_conflicts_tenant_status", "entity_resolution_conflicts", ["tenant_id", "status"]),
    (
        "ix_entity_resolution_conflicts_golden_record_id",
        "entity_resolution_conflicts",
        ["golden_record_id"],
    ),
    ("ix_entity_resolution_conflicts_status", "entity_resolution_conflicts", ["status"]),
    ("ix_golden_records_company_id", "golden_records", ["company_id"]),
    ("ix_golden_records_tenant_active", "golden_records", ["tenant_id", "is_active"]),
    ("ix_golden_records_tenant_company", "golden_records", ["tenant_id", "company_id"]),
    ("ix_licenses_expiry_status", "licenses", ["expiry_date", "status"]),
    ("ix_marketplace_plugins_enabled", "marketplace_plugins", ["enabled"]),
    ("ix_meetings_status", "meetings", ["status"]),
    ("ix_meetings_tenant_date", "meetings", ["tenant_id", "meeting_date"]),
    ("ix_token_blacklist_expires", "token_blacklist", ["expires_at"]),
]


def _index_exists(conn, name: str) -> bool:
    row = conn.execute(
        sa.text("SELECT 1 FROM pg_class WHERE relkind = 'i' AND relname = :n"),
        {"n": name},
    ).fetchone()
    return row is not None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _column_varchar_len(conn, table: str, column: str) -> int | None:
    row = conn.execute(
        sa.text(
            """
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :t
              AND column_name = :c
            """
        ),
        {"t": table, "c": column},
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else None


def upgrade() -> None:
    conn = op.get_bind()

    for name, table, cols in _CREATE_INDEXES:
        if not _table_exists(conn, table):
            continue
        if not _index_exists(conn, name):
            op.create_index(name, table, cols)

    if _table_exists(conn, "contacts"):
        for col in ("name", "name_ar"):
            cur = _column_varchar_len(conn, "contacts", col)
            if cur is not None and cur < 500:
                op.execute(
                    sa.text(
                        f'ALTER TABLE contacts ALTER COLUMN "{col}" TYPE VARCHAR(500)'
                    )
                )


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "contacts"):
        for col in ("name_ar", "name"):
            cur = _column_varchar_len(conn, "contacts", col)
            if cur is not None and cur > 255:
                op.execute(
                    sa.text(
                        f'ALTER TABLE contacts ALTER COLUMN "{col}" TYPE VARCHAR(255)'
                    )
                )

    for name, table, _cols in reversed(_CREATE_INDEXES):
        if _index_exists(conn, name):
            op.drop_index(name, table_name=table)
