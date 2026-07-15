"""Tests for SDK pagination helpers (encode/decode, CursorPage)."""

import base64
import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from sdk.pagination import (
    CursorPage,
    build_keyset_condition,
    decode_cursor,
    encode_cursor,
)


class FakeCond:
    def __and__(self, other):
        return self
    def __or__(self, other):
        return self

class FakeCol:
    def __lt__(self, other):
        return FakeCond()
    def __gt__(self, other):
        return FakeCond()
    def __eq__(self, other):
        return FakeCond()
    def __ne__(self, other):
        return FakeCond()
    def __le__(self, other):
        return FakeCond()
    def __ge__(self, other):
        return FakeCond()

class FakeModel:
    id = FakeCol()
    created_at = FakeCol()


def test_encode_decode_id_only():
    cursor = encode_cursor("abc-123")
    decoded_id, decoded_sort = decode_cursor(cursor)
    assert decoded_id == "abc-123"
    assert decoded_sort is None


def test_encode_decode_with_sort_value():
    created_at = datetime(2026, 7, 14, 10, 0, 0, tzinfo=timezone.utc)
    cursor = encode_cursor("abc-123", created_at)
    decoded_id, decoded_sort = decode_cursor(cursor)
    assert decoded_id == "abc-123"
    assert decoded_sort == created_at


def test_encode_decode_with_string_sort():
    cursor = encode_cursor("id-1", "marhaba")
    decoded_id, decoded_sort = decode_cursor(cursor)
    assert decoded_id == "id-1"
    assert decoded_sort == "marhaba"


def test_encode_decode_with_int_sort():
    cursor = encode_cursor("id-1", 42)
    decoded_id, decoded_sort = decode_cursor(cursor)
    assert decoded_id == "id-1"
    assert decoded_sort == 42


def test_decode_validates_base64():
    with pytest.raises(Exception):
        decode_cursor("not-valid-base64!!!")  


def test_decode_validates_json():
    b64 = base64.urlsafe_b64encode(b"not json").decode()
    with pytest.raises(Exception):
        decode_cursor(b64)


def test_cursor_page_defaults():
    page = CursorPage()
    assert page.items == []
    assert page.next_cursor is None
    assert page.previous_cursor is None
    assert page.has_next is False
    assert page.has_previous is False
    assert page.total is None


def test_cursor_page_with_items():
    page = CursorPage(items=[1, 2, 3], next_cursor="abc", has_next=True)
    assert len(page.items) == 3
    assert page.next_cursor == "abc"
    assert page.has_next is True


def test_encode_cursor_with_uuid():
    uid = UUID("550e8400-e29b-41d4-a716-446655440000")
    cursor = encode_cursor(uid)
    decoded_id, _ = decode_cursor(cursor)
    assert decoded_id == str(uid)


def test_roundtrip_preserves_sort_value():
    now = datetime.now(timezone.utc)
    cursor = encode_cursor("test-id", now)
    _, sort_back = decode_cursor(cursor)
    assert sort_back == now


def test_encode_short_and_readable():
    cursor = encode_cursor("abc", datetime(2026, 1, 1, tzinfo=timezone.utc))
    decoded = base64.urlsafe_b64decode(cursor).decode()
    raw = json.loads(decoded)
    assert raw["id"] == "abc"
    assert "s" in raw


def test_build_keyset_condition_desc():
    uid = "550e8400-e29b-41d4-a716-446655440000"
    condition = build_keyset_condition(FakeModel, uid, datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert condition is not None


def test_build_keyset_condition_asc():
    uid = "550e8400-e29b-41d4-a716-446655440000"
    condition = build_keyset_condition(
        FakeModel, uid, datetime(2026, 1, 1, tzinfo=timezone.utc), sort_dir="asc"
    )
    assert condition is not None
