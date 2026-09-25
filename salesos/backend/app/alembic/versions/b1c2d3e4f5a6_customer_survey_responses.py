"""Persist tenant-scoped customer NPS and CSAT responses.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import generate_policy_sql


revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a0b1c2d3e4f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_survey_responses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("survey_type", sa.String(8), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("survey_type IN ('nps', 'csat')", name="ck_customer_survey_type"),
        sa.CheckConstraint(
            "(survey_type = 'nps' AND score >= 0 AND score <= 10) "
            "OR (survey_type = 'csat' AND score >= 1 AND score <= 5)",
            name="ck_customer_survey_score_scale",
        ),
        sa.UniqueConstraint(
            "tenant_id", "company_id", "idempotency_key",
            name="uq_customer_survey_response_idempotency",
        ),
    )
    op.create_index(
        "ix_customer_survey_tenant_company_recorded",
        "customer_survey_responses",
        ["tenant_id", "company_id", "recorded_at"],
    )
    for statement in generate_policy_sql("customer_survey_responses").strip().split(";\n"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))
    op.execute(sa.text("REVOKE ALL ON customer_survey_responses FROM PUBLIC"))
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
            "THEN GRANT SELECT, INSERT ON customer_survey_responses TO salesos_app; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(sa.text('DROP POLICY IF EXISTS "tenant_isolation_customer_survey_responses" ON "customer_survey_responses"'))
    op.execute(sa.text('ALTER TABLE "customer_survey_responses" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "customer_survey_responses" DISABLE ROW LEVEL SECURITY'))
    op.drop_index("ix_customer_survey_tenant_company_recorded", table_name="customer_survey_responses")
    op.drop_table("customer_survey_responses")
