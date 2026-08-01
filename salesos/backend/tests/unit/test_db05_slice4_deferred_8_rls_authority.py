"""DB-05 Slice 4 (DEC-123): deferred-8 RLS authority — generator inventory."""

from __future__ import annotations

from scripts.generate_rls_policies import (
    ALL_TENANT_TABLES,
    DB05_DEFERRED_8_TENANT_TABLES,
    generate_policy_sql,
)

EXPECTED = [
    "admin_licenses",
    "admin_invoices",
    "admin_transactions",
    "admin_ai_costs",
    "admin_jobs",
    "webhook_endpoints",
    "scoring_scorecards",
    "revenue_analytics_snapshots",
]


def test_deferred_8_inventory_exact() -> None:
    assert DB05_DEFERRED_8_TENANT_TABLES == EXPECTED


def test_deferred_8_not_folded_into_category_a_47() -> None:
    assert len(ALL_TENANT_TABLES) == 47
    for t in DB05_DEFERRED_8_TENANT_TABLES:
        assert t not in ALL_TENANT_TABLES


def test_deferred_8_policy_sql_force_fail_closed() -> None:
    for t in DB05_DEFERRED_8_TENANT_TABLES:
        sql = generate_policy_sql(t)
        assert f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY' in sql
        assert f'ALTER TABLE "{t}" FORCE ROW LEVEL SECURITY' in sql
        assert f'tenant_isolation_{t}' in sql
        assert "current_setting('app.tenant_id', true)" in sql
        # Predicate must stay fail-closed (no NULL bypass).
        assert "IS NULL" not in sql.upper()
        assert " OR " not in sql.upper()
