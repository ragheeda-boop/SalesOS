"""Tests for internal plugins — Slack and Salesforce."""

import pytest

from domains.marketplace.plugins.slack import (
    SLACK_MANIFEST,
    SlackNotification,
    format_slack_message,
    verify_slack_signature,
)
from domains.marketplace.plugins.salesforce import (
    SALESFORCE_MANIFEST,
    SalesforceSyncRecord,
)


class TestSlackPlugin:
    def test_manifest_exists(self):
        assert SLACK_MANIFEST["id"] == "salesos-slack"
        assert SLACK_MANIFEST["name"] == "Slack Integration"
        assert "webhook_url" in SLACK_MANIFEST["config_schema"]["required"]

    def test_manifest_has_hooks(self):
        assert "after.decision.evaluated" in SLACK_MANIFEST["hooks"]
        assert "after.company.enriched" in SLACK_MANIFEST["hooks"]

    def test_manifest_permissions(self):
        assert "notifications" in SLACK_MANIFEST["permissions"]
        assert "webhooks" in SLACK_MANIFEST["permissions"]

    def test_format_decision_message(self):
        payload = {
            "decision": {
                "id": "dec-123",
                "score": 85,
                "reason": "High match score",
            },
        }
        notification = format_slack_message("after.decision.evaluated", payload)
        assert notification.channel == "#sales-alerts"
        assert "Decision Evaluated" in notification.text
        assert len(notification.attachments) == 1
        assert notification.attachments[0]["fields"][1]["value"] == "85"

    def test_format_company_enriched(self):
        payload = {
            "company": {
                "name": "Acme Corp",
                "domain": "acme.com",
                "industry": "Technology",
            },
        }
        notification = format_slack_message("after.company.enriched", payload)
        assert notification.channel == "#data-pipeline"
        assert "Company Enriched" in notification.text

    def test_format_company_merged(self):
        payload = {"merge": {"target_name": "Acme Corp"}}
        notification = format_slack_message("after.company.merged", payload)
        assert "Companies Merged" in notification.text

    def test_format_unknown_event(self):
        notification = format_slack_message("some.random.event", {})
        assert notification.channel == "#general"
        assert "SalesOS Event" in notification.text

    def test_slack_notification_dataclass(self):
        notification = SlackNotification(
            channel="#test",
            text="Test message",
            attachments=[{"color": "#36a64f", "fields": []}],
            bot_name="Test Bot",
        )
        assert notification.channel == "#test"
        assert notification.text == "Test message"
        assert len(notification.attachments) == 1

    def test_verify_signature(self):
        body = b'{"test": "data"}'
        import hashlib, hmac
        secret = "my-secret"
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        signature = f"v0={expected}"
        assert verify_slack_signature(body, signature, secret) is True

    def test_verify_signature_invalid(self):
        assert verify_slack_signature(b"test", "v0=invalid", "secret") is False

    def test_verify_signature_empty(self):
        assert verify_slack_signature(b"test", "", "secret") is False


class TestSalesforcePlugin:
    def test_manifest_exists(self):
        assert SALESFORCE_MANIFEST["id"] == "salesos-salesforce"
        assert SALESFORCE_MANIFEST["name"] == "Salesforce Connector"
        assert "client_id" in SALESFORCE_MANIFEST["config_schema"]["required"]

    def test_manifest_has_hooks(self):
        assert "after.company.created" in SALESFORCE_MANIFEST["hooks"]
        assert "after.company.updated" in SALESFORCE_MANIFEST["hooks"]

    def test_manifest_permissions(self):
        assert "company:read" in SALESFORCE_MANIFEST["permissions"]
        assert "company:write" in SALESFORCE_MANIFEST["permissions"]
        assert "contact:read" in SALESFORCE_MANIFEST["permissions"]
        assert "contact:write" in SALESFORCE_MANIFEST["permissions"]

    def test_sync_record_initial_state(self):
        record = SalesforceSyncRecord()
        assert record.sync_status == "pending"

    def test_sync_record_to_dict(self):
        record = SalesforceSyncRecord(
            external_id="ext-123",
            salesos_id="salesos-456",
            object_type="Contact",
            sync_status="synced",
        )
        d = record.to_dict()
        assert d["external_id"] == "ext-123"
        assert d["salesos_id"] == "salesos-456"
        assert d["object_type"] == "Contact"
        assert d["sync_status"] == "synced"

    def test_compute_checksum(self):
        record = SalesforceSyncRecord()
        data = {"name": "John Doe", "email": "john@acme.com"}
        checksum = record.compute_checksum(data)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hexdigest

    def test_different_data_different_checksum(self):
        record = SalesforceSyncRecord()
        c1 = record.compute_checksum({"name": "John"})
        c2 = record.compute_checksum({"name": "Jane"})
        assert c1 != c2
