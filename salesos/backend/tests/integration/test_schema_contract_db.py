"""Schema contract: static SQL and ORM models must match the migrated schema.

Runs the two audit scripts against a DISPOSABLE database migrated to head,
named by SCHEMA_CONTRACT_DSN (skipped when unset, so it never touches
salesos_test or any shared database by accident).

Every tolerated exception is listed below with the report that justifies it.
A new failure means new drift: fix it, or add it here with a report citing why.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

DSN = os.environ.get("SCHEMA_CONTRACT_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="set SCHEMA_CONTRACT_DSN to a disposable migrated DB")

# file:line -> justification. Lines are matched by file + error text, not line
# number alone, so unrelated edits above a statement do not break the test.
KNOWN_SQL_FAILURES = {
    ("app/modules/gtm/evidence_router.py", "syntax error at or near \"NULL\""):
        "false positive: expanding bind `IN :ids` rendered as IN NULL (report 98)",
}
KNOWN_MISSING_TABLES = {
    "public.event_outbox": "created on demand by sdk.events.outbox; relay never wired (report 101)",
}


def _normalise(path: str) -> str:
    return path.replace("\\", "/")


def test_every_static_sql_statement_plans():
    from audit_sql_explain_sweep import sweep

    failures = asyncio.run(sweep(DSN))
    unexpected = [
        f for f in failures
        if not any(_normalise(f["file"]) == k[0] and k[1] in f["error"] for k in KNOWN_SQL_FAILURES)
    ]
    assert unexpected == [], "new SQL/schema drift:\n" + "\n".join(
        f"{f['file']}:{f['line']} {f['error']}" for f in unexpected)


def test_orm_models_match_schema():
    from audit_orm_schema_drift import check

    report = asyncio.run(check(DSN))
    assert report["columns_checked"] > 1000
    assert report["missing_columns"] == []
    assert report["type_mismatch"] == []
    assert set(report["missing_tables"]) <= set(KNOWN_MISSING_TABLES), report["missing_tables"]
