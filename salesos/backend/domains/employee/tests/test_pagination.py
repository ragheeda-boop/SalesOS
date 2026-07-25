"""Tests for employee keyset cursor pagination — B-3."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

import pytest

from sdk.pagination import encode_cursor, decode_cursor, build_keyset_condition


class TestEmployeePagination:
    def test_encode_decode_cursor(self):
        cursor = encode_cursor("550e8400-e29b-41d4-a716-446655440000",
                               datetime(2026, 7, 15, tzinfo=timezone.utc))
        decoded_id, decoded_sort = decode_cursor(cursor)
        assert decoded_id == "550e8400-e29b-41d4-a716-446655440000"
        assert decoded_sort == datetime(2026, 7, 15, tzinfo=timezone.utc)

    def test_encode_decode_cursor_no_sort(self):
        cursor = encode_cursor("550e8400-e29b-41d4-a716-446655440000")
        decoded_id, decoded_sort = decode_cursor(cursor)
        assert decoded_id == "550e8400-e29b-41d4-a716-446655440000"
        assert decoded_sort is None

    def test_cursor_includes_has_next(self):
        from sdk.pagination import CursorPage
        page = CursorPage(items=[1, 2, 3], next_cursor="abc", has_next=True)
        assert page.has_next is True
        assert page.next_cursor == "abc"
