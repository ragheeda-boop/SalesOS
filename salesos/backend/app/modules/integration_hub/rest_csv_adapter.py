"""STORY-13-04 — Generic REST/CSV SourceConnector (third first-party listing).

Certification reference for the third marketplace connector slot
(Odoo + HubSpot + REST/CSV). In-memory only — not live ERP/network GO.
"""

from __future__ import annotations

from app.modules.integration_hub.fake_adapter import FakeSourceConnector


class RestCsvSourceConnector(FakeSourceConnector):
    """REST/CSV adapter — same certifiable surface as Fake, distinct key."""

    @property
    def connector_key(self) -> str:
        return "rest_csv"
