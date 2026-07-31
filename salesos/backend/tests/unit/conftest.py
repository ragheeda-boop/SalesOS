"""Unit test conftest — overrides root conftest's DB setup with no-op."""

import os
from pathlib import Path

os.environ.setdefault("SALESOS_TESTING", "true")
os.environ.setdefault("SECRET_KEY", "t3st-s3cr3t-k3y-f0r-unit-t3sts-m1n-32-ch4rs!!")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "jwt-t3st-s3cr3t-f0r-unit-t3sts-m1n-32-ch4rs!!")
os.environ.setdefault("SALESOS_JWKS_ALLOW_REGENERATE", "1")


import pytest

_QUARANTINE_FILE = Path(__file__).with_name("QUARANTINE.txt")


def _load_quarantine() -> set[str]:
    if not _QUARANTINE_FILE.is_file():
        return set()
    entries: set[str] = set()
    for line in _QUARANTINE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries.add(line)
    return entries


def pytest_collection_modifyitems(config, items):
    """Skip node ids listed in QUARANTINE.txt (PROD-W3-001 documented quarantine)."""
    quarantine = _load_quarantine()
    if not quarantine:
        return
    skip = pytest.mark.skip(reason="Listed in tests/unit/QUARANTINE.txt (PROD-W3-001)")
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        for entry in quarantine:
            if nodeid == entry or nodeid.endswith(entry) or entry in nodeid:
                item.add_marker(skip)
                break


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Override root conftest's DB-heavy setup_database with a no-op for unit tests."""
    yield
