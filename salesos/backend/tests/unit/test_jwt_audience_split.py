"""STORY-02-03: JWT issuer/audience split groundwork tests."""

from __future__ import annotations

import pytest

from app.common.exceptions import UnauthorizedError
from app.config import settings
from app.modules.identity.service import (
    create_access_token,
    create_owner_access_token,
    create_owner_refresh_token,
    create_refresh_token,
    decode_access_token,
    decode_owner_access_token,
    decode_owner_refresh_token,
    decode_refresh_token,
)


def test_tenant_access_token_audience_claim():
    token = create_access_token("user-1", "tenant-1")
    payload = decode_access_token(token)
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_audience
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["type"] == "access"


def test_owner_access_token_audience_claim():
    token = create_owner_access_token("owner-user-1")
    payload = decode_owner_access_token(token)
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_owner_audience
    assert payload["sub"] == "owner-user-1"
    assert payload["type"] == "access"
    assert "tenant_id" not in payload


def test_tenant_refresh_token_audience_claim():
    token = create_refresh_token("user-2", "tenant-2")
    payload = decode_refresh_token(token)
    assert payload["aud"] == settings.jwt_audience
    assert payload["type"] == "refresh"


def test_owner_refresh_token_audience_claim():
    token = create_owner_refresh_token("owner-user-2")
    payload = decode_owner_refresh_token(token)
    assert payload["aud"] == settings.jwt_owner_audience
    assert payload["type"] == "refresh"


def test_tenant_decoder_rejects_owner_token():
    owner_token = create_owner_access_token("owner-user-3")
    with pytest.raises(UnauthorizedError):
        decode_access_token(owner_token)


def test_owner_decoder_rejects_tenant_token():
    tenant_token = create_access_token("user-3", "tenant-3")
    with pytest.raises(UnauthorizedError):
        decode_owner_access_token(tenant_token)


def test_audiences_are_distinct():
    assert settings.jwt_audience != settings.jwt_owner_audience
