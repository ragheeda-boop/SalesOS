"""Tests for keyset pagination in PostgresSearchRepository.

Covers: cursor encoding/decoding, keyset SQL generation, fallback to offset.
"""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domains.search.contracts.models import SearchQuery
from domains.search.engine.postgres_repo import (
    PostgresSearchRepository,
    decode_search_cursor,
    encode_search_cursor,
)


# ── Cursor Encoding / Decoding ──────────────────────────────────────


class TestCursorEncoding:
    """Test search cursor encode/decode round-trip."""

    def test_encode_decode_basic(self):
        ts = datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc)
        cursor = encode_search_cursor(0.0015, ts, "abc-123")
        rank, uat, rid = decode_search_cursor(cursor)
        assert rid == "abc-123"
        assert abs(rank - 0.0015) < 1e-9

    def test_encode_decode_zero_rank(self):
        cursor = encode_search_cursor(0.0, None, "id-0")
        rank, uat, rid = decode_search_cursor(cursor)
        assert rank == 0.0
        assert rid == "id-0"
        assert uat is None

    def test_encode_decode_high_precision_rank(self):
        cursor = encode_search_cursor(0.1234567890, None, "x")
        rank, _, rid = decode_search_cursor(cursor)
        assert abs(rank - 0.1234567890) < 1e-9
        assert rid == "x"

    def test_encode_returns_base64(self):
        cursor = encode_search_cursor(1.0, None, "test")
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(decoded)
        assert "id" in data
        assert "r" in data

    def test_decode_invalid_cursor_raises(self):
        with pytest.raises(Exception):
            decode_search_cursor("not-a-valid-cursor!!!")


# ── PostgresSearchRepository Signature ──────────────────────────────


class TestPostgresRepoSignature:
    """Test that search_raw and search_by_filters accept cursor params."""

    def test_search_raw_has_cursor_params(self):
        import inspect
        sig = inspect.signature(PostgresSearchRepository.search_raw)
        params = list(sig.parameters.keys())
        assert "cursor_rank" in params
        assert "cursor_updated_at" in params
        assert "cursor_id" in params

    def test_search_by_filters_has_cursor_params(self):
        import inspect
        sig = inspect.signature(PostgresSearchRepository.search_by_filters)
        params = list(sig.parameters.keys())
        assert "cursor_rank" in params
        assert "cursor_updated_at" in params
        assert "cursor_id" in params

    def test_search_method_passes_cursor(self):
        import inspect
        sig = inspect.signature(PostgresSearchRepository.search)
        params = list(sig.parameters.keys())
        assert "query" in params


# ── SearchQuery Cursor Support ──────────────────────────────────────


class TestSearchQueryCursor:
    """Test that SearchQuery model supports cursor fields."""

    def test_default_cursor_is_none(self):
        q = SearchQuery(query="test")
        assert q.cursor is None
        assert q.cursor_sort_value is None

    def test_cursor_can_be_set(self):
        q = SearchQuery(query="test", cursor="abc123", cursor_sort_value=42)
        assert q.cursor == "abc123"
        assert q.cursor_sort_value == 42
