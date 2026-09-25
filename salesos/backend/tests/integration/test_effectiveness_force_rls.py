"""Database proof that account_funnel and score_observations force RLS.

Mechanical audit finding (project-audit/57): both tables had
ENABLE ROW LEVEL SECURITY and a tenant policy from their originating
migrations, but neither had FORCE ROW LEVEL SECURITY, unlike every other
table in the canonical DEC-085 inventory. Migration 70193187420d adds the
missing FORCE clause only.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine

TABLES = ("account_funnel", "score_observations")


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_account_funnel_and_score_observations_force_rls():
    async with async_session() as session:
        for table in TABLES:
            row = (
                await session.execute(
                    text(
                        "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                        "WHERE relname = :t AND relkind = 'r'"
                    ),
                    {"t": table},
                )
            ).one()
            row_security, force_row_security = row
            assert row_security is True, f"{table} must have RLS enabled"
            assert force_row_security is True, f"{table} must FORCE RLS (regression check)"

        for table in TABLES:
            policy_count = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM pg_policies "
                        "WHERE schemaname = 'public' AND tablename = :t "
                        "AND policyname = :p"
                    ),
                    {"t": table, "p": f"tenant_isolation_{table}"},
                )
            ).scalar()
            assert policy_count == 1, f"{table} must keep exactly one canonical tenant policy"
        await session.rollback()
