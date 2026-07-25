"""Tests for Event Bus event types (ADR-012 §15)."""

import pytest
from intelligence.activity_intelligence.contracts.events import (
    CommunicationReceived,
    CommunicationMapped,
    CommunicationSynced,
    CommunicationDeduplicated,
)


class TestCommunicationEvents:
    def test_communication_received_defaults(self):
        ev = CommunicationReceived()
        assert ev.event_type == "communication.received"
        assert ev.channel == ""
        assert ev.source_provider == ""

    def test_communication_mapped_defaults(self):
        ev = CommunicationMapped()
        assert ev.event_type == "communication.mapped"
        assert ev.company_id is None
        assert ev.confidence == 0.0

    def test_communication_mapped_with_data(self):
        ev = CommunicationMapped(
            communication_id="comm-1",
            channel="email",
            company_id="comp-1",
            confidence=0.85,
            mapping_method="domain_match",
            tenant_id="t1",
        )
        assert ev.company_id == "comp-1"
        assert ev.confidence == 0.85
        assert ev.mapping_method == "domain_match"

    def test_communication_synced_errors(self):
        ev = CommunicationSynced(
            provider="gmail",
            channel="email",
            synced_count=10,
            new_count=3,
            errors=["msg-1: timeout"],
        )
        assert ev.synced_count == 10
        assert ev.new_count == 3
        assert len(ev.errors) == 1

    def test_communication_deduplicated(self):
        ev = CommunicationDeduplicated(
            total_processed=100,
            duplicates_found=5,
            channel="email",
        )
        assert ev.total_processed == 100
        assert ev.duplicates_found == 5
