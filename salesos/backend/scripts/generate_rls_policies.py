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

# Sprint 02 pilot set: 10 tables, deliberately spanning both tenant_id column
# representations that exist in this codebase today (uuid.UUID and
# String/varchar) and six distinct domains, so the generator — and the RLS
# mechanism itself — is proven against real, heterogeneous schema shapes
# before Sprint 03 scales it to all 72 tenant-scoped tables. Selection
# rationale is recorded in the Sprint 02 report, not just here.
PILOT_TABLES: list[str] = [
    "companies",                  # app/modules/company/models.py — uuid.UUID tenant_id
    "contacts",                   # app/modules/contact/models.py — uuid.UUID tenant_id
    "users",                      # app/modules/identity/models.py — uuid.UUID tenant_id
    "admin_invoices",             # app/modules/admin/db_models.py — uuid.UUID tenant_id
    "commercial_opportunities",   # domains/commercial/infrastructure/models.py — String(36)
    "decision_center_decisions",  # domains/decision_center/postgres_repo.py — String, IDOR-fixed in Sprint 01
    "webhook_endpoints",          # domains/workflow/db_models.py — String(64), SSRF-adjacent
    "workflow_definitions",       # domains/workflow/db_models.py — String(64)
    "workflow_executions",        # domains/workflow/db_models.py — String(64)
    "scheduled_jobs",             # domains/workflow/db_models.py — String(64)
]


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
    tables = tables if tables is not None else PILOT_TABLES
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

    tables = args.tables if args.tables is not None else PILOT_TABLES

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
