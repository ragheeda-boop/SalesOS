"""STORY-08-01 — SourceConnector contract + FakeSourceConnector certification."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.integration_hub import (
    FakeSourceConnector,
    SourceConnector,
    certify_source_connector,
)


def test_fake_is_source_connector() -> None:
    assert isinstance(FakeSourceConnector(), SourceConnector)


def test_framework_modules_have_no_odoo_leakage() -> None:
    import re

    root = Path(__file__).resolve().parents[2] / "app" / "modules" / "integration_hub"
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        # Forbid importing the external ``odoo`` package (not our OdooAdapter symbol).
        assert re.search(r"(?m)^\s*(from|import)\s+odoo\b", text) is None
        # Vendor adapter *definitions* stay isolated (imports for router wiring are OK).
        if path.name not in {"fake_adapter.py", "odoo_adapter.py"}:
            assert "class OdooAdapter" not in text


@pytest.mark.asyncio
async def test_fake_adapter_certifies() -> None:
    result = await certify_source_connector(FakeSourceConnector())
    assert result["ok"] is True
    assert result["connector_key"] == "fake"
    assert result["pulled"] >= 1


@pytest.mark.asyncio
async def test_connection_failure_fails_certification() -> None:
    with pytest.raises(AssertionError, match="test_connection failed"):
        await certify_source_connector(FakeSourceConnector(fail_connection=True))
