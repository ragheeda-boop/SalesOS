"""Unit tests for Redis-backed OAuth state store (memory fallback)."""

from __future__ import annotations

from app.common.oauth_state import (
    clear_oauth_state_memory,
    get_oauth_state,
    store_oauth_state,
)


def setup_function() -> None:
    clear_oauth_state_memory()


def teardown_function() -> None:
    clear_oauth_state_memory()


def test_store_and_get_string_state() -> None:
    store_oauth_state("k1", "google", ttl=60)
    assert get_oauth_state("k1", consume=False) == "google"
    assert get_oauth_state("k1", consume=True) == "google"
    assert get_oauth_state("k1", consume=True) is None


def test_store_and_get_dict_state() -> None:
    payload = {"tenant_id": "t1", "user_id": "u1", "created_at": 1.0}
    store_oauth_state("k2", payload, ttl=60)
    assert get_oauth_state("k2", consume=False) == payload
