"""STORY-11-10 — Second-connector certification registry (R-02).

Certifies adapters with the identical suite Odoo/Fake use.
Not Production GO — production pilot sync not claimed.
"""

from __future__ import annotations

from typing import Any

from app.modules.integration_hub.certify import certify_source_connector
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.hubspot_adapter import HubSpotAdapter
from app.modules.integration_hub.odoo_adapter import OdooAdapter
from app.modules.integration_hub.rest_csv_adapter import RestCsvSourceConnector
from app.modules.integration_hub.source_connector import SourceConnector

# Provisional Stream A target for R-02 (SAP vs HubSpot board decision still open
# for Chief Architect formal Accept — HubSpot chosen for certification scaffolding).
SECOND_CONNECTOR_KEY = "hubspot"
SECOND_CONNECTOR_TARGET = "HubSpot"


def build_certifiable_adapter(connector_key: str) -> SourceConnector:
    key = (connector_key or "").strip().lower()
    if key in ("fake", "reference"):
        return FakeSourceConnector()
    if key in ("rest_csv", "csv", "rest-csv"):
        return RestCsvSourceConnector()
    if key == "hubspot":
        return HubSpotAdapter()
    if key == "odoo":
        return OdooAdapter()
    raise KeyError(f"unknown connector for certification: {connector_key}")


async def certify_named_connector(connector_key: str) -> dict[str, Any]:
    adapter = build_certifiable_adapter(connector_key)
    result = await certify_source_connector(adapter)
    result["second_connector_target"] = SECOND_CONNECTOR_TARGET
    result["is_second_connector"] = adapter.connector_key == SECOND_CONNECTOR_KEY
    result["honesty"] = (
        "CI certification only; live HubSpot network / production pilot "
        "sync for a paying tenant not claimed."
    )
    return result
