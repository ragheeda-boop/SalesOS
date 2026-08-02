"""STORY-11-10 — Second connector (HubSpot) certification suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.integration_hub import SourceConnector, certify_source_connector
from app.modules.integration_hub.hubspot_adapter import HubSpotAdapter
from app.modules.integration_hub.second_connector import (
    SECOND_CONNECTOR_KEY,
    build_certifiable_adapter,
    certify_named_connector,
)


def test_hubspot_is_source_connector() -> None:
    assert isinstance(HubSpotAdapter(), SourceConnector)
    assert HubSpotAdapter().connector_key == SECOND_CONNECTOR_KEY


def test_hubspot_module_has_no_odoo_class() -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "modules"
        / "integration_hub"
        / "hubspot_adapter.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "class OdooAdapter" not in text
    assert "import odoo" not in text


@pytest.mark.asyncio
async def test_hubspot_passes_identical_certification_suite() -> None:
    result = await certify_source_connector(HubSpotAdapter())
    assert result["ok"] is True
    assert result["connector_key"] == "hubspot"
    assert result["pulled"] >= 1


@pytest.mark.asyncio
async def test_certify_named_hubspot_is_second_connector() -> None:
    result = await certify_named_connector("hubspot")
    assert result["ok"] is True
    assert result["is_second_connector"] is True
    assert "not claimed" in result["honesty"]


@pytest.mark.asyncio
async def test_hubspot_connection_failure_fails_cert() -> None:
    with pytest.raises(AssertionError, match="test_connection failed"):
        await certify_source_connector(HubSpotAdapter(fail_connection=True))


def test_unknown_connector_rejected() -> None:
    with pytest.raises(KeyError, match="unknown connector"):
        build_certifiable_adapter("sap-not-built")
