from datetime import UTC, datetime

from app.modules.integration_hub.health import ConnectorHealth, summarize_connector_health


def test_connector_health_exposes_dead_letter_and_retry_state():
    result = summarize_connector_health(
        [
            ConnectorHealth("odoo", datetime(2026, 9, 22, tzinfo=UTC), 0, 0, True),
            ConnectorHealth("notion", None, 2, 1, True),
        ]
    )
    assert result["counts"] == {"healthy": 1, "degraded": 0, "blocked": 1, "unknown": 0}
    assert result["action_required"] is True
    assert result["connectors"][1]["status"] == "blocked"
