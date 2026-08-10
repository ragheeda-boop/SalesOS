"""Row-Level Security (RLS) migration support — Alembic-only helper library.

Pure SQL-string generation.  Zero database I/O, zero filesystem I/O,
zero environment-dependent behaviour.  Imported by Alembic migration
files that need to generate RLS DDL during ``alembic upgrade head``.

Canonical source: ``scripts/generate_rls_policies.py`` (dev/CLI tool).
This module contains the **same** functions and constants, duplicated
here so that the production Docker image does not need the ``scripts/``
package.
"""
from __future__ import annotations

SESSION_VAR = "app.tenant_id"

# ---------------------------------------------------------------------------
# Category A — tables with a direct tenant_id column
# ---------------------------------------------------------------------------

ALL_TENANT_TABLES: list[str] = [
    # ── Identity / Auth ──
    "users",
    "device_sessions",
    "api_keys",
    # ── Company / Contact ──
    "companies",
    "contacts",
    "company_features",
    # ── Commercial ──
    "commercial_opportunities",
    "commercial_stage_entries",
    "commercial_pipeline_definitions",
    "commercial_activity_sessions",
    "commercial_quotes",
    "commercial_proposals",
    "commercial_contracts",
    "commercial_forecast_snapshots",
    "commercial_analytics_snapshots",
    "commercial_decision_contexts",
    "commercial_policies",
    "meetings",
    "emails",
    "commercial_recommendations",
    "opportunity_contacts",
    "activity_attributions",
    "odoo_external_ids",
    "company_signals",
    # ── Revenue ──
    "opportunities",
    "tasks",
    # ── Workflow (migrated tables only) ──
    "workflow_definitions",
    "workflow_executions",
    "scheduled_jobs",
    "job_executions",
    # ── Analytics ──
    "analytics_reports",
    "analytics_scheduled_reports",
    # ── Entity Resolution ──
    "golden_records",
    "entity_resolution_conflicts",
    "entity_resolution_log",
    "dead_letter_queue",
    # ── Admin (migrated tables only) ──
    "tenant_configs",
    "admin_roles",
    # ── Employee ──
    "employee_signals",
    "employee_scores",
    "employee_calendar_events",
    "employee_email_events",
    "employee_oauth_tokens",
    # ── Communication Hub ──
    "google_accounts",
    # ── Audit / Telemetry / Notifications ──
    "audit_logs",
    "telemetry_events",
    "notifications",
    # ── Decision Center ──
    "decision_center_decisions",
    "decision_center_templates",
    # ── Timeline ──
    "timeline_entries",
    # ── Webhooks (migrated tables only) ──
    "webhook_subscriptions",
]

# ---------------------------------------------------------------------------
# Category B — join/child tables (no tenant_id; isolate via parent FK)
# ---------------------------------------------------------------------------

CATEGORY_B1_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("branches", "companies", "company_id"),
    ("licenses", "companies", "company_id"),
]

CATEGORY_B2_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("commercial_activities", "commercial_activity_sessions", "session_id"),
    ("commercial_quote_lines", "commercial_quotes", "quote_id"),
]

CATEGORY_B3_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("analytics_report_executions", "analytics_reports", "report_id"),
    ("analytics_report_shares", "analytics_reports", "report_id"),
]

CATEGORY_B4_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("decision_center_audits", "decision_center_decisions", "decision_id"),
    ("decision_center_feedback", "decision_center_decisions", "decision_id"),
]

CATEGORY_B5_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("password_reset_tokens", "users", "user_id"),
    ("refresh_token_families", "users", "user_id"),
]

CATEGORY_B6_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("webhook_deliveries", "webhook_subscriptions", "subscription_id"),
]

CATEGORY_B7_JOIN_TABLES: list[tuple[str, str, str]] = [
    ("admin_role_permissions", "admin_roles", "role_id"),
]

# ---------------------------------------------------------------------------
# DEC-110 deferred-8 / DB-05 Slice 4 — Category A tables without prior RLS
# ---------------------------------------------------------------------------

DB05_DEFERRED_8_TENANT_TABLES: list[str] = [
    "admin_licenses",
    "admin_invoices",
    "admin_transactions",
    "admin_ai_costs",
    "admin_jobs",
    "webhook_endpoints",
    "scoring_scorecards",
    "revenue_analytics_snapshots",
]


# ---------------------------------------------------------------------------
# SQL generators
# ---------------------------------------------------------------------------

def generate_policy_sql(
    table: str,
    tenant_column: str = "tenant_id",
    session_var: str = SESSION_VAR,
    policy_name: str | None = None,
) -> str:
    """Return DDL that enables and enforces tenant-isolation RLS on *table*.

    Design notes:
    - ``FORCE ROW LEVEL SECURITY`` — owner is exempt without it.
    - ``current_setting(session_var, true)`` — missing_ok, fail-closed.
    - Both ``USING`` and ``WITH CHECK`` carry the identical predicate.
    - ``::text`` cast avoids uuid-vs-varchar mismatches.
    """
    policy_name = policy_name or f"tenant_isolation_{table}"
    return (
        f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;\n'
        f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY;\n'
        f'DROP POLICY IF EXISTS "{policy_name}" ON "{table}";\n'
        f'CREATE POLICY "{policy_name}" ON "{table}"\n'
        f"    FOR ALL\n"
        f"    USING ({tenant_column}::text = current_setting('{session_var}', true))\n"
        f"    WITH CHECK ({tenant_column}::text = current_setting('{session_var}', true));\n"
    )


def generate_join_policy_sql(
    child_table: str,
    parent_table: str,
    fk_column: str,
    parent_tenant_column: str = "tenant_id",
    parent_pk_column: str = "id",
    session_var: str = SESSION_VAR,
    policy_name: str | None = None,
    cast_parent_pk_to_text: bool = False,
) -> str:
    """Return DDL that enables join/parent-FK RLS on a Category B child table.

    Predicate: ``EXISTS`` parent row whose ``tenant_id`` matches
    ``app.tenant_id`` GUC.  ``cast_parent_pk_to_text=True`` for
    decision-center children (UUID parent PK, varchar child FK).
    """
    policy_name = policy_name or f"tenant_isolation_{child_table}"
    parent_pk_expr = (
        f"p.{parent_pk_column}::text"
        if cast_parent_pk_to_text
        else f"p.{parent_pk_column}"
    )
    exists_pred = (
        f"EXISTS (\n"
        f'        SELECT 1 FROM "{parent_table}" p\n'
        f"        WHERE {parent_pk_expr} = \"{child_table}\".{fk_column}\n"
        f"          AND p.{parent_tenant_column}::text = "
        f"current_setting('{session_var}', true)\n"
        f"    )"
    )
    return (
        f'ALTER TABLE "{child_table}" ENABLE ROW LEVEL SECURITY;\n'
        f'ALTER TABLE "{child_table}" FORCE ROW LEVEL SECURITY;\n'
        f'DROP POLICY IF EXISTS "{policy_name}" ON "{child_table}";\n'
        f'CREATE POLICY "{policy_name}" ON "{child_table}"\n'
        f"    FOR ALL\n"
        f"    USING ({exists_pred})\n"
        f"    WITH CHECK ({exists_pred});\n"
    )
