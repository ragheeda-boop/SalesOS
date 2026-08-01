"""DEC-085 / R-26: CI guard — get_db() tenant GUC must use set_config, never SET LOCAL.

Postgres rejects bind parameters in SET/SET LOCAL ("syntax error at or near $1").
Parallel agents reintroduced SET LOCAL four times; this source guard fails fast
in unit CI so a fifth regression cannot land unnoticed.

Does not touch RLS integration suites — those may still use SET LOCAL with
literal tenant UUIDs for adversarial fixtures.
"""

from __future__ import annotations

import re
from pathlib import Path

DATABASE_PY = Path(__file__).resolve().parents[2] / "app" / "database.py"

_SET_LOCAL_TENANT = re.compile(
    r"SET\s+LOCAL\s+app\.tenant_id",
    re.IGNORECASE,
)
_SET_CONFIG_TENANT = re.compile(
    r"set_config\s*\(\s*['\"]app\.tenant_id['\"]",
    re.IGNORECASE,
)


def _get_db_source() -> str:
    source = DATABASE_PY.read_text(encoding="utf-8")
    match = re.search(
        r"async def get_db\b.*?(?=\n(?:async )?def |\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, "get_db() not found in app/database.py"
    return match.group(0)


def test_get_db_uses_set_config_for_tenant_guc():
    """DEC-085: get_db must call set_config('app.tenant_id', …, true)."""
    body = _get_db_source()
    assert _SET_CONFIG_TENANT.search(body), (
        "DEC-085 / R-26: get_db() must use "
        "SELECT set_config('app.tenant_id', :tenant_id, true). "
        "Missing set_config call in app/database.py."
    )


def test_get_db_never_uses_set_local_for_tenant_guc():
    """DEC-085: SET LOCAL app.tenant_id = :tenant_id is invalid Postgres with binds."""
    body = _get_db_source()
    assert not _SET_LOCAL_TENANT.search(body), (
        "DEC-085 / R-26 REGRESSION: get_db() uses SET LOCAL app.tenant_id. "
        "Postgres rejects bind params in SET/SET LOCAL. Restore "
        "SELECT set_config('app.tenant_id', :tenant_id, true)."
    )
