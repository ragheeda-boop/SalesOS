#!/usr/bin/env python3
"""Generate PostgreSQL Row-Level Security (RLS) policies for tenant-scoped tables.

STORY-02-01 (Sprint 02, Phase 0): "RLS design, start" — this script targets a
10-table pilot set only. It does not enable RLS on the other ~62 tenant-scoped
tables and it is never invoked automatically (not from CI, not from Alembic,
not from application startup). The full 72-table rollout is Sprint 03's
STORY-02-01 ("RLS rollout, complete"), tracked separately in
docs/program/SPRINT_PLAN/Sprint-03.md.

Usage (local/docker):
  python scripts/generate_rls_policies.py                       # print SQL, default, side-effect free
  python scripts/generate_rls_policies.py --tables companies users
  python scripts/generate_rls_policies.py --apply --database-url postgresql+asyncpg://... \
      --yes-i-understand-this-affects-live-queries

Never runs automatically. Never targets production by itself — --apply
requires both an explicit --database-url and the long confirmation flag.

Why FORCE ROW LEVEL SECURITY, why current_setting(..., true), why USING +
WITH CHECK, why the ::text cast on both sides — see the docstring on
generate_policy_sql() below; read it before changing the template.
"""
from __future__ import annotations

import argparse
import sys

SESSION_VAR = "app.tenant_id"

# Sprint 03 full inventory: tenant-scoped tables with existing migrations.
# Tables with tenant_id but NO migration yet (12 tracked in RISK_REGISTER.md
# R-09) are excluded — RLS on them will be added after CREATE TABLE lands.
# Tables without a tenant_id column (keyed via parent FK) are excluded from
# ALL_TENANT_TABLES — Category B inventory + slices pinned in DEC-110.
# B1–B4 join children use generate_join_policy_sql() /
# CATEGORY_B1_JOIN_TABLES … CATEGORY_B4_JOIN_TABLES (DEC-110).
ALL_TENANT_TABLES: list[str] = [
    # ── Identity / Auth ──
    "users",                      # app/modules/identity/models.py — uuid
    "device_sessions",            # app/modules/identity/models.py — uuid
    "api_keys",                   # app/modules/api_keys/models.py — uuid
    # ── Company / Contact ──
    "companies",                  # app/modules/company/models.py — uuid
    "contacts",                   # app/modules/contact/models.py — uuid
    "company_features",           # runtime/feature_store — String(36); CREATE TABLE in 0002_feature_store
    # ── Commercial ──
    "commercial_opportunities",   # domains/commercial/infrastructure/models.py — String(36)
    "commercial_stage_entries",   # domains/commercial/infrastructure/models.py — String(36)
    "commercial_pipeline_definitions",  # domains/commercial/infrastructure/models.py — String(36)
    "commercial_activity_sessions",    # domains/commercial/infrastructure/models.py — String(36)
    "commercial_quotes",          # domains/commercial/infrastructure/models.py — String(36)
    "commercial_proposals",       # domains/commercial/infrastructure/models.py — String(36)
    "commercial_contracts",       # domains/commercial/infrastructure/models.py — String(36)
    "commercial_forecast_snapshots",  # domains/commercial/infrastructure/models.py — String(36)
    "commercial_analytics_snapshots", # domains/commercial/infrastructure/models.py — String(36)
    "commercial_decision_contexts",   # domains/commercial/infrastructure/models.py — String(36)
    "commercial_policies",        # domains/commercial/infrastructure/models.py — String(36)
    "meetings",                   # domains/commercial/infrastructure/models.py — String(36)
    "emails",                     # domains/commercial/infrastructure/models.py — String(36)
    "commercial_recommendations", # domains/commercial/infrastructure/models.py — String(36)
    # ── Revenue ──
    "opportunities",              # app/modules/revenue_execution/models.py — uuid
    "tasks",                      # app/modules/revenue_execution/models.py — uuid
    # ── Workflow (migrated tables only) ──
    "workflow_definitions",       # domains/workflow/db_models.py — String(64)
    "workflow_executions",        # domains/workflow/db_models.py — String(64)
    "scheduled_jobs",             # domains/workflow/db_models.py — String(64)
    "job_executions",             # domains/workflow/db_models.py — String(64)
    # ── Analytics ──
    "analytics_reports",          # domains/analytics/infrastructure/models.py — String(36)
    "analytics_scheduled_reports", # domains/analytics/infrastructure/models.py — String(36)
    # ── Entity Resolution ──
    "golden_records",             # app/modules/entity_resolution/models.py — uuid
    "entity_resolution_conflicts", # app/modules/entity_resolution/models.py — uuid
    "entity_resolution_log",      # app/modules/entity_resolution/models.py — uuid
    "dead_letter_queue",          # app/modules/entity_resolution/models.py — uuid
    # ── Admin (migrated tables only) ──
    "tenant_configs",             # app/modules/admin/db_models.py — String(64)
    "admin_roles",                # app/modules/admin/db_models.py — String(64), nullable
    # ── Employee ──
    "employee_signals",           # domains/employee/db_models.py — uuid
    "employee_scores",            # domains/employee/db_models.py — uuid
    "employee_calendar_events",   # domains/employee/intelligence_models.py — uuid
    "employee_email_events",      # domains/employee/intelligence_models.py — uuid
    "employee_oauth_tokens",      # domains/employee/oauth_service.py — uuid
    # ── Communication Hub ──
    "google_accounts",            # app/modules/communication_hub/models.py — uuid
    # ── Audit / Telemetry / Notifications ──
    "audit_logs",                 # app/modules/audit/models.py — String(64), schema=audit
    "telemetry_events",           # app/modules/telemetry/models.py — String(64)
    "notifications",              # domains/notifications/db_models.py — String(64)
    # ── Decision Center ──
    "decision_center_decisions",  # domains/decision_center/postgres_repo.py — String
    "decision_center_templates",  # domains/decision_center/postgres_repo.py — String, nullable
    # ── Timeline ──
    "timeline_entries",           # domains/timeline/models.py — String(36), nullable
    # ── Webhooks (migrated tables only) ──
    "webhook_subscriptions",      # app/modules/webhooks/repository.py — runtime table
]

