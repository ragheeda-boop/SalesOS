"""Allow CRM companies without a government CR.

Product rule 2026-09-11: do not drop no-CR accounts; merge only on SAFE CR
(additional contact). CR can be filled later. Never fabricate CR numbers.

Revision ID: p7q8r9s0t1u2
Revises: o0p1q2r3s4t5
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p7q8r9s0t1u2"
down_revision: Union[str, None] = "o0p1q2r3s4t5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "companies",
        "cr_number",
        existing_type=sa.String(50),
        nullable=True,
    )
    op.execute(
        """
        UPDATE companies
        SET cr_number = NULL
        WHERE cr_number IS NOT NULL AND btrim(cr_number) = ''
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE companies
        SET cr_number = 'PENDING-' || replace(id::text, '-', '')
        WHERE cr_number IS NULL
        """
    )
    op.alter_column(
        "companies",
        "cr_number",
        existing_type=sa.String(50),
        nullable=False,
    )
