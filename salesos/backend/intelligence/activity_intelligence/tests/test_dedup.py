"""Tests for Deduplicator (ADR-012 §3)."""

import pytest
from intelligence.activity_intelligence.sync.dedup import Deduplicator


class TestDeduplicator:
    def test_is_duplicate_true(self):
        dedup = Deduplicator(known_ids={"msg-1", "msg-2"})
        assert dedup.is_duplicate("msg-1")
        assert dedup.is_duplicate("msg-2")
        assert not dedup.is_duplicate("msg-3")

    def test_add_id(self):
        dedup = Deduplicator()
        assert not dedup.is_duplicate("msg-1")
        dedup.add("msg-1")
        assert dedup.is_duplicate("msg-1")

    def test_content_hash_stable(self):
        h1 = Deduplicator.content_hash("Hello", "Body", "2024-01-01")
        h2 = Deduplicator.content_hash("Hello", "Body", "2024-01-01")
        assert h1 == h2

    def test_content_hash_different(self):
        h1 = Deduplicator.content_hash("Hello", "Body A", "2024-01-01")
        h2 = Deduplicator.content_hash("Hello", "Body B", "2024-01-01")
        assert h1 != h2

    def test_known_ids_property(self):
        dedup = Deduplicator(known_ids={"a", "b"})
        assert dedup.known_ids == {"a", "b"}