# DEC-110 Slice B1 (S04-CATB-01): company children — no tenant_id; isolate via companies.
# Do NOT fold into ALL_TENANT_TABLES (Category A stays 47 / DEC-044).
CATEGORY_B1_JOIN_TABLES: list[tuple[str, str, str]] = [
    # (child_table, parent_table, child_fk_column)
    ("branches", "companies", "company_id"),
    ("licenses", "companies", "company_id"),
]

# DEC-110 Slice B2 (S04-CATB-02): commercial children — no tenant_id; isolate via
# commercial_activity_sessions / commercial_quotes (both Category A).
CATEGORY_B2_JOIN_TABLES: list[tuple[str, str, str]] = [
    # (child_table, parent_table, child_fk_column)
    ("commercial_activities", "commercial_activity_sessions", "session_id"),
    ("commercial_quote_lines", "commercial_quotes", "quote_id"),
]

# DEC-110 Slice B3 (S04-CATB-03): analytics children — no tenant_id; isolate via
# analytics_reports (Category A).
CATEGORY_B3_JOIN_TABLES: list[tuple[str, str, str]] = [
    # (child_table, parent_table, child_fk_column)
    ("analytics_report_executions", "analytics_reports", "report_id"),
    ("analytics_report_shares", "analytics_reports", "report_id"),
]

# DEC-110 Slice B4 (S04-CATB-04): decision-center children — no tenant_id; isolate
# via decision_center_decisions (Category A). Parent PK is UUID; child FK is
# varchar — join uses p.id::text (same cast as postgres_repo feedback join).
CATEGORY_B4_JOIN_TABLES: list[tuple[str, str, str]] = [
    # (child_table, parent_table, child_fk_column)
    ("decision_center_audits", "decision_center_decisions", "decision_id"),
    ("decision_center_feedback", "decision_center_decisions", "decision_id"),
]


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

    Same FORCE / fail-closed / USING+WITH CHECK rationale as generate_policy_sql().
    Predicate: EXISTS parent row whose tenant_id matches app.tenant_id GUC.

    When cast_parent_pk_to_text=True (B4 decision-center children), compare
    p.<pk>::text to the varchar FK — parent id is UUID, child decision_id is
    String(64) (0038 / BaseModel).
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
        f'        WHERE {parent_pk_expr} = "{child_table}".{fk_column}\n'
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


