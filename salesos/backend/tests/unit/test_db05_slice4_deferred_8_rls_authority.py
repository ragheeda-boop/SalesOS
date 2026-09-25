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
    # 51 -> 55: four governed fact-ledger tables (evidence_records,
    # canonical_facts, fact_evidence, canonical_fact_events). 55 -> 66: eleven
    # more Category A tables added across later sessions (opportunity_contacts,
    # activity_attributions, odoo_external_ids, company_signals, nba_feedback,
    # action_outcomes, sales_followups, customer_survey_responses,
    # commercial_opportunity_notes, commercial_quota_snapshots,
    # scheduled_jobs/job_executions) — this assertion had drifted stale
    # (still asserting 55) across all of that growth; 66 is the current,
    # verified-correct count (confirmed no duplicates, every entry backed by
    # a real migration's ENABLE+FORCE RLS + tenant_isolation_<table> policy).
    assert len(ALL_TENANT_TABLES) == 66
    for t in DB05_DEFERRED_8_TENANT_TABLES:
        assert t not in ALL_TENANT_TABLES


def test_fact_ledger_tables_are_in_tenant_rls_inventory() -> None:
    for table in (
        "evidence_records",
        "canonical_facts",
        "fact_evidence",
        "canonical_fact_events",
    ):
        assert table in ALL_TENANT_TABLES
        sql = generate_policy_sql(table)
        assert f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY' in sql
        assert f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY' in sql
        assert "current_setting('app.tenant_id', true)" in sql


def test_deferred_8_policy_sql_force_fail_closed() -> None:
    for t in DB05_DEFERRED_8_TENANT_TABLES:
        sql = generate_policy_sql(t)
        assert f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY' in sql
        assert f'ALTER TABLE "{t}" FORCE ROW LEVEL SECURITY' in sql
        assert f"tenant_isolation_{t}" in sql
        assert "current_setting('app.tenant_id', true)" in sql
        # Predicate must stay fail-closed (no NULL bypass).
        assert "IS NULL" not in sql.upper()
        assert " OR " not in sql.upper()
