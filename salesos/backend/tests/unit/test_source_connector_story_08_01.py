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
    root = Path(__file__).resolve().parents[2] / "app" / "modules" / "integration_hub"
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "import odoo" not in text
        assert "from odoo" not in text
        # Contract files must not hardcode vendor adapters.
        if path.name != "fake_adapter.py":
            assert "odooadapter" not in text.replace("_", "")


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