def generate_policy_sql(
    table: str,
    tenant_column: str = "tenant_id",
    session_var: str = SESSION_VAR,
    policy_name: str | None = None,
) -> str:
    """Return the DDL that enables and enforces tenant-isolation RLS on `table`.

    Design notes — read before changing:

    - `FORCE ROW LEVEL SECURITY` is not optional. Plain `ENABLE ROW LEVEL
      SECURITY` exempts the table's OWNER from every policy, and the
      application connects as the owning role — so without FORCE, this would
      look correct in a naive test (run as a non-owner) while doing nothing
      at all for real application traffic.
    - `current_setting(session_var, true)` passes missing_ok=true, so any
      session that never sets the variable (a stray maintenance connection,
      a forgotten code path) gets NULL back instead of an error, and the
      comparison then evaluates to NULL/false — fail-closed (denied), not
      fail-open. This is deliberate: an unset tenant context must never
      default to "show everything."
    - Both `USING` (governs SELECT/UPDATE/DELETE visibility) and `WITH CHECK`
      (governs INSERT/UPDATE legality) carry the identical predicate. A
      USING-only policy would still let a session write a row stamped with
      someone else's tenant_id — that closes the read half of the IDOR class
      but not the write half.
    - Both sides of the comparison are cast to `::text`. tenant_id is a
      native `uuid` column on some tables (companies, contacts, users,
      admin_invoices) and `varchar` on others (commercial_*,
      decision_center_*, and every workflow-domain table) — casting avoids
      maintaining two policy templates for otherwise identical logic.
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


def generate_all_sql(tables: list[str] | None = None) -> str:
    tables = tables if tables is not None else ALL_TENANT_TABLES
    parts = [
        "-- Generated by scripts/generate_rls_policies.py",
        "-- STORY-02-01 (Sprint 02): pilot scope only, 10 tables. See module docstring.",
        "--",
        "-- WARNING: do not apply this to a database real application traffic",
        "-- depends on until the app's DB session layer sets `app.tenant_id`",
        "-- per request (Sprint 03, STORY-02-01 'RLS rollout, complete'). Until",
        "-- then, enabling this on a live-serving table makes every query",
        "-- against it return zero rows, for every tenant, silently.",
        "",
    ]
    for t in tables:
        parts.append(f"-- {t}")
        parts.append(generate_policy_sql(t))
    return "\n".join(parts)


async def _apply(database_url: str, tables: list[str]) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            for t in tables:
                await conn.execute(text(generate_policy_sql(t)))
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tables", nargs="*", default=None, help="Override the pilot table list (default: the 10-table Sprint 02 set).")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute the generated DDL against --database-url instead of printing it.",
    )
    parser.add_argument("--database-url", default=None, help="asyncpg-style SQLAlchemy URL. Required with --apply.")
    parser.add_argument(
        "--yes-i-understand-this-affects-live-queries",
        action="store_true",
        dest="confirmed",
        help="Required with --apply. See the WARNING in generate_all_sql().",
    )
    args = parser.parse_args(argv)

    tables = args.tables if args.tables is not None else ALL_TENANT_TABLES

    if args.apply:
        if not args.confirmed:
            print(
                "Refusing to --apply without --yes-i-understand-this-affects-live-queries.\n"
                "Enabling RLS on a table application traffic depends on, before the app sets\n"
                "`app.tenant_id` per request (Sprint 03 work), makes every query against that\n"
                "table return zero rows. This flag exists so that cannot happen by accident.",
                file=sys.stderr,
            )
            return 2
        if not args.database_url:
            print("Refusing to --apply without --database-url.", file=sys.stderr)
            return 2
        import asyncio

        asyncio.run(_apply(args.database_url, tables))
        print(f"Applied RLS policies to {len(tables)} table(s): {', '.join(tables)}")
        return 0

    print(generate_all_sql(tables))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
